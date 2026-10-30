export interface GeoLocation {
  latitude: number;
  longitude: number;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  elevation_m?: number | null;
}

export interface BuildingOrientation {
  azimuth_deg: number; // 0 = North, 90 = East, 180 = South, 270 = West
  cardinal_direction: string;
  rotation_angle_rad?: number;
}

export interface ClimateData {
  climate_zone: string;
  mean_temp_c: number;
  max_temp_c: number;
  min_temp_c: number;
  relative_humidity_pct: number;
  annual_rainfall_mm: number;
  solar_radiation_kwh_m2_day: number;
  peak_solar_radiation_mj_m2: number;
  dominant_wind_speed_kmh: number;
  dominant_wind_direction_deg: number;
  dominant_wind_cardinal: string;
  elevation_m: number;
  data_source: string;
  retrieval_timestamp: string;
}

export interface SiteContext {
  urban_density: string;
  nearby_vegetation_pct: number;
  nearby_water_bodies: string[];
  land_use_classification: string;
  terrain_slope_pct: number;
  urban_heat_island_risk: string;
  data_source: string;
}

export interface EnvironmentalEvaluation {
  solar_orientation_score: number;
  solar_exposure_status: string;
  daylight_potential_score: number;
  natural_ventilation_score: number;
  wind_cross_ventilation_status: string;
  annual_rainwater_harvest_liters: number;
  rainwater_harvesting_feasibility: string;
  annual_solar_pv_kwh: number;
  solar_pv_feasibility: string;
  passive_shading_requirement: string;
  green_space_opportunity: string;
  overall_suitability_score: number;
  suitability_rating: string;
}

export interface EnvironmentalRecommendation {
  id: string;
  title: string;
  category: 'orientation' | 'solar_pv' | 'natural_ventilation' | 'rainwater_harvesting' | 'shading' | 'microclimate';
  priority: 'high' | 'medium' | 'low';
  reason: string;
  environmental_evidence: string;
  expected_benefit: string;
  data_source: string;
  limitations: string;
}

export interface EnvironmentalAnalysisRequest {
  location: GeoLocation;
  orientation: BuildingOrientation;
  model_id?: string | null;
  building_params?: Record<string, any> | null;
}

export interface EnvironmentalAnalysisResponse {
  location: GeoLocation;
  orientation: BuildingOrientation;
  climate: ClimateData;
  site_context: SiteContext;
  evaluation: EnvironmentalEvaluation;
  recommendations: EnvironmentalRecommendation[];
  disclaimers: string[];
  missing_data_summary: string[];
  cached?: boolean;
}

export interface LocationPreset {
  display_name: string;
  latitude: number;
  longitude: number;
  city: string;
  state: string;
  country: string;
  climate_hint: string;
}
