# 🌱 Smart Agriculture Assistant

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1.3-green.svg)](https://flask.palletsprojects.com/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.9.1-orange.svg)](https://scikit-learn.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

> **"Recommend crops or provide agricultural guidance from soil, rainfall, season and a curated knowledge base."**

**Smart Agriculture Assistant** is a full-stack, AI-powered agricultural decision-support web application designed to help farmers, agronomists, extension workers, and students determine the most suitable crops for specific farm conditions. It unites a trained **Decision Tree Machine Learning Classifier**, an **Agronomic Rule Engine**, and a structured **Curated Agricultural Knowledge Base** within a modern, responsive SaaS dashboard.

---

## 📌 Problem Statement & Objectives

* **Official Problem Statement:** *"Recommend crops or provide agricultural guidance from soil, rainfall, season and a curated knowledge base."*
* **Category:** Agriculture & FoodTech
* **Key Challenge:** Moving beyond rigid single-prediction tools to provide **Top-3 ranked crop alternatives**, transparent **"Why This Crop?"** explainability, **Soil Health classification**, and actionable **agronomic cultivation and irrigation guidance**.

---

## ✨ Core Features

1. 🌾 **Top-3 Crop Recommendations:** Ranks primary and alternative suitable crops with calibrated model suitability scores.
2. 🔍 **Explainable AI Breakdown ("Why This Crop?"):** Validates temperature, rainfall, humidity, soil nutrients, and season against crop physiological thresholds with visual indicators.
3. 🌱 **Soil Health Screening:** Evaluates Nitrogen (N), Phosphorus (P), Potassium (K), and pH levels with benchmark status tags (*Low*, *Moderate*, *Good*, *High*) and an overall soil fertility score.
4. 🌦 **Environmental Condition Analysis:** Evaluates ambient climate metrics and flags weather anomalies (drought stress, excessive monsoon rainfall, thermal extremes).
5. 📚 **Curated Agricultural Knowledge Base:** Rich encyclopedia of 30+ major crops including soil suitability, water demand category, critical irrigation stages, and pest scouting tips.
6. 💬 **Smart Agri-Assistant Q&A:** Keyword-based semantic question-answering assistant that operates 100% locally and safely without external API dependencies.
7. 📈 **Farm Assessment History:** Automatically logs past evaluations in a local SQLite database with printable report summaries.
8. ⚡ **One-Click Demo Farms:** Pre-loaded realistic farm profiles (Punjab Alluvial Rice, Haryana Wheat, Vidarbha Cotton, Rajasthan Semi-Arid Mustard, Kerala Plantation Coffee, Himachal Apple Orchard).
9. 📊 **Interactive Analytics:** Chart.js radar charts for soil NPK balance vs. benchmarks, crop suitability comparison bars, and feature importance distributions.
10. 🌙 **Modern AgriTech SaaS UI:** Clean responsive design with light/dark theme toggle, toast alerts, and card glassmorphism.

---

## 🏗️ System Architecture

```
User / Web Browser
        ↓ (HTTP / REST API)
Flask Application (app.py)
        ↓
Data Validation & Preprocessing (utils/data_processor.py)
        ├──► ML Crop Recommendation Model (predict.py -> Decision Tree Classifier)
        ├──► Agronomic Rule Engine (utils/rule_engine.py -> Soil & Climate Checks)
        └──► Curated Agricultural Knowledge Base (utils/knowledge_base.py -> JSON Base)
        ↓
Explainable Recommendation & Guidance Aggregator (utils/recommendation_engine.py)
        ├──► SQLite History Database (utils/history_manager.py)
        ↓
Interactive Frontend Dashboard & Visual Analytics (Chart.js + Vanilla JS)
```

### 🧠 Logical Separation of Concerns

* **ML Model:** *"Which crop is predicted based on non-linear multivariate boundaries?"*
* **Rule Engine:** *"Are current soil and weather conditions suitable, deficient, or concerning?"*
* **Knowledge Base:** *"What agronomic guidance, water requirements, and scouting tips should be shown?"*
* **Frontend:** *"How should metrics, charts, and recommendations be presented to the user?"*

---

## 📁 Project Folder Structure

```
smart-agriculture-assistant/
│
├── app.py                      # Flask application and REST API routes
├── train_model.py              # ML model training and evaluation script
├── predict.py                  # Model inference and Top-3 prediction pipeline
├── config.py                   # Central configuration, paths, and thresholds
├── requirements.txt            # Project dependencies
├── README.md                   # Comprehensive documentation
├── .gitignore                  # Git ignore rules
│
├── data/
│   ├── crop_data.csv           # Agronomic training dataset (3,000 samples across 30 crops)
│   ├── crop_knowledge.json     # Curated JSON agricultural knowledge base
│   ├── sample_farms.json       # Demo farm profiles for instant testing
│   ├── generate_dataset.py     # Script to generate/expand the dataset
│   └── farm_history.db         # Local SQLite database for assessment logs
│
├── model/
│   ├── crop_model.pkl          # Serialized Decision Tree Classifier
│   ├── label_encoder.pkl       # Target crop label encoder
│   └── model_metadata.json     # Model metrics, feature importances, and hyperparams
│
├── utils/
│   ├── data_processor.py       # Input sanitation, range validation, DataFrame formatting
│   ├── rule_engine.py          # Soil screening, climate anomaly warnings, explainability
│   ├── knowledge_base.py       # Knowledge retrieval, search filters, and Q&A engine
│   ├── recommendation_engine.py# Aggregates ML, rules, KB, and explainability factors
│   └── history_manager.py      # SQLite manager for assessment records
│
├── templates/
│   ├── index.html              # Modern AgriTech landing page
│   ├── dashboard.html          # Interactive farm assessment dashboard & assistant
│   ├── guidance.html           # Crop knowledge encyclopedia & search explorer
│   ├── history.html            # Historical farm assessments table & modal
│   └── model_performance.html  # ML transparency, feature importance, and benchmarks
│
├── static/
│   ├── css/
│   │   └── style.css           # Modern SaaS stylesheet with Dark Mode support
│   └── js/
│       ├── main.js             # Theme toggle, toast alerts, markdown formatter
│       ├── dashboard.js        # Form validation, sample loader, result renderer
│       ├── charts.js           # Chart.js analytics for soil radar and crop scores
│       └── assistant.js        # Agri-Assistant chatbot controller
│
└── tests/
    ├── test_model.py           # ML inference, accuracy, and probability bounds tests
    ├── test_rules.py           # Soil health thresholds and extreme climate warning tests
    ├── test_knowledge_base.py  # Knowledge retrieval and Q&A matching tests
    └── test_api.py             # Flask REST API endpoints and validation error tests
```

---

## 🔬 Machine Learning Approach

* **Primary Model:** `DecisionTreeClassifier` (Scikit-Learn, CART algorithm)
* **Benchmark Model:** `RandomForestClassifier` (100 estimators)
* **Dataset:** 3,000 samples across 30 crops representing diverse agro-ecological zones.
* **Input Features:**
  * Nitrogen ($N$) - kg/ha
  * Phosphorus ($P$) - kg/ha
  * Potassium ($K$) - kg/ha
  * Ambient Temperature ($^\circ\text{C}$)
  * Relative Humidity ($\%$)
  * Soil pH
  * Rainfall ($mm$)
* **Target Output:** Crop label (30 classes: Rice, Wheat, Maize, Chickpea, Cotton, Sugarcane, Banana, Mango, Apple, Coffee, Mustard, Barley, Tomato, Potato, etc.)

---

## 🚀 Installation & Setup

### 1. Clone the repository / Navigate to directory
```bash
cd smart-agriculture-assistant
```

### 2. Create and Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Train the ML Model (Optional - Pre-trained model included)
```bash
python train_model.py
```

### 5. Run the Application
```bash
python app.py
```

Open your browser and navigate to: **`http://127.0.0.1:5000`**

---

## 🧪 Running Unit Tests

Run the complete test suite with `pytest`:
```bash
pytest tests/ -v
```

The test suite covers model loading, prediction ranking, rule validations, knowledge retrieval, account access, farm isolation, data validation, and REST API routes.

---

## 📡 REST API Documentation

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status and model load verification |
| `POST` | `/api/analyze` | Full farm assessment (ML Top-3 + Rules + Soil + Guidance + History Save) |
| `POST` | `/api/predict` | Quick ML crop recommendation endpoint |
| `GET` | `/api/crops` | List and filter knowledge base crops (`?season=...&category=...&q=...`) |
| `GET` | `/api/crop/<name>` | Detailed knowledge profile for a specific crop |
| `GET` | `/api/sample-farms` | Demo farm profiles for quick testing |
| `POST` | `/api/assistant` | Local knowledge base Q&A query |
| `GET` | `/api/history` | List recent farm analysis logs |
| `DELETE` | `/api/history` | Clear all historical records |
| `GET` | `/api/model-info` | ML model metadata, accuracy, and feature importances |

---

## 👩‍🌾 Farmer Accounts, Farms & Data Collection

The account area adds farmer registration and sign-in, an editable profile, and private farm profiles. Saved assessments are associated with the signed-in farmer and optional selected farm. Guests can still use the existing public analysis page and demo farms; guest history remains separate from account assessments.

Farmers can enter measurements manually, upload a soil report for best-effort extraction, submit a real sensor reading, or deliberately request a simulated demo reading. Extracted N, P, K, and pH values remain editable and must be verified before they are copied into the analysis form. Unsupported report units and unreadable image/PDF content remain blank for manual entry. Image OCR uses `pytesseract` plus the system Tesseract executable; when OCR is unavailable, the app asks the farmer to enter values. PDF text extraction uses `pypdf`.

Weather support uses a server-side OpenWeather provider. Copy `.env.example` to `.env`, set a strong `SECRET_KEY`, and add `OPENWEATHER_API_KEY` to enable it. Without a key, the API returns the manual-entry fallback. The current-conditions endpoint returns a short-window rainfall reading where available; compare it with crop-season rainfall before relying on it for a crop recommendation. Provider keys are never sent to browser code. Farm locations are saved only when the farmer supplies them.

### Added Pages

- `/register` and `/login` — create an account or sign in with mobile/email and password.
- `/farmer-dashboard` — private farm management, saved reports, and soil history trend.
- `/profile` — edit farmer contact and language preferences.
- `/dashboard` — existing analysis dashboard with farm data collection and source indicators. The public/demo analysis remains available without signing in; report upload, sensor history, farms, and private history require sign-in.

### Added APIs

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Create an account and sign in |
| `POST` | `/api/auth/login` | Sign in with mobile number or email |
| `POST` | `/api/auth/logout` | Clear the session |
| `GET` | `/api/auth/me` | Return the signed-in farmer's public profile fields |
| `GET`, `PUT` | `/api/profile` | Read or update the current farmer's profile |
| `GET`, `POST` | `/api/farms` | List or add the current farmer's farms |
| `GET`, `PUT`, `DELETE` | `/api/farms/<id>` | Read, edit, or delete an owned farm |
| `GET` | `/api/farms/<id>/soil-trend` | Return that farm's soil measurements from owned assessments |
| `POST` | `/api/farm-data/validate` | Check completeness, ranges, and sources before analysis |
| `GET` | `/api/farm-data/status` | List the signed-in farmer's farms and soil reports |
| `POST` | `/api/soil-report/upload` | Save a PDF/photo report and attempt N-P-K-pH extraction |
| `GET` | `/api/soil-reports` | List the signed-in farmer's saved reports |
| `POST` | `/api/soil-reports/<id>/verify` | Save farmer-reviewed soil report values |
| `POST` | `/api/sensor-data` | Validate and save a device sensor reading |
| `POST` | `/api/sensor-data/simulate` | Create an explicitly labelled demo reading |
| `POST` | `/api/weather-data` | Request current conditions using the configured provider |

### Database and Privacy

The existing `farm_history` table is extended additively with nullable farmer/farm ownership and data-source metadata, preserving existing history rows as unowned demo history. New `farmers`, `farms`, `soil_reports`, and `sensor_readings` tables hold account data; passwords use Werkzeug's password hash helpers. Account APIs scope farm, report, sensor, and history queries to the authenticated farmer. The SQLite database and uploaded report files remain local application data and are excluded from Git where configured.

For local HTTP development, keep `SESSION_COOKIE_SECURE=false`. Set it to `true` when serving over HTTPS. Choose and preserve a stable random secret in `.env`; do not commit `.env`.

### Added Dependencies and OCR Setup

`python-dotenv` loads the optional local `.env`; `pypdf`, Pillow, and `pytesseract` enable PDF text extraction and optional image OCR. Image OCR additionally needs the Tesseract executable installed on the host. If it is missing or the report is scanned but unreadable, the app leaves values undetected instead of guessing.

After installing requirements, run the app as before:

```bash
python app.py
```

Run all existing and added tests with:

```bash
pytest tests/ -v
```

## ⚠️ Agronomic Disclaimer

> **Responsible Agriculture Notice:** This software application provides informational decision support derived from statistical data, machine-learning models, and a curated agronomic knowledge base. It does **not** replace certified laboratory soil testing, real-time localized weather alerts, or regional agricultural extension services. No guarantees of harvest yield, pest immunity, or financial profit are expressed or implied.

---

## 👤 Author & Contact

* **Developer:** [ValaSrujantee (Srujantee Vala)](https://github.com/ValaSrujantee)
* **Email:** [sruvala333@gmail.com](mailto:sruvala333@gmail.com)
* **GitHub Repository:** [https://github.com/ValaSrujantee](https://github.com/ValaSrujantee)
