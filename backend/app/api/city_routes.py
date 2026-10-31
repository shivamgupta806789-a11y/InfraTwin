from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException, status, Body, UploadFile, File, Form
from app.models.city import CityModel, CityBuildingSummary
from app.services.city_service import CityService
from app.services.city_import_service import CityImportService

router = APIRouter(prefix="/api/v1/city", tags=["City-Scale Digital Twin"])


@router.get("/supported-formats", response_model=Dict[str, str])
async def get_supported_formats():
    """
    Returns dictionary of supported GIS and CAD file formats for district/city import.
    """
    return CityImportService.get_supported_formats()


@router.post("/import-file", response_model=CityModel)
async def import_city_file(
    file: UploadFile = File(..., description="GIS/CAD city file (.geojson, .json, .cityjson, .zip, .gpkg, .dxf)"),
    district_name: Optional[str] = Form(None, description="Custom name for imported district"),
    district_type: Optional[str] = Form("Commercial Center", description="District category"),
    crs_override: Optional[str] = Form(None, description="Optional EPSG code e.g. EPSG:3857 or EPSG:4326"),
    origin_lat: Optional[float] = Form(None, description="Anchor latitude for metric projection"),
    origin_lon: Optional[float] = Form(None, description="Anchor longitude for metric projection"),
):
    """
    Ingests and parses multi-format GIS/CAD datasets (GeoJSON, CityJSON, Shapefile ZIP, GeoPackage, DXF)
    into the canonical city digital twin hierarchy without fabricating heights or geometries.
    """
    try:
        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty."
            )
        updated_city = CityImportService.import_city_file(
            file_bytes=file_bytes,
            filename=file.filename or "imported_file.geojson",
            district_name=district_name,
            district_type=district_type,
            crs_override=crs_override,
            origin_lat=origin_lat,
            origin_lon=origin_lon,
        )
        return updated_city
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import city file: {str(e)}"
        )


@router.post("/restore-sample", response_model=CityModel)
async def restore_sample_city():
    """
    Restores the bundled default TechCity Innovation District sample dataset.
    """
    try:
        return CityService.reset_default_city()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore sample city: {str(e)}"
        )


@router.get("/model", response_model=CityModel)
async def get_city_model():
    """
    Returns the hierarchical city-scale spatial model:
    CITY -> DISTRICT -> SITE -> BUILDING -> STOREY.
    Includes infrastructure networks (roads, power, drainage).
    """
    try:
        return CityService.get_default_city_model()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load city-scale model: {str(e)}"
        )


@router.get("/buildings/{building_id}", response_model=CityBuildingSummary)
async def get_city_building(building_id: str):
    """
    Retrieves summary geometry, typology, and BIM linkage for a specific building in the city dataset.
    """
    bld = CityService.get_building_by_id(building_id)
    if not bld:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Building '{building_id}' not found in city dataset."
        )
    return bld


@router.post("/ingest-geojson", response_model=CityModel)
async def ingest_geojson(
    geojson_data: Dict[str, Any] = Body(..., description="GeoJSON FeatureCollection with building polygon geometries"),
    district_name: str = Query(default="Imported District", description="Name of the new district"),
    district_type: str = Query(default="Commercial Center", description="District category")
):
    """
    Ingests GeoJSON FeatureCollection into the canonical hierarchy (CITY -> DISTRICT -> SITE -> BUILDING).
    Translates GIS polygons to LOD1 3D volumetric buildings with operational energy and carbon estimates.
    """
    try:
        updated_city = CityService.ingest_geojson_district(
            geojson_data=geojson_data,
            district_name=district_name,
            district_type=district_type
        )
        return updated_city
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to ingest GeoJSON dataset: {str(e)}"
        )

