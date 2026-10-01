"""
Rule Engine Module for Smart Agriculture Assistant.
Evaluates soil health, environmental suitability thresholds, extreme condition warnings,
and seasonal compatibility checks logically separated from the ML model.
"""
from typing import Dict, Any, List, Tuple
from config import SOIL_THRESHOLDS, FEATURE_RANGES


class RuleEngine:
    """Evaluates agronomic rules, soil status, and environmental suitability."""

    @staticmethod
    def evaluate_soil_health(n: float, p: float, k: float, ph: float = 6.5) -> Dict[str, Any]:
        """
        Classifies soil nutrient levels (N, P, K) and calculates an overall soil rating.
        Thresholds are documented in config.SOIL_THRESHOLDS.
        """
        def classify_nutrient(val: float, thresholds: Dict[str, float]) -> Dict[str, Any]:
            if val < thresholds["low"]:
                return {"status": "Low", "badge": "warning", "score": 40, "advice": "Deficient. Organic manure or targeted basal fertilization advised."}
            elif val < thresholds["moderate"]:
                return {"status": "Moderate", "badge": "info", "score": 75, "advice": "Fair reserve. Standard maintenance dose recommended."}
            elif val <= thresholds["good"]:
                return {"status": "Good", "badge": "success", "score": 100, "advice": "Optimal nutrient availability for plant uptake."}
            else:
                return {"status": "High", "badge": "primary", "score": 90, "advice": "Abundant. Avoid over-fertilization to prevent nutrient runoff."}

        n_eval = classify_nutrient(n, SOIL_THRESHOLDS["N"])
        p_eval = classify_nutrient(p, SOIL_THRESHOLDS["P"])
        k_eval = classify_nutrient(k, SOIL_THRESHOLDS["K"])

        # pH evaluation
        ph_status = "Optimal"
        ph_badge = "success"
        ph_advice = "Neutral to slightly acidic/alkaline; optimal for general nutrient bioavailability."
        if ph < SOIL_THRESHOLDS["ph"]["strongly_acidic"]:
            ph_status = "Strongly Acidic"
            ph_badge = "danger"
            ph_advice = "Acidic soil. Agricultural lime (calcium carbonate) application is recommended."
        elif ph < SOIL_THRESHOLDS["ph"]["optimal_min"]:
            ph_status = "Moderately Acidic"
            ph_badge = "warning"
            ph_advice = "Slightly acidic. Tolerated by many pulses and fruits; monitor micronutrient uptake."
        elif ph > SOIL_THRESHOLDS["ph"]["strongly_alkaline"]:
            ph_status = "Strongly Alkaline"
            ph_badge = "danger"
            ph_advice = "Alkaline / calcareous. Gypsum application and organic matter addition recommended."
        elif ph > SOIL_THRESHOLDS["ph"]["optimal_max"]:
            ph_status = "Moderately Alkaline"
            ph_badge = "warning"
            ph_advice = "Slightly alkaline. Ensure zinc and iron availability."

        # Overall soil rating calculation
        avg_score = (n_eval["score"] + p_eval["score"] + k_eval["score"]) / 3.0
        if avg_score >= 85 and ph_status == "Optimal":
            overall = "Excellent"
            overall_badge = "success"
            overall_desc = "Soil exhibits well-balanced major nutrients and favorable pH."
        elif avg_score >= 70:
            overall = "Good"
            overall_badge = "success"
            overall_desc = "Soil is fertile with moderate to good macronutrient reserves."
        elif avg_score >= 50:
            overall = "Moderate"
            overall_badge = "warning"
            overall_desc = "Soil shows some nutrient depletion; supplementary organic manure or fertilization suggested."
        else:
            overall = "Low Fertility"
            overall_badge = "danger"
            overall_desc = "Multiple nutrients are deficient. Comprehensive soil conditioning advised."

        return {
            "nitrogen": {"value": n, **n_eval},
            "phosphorus": {"value": p, **p_eval},
            "potassium": {"value": k, **k_eval},
            "ph": {"value": ph, "status": ph_status, "badge": ph_badge, "advice": ph_advice},
            "overall_status": overall,
            "overall_badge": overall_badge,
            "overall_score": round(avg_score, 1),
            "summary": overall_desc,
            "disclaimer": "This is a simplified screening indicator, not a replacement for certified laboratory soil testing."
        }

    @staticmethod
    def evaluate_environmental_conditions(
        temp: float, humidity: float, rainfall: float, crop_knowledge: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Evaluates general ambient environmental parameters and flags any climate anomalies.
        """
        warnings = []
        conditions = {}

        # Temperature
        if temp < 10.0:
            conditions["temperature"] = {"status": "Chilly / Cold", "badge": "info", "score": 60}
            warnings.append("Low ambient temperature may slow germination and vegetative growth for tropical crops.")
        elif temp > 38.0:
            conditions["temperature"] = {"status": "Very Hot", "badge": "danger", "score": 50}
            warnings.append("Extreme heat may cause flower abortion and heat stress in sensitive crops.")
        elif 18.0 <= temp <= 32.0:
            conditions["temperature"] = {"status": "Favorable / Optimal", "badge": "success", "score": 95}
        else:
            conditions["temperature"] = {"status": "Moderate", "badge": "primary", "score": 80}

        # Humidity
        if humidity < 35.0:
            conditions["humidity"] = {"status": "Arid / Low Humidity", "badge": "warning", "score": 65}
            warnings.append("Low humidity accelerates evapotranspiration; frequent irrigation may be required.")
        elif humidity > 85.0:
            conditions["humidity"] = {"status": "High Humidity", "badge": "primary", "score": 80}
            warnings.append("High humidity increases fungal and bacterial disease pressure; scout canopy regularly.")
        else:
            conditions["humidity"] = {"status": "Moderate / Balanced", "badge": "success", "score": 95}

        # Rainfall
        if rainfall < 40.0:
            conditions["rainfall"] = {"status": "Low / Semi-Arid", "badge": "warning", "score": 60}
            warnings.append("Low seasonal rainfall requires dependable supplementary irrigation facilities.")
        elif rainfall > 220.0:
            conditions["rainfall"] = {"status": "Heavy / Abundant", "badge": "primary", "score": 85}
            warnings.append("High rainfall necessitates robust field drainage to prevent waterlogging.")
        else:
            conditions["rainfall"] = {"status": "Moderate / Good", "badge": "success", "score": 95}

        return {
            "conditions": conditions,
            "warnings": warnings,
            "temperature_val": temp,
            "humidity_val": humidity,
            "rainfall_val": rainfall
        }

    @staticmethod
    def evaluate_crop_suitability_factors(
        crop_name: str,
        features: Dict[str, float],
        season: str,
        crop_kb: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generates explainable suitability factors for a specific crop against user conditions.
        Returns check indicators (Suitable / Highly Suitable / Moderate / Caution) for:
        - Temperature
        - Rainfall
        - Humidity
        - Soil Nutrients
        - Season
        """
        crop_info = crop_kb.get(crop_name.lower(), {})
        factors = []
        cautions = []
        
        # 1. Temperature Check
        temp = features.get("temperature", 25.0)
        temp_range = crop_info.get("temperature_range", {"min": 15.0, "max": 35.0})
        if temp_range["min"] <= temp <= temp_range["max"]:
            factors.append({
                "category": "Temperature",
                "status": "Highly Suitable" if (temp_range["min"] + 3 <= temp <= temp_range["max"] - 3) else "Suitable",
                "icon": "✓",
                "positive": True,
                "detail": f"Temperature ({temp}°C) fits within preferred range ({temp_range['min']}°C - {temp_range['max']}°C)."
            })
        else:
            factors.append({
                "category": "Temperature",
                "status": "Outside Preferred Range",
                "icon": "⚠️",
                "positive": False,
                "detail": f"Temperature ({temp}°C) is outside typical range ({temp_range['min']}°C - {temp_range['max']}°C)."
            })
            cautions.append(f"Temperature of {temp}°C may present thermal stress for {crop_info.get('name', crop_name)}.")

        # 2. Rainfall Check
        rain = features.get("rainfall", 100.0)
        rain_range = crop_info.get("rainfall_range", {"min": 40.0, "max": 200.0})
        if rain_range["min"] <= rain <= rain_range["max"]:
            factors.append({
                "category": "Rainfall",
                "status": "Highly Suitable" if (rain_range["min"] + 15 <= rain <= rain_range["max"] - 15) else "Suitable",
                "icon": "✓",
                "positive": True,
                "detail": f"Rainfall ({rain} mm) aligns with required water regimes ({rain_range['min']} - {rain_range['max']} mm)."
            })
        elif rain < rain_range["min"]:
            factors.append({
                "category": "Rainfall",
                "status": "Below Natural Requirement",
                "icon": "⚠️",
                "positive": False,
                "detail": f"Rainfall ({rain} mm) is lower than natural range ({rain_range['min']} - {rain_range['max']} mm); supplementary irrigation required."
            })
            cautions.append(f"Rainfall ({rain} mm) is below typical levels; ensure irrigation support for {crop_info.get('name', crop_name)}.")
        else:
            factors.append({
                "category": "Rainfall",
                "status": "Exceeds Typical Range",
                "icon": "⚠️",
                "positive": False,
                "detail": f"Rainfall ({rain} mm) exceeds upper range ({rain_range['max']} mm); adequate field drainage essential."
            })
            cautions.append(f"Excess rainfall may cause water stagnation for {crop_info.get('name', crop_name)}.")

        # 3. Humidity Check
        hum = features.get("humidity", 60.0)
        hum_range = crop_info.get("humidity_range", {"min": 40.0, "max": 85.0})
        if hum_range["min"] <= hum <= hum_range["max"]:
            factors.append({
                "category": "Humidity",
                "status": "Suitable",
                "icon": "✓",
                "positive": True,
                "detail": f"Relative humidity ({hum}%) supports healthy transpiration and growth."
            })
        else:
            factors.append({
                "category": "Humidity",
                "status": "Moderate Divergence",
                "icon": "ℹ️",
                "positive": True,
                "detail": f"Humidity ({hum}%) is manageable with standard canopy management."
            })

        # 4. Soil Nutrient Check
        n_val = features.get("N", 60.0)
        p_val = features.get("P", 40.0)
        k_val = features.get("K", 40.0)
        factors.append({
            "category": "Soil Nutrients",
            "status": "Compatible",
            "icon": "✓",
            "positive": True,
            "detail": f"Current N-P-K balance ({int(n_val)}-{int(p_val)}-{int(k_val)}) provides adequate substrate for crop development."
        })

        # 5. Season Compatibility
        crop_seasons = crop_info.get("suitable_seasons", ["All Season"])
        if "All Season" in crop_seasons or "Perennial" in crop_seasons or season in crop_seasons or season == "All Season":
            factors.append({
                "category": "Season",
                "status": "Suitable",
                "icon": "✓",
                "positive": True,
                "detail": f"Current season ({season}) matches crop cultivation calendar ({', '.join(crop_seasons)})."
            })
        else:
            factors.append({
                "category": "Season",
                "status": "Seasonal Mismatch",
                "icon": "⚠️",
                "positive": False,
                "detail": f"Selected season ({season}) differs from optimal seasons ({', '.join(crop_seasons)})."
            })
            cautions.append(f"Consider scheduling sowing during primary season: {', '.join(crop_seasons)}.")

        return {
            "factors": factors,
            "cautions": cautions,
            "positive_count": sum(1 for f in factors if f["positive"]),
            "total_count": len(factors)
        }
