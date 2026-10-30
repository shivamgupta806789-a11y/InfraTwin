import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.digital_twin import (
    BuildingModelDetail,
    BuildingElement,
    BoundingBox3D,
    ElementGeometry,
    StoreyInfo,
)
from app.services.intelligence_engine import IntelligenceEngine

client = TestClient(app)

def test_intelligence_endpoint_returns_report():
    response = client.get("/api/v1/models/sample-office-twin/intelligence")
    assert response.status_code == 200
    report = response.json()
    assert report["model_id"] == "sample-office-twin"
    assert report["total_elements"] >= 21
    assert "element_counts_by_category" in report
    assert "material_distribution" in report
    assert isinstance(report["material_distribution"], list)
    assert len(report["material_distribution"]) > 0
    assert report["model_completeness_pct"] > 0
    assert "findings_by_severity" in report
    assert "High" in report["findings_by_severity"]
    assert "Warning" in report["findings_by_severity"]
    assert "Information" in report["findings_by_severity"]
    assert "storey_distribution" in report
    assert len(report["storey_distribution"]) >= 2
    assert "findings" in report
    assert isinstance(report["findings"], list)

def test_intelligence_missing_property_set_rule():
    # Build a synthetic model with a wall missing Pset_WallCommon
    synthetic_element = BuildingElement(
        element_id="test_wall_1",
        source_global_id="3Xk9876543210ABCDEF123",
        element_type="IfcWall",
        name="Test Wall Without Pset",
        storey_id="storey_1",
        storey_name="Level 1",
        source_properties={},  # Missing Pset_WallCommon
        materials=["C30/37 Concrete"],
        geometry=ElementGeometry(vertices=[0,0,0, 1,0,0, 0,1,0], faces=[0,1,2], vertex_count=3, face_count=1),
        bounding_box=BoundingBox3D(min_x=0, min_y=0, min_z=0, max_x=10, max_y=0.3, max_z=3, center_x=5, center_y=0.15, center_z=1.5, width=10, height=0.3, depth=3),
        quantity_estimates={"approx_volume_m3": 9.0, "thickness": 0.3}
    )
    model = BuildingModelDetail(
        model_id="test-model-prop",
        source_filename="test.ifc",
        import_timestamp="2026-10-30T00:00:00Z",
        storeys=[StoreyInfo(storey_id="storey_1", name="Level 1", element_count=1)],
        elements=[synthetic_element],
        element_counts_by_type={"IfcWall": 1},
        total_element_count=1
    )
    report = IntelligenceEngine.analyze_model(model)
    prop_findings = [f for f in report.findings if f.category == "property"]
    assert len(prop_findings) > 0
    assert any("Missing Property Set: Pset_WallCommon" in f.title for f in prop_findings)
    assert prop_findings[0].severity == "Warning"
    assert prop_findings[0].affected_element_id == "test_wall_1"

def test_intelligence_missing_material_rule():
    synthetic_element = BuildingElement(
        element_id="test_slab_1",
        source_global_id="2A19876543210ABCDEF123",
        element_type="IfcSlab",
        name="Test Slab Without Material",
        storey_id="storey_1",
        storey_name="Level 1",
        source_properties={"Pset_SlabCommon": {"LoadBearing": True}},
        materials=[],  # Missing materials
        geometry=ElementGeometry(vertices=[0,0,0, 1,0,0, 0,1,0], faces=[0,1,2], vertex_count=3, face_count=1),
        bounding_box=BoundingBox3D(min_x=0, min_y=0, min_z=0, max_x=10, max_y=10, max_z=0.3, center_x=5, center_y=5, center_z=0.15, width=10, height=10, depth=0.3),
        quantity_estimates={"approx_volume_m3": 30.0}
    )
    model = BuildingModelDetail(
        model_id="test-model-mat",
        source_filename="test.ifc",
        import_timestamp="2026-10-30T00:00:00Z",
        storeys=[StoreyInfo(storey_id="storey_1", name="Level 1", element_count=1)],
        elements=[synthetic_element],
        element_counts_by_type={"IfcSlab": 1},
        total_element_count=1
    )
    report = IntelligenceEngine.analyze_model(model)
    mat_findings = [f for f in report.findings if f.category == "material"]
    assert len(mat_findings) > 0
    assert any("Missing Material Specification" in f.title for f in mat_findings)
    assert mat_findings[0].severity == "Warning"

def test_intelligence_unconnected_aperture_rule():
    # Door with no host wall
    synthetic_door = BuildingElement(
        element_id="test_door_unhosted",
        source_global_id="1D19876543210ABCDEF123",
        element_type="IfcDoor",
        name="Free Floating Door",
        storey_id="storey_1",
        storey_name="Level 1",
        source_properties={"Pset_DoorCommon": {"OverallWidth": 0.95, "OverallHeight": 2.1}},
        materials=["Timber"],
        relationships={"hosted_in": None},  # No host wall
        geometry=ElementGeometry(vertices=[0,0,0, 1,0,0, 0,1,0], faces=[0,1,2], vertex_count=3, face_count=1),
        bounding_box=BoundingBox3D(min_x=0, min_y=0, min_z=0, max_x=0.95, max_y=0.1, max_z=2.1, center_x=0.47, center_y=0.05, center_z=1.05, width=0.95, height=0.1, depth=2.1),
        quantity_estimates={"approx_volume_m3": 0.2, "overallwidth": 0.95, "overallheight": 2.1}
    )
    model = BuildingModelDetail(
        model_id="test-model-aperture",
        source_filename="test.ifc",
        import_timestamp="2026-10-30T00:00:00Z",
        storeys=[StoreyInfo(storey_id="storey_1", name="Level 1", element_count=1)],
        elements=[synthetic_door],
        element_counts_by_type={"IfcDoor": 1},
        total_element_count=1
    )
    report = IntelligenceEngine.analyze_model(model)
    conn_findings = [f for f in report.findings if f.category == "connectivity"]
    assert len(conn_findings) > 0
    assert any("Unhosted IfcDoor" in f.title for f in conn_findings)
    assert conn_findings[0].severity == "Warning"

def test_intelligence_duplicate_identifier_rule():
    guid = "DUPLICATE_GUID_1234567"
    elem1 = BuildingElement(
        element_id="elem_col_1",
        source_global_id=guid,
        element_type="IfcColumn",
        name="Column 1",
        storey_id="storey_1",
        storey_name="Level 1",
        source_properties={"Pset_ColumnCommon": {"LoadBearing": True}},
        materials=["Concrete"],
        geometry=ElementGeometry(vertices=[0,0,0, 1,0,0, 0,1,0], faces=[0,1,2], vertex_count=3, face_count=1),
        bounding_box=BoundingBox3D(min_x=0, min_y=0, min_z=0, max_x=0.4, max_y=0.4, max_z=3, center_x=0.2, center_y=0.2, center_z=1.5, width=0.4, height=0.4, depth=3),
        quantity_estimates={"approx_volume_m3": 0.48}
    )
    elem2 = BuildingElement(
        element_id="elem_col_2",
        source_global_id=guid,  # Duplicate!
        element_type="IfcColumn",
        name="Column 2",
        storey_id="storey_1",
        storey_name="Level 1",
        source_properties={"Pset_ColumnCommon": {"LoadBearing": True}},
        materials=["Concrete"],
        geometry=ElementGeometry(vertices=[0,0,0, 1,0,0, 0,1,0], faces=[0,1,2], vertex_count=3, face_count=1),
        bounding_box=BoundingBox3D(min_x=5, min_y=5, min_z=0, max_x=5.4, max_y=5.4, max_z=3, center_x=5.2, center_y=5.2, center_z=1.5, width=0.4, height=0.4, depth=3),
        quantity_estimates={"approx_volume_m3": 0.48}
    )
    model = BuildingModelDetail(
        model_id="test-model-dup",
        source_filename="test.ifc",
        import_timestamp="2026-10-30T00:00:00Z",
        storeys=[StoreyInfo(storey_id="storey_1", name="Level 1", element_count=2)],
        elements=[elem1, elem2],
        element_counts_by_type={"IfcColumn": 2},
        total_element_count=2
    )
    report = IntelligenceEngine.analyze_model(model)
    id_findings = [f for f in report.findings if f.category == "identifier"]
    assert len(id_findings) > 0
    assert any(f.severity == "High" for f in id_findings)
    assert any("Duplicate IFC GlobalId" in f.title for f in id_findings)

def test_intelligence_geometry_overlap_collision_rule():
    # Two columns occupying overlapping coordinates
    b_common = BoundingBox3D(
        min_x=0.0, min_y=0.0, min_z=0.0,
        max_x=0.4, max_y=0.4, max_z=3.0,
        center_x=0.2, center_y=0.2, center_z=1.5,
        width=0.4, height=0.4, depth=3.0
    )
    col1 = BuildingElement(
        element_id="elem_col_a",
        source_global_id="GUID_COL_A_11111111",
        element_type="IfcColumn",
        name="Primary Column A",
        storey_id="storey_1",
        storey_name="Level 1",
        source_properties={"Pset_ColumnCommon": {"LoadBearing": True}},
        materials=["Concrete"],
        geometry=ElementGeometry(vertices=[0,0,0, 1,0,0, 0,1,0], faces=[0,1,2], vertex_count=3, face_count=1),
        bounding_box=b_common,
        quantity_estimates={"approx_volume_m3": 0.48}
    )
    col2 = BuildingElement(
        element_id="elem_col_b",
        source_global_id="GUID_COL_B_22222222",
        element_type="IfcColumn",
        name="Duplicate Clashing Column B",
        storey_id="storey_1",
        storey_name="Level 1",
        source_properties={"Pset_ColumnCommon": {"LoadBearing": True}},
        materials=["Concrete"],
        geometry=ElementGeometry(vertices=[0,0,0, 1,0,0, 0,1,0], faces=[0,1,2], vertex_count=3, face_count=1),
        bounding_box=b_common,  # Identical coordinates
        quantity_estimates={"approx_volume_m3": 0.48}
    )
    model = BuildingModelDetail(
        model_id="test-model-overlap",
        source_filename="test.ifc",
        import_timestamp="2026-10-30T00:00:00Z",
        storeys=[StoreyInfo(storey_id="storey_1", name="Level 1", element_count=2)],
        elements=[col1, col2],
        element_counts_by_type={"IfcColumn": 2},
        total_element_count=2
    )
    report = IntelligenceEngine.analyze_model(model)
    geom_findings = [f for f in report.findings if f.category == "geometry"]
    assert len(geom_findings) > 0
    assert any(f.severity == "High" for f in geom_findings)
    assert any("Potential Geometry Clashing" in f.title for f in geom_findings)

def test_intelligence_unusual_dimensions_rule():
    # Wall with 20mm thickness
    wall_thin = BuildingElement(
        element_id="elem_thin_wall",
        source_global_id="GUID_THIN_WALL_1111",
        element_type="IfcWall",
        name="Super Thin Wall",
        storey_id="storey_1",
        storey_name="Level 1",
        source_properties={"Pset_WallCommon": {"IsExternal": True, "ThermalTransmittance": 0.35}},
        materials=["Concrete"],
        geometry=ElementGeometry(vertices=[0,0,0, 1,0,0, 0,1,0], faces=[0,1,2], vertex_count=3, face_count=1),
        bounding_box=BoundingBox3D(min_x=0, min_y=0, min_z=0, max_x=10, max_y=0.02, max_z=3, center_x=5, center_y=0.01, center_z=1.5, width=10, height=0.02, depth=3),
        quantity_estimates={"approx_volume_m3": 0.6, "thickness": 0.02}
    )
    model = BuildingModelDetail(
        model_id="test-model-thin",
        source_filename="test.ifc",
        import_timestamp="2026-10-30T00:00:00Z",
        storeys=[StoreyInfo(storey_id="storey_1", name="Level 1", element_count=1)],
        elements=[wall_thin],
        element_counts_by_type={"IfcWall": 1},
        total_element_count=1
    )
    report = IntelligenceEngine.analyze_model(model)
    geom_findings = [f for f in report.findings if f.category == "geometry"]
    assert any("Substandard Wall Thickness" in f.title for f in geom_findings)
    assert any(f.severity == "Warning" for f in geom_findings)
