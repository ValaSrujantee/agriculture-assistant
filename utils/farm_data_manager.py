"""Validation and provenance helpers for collected farm measurements."""
from typing import Any, Dict
from config import FEATURE_RANGES
from utils.data_processor import DataProcessor, DataValidationError


ML_FIELDS = ("N", "P", "K", "ph", "temperature", "humidity", "rainfall")
SOURCE_LABELS = {
    "manual": "Manual", "soil_report": "Soil Test Report", "soil_sensor": "Soil Sensor",
    "weather_service": "Weather Service", "demo": "Demo Data"
}
FIELD_RANGES = {
    "soil_temperature": (-10, 70), "soil_moisture": (0, 100)
}


class FarmDataManager:
    @staticmethod
    def validate_sensor_reading(data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise DataValidationError("Sensor data must be a JSON object.")
        ranges = {"soil_temperature": (-10, 70), "soil_moisture": (0, 100), "ph": (3, 10)}
        reading = {}
        for field, (minimum, maximum) in ranges.items():
            if field in data and data[field] not in (None, ""):
                try:
                    value = float(data[field])
                except (ValueError, TypeError):
                    raise DataValidationError(f"{field.replace('_', ' ').title()} must be numeric.", field)
                if not minimum <= value <= maximum:
                    raise DataValidationError(f"{field.replace('_', ' ').title()} must be between {minimum} and {maximum}.", field)
                reading[field] = value
        if not reading:
            raise DataValidationError("Provide soil temperature, soil moisture, or pH.")
        reading["timestamp"] = str(data.get("timestamp") or "")[:40]
        return reading

    @staticmethod
    def validate_measurements(values: Dict[str, Any]) -> Dict[str, float]:
        if not isinstance(values, dict):
            raise DataValidationError("Farm data must be an object.")
        cleaned = {}
        for field, bounds in FEATURE_RANGES.items():
            if field not in values or values[field] in (None, ""):
                continue
            try:
                value = float(values[field])
            except (ValueError, TypeError):
                raise DataValidationError(f"{bounds['name']} must be a number.", field)
            if not (bounds["min"] <= value <= bounds["max"]):
                raise DataValidationError(
                    f"{bounds['name']} must be between {bounds['min']} and {bounds['max']} {bounds['unit']}.", field)
            cleaned[field] = value
        for field, (minimum, maximum) in FIELD_RANGES.items():
            if field in values and values[field] not in (None, ""):
                try:
                    value = float(values[field])
                except (ValueError, TypeError):
                    raise DataValidationError(f"{field.replace('_', ' ').title()} must be a number.", field)
                if not minimum <= value <= maximum:
                    raise DataValidationError(f"{field.replace('_', ' ').title()} must be between {minimum} and {maximum}.", field)
                cleaned[field] = value
        return cleaned

    @classmethod
    def prepare_analysis(cls, values: Dict[str, Any], sources=None) -> Dict[str, Any]:
        measurements = cls.validate_measurements(values)
        missing = [field for field in ML_FIELDS if field not in measurements]
        if missing:
            labels = {"N": "Nitrogen", "P": "Phosphorus", "K": "Potassium", "ph": "Soil pH",
                      "temperature": "Air temperature", "humidity": "Humidity", "rainfall": "Rainfall"}
            raise DataValidationError("Missing required farm data: " + ", ".join(labels[x] for x in missing) + ".",
                                      missing[0])
        # Keep the original preprocessing/validation path as the final ML schema gate.
        features, season, warnings = DataProcessor.validate_farm_input({**measurements, "season": values.get("season")})
        source_map = {}
        for field in measurements:
            key = (sources or {}).get(field, "manual")
            source_map[field] = SOURCE_LABELS.get(key, "Manual")
        return {"features": features, "season": season, "warnings": warnings,
                "sources": source_map, "measurements": measurements}
