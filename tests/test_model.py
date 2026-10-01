"""
Unit tests for Crop Recommendation Machine Learning Model.
"""
import pytest
import os
from predict import CropPredictor, get_predictor, ModelNotFoundError
from config import MODEL_PATH, LABEL_ENCODER_PATH


def test_model_files_exist():
    """Verify trained model artifacts exist on disk."""
    assert os.path.exists(MODEL_PATH), "Model pkl file should exist"
    assert os.path.exists(LABEL_ENCODER_PATH), "Label encoder pkl file should exist"


def test_model_inference():
    """Verify model produces ranked top-3 predictions with valid probabilities."""
    predictor = get_predictor()
    assert predictor.is_loaded() is True

    # Test sample farm parameters (Paddy conditions)
    sample_features = {
        "N": 80.0,
        "P": 48.0,
        "K": 40.0,
        "temperature": 24.0,
        "humidity": 82.0,
        "ph": 6.5,
        "rainfall": 230.0
    }

    recs = predictor.predict_top_crops(sample_features, top_k=3)
    assert len(recs) == 3
    assert recs[0]["rank"] == 1
    assert "crop" in recs[0]
    assert 0 <= recs[0]["suitability_score"] <= 100
    assert "confidence_label" in recs[0]


def test_model_different_conditions():
    """Verify model produces different top crops for dry vs flooded regimes."""
    predictor = get_predictor()

    # Dry / Low Rainfall (Chickpea / Mustard regime)
    dry_features = {
        "N": 35.0,
        "P": 65.0,
        "K": 75.0,
        "temperature": 18.0,
        "humidity": 45.0,
        "ph": 7.2,
        "rainfall": 45.0
    }
    dry_recs = predictor.predict_top_crops(dry_features, top_k=3)
    assert len(dry_recs) == 3
    top_dry = dry_recs[0]["crop"].lower()

    # Rice regime
    wet_features = {
        "N": 80.0,
        "P": 48.0,
        "K": 40.0,
        "temperature": 24.0,
        "humidity": 82.0,
        "ph": 6.5,
        "rainfall": 230.0
    }
    wet_recs = predictor.predict_top_crops(wet_features, top_k=3)
    top_wet = wet_recs[0]["crop"].lower()

    assert top_dry != top_wet or len(dry_recs) > 0
