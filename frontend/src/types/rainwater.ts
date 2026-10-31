export interface FeatureItem {
  feature_id: string;
  feature_name: string;
  value: any;
  unit: string;
  source: string;
  confidence: 'MEASURED' | 'DOCUMENTED' | 'DERIVED' | 'ESTIMATED_ASSUMPTION' | 'UNKNOWN';
  is_missing: boolean;
  assumptions_applied?: string | null;
}

export interface RoofCatchmentZone {
  zone_id: string;
  name: string;
  area_m2: floatNumber;
  material: string;
  runoff_coefficient: number;
  slope_deg: number;
  orientation_azimuth_deg: number;
}

type floatNumber = number;

export interface BuildingUnifiedFeatures {
  building_id: string;
  building_type: string;
  latitude?: number | null;
  longitude?: number | null;
  elevation_m: number;
  storeys_count: number;
  gross_floor_area_m2: number;
  building_width_m: number;
  building_length_m: number;
  building_height_m: number;
  roof_area_m2: number;
  roof_geometry: string;
  roof_slope_deg: number;
  roof_orientation_deg: number;
  roof_material: string;
  roof_runoff_coefficient: number;
  roof_catchment_zones: RoofCatchmentZone[];
  available_exterior_space_m2: number;
  available_underground_space: boolean;
  max_excavation_depth_m: number;
  roof_load_bearing_capacity_kg_m2: number;
  occupancy_count: number;
  daily_non_potable_water_demand_l: number;
  daily_total_water_demand_l: number;
  existing_drainage_type: string;
  existing_water_infrastructure: string;
  features_audit: FeatureItem[];
}

export interface LocationClimateProfile {
  latitude: number;
  longitude: number;
  place_name: string;
  elevation_m: number;
  annual_rainfall_mm: number;
  monthly_rainfall_mm: number[];
  rainfall_intensity_mm_hr_2yr: number;
  rainfall_intensity_mm_hr_10yr: number;
  rainfall_seasonality_index: number;
  monthly_mean_temp_c: number[];
  monthly_solar_radiation_kwh_m2_day: number[];
  monthly_relative_humidity_pct: number[];
  dominant_wind_direction_deg: number;
  dominant_wind_speed_kmh: number;
  terrain_slope_pct: number;
  nearby_water_bodies: string[];
  soil_texture: string;
  soil_infiltration_rate_mm_hr: number;
  groundwater_depth_m: number;
  flood_risk_level: string;
  retrieval_timestamp: string;
  data_source: string;
  data_period: string;
  geographic_resolution: string;
  is_user_confirmed: boolean;
}

export interface HydrologicalMonthlySimulation {
  month_index: number;
  month_name: string;
  rainfall_mm: number;
  inflow_liters: number;
  demand_liters: number;
  supplied_liters: number;
  unmet_demand_liters: number;
  overflow_liters: number;
  ending_storage_liters: number;
  demand_coverage_pct: number;
}

export interface HydrologicalPerformanceSummary {
  annual_potential_runoff_liters: number;
  annual_captured_liters: number;
  annual_water_demand_liters: number;
  annual_water_supplied_liters: number;
  annual_unmet_demand_liters: number;
  annual_overflow_liters: number;
  annual_demand_coverage_pct: number;
  average_storage_utilization_pct: number;
  overflow_days_count: number;
  monthly_breakdown: HydrologicalMonthlySimulation[];
}

export interface Intervention3DComponent {
  component_id: string;
  component_type: string;
  name: string;
  material: string;
  color_hex: string;
  position: [number, number, number]; // [x, length_y, height_z]
  dimensions: [number, number, number]; // [width_x, height_y, length_z] or [radius, height, 0]
  geometry_type: 'box' | 'cylinder' | 'pipe_path' | 'plane';
  path_points?: [number, number, number][];
  is_subsurface?: boolean;
  volume_liters?: number;
  specification: string;
}

export interface RainwaterDesignAlternative {
  alternative_id: string;
  configuration_type: string;
  name: string;
  description: string;
  tank_capacity_liters: number;
  tank_material: string;
  tank_dimensions_m: Record<string, number>;
  is_feasible: boolean;
  infeasibility_reasons: string[];
  ranking_score: number;
  rank: number;
  hydrological_performance: HydrologicalPerformanceSummary;
  ml_predicted_demand_coverage_pct?: number | null;
  ml_predicted_captured_liters?: number | null;
  capital_cost_inr: number;
  annual_maintenance_inr: number;
  lifecycle_cost_15yr_inr: number;
  simple_payback_years: number;
  space_required_m2: number;
  groundwater_recharge_potential_liters: number;
  environmental_benefits: string[];
  tradeoffs_and_risks: string[];
  proposed_3d_components: Intervention3DComponent[];
}

export interface RainwaterRecommendationReport {
  building_id: string;
  timestamp: string;
  location_profile: LocationClimateProfile;
  building_features: BuildingUnifiedFeatures;
  selected_recommended_alternative_id: string;
  ranked_alternatives: RainwaterDesignAlternative[];
  feasibility_matrix: Record<string, boolean>;
  elimination_justifications: Record<string, string>;
  engineering_assumptions: string[];
}
