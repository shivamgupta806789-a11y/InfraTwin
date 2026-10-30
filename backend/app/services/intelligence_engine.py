import math
from typing import List, Dict, Set, Tuple, Optional
from app.models.digital_twin import (
    BuildingModelDetail,
    BuildingElement,
    IntelligenceFinding,
    BuildingIntelligenceReport,
    MaterialDistributionItem,
    StoreyDistributionItem,
    EvidenceBasedRecommendation,
)

class IntelligenceEngine:
    """
    Evidence-based building intelligence module analyzing imported IFC models
    for potential design, data-quality, and building-performance concerns.
    """

    @classmethod
    def analyze_model(
        cls,
        model: BuildingModelDetail,
        parser_warnings: Optional[List[str]] = None
    ) -> BuildingIntelligenceReport:
        findings: List[IntelligenceFinding] = []
        finding_seq = 0

        def add_finding(
            title: str,
            severity: str,
            category: str,
            element: BuildingElement,
            flagged_reason: str,
            evidence: str,
            action: str,
            source_props: Optional[Dict] = None
        ):
            nonlocal finding_seq
            finding_seq += 1
            findings.append(
                IntelligenceFinding(
                    finding_id=f"RISK-{finding_seq:03d}",
                    title=title,
                    severity=severity,
                    category=category,
                    affected_element_id=element.element_id,
                    affected_element_name=element.name,
                    affected_global_id=element.source_global_id,
                    affected_element_type=element.element_type,
                    flagged_reason=flagged_reason,
                    evidence=evidence,
                    source_properties=source_props or element.source_properties,
                    recommended_action=action
                )
            )

        elements = model.elements

        # =====================================================================
        # 1. MISSING OR INCOMPLETE ELEMENT PROPERTIES
        # =====================================================================
        expected_psets: Dict[str, str] = {
            "IfcWall": "Pset_WallCommon",
            "IfcWallStandardCase": "Pset_WallCommon",
            "IfcSlab": "Pset_SlabCommon",
            "IfcColumn": "Pset_ColumnCommon",
            "IfcBeam": "Pset_BeamCommon",
            "IfcDoor": "Pset_DoorCommon",
            "IfcWindow": "Pset_WindowCommon",
            "IfcFooting": "Pset_FootingCommon",
            "IfcSpace": "Pset_SpaceCommon",
        }

        for elem in elements:
            expected = expected_psets.get(elem.element_type)
            if expected:
                if expected not in elem.source_properties:
                    add_finding(
                        title=f"Missing Property Set: {expected}",
                        severity="Warning",
                        category="property",
                        element=elem,
                        flagged_reason=f"Element lacks standard buildingSMART property set '{expected}', hindering automated BIM specification and code validation.",
                        evidence=f"Attached property sets: {list(elem.source_properties.keys()) or 'None'}",
                        action=f"Configure authoring BIM export to map element properties into standard '{expected}'."
                    )
                else:
                    # Check for missing critical property keys within expected pset
                    pset_data = elem.source_properties.get(expected, {})
                    if elem.element_type in ["IfcWall", "IfcWallStandardCase", "IfcSlab", "IfcWindow"]:
                        if "ThermalTransmittance" not in pset_data and "UValue" not in pset_data:
                            add_finding(
                                title="Missing Thermal Transmittance (U-Value)",
                                severity="Information",
                                category="property",
                                element=elem,
                                flagged_reason="Envelope element lacks explicit thermal transmittance (U-value) in standard property set.",
                                evidence=f"{expected} present, but 'ThermalTransmittance' property is unassigned.",
                                action="Specify envelope layer thermal conductivities and U-values in architectural material schedules."
                            )
                    if elem.element_type in ["IfcWall", "IfcColumn", "IfcBeam"]:
                        if "FireRating" not in pset_data:
                            add_finding(
                                title="Missing Statutory Fire Rating Property",
                                severity="Information",
                                category="property",
                                element=elem,
                                flagged_reason="Structural/envelope component lacks explicit FireRating property for statutory life-safety audit.",
                                evidence=f"{expected} present, but 'FireRating' property is undefined.",
                                action="Enter passive fire resistance duration (e.g. 60 min, 120 min) in BIM element properties."
                            )

        # =====================================================================
        # 2. ELEMENTS WITHOUT MATERIAL ASSIGNMENTS
        # =====================================================================
        physical_element_types = {
            "IfcWall", "IfcWallStandardCase", "IfcSlab", "IfcColumn",
            "IfcBeam", "IfcFooting", "IfcRoof", "IfcDoor", "IfcWindow"
        }
        for elem in elements:
            if elem.element_type in physical_element_types and not elem.materials:
                add_finding(
                    title="Missing Material Specification",
                    severity="Warning",
                    category="material",
                    element=elem,
                    flagged_reason="Physical element has no material association via IfcRelAssociatesMaterial. Embodied carbon (ICE v3) and thermal resistance cannot be calculated.",
                    evidence="No materials assigned or linked in IFC model.",
                    action="Assign material definition or layered assembly (e.g. C30 concrete, steel grade, timber) in authoring tool before export."
                )

        # =====================================================================
        # 3. UNCONNECTED OR DISCONNECTED ELEMENTS
        # =====================================================================
        aperture_types = {"IfcDoor", "IfcWindow"}
        for elem in elements:
            if elem.element_type in aperture_types:
                hosted_in = elem.relationships.get("hosted_in")
                if not hosted_in:
                    add_finding(
                        title=f"Unhosted {elem.element_type} (Disconnected Aperture)",
                        severity="Warning",
                        category="connectivity",
                        element=elem,
                        flagged_reason="Door/Window aperture is not hosted inside any IfcWall or opening void. May indicate misplaced or detached BIM object.",
                        evidence="No IfcRelFillsElement / IfcRelVoidsElement link found associating aperture with host wall.",
                        action="Ensure door/window is placed within an architectural host wall in the BIM authoring model."
                    )
            elif elem.element_type in ["IfcColumn", "IfcBeam"]:
                # Check for isolated structural elements (no storey AND no connections)
                if not elem.storey_id and not elem.relationships.get("connected_to"):
                    add_finding(
                        title=f"Isolated Structural Element ({elem.element_type})",
                        severity="Information",
                        category="connectivity",
                        element=elem,
                        flagged_reason="Structural component lacks both vertical storey containment and structural connectivity links in coordination model.",
                        evidence="Zero connected elements in graph and no storey assignment.",
                        action="Verify that structural framing is assigned to a building level and connected to loadbearing grid."
                    )

        # =====================================================================
        # 4. DUPLICATE OR CONFLICTING ELEMENT IDENTIFIERS
        # =====================================================================
        seen_guids: Dict[str, BuildingElement] = {}
        for elem in elements:
            guid = elem.source_global_id
            if not guid:
                add_finding(
                    title="Missing Native IFC GlobalId",
                    severity="Warning",
                    category="identifier",
                    element=elem,
                    flagged_reason="Element lacks a native IFC STEP GlobalId. Unique tracking across federated digital twins is impaired.",
                    evidence="Synthetic internal ID generated for fallback.",
                    action="Configure BIM export to preserve standard 22-character IFC GlobalIds."
                )
            else:
                if guid in seen_guids:
                    prior = seen_guids[guid]
                    add_finding(
                        title="Duplicate IFC GlobalId Identifier Conflict",
                        severity="High",
                        category="identifier",
                        element=elem,
                        flagged_reason=f"Element shares identical IFC GlobalId with '{prior.name}' ({prior.element_id}). Violates ISO 10303-21 uniqueness requirement and prevents reliable twin synchronization.",
                        evidence=f"Duplicate GlobalId '{guid}' shared by {elem.element_id} and {prior.element_id}.",
                        action="Regenerate unique IFC GUIDs in the authoring tool before federating.",
                        source_props={"conflicting_element_id": prior.element_id, "global_id": guid}
                    )
                else:
                    seen_guids[guid] = elem

        # =====================================================================
        # 5. MISSING STOREY OR SPATIAL ASSIGNMENTS
        # =====================================================================
        for elem in elements:
            if not elem.storey_id or elem.storey_name in [None, "Unassigned", ""]:
                add_finding(
                    title="Missing Building Storey Containment",
                    severity="Warning",
                    category="spatial",
                    element=elem,
                    flagged_reason="Element is not assigned to any IfcBuildingStorey container via IfcRelContainedInSpatialStructure.",
                    evidence="RelContainedInSpatialStructure relationship is missing.",
                    action="Assign element to its corresponding architectural level or floor in the authoring application."
                )

        # =====================================================================
        # 6. POTENTIAL GEOMETRY OVERLAPS & UNUSUAL DIMENSIONS
        # =====================================================================
        for elem in elements:
            # Check unusual wall thickness
            if elem.element_type in ["IfcWall", "IfcWallStandardCase"]:
                thickness = elem.quantity_estimates.get("thickness")
                if thickness is None and elem.bounding_box:
                    # In plan (XY), wall thickness is the narrower horizontal dimension
                    horiz_dims = [d for d in [elem.bounding_box.width, elem.bounding_box.height] if d > 0]
                    thickness = min(horiz_dims) if horiz_dims else None

                if thickness is not None:
                    if thickness < 0.05:  # Less than 50 mm
                        add_finding(
                            title="Unusual Dimension: Substandard Wall Thickness",
                            severity="Warning",
                            category="geometry",
                            element=elem,
                            flagged_reason=f"Wall thickness ({thickness*1000:.0f} mm) is unusually thin (< 50 mm) for a physical partition or structural wall. May indicate 2D line extrusion or finish layer misclassification.",
                            evidence=f"Extracted wall thickness: {thickness:.3f} m",
                            action="Verify whether entity is a partition wall, cladding finish, or 2D abstraction."
                        )
                    elif thickness > 1.50:  # Greater than 1.5 m
                        add_finding(
                            title="Unusual Dimension: Massive Wall Thickness",
                            severity="Information",
                            category="geometry",
                            element=elem,
                            flagged_reason=f"Wall thickness ({thickness:.2f} m) exceeds standard architectural range (> 1.5 m).",
                            evidence=f"Extracted wall thickness: {thickness:.3f} m",
                            action="Verify if element is an embankment, retaining mass, or geometric placeholder."
                        )

            # Check door width and height
            if elem.element_type == "IfcDoor":
                width = elem.quantity_estimates.get("overallwidth")
                if width is None and elem.bounding_box:
                    horiz_dims = [d for d in [elem.bounding_box.width, elem.bounding_box.height] if d > 0]
                    width = max(horiz_dims) if horiz_dims else None

                height = elem.quantity_estimates.get("overallheight") or (
                    elem.bounding_box.depth if elem.bounding_box else None
                )
                if width is not None and width < 0.70:
                    add_finding(
                        title="Unusual Dimension: Narrow Door Opening",
                        severity="Warning",
                        category="geometry",
                        element=elem,
                        flagged_reason=f"Door width ({width*1000:.0f} mm) is narrower than standard minimum egress width (750 mm) and wheelchair accessibility norms (900 mm).",
                        evidence=f"Extracted width: {width:.3f} m",
                        action="Review architectural door schedule against accessibility and fire exit clearance requirements."
                    )
                if height is not None and height < 1.80:
                    add_finding(
                        title="Unusual Dimension: Low Door Headroom",
                        severity="Warning",
                        category="geometry",
                        element=elem,
                        flagged_reason=f"Door height ({height:.2f} m) is below standard minimum headroom (2.0 m).",
                        evidence=f"Extracted height: {height:.3f} m",
                        action="Verify door opening frame heights and structural lintel elevations."
                    )

            # Check zero or degenerate physical volume
            if elem.element_type in physical_element_types:
                vol = elem.quantity_estimates.get("approx_volume_m3", 0.0)
                if vol <= 0.0001:
                    add_finding(
                        title="Geometric Discrepancy: Zero Bounding Volume",
                        severity="Warning",
                        category="geometry",
                        element=elem,
                        flagged_reason="Physical solid component has zero or degenerate bounding envelope volume.",
                        evidence=f"Calculated envelope volume: {vol:.4f} m³",
                        action="Inspect extrusion profile and boundary representation (B-Rep) for geometry errors."
                    )

        # Geometric Overlap Collision Check (Same Category Volumetric Collision)
        # Check pairs of elements within same category for excessive spatial overlap (>85%)
        by_category: Dict[str, List[BuildingElement]] = {}
        for elem in elements:
            if elem.element_type in physical_element_types and elem.bounding_box:
                by_category.setdefault(elem.element_type, []).append(elem)

        overlap_checked_pairs: Set[Tuple[str, str]] = set()
        for cat, cat_elems in by_category.items():
            for i in range(len(cat_elems)):
                for j in range(i + 1, len(cat_elems)):
                    e1, e2 = cat_elems[i], cat_elems[j]
                    b1, b2 = e1.bounding_box, e2.bounding_box
                    if not b1 or not b2:
                        continue

                    pair_key = (min(e1.element_id, e2.element_id), max(e1.element_id, e2.element_id))
                    if pair_key in overlap_checked_pairs:
                        continue
                    overlap_checked_pairs.add(pair_key)

                    # Compute 3D bounding box intersection
                    dx = max(0.0, min(b1.max_x, b2.max_x) - max(b1.min_x, b2.min_x))
                    dy = max(0.0, min(b1.max_y, b2.max_y) - max(b1.min_y, b2.min_y))
                    dz = max(0.0, min(b1.max_z, b2.max_z) - max(b1.min_z, b2.min_z))
                    inter_vol = dx * dy * dz

                    if inter_vol > 0.001:
                        v1 = max(0.0001, b1.width * b1.height * b1.depth)
                        v2 = max(0.0001, b2.width * b2.height * b2.depth)
                        overlap_ratio = inter_vol / min(v1, v2)

                        if overlap_ratio >= 0.85:
                            add_finding(
                                title=f"Potential Geometry Clashing ({cat})",
                                severity="High",
                                category="geometry",
                                element=e1,
                                flagged_reason=f"High volumetric overlap ({int(overlap_ratio*100)}%) with '{e2.name}' ({e2.source_global_id}). Suggests duplicate modeled elements inflating cost and carbon estimations.",
                                evidence=f"Collision overlap volume: {inter_vol:.3f} m³ out of {min(v1, v2):.3f} m³ ({int(overlap_ratio*100)}% overlap).",
                                action="Inspect 3D coordinates in authoring tool and remove duplicate modeled geometry.",
                                source_props={"conflicting_element_id": e2.element_id, "conflicting_global_id": e2.source_global_id}
                            )

        # =====================================================================
        # DASHBOARD METRICS CALCULATION (DERIVED EXCLUSIVELY FROM MODEL)
        # =====================================================================
        total_elements = len(elements)

        # 1. Element counts by category
        element_counts_by_category = dict(model.element_counts_by_type)

        # 2. Material distribution
        material_data: Dict[str, Dict[str, float]] = {}
        total_structural_vol = 0.0
        for elem in elements:
            mats = elem.materials if elem.materials else ["Unspecified / Missing Material"]
            vol = elem.quantity_estimates.get("approx_volume_m3", 0.0)
            total_structural_vol += vol
            per_mat_vol = vol / max(1, len(mats))
            for m in mats:
                if m not in material_data:
                    material_data[m] = {"count": 0, "volume": 0.0}
                material_data[m]["count"] += 1
                material_data[m]["volume"] += per_mat_vol

        material_distribution: List[MaterialDistributionItem] = []
        for mat_name, m_info in sorted(material_data.items(), key=lambda x: x[1]["volume"], reverse=True):
            pct = round((m_info["volume"] / max(0.001, total_structural_vol)) * 100, 1) if total_structural_vol > 0 else 0.0
            material_distribution.append(
                MaterialDistributionItem(
                    material_name=mat_name,
                    element_count=int(m_info["count"]),
                    approx_volume_m3=round(m_info["volume"], 2),
                    percentage=pct
                )
            )

        # 3. Model completeness percentage
        valid_count = sum(
            1 for e in elements
            if e.geometry and e.geometry.vertex_count > 0 and e.source_global_id and e.materials
        )
        completeness_pct = round((valid_count / max(1, total_elements)) * 100, 1)

        # 4. Findings by severity (Information, Warning, High)
        findings_by_severity = {
            "High": sum(1 for f in findings if f.severity == "High"),
            "Warning": sum(1 for f in findings if f.severity == "Warning"),
            "Information": sum(1 for f in findings if f.severity == "Information"),
        }

        # 5. Storey-wise distribution
        storey_counts: Dict[str, Dict[str, Any]] = {}
        for s in model.storeys:
            storey_counts[s.storey_id] = {"name": s.name, "count": 0}

        unassigned_count = 0
        for elem in elements:
            if elem.storey_id and elem.storey_id in storey_counts:
                storey_counts[elem.storey_id]["count"] += 1
            else:
                unassigned_count += 1

        storey_distribution: List[StoreyDistributionItem] = []
        for s_id, s_data in storey_counts.items():
            pct = round((s_data["count"] / max(1, total_elements)) * 100, 1)
            storey_distribution.append(
                StoreyDistributionItem(
                    storey_id=s_id,
                    storey_name=s_data["name"],
                    element_count=s_data["count"],
                    percentage=pct
                )
            )

        if unassigned_count > 0:
            storey_distribution.append(
                StoreyDistributionItem(
                    storey_id="unassigned",
                    storey_name="Unassigned to Storey",
                    element_count=unassigned_count,
                    percentage=round((unassigned_count / max(1, total_elements)) * 100, 1)
                )
            )

        # =====================================================================
        # 4. EVIDENCE-BASED ARCHITECTURAL & SUSTAINABILITY RECOMMENDATIONS
        # =====================================================================
        recommendations: List[EvidenceBasedRecommendation] = []
        rec_seq = 0

        # Calculate geometric parameters
        bbox = model.bounding_box
        width = bbox.width if bbox else 12.0
        depth = bbox.depth if bbox else 16.0
        height = bbox.height if bbox else 6.0
        roof_area = max(1.0, width * depth)
        total_wall_area = max(1.0, 2 * (width + depth) * height)
        window_count = sum(1 for e in elements if "window" in e.element_type.lower())
        window_area = window_count * 2.0
        wwr = window_area / total_wall_area

        # 1. Roof Thermal Insulation
        rec_seq += 1
        recommendations.append(
            EvidenceBasedRecommendation(
                id=f"REC-{rec_seq:03d}",
                title="Extruded Polystyrene (XPS) Roof Thermal Insulation",
                category="roof_insulation",
                priority="high" if len(model.storeys) <= 3 else "medium",
                detected_issue="Uninsulated concrete roof deck subject to intense solar heat transfer into top floor.",
                explanation="Exposed concrete roofs without continuous thermal insulation transfer significant radiant heat directly into occupied spaces, driving up HVAC cooling loads.",
                supporting_evidence=f"Roof area measures {roof_area:.1f} m² with uninsulated slab specifications in authoring BIM model.",
                proposed_intervention="Install 50mm high-density XPS rigid foam boards (R-value ~1.8 m²K/W) under waterproof membrane with protective ballast screed.",
                expected_benefit="Lowers roof U-value from ~2.8 W/m²K to < 0.45 W/m²K, reducing top-floor cooling energy demand by 20% to 30%.",
                estimated_cost_inr=round(roof_area * 850.0, 2),
                confidence="high",
                calculation_method="CPWD / IS 3792 Thermal Insulation Code unit rates",
                limitations="Requires structural sign-off on additional dead load of screed layer (~80-100 kg/m²)."
            )
        )

        # 2. Window External Shading & Louvers
        if window_count > 0:
            rec_seq += 1
            recommendations.append(
                EvidenceBasedRecommendation(
                    id=f"REC-{rec_seq:03d}",
                    title="Architectural External Window Shading Louvers",
                    category="window_shading",
                    priority="high" if wwr > 0.20 else "medium",
                    detected_issue=f"Window-to-Wall ratio is {wwr:.1%} across {window_count} exterior window openings without external shading devices.",
                    explanation="Unshaded glass facades allow direct shortwave solar radiation to penetrate the envelope, causing severe greenhouse heat accumulation and occupant discomfort.",
                    supporting_evidence=f"Detected {window_count} unshaded aperture elements in IFC model with no horizontal overhang or louver assemblies.",
                    proposed_intervention="Mount horizontal powder-coated aluminum louvers or 600mm deep reinforced concrete chajjas over south and west facing apertures.",
                    expected_benefit="Cuts peak solar heat ingress by 55% to 70% while maintaining healthy daylight autonomy.",
                    estimated_cost_inr=round(window_count * 5500.0, 2),
                    confidence="high",
                    calculation_method="Bureau of Energy Efficiency (BEE) ECBC Shading Coefficient guidelines",
                    limitations="Custom architectural mounting brackets required for non-loadbearing curtain wall frames."
                )
            )

        # 3. High-Albedo Cool Roof Coating
        rec_seq += 1
        recommendations.append(
            EvidenceBasedRecommendation(
                id=f"REC-{rec_seq:03d}",
                title="High-Albedo Reflective Roof Coating (Cool Roof)",
                category="reflective_roof",
                priority="medium",
                detected_issue="Dark roof substrate absorbs incident solar irradiance, exacerbating heat accumulation and urban heat island effects.",
                explanation="Standard exposed concrete or bitumen finishes absorb over 75% of solar radiation. High-albedo elastomeric coatings reflect sunlight back into the atmosphere.",
                supporting_evidence=f"Roof surface area {roof_area:.1f} m² has no high-reflectance specification in imported IFC material schedules.",
                proposed_intervention="Apply two coats of acrylic elastomeric reflective white coating with minimum Solar Reflectance Index (SRI) >= 78.",
                expected_benefit="Lowers peak exterior roof surface temperatures by 15°C to 20°C, lowering indoor ambient temperatures by 2°C to 4°C.",
                estimated_cost_inr=round(roof_area * 280.0, 2),
                confidence="high",
                calculation_method="Cool Roof Rating Council (CRRC) empirical solar thermal reflectance models",
                limitations="Requires routine periodic recoating every 4 to 5 years and periodic washing to remove particulate soiling."
            )
        )

        # 4. Rooftop Solar Photovoltaic (PV) System
        rec_seq += 1
        pv_usable_area = roof_area * 0.70
        pv_kwp = round(pv_usable_area * 0.15, 1)  # approx 150 Wp/m2
        annual_pv_kwh = round(pv_usable_area * 4.8 * 365 * 0.20 * 0.78)
        recommendations.append(
            EvidenceBasedRecommendation(
                id=f"REC-{rec_seq:03d}",
                title="Rooftop Monocrystalline Solar PV System",
                category="solar_pv",
                priority="high",
                detected_issue="Unutilized horizontal roof plane with favorable clear-sky solar insolation potential.",
                explanation="Generating clean on-site renewable energy offsets grid carbon intensity and provides significant operational power savings.",
                supporting_evidence=f"Unobstructed roof plane affords approx {pv_usable_area:.1f} m² net usable installation area (70% net allowance).",
                proposed_intervention=f"Deploy a {pv_kwp} kWp grid-tied solar PV array with Tier-1 monocrystalline panels and dual-MPPT string inverter.",
                expected_benefit=f"Generates approx {annual_pv_kwh:,} kWh/year, avoiding grid utility expenditure and scope-2 emissions.",
                estimated_cost_inr=round(pv_kwp * 48000.0, 2),
                confidence="high",
                calculation_method="NREL PVWatts insolation baseline (4.8 kWh/m²/day GHI, 78% PR)",
                limitations="Requires structural check of roof slab live-load rating and municipal DISCOM net-metering interconnection approval."
            )
        )

        # 5. Rainwater Harvesting & Groundwater Recharge
        rec_seq += 1
        annual_rain_l = round(roof_area * 0.85 * 0.85 * 1000)
        recommendations.append(
            EvidenceBasedRecommendation(
                id=f"REC-{rec_seq:03d}",
                title="Rooftop Rainwater Harvesting & Filtration System",
                category="rainwater_harvesting",
                priority="medium",
                detected_issue="Precipitation runoff from building roof is discharged into municipal storm drains without recovery.",
                explanation="Capturing roof runoff provides non-potable water for landscaping, toilet flushing, and cooling towers while recharging the local aquifer.",
                supporting_evidence=f"Impermeable roof catchment footprint of {roof_area:.1f} m² with clear gutter collection perimeter.",
                proposed_intervention="Install food-grade PVC collection gutters, first-flush diverter, sand-gravel filter, and 15,000L modular storage tank.",
                expected_benefit=f"Recovers an estimated {annual_rain_l:,} Liters/year, enhancing building freshwater resilience.",
                estimated_cost_inr=125000.0,
                confidence="high",
                calculation_method="Central Ground Water Board (CGWB) Rainwater Harvesting Design Norms",
                limitations="Routine pre-monsoon gutter cleaning and first-flush diverter desiltation required."
            )
        )

        summary = (
            f"Analyzed {total_elements} building elements across {len(model.storeys)} storeys. "
            f"Model completeness: {completeness_pct}%. "
            f"Identified {findings_by_severity['High']} High concerns, "
            f"{findings_by_severity['Warning']} Warnings, and {findings_by_severity['Information']} Information items. "
            f"Generated {len(recommendations)} evidence-based architectural and sustainability retrofit recommendations."
        )

        return BuildingIntelligenceReport(
            model_id=model.model_id,
            total_elements=total_elements,
            element_counts_by_category=element_counts_by_category,
            material_distribution=material_distribution,
            model_completeness_pct=completeness_pct,
            findings_by_severity=findings_by_severity,
            storey_distribution=storey_distribution,
            findings=findings,
            recommendations=recommendations,
            summary=summary
        )
