import os
import uuid
import tempfile
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, status
from app.models.digital_twin import (
    BuildingModel,
    BuildingModelDetail,
    BuildingElement,
    ImportSummaryResponse,
    ModelQualityReport,
    EsgAssessmentReport,
    BuildingIntelligenceReport,
)
from app.services.ifc_parser import IfcParserService
from app.services.model_store import ModelStore

router = APIRouter(prefix="/api/v1/models", tags=["BIM & Digital Twin"])

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB limit

@router.get("", response_model=List[BuildingModel])
async def list_models():
    """
    Returns models available in the current application session scope.
    Honest disclosure: in-memory session scoped; models reset on server restart.
    """
    return ModelStore.list_models()

@router.post("/import/ifc", response_model=ImportSummaryResponse)
async def import_ifc_model(file: UploadFile = File(...)):
    """
    Securely uploads and parses an IFC architectural/structural file using IfcOpenShell.
    Extracts spatial hierarchy, elements, triangulated 3D mesh geometry, and property sets.
    """
    filename = os.path.basename(file.filename or "uploaded.ifc")
    ext = os.path.splitext(filename)[1].lower()

    if ext not in [".ifc", ".ifcxml", ".ifczip"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Only official IFC formats (.ifc, .ifcxml) are supported."
        )

    # Stream file to disk and validate size & STEP header
    tmp_path = None
    try:
        total_size = 0
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp_file:
            tmp_path = tmp_file.name
            header_sample = b""
            
            while chunk := await file.read(64 * 1024):
                total_size += len(chunk)
                if total_size > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Uploaded file exceeds maximum limit of {MAX_UPLOAD_BYTES // (1024*1024)}MB."
                    )
                if len(header_sample) < 512:
                    header_sample += chunk
                tmp_file.write(chunk)

        # Validation: check for empty file
        if total_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty (0 bytes). Please provide a valid IFC model."
            )

        # Content validation: check for STEP standard physical file signature
        header_text = header_sample[:512].decode("utf-8", errors="ignore")
        if ext == ".ifc" and "ISO-10303-21" not in header_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Malformed or invalid IFC file: missing standard 'ISO-10303-21;' header."
            )

        # Parse with IfcOpenShell
        model_id = str(uuid.uuid4())
        model, warnings, missing_info = IfcParserService.parse_ifc_file(
            filepath=tmp_path,
            filename=filename,
            model_id=model_id
        )

        # Save into session model store
        ModelStore.save_model(model, warnings)

        import_status = "success" if model.total_element_count > 0 else "partial"
        if not model.storeys and not model.elements:
            import_status = "failed"

        return ImportSummaryResponse(
            model_id=model.model_id,
            source_filename=model.source_filename,
            schema_version=model.schema_version,
            import_status=import_status,
            element_counts_by_type=model.element_counts_by_type,
            total_elements=model.total_element_count,
            available_properties=model.available_properties[:20],
            units=model.units,
            coordinate_metadata=model.provenance_metadata,
            parsing_warnings=warnings,
            missing_information_summary=missing_info
        )

    except HTTPException:
        raise
    except Exception as e:
        http_422 = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", status.HTTP_422_UNPROCESSABLE_ENTITY)
        raise HTTPException(
            status_code=http_422,
            detail=f"IFC Parser Error: {str(e)}"
        )
    finally:
        # Secure cleanup: always remove temporary upload file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

@router.get("/{model_id}", response_model=BuildingModelDetail)
async def get_model_detail(model_id: str):
    """Returns canonical model metadata, spatial storeys, and all supported 3D elements."""
    model = ModelStore.get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model with identifier '{model_id}' was not found in active session."
        )
    return model

@router.get("/{model_id}/elements")
async def get_model_elements(
    model_id: str,
    element_type: Optional[str] = Query(None, description="Filter by IFC element type, e.g. IfcWall, IfcDoor"),
    storey_id: Optional[str] = Query(None, description="Filter by storey GlobalId"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Returns paginated elements with optional filtering by type and storey."""
    model = ModelStore.get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_id}' was not found."
        )

    elements, total = ModelStore.get_elements(
        model_id,
        element_type=element_type,
        storey_id=storey_id,
        limit=limit,
        offset=offset
    )

    return {
        "model_id": model_id,
        "items": elements,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/{model_id}/quality", response_model=ModelQualityReport)
async def get_model_quality_report(model_id: str):
    """Evaluates model completeness, missing geometry, identifier uniqueness, and material tags."""
    report = ModelStore.get_quality_report(model_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_id}' was not found."
        )
    return report

@router.get("/{model_id}/esg", response_model=EsgAssessmentReport)
async def get_model_esg_assessment(
    model_id: str,
    annual_kwh: Optional[float] = Query(None, ge=0, description="Optional annual electricity consumption (kWh)")
):
    """
    Generates an evidence-based preliminary ESG assessment across Environmental, Social, and Governance pillars.
    Strictly distinguishes imported facts, calculated figures, and unassessed items.
    """
    report = ModelStore.get_esg_report(model_id, annual_kwh=annual_kwh)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_id}' was not found."
        )
    return report

@router.get("/{model_id}/intelligence", response_model=BuildingIntelligenceReport)
async def get_model_intelligence(model_id: str):
    """
    Evidence-based building intelligence module analyzing imported IFC models
    for potential design, data-quality, and building-performance concerns.
    """
    report = ModelStore.get_intelligence_report(model_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model '{model_id}' was not found."
        )
    return report
