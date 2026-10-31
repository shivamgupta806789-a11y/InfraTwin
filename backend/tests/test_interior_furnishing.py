import io
import pytest
from fastapi.testclient import TestClient
import numpy as np

from app.main import app
from app.models.furniture import (
    Dimensions3D,
    Vector3D,
    FurnitureUpdateRequest,
    FurnitureAddRequest,
)
from app.models.digital_twin import BuildingModelDetail, BuildingElement, ElementGeometry, BoundingBox3D, StoreyInfo
from app.services.interior_furnishing_service import InteriorFurnishingService
from app.services.floorplan_processor import FloorplanProcessorService
from app.services.model_store import ModelStore
from app.services.sustainability_service import SustainabilityRecommendationService

client = TestClient(app)


def make_bbox(min_x: float, min_y: float, min_z: float, max_x: float, max_y: float, max_z: float) -> BoundingBox3D:
    return BoundingBox3D(
        min_x=min_x,
        min_y=min_y,
        min_z=min_z,
        max_x=max_x,
        max_y=max_y,
        max_z=max_z,
        center_x=(min_x + max_x) / 2.0,
        center_y=(min_y + max_y) / 2.0,
        center_z=(min_z + max_z) / 2.0,
        width=max_x - min_x,
        height=max_y - min_y,
        depth=max_z - min_z,
    )


def create_mock_building_model(model_id: str = "mock-twin-furn") -> BuildingModelDetail:
    """Creates a sample BuildingModelDetail with 2 storeys and IfcSpace rooms."""
    storeys = [
        StoreyInfo(storey_id="storey_0", name="Level 1", elevation_m=0.0, height_m=3.0, element_count=4),
        StoreyInfo(storey_id="storey_1", name="Level 2", elevation_m=3.0, height_m=3.0, element_count=4),
    ]

    # Create 2 rooms on Level 1
    # Room 1: Master Bedroom (5m x 4m)
    r1_verts = [
        0.0, 0.0, 0.0,
        5.0, 0.0, 0.0,
        5.0, 0.0, 4.0,
        0.0, 0.0, 4.0,
        0.0, 3.0, 0.0,
        5.0, 3.0, 0.0,
        5.0, 3.0, 4.0,
        0.0, 3.0, 4.0,
    ]
    r1_faces = [0, 1, 2, 0, 2, 3]

    # Room 2: Living Room (6m x 5m)
    r2_verts = [
        5.0, 0.0, 0.0,
        11.0, 0.0, 0.0,
        11.0, 0.0, 5.0,
        5.0, 0.0, 5.0,
        5.0, 3.0, 0.0,
        11.0, 3.0, 0.0,
        11.0, 3.0, 5.0,
        5.0, 3.0, 5.0,
    ]
    r2_faces = [0, 1, 2, 0, 2, 3]

    # Door on Room 1 at (2.5, 0.0)
    d1_verts = [2.0, 0.0, 0.0, 3.0, 0.0, 0.0, 3.0, 2.1, 0.0, 2.0, 2.1, 0.0]

    elements = [
        BuildingElement(
            element_id="space_f0_bedroom",
            source_global_id="GUID_R1",
            element_type="IfcSpace",
            name="Master Bedroom 101",
            storey_id="storey_0",
            geometry=ElementGeometry(format="indexed_mesh", vertices=r1_verts, faces=r1_faces, vertex_count=8, face_count=2),
            bounding_box=make_bbox(min_x=0.0, min_y=0.0, min_z=0.0, max_x=5.0, max_y=3.0, max_z=4.0),
            source_properties={"Pset_SpaceCommon": {"RoomType": "bedroom", "NetFloorArea": 20.0}}
        ),
        BuildingElement(
            element_id="space_f0_living",
            source_global_id="GUID_R2",
            element_type="IfcSpace",
            name="Open Living Lounge",
            storey_id="storey_0",
            geometry=ElementGeometry(format="indexed_mesh", vertices=r2_verts, faces=r2_faces, vertex_count=8, face_count=2),
            bounding_box=make_bbox(min_x=5.0, min_y=0.0, min_z=0.0, max_x=11.0, max_y=3.0, max_z=5.0),
            source_properties={"Pset_SpaceCommon": {"RoomType": "living", "NetFloorArea": 30.0}}
        ),
        BuildingElement(
            element_id="door_entrance",
            source_global_id="GUID_D1",
            element_type="IfcDoor",
            name="Entrance Door",
            storey_id="storey_0",
            geometry=ElementGeometry(format="indexed_mesh", vertices=d1_verts, faces=[0, 1, 2], vertex_count=4, face_count=1),
            bounding_box=make_bbox(min_x=2.0, min_y=0.0, min_z=0.0, max_x=3.0, max_y=2.1, max_z=0.2),
            source_properties={}
        )
    ]

    model = BuildingModelDetail(
        model_id=model_id,
        source_filename="test_office.ifc",
        schema_version="IFC4",
        building_name="Test Twin Building",
        import_timestamp="2026-10-31T00:00:00Z",
        summary_counts={"IfcSpace": 2, "IfcDoor": 1},
        bounding_box=make_bbox(min_x=0.0, min_y=0.0, min_z=0.0, max_x=11.0, max_y=6.0, max_z=5.0),
        storeys=storeys,
        elements=elements
    )
    ModelStore.save_model(model)
    return model


def test_classify_room_types_keywords_and_aspect_ratio():
    """Verifies room classification from keywords and geometric aspect ratio."""
    # Keyword tests
    rtype, conf = InteriorFurnishingService.classify_room_type("Master Bedroom", 18.0)
    assert rtype == "bedroom"
    assert conf >= 0.90

    rtype, conf = InteriorFurnishingService.classify_room_type("Executive Boardroom Conf", 35.0)
    assert rtype == "conference"
    assert conf >= 0.90

    rtype, conf = InteriorFurnishingService.classify_room_type("Kitchenette / Pantry", 12.0)
    assert rtype == "kitchen"
    assert conf >= 0.90

    rtype, conf = InteriorFurnishingService.classify_room_type("Restroom WC", 4.0)
    assert rtype == "bathroom"
    assert conf >= 0.90

    # Geometric corridor test: long narrow corridor
    rtype, conf = InteriorFurnishingService.classify_room_type("", 15.0, aspect_ratio=4.5)
    assert rtype == "corridor"

    # Geometric small bath test
    rtype, conf = InteriorFurnishingService.classify_room_type("", 3.5, aspect_ratio=1.2)
    assert rtype == "bathroom"


def test_generate_furnishing_plan_from_building_model():
    """Tests deterministic furniture generation on a mock building model."""
    model = create_mock_building_model("test-model-furn-01")
    plan = InteriorFurnishingService.generate_furnishing_plan_for_model(model, force_regenerate=True)

    assert plan.model_id == "test-model-furn-01"
    assert plan.total_furniture_count > 0
    assert len(plan.room_profiles) == 2

    # Bedroom profile check
    bed_profile = next((rp for rp in plan.room_profiles if "bedroom" in rp.room_id), None)
    assert bed_profile is not None
    assert bed_profile.room_type == "bedroom"
    assert len(bed_profile.items) >= 1

    # Check for bed category
    categories = [it.category for it in bed_profile.items]
    assert "bed" in categories


def test_door_clearance_preservation():
    """Ensures no furniture item collides with the door clearance zone."""
    model = create_mock_building_model("test-model-clearance")
    plan = InteriorFurnishingService.generate_furnishing_plan_for_model(model, force_regenerate=True)

    for item in plan.all_items:
        if item.room_id == "space_f0_bedroom":
            pos = item.position_m
            # Door is along bottom wall (Z=0.0) between X=2.0 and X=3.0. Clearance buffer is 1.0m.
            if 1.5 <= pos.x <= 3.5:
                assert pos.z > 0.8, f"Item {item.name} placed too close to door clearance zone at z={pos.z}"


def test_furniture_update_item():
    """Tests updating a furniture item's position, rotation, and material."""
    model = create_mock_building_model("test-model-update")
    plan = InteriorFurnishingService.generate_furnishing_plan_for_model(model, force_regenerate=True)

    first_item = plan.all_items[0]
    update_req = FurnitureUpdateRequest(
        position_m=Vector3D(x=2.2, y=0.0, z=2.2),
        rotation_deg=90.0,
        material="walnut",
        color_hex="#5c3a21"
    )

    updated = InteriorFurnishingService.update_furniture_item(
        model_id="test-model-update",
        furniture_id=first_item.id,
        update=update_req
    )

    assert updated is not None
    assert updated.position_m.x == 2.2
    assert updated.rotation_deg == 90.0
    assert updated.material == "walnut"
    assert updated.status == "USER_MODIFIED"


def test_furniture_remove_and_add_item():
    """Tests removing an item and manually adding a new one."""
    model = create_mock_building_model("test-model-mod")
    plan = InteriorFurnishingService.generate_furnishing_plan_for_model(model, force_regenerate=True)

    initial_count = plan.total_furniture_count
    item_to_remove = plan.all_items[0].id

    # Remove item
    removed = InteriorFurnishingService.remove_furniture_item("test-model-mod", item_to_remove)
    assert removed is True
    assert len(plan.all_items) == initial_count - 1

    # Add item
    add_req = FurnitureAddRequest(
        room_id="space_f0_living",
        storey_id="storey_0",
        category="armchair",
        name="Custom Armchair",
        position_m=Vector3D(x=8.0, y=0.0, z=3.0),
        rotation_deg=45.0
    )
    new_item = InteriorFurnishingService.add_furniture_item("test-model-mod", add_req)
    assert new_item is not None
    assert new_item.name == "Custom Armchair"
    assert new_item.category == "armchair"
    assert len(plan.all_items) == initial_count


def test_dxf_ingestion_and_rasterization():
    """Tests DXF format parsing in FloorplanProcessorService."""
    import ezdxf
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    msp.add_line((0, 0), (12, 0))
    msp.add_line((12, 0), (12, 10))
    msp.add_line((12, 10), (0, 10))
    msp.add_line((0, 10), (0, 0))

    stream = io.StringIO()
    doc.write(stream)
    dxf_bytes = stream.getvalue().encode("utf-8")

    img_bgr, detected_type = FloorplanProcessorService.load_drawing_to_bgr(
        file_bytes=dxf_bytes,
        filename="test_floor.dxf"
    )

    assert detected_type == "dxf"
    assert isinstance(img_bgr, np.ndarray)
    assert img_bgr.shape[0] > 1000 and img_bgr.shape[1] > 1000


def test_furniture_routes_api():
    """Tests FastAPI router endpoints for furniture plan and catalog."""
    create_mock_building_model("test-api-furn")

    # 1. Catalog
    res_cat = client.get("/api/v1/furniture/catalog")
    assert res_cat.status_code == 200
    cat_data = res_cat.json()
    assert "categories" in cat_data
    assert len(cat_data["categories"]) > 10

    # 2. Plan
    res_plan = client.get("/api/v1/furniture/plan/test-api-furn")
    assert res_plan.status_code == 200
    plan_data = res_plan.json()
    assert plan_data["model_id"] == "test-api-furn"
    assert plan_data["total_furniture_count"] > 0

    # 3. Patch item
    first_item_id = plan_data["all_items"][0]["id"]
    res_patch = client.patch(
        f"/api/v1/furniture/plan/test-api-furn/item/{first_item_id}",
        json={"rotation_deg": 180.0}
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["rotation_deg"] == 180.0


def test_sustainability_service_incorporates_interior_features():
    """Verifies sustainability recommendation REC-INDOOR-010 is produced incorporating interior features."""
    create_mock_building_model("test-sust-furn")
    # Pre-generate furniture plan
    client.get("/api/v1/furniture/plan/test-sust-furn")

    report = SustainabilityRecommendationService.evaluate_comprehensive_intelligence(
        target_entity_id="test-sust-furn",
        level="building",
        latitude=28.6139,
        longitude=77.2090
    )

    assert report is not None
    rec_ids = [r.id for r in report.recommendations]
    assert "REC-INDOOR-010" in rec_ids

    indoor_rec = next(r for r in report.recommendations if r.id == "REC-INDOOR-010")
    assert "room zones" in indoor_rec.detected_condition.lower()
    assert "DS-09-NASA-POWER" in indoor_rec.contributing_datasets
