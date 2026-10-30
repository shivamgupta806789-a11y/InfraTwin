export interface ScenarioMetricValue {
  value: number;
  unit: string;
  provenance_type: 'MEASURED' | 'SIMULATED' | 'PREDICTED' | 'ASSUMED';
  uncertainty_range?: string | null;
  source_notes: string;
}

export interface DesignScenario {
  scenario_id: string;
  name: string;
  description: string;
  time_horizon_years: number;
  operational_energy_kwh_m2_yr: ScenarioMetricValue;
  embodied_carbon_kg_co2e_m2: ScenarioMetricValue;
  annual_water_demand_kl: ScenarioMetricValue;
  annual_water_recycled_kl: ScenarioMetricValue;
  capital_cost_inr: ScenarioMetricValue;
  annual_operating_cost_inr: ScenarioMetricValue;
  climate_vulnerability_score: ScenarioMetricValue;
  resilience_rating: 'A - Superior' | 'B - High' | 'C - Moderate' | 'D - Vulnerable';
  applied_interventions: string[];
  methodology_limitations: string;
}

export interface ScenarioComparisonReport {
  building_id: string;
  gross_floor_area_m2: number;
  baseline_scenario: DesignScenario;
  alternative_scenarios: DesignScenario[];
  comparative_summary: Record<string, any>;
  scientific_disclaimer: string;
}
