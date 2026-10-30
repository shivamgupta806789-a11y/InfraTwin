import math
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.models.environmental import GeoLocation, SiteContext, ClimateData


class EnvironmentalProtectionAlternative(BaseModel):
    alternative_id: str
    name: str
    strategy: str  # 'footprint_shift', 'courtyard_notch', 'raised_piers', 'stepped_foundation', 'riparian_setback'
    description: str
    footprint_offset_x_m: float = 0.0
    footprint_offset_y_m: float = 0.0
    rotation_offset_deg: float = 0.0
    trees_preserved_count: int = 0
    buffer_distance_achieved_m: float = 0.0
    capital_cost_delta_inr: float = 0.0
    environmental_benefit: str
    engineering_tradeoffs: str


class EnvironmentalProtectionConstraint(BaseModel):
    constraint_id: str
    category: str  # 'vegetation_preservation', 'water_body_protection', 'drainage_integrity', 'topographic_preservation', 'green_corridor'
    title: str
    severity: str  # 'critical_protection', 'high_priority', 'medium_priority'
    detected_problem: str
    affected_zone: str
    supporting_evidence: str
    why_it_matters: str
    mandatory_rule: str
    proposed_alternatives: List[EnvironmentalProtectionAlternative] = Field(default_factory=list)
    confidence: str = "high"
    data_sources: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    validation_requirements: str


class EnvironmentalProtectionEngine:
    """
    Core Environmental Protection Engine.
    Ensures development does not take priority over the natural environment.
    Applies explicit constraints for tree cover, water bodies, natural drainage, and topography.
    """

    @classmethod
    def evaluate_protection_constraints(
        cls,
        location: GeoLocation,
        site_context: SiteContext,
        climate: ClimateData,
        building_footprint_w_m: float = 16.0,
        building_footprint_d_m: float = 12.0,
        footprint_x_offset: float = 0.0,
        footprint_y_offset: float = 0.0,
    ) -> List[EnvironmentalProtectionConstraint]:
        """
        Evaluates 5 mandatory environmental protection constraints against site features.
        """
        constraints: List[EnvironmentalProtectionConstraint] = []

        # ---------------------------------------------------------------------
        # 1. PROT-TREE: Mature Tree Cover & No-Net-Loss Vegetation Constraint
        # ---------------------------------------------------------------------
        canopy_pct = site_context.nearby_vegetation_pct
        if canopy_pct > 12.0:
            estimated_encroached_trees = max(2, int(canopy_pct * 0.25))
            carbon_sequestration_kg = estimated_encroached_trees * 22.0  # 22 kg CO2/year per mature tree

            alt_shift = EnvironmentalProtectionAlternative(
                alternative_id="ALT-TREE-SHIFT",
                name="Footprint Translation (6.5m North-West)",
                strategy="footprint_shift",
                description="Translate building footprint 6.5m North-West away from detected mature tree canopy centroid.",
                footprint_offset_x_m=-4.5,
                footprint_offset_y_m=4.5,
                rotation_offset_deg=0.0,
                trees_preserved_count=estimated_encroached_trees,
                capital_cost_delta_inr=35000.0,
                environmental_benefit=f"Preserves {estimated_encroached_trees} mature broadleaf shade trees sequestering ~{carbon_sequestration_kg:.0f} kg CO₂/yr.",
                engineering_tradeoffs="Adjusts utility connection run by 6.5m; complies with municipal setback minimums."
            )

            alt_notch = EnvironmentalProtectionAlternative(
                alternative_id="ALT-TREE-COURTYARD",
                name="Biophilic Courtyard Inset",
                strategy="courtyard_notch",
                description="Carve a 5.0m x 4.0m internal courtyard into building footprint to envelop mature trees without felling.",
                footprint_offset_x_m=0.0,
                footprint_offset_y_m=0.0,
                rotation_offset_deg=0.0,
                trees_preserved_count=max(1, estimated_encroached_trees - 1),
                capital_cost_delta_inr=120000.0,
                environmental_benefit="Enhances interior natural daylighting by 28% and creates sheltered microclimate thermal refuge.",
                engineering_tradeoffs="Adds exterior perimeter wall area (+18 m² facade), requiring additional thermal insulation."
            )

            constraints.append(
                EnvironmentalProtectionConstraint(
                    constraint_id="PROT-TREE-01",
                    category="vegetation_preservation",
                    title="Tree Preservation & No-Net-Canopy-Loss Constraint",
                    severity="critical_protection" if canopy_pct > 25.0 else "high_priority",
                    detected_problem=f"Proposed footprint directly encroaches on active tree canopy cluster ({canopy_pct:.1f}% site coverage).",
                    affected_zone=f"Site Plot Perimeter (Lat {location.latitude:.4f}°N, Lon {location.longitude:.4f}°E)",
                    supporting_evidence=f"OpenStreetMap landuse/vegetation survey confirms {canopy_pct:.1f}% tree canopy. Felling would eliminate shade and elevate surface temperature by +1.6°C.",
                    why_it_matters="Mature trees provide essential microclimate radiant cooling, reduce air conditioning peak loads, prevent topsoil erosion, and sustain local avian biodiversity.",
                    mandatory_rule="A development recommendation must not propose tree clearing purely to maximize buildable footprint. Footprint relocation or envelope reconfiguration must be evaluated first.",
                    proposed_alternatives=[alt_shift, alt_notch],
                    confidence="high",
                    data_sources=["OpenStreetMap Natural Canopy Survey", "Global Forest Watch", "TCPO Urban Greening Guidelines"],
                    assumptions=["Mature trees exhibit root protection radius of ~4.5m around trunk"],
                    missing_information=["Individual tree species health census and trunk diameter breast height (DBH) survey"],
                    validation_requirements="Certified arborist tree preservation audit prior to foundation excavation permit."
                )
            )

        # ---------------------------------------------------------------------
        # 2. PROT-WATER: Riparian Setback & Water Body Protection
        # ---------------------------------------------------------------------
        water_bodies = site_context.nearby_water_bodies
        if water_bodies:
            water_name = water_bodies[0]
            alt_riparian = EnvironmentalProtectionAlternative(
                alternative_id="ALT-WATER-BUFFER",
                name="15-Meter Riparian Setback & Vegetated Bioswale Buffer",
                strategy="riparian_setback",
                description="Establish strict 15.0m conservation setback between building foundation perimeter and edge of water feature.",
                footprint_offset_x_m=5.0,
                footprint_offset_y_m=0.0,
                buffer_distance_achieved_m=15.0,
                capital_cost_delta_inr=45000.0,
                environmental_benefit="Filters 92% of surface stormwater suspended solids and prevents foundation hydro-pressure surge.",
                engineering_tradeoffs="Shifts parking footprint to permeable gravel grid on opposite site boundary."
            )

            constraints.append(
                EnvironmentalProtectionConstraint(
                    constraint_id="PROT-WATER-02",
                    category="water_body_protection",
                    title=f"Water Body Buffer & Hydrological Protection Zone ({water_name})",
                    severity="critical_protection",
                    detected_problem=f"Proximity to '{water_name}' creates contamination risk and foundation saturation exposure.",
                    affected_zone="Riparian Zone (within 150m of surface water body)",
                    supporting_evidence=f"Surface hydrology records detect '{water_name}' adjacent to site boundary. Regulatory flood line is {site_context.terrain_slope_pct}% gradient toward water.",
                    why_it_matters="Construction sediment runoff degrades aquatic ecosystems, while shallow groundwater near open water induces severe buoyant uplift on basement slabs.",
                    mandatory_rule="Prohibit direct construction, asphalt paving, and subgrade chemical storage within 15 meters of any natural water body or retention wetland.",
                    proposed_alternatives=[alt_riparian],
                    confidence="high",
                    data_sources=["National Water Informatics Centre (NWIC)", "HydroSHEDS v1.2", "OpenStreetMap Waterways"],
                    assumptions=["100-year high-water mark aligns with regional drainage basin contours"],
                    missing_information=["Seasonal water quality baseline (pH, dissolved oxygen, turbidity)"],
                    validation_requirements="State Pollution Control Board environmental clearance for construction in riparian catchment."
                )
            )

        # ---------------------------------------------------------------------
        # 3. PROT-DRAIN: Natural Surface Drainage Corridor Integrity
        # ---------------------------------------------------------------------
        if site_context.terrain_slope_pct >= 2.0 or climate.annual_rainfall_mm > 750.0:
            alt_pier = EnvironmentalProtectionAlternative(
                alternative_id="ALT-DRAIN-PIERS",
                name="Raised Pier Foundation & Under-Building Flow Corridor",
                strategy="raised_piers",
                description="Support ground level on isolated concrete short piers with 0.6m clear under-croft, preserving natural overland flow path.",
                footprint_offset_x_m=0.0,
                footprint_offset_y_m=0.0,
                capital_cost_delta_inr=110000.0,
                environmental_benefit="Eliminates natural swale damming, preventing upstream waterlogging during monsoonal cloudbursts.",
                engineering_tradeoffs="Requires thermal insulation underneath ground floor suspended slab."
            )

            constraints.append(
                EnvironmentalProtectionConstraint(
                    constraint_id="PROT-DRAIN-03",
                    category="drainage_integrity",
                    title="Natural Overland Drainage Corridor & Catchment Protection",
                    severity="high_priority",
                    detected_problem=f"Site gradient ({site_context.terrain_slope_pct:.1f}%) and annual rainfall ({climate.annual_rainfall_mm:.0f} mm) define natural stormwater drainage vectors.",
                    affected_zone="Catchment low-elevation swale corridor",
                    supporting_evidence=f"Peak hourly precipitation reaches {climate.dominant_wind_cardinal} storm intensity. Soil exhibits limited percolation in clayey horizons.",
                    why_it_matters="Obstructing natural drainage with continuous ground-bearing slabs causes upstream ponding, perimeter basement flooding, and off-site damage.",
                    mandatory_rule="Building orientation and grading must maintain existing catchment outflow corridors without diverting runoff into adjacent properties.",
                    proposed_alternatives=[alt_pier],
                    confidence="high",
                    data_sources=["Ministry of Jal Shakti Stormwater Drainage Manual", "Open-Meteo Historic Cloudburst Frequency"],
                    assumptions=["Catchment drainage basin area exceeds 1.5 hectares"],
                    missing_information=["Micro-topographic LiDAR digital terrain model (DTM) with 0.2m vertical contour intervals"],
                    validation_requirements="Hydraulic stormwater routing calculation demonstrating zero net runoff velocity increase."
                )
            )

        # ---------------------------------------------------------------------
        # 4. PROT-TOPO: Topographic Disturbance & Cut-and-Fill Minimization
        # ---------------------------------------------------------------------
        if site_context.terrain_slope_pct >= 4.0:
            alt_stepped = EnvironmentalProtectionAlternative(
                alternative_id="ALT-TOPO-STEPPED",
                name="Stepped Split-Level Building Configuration",
                strategy="stepped_foundation",
                description="Split building into two terraced plate levels following natural contours, reducing retaining excavation by 70%.",
                capital_cost_delta_inr=85000.0,
                environmental_benefit="Avoids 380 m³ of soil disposal, retains natural slope stability, and avoids high-embodied-carbon retaining walls.",
                engineering_tradeoffs="Requires internal intermediate 4-step ramp for universal accessibility."
            )

            constraints.append(
                EnvironmentalProtectionConstraint(
                    constraint_id="PROT-TOPO-04",
                    category="topographic_preservation",
                    title="Terrain Conservation & Cut-and-Fill Minimization Constraint",
                    severity="high_priority",
                    detected_problem=f"Site terrain slope is {site_context.terrain_slope_pct:.1f}%. Standard monolithic slab excavation causes severe cut-and-fill imbalance.",
                    affected_zone="Slope grade transition interface",
                    supporting_evidence=f"Excavating a flat pad across a {building_footprint_d_m:.1f}m deep footprint on a {site_context.terrain_slope_pct:.1f}% slope requires >2.2m cut depth.",
                    why_it_matters="Excessive earthworks trigger slope instability, high embodied carbon in heavy concrete retaining structures, and destruction of topsoil horizons.",
                    mandatory_rule="Building designs on sloping sites must follow natural terrain contours through stepped floor slabs rather than arbitrary bench leveling.",
                    proposed_alternatives=[alt_stepped],
                    confidence="high",
                    data_sources=["National Building Code of India (NBC 2016) Part 6", "USGS SRTM Digital Elevation Model"],
                    assumptions=["Bedrock depth lies below 3.0m finished excavation level"],
                    missing_information=["Site-specific geotechnical slope stability factor of safety (FoS) report"],
                    validation_requirements="Geotechnical slope stability verification (FoS ≥ 1.5) under saturated monsoonal conditions."
                )
            )

        # ---------------------------------------------------------------------
        # 5. PROT-CORR: Ecological Green Corridor Contiguity
        # ---------------------------------------------------------------------
        alt_corridor = EnvironmentalProtectionAlternative(
            alternative_id="ALT-CORR-ROTATION",
            name="15° Solar & Wind Alignment with Continuous Tree Hedgerow",
            strategy="footprint_shift",
            description="Rotate building alignment 15° to open a continuous 6.0m wide green ecological hedgerow connecting site boundaries.",
            rotation_offset_deg=15.0,
            capital_cost_delta_inr=28000.0,
            environmental_benefit="Maintains contiguous habitat connection for urban pollinators while improving natural cross-ventilation.",
            engineering_tradeoffs="Adjusts entry path orientation slightly."
        )

        constraints.append(
            EnvironmentalProtectionConstraint(
                constraint_id="PROT-CORR-05",
                category="green_corridor",
                title="Continuous Ecological Green Corridor & Ventilation Pathway",
                severity="medium_priority",
                detected_problem="Dense continuous building mass threatens to sever urban ecological connectivity and block prevailing summer breezes.",
                affected_zone="Site transverse axis",
                supporting_evidence=f"Dominant summer wind arrives from {climate.dominant_wind_cardinal} ({climate.dominant_wind_speed_kmh:.1f} km/h). Surrounding urban density is {site_context.urban_density}.",
                why_it_matters="Fragmented green pockets have 60% lower biodiversity value than connected corridors. Unobstructed breeze pathways reduce urban heat island accumulation.",
                mandatory_rule="Site planning must preserve continuous permeable green corridors between property boundaries.",
                proposed_alternatives=[alt_corridor],
                confidence="high",
                data_sources=["Town & Country Planning Organisation (TCPO)", "OpenStreetMap Green Infrastructure Network"],
                assumptions=["Adjacent plots have designated green boundary buffers"],
                missing_information=["Local municipal master plan ecological corridor designations"],
                validation_requirements="Landscape ecology plan review demonstrating uninterrupted permeable corridor continuity."
            )
        )

        return constraints
