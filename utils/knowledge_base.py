"""
Knowledge Base Module for Smart Agriculture Assistant.
Handles curated agricultural data retrieval, crop encyclopedia queries,
and intelligent keyword-based agricultural assistant Q&A.
"""
import json
import re
from typing import Dict, Any, List, Optional
from config import KNOWLEDGE_BASE_PATH


class KnowledgeBase:
    """Manages access to curated agricultural knowledge."""

    def __init__(self, kb_path=None):
        self.kb_path = kb_path or KNOWLEDGE_BASE_PATH
        self.crops_data: Dict[str, Any] = {}
        self._load()

    def _load(self):
        """Loads crop knowledge from JSON file."""
        try:
            with open(self.kb_path, "r", encoding="utf-8") as f:
                self.crops_data = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load knowledge base from {self.kb_path}: {e}")
            self.crops_data = {}

    def get_all_crops(self) -> Dict[str, Any]:
        """Returns all crops in the knowledge base."""
        return self.crops_data

    def get_crop(self, crop_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves details for a specific crop by key or name."""
        if not crop_name:
            return None
        key = crop_name.lower().strip()
        if key in self.crops_data:
            return self.crops_data[key]

        # Search by display name
        for k, info in self.crops_data.items():
            if info.get("name", "").lower() == key:
                return info
        return None

    def search_crops(self, season: Optional[str] = None, category: Optional[str] = None, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """Filters crops based on search criteria."""
        results = []
        for key, crop in self.crops_data.items():
            match = True
            if season and season != "All":
                if season not in crop.get("suitable_seasons", []) and "All Season" not in crop.get("suitable_seasons", []):
                    match = False
            if category and category != "All":
                if category.lower() not in crop.get("category", "").lower():
                    match = False
            if query:
                q = query.lower()
                text = f"{crop.get('name', '')} {crop.get('overview', '')} {crop.get('suitable_soil', '')} {crop.get('category', '')}".lower()
                if q not in text:
                    match = False
            if match:
                results.append({"key": key, **crop})
        return results

    def answer_query(self, user_question: str) -> Dict[str, Any]:
        """
        Answers agricultural questions using intelligent semantic keyword retrieval from the knowledge base.
        Provides zero-dependency, guaranteed responsive Q&A.
        """
        if not user_question or not user_question.strip():
            return {
                "answer": "Please ask a question about crops, soil requirements, seasons, or irrigation guidance.",
                "matched_crops": [],
                "confidence": "Low"
            }

        q = user_question.lower().strip()
        matched_crops = []
        
        # Check if question is about a specific crop
        target_crop_key = None
        for key, crop in self.crops_data.items():
            name = crop.get("name", "").lower()
            if key in q or name in q:
                target_crop_key = key
                matched_crops.append(crop.get("name", key.capitalize()))
                break

        # Specific Crop Questions
        if target_crop_key:
            crop = self.crops_data[target_crop_key]
            crop_name = crop.get("name", target_crop_key.capitalize())

            if any(w in q for w in ["soil", "land", "ph", "earth"]):
                return {
                    "answer": f"**Soil Guidelines for {crop_name}:**\n\n• **Ideal Soil:** {crop.get('suitable_soil')}\n• **pH Range:** {crop.get('ph_range', {}).get('optimal', '6.0 - 7.5')}\n• **Nutrient Advice:** {crop.get('general_nutrient_considerations')}",
                    "matched_crops": matched_crops,
                    "crop_key": target_crop_key
                }
            elif any(w in q for w in ["water", "rain", "irrigation", "moisture"]):
                return {
                    "answer": f"**Water & Irrigation for {crop_name}:**\n\n• **Water Requirement:** {crop.get('water_requirement')}\n• **Preferred Rainfall:** {crop.get('rainfall_range', {}).get('optimal', 'N/A')}\n• **Irrigation Guidance:** {crop.get('irrigation_guidance')}",
                    "matched_crops": matched_crops,
                    "crop_key": target_crop_key
                }
            elif any(w in q for w in ["season", "when", "month", "time", "sow", "plant"]):
                seasons = ", ".join(crop.get("suitable_seasons", []))
                return {
                    "answer": f"**Season & Sowing for {crop_name}:**\n\n• **Optimal Seasons:** {seasons}\n• **Temperature Range:** {crop.get('temperature_range', {}).get('optimal', 'N/A')}\n• **Cultivation Tip:** {crop.get('general_cultivation_tips')}",
                    "matched_crops": matched_crops,
                    "crop_key": target_crop_key
                }
            elif any(w in q for w in ["pest", "disease", "monitor", "problem", "threat", "care"]):
                return {
                    "answer": f"**Crop Protection & Monitoring for {crop_name}:**\n\n• **Monitoring Advice:** {crop.get('monitoring_tips')}\n• **Environmental Concerns:** {crop.get('common_environmental_concerns')}",
                    "matched_crops": matched_crops,
                    "crop_key": target_crop_key
                }
            else:
                return {
                    "answer": f"**Overview for {crop_name} ({crop.get('scientific_name', '')}):**\n\n{crop.get('overview')}\n\n• **Category:** {crop.get('category')}\n• **Ideal Climate:** {crop.get('temperature_range', {}).get('optimal', 'N/A')} temp, {crop.get('humidity_range', {}).get('optimal', 'N/A')} humidity\n• **Optimal Seasons:** {', '.join(crop.get('suitable_seasons', []))}",
                    "matched_crops": matched_crops,
                    "crop_key": target_crop_key
                }

        # General Thematic Questions
        if any(w in q for w in ["high rainfall", "heavy rain", "flood", "waterlogged"]):
            high_water_crops = [c.get("name") for k, c in self.crops_data.items() if "High" in c.get("water_requirement", "") or "Very High" in c.get("water_requirement", "")]
            return {
                "answer": f"**Crops Suited for High Rainfall / Abundant Water:**\n\nCrops that thrive with substantial moisture include: **{', '.join(high_water_crops[:6])}**.\n\nThese crops either require continuous standing water (like Paddy Rice and Jute) or heavy sustained root zone moisture (like Banana and Sugarcane).",
                "matched_crops": high_water_crops[:6]
            }

        if any(w in q for w in ["low rainfall", "drought", "arid", "dry", "less water", "water scarcity"]):
            low_water_crops = [c.get("name") for k, c in self.crops_data.items() if "Low" in c.get("water_requirement", "")]
            return {
                "answer": f"**Drought-Tolerant & Low-Water Crops:**\n\nFor low rainfall or water-scarce zones, recommended crops include: **{', '.join(low_water_crops[:6])}**.\n\nThese crops possess deep taproots or high water-use efficiency (C4 physiology) and perform well under semi-arid conditions.",
                "matched_crops": low_water_crops[:6]
            }

        if any(w in q for w in ["rabi", "winter", "cold"]):
            rabi_crops = [c.get("name") for k, c in self.crops_data.items() if "Rabi" in c.get("suitable_seasons", [])]
            return {
                "answer": f"**Major Rabi (Winter) Season Crops:**\n\nKey crops sown in autumn/winter and harvested in spring include: **{', '.join(rabi_crops)}**.\n\nThey require cool weather during germination/growth and warm dry conditions for ripening.",
                "matched_crops": rabi_crops
            }

        if any(w in q for w in ["kharif", "monsoon", "summer rain"]):
            kharif_crops = [c.get("name") for k, c in self.crops_data.items() if "Kharif" in c.get("suitable_seasons", [])]
            return {
                "answer": f"**Major Kharif (Monsoon) Season Crops:**\n\nKey crops sown with the onset of the southwest monsoon include: **{', '.join(kharif_crops)}**.\n\nThey require warm temperatures and consistent moisture during their vegetative stage.",
                "matched_crops": kharif_crops
            }

        if any(w in q for w in ["consider", "choose", "factor", "decision", "how to"]):
            return {
                "answer": (
                    "**Key Factors to Consider Before Sowing:**\n\n"
                    "1. **Soil Health & Nutrients:** Check Nitrogen (N), Phosphorus (P), Potassium (K), and pH.\n"
                    "2. **Water Availability & Rainfall:** Match crop water demand with anticipated rainfall and irrigation.\n"
                    "3. **Thermal Regime:** Ensure expected minimum and maximum temperatures match the crop's vegetative and flowering thresholds.\n"
                    "4. **Sowing Calendar:** Plant within the recognized agronomic window (Kharif, Rabi, or Zaid) to avoid heat/frost damage.\n"
                    "5. **Market & Storage:** Consider post-harvest demand, storage facilities, and local procurement channels."
                ),
                "matched_crops": []
            }

        # Default fallback with helpful recommendations
        sample_crops = [c.get("name") for c in list(self.crops_data.values())[:5]]
        return {
            "answer": f"I can help you with crop requirements, soil health, irrigation advice, and seasonal suitability.\n\nTry asking:\n• *'What crop is suitable for high rainfall?'*\n• *'What soil conditions are suitable for Rice?'*\n• *'What is the recommended season for Wheat?'*\n• *'What are the best drought-tolerant crops?'*",
            "matched_crops": sample_crops
        }
