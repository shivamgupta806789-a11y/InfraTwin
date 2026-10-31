from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Vector3D(BaseModel):
    x: float = Field(default=0.0, description="X coordinate in meters (e.g. building plan width)")
    y: float = Field(default=0.0, description="Y coordinate in meters (elevation above floor slab)")
    z: float = Field(default=0.0, description="Z coordinate in meters (building plan depth)")


class Dimensions3D(BaseModel):
    width: float = Field(..., gt=0.0, description="Width along local X axis in meters")
    depth: float = Field(..., gt=0.0, description="Depth along local Z axis in meters")
    height: float = Field(..., gt=0.0, description="Height along local Y axis in meters")


class FurnitureItem(BaseModel):
    id: str = Field(..., description="Unique furniture element ID, e.g. 'furn_bed_1'")
    room_id: str = Field(..., description="Host room identifier, e.g. 'room_1' or 'space_f0_room_1'")
    storey_id: str = Field(default="storey_0", description="Associated building storey ID")
    category: str = Field(
        ...,
        description="Furniture category: 'bed', 'wardrobe', 'side_table', 'sofa', 'coffee_table', "
                    "'tv_unit', 'armchair', 'kitchen_counter', 'cabinets', 'sink', 'refrigerator', "
                    "'cooktop', 'kitchen_island', 'toilet', 'washbasin', 'shower', 'bathtub', "
                    "'dining_table', 'dining_chair', 'credenza', 'office_desk', 'office_chair', "
                    "'meeting_table', 'storage_cabinet', 'conference_table', 'conference_chair', "
                    "'presentation_screen', 'corridor_bench', 'storage_rack', 'utility_counter'"
    )
    name: str = Field(..., description="Display title of the furniture piece")
    dimensions_m: Dimensions3D
    position_m: Vector3D
    rotation_deg: float = Field(default=0.0, description="Yaw rotation around vertical Y axis in degrees")
    scale: List[float] = Field(default_factory=lambda: [1.0, 1.0, 1.0], description="Scale factors [sx, sy, sz]")
    status: str = Field(default="PROPOSED", description="'PROPOSED', 'USER_MODIFIED', 'CONFIRMED'")
    clearance_m: float = Field(default=0.6, ge=0.0, description="Required circulation clearance corridor around object")
    fits_within_room: bool = Field(default=True, description="Whether object passes polygonal room boundary containment")
    unaccommodated_reason: Optional[str] = Field(default=None, description="Detailed engineering reason if item cannot fit")
    material: str = Field(default="oak_wood", description="Material preset name")
    color_hex: str = Field(default="#8b5a2b", description="Hex display color")
    is_visible: bool = Field(default=True, description="Whether element is currently visible in 3D scene")


class RoomFurnishingProfile(BaseModel):
    room_id: str
    room_name: str
    room_type: str = Field(
        default="office",
        description="'living', 'bedroom', 'kitchen', 'bathroom', 'dining', 'office', 'conference', 'corridor', 'storage', 'utility', 'uncertain'"
    )
    area_sqm: float
    dimensions_summary: str = Field(default="", description="e.g. '4.5m × 3.8m'")
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    is_furnished: bool = True
    items: List[FurnitureItem] = Field(default_factory=list)
    unaccommodated_items: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Items suggested for room type that could not fit due to spatial or clearance constraints"
    )
    notes: List[str] = Field(default_factory=list)


class BuildingFurnishingPlan(BaseModel):
    model_id: str
    building_name: str = "Digital Twin Furnished Layout"
    timestamp: str
    storeys_count: int = 1
    total_furniture_count: int = 0
    room_profiles: List[RoomFurnishingProfile] = Field(default_factory=list)
    all_items: List[FurnitureItem] = Field(default_factory=list)
    validation_status: str = Field(default="VALID", description="'VALID', 'COLLISIONS_RESOLVED', 'UNCERTAIN_ROOMS'")
    circulation_clearance_notes: List[str] = Field(default_factory=list)


class FurnitureUpdateRequest(BaseModel):
    position_m: Optional[Vector3D] = None
    rotation_deg: Optional[float] = None
    scale: Optional[List[float]] = None
    material: Optional[str] = None
    color_hex: Optional[str] = None
    is_visible: Optional[bool] = None
    category: Optional[str] = None
    name: Optional[str] = None


class FurnitureAddRequest(BaseModel):
    room_id: str
    storey_id: str = "storey_0"
    category: str
    name: Optional[str] = None
    position_m: Vector3D
    rotation_deg: float = 0.0
    material: Optional[str] = None
    color_hex: Optional[str] = None
