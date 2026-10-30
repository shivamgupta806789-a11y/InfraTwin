from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class DatasetMetadata(BaseModel):
    dataset_id: str
    name: str
    primary_category: str  # 'land_cover', 'vegetation', 'satellite_imagery', 'building_footprints', 'infrastructure', 'soil_properties', 'hydrography', 'climate', 'solar_exposure', 'urban_land_use'
    usage_bucket: str  # 'A_supervised_ml', 'B_direct_gis_analysis', 'C_model_validation', 'D_simulation_data'
    source: str
    license: str
    geographic_coverage: str
    spatial_resolution: str
    temporal_coverage: str
    available_features: List[str]
    available_labels: List[str]
    potential_ml_tasks: List[str]
    limitations: List[str]
    provenance_reference: str
    is_active_in_pipeline: bool = True


class DatasetRegistryService:
    """
    Registry and Governance Service for Candidate Environmental and Urban Intelligence Datasets.
    Strictly categorizes data across:
    A. Datasets suitable for supervised ML training.
    B. GIS datasets used directly for spatial analysis.
    C. Datasets used for model validation.
    D. Simulation-generated training data.
    """

    CANDIDATE_DATASETS: Dict[str, DatasetMetadata] = {
        "DS-01-ESA-WORLDCOVER": DatasetMetadata(
            dataset_id="DS-01-ESA-WORLDCOVER",
            name="ESA WorldCover 10m",
            primary_category="land_cover",
            usage_bucket="C_model_validation",
            source="European Space Agency (ESA) & VITO Remote Sensing",
            license="Creative Commons Attribution 4.0 International (CC BY 4.0)",
            geographic_coverage="Global (land masses)",
            spatial_resolution="10 meters per pixel",
            temporal_coverage="Annual snapshots (2020, 2021)",
            available_features=["Discrete LULC classification band derived from Sentinel-1 SAR and Sentinel-2 optical data"],
            available_labels=["Tree cover (10)", "Shrubland (20)", "Grassland (30)", "Cropland (40)", "Built-up (50)", "Bare / sparse vegetation (60)", "Snow and ice (70)", "Permanent water bodies (80)", "Herbaceous wetland (90)", "Mangroves (95)", "Moss and lichen (100)"],
            potential_ml_tasks=["Ground-truth validation benchmark for urban footprint boundary verification", "Regional land cover change detection benchmark"],
            limitations=["Annual cadence does not capture seasonal monsoonal vegetation variations", "Single dominant label per 100 m² pixel obscures sub-pixel courtyard trees"],
            provenance_reference="Zanaga et al. (2022). ESA WorldCover 10 m 2021 v200. https://doi.org/10.5281/zenodo.5571936"
        ),

        "DS-02-DYNAMIC-WORLD": DatasetMetadata(
            dataset_id="DS-02-DYNAMIC-WORLD",
            name="Dynamic World (Google / WRI)",
            primary_category="urban_land_use",
            usage_bucket="A_supervised_ml",
            source="Google, World Resources Institute (WRI), National Geographic Society",
            license="Creative Commons Attribution 4.0 International (CC BY 4.0)",
            geographic_coverage="Global",
            spatial_resolution="10 meters per pixel",
            temporal_coverage="Near real-time (2015 - present, updated every 2-5 days with Sentinel-2 overpasses)",
            available_features=["9 probability channels corresponding to discrete land cover classes per pixel"],
            available_labels=["water", "trees", "grass", "flooded_vegetation", "crops", "shrub_and_scrub", "built", "bare", "snow_and_ice"],
            potential_ml_tasks=["Multi-class land cover semantic segmentation", "Temporal vegetation health forecasting", "Urban sprawl rate prediction"],
            limitations=["Cloud cover and cloud shadows degrade optical scene quality during peak monsoon months", "Low probability thresholding required for thin urban linear parks"],
            provenance_reference="Brown et al. (2022). Dynamic World, Near real-time global 10m selective land use land cover mapping. Scientific Data, 9(1), 251."
        ),

        "DS-03-SENTINEL-2": DatasetMetadata(
            dataset_id="DS-03-SENTINEL-2",
            name="Copernicus Sentinel-2 L2A Multispectral Bottom-of-Atmosphere Reflectance",
            primary_category="satellite_imagery",
            usage_bucket="A_supervised_ml",
            source="European Space Agency (ESA) Copernicus Programme",
            license="Copernicus Open Access Free, Full and Open Data Policy",
            geographic_coverage="Global between 56°S and 84°N",
            spatial_resolution="10m (B2, B3, B4, B8), 20m (B5, B6, B7, B8A, B11, B12), 60m (B1, B9, B10)",
            temporal_coverage="5-day revisit cycle with twin satellites (Sentinel-2A and 2B)",
            available_features=["12 spectral bands (Visible RGB, Red Edge 1-3, NIR, Narrow NIR, SWIR-1, SWIR-2)", "Calculated indices: NDVI, NDWI, NDBI, SAVI"],
            available_labels=["Requires manual segmentation or automated transfer labels from OpenStreetMap / WorldCover"],
            potential_ml_tasks=["Urban tree canopy health regression (NDVI)", "Impervious surface fraction estimation (NDBI)", "Rooftop high-albedo material classification"],
            limitations=["10m resolution cannot delineate individual street trees (only canopy clusters > 100 m²)", "Atmospheric correction artifacts in high-turbidity coastal or desert regions"],
            provenance_reference="Drusch et al. (2012). Sentinel-2: ESA's Optical High Resolution Mission for GMES Operational Services. Remote Sensing of Environment, 120, 25-36."
        ),

        "DS-04-GLOBAL-FOREST-WATCH": DatasetMetadata(
            dataset_id="DS-04-GLOBAL-FOREST-WATCH",
            name="Hansen Global Forest Change (GFW)",
            primary_category="vegetation",
            usage_bucket="B_direct_gis_analysis",
            source="University of Maryland, Google, USGS, NASA, World Resources Institute",
            license="Creative Commons Attribution 4.0 International (CC BY 4.0)",
            geographic_coverage="Global (excluding Antarctica and islands)",
            spatial_resolution="30 meters (~0.00025 degrees)",
            temporal_coverage="2000 - 2023 annual updates",
            available_features=["Tree canopy cover percentage (0-100% canopy density for year 2000)", "Forest gain (2000-2012)", "Annual forest loss year (2001-2023)"],
            available_labels=["Tree canopy density threshold (>10%, >30%, >50%)", "Year of deforestation event"],
            potential_ml_tasks=["Long-term tree loss vulnerability modeling", "Regional deforestation risk regression"],
            limitations=["30m resolution is coarse for urban parcel tree preservation (better suited to peri-urban / campus scales)", "Does not distinguish native ecological forest from monoculture commercial plantations"],
            provenance_reference="Hansen et al. (2013). High-Resolution Global Maps of 21st-Century Forest Cover Change. Science, 342(6160), 850-853."
        ),

        "DS-05-OPENSTREETMAP": DatasetMetadata(
            dataset_id="DS-05-OPENSTREETMAP",
            name="OpenStreetMap (OSM) Vector Feature Database",
            primary_category="infrastructure",
            usage_bucket="B_direct_gis_analysis",
            source="OpenStreetMap Foundation & Worldwide Contributor Community",
            license="Open Database License (ODbL) 1.0",
            geographic_coverage="Global",
            spatial_resolution="Sub-meter vector precision (points, lines, polygons)",
            temporal_coverage="Continuous live updates (minutely to daily regional planet dumps)",
            available_features=["Highways (motorway to residential paths)", "Building footprints & levels", "Waterways (rivers, streams, canals)", "Natural elements (trees, wood, water)", "Land use (residential, commercial, industrial, park)"],
            available_labels=["highway=* tags", "building=* tags", "natural=* tags", "amenity=* tags"],
            potential_ml_tasks=["Road network graph connectivity analysis", "Urban block morphology clustering", "Building height estimation from shadow vectors"],
            limitations=["Crowdsourced completeness varies geographically (dense urban centers are rich; informal peri-urban zones are sparse)", "Building heights and floor numbers are frequently unrecorded (~15% attribute completeness)"],
            provenance_reference="Haklay & Weber (2008). OpenStreetMap: User-Generated Street Maps. IEEE Pervasive Computing, 7(4), 12-18."
        ),

        "DS-06-MS-BUILDING-FOOTPRINTS": DatasetMetadata(
            dataset_id="DS-06-MS-BUILDING-FOOTPRINTS",
            name="Microsoft Global ML Building Footprints",
            primary_category="building_footprints",
            usage_bucket="A_supervised_ml",
            source="Microsoft AI for Good & Bing Maps",
            license="Open Database License (ODbL) 1.0",
            geographic_coverage="1.2+ Billion buildings worldwide across 100+ countries",
            spatial_resolution="High-resolution vector polygons (derived from 30cm - 60cm imagery)",
            temporal_coverage="Static imagery composite (2019 - 2023 depending on region)",
            available_features=["Polygon geometries in GeoJSON / GeoPackage format"],
            available_labels=["Building footprint boundaries"],
            potential_ml_tasks=["District-scale building density estimation", "Spatial clustering & urban block classification", "Automated roof surface area extraction"],
            limitations=["Contains planar 2D footprint polygons only; no height, floor count, or structural typology attributes", "Slight polygon vertex jitter under dense tree canopy occlusion"],
            provenance_reference="Microsoft (2023). Global ML Building Footprints Dataset. https://github.com/microsoft/GlobalMLBuildingFootprints"
        ),

        "DS-07-SOILGRIDS": DatasetMetadata(
            dataset_id="DS-07-SOILGRIDS",
            name="SoilGrids 250m v2.0 (ISRIC - World Soil Information)",
            primary_category="soil_properties",
            usage_bucket="B_direct_gis_analysis",
            source="ISRIC - World Soil Information (International Soil Reference and Information Centre)",
            license="Creative Commons Attribution 4.0 International (CC BY 4.0)",
            geographic_coverage="Global (excluding deserts and permanent ice)",
            spatial_resolution="250 meters per pixel",
            temporal_coverage="Static climatological depth profile (standard depths: 0-5cm, 5-15cm, 15-30cm, 30-60cm, 60-100cm, 100-200cm)",
            available_features=["Clay content (g/kg)", "Sand content (g/kg)", "Silt content (g/kg)", "Bulk density of fine earth (cg/cm³)", "Soil pH in H2O", "Soil organic carbon (dg/kg)", "Cation exchange capacity (mmol(c)/kg)"],
            available_labels=["USDA Soil Texture Class", "WRB Soil Classification Group"],
            potential_ml_tasks=["Regional preliminary soil bearing capacity regression", "Foundation liquefaction susceptibility screening", "Soil permeability estimation for stormwater infiltration"],
            limitations=["250m resolution represents regional pedological interpolation; cannot replace site-specific exploratory borehole drilling", "Does not capture deep bedrock strata below 2.0 meters depth"],
            provenance_reference="Poggio et al. (2021). SoilGrids 2.0: Producing soil information for the globe with quantified spatial uncertainty. SOIL, 7(1), 217-240."
        ),

        "DS-08-HYDROSHEDS": DatasetMetadata(
            dataset_id="DS-08-HYDROSHEDS",
            name="HydroSHEDS & HydroBASINS v1.2",
            primary_category="hydrography",
            usage_bucket="B_direct_gis_analysis",
            source="World Wildlife Fund (WWF), USGS, NASA, CIAT, TNC",
            license="Creative Commons Attribution 4.0 International (CC BY 4.0)",
            geographic_coverage="Global between 60°N and 56°S",
            spatial_resolution="3 arc-seconds (~90 meters) and 15 arc-seconds (~450 meters)",
            temporal_coverage="Static baseline hydrological elevation model (derived from SRTM elevation)",
            available_features=["Hydrologically conditioned digital elevation model (DEM)", "D8 flow direction grid", "Flow accumulation (upstream catchment area in km²)", "Vector river network lines with stream order (Strahler)"],
            available_labels=["Pfafstetter sub-basin hierarchical codes (Levels 1 - 12)"],
            potential_ml_tasks=["Catchment runoff peak discharge prediction", "Overland flood flow path classification", "Urban stormwater detention basin capacity sizing"],
            limitations=["90m DEM does not resolve local urban street curbs, storm sewers, or artificial retention culverts", "SRTM radar data penetrated vegetation canopy with variable bias"],
            provenance_reference="Lehner, Verdin, & Jarvis (2008). New Global Hydrography Derived From Spaceborne Elevation Data. Eos, Transactions American Geophysical Union, 89(10), 93-94."
        ),

        "DS-09-NASA-POWER": DatasetMetadata(
            dataset_id="DS-09-NASA-POWER",
            name="NASA POWER (Prediction of Worldwide Energy Resources)",
            primary_category="solar_exposure",
            usage_bucket="B_direct_gis_analysis",
            source="NASA Langley Research Center, NASA Earth Science Division",
            license="Public Domain (US Government Open Data)",
            geographic_coverage="Global grid",
            spatial_resolution="0.5° latitude x 0.625° longitude (~50km)",
            temporal_coverage="Hourly and daily time-series from 1981 to present (near-real-time lag of ~2 days)",
            available_features=["All-Sky Surface Shortwave Downward Irradiance (GHI in kWh/m²/day)", "Direct Normal Irradiance (DNI)", "Diffuse Horizontal Irradiance", "Surface Albedo", "2m Ambient Temperature", "Relative Humidity", "Wind Speed at 10m & 50m"],
            available_labels=["Solar insolation clearness index (Kt)"],
            potential_ml_tasks=["Solar photovoltaic annual yield forecasting", "Hourly building cooling load prediction", "Passive daylight availability simulation"],
            limitations=["Regional 50km grid resolution does not capture localized urban canyon microclimate shading from adjacent skyscrapers", "Hourly interpolation in mountainous terrain has elevation bias"],
            provenance_reference="Stackhouse et al. (2018). The NASA POWER Project: A Global Data Set for Renewable Energy and Building Climate Analysis. NASA Technical Report."
        ),

        "DS-10-ERA5-REANALYSIS": DatasetMetadata(
            dataset_id="DS-10-ERA5-REANALYSIS",
            name="ERA5 Atmospheric Reanalysis (ECMWF Copernicus Climate Change Service)",
            primary_category="climate",
            usage_bucket="C_model_validation",
            source="European Centre for Medium-Range Weather Forecasts (ECMWF)",
            license="Copernicus Open Access License",
            geographic_coverage="Global atmosphere and surface",
            spatial_resolution="0.25° x 0.25° (~31km grid)",
            temporal_coverage="Hourly from 1940 to present",
            available_features=["2m Dry-Bulb Temperature", "2m Dewpoint Temperature", "Surface Pressure", "10m U/V Wind Velocity Vectors", "Total Precipitation (liquid and solid)", "Surface Solar Radiation Downwards", "Boundary Layer Height"],
            available_labels=["Extreme Weather Event Indicators (Heatwave, Cloudburst, Cold Surge)"],
            potential_ml_tasks=["Building climate resilience stress testing", "Long-term Heating & Cooling Degree Day (HDD/CDD) trajectory projection", "Microgrid renewable generation volatility modeling"],
            limitations=["Spatial scale (~31km) requires statistical or dynamical downscaling to capture building-scale thermal comfort", "Extreme localized convective microbursts can be underestimated"],
            provenance_reference="Hersbach et al. (2020). The ERA5 Global Reanalysis. Quarterly Journal of the Royal Meteorological Society, 146(730), 1999-2049."
        ),

        "DS-11-DOE-BUILDING-SIMULATION": DatasetMetadata(
            dataset_id="DS-11-DOE-BUILDING-SIMULATION",
            name="U.S. DOE Commercial & Residential Prototype Building EnergyPlus Simulations",
            primary_category="building_footprints",
            usage_bucket="D_simulation_data",
            source="U.S. Department of Energy (DOE) & Pacific Northwest National Laboratory (PNNL)",
            license="Open Source (U.S. Government Open Data License)",
            geographic_coverage="16 Standard ASHRAE / IECC Climate Zones",
            spatial_resolution="Building-level and thermal zone-level (0.1m simulation domain)",
            temporal_coverage="8,760 hourly annual simulation profiles across multiple code editions",
            available_features=["Zone hourly cooling load (W)", "Zone heating load (W)", "Window daylight illuminance (lux)", "Infiltration rate (ACH)", "Internal heat gain schedules"],
            available_labels=["Whole-building Energy Use Intensity (EUI in kWh/m²/yr)", "Peak cooling demand (kW)", "Annual electricity and gas consumption"],
            potential_ml_tasks=["Physics-informed neural network (PINN) surrogate model training for instantaneous energy prediction", "Synthetic transfer learning for data-sparse geographies"],
            limitations=["Simulation models use standardized operational schedules that do not capture idiosyncratic occupant behavior in real buildings", "Requires envelope calibration against local construction materials"],
            provenance_reference="Deru et al. (2011). U.S. Department of Energy Commercial Reference Building Models of the National Building Stock. NREL/TP-5500-46861."
        )
    }

    @classmethod
    def get_dataset(cls, dataset_id: str) -> Optional[DatasetMetadata]:
        return cls.CANDIDATE_DATASETS.get(dataset_id)

    @classmethod
    def list_all_datasets(cls) -> List[DatasetMetadata]:
        return list(cls.CANDIDATE_DATASETS.values())

    @classmethod
    def filter_by_bucket(cls, bucket: str) -> List[DatasetMetadata]:
        return [d for d in cls.CANDIDATE_DATASETS.values() if d.usage_bucket == bucket]

    @classmethod
    def get_governance_summary(cls) -> Dict[str, Any]:
        """
        Returns strict dataset usage breakdown to prevent data contamination across tasks.
        """
        all_ds = list(cls.CANDIDATE_DATASETS.values())
        return {
            "total_candidate_datasets": len(all_ds),
            "usage_breakdown": {
                "A_supervised_ml": len([d for d in all_ds if d.usage_bucket == "A_supervised_ml"]),
                "B_direct_gis_analysis": len([d for d in all_ds if d.usage_bucket == "B_direct_gis_analysis"]),
                "C_model_validation": len([d for d in all_ds if d.usage_bucket == "C_model_validation"]),
                "D_simulation_data": len([d for d in all_ds if d.usage_bucket == "D_simulation_data"]),
            },
            "governance_rules": [
                "1. Supervised ML datasets (Bucket A) must undergo 80/10/10 train/validation/test split with no cross-contamination.",
                "2. Direct GIS datasets (Bucket B) are deterministic geospatial overlays and must not be used as training targets.",
                "3. Model validation datasets (Bucket C) are strictly held-out real-world observations for calculating MAE, RMSE, and R².",
                "4. All models must record dataset provenance, license compliance, and resolution caveats in their inference response."
            ]
        }
