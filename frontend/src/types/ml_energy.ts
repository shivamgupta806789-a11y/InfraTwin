export type ApplicabilityStatus = 'WITHIN_DOMAIN' | 'OUTSIDE_DOMAIN' | 'INSUFFICIENT_DATA';

export interface FeatureValidationItem {
  feature_id: string;
  feature_name: string;
  value?: number | null;
  unit: string;
  training_domain_range: string;
  is_within_domain: bool;
}

export type bool = boolean;

export interface ModelEvaluationMetrics {
  r2_score_heating: number;
  r2_score_cooling: number;
  rmse_heating: number;
  rmse_cooling: number;
  training_samples_count: number;
  algorithm: string;
}

export interface EnergyPredictionResponse {
  model_id: string;
  model_version: string;
  applicability_status: ApplicabilityStatus;
  heating_load_kwh_m2?: number | null;
  cooling_load_kwh_m2?: number | null;
  total_thermal_load_kwh_m2?: number | null;
  feature_units: Record<string, string>;
  features: Record<string, FeatureValidationItem>;
  out_of_domain_warnings: string[];
  missing_features: string[];
  calculation_assumptions: string[];
  evaluation_metrics: ModelEvaluationMetrics;
  timestamp: string;
}

export interface ParetoAlternative {
  solution_id: string;
  name: string;
  capital_cost_inr: number;
  carbon_reduction_pct: number;
  energy_savings_pct: number;
  is_pareto_optimal: boolean;
  key_interventions: string[];
}

export interface ParetoOptimizationResponse {
  objective_count: number;
  objectives: string[];
  pareto_solutions: ParetoAlternative[];
  tradeoff_summary: string;
}
