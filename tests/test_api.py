"""
Unit tests for Flask Web & REST API endpoints.
"""
import pytest
import json
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_endpoint(client):
    """Test /api/health."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "healthy"
    assert data["model_loaded"] is True


def test_sample_farms_endpoint(client):
    """Test /api/sample-farms."""
    res = client.get("/api/sample-farms")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert len(data["sample_farms"]) >= 3


def test_crops_endpoint(client):
    """Test /api/crops and /api/crop/<name>."""
    res = client.get("/api/crops")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["count"] >= 15

    res_crop = client.get("/api/crop/rice")
    assert res_crop.status_code == 200
    assert res_crop.get_json()["crop"]["name"] == "Rice"


def test_analyze_endpoint_valid(client):
    """Test POST /api/analyze with valid farm data."""
    payload = {
        "farm_name": "Test Farm",
        "N": 80,
        "P": 45,
        "K": 40,
        "temperature": 25.0,
        "humidity": 80.0,
        "ph": 6.5,
        "rainfall": 200.0,
        "season": "Kharif"
    }
    res = client.post("/api/analyze", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert "primary_recommendation" in data["data"]
    assert "top_recommendations" in data["data"]
    assert len(data["data"]["top_recommendations"]) == 3
    assert "soil_health" in data["data"]
    assert "environmental_conditions" in data["data"]


def test_analyze_endpoint_invalid(client):
    """Test POST /api/analyze with invalid/missing data."""
    # Missing rainfall
    payload = {
        "N": 80,
        "P": 45,
        "K": 40,
        "temperature": 25.0,
        "humidity": 80.0
    }
    res = client.post("/api/analyze", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 422
    data = res.get_json()
    assert data["status"] == "error"


def test_assistant_endpoint(client):
    """Test POST /api/assistant."""
    payload = {"question": "What is the best season for wheat?"}
    res = client.post("/api/assistant", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert len(data["answer"]) > 10
