import datetime
import math
from typing import List, Dict, Any, Optional

from app.models.sustainability import ComprehensiveRecommendation, SustainabilityAuditReport
from app.models.environmental import GeoLocation
from app.services.model_store import ModelStore
from app.services.geotechnical_service import GeotechnicalService
from app.services.city_service import CityService
from app.services.environmental_service import EnvironmentalService
from app.services.environmental_protection_service import EnvironmentalProtectionEngine
from app.services.geospatial_integration_service import GeospatialIntegrationService


class SustainabilityRecommendationService:
    """
    Advanced Multi-Domain Sustainability & Infrastructure Intelligence Engine.
    Combines:
    - Verified building geometry & floor layouts (IFC / parametric)
    - Confirmed project geolocation
    - 10 Geospatial, Earth Observation, Pedological, and Climatological Datasets:
      1. ESA WorldCover 10m
      2. Dynamic World
      3. Copernicus Sentinel-2 L2A
      4. Global Forest Watch
      5. OpenStreetMap
      6. Microsoft Global ML Building Footprints
      7. SoilGrids 250m v2.0
      8. HydroSHEDS / HydroRIVERS
      9. NASA POWER
      10. ERA5 Atmospheric Reanalysis
    """

    @classmethod
    def evaluate_comprehensive_intelligence(
        cls,
        target_entity_id: str = "sample-office-twin",
        level: str = "building",
        latitude: float = 28.6139,
        longitude: float = 77.2090
    ) -> SustainabilityAuditReport:
        # 1. Retrieve Building & Baseline Models
        baseline = ModelStore.get_parametric_baseline(target_entity_id)
        geo_profile = GeotechnicalService.get_site_geotechnical_profile(latitude, longitude)
        city = CityService.get_default_city_model()

        # 2. Retrieve Unified Location Profile across all 10 Geospatial Datasets
        loc_profile = GeospatialIntegrationService.get_unified_location_profile(latitude, longitude)

        recs: List[ComprehensiveRecommendation] = []
        insufficient_data: List[str] = []

        gfa = baseline["gross_floor_area_m2"] if baseline else 508.0
        roof_area = baseline["roof_area_m2"] if baseline else 254.0
        window_count = baseline["window_count"] if baseline else 4
        wwr = 0.18
        footprint_w = math.sqrt(roof_area) if roof_area > 0 else 16.0
        footprint_d = math.sqrt(roof_area) if roof_area > 0 else 16.0
        occupants = max(10, int(gfa / 12.0))
        floors = int(baseline.get("floors", 2)) if baseline else 2

        # Extract live features from UnifiedLocationProfile
        solar_ghi = float(loc_profile.climate.annual_solar_ghi_kwh_m2_day.value)
        ann_precip = float(loc_profile.climate.annual_precipitation_mm.value)
        cdd = float(loc_profile.climate.cooling_degree_days.value)
        mean_temp = float(loc_profile.climate.annual_mean_temp_c.value)
        wind_dir = float(loc_profile.climate.prevailing_wind_direction_deg.value)
        wind_speed = float(loc_profile.climate.wind_speed_mps.value)
        i_10yr = float(loc_profile.climate.intensity_10yr_return_mm_hr.value)
        i_2yr = float(loc_profile.climate.intensity_2yr_return_mm_hr.value)

        soil_tex = str(loc_profile.soil_hydrology.soil_texture_usda.value)
        hsg = str(loc_profile.soil_hydrology.hydrologic_soil_group.value)
        infil_rate = float(loc_profile.soil_hydrology.infiltration_rate_mm_hr.value)
        clay_pct = float(loc_profile.soil_hydrology.clay_content_pct.value)
        soil_ph = float(loc_profile.soil_hydrology.soil_ph.value)

        sub_basin = str(loc_profile.soil_hydrology.watershed_basin_level.value)
        stream_order = int(loc_profile.soil_hydrology.strahler_stream_order.value)
        drain_dist = float(loc_profile.soil_hydrology.drainage_channel_distance_m.value)

        built_pct = float(loc_profile.land_cover.built_up_coverage_pct.value)
        veg_pct = float(loc_profile.land_cover.vegetation_coverage_pct.value)
        dominant_land = str(loc_profile.land_cover.dominant_class.value)

        ndvi = float(loc_profile.vegetation.ndvi_mean.value)
        canopy_pct = float(loc_profile.vegetation.tree_canopy_density_pct.value)
        vigor = str(loc_profile.vegetation.vegetation_vigor.value)

        road_dist = float(loc_profile.infrastructure.nearest_road_distance_m.value)
        road_type = str(loc_profile.infrastructure.road_classification.value)
        bld_count = int(loc_profile.infrastructure.nearby_building_count.value)
        density_ratio = float(loc_profile.infrastructure.building_density_ratio.value)

        # Dataset status summary
        dataset_status_map = {k: v.status.value for k, v in loc_profile.dataset_statuses.items()}

        # =========================================================================
        # 1. SOLAR OPTIMISATION (NASA POWER, ERA5, Sentinel-2, MS Footprints)
        # =========================================================================
        pv_kwp = round((roof_area * 0.70) / 6.0, 1)  # 70% usable roof, 6m2 per kWp
        annual_pv_kwh = round(pv_kwp * solar_ghi * 365.0 * 0.78, 0)
        co2_avoided_tons = round(annual_pv_kwh * 0.716 / 1000.0, 1)

        recs.append(
            ComprehensiveRecommendation(
                id="REC-SOLAR-001",
                category="environmental_sustainability",
                category_title="1. Solar Energy Optimisation",
                hierarchical_level="building",
                target_entity_id=target_entity_id,
                priority="high",
                title=f"Rooftop Solar PV Installation ({pv_kwp} kWp Monocrystalline Array)",
                detected_condition=f"Unshaded flat roof plate of {roof_area:.1f} m² has zero active on-site clean power generation.",
                evidence=f"Solar insolation at ({latitude:.4f}°N, {longitude:.4f}°E) averages {solar_ghi:.2f} kWh/m²/day GHI (NASA POWER). Surrounding building coverage ratio is {density_ratio:.2f} m²/m² (MS Building Footprints).",
                explanation=f"Deploying a high-efficiency grid-tied solar photovoltaic array directly offsets high-carbon daytime peak electricity under favorable {solar_ghi:.2f} kWh/m²/day solar exposure.",
                proposed_intervention=f"Install {pv_kwp} kWp monocrystalline PERC solar modules at 28° tilt with bi-directional net metering and micro-inverters.",
                expected_benefit=f"Generates ~{annual_pv_kwh:,.0f} kWh/year clean electricity, avoiding ~{co2_avoided_tons:.1f} t CO₂e annually.",
                estimated_cost_inr=float(pv_kwp * 45000),
                time_horizon="near_term_2026",
                confidence="high",
                data_sources=["NASA POWER Solar Database", "Copernicus Sentinel-2", "ERA5 Atmospheric Reanalysis", "Microsoft Building Footprints"],
                contributing_datasets=["DS-09-NASA-POWER", "DS-03-SENTINEL-2", "DS-10-ERA5-REANALYSIS", "DS-06-MS-BUILDING-FOOTPRINTS"],
                relevant_building_feature=f"Flat concrete roof plate of {roof_area:.1f} m² with dead-load reserve capacity.",
                relevant_location_feature=f"NASA POWER solar irradiance GHI: {solar_ghi:.2f} kWh/m²/day; MS Footprints building density: {density_ratio:.2f}.",
                assumptions=["70% net usable rooftop area after access clearances", "System performance ratio 78%", "South-facing module orientation"],
                missing_information=[],
                validation_requirements="Rooftop structural dead-load bearing check (15 kg/m²) by licensed structural engineer."
            )
        )

        # =========================================================================
        # 2. HEAT REDUCTION & THERMAL COMFORT (Sentinel-2, Dynamic World, WorldCover, NASA POWER, ERA5)
        # =========================================================================
        recs.append(
            ComprehensiveRecommendation(
                id="REC-HEAT-002",
                category="environmental_sustainability",
                category_title="2. Urban Heat Reduction & Thermal Comfort",
                hierarchical_level="building",
                target_entity_id="IfcRoof_and_IfcWindow",
                priority="high" if cdd > 2000.0 else "medium",
                title="High-SRI Cool Roof Coating & External Dynamic Architectural Shading",
                detected_condition=f"Site microclimate exhibits high thermal exposure with {cdd:.0f} annual Cooling Degree Days (ERA5) and localized surface NDVI of {ndvi:.2f} (Sentinel-2).",
                evidence=f"Ambient temperature averages {mean_temp:.1f}°C (NASA POWER). Built-up impervious surface covers {built_pct:.1f}% of the sector (ESA WorldCover), creating localized urban heat island amplification.",
                explanation="High thermal radiation through uninsulated roof plates and unshaded exterior glazing planes drives severe chiller electricity peaks and interior discomfort.",
                proposed_intervention=f"Apply high-reflectance elastomeric cool roof coating (Solar Reflectance Index SRI ≥ 82) over {roof_area:.1f} m² roof and install exterior powder-coated aluminum louvers on South/West window apertures.",
                expected_benefit="Lowers roof surface temperature by 14°C–18°C, reducing annual mechanical HVAC cooling load by ~18% and cutting peak daytime chiller demand.",
                estimated_cost_inr=round(roof_area * 280.0 + window_count * 9500.0, 0),
                time_horizon="near_term_2026",
                confidence="high",
                data_sources=["Copernicus Sentinel-2", "Dynamic World", "ESA WorldCover 10m", "NASA POWER", "ERA5 Atmospheric Reanalysis"],
                contributing_datasets=["DS-03-SENTINEL-2", "DS-02-DYNAMIC-WORLD", "DS-01-ESA-WORLDCOVER", "DS-09-NASA-POWER", "DS-10-ERA5-REANALYSIS"],
                relevant_building_feature=f"Building roof area of {roof_area:.1f} m² and {window_count} external window apertures (WWR {wwr*100:.1f}%).",
                relevant_location_feature=f"Sentinel-2 NDVI: {ndvi:.2f}; ERA5 Cooling Degree Days: {cdd:.0f}; ESA WorldCover built-up: {built_pct:.1f}%.",
                assumptions=["Standard single or double clear glazing without low-E coating"],
                missing_information=[],
                validation_requirements="Field measurement of pre- and post-installation solar reflectance index per ASTM E1980."
            )
        )

        # =========================================================================
        # 3. FLOOD & STORMWATER MANAGEMENT (HydroSHEDS, SoilGrids, WorldCover, OSM, ERA5)
        # =========================================================================
        vault_vol_m3 = round(max(35.0, (roof_area * (i_10yr / 1000.0) * 0.90) * 1.5), 1)
        recs.append(
            ComprehensiveRecommendation(
                id="REC-STORM-003",
                category="infrastructure_resilience",
                category_title="3. Urban Flood Prevention & Stormwater Management",
                hierarchical_level="site",
                target_entity_id=target_entity_id,
                priority="critical" if (i_10yr > 80.0 or hsg in ["C", "D"]) else "high",
                title=f"On-Site Sustainable Drainage System (SuDS) with {vault_vol_m3} m³ Attenuation Vault",
                detected_condition=f"10-year storm intensity reaches {i_10yr:.1f} mm/hr (ERA5). Site sits within Sub-Basin {sub_basin} (HydroSHEDS) with Stream Order {stream_order}.",
                evidence=f"SoilGrids classification identifies {soil_tex} (Hydrologic Group {hsg}, {clay_pct:.1f}% clay) with limited natural infiltration rate ({infil_rate:.1f} mm/hr). Nearest mapped drainage channel is {drain_dist:.0f}m away (OSM).",
                explanation="Intense cloudburst rainfall exceeding soil infiltration capacity over impermeable built surfaces causes flash urban pluvial ponding and street drainage backflow.",
                proposed_intervention=f"Construct an integrated {vault_vol_m3} m³ dual-chamber underground stormwater attenuation vault and perimeter vegetated bioswales to regulate site discharge.",
                expected_benefit=f"Attenuates 100% of 10-year peak storm runoff on-site, releasing water at controlled pre-development greenfield rates (< 2.5 L/s/ha).",
                estimated_cost_inr=round(vault_vol_m3 * 8500.0 + 45000.0, 0),
                time_horizon="immediate",
                confidence="high",
                data_sources=["HydroSHEDS HydroRIVERS", "SoilGrids 250m", "ESA WorldCover 10m", "OpenStreetMap", "ERA5 Atmospheric Reanalysis"],
                contributing_datasets=["DS-08-HYDROSHEDS", "DS-07-SOILGRIDS", "DS-01-ESA-WORLDCOVER", "DS-05-OPENSTREETMAP", "DS-10-ERA5-REANALYSIS"],
                relevant_building_feature=f"Impervious roof catchment of {roof_area:.1f} m² and building perimeter footprint.",
                relevant_location_feature=f"ERA5 10-year storm intensity: {i_10yr:.1f} mm/hr; SoilGrids HSG: {hsg} ({soil_tex}); HydroSHEDS basin: {sub_basin}.",
                assumptions=["10-year return period storm design standard", "15% safety factor for climate precipitation intensification"],
                missing_information=[],
                validation_requirements="Hydraulic HEC-RAS catchment run-off validation and municipal stormwater connection permit."
            )
        )

        # =========================================================================
        # 4. WATER MANAGEMENT & RAINWATER HARVESTING (NASA POWER, ERA5, SoilGrids, HydroSHEDS)
        # =========================================================================
        annual_harvest_m3 = round((ann_precip / 1000.0) * roof_area * 0.85 * 0.85, 1)  # 85% runoff, 85% filter
        annual_demand_m3 = round((occupants * 45.0 * 0.50 * 300.0) / 1000.0, 1)  # 45 lpcd, 50% non-potable, 300 days
        tank_size_m3 = round(min(annual_harvest_m3 * 0.35, max(15.0, annual_demand_m3 * 0.25)), 0)
        water_offset_pct = min(100.0, round((annual_harvest_m3 / max(1.0, annual_demand_m3)) * 100.0, 0))

        recs.append(
            ComprehensiveRecommendation(
                id="REC-WATER-004",
                category="environmental_sustainability",
                category_title="4. Rainwater Harvesting & Water Conservation",
                hierarchical_level="building",
                target_entity_id=target_entity_id,
                priority="high",
                title=f"Building-Specific Rainwater Harvesting System ({tank_size_m3:.0f} m³ Cistern)",
                detected_condition=f"Annual precipitation of {ann_precip:.1f} mm generates ~{annual_harvest_m3:,.0f} m³ of clean roof runoff that is currently discharged unutilized.",
                evidence=f"ERA5 30-year normal rainfall is {ann_precip:.1f} mm/yr. Soil infiltration capacity is {infil_rate:.1f} mm/hr (SoilGrids {soil_tex}). Building non-potable demand equals {annual_demand_m3:,.0f} m³/yr.",
                explanation="Harvesting pristine roof runoff offsets stressed municipal groundwater extraction, stabilizes site water security, and reduces drainage surcharge.",
                proposed_intervention=f"Install an engineered {tank_size_m3:.0f} m³ dual-chamber underground concrete storage cistern with vortex filter, sediment trap, and dual plumbing loop for toilet flushing and cooling tower makeup.",
                expected_benefit=f"Supplies ~{annual_harvest_m3:,.0f} m³/year, meeting {water_offset_pct:.0f}% of building non-potable water demand and saving ₹{annual_harvest_m3 * 95:,.0f} annually.",
                estimated_cost_inr=round(tank_size_m3 * 9200.0 + 35000.0, 0),
                time_horizon="near_term_2026",
                confidence="high",
                data_sources=["ERA5 Atmospheric Reanalysis", "NASA POWER", "SoilGrids 250m", "HydroSHEDS"],
                contributing_datasets=["DS-10-ERA5-REANALYSIS", "DS-09-NASA-POWER", "DS-07-SOILGRIDS", "DS-08-HYDROSHEDS"],
                relevant_building_feature=f"Roof catchment area of {roof_area:.1f} m² with concrete/metal surface coefficient 0.85.",
                relevant_location_feature=f"ERA5 annual rainfall: {ann_precip:.1f} mm; SoilGrids infiltration: {infil_rate:.1f} mm/hr; Soil texture: {soil_tex}.",
                assumptions=["Runoff coefficient 0.85", "First-flush diverter efficiency 85%", "Non-potable water cost ₹95/m³"],
                missing_information=[],
                validation_requirements="Potable vs non-potable dual-pipe separation inspection per NBC 2016 Part 9."
            )
        )

        # =========================================================================
        # 5. GREEN INFRASTRUCTURE & TREE PRESERVATION (GFW, Sentinel-2, WorldCover, Dynamic World, SoilGrids)
        # =========================================================================
        recs.append(
            ComprehensiveRecommendation(
                id="REC-GREEN-005",
                category="environmental_sustainability",
                category_title="5. Green Infrastructure & Biodiversity Preservation",
                hierarchical_level="site",
                target_entity_id=target_entity_id,
                priority="critical" if canopy_pct > 20.0 else "high",
                title=f"Ecological Canopy Conservation Corridor ({canopy_pct:.1f}% Tree Density)",
                detected_condition=f"Site survey detects active tree canopy density of {canopy_pct:.1f}% (Global Forest Watch) with Sentinel-2 NDVI vigor '{vigor}' ({ndvi:.2f}).",
                evidence=f"Dynamic World records {veg_pct:.1f}% green space probability. SoilGrids identifies {soil_tex} with pH {soil_ph:.1f}, favorable for indigenous shade trees.",
                explanation="Mature trees provide irreplaceable radiant shade (-2.2°C ambient microclimate), reduce building cooling loads, sustain urban biodiversity, and prevent soil erosion.",
                proposed_intervention=f"Establish a mandatory 6.5m root-protection exclusion zone preserving mature broadleaf trees, augmented with native biophilic landscaping (Azadirachta indica, Pongamia pinnata) adapted to {soil_tex} soil.",
                expected_benefit=f"Preserves natural carbon sequestration (~{canopy_pct * 22:.0f} kg CO₂/yr), eliminates municipal felling penalties, and maintains natural evaporative microclimate cooling.",
                estimated_cost_inr=52000.0,
                time_horizon="immediate",
                confidence="high",
                data_sources=["Global Forest Watch", "Copernicus Sentinel-2", "ESA WorldCover 10m", "Dynamic World", "SoilGrids 250m"],
                contributing_datasets=["DS-04-GLOBAL-FOREST-WATCH", "DS-03-SENTINEL-2", "DS-01-ESA-WORLDCOVER", "DS-02-DYNAMIC-WORLD", "DS-07-SOILGRIDS"],
                relevant_building_feature=f"Site footprint perimeter setback ({footprint_w:.1f}m x {footprint_d:.1f}m).",
                relevant_location_feature=f"GFW canopy density: {canopy_pct:.1f}%; Sentinel-2 NDVI: {ndvi:.2f}; SoilGrids pH: {soil_ph:.1f}.",
                assumptions=["Root protection radius 4.5m around mature tree trunks"],
                missing_information=["Individual tree species health census"],
                validation_requirements="Certified arborist tree preservation survey prior to excavation permit."
            )
        )

        # =========================================================================
        # 6. BUILDING & URBAN SPATIAL ANALYSIS (OSM, MS Building Footprints, WorldCover)
        # =========================================================================
        recs.append(
            ComprehensiveRecommendation(
                id="REC-URBAN-006",
                category="urban_planning",
                category_title="6. Spatial & Infrastructure Optimisation",
                hierarchical_level="site",
                target_entity_id=target_entity_id,
                priority="medium",
                title=f"Urban Infrastructure Integration & Multi-Modal Access ({road_type.capitalize()} Road, {road_dist:.0f}m)",
                detected_condition=f"Site is located {road_dist:.0f}m from nearest mapped {road_type} road (OpenStreetMap) within an urban fabric of {bld_count} surrounding structures (MS Building Footprints).",
                evidence=f"Built-up footprint density ratio is {density_ratio:.2f} m²/m² (Microsoft Footprints) with {built_pct:.1f}% impervious coverage (ESA WorldCover).",
                explanation="In dense urban clusters, building orientation and access egress design directly affect neighborhood traffic flow, pedestrian safety, and microclimate air ventilation.",
                proposed_intervention=f"Align primary building pedestrian entrance toward the {road_type} corridor, incorporate a 3.5m perimeter acoustic vegetative buffer, and specify permeable interlocking pavement for vehicular parking.",
                expected_benefit="Enhances last-mile pedestrian transit safety, reduces surface runoff coefficient from 0.85 to 0.55 on vehicular areas, and dampens street noise by 6–8 dB.",
                estimated_cost_inr=78000.0,
                time_horizon="near_term_2026",
                confidence="high",
                data_sources=["OpenStreetMap", "Microsoft Global ML Building Footprints", "ESA WorldCover 10m"],
                contributing_datasets=["DS-05-OPENSTREETMAP", "DS-06-MS-BUILDING-FOOTPRINTS", "DS-01-ESA-WORLDCOVER"],
                relevant_building_feature=f"Ground floor entrance layout and site access frontage ({footprint_w:.1f}m width).",
                relevant_location_feature=f"OSM road distance: {road_dist:.0f}m ({road_type}); MS Footprints building count: {bld_count}; Density: {density_ratio:.2f}.",
                assumptions=["Municipal setback requirements conform to standard urban development authority bylaws"],
                missing_information=[],
                validation_requirements="Municipal town planning right-of-way compliance verification."
            )
        )

        # =========================================================================
        # 7. GEOTECHNICAL AND SUBSURFACE INTEGRITY
        # =========================================================================
        gw_depth = geo_profile.groundwater_table_m
        recs.append(
            ComprehensiveRecommendation(
                id="REC-GEO-007",
                category="geotechnical_suitability",
                category_title="B. Geotechnical & Site Suitability",
                hierarchical_level="site",
                target_entity_id=geo_profile.site_id,
                priority="critical" if gw_depth < 3.5 else "high",
                title="Subsurface Hydrostatic Pressure Relief & Waterproofing Barrier",
                detected_condition=f"Measured water table sits at {gw_depth:.1f}m below ground level in site borehole exploration logs.",
                evidence=f"Groundwater encountered at -{gw_depth:.1f}m within {geo_profile.dominant_soil_type}. Monsoonal rise adds up to +1.2m hydrostatic head.",
                explanation="Subsurface structures or deep basement footings risk buoyant uplift pressures, moisture seepage, and concrete sulfate degradation.",
                proposed_intervention="Specify continuous self-adhering HDPE waterproofing membrane below foundation slab and perimeter subsoil French drain perimeter loop.",
                expected_benefit="Prevents basement moisture ingress, dampens capillary rise, and eliminates sub-slab hydrostatic uplift risk.",
                estimated_cost_inr=145000.0,
                time_horizon="immediate",
                confidence="high",
                data_sources=["Apex Geo-Engineering Borehole Investigation Logs", "Central Ground Water Board (CGWB)"],
                contributing_datasets=[],
                relevant_building_feature="Foundation slab and basement retaining walls.",
                relevant_location_feature=f"Measured groundwater table: {gw_depth:.1f}m; Soil type: {geo_profile.dominant_soil_type}.",
                assumptions=["Finished excavation depth reaches 2.5m below finished ground level"],
                missing_information=[],
                validation_requirements="Continuous groundwater monitoring piezometer log across pre-monsoon and post-monsoon seasons."
            )
        )

        # =========================================================================
        # 8. STRUCTURAL ENGINEERING AUDIT & COMPLIANCE
        # =========================================================================
        model_detail = ModelStore.get_model(target_entity_id)
        structural_audit = model_detail.structural_audit if model_detail else None

        if structural_audit:
            missing_docs = structural_audit.get("missing_engineering_documentation", [])
            disclaimer = structural_audit.get("design_safety_disclaimer", "")
            load_bearing = structural_audit.get("load_bearing_elements_count", 0)
            partitions = structural_audit.get("partition_elements_count", 0)
            sys_type = structural_audit.get("structural_system_classification", "Unclassified")

            if missing_docs:
                recs.append(
                    ComprehensiveRecommendation(
                        id="REC-STR-008",
                        category="geotechnical_suitability",
                        category_title="B. Geotechnical & Structural Integrity",
                        hierarchical_level="building",
                        target_entity_id=target_entity_id,
                        priority="critical",
                        title=f"Structural Engineering Peer Review & Missing Documentation ({len(missing_docs)} Items Required)",
                        detected_condition=f"Digital twin contains {load_bearing} load-bearing structural elements and {partitions} partitions ({sys_type}). However, {len(missing_docs)} statutory engineering compliance items are absent.",
                        evidence=f"Missing verification items: {'; '.join(missing_docs[:4])}.",
                        explanation=disclaimer or "3D visual BIM geometry is not an engineered structural safety model. Commencing construction without verified structural calculations, rebar bar bending schedules, and concrete cube test records creates catastrophic collapse liabilities.",
                        proposed_intervention="Commission a licensed structural engineer of record (SER) to prepare finite element load analyses, ductile detailing per IS 13920, and 28-day concrete cube compression testing protocol.",
                        expected_benefit="Ensures building life safety, satisfies NBC Part 6 statutory criteria, and prevents uneven foundation differential settlement.",
                        estimated_cost_inr=125000.0,
                        time_horizon="immediate",
                        confidence="high",
                        data_sources=["IS 456:2000 Plain and Reinforced Concrete Code", "NBC 2016 Part 6", "IS 1893:2016"],
                        contributing_datasets=[],
                        relevant_building_feature=f"{load_bearing} load-bearing structural elements in {sys_type}.",
                        relevant_location_feature=f"Seismic Zone {geo_profile.seismic_zone} (PGA {geo_profile.peak_ground_acceleration_g}g).",
                        assumptions=["Physical building will require independent rebar and footing engineering drawings"],
                        missing_information=missing_docs,
                        validation_requirements="Registered Structural Engineer of Record (SER) certificate of structural design adequacy."
                    )
                )

        # =========================================================================
        # 9. 30-YEAR CARBON & FACADE LIFECYCLE
        # =========================================================================
        recs.append(
            ComprehensiveRecommendation(
                id="REC-LIFE-009",
                category="lifecycle_future_risk",
                category_title="E. Lifecycle & Future Risk",
                hierarchical_level="building",
                target_entity_id=target_entity_id,
                priority="medium",
                title="30-Year Low-Carbon Envelope Retrofit & Chiller Transition Plan",
                detected_condition="Building mechanical systems rely on R-410A refrigerant with standard 15-year lifecycle replacement intervals.",
                evidence=f"Projected 30-year operational energy carbon equals ~{gfa * 82.5 * 30 * 0.716 / 1000:,.0f} metric tons CO₂e. Projected CDD will increase by +18% under ERA5 climate trajectory.",
                explanation="Anticipated climate change will increase annual Cooling Degree Days (CDD), accelerating HVAC wear and increasing Scope 2 electricity costs.",
                proposed_intervention="Plan scheduled Year-12 replacement with ultra-low GWP R-32 or R-1234ze chillers and high-durability thermal facade coatings.",
                expected_benefit="Mitigates 24% lifecycle operational expenditure increase and reduces Scope 1 fugitive refrigerant emissions to near-zero.",
                estimated_cost_inr=280000.0,
                time_horizon="mid_term_2035",
                confidence="medium",
                data_sources=["IPCC AR6 Climate Scenarios", "ERA5 Atmospheric Reanalysis", "ASHRAE Guideline 14"],
                contributing_datasets=["DS-10-ERA5-REANALYSIS"],
                relevant_building_feature=f"Whole building mechanical chiller plant and {gfa:.1f} m² gross floor area.",
                relevant_location_feature=f"ERA5 baseline CDD: {cdd:.0f} degree-days with climate trend warming.",
                assumptions=["National electrical grid decarbonizes at 2.5% CAGR over 2026-2050"],
                missing_information=["Specific maintenance contract history and chiller operational logs"],
                validation_requirements="5-year continuous measurement and verification (M&V) logging against IPMVP standards."
            )
        )

        # =========================================================================
        # 10. INTERIOR SPATIAL EFFICIENCY & PASSIVE VENTILATION (IFC / 2D Interior Model)
        # =========================================================================
        from app.services.interior_furnishing_service import InteriorFurnishingService
        furn_plan = InteriorFurnishingService.get_furnishing_plan(target_entity_id)

        room_count = len(furn_plan.room_profiles) if furn_plan else max(1, int(gfa / 35.0))
        bath_count = sum(1 for item in (furn_plan.all_items if furn_plan else []) if item.category in ["toilet", "washbasin", "shower"])
        workstation_count = sum(1 for item in (furn_plan.all_items if furn_plan else []) if item.category in ["office_desk", "bed"])
        est_occupancy = max(4, workstation_count if workstation_count > 0 else int(gfa / 20.0))

        recs.append(
            ComprehensiveRecommendation(
                id="REC-INDOOR-010",
                category="environmental_sustainability",
                category_title="7. Interior Spatial Efficiency & Passive Ventilation",
                hierarchical_level="building",
                target_entity_id=target_entity_id,
                priority="medium",
                title=f"Interior Passive Ventilation & Low-Flow Water Fixture Optimization ({est_occupancy} Occupants)",
                detected_condition=f"Building interior contains {room_count} functional room zones with estimated occupancy of {est_occupancy} persons based on architectural furniture layout.",
                evidence=f"Furnished twin identifies {room_count} spatial zones across {floors} storeys. ERA5 prevailing wind direction is {wind_dir:.0f}° at {wind_speed:.1f} m/s (NASA POWER). Indoor fixtures comprise {bath_count} sanitary/plumbing points.",
                explanation=f"Aligning interior door circulation paths with prevailing {wind_dir:.0f}° summer wind corridors enables passive cross-ventilation, reducing mechanical fan energy while low-flow aerators reduce water consumption.",
                proposed_intervention=f"Install acoustic louvered interior door transoms along primary circulation paths to sustain cross-ventilation, coupled with 3.8 L/min low-flow aerators on {max(2, bath_count)} sanitary fixtures.",
                expected_benefit=f"Reduces indoor cooling hours by 12% during shoulder seasons and saves ~{est_occupancy * 25 * 300:,.0f} L/year in domestic water demand.",
                estimated_cost_inr=float(room_count * 4500 + max(2, bath_count) * 1200),
                time_horizon="near_term_2026",
                confidence="high",
                data_sources=["BIM Architectural Interior Model", "ERA5 Atmospheric Reanalysis", "NASA POWER Climatology", "NBC 2016 Part 8"],
                contributing_datasets=["DS-10-ERA5-REANALYSIS", "DS-09-NASA-POWER"],
                relevant_building_feature=f"Interior layout with {room_count} room zones, {window_count} windows, and {bath_count} plumbing fixtures.",
                relevant_location_feature=f"Prevailing wind direction: {wind_dir:.0f}°; Mean velocity: {wind_speed:.1f} m/s.",
                assumptions=["Standard occupancy density per furnished desk/bed capacity", "Acoustic transom rating STC ≥ 35"],
                missing_information=[],
                validation_requirements="Field anemometer airflow test across operable interior apertures during commissioning."
            )
        )

        # Category summary counts
        counts: Dict[str, int] = {}
        for r in recs:
            counts[r.category] = counts.get(r.category, 0) + 1

        return SustainabilityAuditReport(
            target_entity_id=target_entity_id,
            target_level=level,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            summary_counts=counts,
            recommendations=recs,
            insufficient_data_warnings=insufficient_data,
            dataset_statuses=dataset_status_map,
            location_profile=loc_profile
        )
