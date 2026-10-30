import os
import math
import uuid
import datetime
from typing import Dict, List, Any, Tuple, Optional
import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.geom
from app.models.digital_twin import (
    BuildingModel,
    BuildingModelDetail,
    BuildingElement,
    ElementGeometry,
    BoundingBox3D,
    StoreyInfo,
)

SUPPORTED_IFC_TYPES = [
    "IfcWall",
    "IfcWallStandardCase",
    "IfcSlab",
    "IfcColumn",
    "IfcBeam",
    "IfcFooting",
    "IfcDoor",
    "IfcWindow",
    "IfcStair",
    "IfcRoof",
    "IfcSpace",
    "IfcBuildingElementProxy",
]

class IfcParserService:
    @classmethod
    def parse_ifc_file(
        cls,
        filepath: str,
        filename: str,
        model_id: Optional[str] = None
    ) -> Tuple[BuildingModelDetail, List[str], List[str]]:
        """
        Parses a physical IFC file using IfcOpenShell.
        Returns:
            (BuildingModelDetail, parsing_warnings, missing_information_list)
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"IFC file not found: {filepath}")

        model_id = model_id or str(uuid.uuid4())
        warnings: List[str] = []
        missing_info: List[str] = []

        try:
            ifc_file = ifcopenshell.open(filepath)
        except Exception as e:
            raise ValueError(f"Failed to parse IFC file structure: {str(e)}")

        schema_version = ifc_file.schema

        # 1. Inspect Project, Site, Building
        project_name = None
        projects = ifc_file.by_type("IfcProject")
        if projects:
            project_name = projects[0].Name or projects[0].GlobalId

        site_name = None
        sites = ifc_file.by_type("IfcSite")
        if sites:
            site_name = sites[0].Name or sites[0].GlobalId

        building_name = None
        buildings = ifc_file.by_type("IfcBuilding")
        if buildings:
            building_name = buildings[0].Name or buildings[0].GlobalId

        # 2. Extract Units
        length_unit = "METRE"
        length_scale = 1.0  # Multiplier to convert to metres
        try:
            unit_assignments = ifc_file.by_type("IfcUnitAssignment")
            if unit_assignments:
                for unit in unit_assignments[0].Units:
                    if hasattr(unit, "UnitType") and unit.UnitType == "LENGTHUNIT":
                        if hasattr(unit, "Prefix") and unit.Prefix:
                            prefix = str(unit.Prefix).upper()
                            if "MILLI" in prefix:
                                length_unit = "MILLIMETRE"
                                length_scale = 0.001
                            elif "CENTI" in prefix:
                                length_unit = "CENTIMETRE"
                                length_scale = 0.01
                        elif hasattr(unit, "Name") and unit.Name:
                            u_name = str(unit.Name).upper()
                            if "FOOT" in u_name or "FEET" in u_name:
                                length_unit = "FOOT"
                                length_scale = 0.3048
                            elif "INCH" in u_name:
                                length_unit = "INCH"
                                length_scale = 0.0254
        except Exception as e:
            warnings.append(f"Could not reliably determine length units from IfcUnitAssignment ({str(e)}). Assuming metric meters.")

        # 3. Extract Storeys & Spatial Mapping
        storeys_dict: Dict[str, StoreyInfo] = {}
        element_to_storey: Dict[str, Tuple[str, str]] = {}  # elem_guid -> (storey_id, storey_name)

        ifc_storeys = ifc_file.by_type("IfcBuildingStorey")
        if ifc_storeys:
            for st in ifc_storeys:
                s_id = st.GlobalId or str(st.id())
                s_name = st.Name or f"Storey {st.id()}"
                elev = getattr(st, "Elevation", None)
                elevation_m = (float(elev) * length_scale) if (elev is not None and not math.isnan(float(elev))) else None
                storeys_dict[s_id] = StoreyInfo(
                    storey_id=s_id,
                    name=s_name,
                    elevation_m=elevation_m,
                    element_count=0
                )

                # RelContainedInSpatialStructure
                try:
                    for rel in getattr(st, "ContainsElements", []):
                        for elem in getattr(rel, "RelatedElements", []):
                            element_to_storey[elem.GlobalId] = (s_id, s_name)
                except Exception:
                    pass

                # RelAggregates (e.g. IfcSpace decomposed under IfcBuildingStorey)
                try:
                    for rel in getattr(st, "IsDecomposedBy", []):
                        for elem in getattr(rel, "RelatedObjects", []):
                            element_to_storey[elem.GlobalId] = (s_id, s_name)
                except Exception:
                    pass
        else:
            missing_info.append("No IfcBuildingStorey spatial hierarchy detected. Elements will be mapped to a default level.")

        # 4. Check for Unsupported Elements (e.g. MEP, Furniture, Railings)
        unsupported_elements: Dict[str, int] = {}
        try:
            all_products = ifc_file.by_type("IfcProduct")
            for prod in all_products:
                prod_type = prod.is_a()
                if (
                    prod_type not in SUPPORTED_IFC_TYPES
                    and prod_type not in ["IfcProject", "IfcSite", "IfcBuilding", "IfcBuildingStorey", "IfcSpace"]
                ):
                    unsupported_elements[prod_type] = unsupported_elements.get(prod_type, 0) + 1
        except Exception:
            pass

        if unsupported_elements:
            unsupported_desc = ", ".join([f"{k} ({v})" for k, v in unsupported_elements.items()])
            warnings.append(
                f"Model contains {sum(unsupported_elements.values())} unsupported non-structural / non-envelope elements: {unsupported_desc}. These were skipped from 3D twin rendering."
            )

        # 5. Extract Topological Relationships & Connectivity Graphs
        opening_to_wall: Dict[str, str] = {}
        try:
            for rel in ifc_file.by_type("IfcRelVoidsElement"):
                wall = rel.RelatingBuildingElement
                opening = rel.RelatedOpeningElement
                if wall and opening:
                    opening_to_wall[opening.GlobalId] = wall.GlobalId
        except Exception:
            pass

        door_window_to_wall: Dict[str, str] = {}
        wall_to_apertures: Dict[str, List[str]] = {}
        try:
            for rel in ifc_file.by_type("IfcRelFillsElement"):
                opening = rel.RelatingOpeningElement
                aperture = rel.RelatedBuildingElement
                if opening and aperture:
                    host_wall = opening_to_wall.get(opening.GlobalId)
                    if host_wall:
                        door_window_to_wall[aperture.GlobalId] = host_wall
                        wall_to_apertures.setdefault(host_wall, []).append(aperture.GlobalId)
        except Exception:
            pass

        connectivity_map: Dict[str, List[str]] = {}
        try:
            for rel in ifc_file.by_type("IfcRelConnectsElements"):
                ea = getattr(rel, "RelatingElement", None)
                eb = getattr(rel, "RelatedElement", None)
                if ea and eb:
                    ga = getattr(ea, "GlobalId", None)
                    gb = getattr(eb, "GlobalId", None)
                    if ga and gb:
                        connectivity_map.setdefault(ga, []).append(gb)
                        connectivity_map.setdefault(gb, []).append(ga)
        except Exception:
            pass

        space_containment: Dict[str, str] = {}
        try:
            for rel in ifc_file.by_type("IfcRelContainedInSpatialStructure"):
                struct = getattr(rel, "RelatingStructure", None)
                if struct and struct.is_a("IfcSpace"):
                    for elem in getattr(rel, "RelatedElements", []):
                        eguid = getattr(elem, "GlobalId", None)
                        if eguid:
                            space_containment[eguid] = struct.GlobalId
        except Exception:
            pass

        # 6. Initialize Geometry Settings for Tessellation
        geom_settings = ifcopenshell.geom.settings()
        geom_settings.set(geom_settings.USE_WORLD_COORDS, True)
        geom_settings.set(geom_settings.WELD_VERTICES, True)

        extracted_elements: List[BuildingElement] = []
        element_counts: Dict[str, int] = {}
        all_prop_names: set = set()

        min_x = min_y = min_z = float("inf")
        max_x = max_y = max_z = float("-inf")

        # 7. Extract Supported Building Elements
        for elem_type in SUPPORTED_IFC_TYPES:
            entities = ifc_file.by_type(elem_type)
            if not entities:
                continue

            element_counts[elem_type] = len(entities)

            for entity in entities:
                global_id = entity.GlobalId or str(uuid.uuid4())
                name = entity.Name or f"{elem_type}_{entity.id()}"
                s_id, s_name = element_to_storey.get(global_id, (None, None))
                if s_id and s_id in storeys_dict:
                    storeys_dict[s_id].element_count += 1

                # Extract property sets
                source_properties: Dict[str, Any] = {}
                try:
                    psets = ifcopenshell.util.element.get_psets(entity)
                    for pset_name, pset_data in psets.items():
                        source_properties[pset_name] = pset_data
                        for p_key in pset_data.keys():
                            all_prop_names.add(f"{pset_name}.{p_key}")
                except Exception:
                    pass

                # Extract material
                materials_list: List[str] = []
                try:
                    mat = ifcopenshell.util.element.get_material(entity)
                    if mat:
                        if hasattr(mat, "Name") and mat.Name:
                            materials_list.append(str(mat.Name))
                        elif isinstance(mat, str):
                            materials_list.append(mat)
                        elif hasattr(mat, "Materials"):
                            for m in mat.Materials:
                                if hasattr(m, "Name") and m.Name:
                                    materials_list.append(str(m.Name))
                except Exception:
                    pass

                # Extract or generate 3D tessellated geometry
                element_geo: Optional[ElementGeometry] = None
                bbox: Optional[BoundingBox3D] = None
                confidence = "imported"

                try:
                    shape = ifcopenshell.geom.create_shape(geom_settings, entity)
                    if shape:
                        verts = shape.geometry.verts  # Flat list: [x0, y0, z0, x1, y1, z1, ...]
                        faces = shape.geometry.faces  # Flat list: [v0, v1, v2, ...]

                        if verts and len(verts) >= 9 and faces:
                            # Apply length scaling to meters if needed
                            scaled_verts = [v * length_scale for v in verts]

                            # Calculate entity bounding box
                            xs = scaled_verts[0::3]
                            ys = scaled_verts[1::3]
                            zs = scaled_verts[2::3]

                            e_min_x, e_max_x = min(xs), max(xs)
                            e_min_y, e_max_y = min(ys), max(ys)
                            e_min_z, e_max_z = min(zs), max(zs)

                            bbox = BoundingBox3D(
                                min_x=round(e_min_x, 3),
                                min_y=round(e_min_y, 3),
                                min_z=round(e_min_z, 3),
                                max_x=round(e_max_x, 3),
                                max_y=round(e_max_y, 3),
                                max_z=round(e_max_z, 3),
                                center_x=round((e_min_x + e_max_x) / 2.0, 3),
                                center_y=round((e_min_y + e_max_y) / 2.0, 3),
                                center_z=round((e_min_z + e_max_z) / 2.0, 3),
                                width=round(e_max_x - e_min_x, 3),
                                height=round(e_max_y - e_min_y, 3),
                                depth=round(e_max_z - e_min_z, 3),
                            )

                            min_x = min(min_x, e_min_x)
                            max_x = max(max_x, e_max_x)
                            min_y = min(min_y, e_min_y)
                            max_y = max(max_y, e_max_y)
                            min_z = min(min_z, e_min_z)
                            max_z = max(max_z, e_max_z)

                            # Cap maximum faces to prevent frontend browser crash
                            max_allowed_faces = 4500
                            face_count = len(faces) // 3
                            if face_count > max_allowed_faces:
                                # Subsample faces
                                step = max(2, face_count // max_allowed_faces)
                                sampled_faces = []
                                for idx in range(0, len(faces), 3 * step):
                                    sampled_faces.extend(faces[idx:idx+3])
                                faces_to_store = sampled_faces
                                warnings.append(f"Entity '{name}' geometry face count ({face_count}) decimated for WebGL performance.")
                            else:
                                faces_to_store = list(faces)

                            element_geo = ElementGeometry(
                                format="indexed_mesh",
                                vertices=[round(v, 4) for v in scaled_verts],
                                faces=faces_to_store,
                                vertex_count=len(scaled_verts) // 3,
                                face_count=len(faces_to_store) // 3
                            )
                except Exception as shape_err:
                    warnings.append(f"Geometric tessellation skipped for entity '{name}' ({elem_type}): {str(shape_err)}")
                    confidence = "unverified"

                # Quantity estimates & dimensional preservation
                quantities: Dict[str, float] = {}
                if bbox:
                    # Estimate approximate envelope dimensions from bounding box
                    quantities["bbox_width_m"] = bbox.width
                    quantities["bbox_height_m"] = bbox.height
                    quantities["bbox_depth_m"] = bbox.depth
                    quantities["approx_volume_m3"] = round(bbox.width * bbox.height * bbox.depth, 3)

                # Check entity attributes for direct dimension parameters
                for dim_attr in ["OverallWidth", "OverallHeight", "NominalWidth", "NominalHeight"]:
                    val = getattr(entity, dim_attr, None)
                    if val is not None:
                        try:
                            quantities[dim_attr.lower()] = round(float(val) * length_scale, 3)
                        except (ValueError, TypeError):
                            pass

                # Check property sets for dimensional attributes
                for pset_data in source_properties.values():
                    if isinstance(pset_data, dict):
                        for k, v in pset_data.items():
                            if k in ["OverallWidth", "OverallHeight", "NominalWidth", "NominalHeight", "Width", "Height", "Length", "Thickness", "Span"]:
                                try:
                                    if isinstance(v, (int, float)) and not math.isnan(float(v)):
                                        quantities[k.lower()] = round(float(v), 3)
                                except Exception:
                                    pass

                # Extract classifications
                classifications: List[str] = []
                if hasattr(entity, "PredefinedType") and entity.PredefinedType:
                    classifications.append(f"PredefinedType: {entity.PredefinedType}")
                if hasattr(entity, "ObjectType") and entity.ObjectType:
                    classifications.append(f"ObjectType: {entity.ObjectType}")
                try:
                    for rel in getattr(entity, "HasAssociations", []):
                        if rel.is_a("IfcRelAssociatesClassification"):
                            cref = getattr(rel, "RelatingClassification", None)
                            if cref:
                                c_name = getattr(cref, "Name", None) or getattr(cref, "ItemReference", None) or str(cref)
                                classifications.append(f"Classification: {c_name}")
                except Exception:
                    pass

                # Determine structural role, load-bearing status, material grade, and fire rating
                is_load_bearing: Optional[bool] = None
                structural_role: str = "unspecified"
                mat_grade: Optional[str] = None
                fire_rating: Optional[str] = None

                # Check property sets
                for pset_name, pset_data in source_properties.items():
                    if isinstance(pset_data, dict):
                        if "LoadBearing" in pset_data:
                            val = pset_data["LoadBearing"]
                            if isinstance(val, bool):
                                is_load_bearing = val
                            elif str(val).lower() in ["true", "1", "yes"]:
                                is_load_bearing = True
                            elif str(val).lower() in ["false", "0", "no"]:
                                is_load_bearing = False
                        if "FireRating" in pset_data:
                            fire_rating = str(pset_data["FireRating"])
                        if "StrengthClass" in pset_data:
                            mat_grade = str(pset_data["StrengthClass"])

                # Classify structural role based on IFC entity type and load bearing status
                if elem_type in ["IfcColumn", "IfcBeam"]:
                    structural_role = "structural_framing"
                    if is_load_bearing is None:
                        is_load_bearing = True
                elif elem_type == "IfcFooting":
                    structural_role = "load_bearing"
                    is_load_bearing = True
                elif elem_type in ["IfcWall", "IfcWallStandardCase"]:
                    if is_load_bearing is True:
                        structural_role = "load_bearing"
                    elif is_load_bearing is False:
                        structural_role = "non_load_bearing_partition"
                    else:
                        thick = quantities.get("thickness", quantities.get("bbox_width_m", 0.2))
                        if thick >= 0.20:
                            structural_role = "load_bearing"
                            is_load_bearing = True
                        else:
                            structural_role = "non_load_bearing_partition"
                            is_load_bearing = False
                elif elem_type == "IfcSlab":
                    structural_role = "load_bearing"
                    if is_load_bearing is None:
                        is_load_bearing = True
                elif elem_type in ["IfcDoor", "IfcWindow"]:
                    structural_role = "aperture"
                    is_load_bearing = False
                elif elem_type == "IfcSpace":
                    structural_role = "spatial_volume"
                    is_load_bearing = False

                # Search materials for grade
                if not mat_grade and materials_list:
                    for m in materials_list:
                        m_upper = m.upper()
                        for g in ["C20/25", "C25/30", "C30/37", "C35/45", "C40/50", "M20", "M25", "M30", "M35", "M40", "S275", "S355"]:
                            if g in m_upper:
                                mat_grade = g
                                break

                # Assemble element relationships
                elem_relationships = {
                    "hosted_in": door_window_to_wall.get(global_id),
                    "hosts": wall_to_apertures.get(global_id, []),
                    "connected_to": connectivity_map.get(global_id, []),
                    "storey_id": s_id,
                    "storey_name": s_name,
                    "space_contained_in": space_containment.get(global_id),
                }

                b_element = BuildingElement(
                    element_id=f"elem_{len(extracted_elements) + 1}",
                    source_global_id=global_id,
                    element_type=elem_type,
                    name=name,
                    storey_id=s_id,
                    storey_name=s_name,
                    geometry=element_geo,
                    bounding_box=bbox,
                    source_properties=source_properties,
                    materials=materials_list,
                    classifications=classifications,
                    relationships=elem_relationships,
                    quantity_estimates=quantities,
                    property_provenance={
                        "source": "IfcOpenShell",
                        "parser_version": ifcopenshell.__version__,
                        "extraction_mode": "native_step"
                    },
                    structural_role=structural_role,
                    is_load_bearing=is_load_bearing,
                    structural_material_grade=mat_grade,
                    fire_rating=fire_rating,
                    confidence_status=confidence
                )
                extracted_elements.append(b_element)

        # 6. Global Model Bounding Box & Centering
        model_bbox = None
        if min_x != float("inf"):
            model_bbox = BoundingBox3D(
                min_x=round(min_x, 3),
                min_y=round(min_y, 3),
                min_z=round(min_z, 3),
                max_x=round(max_x, 3),
                max_y=round(max_y, 3),
                max_z=round(max_z, 3),
                center_x=round((min_x + max_x) / 2.0, 3),
                center_y=round((min_y + max_y) / 2.0, 3),
                center_z=round((min_z + max_z) / 2.0, 3),
                width=round(max_x - min_x, 3),
                height=round(max_y - min_y, 3),
                depth=round(max_z - min_z, 3),
            )

        if not extracted_elements:
            missing_info.append("No supported building elements (walls, slabs, columns, beams, windows, doors) found in IFC file.")

        # Check for structural analytical models
        has_structural_model = len(ifc_file.by_type("IfcStructuralItem")) > 0 or len(ifc_file.by_type("IfcStructuralAnalysisModel")) > 0
        if not has_structural_model:
            missing_info.append("No structural analytical model (IfcStructuralAnalysisModel) detected; model represents visual architectural geometry only.")

        structural_audit = {
            "has_structural_analytical_model": has_structural_model,
            "total_structural_elements": sum(1 for e in extracted_elements if e.is_load_bearing),
            "total_partitions": sum(1 for e in extracted_elements if e.structural_role == "non_load_bearing_partition"),
            "columns_count": element_counts.get("IfcColumn", 0),
            "beams_count": element_counts.get("IfcBeam", 0),
            "slabs_count": element_counts.get("IfcSlab", 0),
            "load_bearing_walls_count": sum(1 for e in extracted_elements if e.element_type in ["IfcWall", "IfcWallStandardCase"] and e.is_load_bearing),
            "missing_structural_documentation": [
                "Bar Bending Schedule (BBS) & Structural Reinforcement Detailing",
                "Concrete Compressive Strength Test Logs (IS 456 / EN 206)",
                "3D Finite Element Structural Calculation & Load Path Report",
                "Geotechnical Soil-Structure Interaction & Foundation Settlement Analysis"
            ],
            "engineering_disclaimer": "Visual 3D BIM geometry represents spatial envelope and physical dimensions only. It does not constitute a structural engineering model or verify load capacity, wind shear resistance, or seismic adequacy. Independent structural engineering analysis by a licensed professional is mandatory."
        }

        model = BuildingModelDetail(
            model_id=model_id,
            source_type="ifc",
            source_filename=filename,
            import_timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            schema_version=schema_version,
            units={"length": length_unit, "coordinate_system": "WCS_Z_UP"},
            project_name=project_name,
            site_name=site_name,
            building_name=building_name,
            storeys=list(storeys_dict.values()),
            element_counts_by_type=element_counts,
            total_element_count=len(extracted_elements),
            available_properties=sorted(list(all_prop_names)),
            missing_data=missing_info,
            structural_audit=structural_audit,
            bounding_box=model_bbox,
            provenance_metadata={
                "parser": "IfcOpenShell",
                "version": ifcopenshell.__version__,
                "length_scale_applied": length_scale,
                "sanitized_filename": os.path.basename(filename),
                "unsupported_elements": unsupported_elements,
            },
            elements=extracted_elements
        )

        return (model, warnings, missing_info)
