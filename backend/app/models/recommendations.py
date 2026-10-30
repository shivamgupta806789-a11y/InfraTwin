from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.building import BuildingInput

class InterventionItem(BaseModel):
    id: str
    name: str
    category: str
    description: str
    cost_estimation_method: str
    unit_cost_description: str
    quantity: float
    quantity_unit: str
    estimated_cost_inr: float
    fits_budget: bool
    is_eligible: bool
    ineligibility_reason: Optional[str] = None
    rank: Optional[int] = None
    score: Optional[float] = None
    explanation: str
    limitations: List[str] = Field(default_factory=list)
    evidence_status: str

class RecommendationRequest(BuildingInput):
    preferred_categories: Optional[List[str]] = None

class RecommendationResponse(BaseModel):
    budget_inr: float
    available_interventions: List[InterventionItem]
    ranked_recommendations: List[InterventionItem]
    total_recommended_cost_inr: float
    remaining_budget_inr: float
    calculation_assumptions: List[str]
    warnings: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)

class CostBreakdownItem(BaseModel):
    id: str
    name: str
    quantity: float
    quantity_unit: str
    unit_rate_inr: float
    total_cost_inr: float
    formula: str
    assumptions: str

class ImpactEstimateItem(BaseModel):
    estimate_type: str
    metric: str
    value: Optional[float] = None
    unit: str
    is_estimated: bool
    calculation_method: str
    assumptions: List[str]
    source_provenance: str
    evidence_limitations: str
    missing_inputs: List[str] = Field(default_factory=list)

class EstimateRequest(BuildingInput):
    annual_electricity_kwh: Optional[float] = Field(
        default=None,
        ge=0,
        description="Optional measured annual electricity consumption in kWh for carbon footprint baseline."
    )
    grid_emission_factor_kg_per_kwh: Optional[float] = Field(
        default=0.716,
        ge=0,
        le=2.0,
        description="Grid emission factor in kg CO2e / kWh (default 0.716 per CEA India 2023 CO2 baseline database)."
    )

class EstimateResponse(BaseModel):
    selected_interventions: List[str]
    total_cost_inr: float
    budget_inr: float
    fits_budget: bool
    cost_breakdown: List[CostBreakdownItem]
    impact_estimates: List[ImpactEstimateItem]
    assumptions: List[str]
    missing_inputs: List[str]
