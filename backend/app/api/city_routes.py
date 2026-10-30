from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, status
from app.models.city import CityModel, CityBuildingSummary
from app.services.city_service import CityService

router = APIRouter(prefix="/api/v1/city", tags=["City-Scale Digital Twin"])


@router.get("/model", response_model=CityModel)
async def get_city_model():
    """
    Returns the hierarchical city-scale spatial model:
    CITY -> DISTRICT -> SITE -> BUILDING -> STOREY.
    Includes infrastructure networks (roads, power, drainage).
    """
    try:
        return CityService.get_default_city_model()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load city-scale model: {str(e)}"
        )


@router.get("/buildings/{building_id}", response_model=CityBuildingSummary)
async def get_city_building(building_id: str):
    """
    Retrieves summary geometry, typology, and BIM linkage for a specific building in the city dataset.
    """
    bld = CityService.get_building_by_id(building_id)
    if not bld:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Building '{building_id}' not found in city dataset."
        )
    return bld
