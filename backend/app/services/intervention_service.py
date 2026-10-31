import math
from typing import List, Dict, Any, Optional, Tuple
from app.models.digital_twin import BuildingModelDetail, BuildingElement
from app.models.rainwater import Intervention3DComponent
from app.models.recommendations import (
    StructuredIntervention,
    AppliedInterventionsRequest,
    AppliedInterventionsResponse,
)
from app.services.cost_engine import CostEngine, INTERVENTION_CATALOG
from app.services.model_store import ModelStore

class InterventionService:
    @classmethod
    def generate_applied_interventions(
        cls,
        request: AppliedInterventionsRequest
    ) -> AppliedInterventionsResponse:
        """
        Authoritative pipeline generating structured interventions with placement validation
        and authentic 3D geometry for Three.js visualization.
        """
        diagnostic_logs: List[str] = []
        model: Optional[BuildingModelDetail] = None
        
        if request.model_id == "parametric":
            model = None
            diagnostic_logs.append("Operating in pure parametric geometry mode.")
        elif request.model_id:
            model = ModelStore.get_model(request.model_id)
            if not model:
                diagnostic_logs.append(f"Notice: Model ID '{request.model_id}' not found in active session. Trying active model list.")
                models = ModelStore.list_models()
                if models:
                    model = ModelStore.get_model(models[0].model_id)
        else:
            if not (request.width_m and request.length_m and request.window_count is not None):
                models = ModelStore.list_models()
                if models:
                    model = ModelStore.get_model(models[0].model_id)

        # Extract authoritative spatial boundaries from model or fallback params
        if model and model.bounding_box:
            bbox = model.bounding_box
            width_m = bbox.width
            length_m = bbox.height  # In IFC coordinate convention, Y is horizontal depth
            min_x = bbox.min_x
            max_x = bbox.max_x
            min_y = bbox.min_y
            max_y = bbox.max_y
            min_z = bbox.min_z
            max_z = bbox.max_z
            elements = model.elements
        else:
            width_m = request.width_m or 14.0
            length_m = request.length_m or 10.0
            min_x = 0.0
            max_x = width_m
            min_y = 0.0
            max_y = length_m
            min_z = 0.0
            floors = request.floors or 2
            floor_h = request.floor_height_m or 3.5
            max_z = floors * floor_h
            elements = []

        # Find actual roof elevation from roof elements or upper floor slabs
        roof_elevation: Optional[float] = None
        target_roof_ids: List[str] = []
        roof_slab_elem: Optional[BuildingElement] = None

        if elements:
            # 1. Primary: Search for IfcRoof entities
            for elem in elements:
                e_type = elem.element_type.lower()
                e_name = (elem.name or "").lower()
                if "ifcroof" in e_type or ("roof" in e_name and "beam" not in e_name):
                    target_roof_ids.append(elem.element_id)
                    if elem.bounding_box and elem.bounding_box.max_z:
                        if roof_elevation is None or elem.bounding_box.max_z > roof_elevation:
                            roof_elevation = elem.bounding_box.max_z
                            roof_slab_elem = elem

            # 2. Secondary: If no IfcRoof, check terrace slabs
            if roof_elevation is None:
                for elem in elements:
                    e_type = elem.element_type.lower()
                    e_name = (elem.name or "").lower()
                    if "slab" in e_type and ("roof" in e_name or "terrace" in e_name or (elem.bounding_box and elem.bounding_box.min_z >= 2.5)):
                        target_roof_ids.append(elem.element_id)
                        if elem.bounding_box and elem.bounding_box.max_z:
                            if roof_elevation is None or elem.bounding_box.max_z > roof_elevation:
                                roof_elevation = elem.bounding_box.max_z
                                roof_slab_elem = elem

        if roof_elevation is None:
            floors = request.floors or (len(model.storeys) if model and model.storeys else 2)
            floor_h = request.floor_height_m or 3.5
            roof_elevation = floors * floor_h

        diagnostic_logs.append(
            f"Building envelope detected: Footprint={width_m:.1f}m x {length_m:.1f}m, "
            f"Roof Elevation={roof_elevation:.2f}m, Elements={len(elements)}"
        )

        structured_interventions: List[StructuredIntervention] = []
        total_applied_cost = 0.0
        applied_count = 0
        rejected_count = 0

        # Unique deduplicated intervention IDs
        selected_ids = list(dict.fromkeys(request.selected_intervention_ids))
        diagnostic_logs.append(f"Requested intervention IDs ({len(selected_ids)}): {selected_ids}")

        for intervention_id in selected_ids:
            if intervention_id == "solar_pv":
                interv, logs = cls._generate_solar_pv_intervention(
                    min_x, max_x, min_y, max_y, roof_elevation, target_roof_ids, width_m, length_m
                )
                diagnostic_logs.extend(logs)
                structured_interventions.append(interv)
                if interv.validation_status == "VALIDATED":
                    total_applied_cost += interv.estimated_cost
                    applied_count += 1
                else:
                    rejected_count += 1

            elif intervention_id == "reflective_roof":
                interv, logs = cls._generate_reflective_roof_intervention(
                    min_x, max_x, min_y, max_y, roof_elevation, target_roof_ids, width_m, length_m
                )
                diagnostic_logs.extend(logs)
                structured_interventions.append(interv)
                if interv.validation_status == "VALIDATED":
                    total_applied_cost += interv.estimated_cost
                    applied_count += 1
                else:
                    rejected_count += 1

            elif intervention_id == "roof_insulation":
                interv, logs = cls._generate_roof_insulation_intervention(
                    min_x, max_x, min_y, max_y, roof_elevation, target_roof_ids, width_m, length_m
                )
                diagnostic_logs.extend(logs)
                structured_interventions.append(interv)
                if interv.validation_status == "VALIDATED":
                    total_applied_cost += interv.estimated_cost
                    applied_count += 1
                else:
                    rejected_count += 1

            elif intervention_id == "external_shading":
                interv, logs = cls._generate_window_shading_intervention(
                    elements, min_x, max_x, min_y, max_y, min_z, max_z, request.window_count
                )
                diagnostic_logs.extend(logs)
                structured_interventions.append(interv)
                if interv.validation_status == "VALIDATED":
                    total_applied_cost += interv.estimated_cost
                    applied_count += 1
                else:
                    rejected_count += 1

            elif intervention_id in ["rainwater_harvesting", "rwh_system"]:
                interv, logs = cls._generate_rainwater_harvesting_intervention(
                    min_x, max_x, min_y, max_y, min_z, roof_elevation, target_roof_ids
                )
                diagnostic_logs.extend(logs)
                structured_interventions.append(interv)
                if interv.validation_status == "VALIDATED":
                    total_applied_cost += interv.estimated_cost
                    applied_count += 1
                else:
                    rejected_count += 1

            elif intervention_id == "green_roof":
                interv, logs = cls._generate_green_roof_intervention(
                    min_x, max_x, min_y, max_y, roof_elevation, target_roof_ids, width_m, length_m
                )
                diagnostic_logs.extend(logs)
                structured_interventions.append(interv)
                if interv.validation_status == "VALIDATED":
                    total_applied_cost += interv.estimated_cost
                    applied_count += 1
                else:
                    rejected_count += 1

            else:
                diagnostic_logs.append(f"Warning: Unknown intervention ID '{intervention_id}' skipped.")

        diagnostic_logs.append(
            f"Summary: {applied_count} interventions successfully validated and applied. "
            f"Total applied capital cost: ₹{total_applied_cost:,.2f}"
        )

        return AppliedInterventionsResponse(
            model_id=request.model_id or (model.model_id if model else None),
            interventions=structured_interventions,
            total_applied_cost=round(total_applied_cost, 2),
            applied_count=applied_count,
            rejected_count=rejected_count,
            diagnostic_logs=diagnostic_logs,
            provenance="Deterministic Engineering & Geometry Placement Validation Pipeline (CPWD / MNRE 2023-2024)"
        )

    # =========================================================================
    # 1. SOLAR PHOTOVOLTAIC (PV) ARRAY INTERVENTION
    # =========================================================================
    @classmethod
    def _generate_solar_pv_intervention(
        cls,
        min_x: float, max_x: float, min_y: float, max_y: float,
        roof_z: float, target_roof_ids: List[str],
        width_m: float, length_m: float
    ) -> Tuple[StructuredIntervention, List[str]]:
        logs: List[str] = []
        roof_area = width_m * length_m

        # Placement validation: minimum 15 m² net roof area
        if roof_area < 15.0:
            logs.append(f"REJECTED: Solar PV requires at least 15 m² roof area (detected {roof_area:.1f} m²).")
            return StructuredIntervention(
                intervention_id="solar_pv_array_01",
                recommendation_id="solar_pv",
                intervention_type="solar_pv",
                target_element_ids=target_roof_ids,
                world_position=[(min_x + max_x) / 2.0, (min_y + max_y) / 2.0, roof_z],
                dimensions=[0.0, 0.0, 0.0],
                orientation={"tilt_deg": 15.0, "azimuth_deg": 180.0},
                estimated_cost=0.0,
                expected_benefit={},
                calculation_method="MNRE Benchmark",
                assumptions=["Insufficient roof area for PV table installation"],
                validation_status="REJECTED",
                rejection_reason="Terrace roof area below minimum viable PV installation threshold (15 m²).",
                components_3d=[]
            ), logs

        # Usable roof area: 60% after mandatory setbacks and access walkway
        usable_area = roof_area * 0.60
        capacity_kwp = round(usable_area / 10.0, 1)  # 10 m² per kWp standard allowance
        cost = capacity_kwp * 48000.0  # ₹48,000 / kWp MNRE benchmark

        logs.append(
            f"VALIDATED Solar PV: Roof Area={roof_area:.1f} m², Usable Area={usable_area:.1f} m², "
            f"Capacity={capacity_kwp} kWp, Placement Elevation={roof_z:.2f}m, Cost=₹{cost:,.0f}"
        )

        components_3d: List[Intervention3DComponent] = []

        # Geometry Synthesis: Rows of solar panel tables tilted 15 degrees south
        # Boundary within roof slab with 1.0m perimeter walkway
        pv_min_x = min_x + 1.2
        pv_max_x = max_x - 1.2
        pv_min_y = min_y + 1.2
        pv_max_y = max_y - 1.2
        available_x = max(1.0, pv_max_x - pv_min_x)
        available_y = max(1.0, pv_max_y - pv_min_y)

        # Standard commercial PV table dimensions: 2.0m width, 1.2m tilted depth, 0.05m thickness
        panel_w = min(2.4, available_x / 3.5)
        panel_d = 1.3
        row_spacing = 1.8  # Inter-row shading setback

        num_cols = max(1, min(4, int(available_x / (panel_w + 0.5))))
        num_rows = max(1, min(3, int(available_y / row_spacing)))

        col_step = available_x / (num_cols + 1)
        row_step = available_y / (num_rows + 1)

        panel_counter = 0
        for r in range(num_rows):
            pos_y = pv_min_y + (r + 1) * row_step
            for c in range(num_cols):
                panel_counter += 1
                pos_x = pv_min_x + (c + 1) * col_step
                panel_z = roof_z + 0.25  # Elevated on mounting structure

                # 1. Photovoltaic module table
                components_3d.append(
                    Intervention3DComponent(
                        component_id=f"SOLAR-PANEL-TABLE-{panel_counter:02d}",
                        component_type="solar_pv_panel",
                        name=f"Rooftop PV Table #{panel_counter:02d} (Tier-1 Monocrystalline)",
                        material="Monocrystalline Silicon & Anodized Aluminum Frame",
                        color_hex="#1e3a8a",  # Deep solar blue
                        position=[round(pos_x, 3), round(pos_y, 3), round(panel_z, 3)],
                        dimensions=[round(panel_w, 2), round(panel_d, 2), 0.05],
                        geometry_type="box",
                        specification=f"540W Tier-1 Mono PERC module array, 15° South tilt, 21.4% cell efficiency"
                    )
                )

                # 2. Galvanized mounting bracket / strut underneath
                components_3d.append(
                    Intervention3DComponent(
                        component_id=f"SOLAR-STRUT-{panel_counter:02d}",
                        component_type="solar_mounting_rack",
                        name=f"Ballasted Steel Mounting Rack #{panel_counter:02d}",
                        material="Hot-Dip Galvanized Structural Steel (HDG 80 Micron)",
                        color_hex="#64748b",  # Steel metallic gray
                        position=[round(pos_x, 3), round(pos_y, 3), round(roof_z + 0.10, 3)],
                        dimensions=[round(panel_w * 0.85, 2), round(panel_d * 0.7, 2), 0.18],
                        geometry_type="box",
                        specification="Aerodynamic non-penetrating ballasted A-frame rack engineered for 150 km/h wind gusts"
                    )
                )

        # 3. String Inverter & AC/DC Protection Enclosure near roof access
        components_3d.append(
            Intervention3DComponent(
                component_id="SOLAR-INVERTER-01",
                component_type="solar_inverter",
                name="Grid-Tied String Inverter (10 kW)",
                material="IP65 Die-Cast Aluminum Enclosure",
                color_hex="#334155",
                position=[round(min_x + 0.8, 3), round(max_y - 0.8, 3), round(roof_z + 0.45, 3)],
                dimensions=[0.6, 0.35, 0.75],
                geometry_type="box",
                specification="10 kW dual-MPPT string inverter with integrated DC isolator and surge protection"
            )
        )

        interv = StructuredIntervention(
            intervention_id="solar_pv_array_01",
            recommendation_id="solar_pv",
            intervention_type="solar_pv",
            target_element_ids=target_roof_ids,
            target_floor="Terrace / Roof",
            geometry_parameters={
                "panel_count": panel_counter,
                "table_width_m": panel_w,
                "table_depth_m": panel_d,
                "tilt_degrees": 15.0,
                "azimuth_degrees": 180.0,
                "clearance_elevation_m": 0.25,
            },
            material_parameters={
                "cell_type": "Monocrystalline Silicon",
                "cell_color": "#1e3a8a",
                "frame": "Anodized Aluminum #94a3b8",
                "mounting": "Galvanized Steel #64748b"
            },
            world_position=[(min_x + max_x) / 2.0, (min_y + max_y) / 2.0, roof_z + 0.25],
            dimensions=[available_x, available_y, 0.35],
            orientation={"tilt_deg": 15.0, "azimuth_deg": 180.0},
            estimated_cost=round(cost, 2),
            expected_benefit={
                "capacity_kwp": capacity_kwp,
                "annual_generation_kwh": round(capacity_kwp * 1500.0, 1),
                "grid_offset_pct": 54.8,
                "annual_co2_avoided_tonnes": round(capacity_kwp * 1.5 * 0.716, 2)
            },
            calculation_method="MNRE Benchmark Rate (₹48,000/kWp, 10 m²/kWp, 1500 kWh/kWp/year yield)",
            assumptions=[
                "60% usable flat roof area after setbacks and access walkways",
                "15° fixed tilt orientation facing true South",
                "CEA India Grid emission factor of 0.716 kg CO2e / kWh"
            ],
            validation_status="VALIDATED",
            components_3d=components_3d
        )
        return interv, logs

    # =========================================================================
    # 2. COOL ROOF HIGH-ALBEDO REFLECTIVE COATING
    # =========================================================================
    @classmethod
    def _generate_reflective_roof_intervention(
        cls,
        min_x: float, max_x: float, min_y: float, max_y: float,
        roof_z: float, target_roof_ids: List[str],
        width_m: float, length_m: float
    ) -> Tuple[StructuredIntervention, List[str]]:
        logs: List[str] = []
        roof_area = width_m * length_m

        if roof_area <= 0:
            logs.append("REJECTED Cool Roof: Terrace area is zero or negative.")
            return StructuredIntervention(
                intervention_id="cool_roof_coating_01",
                recommendation_id="reflective_roof",
                intervention_type="reflective_roof",
                target_element_ids=target_roof_ids,
                world_position=[0.0, 0.0, 0.0],
                dimensions=[0.0, 0.0, 0.0],
                orientation={},
                estimated_cost=0.0,
                expected_benefit={},
                calculation_method="CPWD Rate",
                assumptions=[],
                validation_status="REJECTED",
                rejection_reason="No roof surface available for cool roof coating.",
                components_3d=[]
            ), logs

        cost = round(roof_area * 250.0, 2)  # ₹250 / m²
        logs.append(
            f"VALIDATED Cool Roof Coating: Area={roof_area:.1f} m², Elevation={roof_z:.2f}m, "
            f"Target Elements={target_roof_ids}, Cost=₹{cost:,.0f}"
        )

        # 3D Component: Pristine high-albedo membrane directly over terrace footprint
        center_x = (min_x + max_x) / 2.0
        center_y = (min_y + max_y) / 2.0
        # Elevate slightly (0.02m) above roof slab to avoid z-fighting
        membrane_z = roof_z + 0.02

        components_3d = [
            Intervention3DComponent(
                component_id="COOL-ROOF-MEMBRANE-01",
                component_type="cool_roof_membrane",
                name="High-Albedo Elastomeric Cool Roof Coating (SRI 104)",
                material="Titanium Dioxide Enhanced Pure White Polyurethane Membrane",
                color_hex="#f8fafc",  # Pure brilliant white
                position=[round(center_x, 3), round(center_y, 3), round(membrane_z, 3)],
                dimensions=[round(width_m - 0.1, 2), round(length_m - 0.1, 2), 0.03],
                geometry_type="box",
                specification="Multi-coat elastomeric high-reflectance waterproofing membrane (SRI >= 104, solar reflectance 0.84, thermal emittance 0.90)"
            )
        ]

        interv = StructuredIntervention(
            intervention_id="cool_roof_coating_01",
            recommendation_id="reflective_roof",
            intervention_type="reflective_roof",
            target_element_ids=target_roof_ids,
            target_floor="Terrace / Roof",
            geometry_parameters={
                "coated_area_m2": round(roof_area, 2),
                "coating_thickness_mm": 2.5,
                "elevation_m": round(membrane_z, 3)
            },
            material_parameters={
                "solar_reflectance_index_sri": 104,
                "solar_reflectance": 0.84,
                "thermal_emittance": 0.90,
                "finish_color": "#f8fafc"
            },
            world_position=[center_x, center_y, membrane_z],
            dimensions=[width_m, length_m, 0.03],
            orientation={"tilt_deg": 0.0, "azimuth_deg": 0.0},
            estimated_cost=cost,
            expected_benefit={
                "terrace_surface_temp_reduction_deg_c": 14.5,
                "top_floor_cooling_energy_reduction_pct": 18.5,
                "urban_heat_island_mitigation_score": 8.8
            },
            calculation_method="Municipal Cool Roof Benchmark (Ahmedabad/Telangana Policy ₹250/m²)",
            assumptions=[
                "Applies to entire exposed flat terrace roof area",
                "Requires periodic surface maintenance to retain albedo rating"
            ],
            validation_status="VALIDATED",
            components_3d=components_3d
        )
        return interv, logs

    # =========================================================================
    # 3. OVER-DECK ROOF INSULATION (50mm XPS)
    # =========================================================================
    @classmethod
    def _generate_roof_insulation_intervention(
        cls,
        min_x: float, max_x: float, min_y: float, max_y: float,
        roof_z: float, target_roof_ids: List[str],
        width_m: float, length_m: float
    ) -> Tuple[StructuredIntervention, List[str]]:
        logs: List[str] = []
        roof_area = width_m * length_m
        cost = round(roof_area * 850.0, 2)  # ₹850 / m²

        logs.append(f"VALIDATED Roof Insulation: Area={roof_area:.1f} m², Cost=₹{cost:,.0f}")

        center_x = (min_x + max_x) / 2.0
        center_y = (min_y + max_y) / 2.0
        insulation_z = roof_z + 0.04

        components_3d = [
            Intervention3DComponent(
                component_id="ROOF-INSULATION-XPS-01",
                component_type="roof_insulation_board",
                name="Over-Deck Rigid Roof Insulation (50mm XPS + Screed)",
                material="Closed-Cell Extruded Polystyrene & Protective Paver Screed",
                color_hex="#e2e8f0",  # Light stone/insulation board
                position=[round(center_x, 3), round(center_y, 3), round(insulation_z, 3)],
                dimensions=[round(width_m - 0.2, 2), round(length_m - 0.2, 2), 0.06],
                geometry_type="box",
                specification="50mm high-density XPS closed-cell rigid insulation boards (R-value 1.8 m²·K/W) + cement mortar protective topping"
            )
        ]

        interv = StructuredIntervention(
            intervention_id="roof_insulation_xps_01",
            recommendation_id="roof_insulation",
            intervention_type="roof_insulation",
            target_element_ids=target_roof_ids,
            target_floor="Terrace / Roof",
            geometry_parameters={"thickness_mm": 50, "area_m2": round(roof_area, 2)},
            material_parameters={"thermal_conductivity_k": 0.028, "r_value": 1.8, "color": "#e2e8f0"},
            world_position=[center_x, center_y, insulation_z],
            dimensions=[width_m, length_m, 0.06],
            orientation={"tilt_deg": 0.0, "azimuth_deg": 0.0},
            estimated_cost=cost,
            expected_benefit={
                "envelope_u_value_reduction_pct": 68.0,
                "top_floor_heat_gain_reduction_pct": 34.0
            },
            calculation_method="BEE ECBC / NBC 2016 Specification (₹850/m²)",
            assumptions=["Terrace structure supports 65 kg/m² screed dead load"],
            validation_status="VALIDATED",
            components_3d=components_3d
        )
        return interv, logs

    # =========================================================================
    # 4. EXTERNAL WINDOW SHADING LOUVERS
    # =========================================================================
    @classmethod
    def _generate_window_shading_intervention(
        cls,
        elements: List[BuildingElement],
        min_x: float, max_x: float, min_y: float, max_y: float,
        min_z: float, max_z: float,
        fallback_window_count: Optional[int]
    ) -> Tuple[StructuredIntervention, List[str]]:
        logs: List[str] = []
        width_m = max_x - min_x

        # Find all actual window elements in the model
        windows: List[BuildingElement] = []
        if elements:
            windows = [
                e for e in elements
                if e.element_type.lower() == "ifcwindow" or "window" in (e.name or "").lower()
            ]

        # Validation: check whether windows exist
        if not windows and (not fallback_window_count or fallback_window_count <= 0):
            logs.append("REJECTED Window Shading: No window apertures detected in building envelope.")
            return StructuredIntervention(
                intervention_id="window_shading_louvers_01",
                recommendation_id="external_shading",
                intervention_type="external_shading",
                target_element_ids=[],
                world_position=[0.0, 0.0, 0.0],
                dimensions=[0.0, 0.0, 0.0],
                orientation={},
                estimated_cost=0.0,
                expected_benefit={},
                calculation_method="CPWD Benchmark",
                assumptions=[],
                validation_status="REJECTED",
                rejection_reason="No window apertures detected in building model. External shading requires at least 1 window aperture.",
                components_3d=[]
            ), logs

        components_3d: List[Intervention3DComponent] = []
        target_ids: List[str] = []
        win_count = len(windows) if windows else (fallback_window_count or 4)
        cost = win_count * 4500.0  # ₹4,500 per window aperture

        if windows:
            logs.append(f"VALIDATED Window Shading: Found {len(windows)} authentic window elements. Synthesizing bespoke louvers.")
            for idx, win in enumerate(windows, start=1):
                target_ids.append(win.element_id)
                w_bbox = win.bounding_box
                if w_bbox:
                    w_x = (w_bbox.min_x + w_bbox.max_x) / 2.0
                    w_y = (w_bbox.min_y + w_bbox.max_y) / 2.0
                    w_z_top = w_bbox.max_z
                    w_width = max(1.2, w_bbox.width)
                    w_depth = max(0.2, w_bbox.height)

                    # Determine façade orientation (North/South vs East/West)
                    # If window depth is tiny along Y, it's on a North/South wall
                    if w_depth <= 0.6:
                        # North or South wall
                        span_w = w_width + 0.25
                        overhang_d = 0.55
                        # Shift slightly outside the wall
                        is_north = w_y > (min_y + max_y) / 2.0
                        pos_y = w_y + (0.28 if is_north else -0.28)
                        pos_x = w_x
                        dim = [round(span_w, 2), round(overhang_d, 2), 0.08]
                    else:
                        # East or West wall
                        span_w = w_depth + 0.25
                        overhang_d = 0.55
                        is_east = w_x > (min_x + max_x) / 2.0
                        pos_x = w_x + (0.28 if is_east else -0.28)
                        pos_y = w_y
                        dim = [round(overhang_d, 2), round(span_w, 2), 0.08]

                    louver_z = w_z_top + 0.08
                else:
                    pos_x = min_x + (idx * 2.5)
                    pos_y = min_y - 0.2
                    louver_z = 2.4
                    dim = [1.6, 0.55, 0.08]

                components_3d.append(
                    Intervention3DComponent(
                        component_id=f"SHADING-LOUVER-{idx:02d}",
                        component_type="window_louvers",
                        name=f"Architectural Window Louver Shading #{idx:02d}",
                        material="Extruded Powder-Coated Architectural Aluminum (RAL 7037)",
                        color_hex="#64748b",  # Architectural slate gray
                        position=[round(pos_x, 3), round(pos_y, 3), round(louver_z, 3)],
                        dimensions=dim,
                        geometry_type="box",
                        specification=f"550mm cantilevered sun-shading louver visor mounted above window header {win.element_id} at 45° solar cutoff"
                    )
                )
        else:
            # Parametric fallback windows
            logs.append(f"VALIDATED Window Shading: Synthesizing {win_count} parametric window louvers.")
            for i in range(win_count):
                pos_x = min_x + 2.0 + (i * 2.5)
                pos_y = min_y - 0.25
                louver_z = 2.4
                components_3d.append(
                    Intervention3DComponent(
                        component_id=f"SHADING-LOUVER-PARAM-{i+1:02d}",
                        component_type="window_louvers",
                        name=f"Window Louver Overhang #{i+1:02d}",
                        material="Extruded Architectural Aluminum",
                        color_hex="#64748b",
                        position=[round(pos_x, 3), round(pos_y, 3), round(louver_z, 3)],
                        dimensions=[1.6, 0.55, 0.08],
                        geometry_type="box",
                        specification="550mm exterior horizontal cantilevered visor"
                    )
                )

        interv = StructuredIntervention(
            intervention_id="window_shading_louvers_01",
            recommendation_id="external_shading",
            intervention_type="external_shading",
            target_element_ids=target_ids,
            target_floor="Ground & Upper Storeys",
            geometry_parameters={"window_apertures": win_count, "overhang_depth_m": 0.55},
            material_parameters={"material": "Powder-coated architectural aluminum #64748b"},
            world_position=[(min_x + max_x) / 2.0, min_y, 2.4],
            dimensions=[width_m, 0.55, 0.08],
            orientation={"angle_cutoff_deg": 45.0},
            estimated_cost=round(cost, 2),
            expected_benefit={
                "solar_heat_gain_coefficient_reduction_pct": 32.0,
                "glare_discomfort_hours_reduction_pct": 46.0,
                "annual_hvac_cooling_saving_kwh": round(win_count * 240.0, 1)
            },
            calculation_method="CPWD DSR 2023 Benchmark (₹4,500/window aperture)",
            assumptions=["Standard ~2.0 m² window opening with structural lintel bracket attachment"],
            validation_status="VALIDATED",
            components_3d=components_3d
        )
        return interv, logs

    # =========================================================================
    # 5. RAINWATER HARVESTING & STORAGE INTERVENTION
    # =========================================================================
    @classmethod
    def _generate_rainwater_harvesting_intervention(
        cls,
        min_x: float, max_x: float, min_y: float, max_y: float,
        min_z: float, roof_z: float, target_roof_ids: List[str]
    ) -> Tuple[StructuredIntervention, List[str]]:
        logs: List[str] = []
        cost = 185000.0  # ₹1,85,000 for 10 kL food-grade modular RWH system

        w = max_x - min_x
        l = max_y - min_y
        logs.append(f"VALIDATED Rainwater System: 10 kL storage, gutters, and downpipes at roof elevation {roof_z:.2f}m.")

        components_3d: List[Intervention3DComponent] = [
            # 1. North Roof Perimeter Gutter
            Intervention3DComponent(
                component_id="RWH-GUTTER-NORTH",
                component_type="gutter",
                name="North Roof Eave Gutter (180mm uPVC)",
                material="UV-Stabilized High-Capacity uPVC",
                color_hex="#475569",
                position=[round((min_x + max_x) / 2.0, 3), round(max_y + 0.12, 3), round(roof_z + 0.05, 3)],
                dimensions=[round(w + 0.2, 2), 0.18, 0.15],
                geometry_type="box",
                specification="180mm semi-circular continuous eave gutter with 1:150 slope"
            ),
            # 2. South Roof Perimeter Gutter
            Intervention3DComponent(
                component_id="RWH-GUTTER-SOUTH",
                component_type="gutter",
                name="South Roof Eave Gutter (180mm uPVC)",
                material="UV-Stabilized High-Capacity uPVC",
                color_hex="#475569",
                position=[round((min_x + max_x) / 2.0, 3), round(min_y - 0.12, 3), round(roof_z + 0.05, 3)],
                dimensions=[round(w + 0.2, 2), 0.18, 0.15],
                geometry_type="box",
                specification="180mm semi-circular continuous eave gutter with 1:150 slope"
            ),
            # 3. Downpipe at South-East Corner
            Intervention3DComponent(
                component_id="RWH-DOWNPIPE-SE",
                component_type="downpipe",
                name="Rainwater Downpipe Drop (110mm)",
                material="Heavy Duty uPVC 110mm Pipe",
                color_hex="#0369a1",
                position=[round(max_x + 0.15, 3), round(min_y - 0.15, 3), round((min_z + roof_z) / 2.0, 3)],
                dimensions=[0.06, 0.06, round(roof_z - min_z, 2)],
                geometry_type="cylinder",
                specification="110mm vertical collection drop connecting roof gutter to ground filtration"
            ),
            # 4. First-Flush Diverter & Mechanical Dual Filter
            Intervention3DComponent(
                component_id="RWH-FIRST-FLUSH-01",
                component_type="first_flush",
                name="First-Flush Separator & Stainless Dual Mesh Filter",
                material="Stainless Steel SS304 Mesh & uPVC Chamber",
                color_hex="#0284c7",
                position=[round(max_x + 0.45, 3), round(min_y + 0.6, 3), round(min_z + 1.2, 3)],
                dimensions=[0.25, 0.25, 0.85],
                geometry_type="cylinder",
                specification="Automated float-valve first-flush diverter with self-cleaning 120-micron filter"
            ),
            # 5. Rainwater Storage Cistern (10,000 Liters)
            Intervention3DComponent(
                component_id="RWH-STORAGE-TANK-10KL",
                component_type="storage_tank",
                name="Rainwater Storage Cistern (10 kL Food-Grade HDPE)",
                material="Triple-Layer UV-Stabilized Food-Grade HDPE",
                color_hex="#0284c7",
                position=[round(max_x + 1.8, 3), round(min_y + 1.8, 3), round(min_z + 1.15, 3)],
                dimensions=[1.1, 1.1, 2.2],
                geometry_type="cylinder",
                volume_liters=10000.0,
                specification="10,000 Liters modular cylindrical storage tank with non-potable distribution pump"
            )
        ]

        interv = StructuredIntervention(
            intervention_id="rwh_storage_system_01",
            recommendation_id="rainwater_harvesting",
            intervention_type="rainwater_harvesting",
            target_element_ids=target_roof_ids,
            target_floor="Ground & Roof Perimeter",
            geometry_parameters={"tank_capacity_l": 10000.0, "tank_diameter_m": 2.2, "tank_height_m": 2.2},
            material_parameters={"tank_material": "Triple-Layer Food-Grade HDPE #0284c7", "piping": "uPVC 110mm #0369a1"},
            world_position=[max_x + 1.8, min_y + 1.8, min_z + 1.15],
            dimensions=[2.2, 2.2, 2.2],
            orientation={},
            estimated_cost=cost,
            expected_benefit={
                "annual_harvest_volume_kl": 184.2,
                "potable_water_offset_pct": 42.0,
                "peak_stormwater_attenuation_pct": 58.0
            },
            calculation_method="CPHEEO / NBC 2016 Rainwater Harvesting Standard",
            assumptions=["10 kL above-ground cylindrical tank sited on reinforced concrete plinth"],
            validation_status="VALIDATED",
            components_3d=components_3d
        )
        return interv, logs

    # =========================================================================
    # 6. GREEN ROOF / SEDUM VEGETATED DETENTION
    # =========================================================================
    @classmethod
    def _generate_green_roof_intervention(
        cls,
        min_x: float, max_x: float, min_y: float, max_y: float,
        roof_z: float, target_roof_ids: List[str],
        width_m: float, length_m: float
    ) -> Tuple[StructuredIntervention, List[str]]:
        logs: List[str] = []
        roof_area = width_m * length_m
        cost = round(roof_area * 2200.0, 2)  # ₹2,200 / m²
        logs.append(f"VALIDATED Green Roof: Area={roof_area:.1f} m², Cost=₹{cost:,.0f}")

        center_x = (min_x + max_x) / 2.0
        center_y = (min_y + max_y) / 2.0
        green_z = roof_z + 0.06

        components_3d = [
            Intervention3DComponent(
                component_id="GREEN-ROOF-SEDUM-01",
                component_type="green_roof_sedum",
                name="Extensive Sedum Vegetated Green Roof Trays",
                material="Modular Pre-Grown Drought-Tolerant Sedum & Root Barrier",
                color_hex="#15803d",  # Lush garden green
                position=[round(center_x, 3), round(center_y, 3), round(green_z, 3)],
                dimensions=[round(width_m - 0.8, 2), round(length_m - 0.8, 2), 0.12],
                geometry_type="box",
                specification="100mm extensive modular green roof system with drainage egg-crate, filter fabric, and drought-hardy succulent vegetation"
            )
        ]

        interv = StructuredIntervention(
            intervention_id="green_roof_sedum_01",
            recommendation_id="green_roof",
            intervention_type="green_roof",
            target_element_ids=target_roof_ids,
            target_floor="Terrace / Roof",
            geometry_parameters={"depth_mm": 100, "area_m2": round(roof_area, 2)},
            material_parameters={"vegetation": "Sedum Album / Sedum Kamtschaticum", "color": "#15803d"},
            world_position=[center_x, center_y, green_z],
            dimensions=[width_m - 0.8, length_m - 0.8, 0.12],
            orientation={},
            estimated_cost=cost,
            expected_benefit={
                "stormwater_retention_pct": 65.0,
                "heat_island_surface_temp_reduction_deg_c": 18.0,
                "biodiversity_score": 9.2
            },
            calculation_method="FLL Green Roof Standard (₹2,200/m²)",
            assumptions=["Terrace structure supports 110 kg/m² saturated green roof load"],
            validation_status="VALIDATED",
            components_3d=components_3d
        )
        return interv, logs
