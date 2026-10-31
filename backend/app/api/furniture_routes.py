from fastapi import APIRouter, HTTPException, Query, Body, status
from typing import Optional, Dict, Any, List

from app.models.furniture import (
    BuildingFurnishingPlan,
    FurnitureItem,
    FurnitureUpdateRequest,
    FurnitureAddRequest,
)
from app.services.interior_furnishing_service import InteriorFurnishingService
from app.services.model_store import ModelStore

router = APIRouter(prefix="/api/v1/furniture", tags=["Interior Furnishing & 3D Spatial Layout"])


@router.get("/plan/{model_id}", response_model=BuildingFurnishingPlan)
def get_furnishing_plan(
    model_id: str,
    auto_generate: bool = Query(True, description="Automatically generate plan if not already present")
):
    """
    Retrieves the 3D furniture and spatial layout plan for the specified building model.
    If not yet generated, extracts room geometry from model store and creates it.
    """
    plan = InteriorFurnishingService.get_furnishing_plan(model_id)
    if not plan and auto_generate:
        model = ModelStore.get_model(model_id)
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Building model '{model_id}' not found in active model store."
            )
        plan = InteriorFurnishingService.generate_furnishing_plan_for_model(model)

    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No furnishing plan found for model '{model_id}'. Request generation first."
        )

    return plan


@router.post("/plan/{model_id}/generate", response_model=BuildingFurnishingPlan)
def generate_furnishing_plan(
    model_id: str,
    custom_room_types: Optional[Dict[str, str]] = Body(default=None, description="Optional room_id -> room_type overrides"),
    force_regenerate: bool = Query(True, description="Force re-generation of all proposed furniture")
):
    """
    Executes room classification, boundary clearance calculation, and deterministic
    furniture placement for every room in the building model.
    """
    model = ModelStore.get_model(model_id)
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Building model '{model_id}' not found in model store."
        )

    plan = InteriorFurnishingService.generate_furnishing_plan_for_model(
        model=model,
        custom_room_types=custom_room_types,
        force_regenerate=force_regenerate
    )
    return plan


@router.patch("/plan/{model_id}/item/{furniture_id}", response_model=FurnitureItem)
def update_furniture_item(
    model_id: str,
    furniture_id: str,
    update: FurnitureUpdateRequest
):
    """
    Updates a specific furniture item (position, rotation, scale, material, or visibility).
    Maintains user modifications without altering the original structural IFC model.
    """
    updated = InteriorFurnishingService.update_furniture_item(model_id, furniture_id, update)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Furniture item '{furniture_id}' not found in plan for model '{model_id}'."
        )
    return updated


@router.delete("/plan/{model_id}/item/{furniture_id}")
def remove_furniture_item(model_id: str, furniture_id: str):
    """
    Deletes a specific furniture item from the active layout plan.
    """
    success = InteriorFurnishingService.remove_furniture_item(model_id, furniture_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Furniture item '{furniture_id}' could not be deleted from model '{model_id}'."
        )
    return {"status": "success", "message": f"Furniture item '{furniture_id}' removed."}


@router.post("/plan/{model_id}/item", response_model=FurnitureItem)
def add_furniture_item(
    model_id: str,
    request: FurnitureAddRequest
):
    """
    Manually places a new 3D furniture item into a specified room.
    """
    new_item = InteriorFurnishingService.add_furniture_item(model_id, request)
    if not new_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Furnishing plan for model '{model_id}' does not exist. Generate plan first."
        )
    return new_item


@router.get("/catalog")
def get_furniture_catalog() -> Dict[str, Any]:
    """
    Returns available 3D furniture categories, default dimensions, and material palettes.
    """
    catalog = []
    for cat, pal in InteriorFurnishingService.MATERIAL_PALETTES.items():
        dim = InteriorFurnishingService._get_default_dimensions(cat)
        catalog.append({
            "category": cat,
            "display_name": cat.replace("_", " ").title(),
            "default_dimensions_m": {
                "width": dim.width,
                "depth": dim.depth,
                "height": dim.height
            },
            "default_material": pal["material"],
            "default_color_hex": pal["color"]
        })
    return {"categories": catalog}
