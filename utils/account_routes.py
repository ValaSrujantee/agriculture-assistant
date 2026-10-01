"""Farmer authentication, farm, report, sensor, and collected-data endpoints."""
import json
import os
import random
import re
import uuid
from datetime import datetime, timezone
from functools import wraps

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

import config
from utils.account_manager import AccountManager
from utils.data_processor import DataValidationError
from utils.farm_data_manager import FarmDataManager
from utils.soil_report_parser import parse_soil_report
from utils.weather_service import OpenWeatherProvider, WeatherNotConfigured, WeatherProviderError

account_bp = Blueprint("account", __name__)
accounts = AccountManager()
farm_data = FarmDataManager()
ALLOWED_REPORT_EXTENSIONS = {"pdf", "jpg", "jpeg", "png"}
LANGUAGES = {"English", "Gujarati", "Hindi"}
FARMING_TYPES = {"Crop Farming", "Horticulture", "Plantation", "Mixed Farming", "Other"}
IRRIGATION_SOURCES = {"Borewell", "Canal", "River", "Rainfed", "Drip Irrigation", "Sprinkler", "Other"}


def signed_in_required(api=False):
    def decorate(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("farmer_id"):
                if api:
                    return jsonify({"status": "error", "message": "Please sign in to continue."}), 401
                return redirect(url_for("account.login_page"))
            return view(*args, **kwargs)
        return wrapped
    return decorate


def _json_body():
    return request.get_json(silent=True) or {}


def _farmer_id():
    try:
        return int(session["farmer_id"])
    except (KeyError, TypeError, ValueError):
        return None


def _clean_profile(data, registration=False):
    fields = {name: str(data.get(name) or "").strip() for name in accounts.PROFILE_FIELDS}
    fields["full_name"] = fields["full_name"][:120]
    fields["mobile"] = re.sub(r"[\s()\-]", "", fields["mobile"])
    fields["email"] = fields["email"].lower() or None
    if not fields["full_name"]:
        raise ValueError("Please enter your full name.")
    if not re.fullmatch(r"\+?\d{8,15}", fields["mobile"]):
        raise ValueError("Enter a valid mobile number with 8 to 15 digits.")
    fields["mobile"] = fields["mobile"].lstrip("+")
    if fields["email"] and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", fields["email"]):
        raise ValueError("Enter a valid email address or leave it blank.")
    if fields["pincode"] and not re.fullmatch(r"[A-Za-z0-9 -]{3,12}", fields["pincode"]):
        raise ValueError("Check the pincode/postal code.")
    if fields["preferred_language"] not in LANGUAGES:
        fields["preferred_language"] = "English"
    if registration and not fields["mobile"]:
        raise ValueError("Mobile number is required.")
    return fields


def _clean_farm(data):
    fields = {name: str(data.get(name) or "").strip() for name in accounts.FARM_FIELDS}
    fields["name"] = fields["name"][:100]
    if not fields["name"]:
        raise ValueError("Please give this farm a name.")
    if fields["farming_type"] and fields["farming_type"] not in FARMING_TYPES:
        raise ValueError("Choose a listed farming type.")
    if fields["irrigation_source"] and fields["irrigation_source"] not in IRRIGATION_SOURCES:
        raise ValueError("Choose a listed irrigation source.")
    if fields["size"]:
        try:
            size = float(fields["size"])
        except ValueError:
            raise ValueError("Farm size must be a number.")
        if not (0 < size <= 1000000):
            raise ValueError("Farm size must be greater than zero and no more than 1,000,000.")
        fields["size"] = size
    else:
        fields["size"] = None
    if fields["size_unit"] and fields["size_unit"] not in {"acre", "hectare"}:
        raise ValueError("Farm size unit must be acre or hectare.")
    for date_field in ("sowing_date", "expected_harvest_date"):
        if fields[date_field]:
            try:
                datetime.strptime(fields[date_field], "%Y-%m-%d")
            except ValueError:
                raise ValueError("Crop cycle dates must use a valid calendar date.")
    return fields


@account_bp.get("/login")
def login_page():
    return render_template("login.html")


@account_bp.get("/register")
def register_page():
    return render_template("register.html")


@account_bp.get("/farmer-dashboard")
@signed_in_required()
def farmer_dashboard():
    farmer = accounts.get_farmer(_farmer_id())
    if not farmer:
        session.clear()
        return redirect(url_for("account.login_page"))
    return render_template("farmer_dashboard.html", farmer=farmer)


@account_bp.get("/profile")
@signed_in_required()
def profile_page():
    return render_template("profile.html", farmer=accounts.get_farmer(_farmer_id()))


@account_bp.get("/farms")
@signed_in_required()
def farms_page():
    return redirect(url_for("account.farmer_dashboard"))


@account_bp.post("/api/auth/register")
def register():
    data = _json_body()
    try:
        fields = _clean_profile(data, registration=True)
        password = str(data.get("password") or "")
        if len(password) < 8 or len(password) > 256:
            raise ValueError("Use a password between 8 and 256 characters.")
        if password != str(data.get("confirm_password") or ""):
            raise ValueError("The passwords do not match.")
        farmer_id = accounts.create_farmer(fields, password)
        session.clear()
        session["farmer_id"] = farmer_id
        return jsonify({"status": "success", "farmer": accounts.get_farmer(farmer_id)}), 201
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 422
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc):
            return jsonify({"status": "error", "message": "That mobile number or email is already registered."}), 409
        current_app.logger.warning("Farmer registration failed (%s)", type(exc).__name__)
        return jsonify({"status": "error", "message": "Registration could not be completed."}), 500


@account_bp.post("/api/auth/login")
def login():
    data = _json_body()
    identifier = str(data.get("identifier") or data.get("mobile_or_email") or "").strip()
    password = str(data.get("password") or "")
    if not identifier or not password:
        return jsonify({"status": "error", "message": "Enter your mobile number/email and password."}), 422
    farmer = accounts.authenticate(identifier, password)
    if not farmer:
        return jsonify({"status": "error", "message": "The sign-in details were not recognised."}), 401
    session.clear()
    session["farmer_id"] = farmer["id"]
    return jsonify({"status": "success", "farmer": farmer}), 200


@account_bp.post("/api/auth/logout")
def logout():
    session.clear()
    response = jsonify({"status": "success", "message": "You have signed out."})
    response.delete_cookie(current_app.config.get("SESSION_COOKIE_NAME", "session"))
    return response, 200


@account_bp.get("/api/auth/me")
@signed_in_required(api=True)
def auth_me():
    farmer = accounts.get_farmer(_farmer_id())
    if not farmer:
        session.clear()
        return jsonify({"status": "error", "message": "Please sign in again."}), 401
    return jsonify({"status": "success", "farmer": farmer}), 200


@account_bp.route("/api/profile", methods=["GET", "PUT"])
@signed_in_required(api=True)
def profile_api():
    if request.method == "GET":
        return jsonify({"status": "success", "profile": accounts.get_farmer(_farmer_id())}), 200
    try:
        fields = _clean_profile(_json_body())
        profile = accounts.update_profile(_farmer_id(), fields)
        return jsonify({"status": "success", "profile": profile}), 200
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 422
    except Exception as exc:
        if "UNIQUE constraint failed" in str(exc):
            return jsonify({"status": "error", "message": "That mobile number or email is already in use."}), 409
        return jsonify({"status": "error", "message": "Profile could not be updated."}), 500


@account_bp.route("/api/farms", methods=["GET", "POST"])
@signed_in_required(api=True)
def farms_api():
    farmer_id = _farmer_id()
    if request.method == "GET":
        return jsonify({"status": "success", "farms": accounts.list_farms(farmer_id)}), 200
    try:
        fields = _clean_farm(_json_body())
        farm_id = accounts.save_farm(farmer_id, fields)
        return jsonify({"status": "success", "farm": accounts.get_farm(farmer_id, farm_id)}), 201
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 422


@account_bp.route("/api/farms/<int:farm_id>", methods=["GET", "PUT", "DELETE"])
@signed_in_required(api=True)
def farm_api(farm_id):
    farmer_id = _farmer_id()
    farm = accounts.get_farm(farmer_id, farm_id)
    if not farm:
        return jsonify({"status": "error", "message": "Farm not found."}), 404
    if request.method == "GET":
        return jsonify({"status": "success", "farm": farm}), 200
    if request.method == "DELETE":
        accounts.delete_farm(farmer_id, farm_id)
        return jsonify({"status": "success", "message": "Farm deleted."}), 200
    try:
        fields = _clean_farm(_json_body())
        accounts.save_farm(farmer_id, fields, farm_id=farm_id)
        return jsonify({"status": "success", "farm": accounts.get_farm(farmer_id, farm_id)}), 200
    except ValueError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 422


@account_bp.post("/api/farm-data/validate")
def validate_farm_data():
    data = _json_body()
    try:
        prepared = farm_data.prepare_analysis(data, data.get("sources", {}))
        return jsonify({"status": "success", "valid": True, "completeness": 100,
                        "values": prepared["measurements"], "sources": prepared["sources"],
                        "warnings": prepared["warnings"], "missing": []}), 200
    except DataValidationError as exc:
        try:
            fields = FarmDataManager.validate_measurements(data) if isinstance(data, dict) else {}
        except DataValidationError as invalid:
            return jsonify({"status": "error", "message": invalid.message, "field": invalid.field}), 422
        required = ("N", "P", "K", "ph", "temperature", "humidity", "rainfall")
        missing = [field for field in required if field not in fields]
        return jsonify({"status": "success", "valid": False,
                        "completeness": round(100 * (len(required) - len(missing)) / len(required)),
                        "missing": missing, "message": exc.message, "field": exc.field,
                        "values": fields}), 200


@account_bp.get("/api/farms/<int:farm_id>/soil-trend")
@signed_in_required(api=True)
def farm_soil_trend(farm_id):
    if not accounts.get_farm(_farmer_id(), farm_id):
        return jsonify({"status": "error", "message": "Farm not found."}), 404
    with accounts.connection() as conn:
        rows = conn.execute("""SELECT timestamp, n_val, p_val, k_val, ph FROM farm_history
            WHERE farmer_id = ? AND farm_id = ? ORDER BY id""", (_farmer_id(), farm_id)).fetchall()
    return jsonify({"status": "success", "trend": [dict(row) for row in rows]}), 200


@account_bp.get("/api/farm-data/status")
@signed_in_required(api=True)
def farm_data_status():
    farmer_id = _farmer_id()
    return jsonify({"status": "success", "farms": accounts.list_farms(farmer_id),
                    "reports": accounts.list_reports(farmer_id)}), 200


@account_bp.post("/api/soil-report/upload")
@signed_in_required(api=True)
def upload_soil_report():
    upload = request.files.get("report") or request.files.get("file")
    if not upload or not upload.filename:
        return jsonify({"status": "error", "message": "Choose a soil report file first."}), 422
    filename = secure_filename(upload.filename)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_REPORT_EXTENSIONS:
        return jsonify({"status": "error", "message": "Upload a PDF, JPG, JPEG, or PNG soil report."}), 422
    file_bytes = upload.read()
    if not file_bytes or len(file_bytes) > 8 * 1024 * 1024:
        return jsonify({"status": "error", "message": "The report must be non-empty and 8 MB or smaller."}), 413
    farmer_id = _farmer_id()
    raw_farm_id = request.form.get("farm_id")
    try:
        farm_id = int(raw_farm_id) if raw_farm_id else None
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid farm selection."}), 422
    if farm_id and not accounts.get_farm(farmer_id, farm_id):
        return jsonify({"status": "error", "message": "Farm not found."}), 404
    extracted = parse_soil_report(filename, file_bytes)
    folder = config.SOIL_REPORT_UPLOAD_DIR / str(farmer_id)
    folder.mkdir(parents=True, exist_ok=True)
    stored_path = folder / f"{uuid.uuid4().hex}.{extension}"
    try:
        stored_path.write_bytes(file_bytes)
        report_id = accounts.save_report(farmer_id, farm_id, filename, str(stored_path), extracted)
    except Exception:
        stored_path.unlink(missing_ok=True)
        return jsonify({"status": "error", "message": "The report could not be saved."}), 500
    return jsonify({"status": "success", "report_id": report_id, "filename": filename,
                    "verified": False, "values": extracted}), 201


@account_bp.get("/api/soil-reports")
@signed_in_required(api=True)
def list_soil_reports():
    return jsonify({"status": "success", "reports": accounts.list_reports(_farmer_id())}), 200


@account_bp.post("/api/soil-reports/<int:report_id>/verify")
@signed_in_required(api=True)
def verify_soil_report(report_id):
    values = _json_body().get("values", {})
    mapped = {"N": values.get("N"), "P": values.get("P"), "K": values.get("K"), "ph": values.get("ph")}
    try:
        checked = farm_data.validate_measurements(mapped)
    except DataValidationError as exc:
        return jsonify({"status": "error", "message": exc.message, "field": exc.field}), 422
    if not accounts.verify_report(_farmer_id(), report_id, checked):
        return jsonify({"status": "error", "message": "Soil report not found."}), 404
    return jsonify({"status": "success", "verified": True, "values": checked}), 200


def _validate_sensor(data):
    reading = FarmDataManager.validate_sensor_reading(data)
    reading["timestamp"] = reading.get("timestamp") or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return reading


@account_bp.post("/api/sensor-data")
@signed_in_required(api=True)
def receive_sensor_data():
    data = _json_body()
    try:
        reading = _validate_sensor(data)
        device_id = str(data.get("device_id") or "").strip()[:80]
        if not device_id:
            raise ValueError("A sensor device ID is required.")
        farm_id = data.get("farm_id")
        if farm_id and not accounts.get_farm(_farmer_id(), int(farm_id)):
            return jsonify({"status": "error", "message": "Farm not found."}), 404
        reading_id = accounts.save_sensor_reading(_farmer_id(), int(farm_id) if farm_id else None,
                                                  device_id, "soil_sensor", reading)
        return jsonify({"status": "success", "reading_id": reading_id, "source": "soil_sensor",
                        "demo": False, "reading": reading}), 201
    except (ValueError, TypeError, DataValidationError) as exc:
        return jsonify({"status": "error", "message": str(exc)}), 422


@account_bp.post("/api/sensor-data/simulate")
@signed_in_required(api=True)
def simulate_sensor_data():
    data = _json_body()
    try:
        farm_id = int(data["farm_id"]) if data.get("farm_id") else None
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "Invalid farm selection."}), 422
    if farm_id and not accounts.get_farm(_farmer_id(), int(farm_id)):
        return jsonify({"status": "error", "message": "Farm not found."}), 404
    reading = {"soil_temperature": round(random.uniform(18, 34), 1),
               "soil_moisture": round(random.uniform(20, 65), 1),
               "ph": round(random.uniform(5.5, 7.8), 1),
               "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")}
    reading_id = accounts.save_sensor_reading(_farmer_id(), int(farm_id) if farm_id else None,
                                              "DEMO-SOIL-001", "demo", reading)
    return jsonify({"status": "success", "reading_id": reading_id, "source": "demo",
                    "demo": True, "reading": reading}), 201


@account_bp.post("/api/weather-data")
@signed_in_required(api=True)
def weather_data():
    data = _json_body()
    location = str(data.get("location") or "").strip()[:160]
    if not location:
        return jsonify({"status": "error", "message": "Enter a farm location first."}), 422
    try:
        farm_id = int(data["farm_id"]) if data.get("farm_id") else None
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "Invalid farm selection."}), 422
    if farm_id and not accounts.get_farm(_farmer_id(), farm_id):
        return jsonify({"status": "error", "message": "Farm not found."}), 404
    try:
        result = OpenWeatherProvider().current(location)
        try:
            if farm_id:
                farm = accounts.get_farm(_farmer_id(), int(farm_id))
                farm["location"] = location
                accounts.save_farm(_farmer_id(), _clean_farm(farm), int(farm_id))
        except (TypeError, ValueError):
            pass
        return jsonify({"status": "success", "weather": result}), 200
    except WeatherNotConfigured as exc:
        return jsonify({"status": "error", "message": str(exc), "code": "weather_not_configured"}), 503
    except WeatherProviderError as exc:
        return jsonify({"status": "error", "message": str(exc)}), 502
