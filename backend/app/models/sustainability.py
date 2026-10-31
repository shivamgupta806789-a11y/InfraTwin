from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ComprehensiveRecommendation(BaseModel):
    id: str = Field(..., description="Unique recommendation ID, e.g. 'REC-ENV-001'")
    category: str = Field(
        ...,
        description="'environmental_sustainability', 'geotechnical_suitability', 'infrastructure_resilience', 'urban_planning', or 'lifecycle_future_risk'"
    )
    category_title: str = Field(..., description="Display title of the pillar category")
    hierarchical_level: str = Field(
        ...,
        description="'city', 'district', 'site', 'building', or 'element'"
    )
    target_entity_id: Optional[str] = Field(default=None, description="Affected building ID, element GUID, or site ID")
    priority: str = Field(..., description="'critical', 'high', 'medium', or 'low'")
    title: str
    detected_condition: str
    evidence: str
    explanation: str
    proposed_intervention: str
    expected_benefit: str
    estimated_cost_inr: Optional[float] = None
    time_horizon: str = Field(..., description="'immediate', 'near_term_2026', 'mid_term_2035', or 'long_term_2050'")
    confidence: str = Field(..., description="'high', 'medium', or 'insufficient_data'")
    data_sources: List[str]
    relevant_building_feature: Optional[str] = Field(default=None, description="Specific architectural, geometric, or structural element addressed")
    relevant_location_feature: Optional[str] = Field(default=None, description="Specific geospatial, environmental, soil, or climate feature driving the recommendation")
    contributing_datasets: List[str] = Field(default_factory=list, description="List of the 10 target geospatial datasets that contributed data")
    assumptions: List[str]
    missing_information: List[str]
    validation_requirements: str


class SustainabilityAuditReport(BaseModel):
    target_entity_id: str
    target_level: str
    timestamp: str
    summary_counts: Dict[str, int]
    recommendations: List[ComprehensiveRecommendation]
    insufficient_data_warnings: List[str]
    dataset_statuses: Dict[str, str] = Field(default_factory=dict, description="Status of the 10 target geospatial datasets")
    location_profile: Optional[Any] = Field(default=None, description="UnifiedLocationProfile instance if available")
