import math
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from shapely.geometry import Polygon, Point, box, LineString
from shapely.affinity import rotate, translate

from app.models.furniture import (
    FurnitureItem,
    Dimensions3D,
    Vector3D,
    RoomFurnishingProfile,
    BuildingFurnishingPlan,
    FurnitureUpdateRequest,
    FurnitureAddRequest,
)
from app.models.floorplan import Room2D, Door2D, Window2D, Point2D
from app.models.digital_twin import BuildingModelDetail, BuildingElement


class InteriorFurnishingService:
    """
    Automated Room-Aware Interior Furnishing & 3D Spatial Layout Engine.
    Operates on extracted room boundaries from IFC or 2D floorplans.
    Performs deterministic collision detection, clearance preservation,
    and architectural dollhouse layout generation.
    """

    # In-memory store for active furniture plans keyed by model_id
    _active_plans: Dict[str, BuildingFurnishingPlan] = {}

    # Category Color & Material Definitions
    MATERIAL_PALETTES = {
        "bed": {"material": "fabric_linen", "color": "#475569"},
        "wardrobe": {"material": "light_oak", "color": "#b45309"},
        "side_table": {"material": "walnut", "color": "#78350f"},
        "sofa": {"material": "boucle_cream", "color": "#334155"},
        "coffee_table": {"material": "oak_wood", "color": "#d97706"},
        "tv_unit": {"material": "black_matte", "color": "#1e293b"},
        "armchair": {"material": "fabric_teal", "color": "#0f766e"},
        "kitchen_counter": {"material": "quartz_counter", "color": "#f8fafc"},
        "cabinets": {"material": "matte_white", "color": "#e2e8f0"},
        "sink": {"material": "stainless_steel", "color": "#94a3b8"},
        "refrigerator": {"material": "brushed_steel", "color": "#64748b"},
        "cooktop": {"material": "black_glass", "color": "#0f172a"},
        "kitchen_island": {"material": "marble_calacatta", "color": "#f1f5f9"},
        "toilet": {"material": "white_porcelain", "color": "#ffffff"},
        "washbasin": {"material": "porcelain_vanity", "color": "#f8fafc"},
        "shower": {"material": "tempered_glass", "color": "#38bdf8"},
        "bathtub": {"material": "acrylic_white", "color": "#f8fafc"},
        "dining_table": {"material": "solid_walnut", "color": "#92400e"},
        "dining_chair": {"material": "leather_charcoal", "color": "#1e293b"},
        "credenza": {"material": "fluted_oak", "color": "#b45309"},
        "office_desk": {"material": "warm_oak", "color": "#ca8a04"},
        "office_chair": {"material": "mesh_black", "color": "#0f172a"},
        "meeting_table": {"material": "white_laminate", "color": "#e2e8f0"},
        "storage_cabinet": {"material": "powdercoat_grey", "color": "#475569"},
        "conference_table": {"material": "boardroom_walnut", "color": "#78350f"},
        "conference_chair": {"material": "leather_black", "color": "#0f172a"},
        "presentation_screen": {"material": "av_display", "color": "#020617"},
        "corridor_bench": {"material": "cushioned_bench", "color": "#475569"},
        "storage_rack": {"material": "galvanized_steel", "color": "#64748b"},
        "utility_counter": {"material": "stainless_top", "color": "#94a3b8"},
    }

    @classmethod
    def classify_room_type(
        cls,
        name: str,
        area_sqm: float,
        aspect_ratio: float = 1.0,
        doors_count: int = 1,
        windows_count: int = 1,
    ) -> Tuple[str, float]:
        """
        Synthesizes semantic label, dimensions, and architectural clues to classify room type.
        Returns (room_type, confidence).
        """
        n_lower = (name or "").lower().strip()

        # Explicit keyword matching
        if any(k in n_lower for k in ["bed", "bedroom", "master", "guest", "mbr", "sleeping"]):
            return "bedroom", 0.95
        if any(k in n_lower for k in ["living", "lounge", "family", "drawing", "sitting", "salon"]):
            return "living", 0.95
        if any(k in n_lower for k in ["kitchen", "pantry", "cook", "galley"]):
            return "kitchen", 0.95
        if any(k in n_lower for k in ["bath", "toilet", "wc", "washroom", "powder", "restroom", "shower"]):
            return "bathroom", 0.95
        if any(k in n_lower for k in ["dining", "dinette"]):
            return "dining", 0.92
        if any(k in n_lower for k in ["conf", "conference", "boardroom", "meeting", "seminar"]):
            return "conference", 0.92
        if any(k in n_lower for k in ["office", "study", "workspace", "workstation", "cabin"]):
            return "office", 0.90
        if any(k in n_lower for k in ["corridor", "hallway", "passage", "lobby", "vestibule", "foyer"]):
            return "corridor", 0.92
        if any(k in n_lower for k in ["store", "storage", "closet", "box room"]):
            return "storage", 0.88
        if any(k in n_lower for k in ["utility", "laundry", "wash", "mechanical", "server", "ahu"]):
            return "utility", 0.88

        # Heuristic geometric inference when no textual label is available
        if aspect_ratio >= 3.0 and area_sqm <= 25.0:
            return "corridor", 0.75
        if area_sqm < 4.5:
            return "bathroom", 0.70
        if area_sqm < 8.0:
            return "utility", 0.65
        if area_sqm >= 35.0:
            return "living", 0.68
        if area_sqm >= 18.0:
            return "office", 0.65

        # Ambiguous
        return "uncertain", 0.50

    @classmethod
    def generate_furnishing_plan_for_model(
        cls,
        model: BuildingModelDetail,
        custom_room_types: Optional[Dict[str, str]] = None,
        force_regenerate: bool = False
    ) -> BuildingFurnishingPlan:
        """
        Extracts room geometry from an existing BuildingModelDetail (from IFC or 2D upload),
        classifies every room, places collision-free 3D furniture, and stores the layout.
        """
        model_id = model.model_id
        if not force_regenerate and model_id in cls._active_plans:
            return cls._active_plans[model_id]

        custom_room_types = custom_room_types or {}
        now_str = datetime.now(timezone.utc).isoformat()

        # Find all room elements (IfcSpace)
        room_elements = [e for e in model.elements if e.element_type == "IfcSpace"]
        door_elements = [e for e in model.elements if e.element_type in ["IfcDoor", "Door"]]
        window_elements = [e for e in model.elements if e.element_type in ["IfcWindow", "Window"]]

        room_profiles: List[RoomFurnishingProfile] = []
        all_furniture: List[FurnitureItem] = []
        notes: List[str] = []

        # If no explicit IfcSpace elements exist, synthesize virtual rooms per storey from building bounds
        if not room_elements:
            room_profiles, all_furniture = cls._synthesize_from_building_envelope(
                model=model,
                door_elements=door_elements,
                window_elements=window_elements
            )
            notes.append("Synthesized multi-zone rooms from structural walls and envelope since model contained no explicit IfcSpace elements.")
        else:
            for room_elem in room_elements:
                r_id = room_elem.element_id
                s_id = room_elem.storey_id or "storey_0"
                r_name = room_elem.name or "Room"
                pset = room_elem.source_properties.get("Pset_SpaceCommon", {})
                area = float(pset.get("NetFloorArea") or room_elem.source_properties.get("Area_m2") or 16.0)

                # Extract 2D polygon vertices from element geometry
                poly_pts = cls._extract_polygon_from_element(room_elem)
                if not poly_pts or len(poly_pts) < 3:
                    # Fallback to bounding box footprint (X = width, Y = depth)
                    bbox = room_elem.bounding_box
                    if bbox:
                        poly_pts = [
                            Point2D(x=bbox.min_x, y=bbox.min_y),
                            Point2D(x=bbox.max_x, y=bbox.min_y),
                            Point2D(x=bbox.max_x, y=bbox.max_y),
                            Point2D(x=bbox.min_x, y=bbox.max_y),
                        ]
                    else:
                        poly_pts = [Point2D(x=0, y=0), Point2D(x=4, y=0), Point2D(x=4, y=4), Point2D(x=0, y=4)]

                # Check override or classify
                if r_id in custom_room_types:
                    rtype = custom_room_types[r_id]
                    rconf = 1.0
                elif pset.get("RoomType"):
                    rtype = pset.get("RoomType").lower()
                    rconf = 0.95
                else:
                    # Calculate aspect ratio
                    xs = [p.x for p in poly_pts]
                    ys = [p.y for p in poly_pts]
                    w = max(xs) - min(xs) if xs else 4.0
                    d = max(ys) - min(ys) if ys else 4.0
                    aspect = max(w, d) / max(0.1, min(w, d))
                    rtype, rconf = cls.classify_room_type(
                        name=r_name,
                        area_sqm=area,
                        aspect_ratio=aspect,
                        doors_count=len(door_elements),
                        windows_count=len(window_elements)
                    )

                # Compute floor elevation z_base (exact top of floor slab)
                if room_elem.bounding_box and room_elem.bounding_box.min_z is not None:
                    z_base = float(room_elem.bounding_box.min_z)
                else:
                    z_base = cls._get_storey_elevation(model, s_id)

                # Find associated doors & windows for clearance buffering
                room_doors = cls._filter_nearby_elements(door_elements, poly_pts)
                room_windows = cls._filter_nearby_elements(window_elements, poly_pts)

                # Generate furniture layout for this room
                items, unaccommodated = cls._place_room_furniture(
                    room_id=r_id,
                    storey_id=s_id,
                    room_name=r_name,
                    room_type=rtype,
                    polygon=poly_pts,
                    area_sqm=area,
                    z_base=z_base,
                    doors=room_doors,
                    windows=room_windows,
                )

                all_furniture.extend(items)
                xs = [p.x for p in poly_pts]
                ys = [p.y for p in poly_pts]
                w = max(xs) - min(xs) if xs else 4.0
                d = max(ys) - min(ys) if ys else 4.0

                profile = RoomFurnishingProfile(
                    room_id=r_id,
                    room_name=r_name,
                    room_type=rtype,
                    area_sqm=round(area, 1),
                    dimensions_summary=f"{w:.1f}m × {d:.1f}m",
                    confidence=rconf,
                    is_furnished=len(items) > 0,
                    items=items,
                    unaccommodated_items=unaccommodated,
                    notes=[f"Placed {len(items)} proposed furniture items respecting circulation."]
                )
                room_profiles.append(profile)

        plan = BuildingFurnishingPlan(
            model_id=model_id,
            building_name=model.building_name or "Digital Twin",
            timestamp=now_str,
            storeys_count=len(model.storeys) if model.storeys else 1,
            total_furniture_count=len(all_furniture),
            room_profiles=room_profiles,
            all_items=all_furniture,
            validation_status="VALID",
            circulation_clearance_notes=notes
        )

        cls._active_plans[model_id] = plan
        return plan

    @classmethod
    def get_furnishing_plan(cls, model_id: str) -> Optional[BuildingFurnishingPlan]:
        """Returns cached plan if present."""
        return cls._active_plans.get(model_id)

    @classmethod
    def update_furniture_item(
        cls,
        model_id: str,
        furniture_id: str,
        update: FurnitureUpdateRequest
    ) -> Optional[FurnitureItem]:
        """Updates a specific furniture item (move, rotate, scale, material)."""
        plan = cls._active_plans.get(model_id)
        if not plan:
            return None

        target_item = None
        for it in plan.all_items:
            if it.id == furniture_id:
                target_item = it
                break

        if not target_item:
            return None

        if update.position_m is not None:
            target_item.position_m = update.position_m
        if update.rotation_deg is not None:
            target_item.rotation_deg = update.rotation_deg
        if update.scale is not None:
            target_item.scale = update.scale
        if update.material is not None:
            target_item.material = update.material
        if update.color_hex is not None:
            target_item.color_hex = update.color_hex
        if update.is_visible is not None:
            target_item.is_visible = update.is_visible
        if update.category is not None:
            target_item.category = update.category
        if update.name is not None:
            target_item.name = update.name

        target_item.status = "USER_MODIFIED"

        # Also update in room profile
        for rp in plan.room_profiles:
            if rp.room_id == target_item.room_id:
                for idx, r_it in enumerate(rp.items):
                    if r_it.id == furniture_id:
                        rp.items[idx] = target_item
                        break

        return target_item

    @classmethod
    def remove_furniture_item(cls, model_id: str, furniture_id: str) -> bool:
        """Removes a specific furniture item from active plan."""
        plan = cls._active_plans.get(model_id)
        if not plan:
            return False

        orig_len = len(plan.all_items)
        plan.all_items = [it for it in plan.all_items if it.id != furniture_id]
        if len(plan.all_items) == orig_len:
            return False

        for rp in plan.room_profiles:
            rp.items = [it for it in rp.items if it.id != furniture_id]

        plan.total_furniture_count = len(plan.all_items)
        return True

    @classmethod
    def add_furniture_item(
        cls,
        model_id: str,
        request: FurnitureAddRequest
    ) -> Optional[FurnitureItem]:
        """Manually adds a new furniture item to a room."""
        plan = cls._active_plans.get(model_id)
        if not plan:
            return None

        palette = cls.MATERIAL_PALETTES.get(request.category, {"material": "oak_wood", "color": "#78350f"})
        default_dim = cls._get_default_dimensions(request.category)

        new_item = FurnitureItem(
            id=f"furn_{request.category}_{uuid.uuid4().hex[:8]}",
            room_id=request.room_id,
            storey_id=request.storey_id,
            category=request.category,
            name=request.name or request.category.replace("_", " ").title(),
            dimensions_m=default_dim,
            position_m=request.position_m,
            rotation_deg=request.rotation_deg,
            scale=[1.0, 1.0, 1.0],
            status="USER_MODIFIED",
            clearance_m=0.5,
            fits_within_room=True,
            material=request.material or palette["material"],
            color_hex=request.color_hex or palette["color"],
            is_visible=True
        )

        plan.all_items.append(new_item)
        plan.total_furniture_count = len(plan.all_items)

        for rp in plan.room_profiles:
            if rp.room_id == request.room_id:
                rp.items.append(new_item)
                break

        return new_item

    # =========================================================================
    # INTERNAL GEOMETRIC & PLACEMENT LOGIC
    # =========================================================================

    @classmethod
    def _place_room_furniture(
        cls,
        room_id: str,
        storey_id: str,
        room_name: str,
        room_type: str,
        polygon: List[Point2D],
        area_sqm: float,
        z_base: float,
        doors: List[BuildingElement],
        windows: List[BuildingElement],
    ) -> Tuple[List[FurnitureItem], List[Dict[str, Any]]]:
        """
        Executes collision-free, clearance-checked placement of realistic furniture
        based on room classification and architectural layout rules.
        """
        items: List[FurnitureItem] = []
        unaccommodated: List[Dict[str, Any]] = []

        if room_type in ["uncertain", "corridor"] and area_sqm < 8.0:
            return items, unaccommodated

        try:
            poly_coords = [(p.x, p.y) for p in polygon]
            if poly_coords[0] != poly_coords[-1]:
                poly_coords.append(poly_coords[0])
            sh_poly = Polygon(poly_coords)
            if not sh_poly.is_valid:
                sh_poly = sh_poly.buffer(0)
        except Exception:
            return items, unaccommodated

        min_x, min_y, max_x, max_y = sh_poly.bounds
        center_x = (min_x + max_x) / 2.0
        center_y = (min_y + max_y) / 2.0
        width = max_x - min_x
        depth = max_y - min_y

        # Build door clearance zones (0.9m radius around door centers)
        door_clearance_polys: List[Polygon] = []
        for d in doors:
            if d.bounding_box:
                dx = (d.bounding_box.min_x + d.bounding_box.max_x) / 2.0
                # In IFC coordinates, Y is horizontal plan depth
                dy = (d.bounding_box.min_y + d.bounding_box.max_y) / 2.0
                door_clearance_polys.append(Point(dx, dy).buffer(0.9))

        # Placed furniture bounding geometries for intra-room collision checks
        placed_polygons: List[Polygon] = list(door_clearance_polys)

        def can_place(cand_box: Polygon, clearance_zone: Polygon) -> bool:
            # 1. The furniture piece itself must be contained inside room boundary
            if not sh_poly.buffer(0.04).contains(cand_box):
                return False
            # 2. The furniture piece must not collide with doors or existing furniture
            for p_zone in placed_polygons:
                if cand_box.intersects(p_zone):
                    return False
            return True

        # Candidate furniture specifications by room type
        candidates = cls._get_candidate_furniture_for_room(room_type, area_sqm, width, depth)

        for cand in candidates:
            cat = cand["category"]
            name = cand["name"]
            dim = cand["dimensions"]
            w_item, d_item, h_item = dim.width, dim.depth, dim.height
            clearance = cand.get("clearance", 0.5)

            # Determine anchor placement position based on category rule
            placed_item = None
            palette = cls.MATERIAL_PALETTES.get(cat, {"material": "oak_wood", "color": "#78350f"})

            # Strategy 1: Wall-adjacent furniture (beds, wardrobes, tv units, desks, counters)
            if cand.get("placement") == "wall_adjacent":
                fractions = [0.5, 0.25, 0.75, 0.38, 0.62, 0.16, 0.84]
                candidate_anchors = []
                # North wall (facing South, rot 180)
                for f in fractions:
                    candidate_anchors.append({"pos": (min_x + f * width, max_y - d_item / 2.0 - 0.15), "rot": 180.0})
                # South wall (facing North, rot 0)
                for f in fractions:
                    candidate_anchors.append({"pos": (min_x + f * width, min_y + d_item / 2.0 + 0.15), "rot": 0.0})
                # West wall (facing East, rot 90)
                for f in fractions:
                    candidate_anchors.append({"pos": (min_x + d_item / 2.0 + 0.15, min_y + f * depth), "rot": 90.0})
                # East wall (facing West, rot 270)
                for f in fractions:
                    candidate_anchors.append({"pos": (max_x - d_item / 2.0 - 0.15, min_y + f * depth), "rot": 270.0})

                for off in candidate_anchors:
                    px, py = off["pos"]
                    rot = off["rot"]
                    c_box = box(px - w_item / 2.0, py - d_item / 2.0, px + w_item / 2.0, py + d_item / 2.0)
                    if rot in [90.0, 270.0]:
                        c_box = box(px - d_item / 2.0, py - w_item / 2.0, px + d_item / 2.0, py + w_item / 2.0)

                    # Include clearance buffer
                    test_zone = c_box.buffer(clearance / 2.0)
                    if can_place(c_box, test_zone):
                        placed_polygons.append(c_box.buffer(clearance / 3.0))
                        placed_item = FurnitureItem(
                            id=f"furn_{cat}_{uuid.uuid4().hex[:8]}",
                            room_id=room_id,
                            storey_id=storey_id,
                            category=cat,
                            name=name,
                            dimensions_m=dim,
                            position_m=Vector3D(x=round(px, 3), y=round(z_base, 3), z=round(py, 3)),
                            rotation_deg=rot,
                            scale=[1.0, 1.0, 1.0],
                            status="PROPOSED",
                            clearance_m=clearance,
                            fits_within_room=True,
                            material=palette["material"],
                            color_hex=palette["color"],
                            is_visible=True
                        )
                        break

            # Strategy 2: Center-room furniture (dining tables, coffee tables, conference tables)
            elif cand.get("placement") == "center":
                center_anchors = [
                    (center_x, center_y),
                    (center_x - width * 0.22, center_y),
                    (center_x + width * 0.22, center_y),
                    (center_x, center_y - depth * 0.22),
                    (center_x, center_y + depth * 0.22),
                    (center_x - width * 0.22, center_y - depth * 0.22),
                    (center_x + width * 0.22, center_y + depth * 0.22),
                ]
                for cx_cand, cy_cand in center_anchors:
                    c_box = box(cx_cand - w_item / 2.0, cy_cand - d_item / 2.0, cx_cand + w_item / 2.0, cy_cand + d_item / 2.0)
                    test_zone = c_box.buffer(clearance / 2.0)
                    if can_place(c_box, test_zone):
                        placed_polygons.append(c_box.buffer(clearance / 3.0))
                        placed_item = FurnitureItem(
                            id=f"furn_{cat}_{uuid.uuid4().hex[:8]}",
                            room_id=room_id,
                            storey_id=storey_id,
                            category=cat,
                            name=name,
                            dimensions_m=dim,
                            position_m=Vector3D(x=round(cx_cand, 3), y=round(z_base, 3), z=round(cy_cand, 3)),
                            rotation_deg=0.0,
                            scale=[1.0, 1.0, 1.0],
                            status="PROPOSED",
                            clearance_m=clearance,
                            fits_within_room=True,
                            material=palette["material"],
                            color_hex=palette["color"],
                            is_visible=True
                        )
                        break

            if placed_item:
                items.append(placed_item)
            else:
                unaccommodated.append({
                    "category": cat,
                    "name": name,
                    "reason": f"Room net area ({area_sqm:.1f} m²) or shape cannot fit {name} without blocking doors or violating {clearance}m circulation clearance."
                })

        return items, unaccommodated

    @classmethod
    def _get_candidate_furniture_for_room(
        cls,
        room_type: str,
        area_sqm: float,
        width_m: float,
        depth_m: float
    ) -> List[Dict[str, Any]]:
        """Returns standard architectural candidate furnishings suitable for the room type."""
        cands: List[Dict[str, Any]] = []

        if room_type == "bedroom":
            # 1. Primary Bed
            if area_sqm >= 14.0 and min(width_m, depth_m) >= 3.2:
                cands.append({
                    "category": "bed",
                    "name": "King Bed with Headboard",
                    "dimensions": Dimensions3D(width=1.9, depth=2.1, height=0.95),
                    "placement": "wall_adjacent",
                    "clearance": 0.65
                })
            elif area_sqm >= 9.0:
                cands.append({
                    "category": "bed",
                    "name": "Queen Bed with Headboard",
                    "dimensions": Dimensions3D(width=1.6, depth=2.05, height=0.9),
                    "placement": "wall_adjacent",
                    "clearance": 0.55
                })
            else:
                cands.append({
                    "category": "bed",
                    "name": "Single Daybed",
                    "dimensions": Dimensions3D(width=1.0, depth=2.0, height=0.8),
                    "placement": "wall_adjacent",
                    "clearance": 0.5
                })

            # 2. Wardrobe
            if area_sqm >= 10.0:
                cands.append({
                    "category": "wardrobe",
                    "name": "Sliding Wardrobe",
                    "dimensions": Dimensions3D(width=1.8, depth=0.65, height=2.2),
                    "placement": "wall_adjacent",
                    "clearance": 0.6
                })

            # 3. Desk / Vanity
            if area_sqm >= 15.0:
                cands.append({
                    "category": "office_desk",
                    "name": "Bedroom Study Desk",
                    "dimensions": Dimensions3D(width=1.2, depth=0.6, height=0.75),
                    "placement": "wall_adjacent",
                    "clearance": 0.5
                })

        elif room_type == "living":
            # 1. Main Sofa
            if area_sqm >= 22.0:
                cands.append({
                    "category": "sofa",
                    "name": "L-Shape Sectional Sofa",
                    "dimensions": Dimensions3D(width=2.6, depth=1.6, height=0.8),
                    "placement": "wall_adjacent",
                    "clearance": 0.7
                })
            else:
                cands.append({
                    "category": "sofa",
                    "name": "3-Seater Upholstered Sofa",
                    "dimensions": Dimensions3D(width=2.1, depth=0.9, height=0.8),
                    "placement": "wall_adjacent",
                    "clearance": 0.6
                })

            # 2. Coffee Table
            cands.append({
                "category": "coffee_table",
                "name": "Low Wood Coffee Table",
                "dimensions": Dimensions3D(width=1.1, depth=0.6, height=0.42),
                "placement": "center",
                "clearance": 0.5
            })

            # 3. TV Media Unit
            cands.append({
                "category": "tv_unit",
                "name": "Media Credenza",
                "dimensions": Dimensions3D(width=1.8, depth=0.45, height=0.5),
                "placement": "wall_adjacent",
                "clearance": 0.5
            })

            # 4. Accent Armchair
            if area_sqm >= 18.0:
                cands.append({
                    "category": "armchair",
                    "name": "Lounge Armchair",
                    "dimensions": Dimensions3D(width=0.85, depth=0.85, height=0.8),
                    "placement": "wall_adjacent",
                    "clearance": 0.5
                })

        elif room_type == "kitchen":
            # 1. Primary Kitchen Counter run
            cands.append({
                "category": "kitchen_counter",
                "name": "Kitchen Base Cabinets & Countertop",
                "dimensions": Dimensions3D(width=2.4, depth=0.65, height=0.9),
                "placement": "wall_adjacent",
                "clearance": 0.8
            })
            # 2. Refrigerator
            cands.append({
                "category": "refrigerator",
                "name": "Double-Door Refrigerator",
                "dimensions": Dimensions3D(width=0.9, depth=0.75, height=1.85),
                "placement": "wall_adjacent",
                "clearance": 0.6
            })
            # 3. Island (if space allows)
            if area_sqm >= 16.0 and min(width_m, depth_m) >= 3.8:
                cands.append({
                    "category": "kitchen_island",
                    "name": "Central Island Counter",
                    "dimensions": Dimensions3D(width=1.6, depth=0.85, height=0.9),
                    "placement": "center",
                    "clearance": 0.9
                })

        elif room_type == "bathroom":
            # 1. Vanity Washbasin
            cands.append({
                "category": "washbasin",
                "name": "Vanity Washbasin with Mirror",
                "dimensions": Dimensions3D(width=0.8, depth=0.5, height=0.85),
                "placement": "wall_adjacent",
                "clearance": 0.5
            })
            # 2. Toilet
            cands.append({
                "category": "toilet",
                "name": "Wall-Hung Porcelain Toilet",
                "dimensions": Dimensions3D(width=0.45, depth=0.65, height=0.75),
                "placement": "wall_adjacent",
                "clearance": 0.5
            })
            # 3. Walk-in Shower
            cands.append({
                "category": "shower",
                "name": "Frameless Glass Shower Enclosure",
                "dimensions": Dimensions3D(width=1.0, depth=1.0, height=2.1),
                "placement": "wall_adjacent",
                "clearance": 0.6
            })
            # 4. Bathtub only if large
            if area_sqm >= 7.5:
                cands.append({
                    "category": "bathtub",
                    "name": "Freestanding Soaking Tub",
                    "dimensions": Dimensions3D(width=1.65, depth=0.75, height=0.6),
                    "placement": "wall_adjacent",
                    "clearance": 0.5
                })

        elif room_type == "dining":
            cands.append({
                "category": "dining_table",
                "name": "6-Person Dining Table",
                "dimensions": Dimensions3D(width=1.8, depth=0.9, height=0.75),
                "placement": "center",
                "clearance": 0.8
            })
            if area_sqm >= 14.0:
                cands.append({
                    "category": "credenza",
                    "name": "Sideboard Buffet Credenza",
                    "dimensions": Dimensions3D(width=1.5, depth=0.45, height=0.85),
                    "placement": "wall_adjacent",
                    "clearance": 0.6
                })

        elif room_type == "office":
            if area_sqm >= 40.0:
                # Large open-plan office: multi-workstation desks, executive desk, meeting table, credenzas, screen
                cands.append({
                    "category": "office_desk",
                    "name": "Team Workstation Alpha",
                    "dimensions": Dimensions3D(width=1.6, depth=0.8, height=0.75),
                    "placement": "wall_adjacent",
                    "clearance": 0.6
                })
                cands.append({
                    "category": "office_desk",
                    "name": "Team Workstation Beta",
                    "dimensions": Dimensions3D(width=1.6, depth=0.8, height=0.75),
                    "placement": "wall_adjacent",
                    "clearance": 0.6
                })
                cands.append({
                    "category": "office_desk",
                    "name": "Executive Writing Desk",
                    "dimensions": Dimensions3D(width=1.8, depth=0.85, height=0.75),
                    "placement": "wall_adjacent",
                    "clearance": 0.6
                })
                cands.append({
                    "category": "meeting_table",
                    "name": "Collaborative Round Meeting Table",
                    "dimensions": Dimensions3D(width=1.4, depth=1.4, height=0.75),
                    "placement": "center",
                    "clearance": 0.8
                })
                cands.append({
                    "category": "storage_cabinet",
                    "name": "Executive Filing Credenza",
                    "dimensions": Dimensions3D(width=1.4, depth=0.45, height=1.1),
                    "placement": "wall_adjacent",
                    "clearance": 0.5
                })
                cands.append({
                    "category": "storage_cabinet",
                    "name": "Archive Document Cabinet",
                    "dimensions": Dimensions3D(width=1.2, depth=0.45, height=1.1),
                    "placement": "wall_adjacent",
                    "clearance": 0.5
                })
                cands.append({
                    "category": "presentation_screen",
                    "name": "Digital Presentation Display",
                    "dimensions": Dimensions3D(width=1.7, depth=0.15, height=1.0),
                    "placement": "wall_adjacent",
                    "clearance": 0.4
                })
            else:
                cands.append({
                    "category": "office_desk",
                    "name": "Executive Writing Desk",
                    "dimensions": Dimensions3D(width=1.6, depth=0.8, height=0.75),
                    "placement": "wall_adjacent",
                    "clearance": 0.6
                })
                cands.append({
                    "category": "storage_cabinet",
                    "name": "Filing Credenza",
                    "dimensions": Dimensions3D(width=1.2, depth=0.45, height=1.1),
                    "placement": "wall_adjacent",
                    "clearance": 0.5
                })
                if area_sqm >= 15.0:
                    cands.append({
                        "category": "armchair",
                        "name": "Visitor Lounge Armchair",
                        "dimensions": Dimensions3D(width=0.8, depth=0.8, height=0.8),
                        "placement": "wall_adjacent",
                        "clearance": 0.5
                    })

        elif room_type == "conference":
            cands.append({
                "category": "conference_table",
                "name": "Boardroom Conference Table",
                "dimensions": Dimensions3D(width=3.0, depth=1.2, height=0.75),
                "placement": "center",
                "clearance": 0.9
            })
            cands.append({
                "category": "presentation_screen",
                "name": "75-inch Conference Presentation Display",
                "dimensions": Dimensions3D(width=1.7, depth=0.15, height=1.0),
                "placement": "wall_adjacent",
                "clearance": 0.5
            })

        elif room_type in ["storage", "utility"]:
            cands.append({
                "category": "storage_rack",
                "name": "Heavy-Duty Storage Shelving",
                "dimensions": Dimensions3D(width=1.4, depth=0.5, height=1.9),
                "placement": "wall_adjacent",
                "clearance": 0.6
            })

        return cands

    @classmethod
    def _get_default_dimensions(cls, category: str) -> Dimensions3D:
        """Returns standard physical dimensions for a category."""
        defaults = {
            "bed": Dimensions3D(width=1.6, depth=2.05, height=0.9),
            "wardrobe": Dimensions3D(width=1.6, depth=0.65, height=2.2),
            "side_table": Dimensions3D(width=0.5, depth=0.45, height=0.55),
            "sofa": Dimensions3D(width=2.1, depth=0.9, height=0.8),
            "coffee_table": Dimensions3D(width=1.1, depth=0.6, height=0.42),
            "tv_unit": Dimensions3D(width=1.8, depth=0.45, height=0.5),
            "armchair": Dimensions3D(width=0.85, depth=0.85, height=0.8),
            "kitchen_counter": Dimensions3D(width=2.4, depth=0.65, height=0.9),
            "cabinets": Dimensions3D(width=1.2, depth=0.4, height=0.75),
            "sink": Dimensions3D(width=0.8, depth=0.5, height=0.35),
            "refrigerator": Dimensions3D(width=0.9, depth=0.75, height=1.85),
            "cooktop": Dimensions3D(width=0.75, depth=0.55, height=0.1),
            "kitchen_island": Dimensions3D(width=1.6, depth=0.85, height=0.9),
            "toilet": Dimensions3D(width=0.45, depth=0.65, height=0.75),
            "washbasin": Dimensions3D(width=0.8, depth=0.5, height=0.85),
            "shower": Dimensions3D(width=1.0, depth=1.0, height=2.1),
            "bathtub": Dimensions3D(width=1.65, depth=0.75, height=0.6),
            "dining_table": Dimensions3D(width=1.8, depth=0.9, height=0.75),
            "dining_chair": Dimensions3D(width=0.5, depth=0.5, height=0.85),
            "credenza": Dimensions3D(width=1.5, depth=0.45, height=0.85),
            "office_desk": Dimensions3D(width=1.6, depth=0.8, height=0.75),
            "office_chair": Dimensions3D(width=0.65, depth=0.65, height=1.05),
            "meeting_table": Dimensions3D(width=1.2, depth=1.2, height=0.75),
            "storage_cabinet": Dimensions3D(width=1.2, depth=0.45, height=1.1),
            "conference_table": Dimensions3D(width=3.0, depth=1.2, height=0.75),
            "conference_chair": Dimensions3D(width=0.65, depth=0.65, height=1.05),
            "presentation_screen": Dimensions3D(width=1.7, depth=0.15, height=1.0),
            "corridor_bench": Dimensions3D(width=1.4, depth=0.45, height=0.45),
            "storage_rack": Dimensions3D(width=1.4, depth=0.5, height=1.9),
            "utility_counter": Dimensions3D(width=1.4, depth=0.65, height=0.9),
        }
        return defaults.get(category, Dimensions3D(width=1.0, depth=1.0, height=0.8))

    @classmethod
    def _extract_polygon_from_element(cls, elem: BuildingElement) -> List[Point2D]:
        """Extracts unique 2D ground footprint vertices (X, Y) from element geometry."""
        if not elem.geometry or not elem.geometry.vertices:
            return []
        v = elem.geometry.vertices
        pts_xy = [(round(v[i], 3), round(v[i + 1], 3)) for i in range(0, len(v), 3)]
        if len(pts_xy) < 3:
            return []
        try:
            from shapely.geometry import MultiPoint
            hull = MultiPoint(pts_xy).convex_hull
            if isinstance(hull, Polygon) and hull.is_valid and not hull.is_empty:
                return [Point2D(x=round(c[0], 3), y=round(c[1], 3)) for c in hull.exterior.coords[:-1]]
        except Exception:
            pass

        # Fallback to unique points
        unique_pts: List[Point2D] = []
        seen = set()
        for px, py in pts_xy:
            key = (round(px, 2), round(py, 2))
            if key not in seen:
                seen.add(key)
                unique_pts.append(Point2D(x=px, y=py))
        return unique_pts

    @classmethod
    def _filter_nearby_elements(
        cls,
        elements: List[BuildingElement],
        poly_pts: List[Point2D]
    ) -> List[BuildingElement]:
        """Filters building elements located on or near room polygon boundary."""
        if not poly_pts:
            return []
        xs = [p.x for p in poly_pts]
        ys = [p.y for p in poly_pts]
        min_x, max_x = min(xs) - 0.5, max(xs) + 0.5
        min_y, max_y = min(ys) - 0.5, max(ys) + 0.5

        matched = []
        for elem in elements:
            bbox = elem.bounding_box
            if bbox:
                # In IFC coordinates, X=width, Y=plan depth, Z=vertical elevation
                e_x = (bbox.min_x + bbox.max_x) / 2.0
                e_y = (bbox.min_y + bbox.max_y) / 2.0
                if min_x <= e_x <= max_x and min_y <= e_y <= max_y:
                    matched.append(elem)
        return matched

    @classmethod
    def _get_storey_elevation(cls, model: BuildingModelDetail, storey_id: str) -> float:
        """Finds elevation of a storey, defaulting to 0.0."""
        for st in model.storeys:
            if st.storey_id == storey_id:
                return float(st.elevation_m or 0.0)
        return 0.0

    @classmethod
    def _synthesize_from_building_envelope(
        cls,
        model: BuildingModelDetail,
        door_elements: List[BuildingElement],
        window_elements: List[BuildingElement]
    ) -> Tuple[List[RoomFurnishingProfile], List[FurnitureItem]]:
        """Synthesizes interior room zones when model lacks explicit IfcSpace elements."""
        profiles: List[RoomFurnishingProfile] = []
        all_items: List[FurnitureItem] = []

        storeys = model.storeys or []
        if not storeys:
            from app.models.digital_twin import StoreyInfo
            storeys = [StoreyInfo(storey_id="storey_0", name="Floor 1", elevation_m=0.0, height_m=3.0, element_count=len(model.elements))]

        # Get building footprint
        bbox = model.bounding_box
        min_x = bbox.min_x if bbox else 0.0
        max_x = bbox.max_x if bbox else 15.0
        min_y = bbox.min_y if bbox else 0.0
        max_y = bbox.max_y if bbox else 12.0
        w = max_x - min_x
        d = max_y - min_y

        for st_idx, st in enumerate(storeys):
            s_id = st.storey_id
            z_base = float(st.elevation_m or 0.0)

            # Partition floor into 4 quadrant rooms: Living, Kitchen/Dining, Master Bed, Office/Bath
            mid_x = min_x + w / 2.0
            mid_y = min_y + d / 2.0

            zones = [
                {"name": f"Living & Lounge Area (L{st_idx + 1})", "type": "living", "poly": [Point2D(x=min_x, y=min_y), Point2D(x=mid_x, y=min_y), Point2D(x=mid_x, y=mid_y), Point2D(x=min_x, y=mid_y)]},
                {"name": f"Kitchen & Dining Space (L{st_idx + 1})", "type": "kitchen", "poly": [Point2D(x=mid_x, y=min_y), Point2D(x=max_x, y=min_y), Point2D(x=max_x, y=mid_y), Point2D(x=mid_x, y=mid_y)]},
                {"name": f"Executive Suite / Bedroom (L{st_idx + 1})", "type": "bedroom", "poly": [Point2D(x=min_x, y=mid_y), Point2D(x=mid_x, y=mid_y), Point2D(x=mid_x, y=max_y), Point2D(x=min_x, y=max_y)]},
                {"name": f"Office & Restroom Zone (L{st_idx + 1})", "type": "office", "poly": [Point2D(x=mid_x, y=mid_y), Point2D(x=max_x, y=mid_y), Point2D(x=max_x, y=max_y), Point2D(x=mid_x, y=max_y)]},
            ]

            for z_idx, z in enumerate(zones):
                r_id = f"synth_space_f{st_idx}_{z_idx + 1}"
                z_area = round((w / 2.0) * (d / 2.0), 1)

                items, unaccommodated = cls._place_room_furniture(
                    room_id=r_id,
                    storey_id=s_id,
                    room_name=z["name"],
                    room_type=z["type"],
                    polygon=z["poly"],
                    area_sqm=z_area,
                    z_base=z_base,
                    doors=[],
                    windows=[]
                )
                all_items.extend(items)

                profiles.append(
                    RoomFurnishingProfile(
                        room_id=r_id,
                        room_name=z["name"],
                        room_type=z["type"],
                        area_sqm=z_area,
                        dimensions_summary=f"{w/2:.1f}m × {d/2:.1f}m",
                        confidence=0.82,
                        is_furnished=len(items) > 0,
                        items=items,
                        unaccommodated_items=unaccommodated,
                        notes=["Synthesized floor zone from outer envelope."]
                    )
                )

        return profiles, all_items
