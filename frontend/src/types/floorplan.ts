export interface DrawingClassification {
  typology: 'individual_floor_plan' | 'elevation_drawing' | 'architectural_set' | 'colony_site_plan' | 'aerial_satellite';
  label: string;
  confidence: number;
  reasoning: string;
  detected_building_count: number;
  site_features: string[];
}

export interface ClarificationQuestion {
  question_id: string;
  field_key: string;
  question_text: string;
  reason: string;
  detected_value?: any;
  confidence: number;
  drawing_region?: { x: number; y: number; width: number; height: number } | null;
  element_id?: string | null;
  suggested_options: string[];
  status: 'pending' | 'answered' | 'confirmed';
  user_answer?: string | null;
}

export interface Point2D {
  x: number;
  y: number;
}

export interface Wall2D {
  id: string;
  start: Point2D;
  end: Point2D;
  thickness_m: number;
  confidence: number;
  wall_type: 'exterior' | 'interior' | 'partition';
  detection_status?: 'DETECTED' | 'USER_CONFIRMED' | 'INFERRED' | 'UNCERTAIN' | 'MISSING';
  source_page?: number;
  is_active: boolean;
}

export interface Door2D {
  id: string;
  wall_id?: string | null;
  position: Point2D;
  width_m: number;
  height_m: number;
  confidence: number;
  swing_direction?: string | null;
  detection_status?: 'DETECTED' | 'USER_CONFIRMED' | 'INFERRED' | 'UNCERTAIN' | 'MISSING';
  source_page?: number;
  is_active: boolean;
}

export interface Window2D {
  id: string;
  wall_id?: string | null;
  position: Point2D;
  width_m: number;
  height_m: number;
  sill_height_m: number;
  confidence: number;
  detection_status?: 'DETECTED' | 'USER_CONFIRMED' | 'INFERRED' | 'UNCERTAIN' | 'MISSING';
  source_page?: number;
  is_active: boolean;
}

export interface Room2D {
  id: string;
  name: string;
  polygon: Point2D[];
  area_sqm: number;
  room_type: 'office' | 'living' | 'bedroom' | 'corridor' | 'bathroom' | 'kitchen' | 'balcony' | 'other';
  confidence: number;
  detection_status?: 'DETECTED' | 'USER_CONFIRMED' | 'INFERRED' | 'UNCERTAIN' | 'MISSING';
  source_page?: number;
}

export interface ScaleReference {
  known_dimension_m?: number | null;
  pixels_per_meter: number;
  method: 'user_hint' | 'auto_dimension' | 'ratio_inferred' | 'default';
  pixel_span?: number | null;
}

export interface FloorPlan2D {
  drawing_id: string;
  image_width_px: number;
  image_height_px: number;
  bounds_width_m: number;
  bounds_depth_m: number;
  scale: ScaleReference;
  classification?: DrawingClassification | null;
  detected_storeys?: number | null;
  detected_floor_height_m?: number | null;
  detected_building_typology?: string | null;
  clarification_questions?: ClarificationQuestion[];
  walls: Wall2D[];
  doors: Door2D[];
  windows: Window2D[];
  rooms: Room2D[];
  overall_confidence: number;
  warnings: string[];
}

export interface FloorPlanExtractionResponse {
  drawing_id: string;
  filename: string;
  file_type: string;
  floorplan: FloorPlan2D;
  preview_overlay_base64: string;
  summary: {
    wall_count: number;
    door_count: number;
    window_count: number;
    room_count: number;
    total_room_area_sqm: number;
    footprint_width_m: number;
    footprint_depth_m: number;
    estimated_footprint_sqm: number;
    drawing_classification?: string;
    drawing_label?: string;
    detected_building_count?: number;
    detected_storeys?: number;
    detected_floor_height_m?: number;
    detected_building_typology?: string;
    clarifications_needed?: number;
  };
}

export interface FloorPlan3DGenerateRequest {
  floorplan: FloorPlan2D;
  floors: number;
  floor_height_m: number;
  building_type?: string;
  roof_type: 'flat' | 'parapet' | 'gable';
  building_name?: string;
}
