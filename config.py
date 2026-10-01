"""
Configuration module for Smart Agriculture Assistant.
Defines paths, thresholds, season mappings, and server settings.
"""
import os
import secrets
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent / ".env")
except ImportError:
    pass

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "model"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Data Files
CROP_DATA_PATH = DATA_DIR / "crop_data.csv"
KNOWLEDGE_BASE_PATH = DATA_DIR / "crop_knowledge.json"
SAMPLE_FARMS_PATH = DATA_DIR / "sample_farms.json"
HISTORY_DB_PATH = DATA_DIR / "farm_history.db"

# Model Files
MODEL_PATH = MODEL_DIR / "crop_model.pkl"
LABEL_ENCODER_PATH = MODEL_DIR / "label_encoder.pkl"
METADATA_PATH = MODEL_DIR / "model_metadata.json"

# Server Configuration
SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ["true", "1", "yes"]
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() in ["true", "1", "yes"]
PORT = int(os.getenv("PORT", 5000))
HOST = os.getenv("HOST", "0.0.0.0")

# Optional OpenWeatherMap API Key (graceful fallback if not set)
WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
SOIL_REPORT_UPLOAD_DIR = DATA_DIR / "soil_reports"
SOIL_REPORT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Input Validations & Agronomic Value Ranges
FEATURE_RANGES = {
    "N": {"min": 0, "max": 250, "unit": "kg/ha", "name": "Nitrogen"},
    "P": {"min": 0, "max": 200, "unit": "kg/ha", "name": "Phosphorus"},
    "K": {"min": 0, "max": 250, "unit": "kg/ha", "name": "Potassium"},
    "temperature": {"min": 0.0, "max": 55.0, "unit": "°C", "name": "Temperature"},
    "humidity": {"min": 5.0, "max": 100.0, "unit": "%", "name": "Relative Humidity"},
    "ph": {"min": 3.0, "max": 10.0, "unit": "pH", "name": "Soil pH"},
    "rainfall": {"min": 0.0, "max": 500.0, "unit": "mm", "name": "Rainfall"}
}

# Soil Nutrient Benchmark Classification Thresholds (General Screening)
SOIL_THRESHOLDS = {
    "N": {"low": 40, "moderate": 80, "good": 140},      # <40: Low, 40-80: Moderate, 80-140: Good, >140: High
    "P": {"low": 25, "moderate": 55, "good": 90},       # <25: Low, 25-55: Moderate, 55-90: Good, >90: High
    "K": {"low": 30, "moderate": 70, "good": 130},      # <30: Low, 30-70: Moderate, 70-130: Good, >130: High
    "ph": {
        "strongly_acidic": 5.5,
        "optimal_min": 6.0,
        "optimal_max": 7.5,
        "strongly_alkaline": 8.5
    }
}

# Seasonal Classifications
VALID_SEASONS = ["Kharif", "Rabi", "Zaid", "All Season", "Perennial"]

# Standard Disclaimer
DISCLAIMER_TEXT = (
    "This application provides informational decision support based on available data, "
    "machine-learning algorithms, and a curated agronomic knowledge base. It does not replace "
    "professional agronomic advice, certified laboratory soil testing, local weather forecasts, "
    "or region-specific agricultural extension services."
)
