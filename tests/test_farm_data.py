import sqlite3

import pytest

from utils.account_manager import AccountManager
from utils.data_processor import DataValidationError
from utils.farm_data_manager import FarmDataManager
from utils.history_manager import HistoryManager
from utils.soil_report_parser import parse_soil_report_text
from utils.weather_service import OpenWeatherProvider, WeatherNotConfigured


VALID_DATA = {
    "N": 125, "P": 48, "K": 62, "ph": 6.8,
    "soil_temperature": 26.5, "soil_moisture": 42.3,
    "temperature": 29, "humidity": 72, "rainfall": 180, "season": "Kharif",
}


def test_valid_manual_data_and_final_ml_payload():
    prepared = FarmDataManager.prepare_analysis(VALID_DATA)
    assert prepared["features"]["N"] == 125
    assert prepared["features"]["ph"] == 6.8
    assert prepared["season"] == "Kharif"
    assert "soil_temperature" not in prepared["features"]
    assert prepared["sources"]["N"] == "Manual"


def test_missing_required_npk_or_ph_is_reported_not_defaulted():
    for field in ("N", "P", "K", "ph"):
        values = dict(VALID_DATA)
        values.pop(field)
        with pytest.raises(DataValidationError, match="Missing required farm data") as err:
            FarmDataManager.prepare_analysis(values)
        assert err.value.field == field


@pytest.mark.parametrize("field,value", [("ph", 11), ("temperature", 56), ("humidity", 101), ("rainfall", -1)])
def test_invalid_measurements_are_rejected(field, value):
    values = dict(VALID_DATA)
    values[field] = value
    with pytest.raises(DataValidationError):
        FarmDataManager.prepare_analysis(values)


def test_weather_payload_ranges_are_checked():
    assert FarmDataManager.validate_measurements({"temperature": 23, "humidity": 60, "rainfall": 0}) == {
        "temperature": 23, "humidity": 60, "rainfall": 0
    }
    with pytest.raises(DataValidationError, match="Humidity"):
        FarmDataManager.validate_measurements({"humidity": 120})
    with pytest.raises(WeatherNotConfigured, match="enter weather values manually"):
        OpenWeatherProvider(api_key="").current("Nadiad")


def test_sensor_payload_validation():
    reading = FarmDataManager.validate_sensor_reading({
        "device_id": "SOIL-001", "soil_temperature": 26.5, "soil_moisture": 42.3, "ph": 6.8
    })
    assert reading["ph"] == 6.8
    assert reading["soil_moisture"] == 42.3
    with pytest.raises(DataValidationError, match="between 3 and 10"):
        FarmDataManager.validate_sensor_reading({"ph": 12})


def test_source_tracking_and_incomplete_status():
    sources = {"N": "soil_report", "P": "soil_report", "K": "manual", "ph": "soil_sensor",
               "temperature": "weather_service", "humidity": "weather_service", "rainfall": "weather_service"}
    prepared = FarmDataManager.prepare_analysis(VALID_DATA, sources)
    assert prepared["sources"]["N"] == "Soil Test Report"
    assert prepared["sources"]["ph"] == "Soil Sensor"
    assert prepared["sources"]["rainfall"] == "Weather Service"


def test_soil_report_parser_is_conservative_and_does_not_guess_units():
    parsed = parse_soil_report_text("Nitrogen: 125 kg/ha\nP: 48 kg/ha\npotassium 62 kg/ha\nSoil pH: 6.8")
    assert parsed["N"]["value"] == 125
    assert parsed["P"]["value"] == 48
    assert parsed["K"]["value"] == 62
    assert parsed["ph"]["value"] == 6.8
    missing = parse_soil_report_text("Nitrogen: 125 mg/kg")
    assert missing["N"]["value"] is None
    assert missing["N"]["status"] == "unit_mismatch"
    assert missing["K"]["value"] is None
    assert missing["K"]["status"] == "not_detected"


@pytest.fixture
def account_client(tmp_path, monkeypatch):
    import app as app_module
    from utils import account_routes

    manager = AccountManager(tmp_path / "accounts.db")
    monkeypatch.setattr(account_routes, "accounts", manager)
    monkeypatch.setattr(app_module, "accounts", manager)
    app_module.app.config.update(TESTING=True, SECRET_KEY="test-session-secret", SESSION_COOKIE_SECURE=False)
    return app_module.app.test_client(), manager


def register(client, mobile, email=None):
    return client.post("/api/auth/register", json={
        "full_name": "Test Farmer", "mobile": mobile, "email": email,
        "password": "secure-pass-123", "confirm_password": "secure-pass-123",
        "preferred_language": "Gujarati",
    })


def test_registration_hash_login_logout_and_duplicate(account_client):
    client, manager = account_client
    response = register(client, "9876543210", "farmer@example.test")
    assert response.status_code == 201
    assert "password_hash" not in response.json["farmer"]
    with manager.connection() as conn:
        stored = conn.execute("SELECT password_hash FROM farmers WHERE mobile = ?", ("9876543210",)).fetchone()[0]
    assert stored != "secure-pass-123"
    duplicate = register(client, "9876543210", "other@example.test")
    assert duplicate.status_code == 409
    client.post("/api/auth/logout")
    login = client.post("/api/auth/login", json={"identifier": "farmer@example.test", "password": "secure-pass-123"})
    assert login.status_code == 200
    assert client.get("/farmer-dashboard").status_code == 200
    client.post("/api/auth/logout")
    assert client.get("/api/farms").status_code == 401


def test_farm_data_isolation_and_profile(account_client):
    client_a, manager = account_client
    client_b = client_a.application.test_client()
    assert register(client_a, "9876543211").status_code == 201
    farm = client_a.post("/api/farms", json={"name": "Main Farm", "size": 5, "size_unit": "acre",
                                              "village": "Nadiad", "farming_type": "Crop Farming",
                                              "irrigation_source": "Borewell", "current_crop": "Wheat"})
    assert farm.status_code == 201
    farm_id = farm.json["farm"]["id"]
    client_a.post("/api/auth/logout")
    assert register(client_b, "9876543212").status_code == 201
    assert client_b.get("/api/farms").json["farms"] == []
    assert client_b.get(f"/api/farms/{farm_id}").status_code == 404
    assert client_a.get("/api/profile").status_code == 401


def test_simulated_sensor_is_explicitly_demo_and_report_requires_sign_in(account_client):
    client, manager = account_client
    demo = client.post("/api/sensor-data/simulate", json={})
    assert demo.status_code == 401
    assert register(client, "9876543213").status_code == 201
    demo = client.post("/api/sensor-data/simulate", json={})
    assert demo.status_code == 201
    assert demo.json["demo"] is True
    assert demo.json["source"] == "demo"
    with manager.connection() as conn:
        assert conn.execute("SELECT source FROM sensor_readings").fetchone()[0] == "demo"


def test_history_records_are_scoped_to_farmer_and_legacy_rows_stay_separate(tmp_path):
    db_path = tmp_path / "history.db"
    accounts = AccountManager(db_path)
    farmer_a = accounts.create_farmer({"full_name": "A", "mobile": "9876543214", "preferred_language": "English"}, "password-123")
    farmer_b = accounts.create_farmer({"full_name": "B", "mobile": "9876543215", "preferred_language": "English"}, "password-123")
    history = HistoryManager(db_path)
    result = {"inputs": {"N": 20, "P": 30, "K": 40, "temperature": 22, "humidity": 60, "ph": 6.4, "rainfall": 70},
              "primary_recommendation": {"crop_name": "Wheat", "suitability_score": 80}, "soil_health": {"overall_status": "Good"}}
    record_id = history.save_analysis(result, "Owned farm", farmer_id=farmer_a, data_sources={"N": "Manual"})
    assert len(history.get_recent_history(farmer_id=farmer_a)) == 1
    assert history.get_recent_history(farmer_id=farmer_b) == []
    assert history.get_analysis_by_id(record_id, farmer_id=farmer_b) is None
    assert history.get_analysis_by_id(record_id, farmer_id=farmer_a) == result
    assert history.get_recent_history(farmer_id=None) == []
