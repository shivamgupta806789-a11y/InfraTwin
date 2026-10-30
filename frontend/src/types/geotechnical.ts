export interface SoilStrataLayer {
  layer_id: string;
  layer_name: string;
  uscs_classification: string;
  depth_top_m: float;
  depth_bottom_m: float;
  thickness_m: float;
  color_hex: string;
  spt_n_value_avg?: number | null;
  moisture_content_pct?: number | null;
  cohesion_kpa?: number | null;
  friction_angle_deg?: number | null;
  allowable_bearing_capacity_kpa?: number | null;
  geological_description: string;
}

export type float = number;

export interface BoreholeRecord {
  borehole_id: string;
  name: string;
  latitude: number;
  longitude: number;
  local_x: number;
  local_z: number;
  ground_elevation_m: number;
  total_depth_m: number;
  water_table_depth_m?: number | null;
  drilling_date: string;
  contractor: string;
  strata: SoilStrataLayer[];
  data_source: string;
  confidence: 'verified_investigation' | 'regional_interpolation' | 'historical';
}

export interface GeotechnicalSiteProfile {
  site_id: string;
  site_name: string;
  crs: string;
  origin_latitude: number;
  origin_longitude: number;
  origin_elevation_m: number;
  dominant_soil_type: string;
  seismic_zone: string;
  peak_ground_acceleration_g: number;
  liquefaction_susceptibility: 'Low' | 'Moderate' | 'High';
  slope_gradient_pct: number;
  landslide_risk: 'Very Low' | 'Low' | 'Moderate' | 'High';
  groundwater_table_m: number;
  flood_hazard_level_100yr_m: number;
  boreholes: BoreholeRecord[];
  regional_strata_summary: SoilStrataLayer[];
  data_sources: string[];
  limitations: string[];
  screening_disclaimer: string;
}
