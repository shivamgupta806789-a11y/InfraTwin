import { InterventionId } from './building';
import { Intervention3DComponent } from './rainwater';

export interface StructuredIntervention {
  intervention_id: string;
  recommendation_id: string;
  intervention_type: string;
  target_element_ids: string[];
  target_floor?: string | null;
  geometry_parameters: Record<string, any>;
  material_parameters: Record<string, any>;
  world_position: [number, number, number];
  dimensions: [number, number, number];
  orientation: Record<string, number>;
  estimated_cost: number;
  expected_benefit: Record<string, any>;
  calculation_method: string;
  assumptions: string[];
  validation_status: 'VALIDATED' | 'REJECTED' | 'PARTIAL';
  rejection_reason?: string | null;
  components_3d: Intervention3DComponent[];
}

import { ProjectLocation } from './digital_twin';

export interface OptimalBundle {
  id: string;
  name: string;
  badge: string;
  badgeColor: string;
  description: string;
  interventions: InterventionId[];
  energySavingPct: number;
  waterSavingKL: number;
  runoffReductionPct: number;
  carbonReductionPct: number;
  provenance?: string;
}

export interface AppliedInterventionsRequest {
  model_id?: string | null;
  selected_intervention_ids: string[];
  budget_inr?: number;
  width_m?: number;
  length_m?: number;
  floors?: number;
  floor_height_m?: number;
  window_count?: number;
  latitude?: number;
  longitude?: number;
  address?: string;
  climate_zone?: string;
}

export interface AppliedInterventionsResponse {
  model_id?: string | null;
  interventions: StructuredIntervention[];
  total_applied_cost: number;
  applied_count: number;
  rejected_count: number;
  project_location?: ProjectLocation | null;
  climate_summary?: Record<string, any>;
  contributing_datasets?: string[];
  optimal_bundles?: OptimalBundle[];
  diagnostic_logs: string[];
  provenance: string;
}

export interface InterventionItem {
  id: InterventionId;
  name: string;
  category: string;
  description: string;
  cost_estimation_method: string;
  unit_cost_description: string;
  quantity: number;
  quantity_unit: string;
  estimated_cost_inr: number;
  fits_budget: boolean;
  is_eligible: boolean;
  ineligibility_reason?: string | null;
  rank?: number | null;
  score?: number | null;
  explanation: string;
  limitations: string[];
  evidence_status: string;
}

export interface RecommendationResponse {
  budget_inr: number;
  available_interventions: InterventionItem[];
  ranked_recommendations: InterventionItem[];
  total_recommended_cost_inr: number;
  remaining_budget_inr: number;
  calculation_assumptions: string[];
  warnings: string[];
  missing_information: string[];
}

export interface CostBreakdownItem {
  id: string;
  name: string;
  quantity: number;
  quantity_unit: string;
  unit_rate_inr: number;
  total_cost_inr: number;
  formula: string;
  assumptions: string;
}

export interface ImpactEstimateItem {
  estimate_type: string;
  metric: string;
  value?: number | null;
  unit: string;
  is_estimated: boolean;
  calculation_method: string;
  assumptions: string[];
  source_provenance: string;
  evidence_limitations: string;
  missing_inputs: string[];
}

export interface EstimateResponse {
  selected_interventions: string[];
  total_cost_inr: number;
  budget_inr: number;
  fits_budget: boolean;
  cost_breakdown: CostBreakdownItem[];
  impact_estimates: ImpactEstimateItem[];
  assumptions: string[];
  missing_inputs: string[];
}

export interface ApiHealthResponse {
  status: string;
  application_name: string;
  version: string;
}
