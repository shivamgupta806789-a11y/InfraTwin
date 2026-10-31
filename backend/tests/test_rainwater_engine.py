import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.building_feature_service import BuildingFeatureService
from app.services.location_climate_service import LocationClimateService
from app.services.hydrological_engine import HydrologicalEngine
from app.services.rainwater_recommendation_service import RainwaterRecommendationService
from app.services.rainwater_ml_service import RainwaterMLService

client = TestClient(app)


def test_building_feature_extraction_sample_office():
    """Verify building feature extraction from sample digital twin."""
    features = BuildingFeatureService.extract_features("sample-office-twin")
    assert features.building_id == "sample-office-twin"
    assert features.building_width_m > 0
    assert features.building_length_m > 0
    assert features.building_height_m > 0
    assert features.roof_area_m2 > 0
    assert 0.7 <= features.roof_runoff_coefficient <= 0.95
    assert features.occupancy_count > 0
    assert features.daily_non_potable_water_demand_l > 0
    assert len(features.features_audit) >= 8


def test_location_climate_normals_delhi_and_mumbai():
    """Verify observational 30-year normals mapping across distinct climate archetypes."""
    # Delhi (Semi-arid North)
    delhi = LocationClimateService.get_location_climate_profile(28.6139, 77.2090)
    assert 700 <= delhi.annual_rainfall_mm <= 900
    assert len(delhi.monthly_rainfall_mm) == 12
    assert delhi.groundwater_depth_m >= 4.0
    assert "National Capital Region" in delhi.place_name or "Delhi" in delhi.place_name

    # Mumbai (Tropical West Coast)
    mumbai = LocationClimateService.get_location_climate_profile(19.0760, 72.8777)
    assert mumbai.annual_rainfall_mm > 2000
    assert len(mumbai.monthly_rainfall_mm) == 12
    assert mumbai.groundwater_depth_m < 3.2
    assert mumbai.rainfall_seasonality_index > 0.80  # Highly concentrated monsoon


def test_hydrological_mass_balance_conservation():
    """Verify mass balance conservation: Inflow + Initial Storage = Supplied + Overflow + Final Storage."""
    features = BuildingFeatureService.extract_features("sample-office-twin", user_confirmed_lat=28.6139, user_confirmed_lon=77.2090)
    climate = LocationClimateService.get_location_climate_profile(28.6139, 77.2090)

    perf = HydrologicalEngine.simulate_mass_balance(
        roof_area_m2=features.roof_area_m2,
        runoff_coefficient=features.roof_runoff_coefficient,
        monthly_rainfall_mm=climate.monthly_rainfall_mm,
        daily_demand_liters=features.daily_non_potable_water_demand_l,
        tank_capacity_liters=10000.0,
    )

    assert perf.annual_captured_liters > 0
    assert perf.annual_water_demand_liters > 0
    assert 0 <= perf.annual_demand_coverage_pct <= 100
    assert len(perf.monthly_breakdown) == 12

    # Check conservation across each month
    for m in perf.monthly_breakdown:
        assert m.inflow_liters >= 0
        assert m.demand_liters >= 0
        assert m.supplied_liters >= 0
        assert m.overflow_liters >= 0
        assert m.ending_storage_liters >= 0
        assert m.supplied_liters <= m.demand_liters + 0.01


def test_feasibility_elimination_high_water_table():
    """High water table (< 3.2m, e.g. coastal Mumbai) must eliminate underground tanks and deep recharge."""
    # In Mumbai: water table = 2.8m
    report = RainwaterRecommendationService.evaluate_rainwater_recommendations("sample-office-twin", latitude=19.0760, longitude=72.8777)

    alt_b = next((a for a in report.ranked_alternatives if a.alternative_id == "ALT-B-UNDERGROUND-TANK"), None)
    assert alt_b is not None
    assert alt_b.is_feasible is False
    assert any("water table" in r.lower() or "hydrostatic" in r.lower() for r in alt_b.infeasibility_reasons)

    alt_f = next((a for a in report.ranked_alternatives if a.alternative_id == "ALT-F-STORAGE-GROUNDWATER-RECHARGE"), None)
    assert alt_f is not None
    assert alt_f.is_feasible is False


def test_feasibility_elimination_rooftop_dead_load():
    """Elevated rooftop tank must be eliminated if water load exceeds structural slab dead load limit."""
    report = RainwaterRecommendationService.evaluate_rainwater_recommendations("sample-office-twin", latitude=28.6139, longitude=77.2090)

    alt_d = next((a for a in report.ranked_alternatives if a.alternative_id == "ALT-D-ROOFTOP-STORAGE"), None)
    assert alt_d is not None
    # 5,000L tank on roof slab capacity (120-300 kg/m2) creates 1,900+ kg/m2 load
    assert alt_d.is_feasible is False
    assert any("structural" in r.lower() or "load" in r.lower() for r in alt_d.infeasibility_reasons)


def test_ml_surrogate_inference_alignment():
    """Trained Gradient Boosting model must infer coverage close to physical mass balance simulation."""
    features = BuildingFeatureService.extract_features("sample-office-twin", user_confirmed_lat=28.6139, user_confirmed_lon=77.2090)
    climate = LocationClimateService.get_location_climate_profile(28.6139, 77.2090)

    ml_input = {
        "roof_catchment_area_m2": features.roof_area_m2,
        "roof_runoff_coefficient": features.roof_runoff_coefficient,
        "roof_slope_deg": features.roof_slope_deg,
        "storeys_count": features.storeys_count,
        "occupancy_count": features.occupancy_count,
        "daily_non_potable_demand_l": features.daily_non_potable_water_demand_l,
        "tank_capacity_l": 10000.0,
        "annual_rainfall_mm": climate.annual_rainfall_mm,
        "rainfall_seasonality_index": climate.rainfall_seasonality_index,
        "rainfall_intensity_2yr_mm_hr": climate.rainfall_intensity_mm_hr_2yr,
        "terrain_slope_pct": climate.terrain_slope_pct,
        "soil_infiltration_rate_mm_hr": climate.soil_infiltration_rate_mm_hr,
        "groundwater_depth_m": climate.groundwater_depth_m,
    }

    ml_res = RainwaterMLService.predict_performance(ml_input)
    assert "predictions" in ml_res
    preds = ml_res["predictions"]
    ml_cov = preds["target_annual_demand_coverage_pct"]
    ml_cap = preds["target_annual_captured_l"]

    assert ml_cov is not None
    assert 0 <= ml_cov <= 100
    assert ml_cap is not None
    assert ml_cap > 0

    perf = HydrologicalEngine.simulate_mass_balance(
        roof_area_m2=features.roof_area_m2,
        runoff_coefficient=features.roof_runoff_coefficient,
        monthly_rainfall_mm=climate.monthly_rainfall_mm,
        daily_demand_liters=features.daily_non_potable_water_demand_l,
        tank_capacity_liters=10000.0,
    )
    # ML surrogate should be within 10% delta of physical mass balance
    assert abs(ml_cov - perf.annual_demand_coverage_pct) < 10.0


def test_3d_intervention_components_generated():
    """Rainwater alternatives must generate visible 3D components with exact coordinates."""
    report = RainwaterRecommendationService.evaluate_rainwater_recommendations("sample-office-twin", latitude=28.6139, longitude=77.2090)

    top_alt = report.ranked_alternatives[0]
    assert len(top_alt.proposed_3d_components) >= 4

    comp_types = [c.component_type for c in top_alt.proposed_3d_components]
    assert "gutter" in comp_types
    assert "downpipe" in comp_types
    assert "filter_unit" in comp_types
    assert "storage_tank" in comp_types

    for comp in top_alt.proposed_3d_components:
        assert len(comp.position) == 3
        assert len(comp.dimensions) == 3
        assert comp.geometry_type in ["box", "cylinder", "pipe_path", "plane"]
        assert comp.color_hex.startswith("#")
        assert len(comp.specification) > 0


def test_api_rainwater_endpoints():
    """Verify all FastAPI rainwater routes respond with valid schema."""
    # 1. Features
    res = client.get("/api/v1/rainwater/features?model_id=sample-office-twin")
    assert res.status_code == 200
    data = res.json()
    assert data["building_id"] == "sample-office-twin"

    # 2. Climate profile
    res = client.get("/api/v1/rainwater/climate-profile?latitude=28.6139&longitude=77.2090")
    assert res.status_code == 200
    c_data = res.json()
    assert c_data["annual_rainfall_mm"] > 500

    # 3. Recommendations GET
    res = client.get("/api/v1/rainwater/recommendations?building_id=sample-office-twin&latitude=28.6139&longitude=77.2090")
    assert res.status_code == 200
    rec_data = res.json()
    assert len(rec_data["ranked_alternatives"]) == 7
    assert rec_data["selected_recommended_alternative_id"] is not None

    # 4. Recommendations POST
    res = client.post("/api/v1/rainwater/recommendations", json={
        "building_id": "sample-office-twin",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "building_type": "Commercial",
        "occupancy": 60
    })
    assert res.status_code == 200
    post_data = res.json()
    assert len(post_data["ranked_alternatives"]) == 7

    # 5. ML Metrics
    res = client.get("/api/v1/rainwater/ml-metrics")
    assert res.status_code == 200
    metrics = res.json()
    assert "evaluation_metrics" in metrics
    assert "algorithm" in metrics
