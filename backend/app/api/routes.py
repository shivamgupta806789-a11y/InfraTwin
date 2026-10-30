from fastapi import APIRouter, HTTPException, status
from app.core.config import settings
from app.models.building import BuildingInput, BuildingValidationResponse, NormalizedBuilding
from app.models.recommendations import (
    RecommendationRequest,
    RecommendationResponse,
    EstimateRequest,
    EstimateResponse,
)
from app.services.recommendation_engine import RecommendationEngine
from app.services.impact_estimator import ImpactEstimator

router = APIRouter()

@router.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint to verify backend service status."""
    return {
        "status": "ok",
        "application_name": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

@router.post(
    "/api/v1/building/validate",
    response_model=BuildingValidationResponse,
    tags=["Building"]
)
async def validate_building(building: BuildingInput):
    """
    Authoritative server-side validation of building parameters.
    Computes spatial properties (roof area, gross floor area, wall area, WWR)
    and checks geometric plausibility.
    """
    roof_area = building.width_m * building.length_m
    total_height = building.floors * building.floor_height_m
    gross_floor_area = roof_area * building.floors
    total_wall_area = 2 * (building.width_m + building.length_m) * total_height
    window_area = building.window_count * 2.0
    wwr = (window_area / total_wall_area) if total_wall_area > 0 else 0.0

    warnings = []
    if wwr > 0.40:
        warnings.append(
            f"High Window-to-Wall Ratio ({wwr:.1%}). ECBC recommends WWR <= 40% for energy efficiency in Indian climates."
        )
    if building.floors > 10 and building.floor_height_m < 3.0:
        warnings.append("Floor height is below standard commercial ceiling allowances (>= 3.0m recommended).")
    if building.budget_inr == 0:
        warnings.append("Zero budget specified. No paid capital improvements can be implemented.")

    normalized = NormalizedBuilding(
        width_m=building.width_m,
        length_m=building.length_m,
        floor_height_m=building.floor_height_m,
        floors=building.floors,
        window_count=building.window_count,
        budget_inr=building.budget_inr,
        selected_interventions=building.selected_interventions,
        roof_area_m2=round(roof_area, 2),
        gross_floor_area_m2=round(gross_floor_area, 2),
        total_height_m=round(total_height, 2),
        total_wall_area_m2=round(total_wall_area, 2),
        estimated_window_wall_ratio=round(wwr, 3),
    )

    return BuildingValidationResponse(
        is_valid=True,
        normalized=normalized,
        warnings=warnings,
        errors=[]
    )

@router.post(
    "/api/v1/recommendations",
    response_model=RecommendationResponse,
    tags=["Recommendations"]
)
async def get_recommendations(request: RecommendationRequest):
    """
    Generates deterministic, transparent, budget-aware recommendations.
    Evaluates individual intervention costs against the budget, ranks feasible
    options using documented criteria, and builds an optimal recommended package.
    """
    try:
        response = RecommendationEngine.evaluate_interventions(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating recommendations: {str(e)}"
        )

@router.post(
    "/api/v1/estimate",
    response_model=EstimateResponse,
    tags=["Impact & Cost Estimation"]
)
async def estimate_design(request: EstimateRequest):
    """
    Calculates detailed itemized cost breakdown for selected interventions
    and computes only defensible, documented impact metrics (e.g. baseline emissions
    from provided kWh, solar PV yield). Transparently marks missing inputs as unestimated.
    """
    try:
        response = ImpactEstimator.estimate_impacts(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error estimating design impacts: {str(e)}"
        )
