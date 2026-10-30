import uuid
import math
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

from app.models.floorplan import FloorPlan2D, Wall2D, Door2D, Window2D, Point2D
from app.models.digital_twin import (
    BuildingModelDetail,
    BuildingElement,
    ElementGeometry,
    BoundingBox3D,
    StoreyInfo,
    ImportSummaryResponse,
)
from app.services.model_store import ModelStore


class FloorplanTo3dService:
    """
    3D Geometry Extrusion & Building Synthesis Service.
    Converts normalized 2D floor plans into canonical, editable, triangulated 3D BuildingModelDetail.
    Generates walls with door and window openings, floor slabs, roofs, and storey hierarchies.
    """

    @classmethod
    def generate_building_model(
        cls,
        floorplan: FloorPlan2D,
        floors: int = 2,
        floor_height_m: float = 3.0,
        building_type: str = "Commercial",
        roof_type: str = "flat",
        building_name: str = "2D Floorplan Generated Twin",
    ) -> Tuple[BuildingModelDetail, ImportSummaryResponse]:
        """
        Synthesizes a full 3D building digital twin from 2D floorplan geometry.
        """
        model_id = f"model_{uuid.uuid4().hex[:12]}"
        now_str = datetime.now(timezone.utc).isoformat()

        # Compute plan bounding coordinates in meters
        active_walls = [w for w in floorplan.walls if w.is_active]
        if not active_walls:
            # Fallback 15x12m footprint if no active walls
            active_walls = [
                Wall2D(id="fb_w1", start=Point2D(x=0.0, y=0.0), end=Point2D(x=15.0, y=0.0), thickness_m=0.25, confidence=1.0, wall_type="exterior", is_active=True),
                Wall2D(id="fb_w2", start=Point2D(x=15.0, y=0.0), end=Point2D(x=15.0, y=12.0), thickness_m=0.25, confidence=1.0, wall_type="exterior", is_active=True),
                Wall2D(id="fb_w3", start=Point2D(x=15.0, y=12.0), end=Point2D(x=0.0, y=12.0), thickness_m=0.25, confidence=1.0, wall_type="exterior", is_active=True),
                Wall2D(id="fb_w4", start=Point2D(x=0.0, y=12.0), end=Point2D(x=0.0, y=0.0), thickness_m=0.25, confidence=1.0, wall_type="exterior", is_active=True),
            ]

        all_pts_x: List[float] = []
        all_pts_y: List[float] = []
        for w in active_walls:
            all_pts_x.extend([w.start.x, w.end.x])
            all_pts_y.extend([w.start.y, w.end.y])

        min_x = min(all_pts_x) if all_pts_x else 0.0
        max_x = max(all_pts_x) if all_pts_x else 15.0
        min_y = min(all_pts_y) if all_pts_y else 0.0
        max_y = max(all_pts_y) if all_pts_y else 12.0

        footprint_w = max_x - min_x
        footprint_d = max_y - min_y

        elements: List[BuildingElement] = []
        storeys: List[StoreyInfo] = []

        total_height = float(floors * floor_height_m)
        all_vertices_x: List[float] = []
        all_vertices_y: List[float] = []
        all_vertices_z: List[float] = []

        # =====================================================================
        # 1. GROUND FOUNDATION SLAB (Elevation: -0.35m to 0.0m)
        # =====================================================================
        slab_margin = 0.35
        ground_slab_verts, ground_slab_faces = cls._create_box_mesh(
            p1=(min_x - slab_margin, min_y - slab_margin),
            p2=(max_x + slab_margin, min_y - slab_margin),
            p3=(max_x + slab_margin, max_y + slab_margin),
            p4=(min_x - slab_margin, max_y + slab_margin),
            z_min=-0.35,
            z_max=0.0,
        )
        cls._accumulate_coords(ground_slab_verts, all_vertices_x, all_vertices_y, all_vertices_z)
        ground_slab_elem = BuildingElement(
            element_id="slab_ground",
            source_global_id=f"IFC_SLAB_{uuid.uuid4().hex[:8]}",
            element_type="IfcSlab",
            name="Ground Foundation Slab",
            storey_id="storey_0",
            storey_name="Floor 1",
            geometry=ElementGeometry(
                format="indexed_mesh",
                vertices=ground_slab_verts,
                faces=ground_slab_faces,
                vertex_count=len(ground_slab_verts) // 3,
                face_count=len(ground_slab_faces) // 3,
            ),
            bounding_box=cls._compute_elem_bbox(ground_slab_verts),
            source_properties={"SlabType": "GroundBearing", "Thickness": 0.35, "Area_m2": round(footprint_w * footprint_d, 2)},
            materials=["Reinforced Concrete C30/37", "Vapor Barrier"],
            confidence_status="imported",
        )
        elements.append(ground_slab_elem)

        # =====================================================================
        # 2. STOREY-BY-STOREY GENERATION
        # =====================================================================
        active_doors = [d for d in floorplan.doors if d.is_active]
        active_windows = [w for w in floorplan.windows if w.is_active]

        for floor_idx in range(floors):
            storey_id = f"storey_{floor_idx}"
            storey_name = f"Floor {floor_idx + 1}"
            z_base = float(floor_idx * floor_height_m)
            z_top = float((floor_idx + 1) * floor_height_m)
            storey_elem_count = 0

            # Intermediate Floor Slab (for upper storeys)
            if floor_idx > 0:
                slab_verts, slab_faces = cls._create_box_mesh(
                    p1=(min_x - 0.1, min_y - 0.1),
                    p2=(max_x + 0.1, min_y - 0.1),
                    p3=(max_x + 0.1, max_y + 0.1),
                    p4=(min_x - 0.1, max_y + 0.1),
                    z_min=z_base - 0.25,
                    z_max=z_base,
                )
                cls._accumulate_coords(slab_verts, all_vertices_x, all_vertices_y, all_vertices_z)
                slab_elem = BuildingElement(
                    element_id=f"slab_floor_{floor_idx}",
                    source_global_id=f"IFC_SLAB_{uuid.uuid4().hex[:8]}",
                    element_type="IfcSlab",
                    name=f"Inter-floor Slab L{floor_idx + 1}",
                    storey_id=storey_id,
                    storey_name=storey_name,
                    geometry=ElementGeometry(
                        format="indexed_mesh",
                        vertices=slab_verts,
                        faces=slab_faces,
                        vertex_count=len(slab_verts) // 3,
                        face_count=len(slab_faces) // 3,
                    ),
                    bounding_box=cls._compute_elem_bbox(slab_verts),
                    source_properties={"Thickness": 0.25, "Elevation": z_base},
                    materials=["Reinforced Concrete C30/37"],
                    confidence_status="imported",
                )
                elements.append(slab_elem)
                storey_elem_count += 1

            # Walls on this storey
            for wall_idx, wall in enumerate(active_walls):
                # Find doors and windows located along this wall
                wall_doors = cls._filter_openings_on_wall(wall, active_doors)
                wall_windows = cls._filter_openings_on_wall(wall, active_windows)

                # Generate wall mesh with openings cut out
                wall_verts, wall_faces = cls._extrude_wall_with_openings(
                    wall=wall,
                    doors=wall_doors,
                    windows=wall_windows,
                    z_base=z_base,
                    z_top=z_top,
                )

                if wall_verts and wall_faces:
                    cls._accumulate_coords(wall_verts, all_vertices_x, all_vertices_y, all_vertices_z)
                    wall_elem = BuildingElement(
                        element_id=f"wall_f{floor_idx}_{wall.id}",
                        source_global_id=f"IFC_WALL_{uuid.uuid4().hex[:8]}",
                        element_type="IfcWall",
                        name=f"{wall.wall_type.title()} Wall {wall.id} (L{floor_idx + 1})",
                        storey_id=storey_id,
                        storey_name=storey_name,
                        geometry=ElementGeometry(
                            format="indexed_mesh",
                            vertices=wall_verts,
                            faces=wall_faces,
                            vertex_count=len(wall_verts) // 3,
                            face_count=len(wall_faces) // 3,
                        ),
                        bounding_box=cls._compute_elem_bbox(wall_verts),
                        source_properties={
                            "WallType": wall.wall_type,
                            "Thickness": wall.thickness_m,
                            "Height": floor_height_m,
                            "Confidence": wall.confidence,
                        },
                        materials=["Aerated Autoclaved Concrete", "Gypsum Plaster"] if wall.wall_type == "interior" else ["Clay Brick Masonry", "Cement Render"],
                        confidence_status="imported",
                    )
                    elements.append(wall_elem)
                    storey_elem_count += 1

                # Generate Door Panels for openings on this floor
                # Ground floor gets entry doors; upper floors get interior doors
                for door in wall_doors:
                    door_verts, door_faces = cls._create_door_mesh(door, wall, z_base)
                    if door_verts and door_faces:
                        cls._accumulate_coords(door_verts, all_vertices_x, all_vertices_y, all_vertices_z)
                        door_elem = BuildingElement(
                            element_id=f"door_f{floor_idx}_{door.id}",
                            source_global_id=f"IFC_DOOR_{uuid.uuid4().hex[:8]}",
                            element_type="IfcDoor",
                            name=f"Door {door.id} (L{floor_idx + 1})",
                            storey_id=storey_id,
                            storey_name=storey_name,
                            geometry=ElementGeometry(
                                format="indexed_mesh",
                                vertices=door_verts,
                                faces=door_faces,
                                vertex_count=len(door_verts) // 3,
                                face_count=len(door_faces) // 3,
                            ),
                            bounding_box=cls._compute_elem_bbox(door_verts),
                            source_properties={"Width": door.width_m, "Height": door.height_m},
                            materials=["Timber", "Solid Core Wood"],
                            confidence_status="imported",
                        )
                        elements.append(door_elem)
                        storey_elem_count += 1

                # Generate Window Glazing Panels for openings on this floor
                for win in wall_windows:
                    win_verts, win_faces = cls._create_window_mesh(win, wall, z_base)
                    if win_verts and win_faces:
                        cls._accumulate_coords(win_verts, all_vertices_x, all_vertices_y, all_vertices_z)
                        win_elem = BuildingElement(
                            element_id=f"win_f{floor_idx}_{win.id}",
                            source_global_id=f"IFC_WIN_{uuid.uuid4().hex[:8]}",
                            element_type="IfcWindow",
                            name=f"Window {win.id} (L{floor_idx + 1})",
                            storey_id=storey_id,
                            storey_name=storey_name,
                            geometry=ElementGeometry(
                                format="indexed_mesh",
                                vertices=win_verts,
                                faces=win_faces,
                                vertex_count=len(win_verts) // 3,
                                face_count=len(win_faces) // 3,
                            ),
                            bounding_box=cls._compute_elem_bbox(win_verts),
                            source_properties={"Width": win.width_m, "Height": win.height_m, "SillHeight": win.sill_height_m},
                            materials=["Double Glazed Low-E Glass", "Anodized Aluminum"],
                            confidence_status="imported",
                        )
                        elements.append(win_elem)
                        storey_elem_count += 1

            # Generate IfcSpace Room Volumes for this floor
            for room in floorplan.rooms:
                room_verts, room_faces, room_w, room_d = cls._create_room_space_mesh(
                    room=room, z_base=z_base, height_m=floor_height_m
                )
                if room_verts and room_faces:
                    conn_doors = cls._find_doors_for_room(room, active_doors)
                    conn_wins = cls._find_windows_for_room(room, active_windows)

                    space_elem = BuildingElement(
                        element_id=f"space_f{floor_idx}_{room.id}",
                        source_global_id=f"IFC_SPACE_{uuid.uuid4().hex[:8]}",
                        element_type="IfcSpace",
                        name=f"{room.name} (L{floor_idx + 1})",
                        storey_id=storey_id,
                        storey_name=storey_name,
                        geometry=ElementGeometry(
                            format="indexed_mesh",
                            vertices=room_verts,
                            faces=room_faces,
                            vertex_count=len(room_verts) // 3,
                            face_count=len(room_faces) // 3,
                        ),
                        bounding_box=cls._compute_elem_bbox(room_verts),
                        source_properties={
                            "Pset_SpaceCommon": {
                                "RoomType": room.room_type,
                                "NetFloorArea": room.area_sqm,
                                "FloorNumber": floor_idx + 1,
                                "Height_m": floor_height_m,
                                "Dimensions": f"{room_w:.1f}m × {room_d:.1f}m",
                                "ConnectedDoors": [d.id for d in conn_doors],
                                "AssociatedWindows": [w.id for w in conn_wins],
                            },
                            "RoomType": room.room_type,
                            "Area_m2": room.area_sqm,
                            "FloorNumber": floor_idx + 1,
                            "Height_m": floor_height_m,
                            "Dimensions": f"{room_w:.1f}m × {room_d:.1f}m",
                            "ConnectedDoors": [d.id for d in conn_doors],
                            "AssociatedWindows": [w.id for w in conn_wins],
                        },
                        materials=["Commercial Broadloom Carpet", "Drywall Partition", "Mineral Fiber Acoustic Ceiling"],
                        confidence_status="imported",
                        relationships={
                            "connected_doors": [d.id for d in conn_doors],
                            "associated_windows": [w.id for w in conn_wins],
                        },
                    )
                    elements.append(space_elem)
                    storey_elem_count += 1

            storeys.append(
                StoreyInfo(
                    storey_id=storey_id,
                    name=storey_name,
                    elevation_m=round(z_base, 2),
                    element_count=storey_elem_count,
                )
            )

        # =====================================================================
        # 3. ROOF GENERATION
        # =====================================================================
        roof_z = total_height
        roof_verts, roof_faces = cls._create_roof_mesh(
            min_x=min_x,
            max_x=max_x,
            min_y=min_y,
            max_y=max_y,
            roof_z=roof_z,
            roof_type=roof_type,
        )
        cls._accumulate_coords(roof_verts, all_vertices_x, all_vertices_y, all_vertices_z)

        roof_elem = BuildingElement(
            element_id="roof_main",
            source_global_id=f"IFC_ROOF_{uuid.uuid4().hex[:8]}",
            element_type="IfcRoof",
            name=f"{roof_type.title()} Roof Assembly",
            storey_id=f"storey_{floors - 1}",
            storey_name=f"Floor {floors}",
            geometry=ElementGeometry(
                format="indexed_mesh",
                vertices=roof_verts,
                faces=roof_faces,
                vertex_count=len(roof_verts) // 3,
                face_count=len(roof_faces) // 3,
            ),
            bounding_box=cls._compute_elem_bbox(roof_verts),
            source_properties={"RoofType": roof_type, "Slope": "Flat" if roof_type in ["flat", "parapet"] else "Pitched 22deg"},
            materials=["Structural Steel Deck", "Rigid PIR Thermal Insulation", "EPDM Waterproof Membrane"],
            confidence_status="imported",
        )
        elements.append(roof_elem)
        if storeys:
            storeys[-1].element_count += 1

        # =====================================================================
        # 4. OVERALL BOUNDING BOX & PACKAGING
        # =====================================================================
        overall_min_x = min(all_vertices_x) if all_vertices_x else min_x
        overall_max_x = max(all_vertices_x) if all_vertices_x else max_x
        overall_min_y = min(all_vertices_y) if all_vertices_y else min_y
        overall_max_y = max(all_vertices_y) if all_vertices_y else max_y
        overall_min_z = min(all_vertices_z) if all_vertices_z else -0.35
        overall_max_z = max(all_vertices_z) if all_vertices_z else total_height + 0.35

        overall_bbox = BoundingBox3D(
            min_x=round(float(overall_min_x), 3),
            min_y=round(float(overall_min_y), 3),
            min_z=round(float(overall_min_z), 3),
            max_x=round(float(overall_max_x), 3),
            max_y=round(float(overall_max_y), 3),
            max_z=round(float(overall_max_z), 3),
            center_x=round(float((overall_min_x + overall_max_x) / 2.0), 3),
            center_y=round(float((overall_min_y + overall_max_y) / 2.0), 3),
            center_z=round(float((overall_min_z + overall_max_z) / 2.0), 3),
            width=round(float(overall_max_x - overall_min_x), 3),
            height=round(float(overall_max_y - overall_min_y), 3),
            depth=round(float(overall_max_z - overall_min_z), 3),
        )

        # Element counts by type
        counts_by_type: Dict[str, int] = {}
        for e in elements:
            counts_by_type[e.element_type] = counts_by_type.get(e.element_type, 0) + 1

        model_detail = BuildingModelDetail(
            model_id=model_id,
            source_type="floorplan",
            source_filename=f"2d_drawing_{floorplan.drawing_id}.png",
            import_timestamp=now_str,
            schema_version="IFC4 (FloorPlan-Extruded)",
            units={"length": "METRE", "area": "SQUARE_METRE", "volume": "CUBIC_METRE"},
            project_name="InfraTwinAI Architectural Reconstruction",
            site_name="Urban Digital Twin Prototype",
            building_name=building_name or f"{building_type} Building",
            storeys=storeys,
            element_counts_by_type=counts_by_type,
            total_element_count=len(elements),
            available_properties=["SlabType", "WallType", "Thickness", "Height", "Materials", "Elevation"],
            missing_data=["Structural reinforcement bar details", "MEP conduit paths"],
            bounding_box=overall_bbox,
            provenance_metadata={
                "source": "2D Architectural Drawing Ingestion",
                "drawing_id": floorplan.drawing_id,
                "floors": floors,
                "floor_height_m": floor_height_m,
                "roof_type": roof_type,
                "building_type": building_type,
                "detection_confidence": floorplan.overall_confidence,
                "timestamp": now_str,
            },
            elements=elements,
        )

        # Store in ModelStore
        ModelStore.save_model(model_detail, warnings=floorplan.warnings)

        summary = ImportSummaryResponse(
            model_id=model_detail.model_id,
            source_filename=model_detail.source_filename,
            schema_version=model_detail.schema_version,
            import_status="success",
            element_counts_by_type=counts_by_type,
            total_elements=len(elements),
            available_properties=model_detail.available_properties,
            units=model_detail.units,
            coordinate_metadata={
                "bounds_width_m": overall_bbox.width,
                "bounds_depth_m": overall_bbox.height,
                "building_height_m": overall_bbox.depth,
                "floors": floors,
                "roof_type": roof_type,
            },
            parsing_warnings=floorplan.warnings,
            missing_information_summary=["MEP infrastructure not modeled in 2D floorplan"],
        )

        return model_detail, summary

    # -------------------------------------------------------------------------
    # Geometric Mesh Generators (Watertight Indexed Triangle Meshes)
    # -------------------------------------------------------------------------

    @classmethod
    def _create_box_mesh(
        cls,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        p3: Tuple[float, float],
        p4: Tuple[float, float],
        z_min: float,
        z_max: float,
    ) -> Tuple[List[float], List[int]]:
        """
        Creates an 8-vertex, 12-triangle watertight cuboid mesh.
        p1, p2, p3, p4 are the 4 base vertices in counter-clockwise order.
        """
        verts = [
            p1[0], p1[1], z_min,  # 0
            p2[0], p2[1], z_min,  # 1
            p3[0], p3[1], z_min,  # 2
            p4[0], p4[1], z_min,  # 3
            p1[0], p1[1], z_max,  # 4
            p2[0], p2[1], z_max,  # 5
            p3[0], p3[1], z_max,  # 6
            p4[0], p4[1], z_max,  # 7
        ]
        faces = [
            0, 2, 1,  0, 3, 2,  # bottom (z_min, normal down)
            4, 5, 6,  4, 6, 7,  # top (z_max, normal up)
            0, 1, 5,  0, 5, 4,  # south side
            1, 2, 6,  1, 6, 5,  # east side
            2, 3, 7,  2, 7, 6,  # north side
            3, 0, 4,  3, 4, 7,  # west side
        ]
        return verts, faces

    @classmethod
    def _extrude_wall_segment_box(
        cls,
        start_pt: Tuple[float, float],
        end_pt: Tuple[float, float],
        normal: Tuple[float, float],
        thickness: float,
        z_min: float,
        z_max: float,
    ) -> Tuple[List[float], List[int]]:
        """
        Extrudes a wall sub-segment box along the wall axis with given thickness and z bounds.
        """
        half_t = thickness / 2.0
        nx, ny = normal[0] * half_t, normal[1] * half_t

        c0 = (start_pt[0] - nx, start_pt[1] - ny)
        c1 = (end_pt[0] - nx, end_pt[1] - ny)
        c2 = (end_pt[0] + nx, end_pt[1] + ny)
        c3 = (start_pt[0] + nx, start_pt[1] + ny)

        return cls._create_box_mesh(c0, c1, c2, c3, z_min, z_max)

    @classmethod
    def _extrude_wall_with_openings(
        cls,
        wall: Wall2D,
        doors: List[Door2D],
        windows: List[Window2D],
        z_base: float,
        z_top: float,
    ) -> Tuple[List[float], List[int]]:
        """
        Extrudes a wall with aperture cutouts for doors and windows.
        Partitions wall into solid segments, sills, and lintels.
        """
        x1, y1 = wall.start.x, wall.start.y
        x2, y2 = wall.end.x, wall.end.y
        dx = x2 - x1
        dy = y2 - y1
        wall_len = math.hypot(dx, dy)
        if wall_len < 0.1:
            return [], []

        ux, uy = dx / wall_len, dy / wall_len
        # Normal perpendicular to wall axis
        nx, ny = -uy, ux

        # Collect opening intervals along wall parameter s in [0, wall_len]
        intervals: List[Dict[str, Any]] = []

        for d in doors:
            # Project door position onto wall axis
            s_center = (d.position.x - x1) * ux + (d.position.y - y1) * uy
            s_start = max(0.05, s_center - (d.width_m / 2.0))
            s_end = min(wall_len - 0.05, s_center + (d.width_m / 2.0))
            if s_end > s_start:
                intervals.append({
                    "type": "door",
                    "s_start": s_start,
                    "s_end": s_end,
                    "h_top": min(d.height_m, z_top - z_base - 0.2),
                })

        for w in windows:
            s_center = (w.position.x - x1) * ux + (w.position.y - y1) * uy
            s_start = max(0.05, s_center - (w.width_m / 2.0))
            s_end = min(wall_len - 0.05, s_center + (w.width_m / 2.0))
            if s_end > s_start:
                intervals.append({
                    "type": "window",
                    "s_start": s_start,
                    "s_end": s_end,
                    "sill_h": w.sill_height_m,
                    "win_h": w.height_m,
                })

        # Sort opening intervals along wall
        intervals = sorted(intervals, key=lambda it: it["s_start"])

        # Merge overlapping intervals if any
        merged_intervals: List[Dict[str, Any]] = []
        for it in intervals:
            if not merged_intervals:
                merged_intervals.append(it)
            else:
                last = merged_intervals[-1]
                if it["s_start"] < last["s_end"]:
                    # Overlapping openings: expand previous
                    last["s_end"] = max(last["s_end"], it["s_end"])
                else:
                    merged_intervals.append(it)

        all_verts: List[float] = []
        all_faces: List[int] = []

        def pt_at_s(s: float) -> Tuple[float, float]:
            return (x1 + s * ux, y1 + s * uy)

        def append_mesh(v: List[float], f: List[int]):
            base_idx = len(all_verts) // 3
            all_verts.extend(v)
            all_faces.extend([idx + base_idx for idx in f])

        current_s = 0.0

        for it in merged_intervals:
            # 1. Solid wall segment before opening
            if it["s_start"] > current_s + 0.05:
                v, f = cls._extrude_wall_segment_box(
                    start_pt=pt_at_s(current_s),
                    end_pt=pt_at_s(it["s_start"]),
                    normal=(nx, ny),
                    thickness=wall.thickness_m,
                    z_min=z_base,
                    z_max=z_top,
                )
                append_mesh(v, f)

            # 2. Opening geometry
            if it["type"] == "door":
                # Lintel segment above door
                door_top_z = z_base + it["h_top"]
                if door_top_z < z_top:
                    v, f = cls._extrude_wall_segment_box(
                        start_pt=pt_at_s(it["s_start"]),
                        end_pt=pt_at_s(it["s_end"]),
                        normal=(nx, ny),
                        thickness=wall.thickness_m,
                        z_min=door_top_z,
                        z_max=z_top,
                    )
                    append_mesh(v, f)

            elif it["type"] == "window":
                # Sill segment below window
                sill_z = z_base + it.get("sill_h", 0.9)
                win_top_z = sill_z + it.get("win_h", 1.4)
                if sill_z > z_base:
                    v, f = cls._extrude_wall_segment_box(
                        start_pt=pt_at_s(it["s_start"]),
                        end_pt=pt_at_s(it["s_end"]),
                        normal=(nx, ny),
                        thickness=wall.thickness_m,
                        z_min=z_base,
                        z_max=sill_z,
                    )
                    append_mesh(v, f)

                # Lintel segment above window
                if win_top_z < z_top:
                    v, f = cls._extrude_wall_segment_box(
                        start_pt=pt_at_s(it["s_start"]),
                        end_pt=pt_at_s(it["s_end"]),
                        normal=(nx, ny),
                        thickness=wall.thickness_m,
                        z_min=win_top_z,
                        z_max=z_top,
                    )
                    append_mesh(v, f)

            current_s = it["s_end"]

        # 3. Final solid segment from last opening to wall end
        if current_s < wall_len - 0.05:
            v, f = cls._extrude_wall_segment_box(
                start_pt=pt_at_s(current_s),
                end_pt=pt_at_s(wall_len),
                normal=(nx, ny),
                thickness=wall.thickness_m,
                z_min=z_base,
                z_max=z_top,
            )
            append_mesh(v, f)

        return all_verts, all_faces

    @classmethod
    def _create_door_mesh(cls, door: Door2D, wall: Wall2D, z_base: float) -> Tuple[List[float], List[int]]:
        """Creates a 3D door panel mesh inside the opening aperture."""
        dx = wall.end.x - wall.start.x
        dy = wall.end.y - wall.start.y
        wall_len = math.hypot(dx, dy)
        if wall_len < 0.1:
            return [], []
        ux, uy = dx / wall_len, dy / wall_len
        nx, ny = -uy, ux

        half_w = door.width_m / 2.0
        p_start = (door.position.x - ux * half_w, door.position.y - uy * half_w)
        p_end = (door.position.x + ux * half_w, door.position.y + uy * half_w)

        return cls._extrude_wall_segment_box(
            start_pt=p_start,
            end_pt=p_end,
            normal=(nx, ny),
            thickness=0.06,  # 6cm door panel thickness
            z_min=z_base,
            z_max=z_base + door.height_m,
        )

    @classmethod
    def _create_window_mesh(cls, win: Window2D, wall: Wall2D, z_base: float) -> Tuple[List[float], List[int]]:
        """Creates a 3D window glazing mesh inside the aperture."""
        dx = wall.end.x - wall.start.x
        dy = wall.end.y - wall.start.y
        wall_len = math.hypot(dx, dy)
        if wall_len < 0.1:
            return [], []
        ux, uy = dx / wall_len, dy / wall_len
        nx, ny = -uy, ux

        half_w = win.width_m / 2.0
        p_start = (win.position.x - ux * half_w, win.position.y - uy * half_w)
        p_end = (win.position.x + ux * half_w, win.position.y + uy * half_w)

        z_sill = z_base + win.sill_height_m
        z_win_top = z_sill + win.height_m

        return cls._extrude_wall_segment_box(
            start_pt=p_start,
            end_pt=p_end,
            normal=(nx, ny),
            thickness=0.05,  # 5cm glass + frame thickness
            z_min=z_sill,
            z_max=z_win_top,
        )

    @classmethod
    def _create_roof_mesh(
        cls,
        min_x: float,
        max_x: float,
        min_y: float,
        max_y: float,
        roof_z: float,
        roof_type: str,
    ) -> Tuple[List[float], List[int]]:
        """
        Generates 3D roof geometry: flat slab, parapet perimeter, or pitched gable prism.
        """
        margin = 0.30
        r_min_x = min_x - margin
        r_max_x = max_x + margin
        r_min_y = min_y - margin
        r_max_y = max_y + margin

        if roof_type == "gable":
            # Pitched gable roof with central ridge along X or Y
            ridge_h = 2.2
            mid_y = (r_min_y + r_max_y) / 2.0

            # 6 vertices of a triangular prism
            verts = [
                r_min_x, r_min_y, roof_z,            # 0: south-west eave
                r_max_x, r_min_y, roof_z,            # 1: south-east eave
                r_max_x, r_max_y, roof_z,            # 2: north-east eave
                r_min_x, r_max_y, roof_z,            # 3: north-west eave
                r_min_x, mid_y, roof_z + ridge_h,   # 4: west gable ridge
                r_max_x, mid_y, roof_z + ridge_h,   # 5: east gable ridge
            ]
            faces = [
                0, 2, 1,  0, 3, 2,  # bottom flat ceiling
                0, 1, 5,  0, 5, 4,  # south pitched roof slope
                2, 3, 4,  2, 4, 5,  # north pitched roof slope
                0, 4, 3,            # west triangular gable end
                1, 2, 5,            # east triangular gable end
            ]
            return verts, faces

        elif roof_type == "parapet":
            # Flat base slab + 4 perimeter parapet walls
            all_v: List[float] = []
            all_f: List[int] = []

            # 1. Base roof slab
            v_slab, f_slab = cls._create_box_mesh(
                p1=(r_min_x, r_min_y),
                p2=(r_max_x, r_min_y),
                p3=(r_max_x, r_max_y),
                p4=(r_min_x, r_max_y),
                z_min=roof_z - 0.25,
                z_max=roof_z,
            )
            all_v.extend(v_slab)
            all_f.extend(f_slab)

            # 2. Parapet wall around perimeter (height: 0.8m, thickness: 0.22m)
            parapet_h = 0.8
            p_thick = 0.22
            parapet_segments = [
                ((r_min_x, r_min_y), (r_max_x, r_min_y), (0.0, 1.0)),
                ((r_max_x, r_min_y), (r_max_x, r_max_y), (-1.0, 0.0)),
                ((r_max_x, r_max_y), (r_min_x, r_max_y), (0.0, -1.0)),
                ((r_min_x, r_max_y), (r_min_x, r_min_y), (1.0, 0.0)),
            ]
            for p_start, p_end, p_norm in parapet_segments:
                v_p, f_p = cls._extrude_wall_segment_box(
                    p_start, p_end, p_norm, p_thick, roof_z, roof_z + parapet_h
                )
                b_idx = len(all_v) // 3
                all_v.extend(v_p)
                all_f.extend([idx + b_idx for idx in f_p])

            return all_v, all_f

        else:
            # Default: Flat roof slab with overhang
            return cls._create_box_mesh(
                p1=(r_min_x, r_min_y),
                p2=(r_max_x, r_min_y),
                p3=(r_max_x, r_max_y),
                p4=(r_min_x, r_max_y),
                z_min=roof_z,
                z_max=roof_z + 0.35,
            )

    @classmethod
    def _filter_openings_on_wall(cls, wall: Wall2D, openings: List[Any]) -> List[Any]:
        """Finds openings whose positions lie close to this wall segment."""
        matched = []
        x1, y1 = wall.start.x, wall.start.y
        x2, y2 = wall.end.x, wall.end.y
        dx = x2 - x1
        dy = y2 - y1
        wall_len = math.hypot(dx, dy)
        if wall_len < 0.1:
            return []
        ux, uy = dx / wall_len, dy / wall_len

        for op in openings:
            if getattr(op, "wall_id", None) == wall.id:
                matched.append(op)
                continue
            # Distance from point to line segment
            px = op.position.x
            py = op.position.y
            s = (px - x1) * ux + (py - y1) * uy
            if -0.2 <= s <= wall_len + 0.2:
                # Perpendicular distance
                dist = abs((px - x1) * (-uy) + (py - y1) * ux)
                if dist <= 0.75:
                    matched.append(op)
        return matched

    @classmethod
    def _compute_elem_bbox(cls, vertices: List[float]) -> BoundingBox3D:
        """Computes bounding box for an individual element mesh."""
        if not vertices:
            return BoundingBox3D(
                min_x=0, min_y=0, min_z=0, max_x=1, max_y=1, max_z=1,
                center_x=0.5, center_y=0.5, center_z=0.5, width=1, height=1, depth=1
            )
        xs = vertices[0::3]
        ys = vertices[1::3]
        zs = vertices[2::3]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        min_z, max_z = min(zs), max(zs)
        return BoundingBox3D(
            min_x=round(float(min_x), 3),
            min_y=round(float(min_y), 3),
            min_z=round(float(min_z), 3),
            max_x=round(float(max_x), 3),
            max_y=round(float(max_y), 3),
            max_z=round(float(max_z), 3),
            center_x=round(float((min_x + max_x) / 2.0), 3),
            center_y=round(float((min_y + max_y) / 2.0), 3),
            center_z=round(float((min_z + max_z) / 2.0), 3),
            width=round(float(max_x - min_x), 3),
            height=round(float(max_y - min_y), 3),
            depth=round(float(max_z - min_z), 3),
        )

    @classmethod
    def _accumulate_coords(
        cls, verts: List[float], all_x: List[float], all_y: List[float], all_z: List[float]
    ):
        """Helper to accumulate vertex coordinates for overall model bounding box."""
        if verts:
            all_x.extend(verts[0::3])
            all_y.extend(verts[1::3])
            all_z.extend(verts[2::3])

    @classmethod
    def _create_room_space_mesh(
        cls, room: Any, z_base: float, height_m: float
    ) -> Tuple[List[float], List[int], float, float]:
        """Creates an interior volumetric IfcSpace mesh for a room."""
        if not room.polygon:
            return [], [], 0.0, 0.0
        xs = [p.x for p in room.polygon]
        ys = [p.y for p in room.polygon]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        w = max(0.2, max_x - min_x)
        d = max(0.2, max_y - min_y)

        # Inset slightly inside wall inner face
        margin = 0.12
        p1 = (min_x + margin, min_y + margin)
        p2 = (max_x - margin, min_y + margin)
        p3 = (max_x - margin, max_y - margin)
        p4 = (min_x + margin, max_y - margin)
        z_min = z_base + 0.05
        z_max = z_base + height_m - 0.05

        verts, faces = cls._create_box_mesh(p1, p2, p3, p4, z_min, z_max)
        return verts, faces, round(w, 2), round(d, 2)

    @classmethod
    def _find_doors_for_room(cls, room: Any, doors: List[Door2D]) -> List[Door2D]:
        """Finds doors on or near the boundary of this room."""
        if not room.polygon:
            return []
        xs = [p.x for p in room.polygon]
        ys = [p.y for p in room.polygon]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        connected: List[Door2D] = []
        for d in doors:
            px, py = d.position.x, d.position.y
            if (min_x - 0.75) <= px <= (max_x + 0.75) and (min_y - 0.75) <= py <= (max_y + 0.75):
                connected.append(d)
        return connected

    @classmethod
    def _find_windows_for_room(cls, room: Any, windows: List[Window2D]) -> List[Window2D]:
        """Finds windows on or near the boundary of this room."""
        if not room.polygon:
            return []
        xs = [p.x for p in room.polygon]
        ys = [p.y for p in room.polygon]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        connected: List[Window2D] = []
        for w in windows:
            px, py = w.position.x, w.position.y
            if (min_x - 0.75) <= px <= (max_x + 0.75) and (min_y - 0.75) <= py <= (max_y + 0.75):
                connected.append(w)
        return connected
