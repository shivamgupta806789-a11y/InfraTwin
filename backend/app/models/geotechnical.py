import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SoilStrataLayer(BaseModel):
    layer_id: str
    layer_name: str
    uscs_classification: str = Field(..., description="Unified Soil Classification System symbol (e.g. 'CL', 'SM', 'GW', 'CH')")
    depth_top_m: float = Field(..., ge=0.0)
    depth_bottom_m: float = Field(..., gt=0.0)
    thickness_m: float = Field(..., gt=0.0)
    color_hex: str = Field(default="#c2a68c")
    spt_n_value_avg: Optional[int] = Field(default=None, description="Standard Penetration Test N-value (blows/300mm)")
    moisture_content_pct: Optional[float] = Field(default=None)
    cohesion_kpa: Optional[float] = Field(default=None, description="Undrained shear strength or cohesion in kPa")
    friction_angle_deg: Optional[float] = Field(default=None, description="Effective angle of internal friction in degrees")
    allowable_bearing_capacity_kpa: Optional[float] = Field(
        default=None,
        description="Presumptive indicative bearing pressure. Requires on-site structural engineer validation."
    )
    geological_description: str


class BoreholeRecord(BaseModel):
    borehole_id: str
    name: str
    latitude: float
    longitude: float
    local_x: float = Field(..., description="Local 3D viewer X coordinate in meters relative to site origin")
    local_z: float = Field(..., description="Local 3D viewer Z coordinate in meters relative to site origin")
    ground_elevation_m: float
    total_depth_m: float
    water_table_depth_m: Optional[float] = None
    drilling_date: str
    contractor: str
    strata: List[SoilStrataLayer]
    data_source: str
    confidence: str = Field(default="high", description="'verified_investigation', 'regional_interpolation', or 'historical'")


class GeotechnicalSiteProfile(BaseModel):
    site_id: str
    site_name: str
    crs: str = Field(default="EPSG:4326 (WGS84)", description="Coordinate Reference System")
    origin_latitude: float
    origin_longitude: float
    origin_elevation_m: float
    dominant_soil_type: str
    seismic_zone: str = Field(..., description="Seismic hazard zone rating (e.g., 'Zone IV - High Damage Risk')")
    peak_ground_acceleration_g: float = Field(..., description="Design Peak Ground Acceleration (PGA) in g")
    liquefaction_susceptibility: str = Field(..., description="'Low', 'Moderate', or 'High'")
    slope_gradient_pct: float
    landslide_risk: str = Field(..., description="'Very Low', 'Low', 'Moderate', or 'High'")
    groundwater_table_m: float = Field(..., description="Average water table depth below finished ground level")
    flood_hazard_level_100yr_m: float = Field(..., description="100-year regulatory flood inundation level in meters")
    boreholes: List[BoreholeRecord]
    regional_strata_summary: List[SoilStrataLayer]
    data_sources: List[str]
    limitations: List[str]
    screening_disclaimer: str = (
        "NOTICE: Subsurface profiles and geotechnical visualizations are screening-level models compiled from "
        "regional geological records and available borehole logs. This screening does not substitute for site-specific "
        "geotechnical drilling, laboratory testing, or certified foundation design under relevant building codes."
    )
