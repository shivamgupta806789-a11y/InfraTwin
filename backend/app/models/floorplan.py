from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class Point2D(BaseModel):
    x: float = Field(..., description="X coordinate (in meters or pixels depending on context)")
    y: float = Field(..., description="Y coordinate (in meters or pixels depending on context)")


class Wall2D(BaseModel):
    id: str = Field(..., description="Unique identifier for the wall segment")
    start: Point2D
    end: Point2D
    thickness_m: float = Field(default=0.2, ge=0.05, le=1.5, description="Wall thickness in meters")
    measured_thickness_px: Optional[float] = Field(default=None, description="Actual measured stroke width in image pixels")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Detection confidence score")
    wall_type: str = Field(default="exterior", description="'exterior', 'interior', or 'partition'")
    detection_status: str = Field(default="DETECTED", description="'DETECTED', 'USER_CONFIRMED', 'INFERRED', 'UNCERTAIN', 'MISSING'")
    validation_status: str = Field(default="VALID", description="'VALID', 'DISCONNECTED', 'OVERLAPPING', 'REPAIRED', 'UNCERTAIN'")
    validation_errors: List[str] = Field(default_factory=list)
    connectivity_degree: int = Field(default=2, description="Number of connected or intersecting walls at junctions")
    source_page: int = Field(default=1, description="Source page or drawing sheet index")
    is_active: bool = Field(default=True, description="Whether this wall is included in 3D generation")


class Door2D(BaseModel):
    id: str = Field(..., description="Unique identifier for the door")
    wall_id: Optional[str] = Field(default=None, description="Host wall segment identifier")
    position: Point2D = Field(..., description="Center location of the door along host wall")
    width_m: float = Field(default=0.9, ge=0.5, le=3.0, description="Door opening width in meters")
    height_m: float = Field(default=2.1, ge=1.8, le=3.5, description="Door opening height in meters")
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    swing_direction: Optional[str] = Field(default="inward_left", description="Optional swing arc indicator")
    detection_status: str = Field(default="DETECTED", description="'DETECTED', 'USER_CONFIRMED', 'INFERRED', 'UNCERTAIN', 'MISSING'")
    validation_status: str = Field(default="VALID", description="'VALID', 'UNHOSTED', 'COLLIDING'")
    source_page: int = Field(default=1)
    is_active: bool = Field(default=True)


class Window2D(BaseModel):
    id: str = Field(..., description="Unique identifier for the window")
    wall_id: Optional[str] = Field(default=None, description="Host wall segment identifier")
    position: Point2D = Field(..., description="Center location of the window along host wall")
    width_m: float = Field(default=1.2, ge=0.4, le=6.0, description="Window opening width in meters")
    height_m: float = Field(default=1.4, ge=0.4, le=3.0, description="Window opening height in meters")
    sill_height_m: float = Field(default=0.9, ge=0.0, le=2.0, description="Window sill elevation above floor slab")
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    detection_status: str = Field(default="DETECTED", description="'DETECTED', 'USER_CONFIRMED', 'INFERRED', 'UNCERTAIN', 'MISSING'")
    validation_status: str = Field(default="VALID", description="'VALID', 'UNHOSTED', 'COLLIDING'")
    source_page: int = Field(default=1)
    is_active: bool = Field(default=True)


class Room2D(BaseModel):
    id: str = Field(..., description="Unique identifier for the enclosed room")
    name: str = Field(default="Room", description="Inferred or user-assigned room label")
    polygon: List[Point2D] = Field(default_factory=list, description="Boundary polygon vertices in meters")
    area_sqm: float = Field(default=0.0, ge=0.0, description="Calculated enclosed room area in m²")
    room_type: str = Field(default="office", description="'office', 'living', 'bedroom', 'corridor', 'bathroom', 'kitchen', 'balcony', 'other'")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    detection_status: str = Field(default="DETECTED", description="'DETECTED', 'USER_CONFIRMED', 'INFERRED', 'UNCERTAIN', 'MISSING'")
    dominant_color_hex: Optional[str] = Field(default=None, description="Dominant interior hex fill color extracted from original drawing")
    color_rgb: Optional[List[int]] = Field(default=None, description="RGB values [R, G, B] of interior region")
    inferred_material: str = Field(default="hardwood", description="'hardwood', 'ceramic_tile', 'polished_concrete', 'landscaped_vegetation', 'water_feature', 'carpet', 'custom'")
    material_confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    is_valid_polygon: bool = Field(default=True, description="Whether polygon is non-self-intersecting and topologically valid")
    validation_errors: List[str] = Field(default_factory=list)
    source_page: int = Field(default=1)


class ScaleReference(BaseModel):
    known_dimension_m: Optional[float] = Field(default=None, description="User-supplied real-world reference dimension")
    pixels_per_meter: float = Field(default=50.0, gt=0.0, description="Pixel to meter ratio")
    method: str = Field(default="default", description="'user_hint', 'ocr_text_extracted', 'ratio_inferred', or 'default'")
    detected_labels: List[str] = Field(default_factory=list, description="Extracted scale or dimension text strings")
    pixel_span: Optional[float] = None


class DrawingClassification(BaseModel):
    typology: str = Field(
        default="individual_floor_plan",
        description="'individual_floor_plan', 'elevation_drawing', 'architectural_set', 'colony_site_plan', or 'aerial_satellite'"
    )
    label: str = Field(default="Individual Floor Plan")
    confidence: float = Field(default=0.92, ge=0.0, le=1.0)
    reasoning: str = Field(default="Detected single enclosed perimeter with interior partition network and room voids.")
    detected_building_count: int = Field(default=1, ge=1)
    site_features: List[str] = Field(default_factory=list)


class ClarificationQuestion(BaseModel):
    question_id: str
    field_key: str = Field(..., description="Target property, e.g. 'floors', 'floor_height_m', 'known_dimension_m', 'drawing_typology'")
    question_text: str
    reason: str
    detected_value: Optional[Any] = None
    confidence: float = Field(default=0.6, ge=0.0, le=1.0)
    drawing_region: Optional[Dict[str, float]] = None
    element_id: Optional[str] = None
    suggested_options: List[str] = Field(default_factory=list)
    status: str = Field(default="pending", description="'pending', 'answered', 'confirmed'")
    user_answer: Optional[str] = None


class FloorPlan2D(BaseModel):
    drawing_id: str
    image_width_px: int
    image_height_px: int
    bounds_width_m: float = Field(default=15.0, description="Computed bounding width in meters")
    bounds_depth_m: float = Field(default=12.0, description="Computed bounding depth in meters")
    scale: ScaleReference
    classification: Optional[DrawingClassification] = None
    detected_storeys: Optional[int] = Field(default=1, description="Automatically extracted storeys count")
    detected_floor_height_m: Optional[float] = Field(default=3.0, description="Automatically extracted floor height")
    detected_building_typology: Optional[str] = Field(default="Commercial")
    clarification_questions: List[ClarificationQuestion] = Field(default_factory=list)
    walls: List[Wall2D] = Field(default_factory=list)
    doors: List[Door2D] = Field(default_factory=list)
    windows: List[Window2D] = Field(default_factory=list)
    rooms: List[Room2D] = Field(default_factory=list)
    site_representation: Optional[Dict[str, Any]] = None
    geometry_validation_report: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Detailed geometric validation statistics")
    overall_confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    warnings: List[str] = Field(default_factory=list)


class FloorPlanExtractionResponse(BaseModel):
    drawing_id: str
    filename: str
    file_type: str
    floorplan: FloorPlan2D
    preview_overlay_base64: str = Field(
        ...,
        description="Base64 encoded PNG overlay showing OpenCV detections on the original drawing"
    )
    summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Statistical summary of detected architectural elements"
    )


class FloorPlan3DGenerateRequest(BaseModel):
    floorplan: FloorPlan2D
    floors: int = Field(default=2, ge=1, le=50, description="Number of building storeys")
    floor_height_m: float = Field(default=3.0, ge=2.2, le=6.0, description="Floor-to-floor height in meters")
    building_type: Optional[str] = Field(default="Commercial", description="Building typology")
    roof_type: str = Field(default="flat", description="'flat', 'parapet', or 'gable'")
    building_name: Optional[str] = Field(default="2D Floorplan Generated Twin")
