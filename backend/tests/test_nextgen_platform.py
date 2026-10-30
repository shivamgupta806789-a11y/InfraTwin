import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.model_store import ModelStore
from app.services.geotechnical_service import GeotechnicalService
from app.services.city_service import CityService
from app.services.sustainability_service import SustainabilityRecommendationService
from app.services.scenario_service import ScenarioEvaluationService
from app.services.ml_prediction_service import MLEnergyPredictionService

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_models():
    ModelStore.initialize_with_sample_model()

def test_geotechnical_profile_endpoint():
    response = client.get("/api/v1/geotechnical/profile?latitude=28.6139&longitude=77.2090")
    assert response.status_code == 200
    data = response.json()
    assert "boreholes" in data
    assert len(data["boreholes"]) >= 3
    assert "regional_strata_summary" in data
    assert len(data["regional_strata_summary"]) >= 4
    assert data["crs"] == "EPSG:4326 (WGS84)"
    assert data["seismic_zone"].startswith("Zone")
    assert data["groundwater_table_m"] > 0
    assert "screening_disclaimer" in data

def test_city_hierarchy_endpoint():
    response = client.get("/api/v1/city/model")
    assert response.status_code == 200
    data = response.json()
    assert data["city_id"] == "city-techcity-smart-district"
    assert len(data["districts"]) >= 2
    assert "infrastructure_networks" in data
    assert len(data["infrastructure_networks"]) >= 3
    
    # Check hierarchy: District -> Site -> Building
    district = data["districts"][0]
    assert len(district["sites"]) >= 2
    site = district["sites"][0]
    assert len(site["buildings"]) >= 1
    building = site["buildings"][0]
    assert building["building_id"] == "BLD-HQ-01"
    assert building["has_detailed_bim"] is True

def test_city_building_lookup():
    response = client.get("/api/v1/city/buildings/BLD-HQ-01")
    assert response.status_code == 200
    data = response.json()
    assert data["building_id"] == "BLD-HQ-01"
    assert data["typology"] == "Commercial"
    assert data["bim_model_id"] == "sample-office-twin"

def test_sustainability_comprehensive_intelligence_endpoint():
    response = client.get("/api/v1/sustainability/report?target_entity_id=sample-office-twin&level=building")
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    recs = data["recommendations"]
    assert len(recs) >= 5
    
    categories = {r["category"] for r in recs}
    assert "environmental_sustainability" in categories
    assert "geotechnical_suitability" in categories
    assert "infrastructure_resilience" in categories
    assert "urban_planning" in categories
    assert "lifecycle_future_risk" in categories
    
    for r in recs:
        assert r["id"].startswith("REC-")
        assert r["evidence"]
        assert r["explanation"]
        assert r["proposed_intervention"]
        assert len(r["data_sources"]) > 0
        assert r["validation_requirements"]

def test_scenario_comparison_endpoint():
    response = client.get("/api/v1/scenarios/compare?building_id=sample-office-twin&time_horizon=2026")
    assert response.status_code == 200
    data = response.json()
    assert "baseline_scenario" in data
    assert len(data["alternative_scenarios"]) == 4
    
    baseline = data["baseline_scenario"]
    assert baseline["operational_energy_kwh_m2_yr"]["provenance_type"] == "SIMULATED"
    assert baseline["embodied_carbon_kg_co2e_m2"]["provenance_type"] == "ASSUMED"
    
    # Check horizon 2050 climate amplification
    response_2050 = client.get("/api/v1/scenarios/compare?building_id=sample-office-twin&time_horizon=2050")
    assert response_2050.status_code == 200
    data_2050 = response_2050.json()
    assert data_2050["baseline_scenario"]["time_horizon_years"] == 2050
    assert data_2050["baseline_scenario"]["operational_energy_kwh_m2_yr"]["value"] > baseline["operational_energy_kwh_m2_yr"]["value"]

def test_ml_energy_prediction_endpoint():
    response = client.get("/api/v1/ml/energy-prediction?model_id=sample-office-twin")
    assert response.status_code == 200
    data = response.json()
    assert data["applicability_status"] in ["WITHIN_DOMAIN", "OUTSIDE_DOMAIN"]
    assert data["heating_load_kwh_m2"] is not None
    assert data["cooling_load_kwh_m2"] is not None
    assert data["total_thermal_load_kwh_m2"] > 0
    assert "X1" in data["features"]
    assert "X2" in data["features"]
    assert "X5" in data["features"]
    assert data["evaluation_metrics"]["r2_score_heating"] >= 0.98

def test_pareto_optimization_endpoint():
    response = client.get("/api/v1/ml/pareto-optimization?budget_inr=500000")
    assert response.status_code == 200
    data = response.json()
    assert len(data["pareto_solutions"]) >= 2
    for sol in data["pareto_solutions"]:
        assert sol["capital_cost_inr"] <= 500000 * 1.3
        assert sol["carbon_reduction_pct"] > 0
        assert sol["energy_savings_pct"] > 0
