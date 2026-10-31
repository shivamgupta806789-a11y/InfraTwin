import os
import threading
from typing import Dict, List, Optional, Tuple
from app.models.digital_twin import (
    BuildingModel,
    BuildingModelDetail,
    BuildingElement,
    ModelQualityReport,
    EsgAssessmentReport,
    BuildingIntelligenceReport,
    ProjectLocation,
)
from app.services.ifc_parser import IfcParserService
from app.services.quality_engine import QualityEngine
from app.services.esg_engine import EsgEngine
from app.services.intelligence_engine import IntelligenceEngine

class ModelStore:
    _lock = threading.Lock()
    _models: Dict[str, BuildingModelDetail] = {}
    _parser_warnings: Dict[str, List[str]] = {}
    _quality_cache: Dict[str, ModelQualityReport] = {}
    _intelligence_cache: Dict[str, BuildingIntelligenceReport] = {}

    @classmethod
    def initialize_with_sample_model(cls):
        """Initializes store with pre-packaged sample IFC digital twin if available."""
        sample_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "fixtures",
            "sample_office_building.ifc"
        )
        if os.path.exists(sample_path):
            try:
                model, warnings, _ = IfcParserService.parse_ifc_file(
                    sample_path,
                    "sample_office_building.ifc",
                    model_id="sample-office-twin"
                )
                cls.save_model(model, warnings)
            except Exception as e:
                print(f"Notice: Could not preload sample IFC model: {e}")

    @classmethod
    def save_model(cls, model: BuildingModelDetail, warnings: List[str] = None):
        with cls._lock:
            # Ensure model has associated confirmed project location
            if model.project_location is None:
                if model.georeferencing and model.georeferencing.get("ref_latitude") is not None:
                    model.project_location = ProjectLocation(
                        address=model.site_name or model.project_name or "Project Site (IFC Georeferenced)",
                        latitude=float(model.georeferencing["ref_latitude"]),
                        longitude=float(model.georeferencing["ref_longitude"]),
                        elevation_m=float(model.georeferencing.get("ref_elevation") or 216.0),
                        is_confirmed=True,
                        climate_zone="Composite / Semi-Arid",
                        georeferenced_source="ifc_site",
                        local_to_world_transform=model.georeferencing.get("map_conversion") or {}
                    )
                else:
                    model.project_location = ProjectLocation(
                        address="New Delhi, Delhi, India",
                        latitude=28.6139,
                        longitude=77.2090,
                        elevation_m=216.0,
                        is_confirmed=True,
                        climate_zone="Composite / Semi-Arid (Hot summers, Monsoon rains)",
                        georeferenced_source="default_project",
                        local_to_world_transform={
                            "local_origin": [0.0, 0.0, 0.0],
                            "world_origin": [28.6139, 77.2090],
                            "crs": "EPSG:4326 (WGS84) / EPSG:32643 (UTM Zone 43N)"
                        }
                    )

            cls._models[model.model_id] = model
            cls._parser_warnings[model.model_id] = warnings or []
            # Invalidate cached reports
            cls._quality_cache.pop(model.model_id, None)
            cls._intelligence_cache.pop(model.model_id, None)

    @classmethod
    def list_models(cls) -> List[BuildingModel]:
        with cls._lock:
            models_summary: List[BuildingModel] = []
            for m in cls._models.values():
                summary = BuildingModel(
                    model_id=m.model_id,
                    source_type=m.source_type,
                    source_filename=m.source_filename,
                    import_timestamp=m.import_timestamp,
                    schema_version=m.schema_version,
                    units=m.units,
                    project_name=m.project_name,
                    site_name=m.site_name,
                    building_name=m.building_name,
                    project_location=m.project_location,
                    storeys=m.storeys,
                    element_counts_by_type=m.element_counts_by_type,
                    total_element_count=m.total_element_count,
                    available_properties=m.available_properties,
                    missing_data=m.missing_data,
                    bounding_box=m.bounding_box,
                    georeferencing=m.georeferencing,
                    provenance_metadata=m.provenance_metadata
                )
                models_summary.append(summary)
            return models_summary

    @classmethod
    def set_model_location(cls, model_id: str, location: ProjectLocation) -> Optional[BuildingModelDetail]:
        with cls._lock:
            model = cls._models.get(model_id)
            if model:
                model.project_location = location
                # Invalidate cached intelligence reports
                cls._intelligence_cache.pop(model_id, None)
            return model

    @classmethod
    def get_model_location(cls, model_id: str) -> Optional[ProjectLocation]:
        with cls._lock:
            model = cls._models.get(model_id)
            if model and model.project_location:
                return model.project_location
            return ProjectLocation()

    @classmethod
    def get_model(cls, model_id: str) -> Optional[BuildingModelDetail]:
        with cls._lock:
            return cls._models.get(model_id)

    @classmethod
    def get_elements(
        cls,
        model_id: str,
        element_type: Optional[str] = None,
        storey_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[BuildingElement], int]:
        with cls._lock:
            model = cls._models.get(model_id)
            if not model:
                return ([], 0)

            filtered = model.elements
            if element_type:
                filtered = [e for e in filtered if e.element_type.lower() == element_type.lower()]
            if storey_id:
                filtered = [e for e in filtered if e.storey_id == storey_id]

            total_matching = len(filtered)
            paginated = filtered[offset : offset + limit]
            return (paginated, total_matching)

    @classmethod
    def get_quality_report(cls, model_id: str) -> Optional[ModelQualityReport]:
        with cls._lock:
            if model_id in cls._quality_cache:
                return cls._quality_cache[model_id]

            model = cls._models.get(model_id)
            if not model:
                return None

            warnings = cls._parser_warnings.get(model_id, [])
            report = QualityEngine.evaluate_model_quality(model, warnings)
            cls._quality_cache[model_id] = report
            return report

    @classmethod
    def get_intelligence_report(cls, model_id: str) -> Optional[BuildingIntelligenceReport]:
        with cls._lock:
            if model_id in cls._intelligence_cache:
                return cls._intelligence_cache[model_id]

            model = cls._models.get(model_id)
            if not model:
                return None

            warnings = cls._parser_warnings.get(model_id, [])
            report = IntelligenceEngine.analyze_model(model, warnings)
            cls._intelligence_cache[model_id] = report
            return report

    @classmethod
    def get_esg_report(
        cls,
        model_id: str,
        annual_kwh: Optional[float] = None
    ) -> Optional[EsgAssessmentReport]:
        with cls._lock:
            model = cls._models.get(model_id)
            if not model:
                return None

            return EsgEngine.evaluate_model_esg(model, annual_electricity_kwh=annual_kwh)

    @classmethod
    def get_parametric_baseline(cls, model_id: str) -> Optional[Dict[str, Any]]:
        with cls._lock:
            model = cls._models.get(model_id)
            if not model:
                return None

            bbox = model.bounding_box
            width_m = round(bbox.width if bbox else 12.0, 2)
            length_m = round(bbox.depth if bbox else 16.0, 2)
            total_height_m = round(bbox.height if bbox else 6.0, 2)

            floors = max(1, len(model.storeys))
            floor_height_m = round(total_height_m / floors, 2) if floors > 0 else 3.0

            # Count exterior/visible windows
            window_count = 0
            for elem in model.elements:
                if "window" in elem.element_type.lower():
                    window_count += 1
            if window_count == 0:
                window_count = max(4, floors * 8)

            roof_area_m2 = round(width_m * length_m, 2)
            gross_floor_area_m2 = round(roof_area_m2 * floors, 2)
            total_wall_area_m2 = round(2 * (width_m + length_m) * total_height_m, 2)

            return {
                "model_id": model.model_id,
                "building_id": model.building_id or model.model_id,
                "building_name": model.building_name or model.project_name or "BIM Digital Twin",
                "source_type": model.source_type,
                "source_filename": model.source_filename,
                "schema_version": model.schema_version,
                "version": "1.0-baseline",
                "width_m": width_m,
                "length_m": length_m,
                "floor_height_m": floor_height_m,
                "floors": floors,
                "window_count": window_count,
                "roof_area_m2": roof_area_m2,
                "gross_floor_area_m2": gross_floor_area_m2,
                "total_wall_area_m2": total_wall_area_m2,
                "budget_inr": 250000.0,
                "selected_interventions": ["reflective_roof", "external_shading"],
                "storeys": [s.model_dump() for s in model.storeys],
                "element_counts_by_type": model.element_counts_by_type,
                "materials": list({m for elem in model.elements for m in elem.materials if m}),
            }

# Preload sample digital twin on module load
ModelStore.initialize_with_sample_model()
