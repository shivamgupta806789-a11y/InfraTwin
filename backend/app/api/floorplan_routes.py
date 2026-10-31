import os
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status

from app.models.floorplan import (
    FloorPlanExtractionResponse,
    FloorPlan3DGenerateRequest,
)
from app.models.digital_twin import ImportSummaryResponse
from app.services.floorplan_processor import FloorplanProcessorService
from app.services.floorplan_to_3d_service import FloorplanTo3dService

router = APIRouter(prefix="/api/v1/floorplan", tags=["2D Floorplan to 3D"])

MAX_DRAWING_BYTES = 25 * 1024 * 1024  # 25 MB limit for raster / PDF drawings
SUPPORTED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".pdf", ".webp", ".bmp", ".dxf"]


@router.post("/extract", response_model=FloorPlanExtractionResponse)
async def extract_floorplan_geometry(
    file: UploadFile = File(...),
    known_dimension_m: Optional[float] = Form(None),
):
    """
    Ingests an architectural 2D floor-plan image or PDF.
    Validates drawing format, performs OpenCV computer-vision extraction of walls, openings,
    and rooms, derives scale, and generates an annotated visual detection overlay.
    """
    filename = os.path.basename(file.filename or "drawing.png")
    ext = os.path.splitext(filename)[1].lower()

    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported drawing format '{ext}'. "
                f"Supported architectural formats: {', '.join(SUPPORTED_EXTENSIONS)}"
            ),
        )

    # Read bytes with size protection
    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded drawing file is empty (0 bytes). Please upload a valid architectural floor plan.",
        )
    if len(file_bytes) > MAX_DRAWING_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Drawing file exceeds maximum allowed limit of {MAX_DRAWING_BYTES // (1024 * 1024)}MB.",
        )

    try:
        # Load and validate image / PDF
        img_bgr, detected_type = FloorplanProcessorService.load_drawing_to_bgr(file_bytes, filename)

        # Extract geometry with OpenCV
        extraction_res = FloorplanProcessorService.extract_geometry(
            img_bgr=img_bgr,
            filename=filename,
            file_type=detected_type,
            known_dimension_m=known_dimension_m,
        )

        return extraction_res

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Floorplan processing failed: {str(e)}",
        )


@router.post("/sample/{sample_name}", response_model=FloorPlanExtractionResponse)
async def extract_sample_drawing(sample_name: str = "commercial"):
    """
    Convenience endpoint for 1-click testing: extracts geometry from pre-packaged
    sample architectural drawings (commercial PNG or commercial PDF).
    """
    ext = ".pdf" if "pdf" in sample_name.lower() else ".png"
    filename = f"sample_commercial_floorplan{ext}"
    sample_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "fixtures", filename
    )

    if not os.path.exists(sample_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sample fixture '{filename}' not found on server.",
        )

    with open(sample_path, "rb") as f:
        file_bytes = f.read()

    img_bgr, detected_type = FloorplanProcessorService.load_drawing_to_bgr(file_bytes, filename)
    return FloorplanProcessorService.extract_geometry(
        img_bgr=img_bgr,
        filename=filename,
        file_type=detected_type,
        known_dimension_m=20.0,
    )


@router.post("/generate-3d", response_model=ImportSummaryResponse)
async def generate_3d_building(request: FloorPlan3DGenerateRequest):
    """
    Converts a normalized, user-corrected 2D floor plan into a canonical 3D Building Digital Twin.
    Generates extruded walls with window and door apertures, floor slabs, and selected roof geometries.
    Saves the model into the active ModelStore and returns the import summary.
    """
    if not request.floorplan.walls:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot generate 3D building: floor plan contains no walls.",
        )

    try:
        model_detail, summary = FloorplanTo3dService.generate_building_model(
            floorplan=request.floorplan,
            floors=request.floors,
            floor_height_m=request.floor_height_m,
            building_type=request.building_type or "Commercial",
            roof_type=request.roof_type,
            building_name=request.building_name or "2D Floorplan Generated Twin",
        )
        return summary

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"3D Building synthesis failed: {str(e)}",
        )
