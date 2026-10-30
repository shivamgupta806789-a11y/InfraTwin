from typing import List, Dict, Set
from app.models.digital_twin import (
    BuildingModelDetail,
    QualityFinding,
    ModelQualityReport,
)

class QualityEngine:
    @classmethod
    def evaluate_model_quality(
        cls,
        model: BuildingModelDetail,
        parser_warnings: List[str]
    ) -> ModelQualityReport:
        findings: List[QualityFinding] = []
        finding_seq = 0

        def create_finding(
            severity: str,
            category: str,
            description: str,
            evidence: str,
            limitation: str,
            action: str,
            affected_ids: List[str] = None
        ) -> QualityFinding:
            nonlocal finding_seq
            finding_seq += 1
            return QualityFinding(
                finding_id=f"QUAL-{finding_seq:03d}",
                severity=severity,
                category=category,
                affected_element_ids=affected_ids or [],
                description=description,
                evidence=evidence,
                limitation=limitation,
                recommended_action=action
            )

        # 1. Spatial Hierarchy Check [Missing BIM Data]
        if not model.storeys:
            findings.append(
                create_finding(
                    severity="warning",
                    category="hierarchy",
                    description="[Missing BIM Data] Building contains no IfcBuildingStorey spatial containers.",
                    evidence=f"Model '{model.source_filename}' has 0 defined storeys. All {model.total_element_count} elements lack vertical level containment.",
                    limitation="Cannot filter or slice elements vertically by architectural floor. This is an authoring data omission, not a structural defect.",
                    action="Ensure IFC authoring export (Revit / ArchiCAD) includes building storey assignments."
                )
            )
        else:
            elements_without_storey = [
                e.element_id for e in model.elements if not e.storey_id
            ]
            if elements_without_storey:
                findings.append(
                    create_finding(
                        severity="info",
                        category="hierarchy",
                        description=f"[Missing BIM Data] {len(elements_without_storey)} element(s) are unassigned to any storey.",
                        evidence=f"Elements: {', '.join(elements_without_storey[:5])}{'...' if len(elements_without_storey) > 5 else ''} lack RelContainedInSpatialStructure links.",
                        limitation="These elements will be rendered globally without vertical filter association.",
                        action="Assign elements to their respective building storeys in the BIM authoring tool.",
                        affected_ids=elements_without_storey
                    )
                )

        # 2. Geometric Tessellation Check [Geometry Defect]
        elements_without_geometry = [
            e.element_id for e in model.elements if not e.geometry or not e.geometry.vertices
        ]
        if elements_without_geometry:
            findings.append(
                create_finding(
                    severity="warning",
                    category="geometry",
                    description=f"[Geometry Defect] {len(elements_without_geometry)} element(s) could not produce valid 3D surface geometry.",
                    evidence=f"No tessellated mesh generated for element(s): {', '.join(elements_without_geometry[:5])}.",
                    limitation="Elements cannot be rendered as 3D surface meshes in WebGL view.",
                    action="Inspect IFC shape representation for non-manifold surfaces, boundary representation errors, or missing extrusion profiles.",
                    affected_ids=elements_without_geometry
                )
            )

        # 3. Source GlobalId Integrity Check [Schema Violation]
        seen_guids: Set[str] = set()
        duplicate_guids: List[str] = []
        elements_missing_guid: List[str] = []

        for e in model.elements:
            if not e.source_global_id:
                elements_missing_guid.append(e.element_id)
            else:
                if e.source_global_id in seen_guids:
                    duplicate_guids.append(e.element_id)
                else:
                    seen_guids.add(e.source_global_id)

        if elements_missing_guid:
            findings.append(
                create_finding(
                    severity="error",
                    category="identifier",
                    description=f"[Schema Violation] {len(elements_missing_guid)} element(s) lack a native IFC GlobalId.",
                    evidence=f"Synthesized internal IDs were generated for tracking: {', '.join(elements_missing_guid[:5])}.",
                    limitation="BIM coordination traceability is degraded; cannot guarantee bi-directional sync with authoring tool.",
                    action="Export with unique IFC STEP GlobalIds compliant with ISO 10303-21.",
                    affected_ids=elements_missing_guid
                )
            )

        if duplicate_guids:
            findings.append(
                create_finding(
                    severity="error",
                    category="identifier",
                    description=f"[Schema Violation] Detected {len(duplicate_guids)} element(s) sharing duplicate GlobalIds.",
                    evidence=f"Non-unique GlobalIds encountered on elements: {', '.join(duplicate_guids[:5])}.",
                    limitation="Violates IFC schema uniqueness constraint; risk of incorrect element matching in digital twin.",
                    action="Regenerate unique IFC GUIDs prior to federation.",
                    affected_ids=duplicate_guids
                )
            )

        # 4. Material Specification Check [Missing BIM Data]
        structural_types = {"IfcWall", "IfcWallStandardCase", "IfcSlab", "IfcColumn", "IfcBeam", "IfcRoof", "IfcFooting"}
        elements_missing_material = [
            e.element_id for e in model.elements
            if e.element_type in structural_types and not e.materials
        ]
        if elements_missing_material:
            findings.append(
                create_finding(
                    severity="warning",
                    category="material",
                    description=f"[Missing BIM Data] {len(elements_missing_material)} structural element(s) have no assigned material associations.",
                    evidence=f"Elements {', '.join(elements_missing_material[:5])} lack IfcRelAssociatesMaterial.",
                    limitation="Embodied carbon and thermal transmittance cannot be calculated without material assignments. This is an authoring omission, not a physical defect.",
                    action="Assign material layers or material definitions in the BIM model before export.",
                    affected_ids=elements_missing_material
                )
            )

        # 5. Missing Standard Property Sets Check [Missing BIM Data]
        expected_psets = {
            "IfcWall": "Pset_WallCommon",
            "IfcWallStandardCase": "Pset_WallCommon",
            "IfcSlab": "Pset_SlabCommon",
            "IfcColumn": "Pset_ColumnCommon",
            "IfcBeam": "Pset_BeamCommon",
            "IfcDoor": "Pset_DoorCommon",
            "IfcWindow": "Pset_WindowCommon",
        }
        elements_missing_psets = []
        for e in model.elements:
            expected = expected_psets.get(e.element_type)
            if expected and expected not in e.source_properties:
                elements_missing_psets.append(e.element_id)

        if elements_missing_psets:
            findings.append(
                create_finding(
                    severity="warning",
                    category="completeness",
                    description=f"[Missing BIM Data] {len(elements_missing_psets)} element(s) lack standard buildingSMART property sets (e.g. Pset_WallCommon, Pset_DoorCommon).",
                    evidence=f"Elements {', '.join(elements_missing_psets[:5])}{'...' if len(elements_missing_psets) > 5 else ''} contain no standardized property sets.",
                    limitation="Limits automated thermal transmittance, acoustic, and fire rating audits. Authoring data omission.",
                    action="Enable standard buildingSMART property set export in BIM software.",
                    affected_ids=elements_missing_psets
                )
            )

        # 6. Dimensional Quantity Check [Geometry Defect]
        elements_missing_volume = [
            e.element_id for e in model.elements
            if e.element_type in structural_types and not e.quantity_estimates.get("approx_volume_m3")
        ]
        if elements_missing_volume:
            findings.append(
                create_finding(
                    severity="info",
                    category="geometry",
                    description=f"[Geometry Defect] {len(elements_missing_volume)} element(s) lack measurable volumetric bounding boxes.",
                    evidence=f"Bounding box volume is zero or unavailable for {', '.join(elements_missing_volume[:5])}.",
                    limitation="Material take-off and structural mass estimation cannot be performed.",
                    action="Verify geometric representation completeness in BIM authoring software.",
                    affected_ids=elements_missing_volume
                )
            )

        # 7. Unsupported Elements Check [Unsupported Entity]
        unsupported = model.provenance_metadata.get("unsupported_elements", {})
        if unsupported:
            unsupported_desc = ", ".join([f"{k} ({v})" for k, v in unsupported.items()])
            findings.append(
                create_finding(
                    severity="info",
                    category="completeness",
                    description=f"[Unsupported Entity] Model contains {sum(unsupported.values())} non-structural / non-envelope elements ({unsupported_desc}).",
                    evidence="Entities detected outside core architectural structural/envelope scope.",
                    limitation="MEP fixtures and furnishings are excluded from 3D structural twin rendering.",
                    action="No action required. Core structural and envelope twin is intact."
                )
            )

        # 8. Parser Warnings Ingestion
        for p_warn in parser_warnings[:5]:
            findings.append(
                create_finding(
                    severity="info",
                    category="coordination",
                    description=f"[Import Notice] {p_warn[:80]}...",
                    evidence=p_warn,
                    limitation="Parser executed standard heuristic or subsampling fallback.",
                    action="Verify original IFC export configuration."
                )
            )

        # Calculate completeness ratio
        total_elems = max(1, model.total_element_count)
        valid_elems = sum(
            1 for e in model.elements
            if e.geometry and e.geometry.vertices and e.source_global_id
        )
        completeness_ratio = round(valid_elems / total_elems, 2)

        # Count severity
        severity_counts = {"info": 0, "warning": 0, "error": 0, "critical": 0}
        for f in findings:
            severity_counts[f.severity] = severity_counts.get(f.severity, 0) + 1

        summary = (
            f"Evaluated {model.total_element_count} elements across {len(model.storeys)} storeys. "
            f"Data completeness ratio: {completeness_ratio * 100:.0f}%. "
            f"Found {severity_counts['critical']} critical, {severity_counts['error']} errors, "
            f"{severity_counts['warning']} warnings, and {severity_counts['info']} informative notes."
        )

        return ModelQualityReport(
            model_id=model.model_id,
            total_findings=len(findings),
            by_severity=severity_counts,
            findings=findings,
            data_completeness_ratio=completeness_ratio,
            summary=summary
        )
