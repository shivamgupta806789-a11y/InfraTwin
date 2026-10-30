import io
import cv2
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from app.services.floorplan_processor import FloorplanProcessorService
from app.services.floorplan_to_3d_service import FloorplanTo3dService
from app.services.model_store import ModelStore

client = TestClient(app)


def create_synthetic_floorplan_bytes() -> bytes:
    """Creates a synthetic black-and-white architectural floor plan image in PNG format."""
    img = np.ones((700, 900, 3), dtype=np.uint8) * 255
    # Exterior walls
    cv2.rectangle(img, (80, 80), (820, 620), (0, 0, 0), 12)
    # Interior dividing wall
    cv2.line(img, (450, 80), (450, 620), (0, 0, 0), 10)
    # Door opening in interior wall
    cv2.line(img, (450, 300), (450, 380), (255, 255, 255), 14)
    # Window opening in south wall
    cv2.line(img, (200, 620), (320, 620), (255, 255, 255), 14)

    success, buf = cv2.imencode(".png", img)
    assert success
    return buf.tobytes()


def create_synthetic_pdf_bytes() -> bytes:
    """Creates a synthetic 1-page PDF floor plan."""
    im = Image.new("RGB", (600, 450), color=(255, 255, 255))
    # Draw simple black rectangle
    arr = np.array(im)
    cv2.rectangle(arr, (50, 50), (550, 400), (0, 0, 0), 8)
    pil_img = Image.fromarray(arr)
    pdf_buf = io.BytesIO()
    pil_img.save(pdf_buf, format="PDF")
    return pdf_buf.getvalue()


def test_floorplan_processor_service_synthetic():
    png_bytes = create_synthetic_floorplan_bytes()
    img_bgr, ftype = FloorplanProcessorService.load_drawing_to_bgr(png_bytes, "test_plan.png")
    assert ftype == "png"
    assert img_bgr.shape == (700, 900, 3)

    res = FloorplanProcessorService.extract_geometry(
        img_bgr=img_bgr,
        filename="test_plan.png",
        file_type="png",
        known_dimension_m=16.0,
    )

    assert res.drawing_id.startswith("plan_")
    assert len(res.floorplan.walls) > 0
    assert len(res.floorplan.doors) > 0
    assert len(res.floorplan.windows) > 0
    assert len(res.floorplan.rooms) > 0
    assert res.floorplan.scale.pixels_per_meter > 0
    assert res.preview_overlay_base64.startswith("data:image/png;base64,")
    assert res.summary["wall_count"] == len(res.floorplan.walls)


def test_floorplan_processor_pdf_rendering():
    pdf_bytes = create_synthetic_pdf_bytes()
    img_bgr, ftype = FloorplanProcessorService.load_drawing_to_bgr(pdf_bytes, "test_plan.pdf")
    assert ftype == "pdf"
    assert img_bgr.shape[0] > 0 and img_bgr.shape[1] > 0

    res = FloorplanProcessorService.extract_geometry(
        img_bgr=img_bgr,
        filename="test_plan.pdf",
        file_type="pdf",
        known_dimension_m=12.0,
    )
    assert len(res.floorplan.walls) > 0
    assert res.preview_overlay_base64.startswith("data:image/png;base64,")


def test_3d_generation_service_roof_types():
    png_bytes = create_synthetic_floorplan_bytes()
    img_bgr, _ = FloorplanProcessorService.load_drawing_to_bgr(png_bytes, "plan.png")
    extraction = FloorplanProcessorService.extract_geometry(img_bgr, "plan.png", "png", known_dimension_m=15.0)

    # Test flat roof
    model_flat, summary_flat = FloorplanTo3dService.generate_building_model(
        floorplan=extraction.floorplan,
        floors=2,
        floor_height_m=3.0,
        roof_type="flat",
        building_name="Flat Roof Model",
    )
    assert model_flat.source_type == "floorplan"
    assert model_flat.total_element_count > 0
    assert len(model_flat.storeys) == 2
    assert summary_flat.import_status == "success"

    # Test parapet roof
    model_parapet, summary_parapet = FloorplanTo3dService.generate_building_model(
        floorplan=extraction.floorplan,
        floors=3,
        floor_height_m=3.5,
        roof_type="parapet",
        building_name="Parapet Model",
    )
    assert len(model_parapet.storeys) == 3
    assert any(e.element_type == "IfcRoof" for e in model_parapet.elements)

    # Test gable roof
    model_gable, summary_gable = FloorplanTo3dService.generate_building_model(
        floorplan=extraction.floorplan,
        floors=1,
        floor_height_m=2.8,
        roof_type="gable",
        building_name="Gable Model",
    )
    assert len(model_gable.storeys) == 1
    assert model_gable.bounding_box.width > 0
    assert model_gable.bounding_box.height > 0
    assert model_gable.bounding_box.depth > 0


def test_api_extract_endpoint_success():
    png_bytes = create_synthetic_floorplan_bytes()
    response = client.post(
        "/api/v1/floorplan/extract",
        files={"file": ("drawing.png", png_bytes, "image/png")},
        data={"known_dimension_m": "18.0"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "floorplan" in data
    assert "preview_overlay_base64" in data
    assert len(data["floorplan"]["walls"]) > 0
    assert data["summary"]["wall_count"] > 0


def test_api_extract_endpoint_empty_file():
    response = client.post(
        "/api/v1/floorplan/extract",
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_api_extract_endpoint_unsupported_format():
    response = client.post(
        "/api/v1/floorplan/extract",
        files={"file": ("notes.txt", b"hello world", "text/plain")},
    )
    assert response.status_code == 400
    assert "unsupported" in response.json()["detail"].lower()


def test_api_generate_3d_endpoint_and_reports():
    png_bytes = create_synthetic_floorplan_bytes()
    # 1. Extract
    extract_resp = client.post(
        "/api/v1/floorplan/extract",
        files={"file": ("drawing.png", png_bytes, "image/png")},
        data={"known_dimension_m": "16.0"},
    )
    assert extract_resp.status_code == 200
    floorplan_data = extract_resp.json()["floorplan"]

    # 2. Generate 3D
    gen_payload = {
        "floorplan": floorplan_data,
        "floors": 2,
        "floor_height_m": 3.0,
        "building_type": "Commercial",
        "roof_type": "parapet",
        "building_name": "Automated Test Digital Twin",
    }
    gen_resp = client.post("/api/v1/floorplan/generate-3d", json=gen_payload)
    assert gen_resp.status_code == 200
    summary = gen_resp.json()
    model_id = summary["model_id"]
    assert summary["import_status"] == "success"
    assert summary["total_elements"] > 0

    # 3. Retrieve model detail from ModelStore
    model_resp = client.get(f"/api/v1/models/{model_id}")
    assert model_resp.status_code == 200
    model_detail = model_resp.json()
    assert model_detail["model_id"] == model_id
    assert model_detail["source_type"] == "floorplan"
    assert len(model_detail["elements"]) > 0

    # 4. Check that Quality, ESG, and Intelligence audits work seamlessly on this model
    q_resp = client.get(f"/api/v1/models/{model_id}/quality")
    assert q_resp.status_code == 200
    assert "data_completeness_ratio" in q_resp.json()

    esg_resp = client.get(f"/api/v1/models/{model_id}/esg")
    assert esg_resp.status_code == 200
    assert "status_counts" in esg_resp.json()

    intel_resp = client.get(f"/api/v1/models/{model_id}/intelligence")
    assert intel_resp.status_code == 200
    assert intel_resp.json()["total_elements"] == model_detail["total_element_count"]


def test_interior_spaces_and_relationships_generation():
    """Validates that IfcSpace interior rooms with connected doors and windows are synthesized."""
    png_bytes = create_synthetic_floorplan_bytes()
    img_bgr, _ = FloorplanProcessorService.load_drawing_to_bgr(png_bytes, "plan.png")
    extraction = FloorplanProcessorService.extract_geometry(img_bgr, "plan.png", "png", known_dimension_m=16.0)

    model_detail, _ = FloorplanTo3dService.generate_building_model(
        floorplan=extraction.floorplan,
        floors=2,
        floor_height_m=3.0,
        building_name="Interior Space Test",
    )

    spaces = [e for e in model_detail.elements if e.element_type == "IfcSpace"]
    assert len(spaces) >= 2, "Expected IfcSpace elements for every floor storey"

    ground_space = spaces[0]
    assert ground_space.geometry is not None
    assert len(ground_space.geometry.vertices) >= 24  # 8 vertices * 3 coords
    assert len(ground_space.geometry.faces) >= 36     # 12 triangles * 3 indices
    assert ground_space.source_properties["Area_m2"] > 0
    assert "ConnectedDoors" in ground_space.source_properties
    assert "AssociatedWindows" in ground_space.source_properties
    assert len(ground_space.relationships.get("connected_doors", [])) > 0
    assert len(ground_space.relationships.get("associated_windows", [])) > 0

