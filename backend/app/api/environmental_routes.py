from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Query, HTTPException, status

from app.models.environmental import (
    EnvironmentalAnalysisRequest,
    EnvironmentalAnalysisResponse,
    ClimateData,
)
from app.services.environmental_service import EnvironmentalService

router = APIRouter(prefix="/api/v1/environmental", tags=["Geolocation & Environmental Intelligence"])


@router.post("/analyze", response_model=EnvironmentalAnalysisResponse)
async def analyze_environmental_suitability(request: EnvironmentalAnalysisRequest):
    """
    Evaluates building design suitability against geographical location and local microclimate.
    Retrieves real meteorological data (Open-Meteo), terrain elevation, and geospatial context (OpenStreetMap),
    evaluates solar alignment, daylight, wind ventilation, and rainwater harvesting potential,
    and returns evidence-backed recommendations.
    """
    try:
        return EnvironmentalService.analyze_environmental_suitability(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Environmental analysis failed: {str(e)}",
        )


@router.get("/geocode", response_model=List[Dict[str, Any]])
async def search_locations(query: str = Query(..., min_length=2, description="Place, city, or address query")):
    """
    Geocoding search powered by OpenStreetMap Nominatim with safe rate limiting and preset fallbacks.
    """
    try:
        return EnvironmentalService.search_locations(query)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Geocoding lookup failed: {str(e)}",
        )


@router.get("/presets", response_model=List[Dict[str, Any]])
async def get_location_presets():
    """
    Returns curated preset locations spanning diverse Köppen climate zones for instant exploration.
    """
    return EnvironmentalService.get_location_presets()


@router.get("/climate", response_model=ClimateData)
async def get_climate_data(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
):
    """
    Returns verified meteorological indicators (temperature, solar radiation, wind, precipitation) for given coordinates.
    """
    try:
        return EnvironmentalService.get_climate_data(latitude, longitude)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Climate data retrieval failed: {str(e)}",
        )
