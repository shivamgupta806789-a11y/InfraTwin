import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.environmental import (
    GeoLocation,
    BuildingOrientation,
    EnvironmentalAnalysisRequest,
)
from app.services.environmental_service import EnvironmentalService

client = TestClient(app)


def test_get_climate_data_real_or_fallback():
    # New Delhi coordinates
    climate = EnvironmentalService.get_climate_data(28.6139, 77.2090)
    assert climate.climate_zone is not None
    assert -50.0 < climate.mean_temp_c < 60.0
    assert climate.solar_radiation_kwh_m2_day > 0.0
    assert climate.annual_rainfall_mm >= 0.0
    assert 0.0 <= climate.dominant_wind_direction_deg <= 360.0
    assert climate.dominant_wind_cardinal in ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    assert climate.elevation_m is not None
    assert "Open-Meteo" in climate.data_source or "Baseline" in climate.data_source


def test_site_context_resolution():
    loc = GeoLocation(latitude=28.6139, longitude=77.2090, city="New Delhi", country="India")
    site = EnvironmentalService.get_site_context(28.6139, 77.2090, loc)
    assert site.urban_density in ["High Density Urban", "Moderate Urban", "Suburban", "Rural"]
    assert 0.0 <= site.nearby_vegetation_pct <= 100.0
    assert len(site.nearby_water_bodies) > 0


def test_location_presets():
    presets = EnvironmentalService.get_location_presets()
    assert len(presets) >= 5
    cities = [p["city"] for p in presets]
    assert "New Delhi" in cities
    assert "Mumbai" in cities
    assert "London" in cities


def test_search_locations():
    results = EnvironmentalService.search_locations("Delhi")
    assert len(results) > 0
    assert "latitude" in results[0]
    assert "longitude" in results[0]


def test_analyze_environmental_suitability_service():
    req = EnvironmentalAnalysisRequest(
        location=GeoLocation(
            latitude=19.0760,
            longitude=72.8777,
            city="Mumbai",
            country="India",
        ),
        orientation=BuildingOrientation(
            azimuth_deg=90.0,
            cardinal_direction="East-Facing",
        ),
        building_params={
            "width_m": 20.0,
            "length_m": 15.0,
            "floors": 3,
            "floor_height_m": 3.2,
        },
    )
    res = EnvironmentalService.analyze_environmental_suitability(req)
    assert res.location.city == "Mumbai"
    assert res.climate.mean_temp_c > 0.0
    assert res.evaluation.solar_orientation_score >= 0.0
    assert res.evaluation.annual_rainwater_harvest_liters > 0.0
    assert res.evaluation.annual_solar_pv_kwh > 0.0
    assert len(res.recommendations) > 0
    assert len(res.disclaimers) >= 2

    for rec in res.recommendations:
        assert rec.id.startswith("env_rec_")
        assert len(rec.environmental_evidence) > 0
        assert len(rec.expected_benefit) > 0
        assert len(rec.data_source) > 0
        assert len(rec.limitations) > 0


def test_api_analyze_endpoint():
    payload = {
        "location": {
            "latitude": 28.6139,
            "longitude": 77.2090,
            "city": "New Delhi",
            "country": "India",
        },
        "orientation": {
            "azimuth_deg": 180.0,
            "cardinal_direction": "South-Facing",
        },
        "building_params": {
            "width_m": 16.0,
            "length_m": 12.0,
            "floors": 2,
            "floor_height_m": 3.0,
        },
    }
    response = client.post("/api/v1/environmental/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "climate" in data
    assert "site_context" in data
    assert "evaluation" in data
    assert len(data["recommendations"]) > 0


def test_api_presets_endpoint():
    response = client.get("/api/v1/environmental/presets")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5


def test_api_climate_endpoint():
    response = client.get("/api/v1/environmental/climate?latitude=28.6139&longitude=77.2090")
    assert response.status_code == 200
    data = response.json()
    assert "climate_zone" in data
    assert "mean_temp_c" in data
