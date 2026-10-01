"""
Recommendation Engine Module for Smart Agriculture Assistant.
Orchestrates ML inference, rule-based validations, curated knowledge base lookup,
and transparent explainability calculations into a unified decision-support response.
"""
from typing import Dict, Any, List, Optional
from predict import get_predictor
from utils.rule_engine import RuleEngine
from utils.knowledge_base import KnowledgeBase
from config import DISCLAIMER_TEXT


class RecommendationEngine:
    """Combines ML recommendations, rule validations, and agronomic knowledge."""

    def __init__(self, kb: Optional[KnowledgeBase] = None):
        self.kb = kb or KnowledgeBase()
        self.rule_engine = RuleEngine()

    def generate_full_analysis(
        self,
        features: Dict[str, float],
        season: str = "All Season",
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Executes end-to-end farm assessment:
        1. Predict top crops using trained Decision Tree ML model.
        2. Evaluate soil health indicators (NPK + pH).
        3. Evaluate ambient environmental conditions and weather anomalies.
        4. Build explainable "WHY THIS CROP?" breakdowns for each recommendation.
        5. Attach crop-specific agronomic guidance from curated knowledge base.
        """
        # 1. ML Model Predictions
        predictor = get_predictor()
        ml_recs = predictor.predict_top_crops(features, top_k=top_k)

        # 2. Soil Health Analysis
        soil_analysis = self.rule_engine.evaluate_soil_health(
            n=features["N"],
            p=features["P"],
            k=features["K"],
            ph=features.get("ph", 6.5)
        )

        # 3. Environmental Conditions Analysis
        env_analysis = self.rule_engine.evaluate_environmental_conditions(
            temp=features["temperature"],
            humidity=features["humidity"],
            rainfall=features["rainfall"]
        )

        # 4. Enrich Each Recommendation with Knowledge & Explainability
        enriched_recommendations = []
        for rec in ml_recs:
            crop_key = rec["crop"].lower()
            crop_info = self.kb.get_crop(crop_key) or {
                "name": rec["crop"].capitalize(),
                "overview": "Detailed agronomic profile is being compiled for this crop.",
                "suitable_soil": "Fertile, well-drained agricultural soil.",
                "water_requirement": "Moderate",
                "suitable_seasons": [season] if season else ["All Season"]
            }

            # Generate Explainability Factors
            why_breakdown = self.rule_engine.evaluate_crop_suitability_factors(
                crop_name=crop_key,
                features=features,
                season=season,
                crop_kb=self.kb.get_all_crops()
            )

            enriched_recommendations.append({
                "rank": rec["rank"],
                "crop_key": crop_key,
                "crop_name": crop_info.get("name", rec["crop"].capitalize()),
                "scientific_name": crop_info.get("scientific_name", ""),
                "category": crop_info.get("category", "General Crop"),
                "icon": crop_info.get("icon", "🌱"),
                "suitability_score": rec["suitability_score"],
                "confidence_label": rec["confidence_label"],
                "model_probability": rec["model_probability"],
                "why_breakdown": why_breakdown,
                "guidance": {
                    "overview": crop_info.get("overview"),
                    "suitable_soil": crop_info.get("suitable_soil"),
                    "water_requirement": crop_info.get("water_requirement"),
                    "irrigation_guidance": crop_info.get("irrigation_guidance", "Maintain regular soil moisture based on local conditions."),
                    "nutrient_considerations": crop_info.get("general_nutrient_considerations", "Apply balanced NPK according to regional soil test recommendations."),
                    "cultivation_tips": crop_info.get("general_cultivation_tips", "Ensure proper seedbed preparation and certified seed usage."),
                    "monitoring_tips": crop_info.get("monitoring_tips", "Scout field regularly for early signs of pest or moisture stress."),
                    "common_concerns": crop_info.get("common_environmental_concerns", "Avoid water stagnation and extreme weather exposure during critical growth stages.")
                }
            })

        # Primary Recommendation
        primary_crop = enriched_recommendations[0] if enriched_recommendations else None

        # Compile overall response
        return {
            "primary_recommendation": primary_crop,
            "top_recommendations": enriched_recommendations,
            "soil_health": soil_analysis,
            "environmental_conditions": env_analysis,
            "inputs": {
                **features,
                "season": season
            },
            "disclaimer": DISCLAIMER_TEXT
        }
