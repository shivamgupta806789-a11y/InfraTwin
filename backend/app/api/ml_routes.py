from fastapi import APIRouter, Query, HTTPException, status
from app.models.ml_energy import EnergyPredictionResponse, ParetoOptimizationResponse
from app.services.ml_prediction_service import MLEnergyPredictionService

router = APIRouter(prefix="/api/v1/ml", tags=["Machine Learning & Optimization"])


@router.get("/energy-prediction", response_model=EnergyPredictionResponse)
async def get_energy_prediction(
    model_id: str = Query(default="sample-office-twin", description="BIM Model ID")
):
    """
    Dual-target energy efficiency regression predicting Heating Load (Y1)
    and Cooling Load (Y2) in kWh/m² using UCI feature parameter extraction.
    """
    try:
        return MLEnergyPredictionService.predict_energy_loads(model_id=model_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute ML energy predictions: {str(e)}"
        )


@router.get("/pareto-optimization", response_model=ParetoOptimizationResponse)
async def get_pareto_optimization(
    budget_inr: float = Query(default=500000.0, ge=10000.0, description="Available budget limit in INR")
):
    """
    Computes multi-objective Pareto optimization solutions balancing
    Capital Cost vs Carbon Reduction vs Energy Savings.
    """
    try:
        return MLEnergyPredictionService.get_pareto_design_alternatives(budget_inr=budget_inr)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate Pareto optimization alternatives: {str(e)}"
        )
