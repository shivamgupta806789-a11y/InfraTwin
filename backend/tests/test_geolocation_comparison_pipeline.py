"""
End-to-End Test Suite for Geolocation-Aware AI Recommendations,
Baseline BIM Immutability, and Multi-Domain 3D Interventions.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.model_store import ModelStore

client = TestClient(app)


def test_baseline_bim_immutability():
    """Verify that the original IFC baseline model geometry is preserved and NEVER overwritten by recommendations."""
    baseline_before = ModelStore.get_model("sample-office-twin")
    assert baseline_before is not None

    # Record baseline dimensions and structural properties
    orig_name = baseline_before.building_name
    orig_elements_count = len(baseline_before.elements)
    orig_storeys_count = len(baseline_before.storeys)
    orig_bbox = baseline_before.bounding_box.model_dump()

    # Apply aggressive interventions
    payload = {
        "model_id": "sample-office-twin",
        "selected_intervention_ids": [
            "solar_pv",
            "reflective_roof",
            "roof_insulation",
            "external_shading",
            "rainwater_harvesting",
            "stormwater_bioswale",
            "permeable_paving",
        ],
        "width_m": 12.0,
        "length_m": 16.0,
        "floors": 2,
        "floor_height_m": 3.0,
        "window_count": 16,
        "latitude": 28.6139,
        "longitude": 77.2090,
    }
    response = client.post("/api/v1/models/sample-office-twin/interventions", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["applied_count"] > 0

    # Retrieve baseline model again from store
    baseline_after = ModelStore.get_model("sample-office-twin")
    assert baseline_after is not None

    # Strict immutability checks
    assert baseline_after.building_name == orig_name
    assert len(baseline_after.elements) == orig_elements_count
    assert len(baseline_after.storeys) == orig_storeys_count
    assert baseline_after.bounding_box.model_dump() == orig_bbox


def test_new_delhi_location_recommendations():
    """
    Test 1: New Delhi (Lat: 28.6139, Lon: 77.2090)
    Climate: Hot Semi-Arid / Composite (BSh).
    Expectation:
    - High solar irradiance (GHI > 5.0 kWh/m²/day)
    - Moderate precipitation (~790 mm)
    - Rainwater harvesting cistern sized to 10 kL
    - Solar PV high yield and cool roof prioritized
    """
    payload = {
        "model_id": "sample-office-twin",
        "selected_intervention_ids": ["solar_pv", "reflective_roof", "rainwater_harvesting", "external_shading"],
        "width_m": 12.0,
        "length_m": 16.0,
        "floors": 2,
        "floor_height_m": 3.0,
        "window_count": 16,
        "latitude": 28.6139,
        "longitude": 77.2090,
        "address": "New Delhi, Delhi, India",
    }
    response = client.post("/api/v1/models/sample-office-twin/interventions", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["project_location"]["address"] == "New Delhi, Delhi, India"
    assert any(k in data["project_location"]["climate_zone"] for k in ["BSh", "Cwa", "Composite"])

    interv_map = {item["intervention_type"]: item for item in data["interventions"]}

    # Rainwater harvesting cistern sizing in semi-arid New Delhi: 10 kL
    assert "rainwater_harvesting" in interv_map
    rwh = interv_map["rainwater_harvesting"]
    assert rwh["validation_status"] == "VALIDATED"
    assert rwh["geometry_parameters"]["cistern_capacity_kl"] == 10.0

    # Solar PV yield should reflect high solar resource
    assert "solar_pv" in interv_map
    solar = interv_map["solar_pv"]
    assert solar["validation_status"] == "VALIDATED"
    assert solar["geometry_parameters"]["panel_count"] > 0
    assert solar["expected_benefit"]["annual_generation_kwh"] > 0

    # Verify optimal bundles reflect New Delhi climate priorities
    assert "optimal_bundles" in data
    bundles = data["optimal_bundles"]
    assert len(bundles) >= 3
    bundle_ids = [b["id"] for b in bundles]
    assert "bundle_balanced" in bundle_ids


def test_mumbai_location_recommendations_and_adaptation():
    """
    Test 2: Mumbai (Lat: 19.0760, Lon: 72.8777)
    Climate: Tropical Monsoon / Coastal (Am).
    Expectation:
    - Heavy annual precipitation (> 2000 mm)
    - Peak storm intensity (135 mm/hr)
    - Rainwater harvesting cistern dynamically upsized to 25 kL
    - Stormwater bioswales successfully validated and generated
    - Permeable paving fronting site generated
    """
    payload = {
        "model_id": "sample-office-twin",
        "selected_intervention_ids": [
            "rainwater_harvesting",
            "stormwater_bioswale",
            "permeable_paving",
            "solar_pv",
        ],
        "width_m": 12.0,
        "length_m": 16.0,
        "floors": 2,
        "floor_height_m": 3.0,
        "window_count": 16,
        "latitude": 19.0760,
        "longitude": 72.8777,
        "address": "Mumbai, Maharashtra, India",
    }
    response = client.post("/api/v1/models/sample-office-twin/interventions", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["project_location"]["address"] == "Mumbai, Maharashtra, India"
    assert "Am" in data["project_location"]["climate_zone"]

    interv_map = {item["intervention_type"]: item for item in data["interventions"]}

    # Rainwater harvesting cistern sizing in heavy rainfall Mumbai: 25 kL
    assert "rainwater_harvesting" in interv_map
    rwh = interv_map["rainwater_harvesting"]
    assert rwh["validation_status"] == "VALIDATED"
    assert rwh["geometry_parameters"]["cistern_capacity_kl"] == 25.0
    assert rwh["geometry_parameters"]["radius_m"] == 1.6  # Upsized radius
    assert rwh["geometry_parameters"]["height_m"] == 3.2  # Upsized height

    # Stormwater bioswales generated for pluvial flood attenuation
    assert "stormwater_bioswale" in interv_map
    bioswale = interv_map["stormwater_bioswale"]
    assert bioswale["validation_status"] == "VALIDATED"
    assert len(bioswale["components_3d"]) >= 2  # Swale trench + standpipe overflow
    assert bioswale["expected_benefit"]["peak_discharge_attenuation_pct"] >= 70.0
    assert bioswale["geometry_parameters"]["swale_width_m"] == 1.6

    # Permeable paving generated for front curb
    assert "permeable_paving" in interv_map
    paver = interv_map["permeable_paving"]
    assert paver["validation_status"] == "VALIDATED"
    assert len(paver["components_3d"]) > 0
    assert paver["geometry_parameters"]["infiltration_rate_mm_hr"] == 35.0

    # Cost consistency check
    total_cost = data["total_applied_cost"]
    calc_sum = sum(item["estimated_cost"] for item in data["interventions"] if item["validation_status"] == "VALIDATED")
    assert pytest.approx(total_cost, 0.01) == calc_sum


def test_model_location_endpoints():
    """Verify GET and POST endpoints for model location persistence and local-to-world transform."""
    # 1. Get initial location
    res_get = client.get("/api/v1/models/sample-office-twin/location")
    assert res_get.status_code == 200
    loc_data = res_get.json()
    assert loc_data["is_confirmed"] is True

    # 2. Update model location to Bengaluru
    bengaluru_payload = {
        "address": "Bengaluru, Karnataka, India",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "elevation_m": 920.0,
        "is_confirmed": True,
        "climate_zone": "Aw (Tropical Savanna / Highland)",
        "georeferenced_source": "user_confirmed",
        "local_to_world_transform": {
            "crs": "EPSG:4326",
            "projected_origin": [12.9716, 77.5946],
        },
    }
    res_post = client.post("/api/v1/models/sample-office-twin/location", json=bengaluru_payload)
    assert res_post.status_code == 200
    updated_loc = res_post.json()
    assert updated_loc["address"] == "Bengaluru, Karnataka, India"
    assert updated_loc["latitude"] == 12.9716
    assert updated_loc["elevation_m"] == 920.0

    # 3. Verify GET returns updated location
    res_get_updated = client.get("/api/v1/models/sample-office-twin/location")
    assert res_get_updated.status_code == 200
    assert res_get_updated.json()["address"] == "Bengaluru, Karnataka, India"

    # 4. Verify Bundles endpoint for this location
    res_bundles = client.get("/api/v1/models/sample-office-twin/bundles")
    assert res_bundles.status_code == 200
    bundles_list = res_bundles.json()
    assert len(bundles_list) >= 3


def test_multi_domain_natural_ventilation_and_rooftop_greenhouse():
    """Verify that natural ventilation and rooftop greenhouse 3D geometry generate with authentic climate links."""
    payload = {
        "model_id": "sample-office-twin",
        "selected_intervention_ids": [
            "natural_ventilation",
            "rooftop_greenhouse",
        ],
        "width_m": 12.0,
        "length_m": 16.0,
        "floors": 2,
        "floor_height_m": 3.0,
        "window_count": 16,
        "latitude": 28.6139,
        "longitude": 77.2090,
    }
    response = client.post("/api/v1/models/sample-office-twin/interventions", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["applied_count"] == 2
    assert data["rejected_count"] == 0
    interv_map = {item["intervention_type"]: item for item in data["interventions"]}

    # Check Natural Ventilation
    assert "natural_ventilation" in interv_map
    nat_vent = interv_map["natural_ventilation"]
    assert nat_vent["validation_status"] == "VALIDATED"
    assert len(nat_vent["components_3d"]) == 2  # North and South clerestory louvers
    assert nat_vent["expected_benefit"]["hvac_cooling_energy_reduction_pct"] > 10.0
    assert nat_vent["estimated_cost"] > 0

    # Check Rooftop Greenhouse
    assert "rooftop_greenhouse" in interv_map
    gh = interv_map["rooftop_greenhouse"]
    assert gh["validation_status"] == "VALIDATED"
    assert len(gh["components_3d"]) == 1
    assert gh["geometry_parameters"]["greenhouse_area_m2"] > 0
    assert gh["expected_benefit"]["rooftop_thermal_barrier_temp_drop_deg_c"] > 5.0
    assert gh["estimated_cost"] > 0

    # Ensure total cost matches sum of validated components
    assert pytest.approx(data["total_applied_cost"], 0.01) == (nat_vent["estimated_cost"] + gh["estimated_cost"])

