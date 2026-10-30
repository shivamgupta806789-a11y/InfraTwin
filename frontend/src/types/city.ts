import { BoundingBox3D } from './digital_twin';

export interface CityBuildingSummary {
  building_id: string;
  name: string;
  typology: 'Commercial' | 'Residential' | 'Civic' | 'Transit' | 'Mixed-Use';
  footprint_area_m2: number;
  gross_floor_area_m2: number;
  storeys_count: number;
  height_m: number;
  center_x: number;
  center_y: number;
  center_z: number;
  width_m: number;
  length_m: number;
  has_detailed_bim: boolean;
  bim_model_id?: string | null;
  operational_energy_intensity_kwh_m2: number;
  embodied_carbon_kg_co2e_m2: number;
  solar_pv_capacity_kw: number;
  occupancy_capacity: number;
}

export interface SiteModel {
  site_id: string;
  name: string;
  boundary_polygon: number[][];
  area_m2: number;
  ground_elevation_m: number;
  buildings: CityBuildingSummary[];
  open_space_ratio: number;
  tree_canopy_coverage_pct: number;
}

export interface DistrictModel {
  district_id: string;
  name: string;
  district_type: string;
  boundary_polygon: number[][];
  total_area_hectares: number;
  sites: SiteModel[];
  total_buildings_count: number;
  total_population_estimate: number;
  infrastructure_types: string[];
}

export interface InfrastructureNetwork {
  network_id: string;
  name: string;
  network_type: string;
  line_segments: number[][][];
  color_hex: string;
}

export interface CityModel {
  city_id: string;
  name: string;
  crs: string;
  origin_latitude: number;
  origin_longitude: number;
  bounding_box: BoundingBox3D;
  districts: DistrictModel[];
  infrastructure_networks: InfrastructureNetwork[];
  total_gfa_m2: number;
  total_buildings: number;
  spatial_index_bounds: Record<string, number>;
}
