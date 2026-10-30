from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

class BuildingInput(BaseModel):
    width_m: float = Field(
        ...,
        gt=0,
        le=200,
        description="Building width along X-axis in metres (must be between 0 and 200m)."
    )
    length_m: float = Field(
        ...,
        gt=0,
        le=200,
        description="Building length along Y-axis in metres (must be between 0 and 200m)."
    )
    floor_height_m: float = Field(
        default=3.0,
        gt=1.5,
        le=10.0,
        description="Floor height in metres (typically 2.8 - 4.0m)."
    )
    floors: int = Field(
        ...,
        ge=1,
        le=50,
        description="Integer number of above-ground floors (at least 1, max 50)."
    )
    window_count: int = Field(
        ...,
        ge=0,
        le=1000,
        description="Total count of visible exterior windows across all facades."
    )
    budget_inr: float = Field(
        default=0.0,
        ge=0,
        le=1_000_000_000,
        description="Available sustainable improvement budget in Indian Rupees (INR)."
    )
    selected_interventions: List[str] = Field(
        default_factory=list,
        description="List of selected intervention IDs for simulation / comparison."
    )

    @field_validator("selected_interventions")
    @classmethod
    def validate_intervention_ids(cls, v: List[str]) -> List[str]:
        # Clean duplicates preserving order
        seen = set()
        clean = []
        for item in v:
            item_clean = item.strip().lower()
            if item_clean and item_clean not in seen:
                seen.add(item_clean)
                clean.append(item_clean)
        return clean

    @model_validator(mode="after")
    def validate_spatial_consistency(self) -> "BuildingInput":
        # Check window distribution plausibility
        total_wall_area = 2 * (self.width_m + self.length_m) * (self.floors * self.floor_height_m)
        assumed_window_area = self.window_count * 2.0  # ~2 m2 per standard window
        if self.window_count > 0 and assumed_window_area > total_wall_area * 0.9:
            raise ValueError(
                f"Window count ({self.window_count}) exceeds realistic facade surface area "
                f"({total_wall_area:.1f} m²)."
            )
        return self


class NormalizedBuilding(BaseModel):
    width_m: float
    length_m: float
    floor_height_m: float
    floors: int
    window_count: int
    budget_inr: float
    selected_interventions: List[str]
    roof_area_m2: float
    gross_floor_area_m2: float
    total_height_m: float
    total_wall_area_m2: float
    estimated_window_wall_ratio: float


class BuildingValidationResponse(BaseModel):
    is_valid: bool
    normalized: Optional[NormalizedBuilding] = None
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
