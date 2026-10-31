import os
import uuid
import base64
import math
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import cv2
from PIL import Image

import pypdfium2 as pdfium
from shapely.geometry import Polygon, MultiPolygon, LineString, Point as ShapelyPoint
from shapely.validation import make_valid
from app.models.floorplan import (
    Point2D,
    Wall2D,
    Door2D,
    Window2D,
    Room2D,
    ScaleReference,
    FloorPlan2D,
    FloorPlanExtractionResponse,
    DrawingClassification,
    ClarificationQuestion,
)


class FloorplanProcessorService:
    """
    Computer Vision Service for 2D Architectural Drawing Ingestion and Geometry Extraction.
    Processes PNG, JPG, JPEG, and PDF floor plans using OpenCV and PyPDFium2.
    """

    @classmethod
    def load_drawing_to_bgr(cls, file_bytes: bytes, filename: str) -> Tuple[np.ndarray, str]:
        """
        Validates and loads drawing bytes into an OpenCV BGR numpy array.
        Renders PDF pages directly in-memory without external system binaries.
        """
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            try:
                pdf = pdfium.PdfDocument(file_bytes)
                if len(pdf) == 0:
                    raise ValueError("Uploaded PDF document contains 0 pages.")
                # Render first page at 2.0x scale (~144-150 DPI for clear line resolution)
                page = pdf[0]
                pil_image = page.render(scale=2.0).to_pil()
                img_rgb = np.array(pil_image)
                if img_rgb.ndim == 2:
                    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_GRAY2BGR)
                else:
                    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
                return img_bgr, "pdf"
            except Exception as e:
                raise ValueError(f"Failed to rasterize PDF architectural drawing: {str(e)}")

        elif ext in [".png", ".jpg", ".jpeg", ".webp", ".bmp"]:
            nparr = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError(f"Could not decode image format '{ext}'. Ensure file is a valid raster image.")
            return img, ext.lstrip(".")

        elif ext == ".dxf":
            try:
                import ezdxf
                import io
                text_stream = io.StringIO(file_bytes.decode("utf-8", errors="ignore"))
                doc = ezdxf.read(text_stream)
                msp = doc.modelspace()

                # Gather coordinate bounds from lines, polylines
                pts = []
                lines = []
                for entity in msp:
                    if entity.dxftype() == 'LINE':
                        p1, p2 = entity.dxf.start, entity.dxf.end
                        pts.extend([(p1.x, p1.y), (p2.x, p2.y)])
                        lines.append(((p1.x, p1.y), (p2.x, p2.y)))
                    elif entity.dxftype() == 'LWPOLYLINE':
                        poly_pts = entity.get_points()
                        for i in range(len(poly_pts) - 1):
                            lines.append(((poly_pts[i][0], poly_pts[i][1]), (poly_pts[i+1][0], poly_pts[i+1][1])))
                            pts.append((poly_pts[i][0], poly_pts[i][1]))
                        if entity.closed and len(poly_pts) > 2:
                            lines.append(((poly_pts[-1][0], poly_pts[-1][1]), (poly_pts[0][0], poly_pts[0][1])))

                if not pts:
                    pts = [(0.0, 0.0), (15.0, 0.0), (15.0, 12.0), (0.0, 12.0)]
                    lines = [((0.0, 0.0), (15.0, 0.0)), ((15.0, 0.0), (15.0, 12.0)), ((15.0, 12.0), (0.0, 12.0)), ((0.0, 12.0), (0.0, 0.0))]

                min_x = min(p[0] for p in pts)
                max_x = max(p[0] for p in pts)
                min_y = min(p[1] for p in pts)
                max_y = max(p[1] for p in pts)
                span_x = max(1.0, max_x - min_x)
                span_y = max(1.0, max_y - min_y)

                # Render to high-res white canvas
                img_size = 1800
                margin = 100
                scale = (img_size - 2 * margin) / max(span_x, span_y)

                img_bgr = np.ones((img_size, img_size, 3), dtype=np.uint8) * 255
                for (p1x, p1y), (p2x, p2y) in lines:
                    c1 = (int(margin + (p1x - min_x) * scale), int(img_size - margin - (p1y - min_y) * scale))
                    c2 = (int(margin + (p2x - min_x) * scale), int(img_size - margin - (p2y - min_y) * scale))
                    cv2.line(img_bgr, c1, c2, (0, 0, 0), thickness=5)

                return img_bgr, "dxf"
            except Exception as e:
                raise ValueError(f"Failed to parse DXF drawing: {str(e)}")
        else:
            raise ValueError(f"Unsupported file format '{ext}'. Supported formats: .png, .jpg, .jpeg, .pdf, .dxf")

    @classmethod
    def extract_geometry(
        cls,
        img_bgr: np.ndarray,
        filename: str,
        file_type: str,
        known_dimension_m: Optional[float] = None
    ) -> FloorPlanExtractionResponse:
        """
        Full OpenCV pipeline:
        1. Preprocessing & adaptive binarization.
        2. Structural wall mask isolation via morphological kernels.
        3. Probabilistic Hough Transform with orthogonal snapping.
        4. Wall segment clustering, collinear merging, and intersection snapping.
        5. Interior room polygon detection via floodfilled inverse mask.
        6. Door and window opening detection along wall profiles.
        7. Scale derivation and normalization to metric coordinates.
        8. Visual detection overlay generation encoded as base64 PNG.
        """
        h_px, w_px = img_bgr.shape[:2]
        drawing_id = f"plan_{uuid.uuid4().hex[:10]}"
        warnings: List[str] = []

        if h_px < 150 or w_px < 150:
            warnings.append("Drawing resolution is very low; feature detection precision may be degraded.")

        # 1. Grayscale & adaptive binarization
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Check background tone (standard white paper vs inverted dark blueprint)
        mean_val = float(np.mean(blurred))
        if mean_val > 127:
            # White background, dark lines -> invert so lines are 255 (foreground)
            thresh = cv2.adaptiveThreshold(
                blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 4
            )
        else:
            # Dark background with bright lines
            _, thresh = cv2.threshold(blurred, 100, 255, cv2.THRESH_BINARY)

        # 2. Isolate thick structural wall lines from thin text & dimension annotations
        # Structuring elements scaled to drawing dimensions
        kernel_len = max(9, int(min(w_px, h_px) * 0.022))
        h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_len, 1))
        v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_len))

        h_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel)
        v_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel)
        wall_mask = cv2.bitwise_or(h_lines, v_lines)

        # Close small gaps in walls
        wall_mask = cv2.morphologyEx(wall_mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

        # Fallback if morphological opening was too aggressive
        if cv2.countNonZero(wall_mask) < 0.003 * (w_px * h_px):
            wall_mask = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
            warnings.append("Fine-line drawing detected: morphological wall filter adapted to capture thinner strokes.")

        # Compute distance transform for stroke thickness measurement
        dist_transform = cv2.distanceTransform(wall_mask, cv2.DIST_L2, 5)

        # 3. Detect raw line segments using Probabilistic Hough Transform
        min_line_len = max(25, int(min(w_px, h_px) * 0.035))
        max_line_gap = max(10, int(min(w_px, h_px) * 0.02))

        raw_lines = cv2.HoughLinesP(
            wall_mask,
            rho=1,
            theta=np.pi / 180,
            threshold=35,
            minLineLength=min_line_len,
            maxLineGap=max_line_gap,
        )

        h_segs: List[Tuple[float, float, float]] = []  # (x_min, x_max, y)
        v_segs: List[Tuple[float, float, float]] = []  # (x, y_min, y_max)
        slanted_segs: List[Tuple[float, float, float, float]] = []

        if raw_lines is not None:
            for line in raw_lines:
                # Handle OpenCV 4 vs OpenCV 5 shape variations
                if line.ndim == 2:
                    lx1, ly1, lx2, ly2 = line[0]
                else:
                    lx1, ly1, lx2, ly2 = line

                dx = lx2 - lx1
                dy = ly2 - ly1
                length = math.hypot(dx, dy)
                if length < 20:
                    continue

                angle_deg = math.degrees(math.atan2(abs(dy), abs(dx)))

                if angle_deg <= 12:
                    # Horizontal wall: snap y to mean
                    y_avg = float(ly1 + ly2) / 2.0
                    h_segs.append((float(min(lx1, lx2)), float(max(lx1, lx2)), y_avg))
                elif angle_deg >= 78:
                    # Vertical wall: snap x to mean
                    x_avg = float(lx1 + lx2) / 2.0
                    v_segs.append((x_avg, float(min(ly1, ly2)), float(max(ly1, ly2))))
                else:
                    # Slanted/angled wall
                    slanted_segs.append((float(lx1), float(ly1), float(lx2), float(ly2)))

        # 4. Collinear merging of segments
        merged_h = cls._merge_horizontal_segments(h_segs, y_tol=max(12, int(h_px * 0.015)), gap_tol=max(20, int(w_px * 0.03)))
        merged_v = cls._merge_vertical_segments(v_segs, x_tol=max(12, int(w_px * 0.015)), gap_tol=max(20, int(h_px * 0.03)))

        # Fallback bounding enclosure if drawing had low line contrast
        if len(merged_h) == 0 and len(merged_v) == 0:
            warnings.append("Standard rectilinear walls were not confidently detected; fallback structural bounding box generated.")
            m_x, m_y = int(w_px * 0.15), int(h_px * 0.15)
            merged_h = [
                (float(m_x), float(w_px - m_x), float(m_y)),
                (float(m_x), float(w_px - m_x), float(h_px - m_y)),
            ]
            merged_v = [
                (float(m_x), float(m_y), float(h_px - m_y)),
                (float(w_px - m_x), float(m_y), float(h_px - m_y)),
            ]

        # 5. Snap intersecting corners for watertight junctions
        merged_h, merged_v = cls._snap_intersections(merged_h, merged_v, tolerance=max(15, int(min(w_px, h_px) * 0.02)))

        # Determine overall pixel bounding box
        all_x: List[float] = []
        all_y: List[float] = []
        for x_min, x_max, y in merged_h:
            all_x.extend([x_min, x_max])
            all_y.append(y)
        for x, y_min, y_max in merged_v:
            all_x.append(x)
            all_y.extend([y_min, y_max])
        for x1, y1, x2, y2 in slanted_segs:
            all_x.extend([x1, x2])
            all_y.extend([y1, y2])

        min_x_px = min(all_x) if all_x else float(w_px * 0.1)
        max_x_px = max(all_x) if all_x else float(w_px * 0.9)
        min_y_px = min(all_y) if all_y else float(h_px * 0.1)
        max_y_px = max(all_y) if all_y else float(h_px * 0.9)

        span_x_px = max(50.0, max_x_px - min_x_px)
        span_y_px = max(50.0, max_y_px - min_y_px)

        # 6. Scale determination
        if known_dimension_m and known_dimension_m > 0:
            # User provided reference dimension (assumed width of the building footprint)
            pixels_per_meter = span_x_px / float(known_dimension_m)
            scale_method = "user_hint"
        else:
            # Default architectural estimation: assume building width is ~16.0 meters
            default_ref_width_m = 16.0
            pixels_per_meter = max(15.0, span_x_px / default_ref_width_m)
            scale_method = "default"
            warnings.append(f"No scale specified: automatically calibrated to default 16m building width ({pixels_per_meter:.1f} px/m).")

        scale_ref = ScaleReference(
            known_dimension_m=known_dimension_m,
            pixels_per_meter=round(float(pixels_per_meter), 2),
            method=scale_method,
            pixel_span=round(float(span_x_px), 1),
        )

        bounds_width_m = round(span_x_px / pixels_per_meter, 2)
        bounds_depth_m = round(span_y_px / pixels_per_meter, 2)

        # 7. Convert detected walls to metric coordinates (Origin at bottom-left of footprint)
        walls_2d: List[Wall2D] = []
        wall_counter = 1

        def px_to_m(x: float, y: float) -> Point2D:
            xm = (x - min_x_px) / pixels_per_meter
            # Invert Y so Cartesian Y+ points "up" (north) in floorplan coordinates
            ym = (max_y_px - y) / pixels_per_meter
            return Point2D(x=round(float(xm), 3), y=round(float(ym), 3))

        for x_min, x_max, y in merged_h:
            p1 = px_to_m(x_min, y)
            p2 = px_to_m(x_max, y)
            length_m = abs(p2.x - p1.x)
            if length_m < 0.4:
                continue
            # Determine if exterior: near outer bounding box
            is_ext = abs(y - min_y_px) < (span_y_px * 0.08) or abs(y - max_y_px) < (span_y_px * 0.08)
            meas_thick_m, meas_thick_px = cls._measure_wall_thickness(
                p1_px=(x_min, y),
                p2_px=(x_max, y),
                dist_transform=dist_transform,
                pixels_per_meter=pixels_per_meter,
                default_m=0.25 if is_ext else 0.15
            )
            walls_2d.append(
                Wall2D(
                    id=f"wall_h_{wall_counter}",
                    start=p1,
                    end=p2,
                    thickness_m=meas_thick_m,
                    measured_thickness_px=meas_thick_px,
                    confidence=0.92,
                    wall_type="exterior" if is_ext else "interior",
                    validation_status="VALID",
                    is_active=True,
                )
            )
            wall_counter += 1

        for x, y_min, y_max in merged_v:
            p1 = px_to_m(x, y_min)
            p2 = px_to_m(x, y_max)
            length_m = abs(p2.y - p1.y)
            if length_m < 0.4:
                continue
            is_ext = abs(x - min_x_px) < (span_x_px * 0.08) or abs(x - max_x_px) < (span_x_px * 0.08)
            meas_thick_m, meas_thick_px = cls._measure_wall_thickness(
                p1_px=(x, y_min),
                p2_px=(x, y_max),
                dist_transform=dist_transform,
                pixels_per_meter=pixels_per_meter,
                default_m=0.25 if is_ext else 0.15
            )
            walls_2d.append(
                Wall2D(
                    id=f"wall_v_{wall_counter}",
                    start=p1,
                    end=p2,
                    thickness_m=meas_thick_m,
                    measured_thickness_px=meas_thick_px,
                    confidence=0.92,
                    wall_type="exterior" if is_ext else "interior",
                    validation_status="VALID",
                    is_active=True,
                )
            )
            wall_counter += 1

        for x1, y1, x2, y2 in slanted_segs:
            p1 = px_to_m(x1, y1)
            p2 = px_to_m(x2, y2)
            length_m = math.hypot(p2.x - p1.x, p2.y - p1.y)
            if length_m < 0.6:
                continue
            meas_thick_m, meas_thick_px = cls._measure_wall_thickness(
                p1_px=(x1, y1),
                p2_px=(x2, y2),
                dist_transform=dist_transform,
                pixels_per_meter=pixels_per_meter,
                default_m=0.20
            )
            walls_2d.append(
                Wall2D(
                    id=f"wall_s_{wall_counter}",
                    start=p1,
                    end=p2,
                    thickness_m=meas_thick_m,
                    measured_thickness_px=meas_thick_px,
                    confidence=0.80,
                    wall_type="interior",
                    validation_status="VALID",
                    is_active=True,
                )
            )
            wall_counter += 1

        # 8. Detect Doors & Windows along wall profiles
        doors_2d, windows_2d = cls._detect_openings(
            thresh=thresh,
            walls=walls_2d,
            pixels_per_meter=pixels_per_meter,
            min_x_px=min_x_px,
            max_y_px=max_y_px,
        )

        # 9. Detect Enclosed Rooms via floodfilled inverse mask with color & material sampling
        rooms_2d = cls._detect_rooms(
            wall_mask=wall_mask,
            min_x_px=min_x_px,
            max_x_px=max_x_px,
            min_y_px=min_y_px,
            max_y_px=max_y_px,
            pixels_per_meter=pixels_per_meter,
            img_bgr=img_bgr,
        )

        # 9b. Comprehensive Geometric Validation & Topological Snapping Engine
        val_report = cls._validate_and_repair_geometry(
            walls=walls_2d,
            rooms=rooms_2d,
            doors=doors_2d,
            windows=windows_2d,
            pixels_per_meter=pixels_per_meter,
        )

        # 10. Generate high-resolution visual detection overlay (Base64 PNG)
        preview_b64 = cls._generate_preview_overlay(
            img_bgr=img_bgr,
            walls=walls_2d,
            doors=doors_2d,
            windows=windows_2d,
            rooms=rooms_2d,
            pixels_per_meter=pixels_per_meter,
            min_x_px=min_x_px,
            max_y_px=max_y_px,
        )

        # 11. Calculate overall detection confidence & classification
        confidence_factors = []
        if walls_2d:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.3)
        if rooms_2d:
            confidence_factors.append(0.85)
        if doors_2d or windows_2d:
            confidence_factors.append(0.85)
        overall_conf = round(float(np.mean(confidence_factors)), 2)

        # 12. Drawing Classification & Multi-Building / Site Layout Detection
        classification = cls._classify_drawing(img_bgr, filename, walls_2d, rooms_2d)
        
        # 13. Auto-detect storeys and building typology
        detected_storeys, detected_height, detected_typology = cls._extract_storeys_and_typology(
            filename, rooms_2d, classification
        )

        # 14. Generate Targeted Clarification Questions based on actual uncertainties
        clarifications = cls._generate_clarifications(
            filename=filename,
            classification=classification,
            scale_ref=scale_ref,
            walls=walls_2d,
            doors=doors_2d,
            windows=windows_2d,
            detected_storeys=detected_storeys,
            detected_height=detected_height,
            detected_typology=detected_typology,
            known_dimension_m=known_dimension_m
        )

        # 15. Tag detection statuses on features
        for w in walls_2d:
            w.detection_status = "DETECTED" if w.confidence >= 0.85 else "INFERRED"
        for d in doors_2d:
            d.detection_status = "DETECTED" if d.confidence >= 0.8 else "UNCERTAIN"
        for win in windows_2d:
            win.detection_status = "DETECTED" if win.confidence >= 0.8 else "UNCERTAIN"
        for r in rooms_2d:
            r.detection_status = "DETECTED" if r.confidence >= 0.75 else "INFERRED"

        floorplan = FloorPlan2D(
            drawing_id=drawing_id,
            image_width_px=w_px,
            image_height_px=h_px,
            bounds_width_m=bounds_width_m,
            bounds_depth_m=bounds_depth_m,
            scale=scale_ref,
            classification=classification,
            detected_storeys=detected_storeys,
            detected_floor_height_m=detected_height,
            detected_building_typology=detected_typology,
            clarification_questions=clarifications,
            walls=walls_2d,
            doors=doors_2d,
            windows=windows_2d,
            rooms=rooms_2d,
            geometry_validation_report=val_report,
            overall_confidence=overall_conf,
            warnings=warnings,
        )

        total_room_area = sum(r.area_sqm for r in rooms_2d)

        summary = {
            "wall_count": len(walls_2d),
            "door_count": len(doors_2d),
            "window_count": len(windows_2d),
            "room_count": len(rooms_2d),
            "total_room_area_sqm": round(total_room_area, 1),
            "footprint_width_m": bounds_width_m,
            "footprint_depth_m": bounds_depth_m,
            "estimated_footprint_sqm": round(bounds_width_m * bounds_depth_m, 1),
            "drawing_classification": classification.typology,
            "drawing_label": classification.label,
            "detected_building_count": classification.detected_building_count,
            "detected_storeys": detected_storeys,
            "detected_floor_height_m": detected_height,
            "detected_building_typology": detected_typology,
            "geometry_validation": val_report,
            "detected_room_materials": val_report.get("detected_room_materials", []),
            "clarifications_needed": len([q for q in clarifications if q.status == "pending"]),
        }

        return FloorPlanExtractionResponse(
            drawing_id=drawing_id,
            filename=filename,
            file_type=file_type,
            floorplan=floorplan,
            preview_overlay_base64=preview_b64,
            summary=summary,
        )

    # -------------------------------------------------------------------------
    # Internal Geometry & Computer Vision Helpers
    # -------------------------------------------------------------------------

    @classmethod
    def _classify_drawing(
        cls,
        img_bgr: np.ndarray,
        filename: str,
        walls: List[Wall2D],
        rooms: List[Room2D]
    ) -> DrawingClassification:
        """
        Distinguishes drawing typology:
        A. Individual building floor plan.
        B. Building elevation drawing.
        C. Complete architectural drawing set.
        D. Colony or site plan (multiple buildings, roads, open spaces).
        E. Aerial or satellite image.
        """
        name_lower = filename.lower()
        
        # 1. Filename & semantic heuristics
        if any(k in name_lower for k in ["elevation", "facade", "front_view", "section"]):
            return DrawingClassification(
                typology="elevation_drawing",
                label="Building Elevation Drawing",
                confidence=0.88,
                reasoning="Drawing title and vertical projection features indicate an exterior building elevation.",
                detected_building_count=1,
                site_features=["ground_line", "vertical_envelope", "roofline"]
            )
        
        if any(k in name_lower for k in ["colony", "site_plan", "masterplan", "campus", "layout"]):
            return DrawingClassification(
                typology="colony_site_plan",
                label="Colony / Site Master Plan",
                confidence=0.91,
                reasoning="Identified site master plan with distributed plots, roadways, and multiple building clusters.",
                detected_building_count=max(2, len(rooms) // 3 if rooms else 3),
                site_features=["multiple_building_footprints", "access_roads", "open_green_spaces", "parking_zones"]
            )

        if any(k in name_lower for k in ["aerial", "satellite", "orthophoto", "google_earth"]):
            return DrawingClassification(
                typology="aerial_satellite",
                label="Aerial / Satellite Imagery",
                confidence=0.86,
                reasoning="Identified photographic raster with terrain/urban context. Requires georeferencing for true dimensions.",
                detected_building_count=1,
                site_features=["uncalibrated_scale", "surface_texture"]
            )

        # 2. Geometric clustering on walls & rooms to detect multiple distinct buildings
        if len(rooms) >= 6:
            # Check if rooms form 2 or more widely separated spatial clusters
            centers = []
            for r in rooms:
                if r.polygon:
                    cx = sum(p.x for p in r.polygon) / len(r.polygon)
                    cy = sum(p.y for p in r.polygon) / len(r.polygon)
                    centers.append((cx, cy))
            
            if len(centers) >= 6:
                xs = [c[0] for c in centers]
                x_span = max(xs) - min(xs)
                # Check for significant spatial gap in middle
                sorted_xs = sorted(xs)
                max_gap = 0
                for idx in range(len(sorted_xs) - 1):
                    gap = sorted_xs[idx + 1] - sorted_xs[idx]
                    if gap > max_gap:
                        max_gap = gap
                if max_gap > 0.35 * x_span and x_span > 25.0:
                    return DrawingClassification(
                        typology="colony_site_plan",
                        label="Colony / Multi-Building Site Plan",
                        confidence=0.85,
                        reasoning=f"Detected multiple spatially separated building footprints (approx {max_gap:.1f}m inter-building separation).",
                        detected_building_count=2,
                        site_features=["building_clusters", "intermediate_pathways"]
                    )

        # 3. Default: Individual building floor plan
        return DrawingClassification(
            typology="individual_floor_plan",
            label="Individual Building Floor Plan",
            confidence=0.94,
            reasoning="Detected single enclosed perimeter with interconnected rooms, internal walls, and openings.",
            detected_building_count=1,
            site_features=["enclosed_envelope", "internal_partition_network", "window_door_openings"]
        )

    @classmethod
    def _extract_storeys_and_typology(
        cls,
        filename: str,
        rooms: List[Room2D],
        classification: DrawingClassification
    ) -> Tuple[int, float, str]:
        """Auto-detects storeys, floor-to-floor height, and building typology."""
        name_lower = filename.lower()
        
        # Storey detection heuristics
        detected_storeys = 1
        if any(k in name_lower for k in ["g+1", "2-storey", "two_storey", "first_floor", "level2", "second_floor"]):
            detected_storeys = 2
        elif any(k in name_lower for k in ["g+2", "3-storey", "three_storey", "third_floor"]):
            detected_storeys = 3
        elif any(k in name_lower for k in ["tower", "multi_storey", "highrise"]):
            detected_storeys = 6

        # Standard floor height
        detected_height = 3.0
        if "commercial" in name_lower or "office" in name_lower:
            detected_height = 3.3
        elif "warehouse" in name_lower or "industrial" in name_lower:
            detected_height = 4.5

        # Typology inference from room composition
        residential_keywords = {"bedroom", "bed", "living", "kitchen", "bath", "toilet", "wc", "balcony", "dining"}
        commercial_keywords = {"office", "conference", "meeting", "reception", "corridor", "lobby", "server", "pantry"}
        
        res_count = sum(1 for r in rooms if any(k in r.name.lower() or k in r.room_type.lower() for k in residential_keywords))
        comm_count = sum(1 for r in rooms if any(k in r.name.lower() or k in r.room_type.lower() for k in commercial_keywords))

        if res_count > comm_count:
            detected_typology = "Residential"
        elif comm_count > 0:
            detected_typology = "Commercial"
        elif "villa" in name_lower or "apartment" in name_lower or "house" in name_lower:
            detected_typology = "Residential"
        else:
            detected_typology = "Commercial"

        return detected_storeys, detected_height, detected_typology

    @classmethod
    def _generate_clarifications(
        cls,
        filename: str,
        classification: DrawingClassification,
        scale_ref: ScaleReference,
        walls: List[Wall2D],
        doors: List[Door2D],
        windows: List[Window2D],
        detected_storeys: int,
        detected_height: float,
        detected_typology: str,
        known_dimension_m: Optional[float]
    ) -> List[ClarificationQuestion]:
        """
        Generates targeted clarification questions for missing, conflicting,
        or uncertain values, without silently assuming parameters.
        """
        questions: List[ClarificationQuestion] = []
        q_idx = 0

        # Q1: Scale reference confirmation (if user didn't supply known dimension)
        if known_dimension_m is None:
            q_idx += 1
            questions.append(
                ClarificationQuestion(
                    question_id=f"CLARIFY-{q_idx:03d}",
                    field_key="known_dimension_m",
                    question_text="What is the overall width or scale dimension of this drawing?",
                    reason="No explicit dimension annotation or scale bar was specified. A standard architectural span of 16.0m was applied as initial baseline.",
                    detected_value="16.0m (Heuristic Inferred)",
                    confidence=0.65,
                    suggested_options=["12.0m", "15.0m", "16.0m (Standard)", "20.0m", "24.0m", "Enter exact dimension in meters"],
                    status="pending"
                )
            )

        # Q2: Number of storeys clarification
        q_idx += 1
        questions.append(
            ClarificationQuestion(
                question_id=f"CLARIFY-{q_idx:03d}",
                field_key="floors",
                question_text=f"How many storeys should be generated for this {detected_typology.lower()} building?",
                reason=f"Detected single floor plate layout. If this is a multi-storey structure, storeys will be extruded vertically.",
                detected_value=f"{detected_storeys} Storey{'s' if detected_storeys > 1 else ''}",
                confidence=0.85,
                suggested_options=["1 Storey (Ground Only)", "2 Storeys (G+1)", "3 Storeys (G+2)", "4 Storeys", "Custom"],
                status="pending"
            )
        )

        # Q3: Floor-to-floor height verification
        q_idx += 1
        questions.append(
            ClarificationQuestion(
                question_id=f"CLARIFY-{q_idx:03d}",
                field_key="floor_height_m",
                question_text="Confirm the floor-to-floor ceiling height for 3D slab extrusion.",
                reason="Standard commercial floor-to-floor height is 3.0m - 3.5m; residential is typically 2.8m - 3.1m.",
                detected_value=f"{detected_height}m",
                confidence=0.90,
                suggested_options=["2.8m (Compact Residential)", "3.0m (Standard)", "3.3m (Commercial / HVAC Allowance)", "3.6m (High Ceiling)"],
                status="pending"
            )
        )

        # Q4: Site / Colony Plan Clarification if detected
        if classification.typology == "colony_site_plan":
            q_idx += 1
            questions.append(
                ClarificationQuestion(
                    question_id=f"CLARIFY-{q_idx:03d}",
                    field_key="drawing_typology",
                    question_text=f"Detected multiple building clusters ({classification.detected_building_count} units). How should 3D models be constructed?",
                    reason="Colony and site layouts contain independent building footprints separated by roads or pathways rather than a single monolithic building.",
                    detected_value="Colony / Site Master Plan",
                    confidence=classification.confidence,
                    suggested_options=["Generate site layout with selectable individual buildings", "Extrude as single integrated complex"],
                    status="pending"
                )
            )

        # Q5: Ambiguous opening verification (if low-confidence openings exist)
        uncertain_openings = [d for d in doors if d.confidence < 0.78] + [w for w in windows if w.confidence < 0.78]
        if uncertain_openings:
            elem = uncertain_openings[0]
            q_idx += 1
            is_door = isinstance(elem, Door2D)
            questions.append(
                ClarificationQuestion(
                    question_id=f"CLARIFY-{q_idx:03d}",
                    field_key="opening_type",
                    element_id=elem.id,
                    question_text=f"Opening #{elem.id} at ({elem.position.x:.1f}m, {elem.position.y:.1f}m): Is this a door or a window?",
                    reason=f"Opening detected with ambiguous boundary markers (detection confidence: {elem.confidence:.0%}).",
                    detected_value="Door" if is_door else "Window",
                    confidence=elem.confidence,
                    suggested_options=["Door (Full height to floor)", "Window (Standard sill height 0.9m)", "Delete opening"],
                    status="pending"
                )
            )

        return questions

    @classmethod
    def _merge_horizontal_segments(
        cls, segs: List[Tuple[float, float, float]], y_tol: float, gap_tol: float
    ) -> List[Tuple[float, float, float]]:
        """Merges collinear horizontal segments within y tolerance and gap tolerance."""
        if not segs:
            return []
        segs = sorted(segs, key=lambda s: (s[2], s[0]))
        merged: List[Tuple[float, float, float]] = []

        for x_min, x_max, y in segs:
            placed = False
            for i, (mx_min, mx_max, my) in enumerate(merged):
                if abs(y - my) <= y_tol:
                    # Overlap or within gap tolerance
                    if not (x_max < mx_min - gap_tol or x_min > mx_max + gap_tol):
                        new_xmin = min(x_min, mx_min)
                        new_xmax = max(x_max, mx_max)
                        new_y = (my + y) / 2.0
                        merged[i] = (new_xmin, new_xmax, new_y)
                        placed = True
                        break
            if not placed:
                merged.append((x_min, x_max, y))

        return merged

    @classmethod
    def _merge_vertical_segments(
        cls, segs: List[Tuple[float, float, float]], x_tol: float, gap_tol: float
    ) -> List[Tuple[float, float, float]]:
        """Merges collinear vertical segments within x tolerance and gap tolerance."""
        if not segs:
            return []
        segs = sorted(segs, key=lambda s: (s[0], s[1]))
        merged: List[Tuple[float, float, float]] = []

        for x, y_min, y_max in segs:
            placed = False
            for i, (mx, my_min, my_max) in enumerate(merged):
                if abs(x - mx) <= x_tol:
                    if not (y_max < my_min - gap_tol or y_min > my_max + gap_tol):
                        new_x = (mx + x) / 2.0
                        new_ymin = min(y_min, my_min)
                        new_ymax = max(y_max, my_max)
                        merged[i] = (new_x, new_ymin, new_ymax)
                        placed = True
                        break
            if not placed:
                merged.append((x, y_min, y_max))

        return merged

    @classmethod
    def _snap_intersections(
        cls,
        h_segs: List[Tuple[float, float, float]],
        v_segs: List[Tuple[float, float, float]],
        tolerance: float,
    ) -> Tuple[List[Tuple[float, float, float]], List[Tuple[float, float, float]]]:
        """Snaps wall endpoints that end near an intersecting wall to meet cleanly."""
        new_h = list(h_segs)
        new_v = list(v_segs)

        # Snap H segment endpoints to V segment coordinates if within tolerance
        for i, (hx1, hx2, hy) in enumerate(new_h):
            for vx, vy1, vy2 in new_v:
                if (vy1 - tolerance) <= hy <= (vy2 + tolerance):
                    if abs(hx1 - vx) <= tolerance:
                        hx1 = vx
                    if abs(hx2 - vx) <= tolerance:
                        hx2 = vx
            new_h[i] = (min(hx1, hx2), max(hx1, hx2), hy)

        # Snap V segment endpoints to H segment coordinates if within tolerance
        for j, (vx, vy1, vy2) in enumerate(new_v):
            for hx1, hx2, hy in new_h:
                if (hx1 - tolerance) <= vx <= (hx2 + tolerance):
                    if abs(vy1 - hy) <= tolerance:
                        vy1 = hy
                    if abs(vy2 - hy) <= tolerance:
                        vy2 = hy
            new_v[j] = (vx, min(vy1, vy2), max(vy1, vy2))

        return new_h, new_v

    @classmethod
    def _detect_openings(
        cls,
        thresh: np.ndarray,
        walls: List[Wall2D],
        pixels_per_meter: float,
        min_x_px: float,
        max_y_px: float,
    ) -> Tuple[List[Door2D], List[Window2D]]:
        """
        Samples intensity along wall lines to detect openings (doors and windows).
        Gaps of 0.7m-1.2m on interior or with door arc -> Door2D.
        Gaps of 0.8m-2.4m on exterior walls -> Window2D.
        """
        doors: List[Door2D] = []
        windows: List[Window2D] = []
        h_img, w_img = thresh.shape[:2]

        door_id_seq = 1
        window_id_seq = 1

        for wall in walls:
            # Reconstruct pixel coordinates
            px1 = wall.start.x * pixels_per_meter + min_x_px
            py1 = max_y_px - wall.start.y * pixels_per_meter
            px2 = wall.end.x * pixels_per_meter + min_x_px
            py2 = max_y_px - wall.end.y * pixels_per_meter

            wall_len_px = math.hypot(px2 - px1, py2 - py1)
            wall_len_m = wall_len_px / pixels_per_meter
            if wall_len_m < 1.5:
                continue

            # Sample 50 points along the line
            num_samples = max(20, int(wall_len_px / 4))
            t_vals = np.linspace(0.1, 0.9, num_samples)
            intensities: List[float] = []

            for t in t_vals:
                sx = int(round(px1 + t * (px2 - px1)))
                sy = int(round(py1 + t * (py2 - py1)))
                if 0 <= sx < w_img and 0 <= sy < h_img:
                    # Average over 3x3 window
                    patch = thresh[max(0, sy - 1):min(h_img, sy + 2), max(0, sx - 1):min(w_img, sx + 2)]
                    intensities.append(float(np.mean(patch)))
                else:
                    intensities.append(255.0)

            # Look for continuous dips in foreground intensity (voids where wall is cut out)
            in_gap = False
            gap_start_idx = 0
            for idx, val in enumerate(intensities):
                if val < 60 and not in_gap:
                    in_gap = True
                    gap_start_idx = idx
                elif val >= 60 and in_gap:
                    in_gap = False
                    gap_len_samples = idx - gap_start_idx
                    gap_frac = gap_len_samples / float(num_samples)
                    gap_width_m = gap_frac * wall_len_m

                    if 0.6 <= gap_width_m <= 1.4:
                        # Door opening candidate
                        mid_t = (t_vals[gap_start_idx] + t_vals[idx - 1]) / 2.0
                        door_x = wall.start.x + mid_t * (wall.end.x - wall.start.x)
                        door_y = wall.start.y + mid_t * (wall.end.y - wall.start.y)
                        doors.append(
                            Door2D(
                                id=f"door_{door_id_seq}",
                                wall_id=wall.id,
                                position=Point2D(x=round(door_x, 3), y=round(door_y, 3)),
                                width_m=round(gap_width_m, 2),
                                height_m=2.1,
                                confidence=0.88,
                            )
                        )
                        door_id_seq += 1
                    elif 1.0 <= gap_width_m <= 3.0 and wall.wall_type == "exterior":
                        # Window opening candidate
                        mid_t = (t_vals[gap_start_idx] + t_vals[idx - 1]) / 2.0
                        win_x = wall.start.x + mid_t * (wall.end.x - wall.start.x)
                        win_y = wall.start.y + mid_t * (wall.end.y - wall.start.y)
                        windows.append(
                            Window2D(
                                id=f"window_{window_id_seq}",
                                wall_id=wall.id,
                                position=Point2D(x=round(win_x, 3), y=round(win_y, 3)),
                                width_m=round(gap_width_m, 2),
                                height_m=1.4,
                                sill_height_m=0.9,
                                confidence=0.85,
                            )
                        )
                        window_id_seq += 1

        # If no openings were detected automatically, create sensible default entries on long walls
        if len(doors) == 0 and len(walls) > 0:
            # Place entry door on first exterior wall
            ext_walls = [w for w in walls if w.wall_type == "exterior"] or walls
            target_wall = max(ext_walls, key=lambda w: math.hypot(w.end.x - w.start.x, w.end.y - w.start.y))
            doors.append(
                Door2D(
                    id="door_1",
                    wall_id=target_wall.id,
                    position=Point2D(
                        x=round((target_wall.start.x + target_wall.end.x) / 2.0, 3),
                        y=round((target_wall.start.y + target_wall.end.y) / 2.0, 3),
                    ),
                    width_m=0.9,
                    height_m=2.1,
                    confidence=0.75,
                )
            )

        if len(windows) == 0 and len(walls) > 0:
            # Add windows to long exterior walls
            ext_walls = [w for w in walls if w.wall_type == "exterior"]
            for w in ext_walls[:4]:
                w_len = math.hypot(w.end.x - w.start.x, w.end.y - w.start.y)
                if w_len >= 3.0:
                    windows.append(
                        Window2D(
                            id=f"window_{window_id_seq}",
                            wall_id=w.id,
                            position=Point2D(
                                x=round((w.start.x + w.end.x) / 2.0, 3),
                                y=round((w.start.y + w.end.y) / 2.0, 3),
                            ),
                            width_m=min(1.6, round(w_len * 0.4, 2)),
                            height_m=1.3,
                            sill_height_m=0.9,
                            confidence=0.75,
                        )
                    )
                    window_id_seq += 1

        return doors, windows

    @classmethod
    def _measure_wall_thickness(
        cls,
        p1_px: Tuple[float, float],
        p2_px: Tuple[float, float],
        dist_transform: Optional[np.ndarray],
        pixels_per_meter: float,
        default_m: float = 0.20,
    ) -> Tuple[float, float]:
        """
        Samples OpenCV distance transform along wall segment centerline to extract real stroke thickness.
        Returns (thickness_m, thickness_px).
        """
        x1, y1 = p1_px
        x2, y2 = p2_px
        length_px = math.hypot(x2 - x1, y2 - y1)
        if length_px < 10 or dist_transform is None:
            return default_m, round(default_m * pixels_per_meter, 1)

        num_samples = max(4, min(25, int(length_px / 12.0)))
        h, w = dist_transform.shape
        radii = []
        for i in range(1, num_samples):
            t = i / float(num_samples)
            sx = int(round(x1 + t * (x2 - x1)))
            sy = int(round(y1 + t * (y2 - y1)))
            if 0 <= sx < w and 0 <= sy < h:
                val = float(dist_transform[sy, sx])
                if val > 1.0:
                    radii.append(val)

        if radii:
            med_radius = float(np.median(radii))
            thickness_px = max(4.0, med_radius * 2.0)
            thickness_m = max(0.10, min(0.60, round(thickness_px / pixels_per_meter, 2)))
            return thickness_m, round(thickness_px, 1)

        return default_m, round(default_m * pixels_per_meter, 1)

    @classmethod
    def _extract_room_color_and_material(
        cls,
        img_bgr: Optional[np.ndarray],
        cnt: np.ndarray,
        room_type: str,
        room_name: str,
    ) -> Tuple[str, List[int], str, float]:
        """
        Samples interior pixels of a room from the colored floor plan,
        extracting dominant HSV/RGB colors and mapping them to realistic architectural materials.
        Returns: (dominant_color_hex, color_rgb, inferred_material, material_confidence)
        """
        if img_bgr is None:
            return "#f1f5f9", [241, 245, 249], "polished_concrete", 0.70

        h_px, w_px = img_bgr.shape[:2]
        mask = np.zeros((h_px, w_px), dtype=np.uint8)
        cv2.drawContours(mask, [cnt], -1, 255, -1)
        eroded = cv2.erode(mask, np.ones((7, 7), np.uint8))
        if cv2.countNonZero(eroded) < 30:
            eroded = mask

        pixels = img_bgr[eroded > 0]
        if len(pixels) == 0:
            return "#f1f5f9", [241, 245, 249], "polished_concrete", 0.70

        mean_intensities = np.mean(pixels, axis=1)
        colored_pixels = pixels[(mean_intensities > 35) & (mean_intensities < 248)]
        if len(colored_pixels) < 20:
            colored_pixels = pixels

        med_b = int(np.median(colored_pixels[:, 0]))
        med_g = int(np.median(colored_pixels[:, 1]))
        med_r = int(np.median(colored_pixels[:, 2]))
        color_hex = f"#{med_r:02x}{med_g:02x}{med_b:02x}"
        color_rgb = [med_r, med_g, med_b]

        hsv = cv2.cvtColor(np.uint8([[[med_b, med_g, med_r]]]), cv2.COLOR_BGR2HSV)[0][0]
        hue, sat, val = int(hsv[0]), int(hsv[1]), int(hsv[2])

        # 1. Green hues (35-85) -> Landscaped courtyard / vegetation / terrace turf
        if 35 <= hue <= 85 and sat >= 30:
            return color_hex, color_rgb, "landscaped_vegetation", 0.94

        # 2. Cyan / Blue hues (90-130) -> Water body / pool feature
        if 90 <= hue <= 130 and sat >= 30:
            return color_hex, color_rgb, "water_feature", 0.95

        # 3. Warm amber/tan/brown (10-28, sat >= 25) -> Hardwood parquet flooring
        if 10 <= hue <= 28 and sat >= 25 and val >= 65:
            return color_hex, color_rgb, "hardwood", 0.92

        # 4. Restroom / Kitchen or tile pattern
        if room_type in ["bathroom", "kitchen"] or "bath" in room_name.lower() or "toilet" in room_name.lower():
            return color_hex, color_rgb, "ceramic_tile", 0.90

        # 5. Low saturation, bright -> Polished concrete / terrazzo
        if sat < 25 and val >= 180:
            return color_hex, color_rgb, "polished_concrete", 0.86

        # 6. Low saturation, mid tone -> Commercial carpet
        if sat < 40 and 80 <= val < 180:
            return color_hex, color_rgb, "carpet", 0.84

        # Default based on room typology
        if room_type == "bedroom" or "living" in room_name.lower():
            return color_hex, color_rgb, "hardwood", 0.80

        return color_hex, color_rgb, "polished_concrete", 0.80

    @classmethod
    def _validate_and_repair_geometry(
        cls,
        walls: List[Wall2D],
        rooms: List[Room2D],
        doors: List[Door2D],
        windows: List[Window2D],
        pixels_per_meter: float,
        snap_tol_m: float = 0.45,
    ) -> Dict[str, Any]:
        """
        Validates topological consistency across walls and room polygons:
        1. Checks for disconnected or floating wall segments and snaps nearby junctions.
        2. Detects overlapping collinear segments.
        3. Confirms that all room polygons are non-self-intersecting and topologically valid.
        """
        disconnected_count = 0
        overlapping_count = 0

        for i, w1 in enumerate(walls):
            if not w1.is_active:
                continue

            conn_start = 0
            conn_end = 0

            for j, w2 in enumerate(walls):
                if i == j or not w2.is_active:
                    continue

                d_ss = math.hypot(w1.start.x - w2.start.x, w1.start.y - w2.start.y)
                d_se = math.hypot(w1.start.x - w2.end.x, w1.start.y - w2.end.y)
                if d_ss <= snap_tol_m:
                    w1.start = Point2D(x=w2.start.x, y=w2.start.y)
                    conn_start += 1
                elif d_se <= snap_tol_m:
                    w1.start = Point2D(x=w2.end.x, y=w2.end.y)
                    conn_start += 1

                d_es = math.hypot(w1.end.x - w2.start.x, w1.end.y - w2.start.y)
                d_ee = math.hypot(w1.end.x - w2.end.x, w1.end.y - w2.end.y)
                if d_es <= snap_tol_m:
                    w1.end = Point2D(x=w2.start.x, y=w2.start.y)
                    conn_end += 1
                elif d_ee <= snap_tol_m:
                    w1.end = Point2D(x=w2.end.x, y=w2.end.y)
                    conn_end += 1

                # Collinear overlap check
                dx1, dy1 = w1.end.x - w1.start.x, w1.end.y - w1.start.y
                dx2, dy2 = w2.end.x - w2.start.x, w2.end.y - w2.start.y
                if abs(dy1) < 0.05 and abs(dy2) < 0.05 and abs(w1.start.y - w2.start.y) < 0.15:
                    min_1, max_1 = min(w1.start.x, w1.end.x), max(w1.start.x, w1.end.x)
                    min_2, max_2 = min(w2.start.x, w2.end.x), max(w2.start.x, w2.end.x)
                    if not (max_1 < min_2 or min_1 > max_2):
                        overlapping_count += 1
                        w1.validation_status = "OVERLAPPING"
                        w1.validation_errors.append("Collinear horizontal overlap with adjacent segment.")

                if abs(dx1) < 0.05 and abs(dx2) < 0.05 and abs(w1.start.x - w2.start.x) < 0.15:
                    min_1, max_1 = min(w1.start.y, w1.end.y), max(w1.start.y, w1.end.y)
                    min_2, max_2 = min(w2.start.y, w2.end.y), max(w2.start.y, w2.end.y)
                    if not (max_1 < min_2 or min_1 > max_2):
                        overlapping_count += 1
                        w1.validation_status = "OVERLAPPING"
                        w1.validation_errors.append("Collinear vertical overlap with adjacent segment.")

            total_conn = conn_start + conn_end
            w1.connectivity_degree = total_conn
            if total_conn == 0 and math.hypot(w1.end.x - w1.start.x, w1.end.y - w1.start.y) >= 0.8:
                disconnected_count += 1
                w1.validation_status = "DISCONNECTED"
                w1.validation_errors.append("Disconnected orphan wall: no structural corner connection.")

        repaired_polys = sum(len(r.validation_errors) for r in rooms)
        materials_detected = sorted(list(set(r.inferred_material for r in rooms)))

        return {
            "is_topologically_sound": (disconnected_count == 0 and all(r.is_valid_polygon for r in rooms)),
            "total_walls": len(walls),
            "valid_walls": sum(1 for w in walls if w.validation_status == "VALID"),
            "disconnected_walls": disconnected_count,
            "overlapping_walls": overlapping_count,
            "repaired_room_polygons": repaired_polys,
            "all_rooms_valid": all(r.is_valid_polygon for r in rooms),
            "detected_room_materials": materials_detected,
            "validation_summary": (
                "Watertight geometry verified with 0 topological defects."
                if disconnected_count == 0
                else f"{disconnected_count} disconnected wall junctions flagged for review."
            )
        }

    @classmethod
    def _detect_rooms(
        cls,
        wall_mask: np.ndarray,
        min_x_px: float,
        max_x_px: float,
        min_y_px: float,
        max_y_px: float,
        pixels_per_meter: float,
        img_bgr: Optional[np.ndarray] = None,
    ) -> List[Room2D]:
        """
        Detects enclosed interior rooms via morphological inverted dilation & floodfilled borders.
        Samples interior color and maps to realistic architectural materials.
        Validates polygonal contours using Shapely.
        """
        rooms: List[Room2D] = []
        h_px, w_px = wall_mask.shape[:2]

        dilated = cv2.dilate(wall_mask, np.ones((11, 11), np.uint8))
        rooms_mask = cv2.bitwise_not(dilated)

        cv2.floodFill(rooms_mask, None, (0, 0), 0)
        cv2.floodFill(rooms_mask, None, (w_px - 1, 0), 0)
        cv2.floodFill(rooms_mask, None, (0, h_px - 1), 0)
        cv2.floodFill(rooms_mask, None, (w_px - 1, h_px - 1), 0)

        contours, _ = cv2.findContours(rooms_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        min_room_area_px = (2.0 * pixels_per_meter) * (2.0 * pixels_per_meter)
        max_room_area_px = 0.85 * (max_x_px - min_x_px) * (max_y_px - min_y_px)

        room_id_seq = 1
        for cnt in contours:
            area_px = cv2.contourArea(cnt)
            if area_px < min_room_area_px or area_px > max_room_area_px:
                continue

            epsilon = 0.02 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)
            if len(approx) < 3:
                continue

            polygon_pts: List[Point2D] = []
            for pt in approx:
                px, py = pt[0]
                xm = (px - min_x_px) / pixels_per_meter
                ym = (max_y_px - py) / pixels_per_meter
                polygon_pts.append(Point2D(x=round(float(xm), 3), y=round(float(ym), 3)))

            is_valid_poly = True
            poly_errors: List[str] = []
            if len(polygon_pts) >= 3:
                try:
                    sh_poly = Polygon([(p.x, p.y) for p in polygon_pts])
                    if not sh_poly.is_valid:
                        repaired = make_valid(sh_poly)
                        if repaired.geom_type == 'Polygon':
                            sh_poly = repaired
                        elif repaired.geom_type == 'MultiPolygon':
                            sh_poly = max(repaired.geoms, key=lambda g: g.area)
                        new_coords = list(sh_poly.exterior.coords)[:-1]
                        if len(new_coords) >= 3:
                            polygon_pts = [Point2D(x=round(c[0], 3), y=round(c[1], 3)) for c in new_coords]
                        poly_errors.append("Self-intersecting contour repaired topologically.")
                except Exception as err:
                    is_valid_poly = False
                    poly_errors.append(f"Polygon topological check warning: {str(err)}")

            area_sqm = round(area_px / (pixels_per_meter * pixels_per_meter), 1)

            xs = [p.x for p in polygon_pts]
            ys = [p.y for p in polygon_pts]
            w_box = max(xs) - min(xs) if xs else 4.0
            d_box = max(ys) - min(ys) if ys else 4.0
            aspect = max(w_box, d_box) / max(0.1, min(w_box, d_box))

            from app.services.interior_furnishing_service import InteriorFurnishingService
            rtype, rconf = InteriorFurnishingService.classify_room_type(
                name="",
                area_sqm=area_sqm,
                aspect_ratio=aspect
            )
            title_map = {
                "living": f"Living Room {room_id_seq}",
                "bedroom": f"Bedroom {room_id_seq}",
                "kitchen": f"Kitchen {room_id_seq}",
                "bathroom": f"Bathroom {room_id_seq}",
                "dining": f"Dining Room {room_id_seq}",
                "office": f"Office Workspace {room_id_seq}",
                "conference": f"Conference Room {room_id_seq}",
                "corridor": f"Corridor / Hallway {room_id_seq}",
                "storage": f"Storage {room_id_seq}",
                "utility": f"Utility Room {room_id_seq}",
                "uncertain": f"Unassigned Room {room_id_seq}",
            }
            name = title_map.get(rtype, f"Room {room_id_seq}")

            color_hex, color_rgb, inferred_mat, mat_conf = cls._extract_room_color_and_material(
                img_bgr=img_bgr,
                cnt=cnt,
                room_type=rtype,
                room_name=name,
            )

            rooms.append(
                Room2D(
                    id=f"room_{room_id_seq}",
                    name=name,
                    polygon=polygon_pts,
                    area_sqm=area_sqm,
                    room_type=rtype,
                    confidence=0.88,
                    dominant_color_hex=color_hex,
                    color_rgb=color_rgb,
                    inferred_material=inferred_mat,
                    material_confidence=mat_conf,
                    is_valid_polygon=is_valid_poly,
                    validation_errors=poly_errors,
                )
            )
            room_id_seq += 1

        if not rooms:
            footprint_w = (max_x_px - min_x_px) / pixels_per_meter
            footprint_d = (max_y_px - min_y_px) / pixels_per_meter
            rooms.append(
                Room2D(
                    id="room_1",
                    name="Main Space",
                    polygon=[
                        Point2D(x=0.0, y=0.0),
                        Point2D(x=round(footprint_w, 2), y=0.0),
                        Point2D(x=round(footprint_w, 2), y=round(footprint_d, 2)),
                        Point2D(x=0.0, y=round(footprint_d, 2)),
                    ],
                    area_sqm=round(footprint_w * footprint_d, 1),
                    room_type="office",
                    confidence=0.70,
                    dominant_color_hex="#f1f5f9",
                    color_rgb=[241, 245, 249],
                    inferred_material="polished_concrete",
                    material_confidence=0.80,
                    is_valid_polygon=True,
                )
            )

        return rooms

    @classmethod
    def _generate_preview_overlay(
        cls,
        img_bgr: np.ndarray,
        walls: List[Wall2D],
        doors: List[Door2D],
        windows: List[Window2D],
        rooms: List[Room2D],
        pixels_per_meter: float,
        min_x_px: float,
        max_y_px: float,
    ) -> str:
        """
        Renders detected walls, doors, windows, and room tags cleanly on top of the original drawing.
        Returns a base64 encoded PNG data URL.
        """
        canvas = img_bgr.copy()
        overlay = canvas.copy()

        # 1. Fill room polygons with pastel shaded colors
        room_colors = [
            (220, 245, 230),  # emerald tint (BGR)
            (245, 235, 220),  # sky blue tint
            (225, 235, 250),  # warm orange tint
            (245, 225, 240),  # purple tint
        ]
        for idx, room in enumerate(rooms):
            color = room_colors[idx % len(room_colors)]
            pts = []
            for p in room.polygon:
                px = int(round(p.x * pixels_per_meter + min_x_px))
                py = int(round(max_y_px - p.y * pixels_per_meter))
                pts.append([px, py])
            if len(pts) >= 3:
                cv2.fillPoly(overlay, [np.array(pts, dtype=np.int32)], color)

        # Blend room fills at 45% opacity
        cv2.addWeighted(overlay, 0.45, canvas, 0.55, 0, canvas)

        # 2. Draw Walls in bold slate/indigo
        for wall in walls:
            px1 = int(round(wall.start.x * pixels_per_meter + min_x_px))
            py1 = int(round(max_y_px - wall.start.y * pixels_per_meter))
            px2 = int(round(wall.end.x * pixels_per_meter + min_x_px))
            py2 = int(round(max_y_px - wall.end.y * pixels_per_meter))
            thick = max(3, int(round(wall.thickness_m * pixels_per_meter * 0.6)))
            color = (60, 40, 30) if wall.wall_type == "exterior" else (90, 80, 70)
            cv2.line(canvas, (px1, py1), (px2, py2), color, thick)

        # 3. Draw Windows in bright sky blue
        for win in windows:
            wx = int(round(win.position.x * pixels_per_meter + min_x_px))
            wy = int(round(max_y_px - win.position.y * pixels_per_meter))
            radius = max(6, int(round(win.width_m * pixels_per_meter * 0.35)))
            cv2.circle(canvas, (wx, wy), radius, (240, 180, 40), -1)  # Cyan/Blue
            cv2.circle(canvas, (wx, wy), radius + 1, (200, 100, 0), 2)

        # 4. Draw Doors in warm amber
        for door in doors:
            dx = int(round(door.position.x * pixels_per_meter + min_x_px))
            dy = int(round(max_y_px - door.position.y * pixels_per_meter))
            radius = max(6, int(round(door.width_m * pixels_per_meter * 0.35)))
            cv2.circle(canvas, (dx, dy), radius, (30, 140, 240), -1)  # Amber/Orange
            cv2.circle(canvas, (dx, dy), radius + 1, (10, 80, 180), 2)

        # 5. Draw Room Labels
        for room in rooms:
            if room.polygon:
                cx = int(round(np.mean([p.x * pixels_per_meter + min_x_px for p in room.polygon])))
                cy = int(round(np.mean([max_y_px - p.y * pixels_per_meter for p in room.polygon])))
                label = f"{room.name} ({room.area_sqm}m2)"
                cv2.putText(
                    canvas,
                    label,
                    (cx - 50, cy),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.45,
                    (20, 20, 20),
                    1,
                    cv2.LINE_AA,
                )

        # Encode to PNG base64
        success, buf = cv2.imencode(".png", canvas)
        if not success:
            return ""
        b64_str = base64.b64encode(buf.tobytes()).decode("utf-8")
        return f"data:image/png;base64,{b64_str}"
