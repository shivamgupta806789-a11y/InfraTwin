from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.building import BuildingInput
from app.models.rainwater import Intervention3DComponent

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

class StructuredIntervention(BaseModel):
    intervention_id: str
    recommendation_id: str
    intervention_type: str
    target_element_ids: List[str] = Field(default_factory=list)
    target_floor: Optional[str] = None
    geometry_parameters: Dict[str, Any] = Field(default_factory=dict)
    material_parameters: Dict[str, Any] = Field(default_factory=dict)
    world_position: List[float] = Field(default_factory=list, description="[x, y, z] anchor in IFC coordinate space")
    dimensions: List[float] = Field(default_factory=list, description="[width, height, depth]")
    orientation: Dict[str, float] = Field(default_factory=dict, description="tilt_deg, azimuth_deg")
    estimated_cost: float
    expected_benefit: Dict[str, Any] = Field(default_factory=dict)
    calculation_method: str
    assumptions: List[str] = Field(default_factory=list)
    validation_status: str = Field(default="VALIDATED", description="'VALIDATED' | 'REJECTED' | 'PARTIAL'")
    rejection_reason: Optional[str] = None
    components_3d: List[Intervention3DComponent] = Field(default_factory=list)

class AppliedInterventionsRequest(BaseModel):
    model_id: Optional[str] = None
    selected_intervention_ids: List[str]
    budget_inr: Optional[float] = 1000000.0
    width_m: Optional[float] = None
    length_m: Optional[float] = None
    floors: Optional[int] = None
    floor_height_m: Optional[float] = None
    window_count: Optional[int] = None

class AppliedInterventionsResponse(BaseModel):
    model_id: Optional[str] = None
    interventions: List[StructuredIntervention]
    total_applied_cost: float
    applied_count: int
    rejected_count: int
    diagnostic_logs: List[str] = Field(default_factory=list)
    provenance: str = "Deterministic Engineering & Geometry Placement Validation Pipeline"

