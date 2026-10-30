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
                    storeys=m.storeys,
                    element_counts_by_type=m.element_counts_by_type,
                    total_element_count=m.total_element_count,
                    available_properties=m.available_properties,
                    missing_data=m.missing_data,
                    bounding_box=m.bounding_box,
                    provenance_metadata=m.provenance_metadata
                )
                models_summary.append(summary)
            return models_summary

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

# Preload sample digital twin on module load
ModelStore.initialize_with_sample_model()
