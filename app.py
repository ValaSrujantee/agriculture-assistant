"""
Flask Application Entrypoint for Smart Agriculture Assistant.
Serves web dashboard interfaces and clean REST API endpoints for crop recommendations,
soil health analysis, agricultural knowledge exploration, and historical assessments.
"""
import os
import json
import datetime
from flask import Flask, render_template, request, jsonify, session

import config
from utils.data_processor import DataProcessor, DataValidationError
from utils.recommendation_engine import RecommendationEngine
from utils.knowledge_base import KnowledgeBase
from utils.history_manager import get_history_manager
from utils.farm_data_manager import FarmDataManager, SOURCE_LABELS
from utils.account_routes import account_bp, accounts
from predict import get_predictor, ModelNotFoundError

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static"
)
app.config["SECRET_KEY"] = config.SECRET_KEY
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = config.SESSION_COOKIE_SECURE
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
app.register_blueprint(account_bp)

# Initialize Singletons
knowledge_base = KnowledgeBase()
recommendation_engine = RecommendationEngine(kb=knowledge_base)
history_manager = get_history_manager()


# -----------------------------------------------------------------------------
# Web Page Routes
# -----------------------------------------------------------------------------

@app.route("/")
def index():
    """Landing Page."""
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    """Main Farm Analysis Dashboard."""
    farmer = accounts.get_farmer(session.get("farmer_id")) if session.get("farmer_id") else None
    return render_template("dashboard.html", farmer=farmer)


@app.route("/guidance")
def guidance():
    """Crop Guidance Encyclopedia and Knowledge Explorer."""
    return render_template("guidance.html")


@app.route("/history")
def history():
    """Past Farm Assessment History."""
    return render_template("history.html")


@app.route("/model-performance")
def model_performance():
    """ML Model Transparency & Performance Metrics."""
    return render_template("model_performance.html")


# -----------------------------------------------------------------------------
# REST API Endpoints
# -----------------------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def api_health():
    """System Health Check."""
    model_loaded = False
    try:
        predictor = get_predictor()
        model_loaded = predictor.is_loaded()
    except Exception:
        model_loaded = False

    return jsonify({
        "status": "healthy",
        "service": "Smart Agriculture Assistant API",
        "version": "2.0.0",
        "model_loaded": model_loaded,
        "timestamp": datetime.datetime.now().isoformat()
    }), 200


@app.route("/api/sample-farms", methods=["GET"])
def api_sample_farms():
    """Provides sample farm demo profiles for quick testing."""
    try:
        if os.path.exists(config.SAMPLE_FARMS_PATH):
            with open(config.SAMPLE_FARMS_PATH, "r", encoding="utf-8") as f:
                farms = json.load(f)
            return jsonify({"status": "success", "sample_farms": farms}), 200
        return jsonify({"status": "error", "message": "Sample farms file not found."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/crops", methods=["GET"])
def api_get_crops():
    """List and search all crops in knowledge base."""
    season = request.args.get("season")
    category = request.args.get("category")
    query = request.args.get("q")

    if season or category or query:
        crops = knowledge_base.search_crops(season=season, category=category, query=query)
        return jsonify({"status": "success", "count": len(crops), "crops": crops}), 200
    
    crops_dict = knowledge_base.get_all_crops()
    crops_list = [{"key": k, **v} for k, v in crops_dict.items()]
    return jsonify({"status": "success", "count": len(crops_list), "crops": crops_list}), 200


@app.route("/api/crop/<crop_name>", methods=["GET"])
def api_get_crop_detail(crop_name):
    """Retrieve detailed knowledge profile for a specific crop."""
    crop = knowledge_base.get_crop(crop_name)
    if crop:
        return jsonify({"status": "success", "crop": crop}), 200
    return jsonify({"status": "error", "message": f"Crop '{crop_name}' not found in knowledge base."}), 404


@app.route("/api/predict", methods=["POST"])
def api_predict():
    """Quick ML prediction endpoint for top crop recommendation."""
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON payload."}), 400

        features, season, warnings = DataProcessor.validate_farm_input(data)
        top_k = int(data.get("top_k", 3))

        predictor = get_predictor()
        predictions = predictor.predict_top_crops(features, top_k=top_k)

        return jsonify({
            "status": "success",
            "top_recommendations": predictions,
            "inputs": features,
            "warnings": warnings
        }), 200

    except DataValidationError as dve:
        return jsonify({"status": "error", "message": dve.message, "field": dve.field}), 422
    except ModelNotFoundError as mne:
        return jsonify({"status": "error", "message": str(mne)}), 503
    except Exception as e:
        return jsonify({"status": "error", "message": f"Prediction failed: {str(e)}"}), 500


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    """
    Comprehensive Farm Assessment Endpoint:
    Combines ML prediction, Rule Engine, Soil Health, Environmental Analysis,
    Explainability Factors, and Curated Agronomic Guidance.
    Auto-saves to assessment history.
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"status": "error", "message": "Invalid JSON payload."}), 400

        if data.get("require_complete"):
            prepared = FarmDataManager.prepare_analysis(data, data.get("sources", {}))
            features, season, warnings = prepared["features"], prepared["season"], prepared["warnings"]
        else:
            prepared = None
            features, season, warnings = DataProcessor.validate_farm_input(data)
        farmer_id = session.get("farmer_id")
        farm_id = data.get("farm_id")
        farm = None
        if farm_id:
            if not farmer_id or not accounts.get_farm(int(farmer_id), int(farm_id)):
                return jsonify({"status": "error", "message": "Farm not found for this account."}), 404
            farm = accounts.get_farm(int(farmer_id), int(farm_id))
        farm_name = data.get("farm_name") or (farm["name"] if farm else "My Farm")
        top_k = int(data.get("top_k", 3))

        # Run unified recommendation engine
        result = recommendation_engine.generate_full_analysis(
            features=features,
            season=season,
            top_k=top_k
        )
        result["warnings"] = warnings
        data_sources = {}
        if prepared:
            result["data_sources"] = prepared["sources"]
            result["collected_measurements"] = prepared["measurements"]
            data_sources = prepared["sources"]

        # Save to database
        try:
            record_id = history_manager.save_analysis(
                result, farm_name=farm_name, farmer_id=int(farmer_id) if farmer_id else None,
                farm_id=int(farm_id) if farm_id else None, data_sources=data_sources,
                report_uploaded=bool(data.get("report_id")),
                sensor_used=any(source in {"Soil Sensor", "Demo Data"} for source in data_sources.values()),
                weather_mode="automatic" if "Weather Service" in data_sources.values() else "manual",
                farm_location=(str(data.get("farm_location") or "").strip()[:160] or None))
            result["history_id"] = record_id
        except Exception as db_err:
            print(f"Warning: Could not save to history: {db_err}")
            result["history_id"] = None

        return jsonify({"status": "success", "data": result}), 200

    except DataValidationError as dve:
        return jsonify({"status": "error", "message": dve.message, "field": dve.field}), 422
    except ModelNotFoundError as mne:
        return jsonify({"status": "error", "message": str(mne)}), 503
    except Exception as e:
        return jsonify({"status": "error", "message": f"Farm analysis failed: {str(e)}"}), 500


@app.route("/api/assistant", methods=["POST"])
def api_assistant():
    """
    Curated Agriculture Knowledge Assistant Q&A endpoint.
    Runs 100% locally and safely using the curated knowledge base without third-party dependencies.
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        question = data.get("question", "").strip()

        if not question:
            return jsonify({
                "status": "error",
                "message": "Question cannot be empty."
            }), 400

        response = knowledge_base.answer_query(question)
        return jsonify({
            "status": "success",
            "question": question,
            "answer": response["answer"],
            "matched_crops": response.get("matched_crops", []),
            "crop_key": response.get("crop_key")
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": f"Assistant query failed: {str(e)}"}), 500


@app.route("/api/history", methods=["GET", "DELETE"])
def api_history():
    """Get recent farm assessments or clear history."""
    farmer_id = session.get("farmer_id")
    if request.method == "DELETE":
        history_manager.clear_history(farmer_id=farmer_id)
        return jsonify({"status": "success", "message": "History cleared."}), 200

    limit = int(request.args.get("limit", 20))
    history_list = history_manager.get_recent_history(limit=limit, farmer_id=farmer_id)
    return jsonify({"status": "success", "count": len(history_list), "history": history_list}), 200


@app.route("/api/history/<int:record_id>", methods=["GET"])
def api_get_history_detail(record_id):
    """Retrieve full analysis details of a historical record."""
    analysis = history_manager.get_analysis_by_id(record_id, farmer_id=session.get("farmer_id"))
    if analysis:
        return jsonify({"status": "success", "analysis": analysis}), 200
    return jsonify({"status": "error", "message": f"Record #{record_id} not found."}), 404


@app.route("/api/model-info", methods=["GET"])
def api_model_info():
    """Returns model metadata, performance metrics, and feature importances."""
    try:
        if os.path.exists(config.METADATA_PATH):
            with open(config.METADATA_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
            return jsonify({"status": "success", "metadata": meta}), 200
        return jsonify({"status": "error", "message": "Model metadata not found."}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# -----------------------------------------------------------------------------
# Global Error Handlers
# -----------------------------------------------------------------------------

@app.errorhandler(404)
def not_found_error(e):
    if request.path.startswith("/api/"):
        return jsonify({"status": "error", "message": "API endpoint not found."}), 404
    return render_template("index.html"), 404


@app.errorhandler(500)
def internal_error(e):
    if request.path.startswith("/api/"):
        return jsonify({"status": "error", "message": "Internal server error occurred."}), 500
    return render_template("index.html"), 500


if __name__ == "__main__":
    print("=" * 60)
    print("  SMART AGRICULTURE ASSISTANT - SERVER RUNNING")
    print(f"  Access web application at: http://127.0.0.1:{config.PORT}")
    print("=" * 60)
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG, use_reloader=False)
