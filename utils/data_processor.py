"""
Data Processor and Validation Module for Smart Agriculture Assistant.
Handles input sanitation, schema validation, and feature preparation for ML models.
"""
from typing import Dict, Any, Tuple, List, Optional
import numpy as np
from config import FEATURE_RANGES, VALID_SEASONS


class DataValidationError(Exception):
    """Custom exception raised when farm input fails validation."""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message)
        self.field = field
        self.message = message


class DataProcessor:
    """Preprocesses and validates user input and batch datasets."""

    @staticmethod
    def validate_farm_input(data: Dict[str, Any]) -> Tuple[Dict[str, float], Optional[str], List[str]]:
        """
        Validates and cleans input parameters from web requests.
        Returns:
            - cleaned numeric features dict
            - validated season string (or None)
            - list of minor warnings/notes
        Raises:
            - DataValidationError on invalid or missing critical fields
        """
        if not isinstance(data, dict):
            raise DataValidationError("Input payload must be a JSON object.")

        cleaned = {}
        warnings = []

        # Required numerical fields
        num_fields = ["N", "P", "K", "temperature", "humidity", "rainfall"]
        # pH is optional or defaults to 6.5
        all_num_fields = num_fields + (["ph"] if "ph" in data and data["ph"] is not None else [])

        for field in num_fields:
            if field not in data or data[field] is None or data[field] == "":
                raise DataValidationError(f"Missing required parameter: '{field}'.", field=field)

            try:
                val = float(data[field])
            except (ValueError, TypeError):
                raise DataValidationError(
                    f"Parameter '{field}' must be a valid number, received: {data[field]}.",
                    field=field
                )

            # Range bounds check
            bounds = FEATURE_RANGES.get(field)
            if bounds:
                if val < bounds["min"]:
                    raise DataValidationError(
                        f"'{bounds['name']}' ({val} {bounds['unit']}) cannot be below {bounds['min']} {bounds['unit']}.",
                        field=field
                    )
                if val > bounds["max"]:
                    raise DataValidationError(
                        f"'{bounds['name']}' ({val} {bounds['unit']}) exceeds maximum expected range of {bounds['max']} {bounds['unit']}.",
                        field=field
                    )

            cleaned[field] = val

        # Handle pH
        if "ph" in data and data["ph"] is not None and data["ph"] != "":
            try:
                ph_val = float(data["ph"])
                ph_bounds = FEATURE_RANGES["ph"]
                if ph_val < ph_bounds["min"] or ph_val > ph_bounds["max"]:
                    raise DataValidationError(
                        f"Soil pH ({ph_val}) must be between {ph_bounds['min']} and {ph_bounds['max']}.",
                        field="ph"
                    )
                cleaned["ph"] = ph_val
            except (ValueError, TypeError):
                raise DataValidationError(f"Soil pH must be a valid number, received: {data['ph']}.", field="ph")
        else:
            cleaned["ph"] = 6.5  # Neutral default if not provided
            warnings.append("Soil pH was not specified; default neutral value (6.5) was assumed.")

        # Handle Season
        season = data.get("season")
        if season:
            season_clean = str(season).strip().capitalize()
            matched = False
            for valid_s in VALID_SEASONS:
                if season_clean.lower() == valid_s.lower():
                    season = valid_s
                    matched = True
                    break
            if not matched:
                warnings.append(f"Unrecognized season '{season}'; defaulting to 'All Season'.")
                season = "All Season"
        else:
            season = "All Season"

        return cleaned, season, warnings

    @staticmethod
    def prepare_feature_dataframe(cleaned_features: Dict[str, float]):
        """
        Converts feature dictionary into pandas DataFrame with feature names matching training data:
        [N, P, K, temperature, humidity, ph, rainfall]
        """
        import pandas as pd
        feature_order = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
        return pd.DataFrame([[cleaned_features[f] for f in feature_order]], columns=feature_order)

    @staticmethod
    def prepare_feature_array(cleaned_features: Dict[str, float]) -> np.ndarray:
        """
        Converts feature dictionary into standard 2D numpy array in model training order:
        [N, P, K, temperature, humidity, ph, rainfall]
        """
        feature_order = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
        values = [cleaned_features[f] for f in feature_order]
        return np.array([values], dtype=float)
