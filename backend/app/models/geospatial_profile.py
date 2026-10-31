from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class DatasetConnectionStatus(str, Enum):
    CONNECTED = "connected"
    SUCCESSFULLY_RETRIEVED = "successfully_retrieved"
    PARTIALLY_AVAILABLE = "partially_available"
    UNAVAILABLE = "unavailable"
    INVALID_RESPONSE = "invalid_response"
    REQUIRES_CREDENTIALS = "requires_credentials"
    REQUIRES_MANUAL_DOWNLOAD = "requires_manual_download"


class DatasetStatusItem(BaseModel):
    dataset_id: str
    name: str
    status: DatasetConnectionStatus
    access_method: str
    source_url: str
    response_time_ms: Optional[float] = None
    last_retrieved: Optional[str] = None
    error_message: Optional[str] = None
    limitations: str = ""


class LocationFeatureItem(BaseModel):
    feature_id: str
    feature_name: str
    category: str  # 'land_cover', 'vegetation', 'infrastructure', 'soil_hydrology', 'climate'
    value: Any
    unit: str
    dataset_source: str
    retrieval_date: str
    spatial_resolution: str
    confidence: str  # 'AUTHENTIC_LIVE', 'SATELLITE_DERIVED', 'REGIONAL_MIRROR', 'DOCUMENTED_FALLBACK'
    missing_data_status: str = "AVAILABLE"  # 'AVAILABLE', 'PARTIALLY_AVAILABLE', 'UNAVAILABLE', 'FALLBACK_USED'
    limitations: str = ""


class LandCoverProfile(BaseModel):
    built_up_coverage_pct: LocationFeatureItem
    vegetation_coverage_pct: LocationFeatureItem
    water_body_coverage_pct: LocationFeatureItem
    bare_ground_coverage_pct: LocationFeatureItem
    dominant_class: LocationFeatureItem


class VegetationProfile(BaseModel):
    tree_canopy_density_pct: LocationFeatureItem
    ndvi_mean: LocationFeatureItem
    vegetation_vigor: LocationFeatureItem
    green_space_coverage_pct: LocationFeatureItem
    preservation_priority: LocationFeatureItem


class InfrastructureProfile(BaseModel):
    nearest_road_distance_m: LocationFeatureItem
    road_classification: LocationFeatureItem
    nearby_building_count: LocationFeatureItem
    building_density_ratio: LocationFeatureItem
    nearest_waterway_distance_m: LocationFeatureItem
    waterway_type: LocationFeatureItem


class SoilHydrologyProfile(BaseModel):
    clay_content_pct: LocationFeatureItem
    sand_content_pct: LocationFeatureItem
    silt_content_pct: LocationFeatureItem
    soil_texture_usda: LocationFeatureItem
    hydrologic_soil_group: LocationFeatureItem
    bulk_density_g_cm3: LocationFeatureItem
    soil_ph: LocationFeatureItem
    watershed_basin_level: LocationFeatureItem
    strahler_stream_order: LocationFeatureItem
    drainage_channel_distance_m: LocationFeatureItem
    infiltration_rate_mm_hr: LocationFeatureItem


class ClimateProfile(BaseModel):
    annual_solar_ghi_kwh_m2_day: LocationFeatureItem
    monthly_solar_ghi: LocationFeatureItem
    annual_precipitation_mm: LocationFeatureItem
    monthly_precipitation_mm: LocationFeatureItem
    annual_mean_temp_c: LocationFeatureItem
    wind_speed_mps: LocationFeatureItem
    prevailing_wind_direction_deg: LocationFeatureItem
    intensity_2yr_return_mm_hr: LocationFeatureItem
    intensity_10yr_return_mm_hr: LocationFeatureItem
    cooling_degree_days: LocationFeatureItem
    heating_degree_days: LocationFeatureItem


class UnifiedLocationProfile(BaseModel):
    latitude: float
    longitude: float
    elevation_m: float
    place_name: Optional[str] = None
    timestamp: str
    dataset_statuses: Dict[str, DatasetStatusItem] = Field(default_factory=dict)
    land_cover: LandCoverProfile
    vegetation: VegetationProfile
    infrastructure: InfrastructureProfile
    soil_hydrology: SoilHydrologyProfile
    climate: ClimateProfile
    all_features: List[LocationFeatureItem] = Field(default_factory=list)
