import { InterventionId } from './building';

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
