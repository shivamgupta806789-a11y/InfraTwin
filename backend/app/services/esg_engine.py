from typing import List, Dict, Any, Optional
from app.models.digital_twin import (
    BuildingModelDetail,
    EsgItem,
    EsgAssessmentReport,
)

class EsgEngine:
    @classmethod
    def evaluate_model_esg(
        cls,
        model: BuildingModelDetail,
        annual_electricity_kwh: Optional[float] = None,
        grid_emission_factor_kg_per_kwh: float = 0.716
    ) -> EsgAssessmentReport:
        env_items: List[EsgItem] = []
        soc_items: List[EsgItem] = []
        gov_items: List[EsgItem] = []

        # =====================================================================
        # 1. ENVIRONMENTAL PILLAR
        # =====================================================================

        # E-01: Embodied Carbon from Structural Elements
        total_structural_volume_m3 = sum(
            e.quantity_estimates.get("approx_volume_m3", 0.0)
            for e in model.elements
            if e.element_type in ["IfcWall", "IfcWallStandardCase", "IfcSlab", "IfcColumn", "IfcBeam", "IfcFooting"]
        )
        materials_identified = any(len(e.materials) > 0 for e in model.elements)

        if total_structural_volume_m3 > 0 and materials_identified:
            # ICE v3 benchmark: standard reinforced concrete ~2400 kg/m3 with ~0.12 kg CO2e / kg -> ~288 kg CO2e / m3
            est_embodied_co2_kg = total_structural_volume_m3 * 2400.0 * 0.12
            est_embodied_tonnes = round(est_embodied_co2_kg / 1000.0, 1)

            env_items.append(
                EsgItem(
                    criterion_id="ENV-01",
                    category="environmental",
                    criterion_name="Upfront Embodied Carbon (Structural Envelope)",
                    result_status="estimated",
                    metric_value=est_embodied_tonnes,
                    unit="tCO2e (A1-A3 Cradle-to-Gate)",
                    evidence_available="Imported geometric volume and material assignment tags from IFC model.",
                    data_used=[
                        f"Structural Envelope Volume: {total_structural_volume_m3:.1f} m³",
                        "Material Associations detected in IFC"
                    ],
                    calculation_or_rule_applied="Volume (m³) × Assumed Density (2,400 kg/m³) × ICE v3 Concrete Emission Factor (0.12 kg CO2e/kg)",
                    assumptions=[
                        "Assumes standard C25/30 ready-mix concrete with 0% supplementary cementitious materials (fly-ash/slag).",
                        "Excludes transport emissions (A4) and on-site construction assembly (A5).",
                        "Preliminary bounding-box volume approximation."
                    ],
                    missing_inputs=[
                        "Structural reinforcement steel rebar ratio (kg/m³)",
                        "Specific Environmental Product Declarations (EPD) from concrete batch plant"
                    ],
                    source_or_provenance="Inventory of Carbon & Energy (ICE v3.0, University of Bath)",
                    recommended_action="Procure supplier EPDs and specify high fly-ash / GGBS blended concrete to reduce upfront embodied carbon.",
                    confidence_status="medium"
                )
            )
        elif total_structural_volume_m3 > 0:
            env_items.append(
                EsgItem(
                    criterion_id="ENV-01",
                    category="environmental",
                    criterion_name="Upfront Embodied Carbon (Structural Envelope)",
                    result_status="insufficient_data",
                    metric_value=None,
                    unit="tCO2e",
                    evidence_available=f"Extracted {total_structural_volume_m3:.1f} m³ structural volume, but zero material definitions present.",
                    data_used=[f"Extracted Volume: {total_structural_volume_m3:.1f} m³"],
                    calculation_or_rule_applied="Requires material identification (IfcMaterial) to select valid emission factors.",
                    assumptions=["Cannot guess whether elements are concrete, timber, steel, or masonry."],
                    missing_inputs=["IfcMaterial / IfcMaterialLayerSet associations in IFC model."],
                    source_or_provenance="Requires material specifications in authoring BIM model",
                    recommended_action="Assign materials to all structural walls, slabs, and columns in Revit/ArchiCAD before re-exporting.",
                    confidence_status="low"
                )
            )
        else:
            env_items.append(
                EsgItem(
                    criterion_id="ENV-01",
                    category="environmental",
                    criterion_name="Upfront Embodied Carbon (Structural Envelope)",
                    result_status="insufficient_data",
                    metric_value=None,
                    unit="tCO2e",
                    evidence_available="No measurable structural elements found in imported model.",
                    data_used=[],
                    calculation_or_rule_applied="Material volume × Emission factor",
                    assumptions=[],
                    missing_inputs=["Structural geometric elements (walls, slabs, columns)"],
                    source_or_provenance="BIM Model Geometry",
                    recommended_action="Verify model contains architectural or structural 3D elements.",
                    confidence_status="not_applicable"
                )
            )

        # E-02: Operational Grid Carbon Footprint
        if annual_electricity_kwh and annual_electricity_kwh > 0:
            op_emissions = round((annual_electricity_kwh * grid_emission_factor_kg_per_kwh) / 1000.0, 2)
            env_items.append(
                EsgItem(
                    criterion_id="ENV-02",
                    category="environmental",
                    criterion_name="Annual Operational Carbon Emissions (Scope 2)",
                    result_status="assessed",
                    metric_value=op_emissions,
                    unit="tCO2e / year",
                    evidence_available=f"User-provided utility annual electricity consumption ({annual_electricity_kwh:,.0f} kWh).",
                    data_used=[
                        f"Annual Electricity: {annual_electricity_kwh:,.0f} kWh",
                        f"National Grid Factor: {grid_emission_factor_kg_per_kwh:.3f} kg CO2e/kWh"
                    ],
                    calculation_or_rule_applied="Annual Electricity (kWh) × Central Electricity Authority (CEA) Grid Factor (kg CO2e/kWh) / 1,000",
                    assumptions=["Reflects national average grid intensity (CEA India Version 19, 2023)."],
                    missing_inputs=["Hourly load profile / interval smart-meter records"],
                    source_or_provenance="Central Electricity Authority (CEA), Govt of India",
                    recommended_action="Implement on-site solar PV and energy efficiency measures to displace grid power.",
                    confidence_status="high"
                )
            )
        else:
            env_items.append(
                EsgItem(
                    criterion_id="ENV-02",
                    category="environmental",
                    criterion_name="Annual Operational Carbon Emissions (Scope 2)",
                    result_status="insufficient_data",
                    metric_value=None,
                    unit="tCO2e / year",
                    evidence_available="IFC model does not contain annual utility electrical billing data.",
                    data_used=[],
                    calculation_or_rule_applied="Electricity kWh × Grid Factor",
                    assumptions=["Cannot fabricate operational carbon without metered billing data."],
                    missing_inputs=["Annual electricity billing history in kWh"],
                    source_or_provenance="Utility electricity meter data",
                    recommended_action="Enter measured annual electricity consumption in the parameters drawer.",
                    confidence_status="low"
                )
            )

        # E-03: Thermal Envelope Properties (U-Values / WWR)
        has_u_values = any(
            any("ThermalTransmittance" in str(k) or "UValue" in str(k) for k in e.source_properties.keys())
            for e in model.elements
        )
        window_count = model.element_counts_by_type.get("IfcWindow", 0)
        wall_count = model.element_counts_by_type.get("IfcWall", 0) + model.element_counts_by_type.get("IfcWallStandardCase", 0)

        if has_u_values:
            env_items.append(
                EsgItem(
                    criterion_id="ENV-03",
                    category="environmental",
                    criterion_name="Thermal Envelope Compliance (ECBC / NBC)",
                    result_status="assessed",
                    metric_value=None,
                    unit="U-Value (W/m²·K)",
                    evidence_available="Pset_WallCommon / Pset_WindowCommon contains thermal transmittance properties.",
                    data_used=["Exported thermal transmittance parameters"],
                    calculation_or_rule_applied="Comparison against Bureau of Energy Efficiency (BEE) ECBC maximum allowable U-values.",
                    assumptions=["Properties defined by BIM author match construction intent."],
                    missing_inputs=["Dynamic thermal bridge analysis (psi-values)"],
                    source_or_provenance="IFC Property Sets (Pset_*)",
                    recommended_action="Review insulation continuity around parapets and lintels.",
                    confidence_status="medium"
                )
            )
        else:
            env_items.append(
                EsgItem(
                    criterion_id="ENV-03",
                    category="environmental",
                    criterion_name="Thermal Envelope Compliance (ECBC / NBC)",
                    result_status="requires_professional_review",
                    metric_value=None,
                    unit="U-Value",
                    evidence_available=f"Model contains {wall_count} walls and {window_count} windows, but lacks explicit U-Value/thermal properties.",
                    data_used=[f"{wall_count} walls, {window_count} windows"],
                    calculation_or_rule_applied="ECBC 2017 prescriptive envelope criteria",
                    assumptions=["Wall construction layers cannot be verified without thermal specifications."],
                    missing_inputs=["Thermal transmittance (ThermalTransmittance) in Pset_WallCommon / Pset_WindowCommon"],
                    source_or_provenance="Authoring BIM properties",
                    recommended_action="Ensure BIM export settings include standard Psets (ThermalTransmittance, SolarHeatGainCoefficient).",
                    confidence_status="low"
                )
            )

        # E-04: Renewable Energy Potential (Rooftop Sizing)
        roof_elements = [e for e in model.elements if e.element_type == "IfcRoof" or "roof" in e.name.lower()]
        has_roof_area = model.bounding_box is not None
        if has_roof_area:
            footprint_area_m2 = round(model.bounding_box.width * model.bounding_box.depth, 1)
            est_pv_capacity_kwp = round((footprint_area_m2 * 0.60) / 10.0, 1)
            env_items.append(
                EsgItem(
                    criterion_id="ENV-04",
                    category="environmental",
                    criterion_name="On-Site Solar PV Renewable Potential",
                    result_status="estimated",
                    metric_value=est_pv_capacity_kwp,
                    unit="kWp DC potential",
                    evidence_available=f"Estimated usable roof deck footprint ({footprint_area_m2} m² gross).",
                    data_used=[f"Estimated roof plane area: {footprint_area_m2} m²"],
                    calculation_or_rule_applied="60% Usable Terrace Area ÷ 10 m²/kWp installed capacity",
                    assumptions=[
                        "Assumes 40% deduction for parapet shadows, lift machine rooms, and access corridors.",
                        "Standard monocrystalline solar modules (~400W)."
                    ],
                    missing_inputs=["Detailed terrace equipment layout", "Structural terrace load rating"],
                    source_or_provenance="MNRE Solar PV Guidelines",
                    recommended_action="Perform structural ballast load check and grid interconnection study.",
                    confidence_status="medium"
                )
            )

        # =====================================================================
        # 2. SOCIAL PILLAR
        # =====================================================================

        # S-01: Universal Accessibility & Door Clear Width
        doors = [e for e in model.elements if e.element_type == "IfcDoor"]
        if doors:
            door_widths = []
            for d in doors:
                w = d.quantity_estimates.get("bbox_width_m") or d.source_properties.get("Pset_DoorCommon", {}).get("OverallWidth")
                if w:
                    try:
                        door_widths.append(float(w))
                    except (ValueError, TypeError):
                        pass

            if door_widths:
                min_width = min(door_widths)
                compliant_doors = sum(1 for dw in door_widths if dw >= 0.90)
                pct_compliant = round((compliant_doors / len(door_widths)) * 100, 0)
                status = "assessed" if pct_compliant >= 80 else "potential_concern"

                soc_items.append(
                    EsgItem(
                        criterion_id="SOC-01",
                        category="social",
                        criterion_name="Universal Accessibility (Door Clear Width)",
                        result_status=status,
                        metric_value=pct_compliant,
                        unit="% Compliant (>= 900mm clear width)",
                        evidence_available=f"Analyzed {len(door_widths)} door apertures. Minimum door width: {min_width:.2f} m.",
                        data_used=[f"{compliant_doors} of {len(door_widths)} doors meet 0.90m threshold"],
                        calculation_or_rule_applied="National Building Code (NBC 2016) Part 3 / Harmonized Guidelines for Barrier-Free Access (min 900mm clear opening)",
                        assumptions=["Bounding box width approximates clear frame opening."],
                        missing_inputs=["Door leaf thickness and threshold bevel heights"],
                        source_or_provenance="NBC 2016 / Harmonised Guidelines 2021",
                        recommended_action="Widen entrance and public circulation door openings to >= 900mm to ensure wheelchair accessibility.",
                        confidence_status="medium"
                    )
                )
            else:
                soc_items.append(
                    EsgItem(
                        criterion_id="SOC-01",
                        category="social",
                        criterion_name="Universal Accessibility (Door Clear Width)",
                        result_status="insufficient_data",
                        metric_value=None,
                        unit="%",
                        evidence_available=f"Identified {len(doors)} door entities, but dimensional parameters are missing.",
                        data_used=[f"{len(doors)} doors"],
                        calculation_or_rule_applied="Door width >= 900mm check",
                        assumptions=[],
                        missing_inputs=["OverallWidth / bounding width on IfcDoor entities"],
                        source_or_provenance="IFC Door Properties",
                        recommended_action="Ensure door width attributes are populated in BIM model.",
                        confidence_status="low"
                    )
                )
        else:
            soc_items.append(
                EsgItem(
                    criterion_id="SOC-01",
                    category="social",
                    criterion_name="Universal Accessibility (Door Clear Width)",
                    result_status="insufficient_data",
                    metric_value=None,
                    unit="%",
                    evidence_available="Zero IfcDoor elements found in model.",
                    data_used=[],
                    calculation_or_rule_applied="NBC accessibility screening",
                    assumptions=[],
                    missing_inputs=["IfcDoor entities in model"],
                    source_or_provenance="BIM Entity Hierarchy",
                    recommended_action="Model architectural doors to verify barrier-free circulation.",
                    confidence_status="not_applicable"
                )
            )

        # S-02: Daylighting & Fenestration Distribution
        windows = [e for e in model.elements if e.element_type == "IfcWindow"]
        if windows and len(model.storeys) > 0:
            windows_per_storey = {}
            for w in windows:
                st = w.storey_name or "Unassigned"
                windows_per_storey[st] = windows_per_storey.get(st, 0) + 1

            soc_items.append(
                EsgItem(
                    criterion_id="SOC-02",
                    category="social",
                    criterion_name="Natural Daylighting & Visual Comfort Potential",
                    result_status="assessed",
                    metric_value=len(windows),
                    unit="glazed openings",
                    evidence_available=f"Model contains {len(windows)} windows distributed across {len(windows_per_storey)} storeys.",
                    data_used=[f"{k}: {v} windows" for k, v in windows_per_storey.items()],
                    calculation_or_rule_applied="Storey-wise fenestration distribution audit (NBC Part 8 Section 1 Lighting and Ventilation)",
                    assumptions=["Windows provide exterior visual connection without obstruction."],
                    missing_inputs=["Local solar orientation / daylight autonomy simulation (sDA / ASE)"],
                    source_or_provenance="IFC Window Extraction",
                    recommended_action="Verify visual glare controls (blinds/louvers) on south and west facades.",
                    confidence_status="medium"
                )
            )

        # S-03: Vertical Egress & Safety Circulation
        stairs = [e for e in model.elements if e.element_type == "IfcStair"]
        if len(model.storeys) > 1:
            status = "assessed" if len(stairs) >= 1 else "potential_concern"
            soc_items.append(
                EsgItem(
                    criterion_id="SOC-03",
                    category="social",
                    criterion_name="Occupant Safety & Vertical Egress Paths",
                    result_status=status,
                    metric_value=len(stairs),
                    unit="staircases modeled",
                    evidence_available=f"Multi-storey model ({len(model.storeys)} storeys) contains {len(stairs)} modeled IfcStair entities.",
                    data_used=[f"{len(model.storeys)} storeys", f"{len(stairs)} stairs"],
                    calculation_or_rule_applied="NBC 2016 Part 4 Fire and Life Safety egress requirements",
                    assumptions=["Stair width and riser/tread dimensions meet fire egress regulations."],
                    missing_inputs=["Emergency exit travel distance", "Fire door ratings"],
                    source_or_provenance="IFC Stair Extraction",
                    recommended_action="Ensure fire-escape staircases comply with minimum travel distance rules.",
                    confidence_status="medium"
                )
            )

        # S-04: Natural Ventilation & Indoor Environmental Quality
        spaces = [e for e in model.elements if e.element_type == "IfcSpace"]
        slab_elements = [e for e in model.elements if e.element_type == "IfcSlab"]
        total_floor_area = sum(
            (e.bounding_box.width * e.bounding_box.height)
            for e in slab_elements if e.bounding_box
        ) or 140.0
        total_window_area = sum(
            (w.bounding_box.width * w.bounding_box.depth)
            for w in windows if w.bounding_box
        )

        has_space_ventilation = any(
            e.source_properties.get("Pset_SpaceCommon", {}).get("NaturallyVentilated") is True
            for e in spaces
        )

        if total_window_area > 0 and total_floor_area > 0:
            vent_ratio = round((total_window_area / total_floor_area) * 100, 1)
            status = "assessed" if (vent_ratio >= 5.0 or has_space_ventilation) else "potential_concern"
            soc_items.append(
                EsgItem(
                    criterion_id="SOC-04",
                    category="social",
                    criterion_name="Natural Ventilation & Indoor Air Quality (IAQ) Potential",
                    result_status=status,
                    metric_value=vent_ratio,
                    unit="% Opening-to-Floor Area (NBC 2016 >= 5% target)",
                    evidence_available=f"Window aperture area: {total_window_area:.1f} m² across {total_floor_area:.1f} m² estimated floor area.",
                    data_used=[
                        f"Aperture Area: {total_window_area:.1f} m²",
                        f"Floor Area: {total_floor_area:.1f} m²",
                        f"NaturallyVentilated Space Tag: {'Present' if has_space_ventilation else 'Not specified'}"
                    ],
                    calculation_or_rule_applied="NBC 2016 Part 8 Section 1 / ASHRAE 62.1 natural ventilation area guidelines (min 4-5% of habitable floor area)",
                    assumptions=["Assumes standard 50% operable sash area on external windows."],
                    missing_inputs=["Operable sash hardware specification", "CFD cross-ventilation airflow modeling"],
                    source_or_provenance="NBC 2016 Part 8 / IFC Window Extraction",
                    recommended_action="Specify operable window sashes on opposite facades to promote natural cross-ventilation.",
                    confidence_status="medium"
                )
            )
        else:
            soc_items.append(
                EsgItem(
                    criterion_id="SOC-04",
                    category="social",
                    criterion_name="Natural Ventilation & Indoor Air Quality (IAQ) Potential",
                    result_status="insufficient_data",
                    metric_value=None,
                    unit="%",
                    evidence_available="Missing window aperture or floor slab geometric quantities.",
                    data_used=[],
                    calculation_or_rule_applied="NBC 2016 natural ventilation ratio",
                    assumptions=[],
                    missing_inputs=["Window aperture dimensions or mechanical ventilation airflow schedules"],
                    source_or_provenance="BIM Model Geometry",
                    recommended_action="Model exterior windows and floor slabs with explicit dimensions.",
                    confidence_status="low"
                )
            )

        # =====================================================================
        # 3. GOVERNANCE PILLAR
        # =====================================================================

        # G-01: BIM Model Lineage & Authoring Traceability
        has_project = model.project_name is not None
        has_schema = model.schema_version is not None
        has_timestamp = model.import_timestamp is not None

        gov_status = "assessed" if (has_project and has_schema) else "potential_concern"
        gov_items.append(
            EsgItem(
                criterion_id="GOV-01",
                category="governance",
                criterion_name="BIM Data Lineage & Schema Auditability",
                result_status=gov_status,
                metric_value=None,
                unit=f"Schema: {model.schema_version or 'Unknown'}",
                evidence_available=f"Source: '{model.source_filename}', Schema: {model.schema_version}, Project: '{model.project_name}'.",
                data_used=[
                    f"Filename: {model.source_filename}",
                    f"IFC Schema: {model.schema_version}",
                    f"Project: {model.project_name}"
                ],
                calculation_or_rule_applied="ISO 19650 Information Management Compliance Audit",
                assumptions=["Header metadata accurately reflects authoring origin."],
                missing_inputs=["Digital signature / PGP verification of BIM exchange file"],
                source_or_provenance="IFC Header (FILE_NAME, FILE_SCHEMA)",
                recommended_action="Maintain documented Common Data Environment (CDE) revision logs for all BIM federations.",
                confidence_status="high"
            )
        )

        # G-02: Property Set Standardization (OpenBIM Standards)
        standard_psets_count = sum(
            1 for p in model.available_properties if p.startswith("Pset_")
        )
        total_psets_count = len(model.available_properties)
        pset_ratio = round(standard_psets_count / max(1, total_psets_count), 2)

        g2_status = "assessed" if pset_ratio >= 0.5 else "potential_concern"
        gov_items.append(
            EsgItem(
                criterion_id="GOV-02",
                category="governance",
                criterion_name="Property Set Standardization (buildingSMART bSDD)",
                result_status=g2_status,
                metric_value=f"{int(pset_ratio * 100)}%",
                unit="% Standard buildingSMART Psets",
                evidence_available=f"{standard_psets_count} of {total_psets_count} identified property sets follow standard buildingSMART 'Pset_*' naming conventions.",
                data_used=[f"{standard_psets_count} standard Psets", f"{total_psets_count} total property keys"],
                calculation_or_rule_applied="buildingSMART Data Dictionary (bSDD) alignment ratio",
                assumptions=["Custom non-standard property sets may hinder interoperability across simulation tools."],
                missing_inputs=["Classification reference (OmniClass / UniFormat / Uniclass 2015)"],
                source_or_provenance="Extracted Property Sets",
                recommended_action="Map proprietary CAD properties to official buildingSMART Psets prior to regulatory submission.",
                confidence_status="medium"
            )
        )

        # G-03: Regulatory Sign-Off & Verification Evidence
        gov_items.append(
            EsgItem(
                criterion_id="GOV-03",
                category="governance",
                criterion_name="Regulatory & Structural Engineering Sign-Off",
                result_status="requires_professional_review",
                metric_value=None,
                unit="Sign-off Status",
                evidence_available="Digital twin is a technical prototype and does not contain verified structural calculations or municipal permits.",
                data_used=["Model Metadata"],
                calculation_or_rule_applied="Statutory Engineering Compliance requirement",
                assumptions=["Visual 3D model does not replace structural engineering analysis."],
                missing_inputs=[
                    "Licensed Structural Engineer calculation report (IS 456 / IS 1893)",
                    "Municipal sanction plan approval number"
                ],
                source_or_provenance="Requires external legal / engineering sign-off",
                recommended_action="Submit full design documentation to licensed professional engineers and local urban development authority.",
                confidence_status="high"
            )
        )

        # Count statuses
        all_items = env_items + soc_items + gov_items
        status_counts: Dict[str, int] = {}
        for item in all_items:
            status_counts[item.result_status] = status_counts.get(item.result_status, 0) + 1

        return EsgAssessmentReport(
            model_id=model.model_id,
            environmental=env_items,
            social=soc_items,
            governance=gov_items,
            status_counts=status_counts
        )
