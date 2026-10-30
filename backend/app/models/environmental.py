from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class GeoLocation(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    address: Optional[str] = Field(default=None, description="Formatted street address or locality")
    city: Optional[str] = Field(default=None, description="City or district")
    state: Optional[str] = Field(default=None, description="State or province")
    country: Optional[str] = Field(default=None, description="Country name")
    elevation_m: Optional[float] = Field(default=None, description="Terrain elevation above sea level in meters")


class BuildingOrientation(BaseModel):
    azimuth_deg: float = Field(
        default=0.0,
        ge=0.0,
        le=360.0,
        description="Building long-axis or main facade orientation (0°=North, 90°=East, 180°=South, 270°=West)"
    )
    cardinal_direction: str = Field(default="North-Facing", description="Cardinal description")
    rotation_angle_rad: float = Field(default=0.0, description="Orientation in radians for geometric transformations")


class ClimateData(BaseModel):
    climate_zone: str = Field(..., description="Köppen-Geiger climate classification")
    mean_temp_c: float = Field(..., description="Mean annual temperature in °C")
    max_temp_c: float = Field(..., description="Peak summer temperature in °C")
    min_temp_c: float = Field(..., description="Lowest winter temperature in °C")
    relative_humidity_pct: float = Field(..., description="Mean relative humidity percentage")
    annual_rainfall_mm: float = Field(..., description="Annual precipitation in mm")
    solar_radiation_kwh_m2_day: float = Field(..., description="Average daily global horizontal irradiance (GHI)")
    peak_solar_radiation_mj_m2: float = Field(..., description="Peak daily shortwave radiation sum")
    dominant_wind_speed_kmh: float = Field(..., description="Dominant wind speed in km/h")
    dominant_wind_direction_deg: float = Field(..., description="Dominant wind direction azimuth in degrees")
    dominant_wind_cardinal: str = Field(..., description="Dominant wind direction cardinal (e.g. WSW)")
    elevation_m: float = Field(..., description="Topographic elevation in meters")
    data_source: str = Field(..., description="Originating meteorological data source")
    retrieval_timestamp: str


class SiteContext(BaseModel):
    urban_density: str = Field(..., description="'High Density Urban', 'Moderate Urban', 'Suburban', or 'Rural'")
    nearby_vegetation_pct: float = Field(..., ge=0.0, le=100.0, description="Estimated tree canopy & green-cover within 800m")
    nearby_water_bodies: List[str] = Field(default_factory=list, description="Names or types of detected water bodies within 1.5km")
    land_use_classification: str = Field(..., description="Zoning / land-use classification")
    terrain_slope_pct: float = Field(default=1.5, ge=0.0, description="Estimated slope gradient")
    urban_heat_island_risk: str = Field(..., description="'High', 'Moderate', or 'Low'")
    data_source: str = Field(..., description="Provenance for geospatial context")


class EnvironmentalEvaluation(BaseModel):
    solar_orientation_score: float = Field(..., ge=0.0, le=100.0, description="0-100 score evaluating building solar alignment")
    solar_exposure_status: str = Field(..., description="'Optimal', 'Acceptable', 'High Afternoon Glare', or 'High Solar Heat Gain'")
    daylight_potential_score: float = Field(..., ge=0.0, le=100.0)
    natural_ventilation_score: float = Field(..., ge=0.0, le=100.0)
    wind_cross_ventilation_status: str = Field(..., description="'Favorable', 'Moderate', or 'Shielded / Weak'")
    annual_rainwater_harvest_liters: float = Field(..., ge=0.0, description="Harvestable rainwater volume per year in liters")
    rainwater_harvesting_feasibility: str = Field(..., description="'High', 'Medium', or 'Low'")
    annual_solar_pv_kwh: float = Field(..., ge=0.0, description="Estimated annual clean electricity generation in kWh")
    solar_pv_feasibility: str = Field(..., description="'Excellent', 'Good', or 'Moderate'")
    passive_shading_requirement: str = Field(..., description="'Critical', 'Recommended', or 'Optional'")
    green_space_opportunity: str
    overall_suitability_score: float = Field(..., ge=0.0, le=100.0)
    suitability_rating: str = Field(..., description="'Highly Suitable', 'Suitable with Adaptations', or 'Sub-optimal Alignment'")


class EnvironmentalRecommendation(BaseModel):
    id: str
    title: str
    category: str = Field(..., description="'orientation', 'solar_pv', 'natural_ventilation', 'rainwater_harvesting', 'shading', 'microclimate'")
    priority: str = Field(..., description="'high', 'medium', or 'low'")
    reason: str = Field(..., description="Why this design adaptation is recommended")
    environmental_evidence: str = Field(..., description="Measured site environmental data supporting the recommendation")
    expected_benefit: str = Field(..., description="Quantified performance or energy benefit")
    data_source: str = Field(..., description="Legitimate dataset or meteorological model referenced")
    limitations: str = Field(..., description="Engineering limitations and statutory screening disclaimers")


class EnvironmentalAnalysisRequest(BaseModel):
    location: GeoLocation
    orientation: BuildingOrientation
    model_id: Optional[str] = Field(default=None, description="Optional active IFC / 2D digital twin model ID")
    building_params: Optional[Dict[str, Any]] = Field(default=None, description="Optional parametric building dimensions")


class EnvironmentalAnalysisResponse(BaseModel):
    location: GeoLocation
    orientation: BuildingOrientation
    climate: ClimateData
    site_context: SiteContext
    evaluation: EnvironmentalEvaluation
    recommendations: List[EnvironmentalRecommendation]
    disclaimers: List[str] = Field(default_factory=list)
    missing_data_summary: List[str] = Field(default_factory=list)
    cached: bool = False
