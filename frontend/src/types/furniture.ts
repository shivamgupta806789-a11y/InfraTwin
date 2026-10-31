export interface Vector3D {
  x: number;
  y: number;
  z: number;
}

export interface Dimensions3D {
  width: number;
  depth: number;
  height: number;
}

export interface FurnitureItem {
  id: string;
  room_id: string;
  storey_id: string;
  category: string;
  name: string;
  dimensions_m: Dimensions3D;
  position_m: Vector3D;
  rotation_deg: number;
  scale: [number, number, number];
  status: 'PROPOSED' | 'USER_MODIFIED' | 'CONFIRMED';
  clearance_m: number;
  fits_within_room: boolean;
  unaccommodated_reason?: string | null;
  material: string;
  color_hex: string;
  is_visible: boolean;
}

export interface RoomFurnishingProfile {
  room_id: string;
  room_name: string;
  room_type: string;
  area_sqm: number;
  dimensions_summary: string;
  confidence: number;
  is_furnished: boolean;
  items: FurnitureItem[];
  unaccommodated_items: Array<{ category: string; name: string; reason: string }>;
  notes: string[];
}

export interface BuildingFurnishingPlan {
  model_id: string;
  building_name: string;
  timestamp: string;
  storeys_count: number;
  total_furniture_count: number;
  room_profiles: RoomFurnishingProfile[];
  all_items: FurnitureItem[];
  validation_status: string;
  circulation_clearance_notes: string[];
}

export interface FurnitureUpdateRequest {
  position_m?: Vector3D;
  rotation_deg?: number;
  scale?: [number, number, number];
  material?: string;
  color_hex?: string;
  is_visible?: boolean;
  category?: string;
  name?: string;
}

export interface FurnitureAddRequest {
  room_id: string;
  storey_id?: string;
  category: string;
  name?: string;
  position_m: Vector3D;
  rotation_deg?: number;
  material?: string;
  color_hex?: string;
}

export interface FurnitureCatalogCategory {
  category: string;
  display_name: string;
  default_dimensions_m: {
    width: number;
    depth: number;
    height: number;
  };
  default_material: string;
  default_color_hex: string;
}
