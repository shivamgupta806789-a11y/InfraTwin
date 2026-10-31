from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class FeatureItem(BaseModel):
    feature_id: str
    feature_name: str
    value: Any
    unit: str
    source: str = Field(..., description="'IFC_GEOMETRY', 'IFC_PROPERTY', 'USER_CONFIRMED', 'DERIVED_STANDARD', 'ESTIMATED_ASSUMPTION', 'OPEN_METEO'")
    confidence: str = Field(..., description="'MEASURED', 'DOCUMENTED', 'DERIVED', 'ESTIMATED_ASSUMPTION', 'UNKNOWN'")
    is_missing: bool = False
    assumptions_applied: Optional[str] = None


class RoofCatchmentZone(BaseModel):
    zone_id: str
    name: str
    area_m2: float
    material: str  # 'concrete_slab', 'metal_sheet', 'clay_tile', 'asphalt_shingle', 'green_roof'
    runoff_coefficient: float
    slope_deg: float
    orientation_azimuth_deg: float


class BuildingUnifiedFeatures(BaseModel):
    building_id: str
    building_type: str = Field(default="Commercial", description="'Commercial', 'Residential', 'Mixed-Use', 'Educational', 'Industrial', 'Civic'")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    elevation_m: float = 0.0
    storeys_count: int = 1
    gross_floor_area_m2: float = 0.0
    building_width_m: float = 0.0
    building_length_m: float = 0.0
    building_height_m: float = 0.0
    roof_area_m2: float = 0.0
    roof_geometry: str = "flat"  # 'flat', 'shed', 'gable', 'hip', 'complex'
    roof_slope_deg: float = 1.5
    roof_orientation_deg: float = 180.0
    roof_material: str = "concrete_slab"
    roof_runoff_coefficient: float = 0.80
    roof_catchment_zones: List[RoofCatchmentZone] = Field(default_factory=list)
    available_exterior_space_m2: float = 45.0
    available_underground_space: bool = True
    max_excavation_depth_m: float = 4.0
    roof_load_bearing_capacity_kg_m2: float = 120.0  # Dead load capacity for elevated tanks
    occupancy_count: int = 50
    daily_non_potable_water_demand_l: float = 1250.0  # Flushing + Landscape irrigation
    daily_total_water_demand_l: float = 2250.0
    existing_drainage_type: str = "municipal_storm_sewer"
    existing_water_infrastructure: str = "municipal_pipe_supply"
    features_audit: List[FeatureItem] = Field(default_factory=list)


class LocationClimateProfile(BaseModel):
    latitude: float
    longitude: float
    place_name: str
    elevation_m: float
    annual_rainfall_mm: float
    monthly_rainfall_mm: List[float] = Field(..., description="12 monthly rainfall depths in mm (Jan - Dec)")
    rainfall_intensity_mm_hr_2yr: float = 45.0
    rainfall_intensity_mm_hr_10yr: float = 85.0
    rainfall_seasonality_index: float = Field(..., description="Ratio of 4 wettest months rainfall to annual total")
    monthly_mean_temp_c: List[float] = Field(default_factory=list)
    monthly_solar_radiation_kwh_m2_day: List[float] = Field(default_factory=list)
    monthly_relative_humidity_pct: List[float] = Field(default_factory=list)
    dominant_wind_direction_deg: float = 270.0
    dominant_wind_speed_kmh: float = 12.0
    terrain_slope_pct: float = 1.5
    nearby_water_bodies: List[str] = Field(default_factory=list)
    soil_texture: str = "Sandy Silt"
    soil_infiltration_rate_mm_hr: float = 25.0
    groundwater_depth_m: float = 4.5
    flood_risk_level: str = "Low to Moderate"
    retrieval_timestamp: str
    data_source: str = "Open-Meteo & WMO Climatological Normal"
    data_period: str = "1991-2020 30-Year Normal"
    geographic_resolution: str = "0.1° (~11km)"
    is_user_confirmed: bool = True


class HydrologicalMonthlySimulation(BaseModel):
    month_index: int  # 1 to 12
    month_name: str
    rainfall_mm: float
    inflow_liters: float
    demand_liters: float
    supplied_liters: float
    unmet_demand_liters: float
    overflow_liters: float
    ending_storage_liters: float
    demand_coverage_pct: float


class HydrologicalPerformanceSummary(BaseModel):
    annual_potential_runoff_liters: float
    annual_captured_liters: float
    annual_water_demand_liters: float
    annual_water_supplied_liters: float
    annual_unmet_demand_liters: float
    annual_overflow_liters: float
    annual_demand_coverage_pct: float
    average_storage_utilization_pct: float
    overflow_days_count: int
    monthly_breakdown: List[HydrologicalMonthlySimulation]


class Intervention3DComponent(BaseModel):
    component_id: str
    component_type: str  # 'gutter', 'downpipe', 'collection_pipe', 'filter_unit', 'first_flush', 'storage_tank', 'overflow_pipe', 'recharge_trench', 'rain_garden'
    name: str
    material: str
    color_hex: str
    position: List[float] = Field(..., description="[x, y, z] center coordinates in local building space")
    dimensions: List[float] = Field(..., description="[width, height, depth] or [radius, height, 0] for cylinders")
    geometry_type: str  # 'box', 'cylinder', 'pipe_path', 'plane'
    path_points: Optional[List[List[float]]] = None  # Polyline coordinates for pipes
    is_subsurface: bool = False
    volume_liters: Optional[float] = None
    specification: str


class RainwaterDesignAlternative(BaseModel):
    alternative_id: str  # e.g. 'ALT-A-GROUND-TANK', 'ALT-B-UNDERGROUND-TANK'
    configuration_type: str  # 'ground_tank', 'underground_tank', 'distributed_tanks', 'rooftop_storage', 'storage_swale', 'storage_recharge', 'rain_garden'
    name: str
    description: str
    tank_capacity_liters: float
    tank_material: str
    tank_dimensions_m: Dict[str, float]  # {'diameter': 2.2, 'height': 2.7} or {'width': 2.5, 'length': 3.0, 'depth': 2.0}
    is_feasible: bool = True
    infeasibility_reasons: List[str] = Field(default_factory=list)
    ranking_score: float = 0.0
    rank: int = 1
    hydrological_performance: HydrologicalPerformanceSummary
    ml_predicted_demand_coverage_pct: Optional[float] = None
    ml_predicted_captured_liters: Optional[float] = None
    capital_cost_inr: float
    annual_maintenance_inr: float
    lifecycle_cost_15yr_inr: float
    simple_payback_years: float
    space_required_m2: float
    groundwater_recharge_potential_liters: float = 0.0
    environmental_benefits: List[str]
    tradeoffs_and_risks: List[str]
    proposed_3d_components: List[Intervention3DComponent] = Field(default_factory=list)


class RainwaterRecommendationReport(BaseModel):
    building_id: str
    timestamp: str
    location_profile: LocationClimateProfile
    building_features: BuildingUnifiedFeatures
    selected_recommended_alternative_id: str
    ranked_alternatives: List[RainwaterDesignAlternative]
    feasibility_matrix: Dict[str, bool]
    elimination_justifications: Dict[str, str]
    engineering_assumptions: List[str]
    missing_data_warnings: List[str]
    statutory_compliance_notices: List[str]
