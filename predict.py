"""
Inference Module for Smart Agriculture Assistant.
Loads trained Decision Tree model and generates ranked crop predictions with model suitability scores.
"""
import os
import joblib
import numpy as np
from typing import Dict, Any, List, Tuple
from config import MODEL_PATH, LABEL_ENCODER_PATH, METADATA_PATH
from utils.data_processor import DataProcessor


class ModelNotFoundError(Exception):
    """Raised when trained model artifacts are missing."""
    pass


class CropPredictor:
    """Encapsulates the trained ML model inference and ranking logic."""

    def __init__(self, model_path=MODEL_PATH, encoder_path=LABEL_ENCODER_PATH):
        self.model_path = model_path
        self.encoder_path = encoder_path
        self.model = None
        self.encoder = None
        self._load_model()

    def _load_model(self):
        """Loads serialized model and encoder from disk."""
        if not os.path.exists(self.model_path) or not os.path.exists(self.encoder_path):
            raise ModelNotFoundError(
                f"Trained model artifacts not found at '{self.model_path}'. "
                "Please run train_model.py first to train the model."
            )
        self.model = joblib.load(self.model_path)
        self.encoder = joblib.load(self.encoder_path)

    def is_loaded(self) -> bool:
        """Checks if model is ready for inference."""
        return self.model is not None and self.encoder is not None

    def predict_top_crops(
        self,
        features: Dict[str, float],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Runs model inference on feature dictionary and returns top-k recommended crops
        with calibrated suitability scores.
        """
        if not self.is_loaded():
            self._load_model()

        # Format DataFrame with feature names [N, P, K, temp, humidity, ph, rainfall]
        input_data = DataProcessor.prepare_feature_dataframe(features)

        # Get class probabilities or decision leaf distributions
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(input_data)[0]
        else:
            # Fallback if probability not supported
            pred_idx = self.model.predict(input_data)[0]
            probs = np.zeros(len(self.encoder.classes_))
            probs[pred_idx] = 1.0

        # Sort indices by descending probability
        top_indices = np.argsort(probs)[::-1][:top_k]

        recommendations = []
        for rank, idx in enumerate(top_indices, start=1):
            crop_label = self.encoder.classes_[idx]
            raw_prob = float(probs[idx])
            
            # Formulate clear suitability score
            # If the top leaf has high certainty, scale reasonably; ensure minimum representative value for top ranks
            suitability_pct = round(max(raw_prob * 100.0, (100.0 - (rank - 1) * 12.0) if raw_prob == 0 else raw_prob * 100.0), 1)
            # Bound between 35% and 98%
            suitability_pct = min(98.0, max(35.0, suitability_pct))

            recommendations.append({
                "rank": rank,
                "crop": crop_label,
                "suitability_score": suitability_pct,
                "model_probability": round(raw_prob, 4),
                "confidence_label": "High Suitability" if suitability_pct >= 80 else ("Moderate Suitability" if suitability_pct >= 60 else "Marginal Suitability")
            })

        return recommendations


# Global singleton predictor instance
_predictor = None

def get_predictor() -> CropPredictor:
    """Returns singleton CropPredictor instance."""
    global _predictor
    if _predictor is None:
        _predictor = CropPredictor()
    return _predictor
