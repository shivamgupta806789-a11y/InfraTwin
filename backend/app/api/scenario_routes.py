from fastapi import APIRouter, Query, HTTPException, status
from app.models.scenarios import ScenarioComparisonReport
from app.services.scenario_service import ScenarioEvaluationService

router = APIRouter(prefix="/api/v1/scenarios", tags=["Future Design Intelligence"])


@router.get("/compare", response_model=ScenarioComparisonReport)
async def compare_design_scenarios(
    building_id: str = Query(default="sample-office-twin", description="Target building ID"),
    time_horizon: int = Query(default=2026, description="Evaluation horizon year: 2026, 2035, or 2050")
):
    """
    Evaluates multi-scenario design alternatives (Baseline vs Energy Opt vs Low-Carbon vs Flood-Resilient vs 2050 Extreme)
    with explicit metric provenance (MEASURED, SIMULATED, PREDICTED, ASSUMED).
    """
    if time_horizon not in [2026, 2035, 2050]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="time_horizon must be one of [2026, 2035, 2050]."
        )
    try:
        return ScenarioEvaluationService.evaluate_building_scenarios(
            building_id=building_id,
            time_horizon=time_horizon
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate design scenarios: {str(e)}"
        )
