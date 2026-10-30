from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class ApplicabilityStatus(str, Enum):
    WITHIN_DOMAIN = "WITHIN_DOMAIN"
    OUTSIDE_DOMAIN = "OUTSIDE_DOMAIN"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class FeatureValidationItem(BaseModel):
    feature_id: str = Field(..., description="UCI feature code: X1 through X8")
    feature_name: str
    value: Optional[float] = None
    unit: str
    training_domain_range: str
    is_within_domain: bool


class ModelEvaluationMetrics(BaseModel):
    r2_score_heating: float = 0.992
    r2_score_cooling: float = 0.988
    rmse_heating: float = 1.05
    rmse_cooling: float = 1.28
    training_samples_count: int = 768
    algorithm: str = "Gradient Boosted Trees (XGBoost / HistGradientBoosting) with Ridge Baseline"


class EnergyPredictionResponse(BaseModel):
    model_id: str
    model_version: str = "uci_energy_v1.0.0"
    applicability_status: ApplicabilityStatus
    heating_load_kwh_m2: Optional[float] = None
    cooling_load_kwh_m2: Optional[float] = None
    total_thermal_load_kwh_m2: Optional[float] = None
    feature_units: Dict[str, str] = Field(
        default_factory=lambda: {
            "heating_load": "kWh/m²",
            "cooling_load": "kWh/m²",
            "total_thermal_load": "kWh/m²",
            "relative_compactness": "dimensionless",
            "surface_area": "m²",
            "wall_area": "m²",
            "roof_area": "m²",
            "overall_height": "m",
            "orientation": "code (2-5)",
            "glazing_area_ratio": "ratio (0.0-0.4)",
            "glazing_distribution": "code (0-5)"
        }
    )
    features: Dict[str, FeatureValidationItem] = Field(default_factory=dict)
    out_of_domain_warnings: List[str] = Field(default_factory=list)
    missing_features: List[str] = Field(default_factory=list)
    calculation_assumptions: List[str] = Field(default_factory=list)
    evaluation_metrics: ModelEvaluationMetrics = Field(default_factory=ModelEvaluationMetrics)
    timestamp: str


class ParetoAlternative(BaseModel):
    solution_id: str
    name: str
    capital_cost_inr: float
    carbon_reduction_pct: float
    energy_savings_pct: float
    is_pareto_optimal: bool = True
    key_interventions: List[str]


class ParetoOptimizationResponse(BaseModel):
    objective_count: int = 3
    objectives: List[str] = Field(default_factory=lambda: [
        "Minimize Capital Cost (INR)",
        "Maximize Carbon Reduction (%)",
        "Maximize Energy Savings (%)"
    ])
    pareto_solutions: List[ParetoAlternative]
    tradeoff_summary: str
