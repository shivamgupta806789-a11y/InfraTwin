from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_valid_building_accepted():
    payload = {
        "width_m": 12.0,
        "length_m": 16.0,
        "floor_height_m": 3.0,
        "floors": 2,
        "window_count": 16,
        "budget_inr": 250000.0,
        "selected_interventions": []
    }
    response = client.post("/api/v1/building/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is True
    assert data["normalized"]["roof_area_m2"] == 192.0
    assert data["normalized"]["gross_floor_area_m2"] == 384.0
    assert data["normalized"]["total_height_m"] == 6.0

def test_zero_or_negative_dimension_rejected():
    # Negative width
    payload = {
        "width_m": -5.0,
        "length_m": 16.0,
        "floor_height_m": 3.0,
        "floors": 2,
        "window_count": 8,
        "budget_inr": 100000.0
    }
    response = client.post("/api/v1/building/validate", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert "errors" in data

    # Zero length
    payload["width_m"] = 10.0
    payload["length_m"] = 0.0
    response = client.post("/api/v1/building/validate", json=payload)
    assert response.status_code == 422

def test_invalid_floor_and_window_counts_rejected():
    # Zero floors
    payload = {
        "width_m": 10.0,
        "length_m": 10.0,
        "floor_height_m": 3.0,
        "floors": 0,
        "window_count": 4,
        "budget_inr": 50000.0
    }
    response = client.post("/api/v1/building/validate", json=payload)
    assert response.status_code == 422

    # Negative windows
    payload["floors"] = 1
    payload["window_count"] = -3
    response = client.post("/api/v1/building/validate", json=payload)
    assert response.status_code == 422

def test_excessive_window_count_rejected():
    # Windows exceeding wall surface area
    payload = {
        "width_m": 5.0,
        "length_m": 5.0,
        "floor_height_m": 2.5,
        "floors": 1,
        "window_count": 100,  # 200 m² windows on 50 m² wall
        "budget_inr": 50000.0
    }
    response = client.post("/api/v1/building/validate", json=payload)
    assert response.status_code == 422
