from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ScenarioMetricValue(BaseModel):
    value: float
    unit: str
    provenance_type: str = Field(..., description="'MEASURED', 'SIMULATED', 'PREDICTED', or 'ASSUMED'")
    uncertainty_range: Optional[str] = None
    source_notes: str


class DesignScenario(BaseModel):
    scenario_id: str
    name: str
    description: str
    time_horizon_years: int = Field(..., description="2026 (Near-term), 2035 (Mid-term), or 2050 (Long-term)")
    operational_energy_kwh_m2_yr: ScenarioMetricValue
    embodied_carbon_kg_co2e_m2: ScenarioMetricValue
    annual_water_demand_kl: ScenarioMetricValue
    annual_water_recycled_kl: ScenarioMetricValue
    capital_cost_inr: ScenarioMetricValue
    annual_operating_cost_inr: ScenarioMetricValue
    climate_vulnerability_score: ScenarioMetricValue  # 0 (resilient) to 100 (vulnerable)
    resilience_rating: str = Field(..., description="'A - Superior', 'B - High', 'C - Moderate', 'D - Vulnerable'")
    applied_interventions: List[str]
    methodology_limitations: str


class ScenarioComparisonReport(BaseModel):
    building_id: str
    gross_floor_area_m2: float
    baseline_scenario: DesignScenario
    alternative_scenarios: List[DesignScenario]
    comparative_summary: Dict[str, Any]
    scientific_disclaimer: str = (
        "PROJECTION NOTICE: Future scenario calculations are simulated engineering sensitivity models based on "
        "IPCC AR6 climate projections and official grid decarbonization trajectories. They are intended for comparative "
        "decision support and must not be treated as deterministic guarantees of future performance."
    )
