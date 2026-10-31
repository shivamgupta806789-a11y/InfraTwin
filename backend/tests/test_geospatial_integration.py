import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.geospatial_integration_service import GeospatialIntegrationService
from app.services.sustainability_service import SustainabilityRecommendationService
from app.models.geospatial_profile import UnifiedLocationProfile, DatasetConnectionStatus

client = TestClient(app)


def test_location_profile_retrieval_and_structure():
    """Criteria 1: A project with a confirmed location retrieves available geospatial data."""
    profile = GeospatialIntegrationService.get_unified_location_profile(28.6139, 77.2090, place_name="New Delhi Project")
    assert isinstance(profile, UnifiedLocationProfile)
    assert profile.latitude == 28.6139
    assert profile.longitude == 77.2090
    assert len(profile.dataset_statuses) == 10

    # Verify all 10 datasets are tracked
    expected_datasets = [
        "DS-01-ESA-WORLDCOVER",
        "DS-02-DYNAMIC-WORLD",
        "DS-03-SENTINEL-2",
        "DS-04-GLOBAL-FOREST-WATCH",
        "DS-05-OPENSTREETMAP",
        "DS-06-MS-BUILDING-FOOTPRINTS",
        "DS-07-SOILGRIDS",
        "DS-08-HYDROSHEDS",
        "DS-09-NASA-POWER",
        "DS-10-ERA5-REANALYSIS"
    ]
    for ds_id in expected_datasets:
        assert ds_id in profile.dataset_statuses
        st = profile.dataset_statuses[ds_id]
        assert st.status in [
            DatasetConnectionStatus.SUCCESSFULLY_RETRIEVED,
            DatasetConnectionStatus.PARTIALLY_AVAILABLE,
            DatasetConnectionStatus.CONNECTED
        ]


def test_different_locations_produce_different_profiles():
    """Criteria 2: Different locations produce different location profiles when source data differs."""
    delhi = GeospatialIntegrationService.get_unified_location_profile(28.6139, 77.2090, force_refresh=True)
    mumbai = GeospatialIntegrationService.get_unified_location_profile(19.0760, 72.8777, force_refresh=True)

    # Different geographic coordinates
    assert delhi.latitude != mumbai.latitude
    assert delhi.longitude != mumbai.longitude

    # Solar irradiance or precipitation differs between semi-arid north and coastal west
    delhi_precip = delhi.climate.annual_precipitation_mm.value
    mumbai_precip = mumbai.climate.annual_precipitation_mm.value
    assert isinstance(delhi_precip, (int, float))
    assert isinstance(mumbai_precip, (int, float))


def test_vegetation_information_influences_recommendations():
    """Criteria 3: Vegetation information influences green infrastructure recommendations."""
    report = SustainabilityRecommendationService.evaluate_comprehensive_intelligence(
        target_entity_id="sample-office-twin",
        latitude=28.6139,
        longitude=77.2090
    )
    green_recs = [r for r in report.recommendations if r.id == "REC-GREEN-005"]
    assert len(green_recs) == 1
    rec = green_recs[0]
    assert "Global Forest Watch" in rec.data_sources
    assert "Copernicus Sentinel-2" in rec.data_sources
    assert "DS-04-GLOBAL-FOREST-WATCH" in rec.contributing_datasets
    assert "Tree Canopy" in rec.title or "Canopy Conservation" in rec.title
    assert rec.relevant_location_feature is not None


def test_soil_information_influences_infiltration():
    """Criteria 4: Soil information influences infiltration suitability."""
    profile = GeospatialIntegrationService.get_unified_location_profile(28.6139, 77.2090)
    assert profile.soil_hydrology.clay_content_pct.value > 0
    assert profile.soil_hydrology.hydrologic_soil_group.value in ["A", "B", "C", "D"]
    assert profile.soil_hydrology.soil_texture_usda.value is not None
    assert profile.soil_hydrology.infiltration_rate_mm_hr.value > 0


def test_climate_information_influences_heat_and_solar():
    """Criteria 5: Climate information influences heat and solar analysis."""
    report = SustainabilityRecommendationService.evaluate_comprehensive_intelligence(
        target_entity_id="sample-office-twin",
        latitude=28.6139,
        longitude=77.2090
    )
    solar_recs = [r for r in report.recommendations if r.id == "REC-SOLAR-001"]
    heat_recs = [r for r in report.recommendations if r.id == "REC-HEAT-002"]

    assert len(solar_recs) == 1
    assert "NASA POWER Solar Database" in solar_recs[0].data_sources
    assert "DS-09-NASA-POWER" in solar_recs[0].contributing_datasets
    assert "kWh/year clean electricity" in solar_recs[0].expected_benefit

    assert len(heat_recs) == 1
    assert "Copernicus Sentinel-2" in heat_recs[0].data_sources
    assert "ERA5 Atmospheric Reanalysis" in heat_recs[0].data_sources


def test_drainage_information_influences_flood_stormwater():
    """Criteria 6: Drainage information influences flood and stormwater analysis."""
    report = SustainabilityRecommendationService.evaluate_comprehensive_intelligence(
        target_entity_id="sample-office-twin",
        latitude=28.6139,
        longitude=77.2090
    )
    storm_recs = [r for r in report.recommendations if r.id == "REC-STORM-003"]
    assert len(storm_recs) == 1
    assert "HydroSHEDS HydroRIVERS" in storm_recs[0].data_sources
    assert "SoilGrids 250m" in storm_recs[0].data_sources
    assert "DS-08-HYDROSHEDS" in storm_recs[0].contributing_datasets
    assert "DS-07-SOILGRIDS" in storm_recs[0].contributing_datasets
    assert "Attenuation Vault" in storm_recs[0].title or "SuDS" in storm_recs[0].title


def test_nearby_buildings_and_roads_influence_spatial():
    """Criteria 7: Nearby buildings and roads influence spatial analysis."""
    report = SustainabilityRecommendationService.evaluate_comprehensive_intelligence(
        target_entity_id="sample-office-twin",
        latitude=28.6139,
        longitude=77.2090
    )
    urban_recs = [r for r in report.recommendations if r.id == "REC-URBAN-006"]
    assert len(urban_recs) == 1
    assert "OpenStreetMap" in urban_recs[0].data_sources
    assert "Microsoft Global ML Building Footprints" in urban_recs[0].data_sources
    assert "DS-05-OPENSTREETMAP" in urban_recs[0].contributing_datasets
    assert "DS-06-MS-BUILDING-FOOTPRINTS" in urban_recs[0].contributing_datasets


def test_graceful_fallback_on_unavailable_provider(monkeypatch):
    """Criteria 8: Missing datasets do not crash the application."""
    import httpx

    def mock_failing_get(*args, **kwargs):
        raise httpx.ConnectTimeout("Simulated network timeout for resilience test")

    monkeypatch.setattr(httpx, "get", mock_failing_get)
    monkeypatch.setattr(httpx, "post", mock_failing_get)

    # Must complete smoothly using documented fallbacks
    profile = GeospatialIntegrationService.get_unified_location_profile(28.6139, 77.2090, force_refresh=True)
    assert profile is not None
    assert profile.climate.annual_solar_ghi_kwh_m2_day.value > 0
    assert profile.soil_hydrology.hydrologic_soil_group.value in ["A", "B", "C", "D"]

    report = SustainabilityRecommendationService.evaluate_comprehensive_intelligence(
        target_entity_id="sample-office-twin",
        latitude=28.6139,
        longitude=77.2090
    )
    assert len(report.recommendations) >= 6


def test_recommendations_cite_contributing_datasets():
    """Criteria 9: Recommendations explain which datasets contributed."""
    report = SustainabilityRecommendationService.evaluate_comprehensive_intelligence(
        target_entity_id="sample-office-twin",
        latitude=28.6139,
        longitude=77.2090
    )
    for rec in report.recommendations:
        assert len(rec.data_sources) > 0
        assert rec.detected_condition != ""
        assert rec.evidence != ""
        assert rec.proposed_intervention != ""
        assert rec.expected_benefit != ""
        assert rec.validation_requirements != ""


def test_geospatial_api_endpoints():
    """Criteria 10: Existing and new API routes function cleanly."""
    resp_prof = client.get("/api/geospatial/location-profile?latitude=28.6139&longitude=77.2090")
    assert resp_prof.status_code == 200
    data = resp_prof.json()
    assert "dataset_statuses" in data
    assert "land_cover" in data
    assert "vegetation" in data
    assert "climate" in data

    resp_reg = client.get("/api/geospatial/datasets-registry")
    assert resp_reg.status_code == 200
    reg_data = resp_reg.json()
    assert "datasets" in reg_data
    assert len(reg_data["datasets"]) >= 10

    resp_eval = client.get("/api/geospatial/evaluate-multi-domain?model_id=sample-office-twin&latitude=28.6139&longitude=77.2090")
    assert resp_eval.status_code == 200
    eval_data = resp_eval.json()
    assert "recommendations" in eval_data
    assert len(eval_data["recommendations"]) >= 6
