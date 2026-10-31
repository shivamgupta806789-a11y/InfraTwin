"""
Test suite for Structured 3D Intervention Generation and Spatial Placement Validation
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.intervention_service import InterventionService
from app.services.model_store import ModelStore

client = TestClient(app)

def test_generate_interventions_sample_office_building():
    """Verify that applying solar_pv, reflective_roof, and external_shading generates valid 3D geometry."""
    payload = {
        "model_id": "sample-office-twin",
        "selected_intervention_ids": ["solar_pv", "reflective_roof", "external_shading"],
        "width_m": 12.0,
        "length_m": 16.0,
        "floors": 2,
        "floor_height_m": 3.0,
        "window_count": 16,
    }
    response = client.post("/api/v1/models/sample-office-twin/interventions", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["model_id"] == "sample-office-twin"
    assert data["applied_count"] == 3
    assert data["rejected_count"] == 0
    assert data["total_applied_cost"] > 0

    # Ensure total cost is exact sum of applied costs
    validated_costs = [item["estimated_cost"] for item in data["interventions"] if item["validation_status"] == "VALIDATED"]
    assert pytest.approx(data["total_applied_cost"], 0.01) == sum(validated_costs)

    interv_map = {item["intervention_type"]: item for item in data["interventions"]}
    
    # Check Solar PV
    assert "solar_pv" in interv_map
    solar = interv_map["solar_pv"]
    assert solar["validation_status"] == "VALIDATED"
    assert len(solar["components_3d"]) > 0
    assert solar["orientation"]["tilt_deg"] == 15.0
    assert solar["orientation"]["azimuth_deg"] == 180.0  # South-facing
    assert solar["geometry_parameters"]["panel_count"] > 0
    # Coordinate validation: rooftop elevation
    assert solar["world_position"][2] >= 2.5

    # Check Reflective Roof
    assert "reflective_roof" in interv_map
    roof = interv_map["reflective_roof"]
    assert roof["validation_status"] == "VALIDATED"
    assert roof["material_parameters"]["solar_reflectance"] >= 0.82
    assert roof["geometry_parameters"]["coated_area_m2"] > 0

    # Check External Shading
    assert "external_shading" in interv_map
    shading = interv_map["external_shading"]
    assert shading["validation_status"] == "VALIDATED"
    assert len(shading["components_3d"]) > 0
    assert shading["geometry_parameters"]["window_apertures"] > 0


def test_placement_validation_rejection_zero_windows():
    """Verify that external_shading is rejected if the building has 0 window apertures."""
    payload = {
        "model_id": "parametric",
        "selected_intervention_ids": ["solar_pv", "external_shading"],
        "width_m": 10.0,
        "length_m": 10.0,
        "floors": 1,
        "floor_height_m": 3.0,
        "window_count": 0,  # Zero windows
    }
    response = client.post("/api/v1/models/interventions/generate", json=payload)
    assert response.status_code == 200
    data = response.json()

    interv_map = {item["intervention_type"]: item for item in data["interventions"]}
    
    # Solar PV should pass
    assert interv_map["solar_pv"]["validation_status"] == "VALIDATED"
    
    # External shading must be REJECTED
    shading = interv_map["external_shading"]
    assert shading["validation_status"] == "REJECTED"
    assert shading["rejection_reason"] is not None
    assert "window aperture" in shading["rejection_reason"].lower()
    assert len(shading["components_3d"]) == 0
    assert shading["estimated_cost"] == 0.0

    assert data["applied_count"] == 1
    assert data["rejected_count"] == 1
    # Cost should strictly reflect only the validated Solar PV
    assert data["total_applied_cost"] == interv_map["solar_pv"]["estimated_cost"]


def test_empty_interventions_request():
    """Verify clean response when no interventions are selected."""
    payload = {
        "model_id": "sample-office-twin",
        "selected_intervention_ids": [],
    }
    response = client.post("/api/v1/models/sample-office-twin/interventions", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["applied_count"] == 0
    assert data["rejected_count"] == 0
    assert data["total_applied_cost"] == 0.0
    assert len(data["interventions"]) == 0


def test_rainwater_and_green_roof_synthesis():
    """Verify rainwater harvesting and green roof placement geometry."""
    payload = {
        "model_id": "parametric",
        "selected_intervention_ids": ["rainwater_harvesting", "green_roof"],
        "width_m": 20.0,
        "length_m": 30.0,
        "floors": 3,
        "floor_height_m": 3.5,
        "window_count": 24,
    }
    response = client.post("/api/v1/models/interventions/generate", json=payload)
    assert response.status_code == 200
    data = response.json()

    interv_map = {item["intervention_type"]: item for item in data["interventions"]}

    assert "rainwater_harvesting" in interv_map
    rwh = interv_map["rainwater_harvesting"]
    assert rwh["validation_status"] == "VALIDATED"
    assert len(rwh["components_3d"]) >= 2  # Tank + Downpipe
    tank = next(c for c in rwh["components_3d"] if c["component_type"] == "storage_tank")
    assert tank["geometry_type"] == "cylinder"

    assert "green_roof" in interv_map
    groof = interv_map["green_roof"]
    assert groof["validation_status"] == "VALIDATED"
    assert groof["geometry_parameters"]["depth_mm"] == 100
    assert groof["geometry_parameters"]["area_m2"] > 0
