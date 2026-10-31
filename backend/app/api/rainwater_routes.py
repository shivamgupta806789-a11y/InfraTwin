from typing import Optional
from fastapi import APIRouter, Query, HTTPException, status, Body
from pydantic import BaseModel, Field

from app.models.rainwater import (
    BuildingUnifiedFeatures,
    LocationClimateProfile,
    RainwaterRecommendationReport,
)
from app.services.building_feature_service import BuildingFeatureService
from app.services.location_climate_service import LocationClimateService
from app.services.rainwater_recommendation_service import RainwaterRecommendationService
from app.services.rainwater_ml_service import RainwaterMLService

router = APIRouter(prefix="/api/v1/rainwater", tags=["Rainwater Management & 3D Interventions"])


class RainwaterAnalysisRequest(BaseModel):
    model_id: str = Field(default="sample-office-twin")
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    building_type: Optional[str] = Field(default=None)
    occupancy: Optional[int] = Field(default=None, ge=1)
    is_user_confirmed_location: bool = Field(default=True)


@router.get("/features", response_model=BuildingUnifiedFeatures)
async def get_building_features(
    model_id: str = Query(default="sample-office-twin"),
    latitude: Optional[float] = Query(default=None),
    longitude: Optional[float] = Query(default=None),
    building_type: Optional[str] = Query(default=None),
    occupancy: Optional[int] = Query(default=None),
):
    """
    Extracts verified building envelope, roof catchment, occupancy, and water demand features.
    Every feature carries provenance, confidence, and explicit assumption logs.
    """
    try:
        return BuildingFeatureService.extract_features(
            model_id=model_id,
            user_confirmed_lat=latitude,
            user_confirmed_lon=longitude,
            user_confirmed_type=building_type,
            user_confirmed_occupancy=occupancy,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract building features: {str(e)}"
        )


@router.get("/climate-profile", response_model=LocationClimateProfile)
async def get_climate_profile(
    latitude: float = Query(default=28.6139, ge=-90.0, le=90.0),
    longitude: float = Query(default=77.2090, ge=-180.0, le=180.0),
    place_name: Optional[str] = Query(default=None),
    is_confirmed: bool = Query(default=True),
):
    """
    Retrieves authentic 30-year climatological normal data (1991-2020),
    including 12-month precipitation, 2-yr/10-yr storm intensities, and hydrogeological factors.
    """
    try:
        return LocationClimateService.get_location_climate_profile(
            latitude=latitude,
            longitude=longitude,
            place_name=place_name,
            is_user_confirmed=is_confirmed,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve location climate profile: {str(e)}"
        )


@router.get("/recommendations", response_model=RainwaterRecommendationReport)
async def get_rainwater_recommendations(
    model_id: str = Query(default="sample-office-twin"),
    latitude: Optional[float] = Query(default=None),
    longitude: Optional[float] = Query(default=None),
    building_type: Optional[str] = Query(default=None),
    occupancy: Optional[int] = Query(default=None),
    is_confirmed: bool = Query(default=True),
):
    """
    Generates building-specific rainwater management recommendations across 7 candidate design configurations.
    Simulates monthly hydrological mass balance, validates via ML models,
    ranks alternatives by multi-criteria score, and generates 3D intervention components.
    """
    try:
        return RainwaterRecommendationService.evaluate_rainwater_recommendations(
            model_id=model_id,
            latitude=latitude,
            longitude=longitude,
            building_type=building_type,
            occupancy=occupancy,
            user_confirmed_location=is_confirmed,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate rainwater recommendations: {str(e)}"
        )


@router.post("/recommendations", response_model=RainwaterRecommendationReport)
async def post_rainwater_recommendations(
    request: RainwaterAnalysisRequest = Body(...)
):
    """
    Evaluates rainwater design alternatives with confirmed user parameters.
    """
    try:
        return RainwaterRecommendationService.evaluate_rainwater_recommendations(
            model_id=request.model_id,
            latitude=request.latitude,
            longitude=request.longitude,
            building_type=request.building_type,
            occupancy=request.occupancy,
            user_confirmed_location=request.is_user_confirmed_location,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate rainwater recommendations: {str(e)}"
        )


@router.get("/ml-metrics")
async def get_ml_metrics():
    """
    Returns supervised ML evaluation metrics (MAE, RMSE, R²), feature columns,
    and training dataset metadata.
    """
    try:
        bundle = RainwaterMLService.get_loaded_bundle()
        return {
            "model_version": bundle["model_version"],
            "algorithm": bundle["algorithm"],
            "training_dataset_records": bundle["training_dataset_records"],
            "training_timestamp": bundle["training_timestamp"],
            "evaluation_metrics": bundle["evaluation_metrics"],
            "feature_columns": bundle["feature_columns"],
            "feature_domains": bundle["feature_domains"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load ML metrics: {str(e)}"
        )
