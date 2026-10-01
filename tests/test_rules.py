"""
Unit tests for Agronomic Rule Engine and Soil Health Evaluator.
"""
from utils.rule_engine import RuleEngine


def test_soil_health_good():
    """Verify balanced nutrients classify as Good or Excellent."""
    res = RuleEngine.evaluate_soil_health(n=90, p=50, k=80, ph=6.5)
    assert res["overall_status"] in ["Good", "Excellent"]
    assert res["nitrogen"]["status"] == "Good"
    assert res["phosphorus"]["status"] == "Moderate"
    assert res["potassium"]["status"] == "Good"
    assert res["ph"]["status"] == "Optimal"


def test_soil_health_low_nitrogen():
    """Verify deficient nitrogen is flagged as Low."""
    res = RuleEngine.evaluate_soil_health(n=15, p=50, k=80, ph=6.5)
    assert res["nitrogen"]["status"] == "Low"


def test_soil_health_acidic_ph():
    """Verify low pH is flagged as acidic."""
    res = RuleEngine.evaluate_soil_health(n=80, p=50, k=80, ph=4.8)
    assert res["ph"]["status"] == "Strongly Acidic"


def test_environmental_anomalies():
    """Verify extreme heat, drought, or floods trigger rule warnings."""
    # Extreme heat and low rainfall
    res = RuleEngine.evaluate_environmental_conditions(temp=42.0, humidity=30.0, rainfall=20.0)
    assert len(res["warnings"]) >= 2
    assert any("Extreme heat" in w or "temperature" in w for w in res["warnings"])
    assert any("rainfall" in w or "evapotranspiration" in w for w in res["warnings"])
