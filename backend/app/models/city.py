from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.models.digital_twin import BoundingBox3D, StoreyInfo


class CityBuildingSummary(BaseModel):
    building_id: str
    name: str
    typology: str = Field(..., description="'Commercial', 'Residential', 'Civic', 'Transit', or 'Mixed-Use'")
    footprint_area_m2: float
    gross_floor_area_m2: float
    storeys_count: int
    height_m: float
    center_x: float = Field(..., description="Local city 3D X coordinate in meters")
    center_y: float = Field(..., description="Local city 3D Y coordinate in meters")
    center_z: float = Field(..., description="Elevation offset in meters")
    width_m: float
    length_m: float
    has_detailed_bim: bool = Field(default=False, description="True if detailed element-level IFC mesh is loaded")
    bim_model_id: Optional[str] = Field(default=None, description="Linked BIM model ID in ModelStore")
    operational_energy_intensity_kwh_m2: float
    embodied_carbon_kg_co2e_m2: float
    solar_pv_capacity_kw: float
    occupancy_capacity: int


class SiteModel(BaseModel):
    site_id: str
    name: str
    boundary_polygon: List[List[float]] = Field(..., description="Polygon points [x, y] in local site space")
    area_m2: float
    ground_elevation_m: float
    buildings: List[CityBuildingSummary]
    open_space_ratio: float = Field(default=0.35, ge=0.0, le=1.0)
    tree_canopy_coverage_pct: float = Field(default=22.0, ge=0.0, le=100.0)


class DistrictModel(BaseModel):
    district_id: str
    name: str
    district_type: str = Field(..., description="'Commercial Center', 'Innovation Hub', 'Transit-Oriented Zone', 'Residential Quarter'")
    boundary_polygon: List[List[float]] = Field(..., description="Boundary coordinates")
    total_area_hectares: float
    sites: List[SiteModel]
    total_buildings_count: int
    total_population_estimate: int
    infrastructure_types: List[str] = Field(default_factory=lambda: ["Roads", "Power Grid", "Stormwater Drainage", "District Cooling"])


class InfrastructureNetwork(BaseModel):
    network_id: str
    name: str
    network_type: str = Field(..., description="'Roads', 'Water Distribution', 'Power Grid', 'Fiber Telecom'")
    line_segments: List[List[List[float]]] = Field(..., description="List of 3D polyline coordinates [[x1,y1,z1], [x2,y2,z2]]")
    color_hex: str = "#475569"


class CityModel(BaseModel):
    city_id: str
    name: str
    crs: str = "EPSG:4326 (WGS84)"
    origin_latitude: float
    origin_longitude: float
    bounding_box: BoundingBox3D
    districts: List[DistrictModel]
    infrastructure_networks: List[InfrastructureNetwork]
    total_gfa_m2: float
    total_buildings: int
    spatial_index_bounds: Dict[str, float]
