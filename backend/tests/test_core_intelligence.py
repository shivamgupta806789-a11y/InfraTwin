import pytest
import numpy as np
import cv2
from shapely.geometry import Polygon

from app.models.environmental import GeoLocation, SiteContext, ClimateData
from app.models.floorplan import Point2D, Wall2D
from app.services.floorplan_processor import FloorplanProcessorService
from app.services.environmental_protection_service import (
    EnvironmentalProtectionEngine,
    EnvironmentalProtectionConstraint,
)
from app.services.dataset_registry import DatasetRegistryService, DatasetMetadata
from app.services.city_service import CityService
from app.services.sustainability_service import SustainabilityRecommendationService
from app.services.model_store import ModelStore


def test_opencv_distance_transform_wall_thickness():
    """Verify that OpenCV distance transform computes physical stroke thickness in meters."""
    # Create synthetic binary wall mask with an 8-pixel wide horizontal stroke
    mask = np.zeros((200, 200), dtype=np.uint8)
    mask[96:104, 20:180] = 255  # 8 px thickness
    dist_map = cv2.distanceTransform(mask, cv2.DIST_L2, 5)

    pixels_per_meter = 40.0  # 40 px = 1 meter -> 8 px should be 0.20m
    p1 = (20.0, 100.0)
    p2 = (180.0, 100.0)
    thickness_m, thickness_px = FloorplanProcessorService._measure_wall_thickness(
        p1, p2, dist_map, pixels_per_meter
    )

    assert thickness_px > 5.0
    assert 0.15 <= thickness_m <= 0.25


def test_room_color_and_material_extraction():
    """Verify that interior floor colors are extracted and mapped to architectural materials."""
    # Create a 200x200 BGR canvas: dark walls with a warm amber wood floor interior
    image_bgr = np.zeros((200, 200, 3), dtype=np.uint8)
    image_bgr[:, :] = (30, 30, 30)  # Dark background / walls

    # Warm hardwood floor fill (BGR: Blue=45, Green=110, Red=180)
    image_bgr[30:170, 30:170] = (45, 110, 180)

    # Contour around the interior
    contour = np.array([
        [[30, 30]], [[170, 30]], [[170, 170]], [[30, 170]]
    ], dtype=np.int32)

    color_hex, rgb, material, conf = FloorplanProcessorService._extract_room_color_and_material(
        image_bgr, contour, room_type="office", room_name="Office 101"
    )

    assert color_hex.startswith("#")
    assert rgb[0] > rgb[2]  # Red dominant over Blue
    assert material in ["hardwood", "ceramic_tile", "polished_concrete"]
    assert conf >= 0.70


def test_vegetation_courtyard_color_material():
    """Verify that green courtyard/garden fill is correctly classified as landscaped vegetation."""
    image_bgr = np.zeros((200, 200, 3), dtype=np.uint8)
    # Lush green fill (BGR: Blue=40, Green=160, Red=60)
    image_bgr[20:180, 20:180] = (40, 160, 60)

    contour = np.array([
        [[20, 20]], [[180, 20]], [[180, 180]], [[20, 180]]
    ], dtype=np.int32)

    color_hex, rgb, material, conf = FloorplanProcessorService._extract_room_color_and_material(
        image_bgr, contour, room_type="courtyard", room_name="Central Courtyard"
    )

    assert material == "landscaped_vegetation"
    assert conf >= 0.85
    assert rgb[1] > rgb[0] and rgb[1] > rgb[2]  # Green channel highest


def test_shapely_room_polygon_validation_and_repair():
    """Verify that self-intersecting / invalid room polygons are topologically repaired."""
    invalid_coords = [[0.0, 0.0], [5.0, 5.0], [0.0, 5.0], [5.0, 0.0], [0.0, 0.0]]
    raw_poly = Polygon(invalid_coords)
    assert not raw_poly.is_valid

    from shapely.validation import make_valid
    repaired = make_valid(raw_poly)
    assert repaired.is_valid


def test_wall_snapping_and_orphan_detection():
    """Verify that near wall endpoints snap and disconnected walls are flagged in report."""
    walls = [
        # Wall 1: (0, 0) to (5, 0)
        Wall2D(id="W1", start=Point2D(x=0.0, y=0.0), end=Point2D(x=5.0, y=0.0), thickness_m=0.2),
        # Wall 2: starts slightly disconnected at (5.08, 0.02) within 0.15m tolerance
        Wall2D(id="W2", start=Point2D(x=5.08, y=0.02), end=Point2D(x=5.08, y=4.0), thickness_m=0.2),
        # Wall 3: completely isolated floating wall
        Wall2D(id="W3", start=Point2D(x=50.0, y=50.0), end=Point2D(x=54.0, y=50.0), thickness_m=0.2),
    ]

    report = FloorplanProcessorService._validate_and_repair_geometry(
        walls=walls,
        rooms=[],
        doors=[],
        windows=[],
        pixels_per_meter=40.0,
        snap_tol_m=0.15
    )

    assert report["total_walls"] == 3
    # Check that W1 and W2 were snapped together
    assert abs(walls[0].end.x - walls[1].start.x) < 0.001
    assert abs(walls[0].end.y - walls[1].start.y) < 0.001

    # W3 should be flagged as DISCONNECTED orphan
    w3 = next(w for w in walls if w.id == "W3")
    assert w3.validation_status == "DISCONNECTED"
    assert len(w3.validation_errors) > 0


def test_environmental_protection_engine_rules():
    """Verify all 5 ecological protection constraints fire with concrete non-destructive alternatives."""
    loc = GeoLocation(latitude=28.6139, longitude=77.2090, place_name="Urban Green Field")
    site_ctx = SiteContext(
        urban_density="Moderate Urban",
        nearby_vegetation_pct=28.0,  # > 12% triggers PROT-TREE-01
        nearby_water_bodies=["River Yamuna Tributary (12m west)"],  # triggers PROT-WATER-02
        land_use_classification="Open Natural Land",
        terrain_slope_pct=2.5,
        urban_heat_island_risk="Moderate",
        data_source="OpenStreetMap & NASA POWER"
    )
    climate = ClimateData(
        climate_zone="Cwa (Humid Subtropical)",
        mean_temp_c=25.0,
        max_temp_c=42.0,
        min_temp_c=8.0,
        relative_humidity_pct=60.0,
        annual_rainfall_mm=1250.0,  # triggers PROT-DRAIN-03
        solar_radiation_kwh_m2_day=5.0,
        peak_solar_radiation_mj_m2=22.0,
        dominant_wind_speed_kmh=12.5,
        dominant_wind_direction_deg=270.0,
        dominant_wind_cardinal="W",
        elevation_m=215.0,
        data_source="Open-Meteo Historic Reanalysis",
        retrieval_timestamp="2026-10-31T00:00:00Z"
    )

    constraints = EnvironmentalProtectionEngine.evaluate_protection_constraints(
        location=loc,
        site_context=site_ctx,
        climate=climate,
        building_footprint_w_m=18.0,
        building_footprint_d_m=14.0
    )

    constraint_ids = [c.constraint_id for c in constraints]
    assert "PROT-TREE-01" in constraint_ids
    assert "PROT-WATER-02" in constraint_ids
    assert "PROT-DRAIN-03" in constraint_ids

    # Verify that alternatives do NOT recommend clear-cutting
    tree_constraint = next(c for c in constraints if c.constraint_id == "PROT-TREE-01")
    assert len(tree_constraint.proposed_alternatives) >= 2
    strategies = [alt.strategy for alt in tree_constraint.proposed_alternatives]
    assert "footprint_shift" in strategies
    assert "courtyard_notch" in strategies

    water_constraint = next(c for c in constraints if c.constraint_id == "PROT-WATER-02")
    assert water_constraint.severity == "critical_protection"
    assert water_constraint.proposed_alternatives[0].buffer_distance_achieved_m >= 15.0


def test_dataset_registry_governance_and_buckets():
    """Verify that DatasetRegistryService contains all datasets across 4 strict usage buckets."""
    all_datasets = DatasetRegistryService.list_all_datasets()
    assert len(all_datasets) >= 10

    ml_datasets = DatasetRegistryService.filter_by_bucket("A_supervised_ml")
    gis_datasets = DatasetRegistryService.filter_by_bucket("B_direct_gis_analysis")
    val_datasets = DatasetRegistryService.filter_by_bucket("C_model_validation")
    sim_datasets = DatasetRegistryService.filter_by_bucket("D_simulation_data")

    assert len(ml_datasets) >= 2
    assert len(gis_datasets) >= 4
    assert len(val_datasets) >= 2
    assert len(sim_datasets) >= 1

    # Verify metadata completeness
    for d in all_datasets:
        assert d.dataset_id
        assert d.name
        assert d.geographic_coverage
        assert d.source
        assert len(d.limitations) > 0

    # Query helper
    nasa = DatasetRegistryService.get_dataset("DS-09-NASA-POWER")
    assert nasa is not None
    assert "Solar" in nasa.name or "NASA" in nasa.name

    # Governance summary
    gov = DatasetRegistryService.get_governance_summary()
    assert gov["total_candidate_datasets"] >= 10
    assert len(gov["governance_rules"]) >= 4


def test_city_service_geojson_district_ingestion():
    """Verify that GeoJSON building polygons are ingested into the canonical hierarchy."""
    geojson_payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "id": "BLD-GIS-TEST-01",
                    "name": "Green Eco-Lab 1",
                    "building": "commercial",
                    "height": 14.0,
                    "building:levels": 4
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [77.2090, 28.6139],
                            [77.2092, 28.6139],
                            [77.2092, 28.6141],
                            [77.2090, 28.6141],
                            [77.2090, 28.6139]
                        ]
                    ]
                }
            },
            {
                "type": "Feature",
                "properties": {
                    "id": "BLD-GIS-TEST-02",
                    "name": "Eco Residential Flats",
                    "building": "residential",
                    "height": 10.5,
                    "building:levels": 3
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [77.2094, 28.6139],
                            [77.2096, 28.6139],
                            [77.2096, 28.6141],
                            [77.2094, 28.6141],
                            [77.2094, 28.6139]
                        ]
                    ]
                }
            }
        ]
    }

    updated_city = CityService.ingest_geojson_district(
        geojson_data=geojson_payload,
        district_name="Ingested Eco District",
        district_type="Innovation Hub"
    )

    district_names = [d.name for d in updated_city.districts]
    assert "Ingested Eco District" in district_names

    imported_dist = next(d for d in updated_city.districts if d.name == "Ingested Eco District")
    assert len(imported_dist.sites) == 1
    assert len(imported_dist.sites[0].buildings) == 2

    b1 = imported_dist.sites[0].buildings[0]
    assert b1.building_id == "BLD-GIS-TEST-01"
    assert b1.storeys_count == 4
    assert b1.height_m == 14.0
    assert b1.footprint_area_m2 > 10.0


def test_unified_sustainability_recommendation_engine():
    """Verify that SustainabilityRecommendationService produces evidence-backed recommendations with ecological protection."""
    ModelStore.initialize_with_sample_model()

    report = SustainabilityRecommendationService.evaluate_comprehensive_intelligence(
        target_entity_id="sample-office-twin",
        level="building",
        latitude=28.6139,
        longitude=77.2090
    )

    assert report.target_entity_id == "sample-office-twin"
    assert len(report.recommendations) >= 5

    categories = [r.category for r in report.recommendations]
    assert "environmental_sustainability" in categories
    assert "geotechnical_suitability" in categories

    # Verify structural audit recommendation format
    str_recs = [r for r in report.recommendations if r.id == "REC-STR-001"]
    if str_recs:
        assert str_recs[0].priority == "critical"
        assert "licensed" in str_recs[0].proposed_intervention.lower() or "structural" in str_recs[0].proposed_intervention.lower()
