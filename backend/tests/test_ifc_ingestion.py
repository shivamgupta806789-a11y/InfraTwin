import io
import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.model_store import ModelStore

client = TestClient(app)

def test_list_models_returns_sample():
    response = client.get("/api/v1/models")
    assert response.status_code == 200
    models = response.json()
    assert isinstance(models, list)
    # The preloaded sample-office-twin should be in the list
    sample_models = [m for m in models if m["model_id"] == "sample-office-twin"]
    assert len(sample_models) == 1
    assert sample_models[0]["source_filename"] == "sample_office_building.ifc"
    assert sample_models[0]["total_element_count"] > 0

def test_get_model_detail():
    response = client.get("/api/v1/models/sample-office-twin")
    assert response.status_code == 200
    data = response.json()
    assert data["model_id"] == "sample-office-twin"
    assert "elements" in data
    assert len(data["elements"]) > 0
    # Check canonical properties
    first_elem = data["elements"][0]
    assert "element_id" in first_elem
    assert "element_type" in first_elem
    assert "source_global_id" in first_elem
    assert "geometry" in first_elem
    assert first_elem["geometry"]["format"] == "indexed_mesh"

def test_get_elements_with_pagination_and_filter():
    # Filter by element_type=IfcWall
    response = client.get("/api/v1/models/sample-office-twin/elements?element_type=IfcWall&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert all(e["element_type"] == "IfcWall" for e in data["items"])

def test_get_nonexistent_model_returns_404():
    response = client.get("/api/v1/models/non-existent-guid")
    assert response.status_code == 404

def test_import_unsupported_extension_rejected():
    file_content = b"Dummy CAD file content"
    response = client.post(
        "/api/v1/models/import/ifc",
        files={"file": ("drawing.dwg", io.BytesIO(file_content), "application/octet-stream")}
    )
    assert response.status_code == 400
    assert "Unsupported file format" in response.json()["detail"]

def test_import_malformed_header_rejected():
    # File with .ifc extension but missing ISO-10303-21 header
    fake_content = b"This is not a real STEP file header..."
    response = client.post(
        "/api/v1/models/import/ifc",
        files={"file": ("corrupt.ifc", io.BytesIO(fake_content), "application/octet-stream")}
    )
    assert response.status_code == 400
    assert "missing standard 'ISO-10303-21;' header" in response.json()["detail"]

def test_import_valid_ifc_file_fixture():
    fixture_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "app",
        "fixtures",
        "sample_office_building.ifc"
    )
    assert os.path.exists(fixture_path), "Fixture file must exist"

    with open(fixture_path, "rb") as f:
        file_bytes = f.read()

    response = client.post(
        "/api/v1/models/import/ifc",
        files={"file": ("test_upload.ifc", io.BytesIO(file_bytes), "application/octet-stream")}
    )
    assert response.status_code == 200
    summary = response.json()
    assert summary["import_status"] == "success"
    assert summary["total_elements"] > 0
    assert "IfcWall" in summary["element_counts_by_type"]
    assert "model_id" in summary

    # Verify newly imported model is now queryable
    new_model_id = summary["model_id"]
    get_res = client.get(f"/api/v1/models/{new_model_id}")
    assert get_res.status_code == 200
    assert get_res.json()["model_id"] == new_model_id

def test_import_empty_file_rejected():
    empty_content = b""
    response = client.post(
        "/api/v1/models/import/ifc",
        files={"file": ("empty.ifc", io.BytesIO(empty_content), "application/octet-stream")}
    )
    assert response.status_code == 400
    assert "empty (0 bytes)" in response.json()["detail"]

def test_import_corrupted_spf_syntax_rejected():
    # Valid header prefix, but corrupted unparseable STEP syntax
    corrupt_content = b"ISO-10303-21;\nHEADER;\nCORRUPT SYNTAX / UNCLOSED SECTION"
    response = client.post(
        "/api/v1/models/import/ifc",
        files={"file": ("corrupt_syntax.ifc", io.BytesIO(corrupt_content), "application/octet-stream")}
    )
    assert response.status_code == 422
    assert "IFC Parser Error" in response.json()["detail"]

def test_ifc_elements_contain_all_major_types_and_metadata():
    """Confirms extraction of walls, columns, beams, slabs, doors, windows, and storeys with properties."""
    response = client.get("/api/v1/models/sample-office-twin")
    assert response.status_code == 200
    model = response.json()
    
    # Verify storeys
    assert len(model["storeys"]) >= 2
    storey_names = [s["name"] for s in model["storeys"]]
    assert "Ground Floor" in storey_names
    assert "Roof Level" in storey_names

    # Verify building elements
    counts = model["element_counts_by_type"]
    assert "IfcWall" in counts and counts["IfcWall"] > 0
    assert "IfcColumn" in counts and counts["IfcColumn"] > 0
    assert "IfcBeam" in counts and counts["IfcBeam"] > 0
    assert "IfcSlab" in counts and counts["IfcSlab"] > 0
    assert "IfcDoor" in counts and counts["IfcDoor"] > 0
    assert "IfcWindow" in counts and counts["IfcWindow"] > 0

    # Verify preservation of IDs, names, dimensions, materials, and properties
    elements = model["elements"]
    for elem in elements:
        assert elem["element_id"].startswith("elem_")
        assert len(elem["name"]) > 0
        assert elem["source_global_id"] is not None
        assert elem["geometry"] is not None
        assert elem["geometry"]["vertex_count"] > 0
        assert elem["bounding_box"] is not None
        assert "approx_volume_m3" in elem["quantity_estimates"]

    # Verify specific materials and Psets
    wall = next(e for e in elements if e["element_type"] == "IfcWall")
    assert "C30/37 Reinforced Concrete" in wall["materials"]
    assert "Pset_WallCommon" in wall["source_properties"]

    beam = next(e for e in elements if e["element_type"] == "IfcBeam")
    assert "S355 Structural Steel" in beam["materials"]
    assert "Pset_BeamCommon" in beam["source_properties"]

def test_model_quality_distinguishes_missing_data_and_defects():
    """Confirms quality findings explicitly distinguish missing data from defects."""
    response = client.get("/api/v1/models/sample-office-twin/quality")
    assert response.status_code == 200
    quality = response.json()
    assert "data_completeness_ratio" in quality
    assert quality["data_completeness_ratio"] == 1.0

    # Ensure findings (if present) include clear descriptions and categories
    for f in quality["findings"]:
        assert any(tag in f["description"] for tag in ["[Missing BIM Data]", "[Geometry Defect]", "[Schema Violation]", "[Unsupported Entity]", "[Import Notice]"])

