export type InterventionId =
  | 'external_shading'
  | 'reflective_roof'
  | 'roof_insulation'
  | 'solar_pv'
  | 'rainwater_harvesting'
  | 'stormwater_bioswale'
  | 'permeable_paving'
  | 'green_roof'
  | 'natural_ventilation'
  | 'rooftop_greenhouse';

export interface BuildingParams {
  width_m: number;
  length_m: number;
  floor_height_m: number;
  floors: number;
  window_count: number;
  budget_inr: number;
  selected_interventions: InterventionId[];
}

export interface NormalizedBuilding {
  width_m: number;
  length_m: number;
  floor_height_m: number;
  floors: number;
  window_count: number;
  budget_inr: number;
  selected_interventions: string[];
  roof_area_m2: number;
  gross_floor_area_m2: number;
  total_height_m: number;
  total_wall_area_m2: number;
  estimated_window_wall_ratio: number;
}

export interface BuildingValidationResult {
  is_valid: boolean;
  normalized?: NormalizedBuilding;
  warnings: string[];
  errors: string[];
}

export interface BuildingFormErrors {
  width_m?: string;
  length_m?: string;
  floor_height_m?: string;
  floors?: string;
  window_count?: string;
  budget_inr?: string;
  general?: string;
}
