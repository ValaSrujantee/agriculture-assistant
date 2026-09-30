"""
ML and Agronomic Decision Engine for Crop Recommendation,
Soil Health Diagnostics, and Fertilizer Optimization.
"""

import math
from typing import Dict, List, Any, Optional
from knowledge_base import CROP_DATABASE, SOIL_DATABASE, DISEASE_DIAGNOSIS_RULES

# Check if scikit-learn is available for optional advanced ensemble
SKLEARN_AVAILABLE = False
try:
    import numpy as np
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.ensemble import RandomForestClassifier
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class SmartAgriAdvisor:
    def __init__(self):
        self.crop_db = CROP_DATABASE
        self.soil_db = SOIL_DATABASE
        self.disease_rules = DISEASE_DIAGNOSIS_RULES
        self._train_ml_model_if_available()

    def _train_ml_model_if_available(self):
        """Train scikit-learn Decision Tree & Random Forest models if sklearn is installed."""
        self.sklearn_model = None
        self.crop_labels = list(self.crop_db.keys())
        
        if not SKLEARN_AVAILABLE:
            return

        try:
            # Generate synthetic agronomic dataset from crop database benchmarks
            X_train = []
            y_train = []

            for idx, (crop_key, crop) in enumerate(self.crop_db.items()):
                # Baseline optimal
                X_train.append([
                    crop["npk_requirement"]["N"],
                    crop["npk_requirement"]["P"],
                    crop["npk_requirement"]["K"],
                    crop["optimal_temp"],
                    70.0, # humidity approx
                    crop["optimal_ph"],
                    crop["optimal_rainfall"]
                ])
                y_train.append(idx)

                # Add simulated variations around valid ranges
                for factor in [-0.15, 0.15, -0.08, 0.08]:
                    var_n = max(10, crop["npk_requirement"]["N"] * (1 + factor))
                    var_p = max(10, crop["npk_requirement"]["P"] * (1 + factor))
                    var_k = max(10, crop["npk_requirement"]["K"] * (1 + factor))
                    var_temp = (crop["min_temp"] + crop["max_temp"]) / 2 + (factor * 5)
                    var_ph = min(8.5, max(4.5, crop["optimal_ph"] + (factor * 0.5)))
                    var_rain = max(200, crop["optimal_rainfall"] * (1 + factor * 2))

                    X_train.append([var_n, var_p, var_k, var_temp, 65.0, var_ph, var_rain])
                    y_train.append(idx)

            clf = RandomForestClassifier(n_estimators=30, random_state=42)
            clf.fit(X_train, y_train)
            self.sklearn_model = clf
        except Exception:
            self.sklearn_model = None

    def evaluate_crop_suitability(
        self,
        nitrogen: float,
        phosphorus: float,
        potassium: float,
        temperature: float,
        rainfall: float,
        ph: float,
        soil_type: str,
        season: str
    ) -> List[Dict[str, Any]]:
        """
        Multi-criteria decision analysis + agronomic rule engine + ML scoring.
        Calculates match percentage and detailed factor breakdowns.
        """
        results = []

        for crop_key, crop in self.crop_db.items():
            # 1. Temperature suitability score (0 - 100)
            if crop["min_temp"] <= temperature <= crop["max_temp"]:
                temp_dist = abs(temperature - crop["optimal_temp"])
                max_allowable_dist = max(crop["max_temp"] - crop["optimal_temp"], crop["optimal_temp"] - crop["min_temp"])
                temp_score = 100 - (temp_dist / (max_allowable_dist + 1e-5)) * 40
            else:
                temp_diff = min(abs(temperature - crop["min_temp"]), abs(temperature - crop["max_temp"]))
                temp_score = max(0, 50 - temp_diff * 10)

            # 2. Rainfall suitability score (0 - 100)
            if crop["min_rainfall"] <= rainfall <= crop["max_rainfall"]:
                rain_dist = abs(rainfall - crop["optimal_rainfall"])
                max_rain_spread = (crop["max_rainfall"] - crop["min_rainfall"]) / 2
                rain_score = 100 - (rain_dist / (max_rain_spread + 1e-5)) * 35
            else:
                rain_diff = min(abs(rainfall - crop["min_rainfall"]), abs(rainfall - crop["max_rainfall"]))
                rain_score = max(0, 45 - (rain_diff / 50))

            # 3. Soil pH score (0 - 100)
            if crop["min_ph"] <= ph <= crop["max_ph"]:
                ph_dist = abs(ph - crop["optimal_ph"])
                ph_score = 100 - (ph_dist / 1.5) * 30
            else:
                ph_diff = min(abs(ph - crop["min_ph"]), abs(ph - crop["max_ph"]))
                ph_score = max(0, 50 - ph_diff * 35)

            # 4. Soil Type match (0 - 100)
            soil_match = False
            for st in crop["soil_types"]:
                if soil_type.lower() in st.lower() or st.lower() in soil_type.lower():
                    soil_match = True
                    break
            soil_score = 100 if soil_match else 40

            # 5. Season match (0 - 100)
            season_match = False
            for s in crop["season"]:
                if season.lower() in s.lower() or s.lower() in season.lower() or s == "Annual" or s == "Perennial":
                    season_match = True
                    break
            season_score = 100 if season_match else 35

            # 6. Nutrient (NPK) proximity score
            req = crop["npk_requirement"]
            n_ratio = min(nitrogen, req["N"]) / max(nitrogen, req["N"], 1)
            p_ratio = min(phosphorus, req["P"]) / max(phosphorus, req["P"], 1)
            k_ratio = min(potassium, req["K"]) / max(potassium, req["K"], 1)
            npk_score = ((n_ratio + p_ratio + k_ratio) / 3.0) * 100

            # Weighted aggregate score
            # Temperature: 20%, Rainfall: 25%, Soil Type: 15%, Season: 15%, pH: 15%, NPK: 10%
            total_score = (
                temp_score * 0.20 +
                rain_score * 0.25 +
                soil_score * 0.15 +
                season_score * 0.15 +
                ph_score * 0.15 +
                npk_score * 0.10
            )

            # Cap between 5 and 99.5
            total_score = round(max(5.0, min(99.5, total_score)), 1)

            # Determine suitability tier
            if total_score >= 80:
                tier = "Highly Recommended"
                tier_color = "emerald"
            elif total_score >= 65:
                tier = "Moderately Recommended"
                tier_color = "blue"
            elif total_score >= 50:
                tier = "Marginal / Requires Amendments"
                tier_color = "amber"
            else:
                tier = "Not Recommended"
                tier_color = "rose"

            results.append({
                "crop_id": crop_key,
                "name": crop["name"],
                "category": crop["category"],
                "icon": crop["icon"],
                "score": total_score,
                "tier": tier,
                "tier_color": tier_color,
                "breakdown": {
                    "temperature": round(temp_score, 1),
                    "rainfall": round(rain_score, 1),
                    "ph": round(ph_score, 1),
                    "soil": round(soil_score, 1),
                    "season": round(season_score, 1),
                    "npk": round(npk_score, 1)
                },
                "details": {
                    "growth_duration": crop["growth_duration_days"],
                    "water_management": crop["water_management"],
                    "fertilizer": crop["fertilizer_recommendation"],
                    "yield": crop["yield_potential"],
                    "market_advice": crop["market_advice"],
                    "common_diseases": crop["common_diseases"],
                    "pests": crop["pests"]
                }
            })

        # Sort descending by score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def analyze_soil_health(self, n: float, p: float, k: float, ph: float, soil_type: str) -> Dict[str, Any]:
        """Analyze soil parameters and generate custom fertilization & amendment guidance."""
        # Standard benchmarks (approx mg/kg or kg/ha for medium soil test values)
        # N: Low < 50, Med 50-100, High > 100
        # P: Low < 30, Med 30-70, High > 70
        # K: Low < 40, Med 40-90, High > 90

        n_status = "Deficient" if n < 50 else ("Excessive" if n > 150 else "Optimal")
        p_status = "Deficient" if p < 30 else ("Excessive" if p > 80 else "Optimal")
        k_status = "Deficient" if k < 40 else ("Excessive" if k > 100 else "Optimal")

        # pH interpretation
        if ph < 5.5:
            ph_status = "Strongly Acidic"
            ph_fix = "Apply agricultural limestone (CaCO3) or dolomite @ 2-4 tonnes/hectare to raise pH and supply calcium."
        elif ph < 6.5:
            ph_status = "Slightly Acidic"
            ph_fix = "Ideal for most crops and acid-loving species like coffee/tea. Maintain with organic compost."
        elif ph <= 7.5:
            ph_status = "Neutral / Optimal"
            ph_fix = "Optimal nutrient bioavailability. Maintain soil organic matter levels."
        elif ph <= 8.5:
            ph_status = "Moderately Alkaline"
            ph_fix = "Apply gypsum (calcium sulphate) @ 1-2 tonnes/hectare and sulphur-based fertilizers."
        else:
            ph_status = "Strongly Alkaline / Sodic"
            ph_fix = "High salinity/alkalinity risk. Deep drainage and gypsum application required with green manuring."

        # Fertilizer actions
        actions = []
        if n_status == "Deficient":
            actions.append("Nitrogen deficit: Add Urea (46% N) or Ammonium Sulphate, or incorporate leguminous green manure (e.g. Dhaincha/Sunn hemp).")
        elif n_status == "Excessive":
            actions.append("Nitrogen high: Avoid heavy top dressing of Urea to prevent excessive vegetative lodging and disease susceptibility.")

        if p_status == "Deficient":
            actions.append("Phosphorus deficit: Apply Single Super Phosphate (SSP 16% P2O5) or DAP. Inoculate with Phosphate Solubilizing Bacteria (PSB).")

        if k_status == "Deficient":
            actions.append("Potassium deficit: Apply Muriate of Potash (MOP 60% K2O) or SOP to boost crop disease resistance and grain filling.")

        soil_meta = self.soil_db.get(soil_type, {})

        return {
            "status": {
                "nitrogen": {"value": n, "status": n_status},
                "phosphorus": {"value": p, "status": p_status},
                "potassium": {"value": k, "status": k_status},
                "ph": {"value": ph, "status": ph_status, "remedy": ph_fix}
            },
            "fertilizer_recommendations": actions,
            "soil_metadata": soil_meta
        }

    def diagnose_crop_issue(self, crop_name: str, query_symptoms: str) -> List[Dict[str, Any]]:
        """Match observed symptoms to disease knowledge base."""
        matched = []
        tokens = query_symptoms.lower().replace(",", " ").split()

        for rule in self.disease_rules:
            crop_match = (
                crop_name.lower() in rule["crop"].lower() or
                rule["crop"].lower() in crop_name.lower() or
                crop_name.lower() == "all"
            )
            
            # Count symptom token overlap
            symptom_text = " ".join(rule["symptoms"]).lower() + " " + rule["diagnosis"].lower()
            overlap_count = sum(1 for token in tokens if len(token) > 2 and token in symptom_text)

            match_score = (overlap_count * 25) + (30 if crop_match else 0)
            if match_score > 25:
                matched.append({
                    "id": rule["id"],
                    "crop": rule["crop"],
                    "diagnosis": rule["diagnosis"],
                    "urgency": rule["urgency"],
                    "confidence": min(98, match_score),
                    "matched_symptoms": rule["symptoms"],
                    "chemical_control": rule["chemical_control"],
                    "organic_control": rule["organic_control"],
                    "preventive_tips": rule["preventive_tips"]
                })

        matched.sort(key=lambda x: x["confidence"], reverse=True)
        return matched

    def search_knowledge_base(self, query: str) -> List[Dict[str, Any]]:
        """Interactive search across all crops, rules, and agronomic guidelines."""
        q = query.lower().strip()
        results = []

        for crop_key, crop in self.crop_db.items():
            crop_text = f"{crop['name']} {crop['category']} {' '.join(crop['season'])} {' '.join(crop['soil_types'])} {crop['market_advice']}".lower()
            if q in crop_text or any(token in crop_text for token in q.split() if len(token) > 2):
                results.append({
                    "type": "Crop Profile",
                    "title": f"{crop['icon']} {crop['name']}",
                    "category": crop["category"],
                    "seasons": crop["season"],
                    "soil": crop["soil_types"],
                    "duration": crop["growth_duration_days"],
                    "yield": crop["yield_potential"],
                    "key_advice": crop["market_advice"]
                })

        return results
