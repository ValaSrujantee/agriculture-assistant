# 🌾 AgriSmart — Smart Agriculture & Crop Recommendation Assistant

An intelligent agronomic decision-support platform designed for precision agriculture, soil nutrient optimization, and crop selection based on multi-variable climate parameters, soil profiles, and pest diagnostics.

---

## 🌟 Key Features

1. **🌾 AI & Decision-Tree Crop Recommendation**:
   - Multi-criteria scoring across **Rainfall, Temperature, Soil Type, Season, pH, and NPK nutrients**.
   - Ranked crop alternatives with percentage match confidence.
   - Interactive radar/bar breakdown of environmental suitability.

2. **🧪 Soil Health & Fertilizer Diagnostics**:
   - Analyzes Nitrogen (N), Phosphorus (P), Potassium (K) deficits.
   - Soil pH conditioning guidance (liming for acidic soils, gypsum for alkaline/sodic soils).
   - Fertilizer dosage recommendations.

3. **🩺 Pest & Crop Disease Doctor**:
   - Symptom-to-disease matcher for major cash and food crops.
   - Actionable dual treatment protocols: **Chemical Treatment** and **Bio-control / Organic Remedies**.
   - Preventive field management practices.

4. **📚 Comprehensive Agronomy Encyclopedia**:
   - 15+ curated crop profiles (Rice, Wheat, Maize, Cotton, Sugarcane, Tomato, Potato, Banana, Coffee, etc.).
   - Growth timelines, water management instructions, expected yields, and market advice.

5. **🌦️ Cropping Seasons Calendar**:
   - Kharif (Monsoon), Rabi (Winter), and Zaid (Summer) sowing and harvesting cycles.

6. **🖨️ Advisory Report Export**:
   - One-click print-ready field recommendation summary.

---

## 🚀 Quick Start (Zero-Setup)

The project includes a built-in server that runs directly with Python's standard library:

```powershell
cd smart-agriculture-assistant
python app.py
```

Open your browser and navigate to:
👉 **`http://localhost:8000`**

---

## 📦 Optional ML Dependencies

To enable optional scikit-learn / pandas ensemble models:

```powershell
pip install -r requirements.txt
```

---

## 🐙 Push to Your GitHub Repository

Initialize and push this project to your GitHub:

```powershell
# 1. Navigate to the project directory
cd "C:\Users\SRUJANTEE\.gemini\antigravity\scratch\smart-agriculture-assistant"

# 2. Initialize git and commit
git init
git add .
git commit -m "feat: Initial commit for Smart Agriculture Assistant"

# 3. Rename branch to main
git branch -M main

# 4. Link your remote GitHub repository and push
# (Replace with your actual GitHub username and repository name)
git remote add origin https://github.com/<your-username>/smart-agriculture-assistant.git
git push -u origin main
```

---

## 📁 Project Structure

```
smart-agriculture-assistant/
├── app.py                 # Universal web server and REST API
├── ml_engine.py           # Multi-Criteria Decision & ML Agronomic Engine
├── knowledge_base.py      # Curated crop, soil, and disease database
├── static/
│   ├── index.html         # Interactive UI (Tailwind CSS, Lucide, Chart.js)
│   ├── style.css          # Custom styling and print formatting
│   └── app.js             # Dynamic frontend application logic
├── requirements.txt       # Python dependencies
├── .gitignore             # Standard ignore rules
└── README.md              # Project documentation
```
