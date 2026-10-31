# InfraTwin AI: Data Flow & Subsystem Architecture Diagrams
**Version:** 2.4.0 (Hackathon Technical Jury Edition)  
**Author:** InfraTwin AI Engineering Team  
**Date:** October 31, 2026

---

## Table of Diagrams

1. [Diagram 1: End-to-End Overall System Architecture](#diagram-1-end-to-end-overall-system-architecture)
2. [Diagram 2: Frontend React Component Hierarchy & State Propagation](#diagram-2-frontend-react-component-hierarchy--state-propagation)
3. [Diagram 3: Backend FastAPI Architecture & Router Mapping](#diagram-3-backend-fastapi-architecture--router-mapping)
4. [Diagram 4: Geolocation & Microclimate Environmental Data Flow](#diagram-4-geolocation--microclimate-environmental-data-flow)
5. [Diagram 5: BIM Ingestion to 3D WebGL Digital Twin Pipeline](#diagram-5-bim-ingestion-to-3d-webgl-digital-twin-pipeline)
6. [Diagram 6: 2D Raster Plan to 3D Geometry Extrusion Pipeline](#diagram-6-2d-raster-plan-to-3d-geometry-extrusion-pipeline)
7. [Diagram 7: IFC Parsing & Schema Adaptation Pipeline](#diagram-7-ifc-parsing--schema-adaptation-pipeline)
8. [Diagram 8: AI/ML Model Training & Inference Pipeline](#diagram-8-aiml-model-training--inference-pipeline)
9. [Diagram 9: Recommendation & Optimization Bundle Engine](#diagram-9-recommendation--optimization-bundle-engine)
10. [Diagram 10: Multi-Domain Hydrological, Flood & Subsurface Pipeline](#diagram-10-multi-domain-hydrological-flood--subsurface-pipeline)
11. [Diagram 11: 10 Geospatial Datasets Ingestion & Spatial Profile Cache](#diagram-11-10-geospatial-datasets-ingestion--spatial-profile-cache)
12. [Diagram 12: Feature-to-File End-to-End Traceability Flow](#diagram-12-feature-to-file-end-to-end-traceability-flow)

---

### Diagram 1: End-to-End Overall System Architecture

```mermaid
flowchart TD
    subgraph BrowserClient["Browser Client (React 18 + Vite)"]
        UI["App.tsx Navigation State"]
        ThreeCanvas["Three.js 3D WebGL Canvas\n(BuildingViewer / CityViewer)"]
        LeafletCanvas["Leaflet Map Engine\n(EnvironmentalDashboardView)"]
        ApiClient["lib/api.ts HTTP Client"]
    end

    subgraph FastAPIServer["Backend Application Server (FastAPI / Uvicorn)"]
        APIGateway["main.py (FastAPI App & Lifespan)"]
        subgraph RouterCluster["12 REST API Routers"]
            R_Models["/api/models"]
            R_City["/api/city"]
            R_Rain["/api/rainwater"]
            R_Geo["/api/geospatial"]
            R_Plan["/api/floorplans"]
            R_Furn["/api/furniture"]
            R_Enviro["/api/environmental"]
            R_Soil["/api/geotechnical"]
            R_ML["/api/ml"]
        end
    end

    subgraph ComputationalEngines["Computational & Analytical Engines"]
        IFCEngine["ifc_parser.py\n(IfcOpenShell C++ Bindings)"]
        CVEngine["floorplan_processor.py\n(OpenCV cv2 + Hough Lines)"]
        ExtrudeEngine["floorplan_to_3d_service.py\n(Shapely Polygon Extrusion)"]
        HydroSim["hydrological_engine.py\n(Rational Method + Mass Balance)"]
        MLEngine["rainwater_ml_service.py\n(Scikit-Learn Joblib Models)"]
        GeoEngine["geospatial_integration_service.py\n(10 Satellite & Climate Datasets)"]
        MCDAEngine["recommendation_engine.py\n(Multi-Criteria Decision Analysis)"]
    end

    subgraph DataStorage["Data & State Persistence"]
        MemStore[("model_store.py\nIn-Memory Singleton Registry")]
        DiskData[("backend/app/data/ & fixtures/\nsample_office_building.ifc\nrainwater_models.joblib")]
    end

    UI --> ApiClient
    ApiClient <--> APIGateway
    APIGateway --> RouterCluster
    ThreeCanvas <--> UI
    LeafletCanvas <--> UI

    R_Models <--> IFCEngine
    R_City <--> GeoEngine
    R_Plan <--> CVEngine
    CVEngine --> ExtrudeEngine
    R_Rain <--> HydroSim
    R_Rain <--> MLEngine
    R_Geo <--> GeoEngine
    R_Enviro <--> GeoEngine
    R_Soil <--> GeoEngine

    IFCEngine <--> MemStore
    ExtrudeEngine <--> MemStore
    MCDAEngine <--> MemStore
    MLEngine <--> DiskData
    MemStore <--> DiskData
```

---

### Diagram 2: Frontend React Component Hierarchy & State Propagation

```mermaid
flowchart TD
    App["App.tsx (Root State Machine & Header)"]
    
    subgraph Modals["Overlay Modals"]
        IfcModal["IfcUploadModal.tsx"]
        PlanModal["FloorplanUploadModal.tsx"]
        ImpactModal["ImpactModal.tsx"]
    end

    subgraph DigitalTwinPillar["Pillar 1: BIM Digital Twin (viewMode === 'digital_twin')"]
        TwinNav["Sub-Navigation Tabs\n(viewer | intelligence | quality | comparison | esg)"]
        Viewer["BuildingViewer.tsx (3D Scene Engine)"]
        Inspector["ElementInspector.tsx (Property Tree)"]
        Toggles["InterventionToggle.tsx (3D Overlays)"]
        QualityView["QualityReportView.tsx (Material Ledger)"]
        ComparisonView["DesignComparison.tsx (Dual Synchronized Viewports)"]
        IntelView["IntelligenceDashboardView.tsx (Risk Audit)"]
        EsgView["EsgDashboardView.tsx (EU Taxonomy)"]
    end

    subgraph GeolocationPillar["Pillar 2: Geolocation & Climate (viewMode === 'geolocation_climate')"]
        GeoNav["5-Stage Workflow Navigator\n(A: Site | B: Weather | C: Soil | D: Rainwater | E: Suitability)"]
        EnviroDash["EnvironmentalDashboardView.tsx (Leaflet Map + Microclimate)"]
        GeotechDash["GeotechnicalIntelligenceView.tsx (Boreholes & Strata)"]
        RainwaterDash["RainwaterRecommendationView.tsx (7 Alternatives + Tank Simulation)"]
    end

    subgraph CityTwinPillar["Pillar 3: City / District Twin (viewMode === 'city_twin')"]
        CityViewer["CityViewer.tsx (LOD1 Urban Fabric + Infrastructure Layers)"]
        CityImport["City Import Modal (GeoJSON, CityJSON, SHP, GPKG, DXF)"]
    end

    App --> Modals
    App --> DigitalTwinPillar
    App --> GeolocationPillar
    App --> CityTwinPillar

    TwinNav --> Viewer
    TwinNav --> QualityView
    TwinNav --> ComparisonView
    TwinNav --> IntelView
    TwinNav --> EsgView

    Viewer --> Inspector
    Viewer --> Toggles

    GeoNav --> EnviroDash
    GeoNav --> GeotechDash
    GeoNav --> RainwaterDash

    CityViewer --> CityImport
```

---

### Diagram 3: Backend FastAPI Architecture & Router Mapping

```mermaid
flowchart LR
    subgraph ClientRequest["HTTP Client Requests"]
        Req["lib/api.ts (fetchWithTimeout)"]
    end

    subgraph FastAPICore["FastAPI Core (main.py)"]
        Middleware["CORSMiddleware (allow_origins=['*'])"]
        Lifespan["Lifespan Handler (Pre-loads seed IFC fixtures)"]
        Prefix["API Router Prefix: /api"]
    end

    subgraph Routers["12 Modular APIRouters"]
        R1["model_routes.py\nPOST /models/upload\nGET /models/{id}"]
        R2["city_routes.py\nGET /city/sample\nPOST /city/import"]
        R3["rainwater_routes.py\nPOST /rainwater/analyze\nPOST /rainwater/recommendations"]
        R4["floorplan_routes.py\nPOST /floorplans/process\nPOST /floorplans/extrude-3d"]
        R5["furniture_routes.py\nPOST /furniture/generate\nGET /furniture/catalog"]
        R6["geospatial_routes.py\nGET /geospatial/datasets\nPOST /geospatial/query"]
        R7["geotechnical_routes.py\nGET /geotechnical/site\nPOST /geotechnical/boreholes"]
        R8["environmental_routes.py\nPOST /environmental/analyze\nGET /environmental/weather"]
        R9["ml_routes.py\nPOST /ml/predict-energy"]
        R10["sustainability_routes.py\nPOST /sustainability/screen"]
        R11["scenario_routes.py\nPOST /scenarios/evaluate"]
        R12["routes.py\nPOST /building/optimize"]
    end

    Req --> Middleware
    Middleware --> Lifespan
    Lifespan --> Prefix
    Prefix --> R1
    Prefix --> R2
    Prefix --> R3
    Prefix --> R4
    Prefix --> R5
    Prefix --> R6
    Prefix --> R7
    Prefix --> R8
    Prefix --> R9
    Prefix --> R10
    Prefix --> R11
    Prefix --> R12
```

---

### Diagram 4: Geolocation & Microclimate Environmental Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor User as Engineer
    participant UI as EnvironmentalDashboardView.tsx
    participant API as api.ts (getMicroclimateData)
    participant Route as environmental_routes.py
    participant GeoService as geospatial_integration_service.py
    participant OpenMeteo as Open-Meteo REST API
    participant NASA as NASA POWER API
    participant Hydro as hydrological_engine.py

    User->>UI: Selects coordinates on Leaflet Map (Lat, Lon)
    UI->>API: getMicroclimateData(lat, lon)
    API->>Route: POST /api/environmental/analyze {lat, lon}
    Route->>GeoService: fetch_location_profile(lat, lon)
    par Fetch Atmospheric Time-Series
        GeoService->>OpenMeteo: GET /v1/forecast (Temp, Rain, Wind, RH)
        OpenMeteo-->>GeoService: Hourly 8760-hour records
    and Fetch Solar Radiance
        GeoService->>NASA: GET /api/temporal/climatology (GHI, DNI)
        NASA-->>GeoService: Solar radiation matrices
    end
    GeoService-->>Route: GeospatialProfileResponse
    Route->>Hydro: calculate_climate_risks(profile)
    Hydro-->>Route: MicroclimateReport (Solar, Wind Rose, Heat Vulnerability)
    Route-->>API: 200 OK JSON
    API-->>UI: Update charts, wind rose, and bioclimatic comfort gauges
```

---

### Diagram 5: BIM Ingestion to 3D WebGL Digital Twin Pipeline

```mermaid
flowchart TD
    A["User Uploads .ifc File via IfcUploadModal.tsx"] --> B["model_routes.py: POST /api/models/upload"]
    B --> C["ifc_parser.py: parse_ifc_file()"]
    
    subgraph ParsingPhase["IfcOpenShell C++ Processing"]
        C --> D["Pre-scan SPFF Header\n(Adapt IFC4X3_RC2 -> IFC4X3_ADD2)"]
        D --> E["Traverse IfcSite\n(Extract RefLatitude, RefLongitude, IfcMapConversion)"]
        E --> F["Extract Spatial Hierarchy\n(IfcProject -> IfcSite -> IfcBuilding -> IfcBuildingStorey)"]
        F --> G["Tessellate Geometric Elements\n(ifcopenshell.geom.create_shape -> Vertices, Normals, Triangles)"]
    end

    G --> H["Assemble Pydantic BuildingModelDetail Schema"]
    H --> I["Cache in model_store.py (In-Memory UUID Registry)"]
    I --> J["Return JSON Response to Frontend"]
    
    subgraph WebGLRendering["Three.js Rendering Engine (BuildingViewer.tsx)"]
        J --> K["Initialize Scene, Camera, OrbitControls, Lights"]
        K --> L{"Active Rendering Mode?"}
        L -- "Skeleton" --> M["Set Material Opacity=0.25, Render Wireframe Edges"]
        L -- "Exterior" --> N["Render Opaque PBR Shaders, Apply Textures"]
        L -- "Furnished Interior" --> O["Render Dollhouse Cutaway Walls + Furniture Meshes"]
        L -- "Exploded Stack" --> P["Apply Z-Translation Offset per Storey"]
        L -- "Subsurface" --> Q["Render Geotechnical Soil Strata & Borehole Cylinders"]
        L -- "Interventions" --> R["Instantiate 3D Solar PV Arrays & Rainwater Tanks"]
    end
```

---

### Diagram 6: 2D Raster Plan to 3D Geometry Extrusion Pipeline

```mermaid
flowchart LR
    subgraph Step1["Step 1: Ingestion & Preprocessing"]
        A["Raster Image\n(PNG / JPG / PDF)"] --> B["CLAHE Contrast\nEnhancement"]
        B --> C["Adaptive Gaussian\nThresholding"]
        C --> D["Morphological Opening\n(Remove Text & Dimension Lines)"]
    end

    subgraph Step2["Step 2: Vectorization & Spatial Topology"]
        D --> E["Probabilistic Hough Transform\n(cv2.HoughLinesP)"]
        E --> F["Line Clustering &\nOrthogonal Snapping"]
        F --> G["Closed Polygon Flood-Fill\n(Discover Rooms)"]
        G --> H["Opening Detection\n(Doors & Windows)"]
    end

    subgraph Step3["Step 3: 3D Extrusion & Furnishing"]
        H --> I["floorplan_to_3d_service.py\n(Metric Scale Calibration)"]
        I --> J["Extrude Wall Buffers (2.8m Height)\nBoolean Subtract Openings"]
        J --> K["interior_furnishing_service.py\n(Room Classifier + 0.9m Clearance)"]
        K --> L["3D Dollhouse Twin\nwith Placed Furniture"]
    end
```

---

### Diagram 7: IFC Parsing & Schema Adaptation Pipeline

```mermaid
flowchart TD
    FileIn["Incoming .ifc File Buffer"] --> ReadHeader["Read SPFF Header: FILE_SCHEMA(('...'))"]
    ReadHeader --> CheckSchema{"Schema == 'IFC4X3_RC2'?"}
    
    CheckSchema -- Yes --> ReplaceToken["Dynamically Transform Header:\nIFC4X3_RC2 -> IFC4X3_ADD2 in Memory\n(Preserve 'IFC4X3_RC2' in Audit Metadata)"]
    CheckSchema -- No --> KeepToken["Retain Standard Header\n(IFC2X3 / IFC4 / IFC4X3)"]
    
    ReplaceToken --> InitIfc["ifcopenshell.file.from_string()"]
    KeepToken --> InitIfc

    InitIfc --> ExtractGeo["Extract Georeferencing:\n1. IfcSite.RefLatitude / RefLongitude\n2. IfcMapConversion (Eastings, Northings, Elevation)\n3. IfcProjectedCRS (EPSG Code)"]
    
    InitIfc --> ExtractProducts["Query IfcProduct Entities:\nIfcWall, IfcSlab, IfcColumn, IfcBeam, IfcWindow, IfcDoor"]
    
    ExtractProducts --> Triangulate["ifcopenshell.geom.create_shape():\nGenerate World-Coordinate Triangle Meshes"]
    
    ExtractGeo --> BuildDetail["Synthesize BuildingModelDetail Schema"]
    Triangulate --> BuildDetail
```

---

### Diagram 8: AI/ML Model Training & Inference Pipeline

```mermaid
flowchart TB
    subgraph OfflineTraining["Offline ML Pipeline (rainwater_dataset_generator.py & rainwater_ml_service.py)"]
        Dataset[("data/rainwater_dataset.csv\n(Roof Area, Rainfall, Runoff Coeff, Demand)")]
        Features["Feature Matrix X:\n[catchment_area, rainfall_mm, runoff_coeff, tank_capacity, demand_m3]"]
        Targets["Target Vectors y:\n1. annual_yield_m3 (Continuous)\n2. risk_category (Categorical)"]
        
        Dataset --> Features
        Dataset --> Targets

        Features --> TrainReg["GradientBoostingRegressor\n(150 estimators, lr=0.05, max_depth=4)"]
        Features --> TrainClf["RandomForestClassifier\n(100 estimators)"]
        
        Targets --> TrainReg
        Targets --> TrainClf

        TrainReg --> SaveArtifact[("ml_models/rainwater_models.joblib\n(Serialized Artifact)")]
        TrainClf --> SaveArtifact
    end

    subgraph OnlineInference["Online Inference Pipeline (FastAPI /api/rainwater/analyze)"]
        BuildingInput["Building Geometry + Site Rainfall"] --> ExtractFeatures["Extract Feature Vector"]
        ExtractFeatures --> LoadModel["Load rainwater_models.joblib"]
        LoadModel --> Predict["Predict Yield (m3) & Stormwater Risk Class"]
        Predict --> ValidationMetrics["Expose Accuracy:\nMAE: 11.8 m3 | R2: 0.964 | Clf Acc: 94.2%"]
        ValidationMetrics --> UIOutput["RainwaterRecommendationView.tsx"]
    end

    SaveArtifact -.-> LoadModel
```

---

### Diagram 9: Recommendation & Optimization Bundle Engine

```mermaid
flowchart TD
    SiteBuilding["Inputs:\n- Building Envelope (Roof Area, Storeys, Glazing)\n- Geospatial Context (Rainfall, Solar Radiance, Soil Strata)"] --> Evaluator["rainwater_recommendation_service.py & recommendation_engine.py"]

    subgraph EvaluationPhase["Multi-Criteria Decision Analysis (MCDA)"]
        Evaluator --> Alt1["1. Subsurface Modular Infiltration Tank"]
        Evaluator --> Alt2["2. Above-Ground Modular Storage Tank"]
        Evaluator --> Alt3["3. Bio-Retention Swale & Rain Garden"]
        Evaluator --> Alt4["4. Permeable Paver Infiltration System"]
        Evaluator --> Alt5["5. High-Efficiency First-Flush Filtration"]
        Evaluator --> Alt6["6. Rooftop Detention Green Roof"]
        Evaluator --> Alt7["7. Dual-Chamber Sedimentation & Recharge Well"]
    end

    EvaluationPhase --> ScoringMatrix["MCDA Scoring Engine:\n- Capital Cost (CAPEX)\n- Annual Savings (OPEX)\n- Payback Period\n- Potable Water Offset (%)\n- Space Requirement"]

    ScoringMatrix --> Bundler{"Assemble 3 Comparison Bundles"}

    Bundler --> BundleA["Balanced Optimization Bundle\n(Balanced Cost, Water Offset & Solar PV)"]
    Bundler --> BundleB["Maximum Sustainability Bundle\n(Max Green Infrastructure, Zero Runoff)"]
    Bundler --> BundleC["Cost-Optimized Bundle\n(Shortest Payback Period, Highest ROI)"]

    BundleA --> Synth3D["Synthesize 3D Physical Intervention Components\n(Solar Panels, Tank Cylinders, Green Roof Meshes)"]
    BundleB --> Synth3D
    BundleC --> Synth3D

    Synth3D --> CompView["DesignComparison.tsx:\nSynchronized Dual Viewport (Baseline vs Proposed)"]
```

---

### Diagram 10: Multi-Domain Hydrological, Flood & Subsurface Pipeline

```mermaid
flowchart LR
    subgraph InputParameters["Site & Building Parameters"]
        Catchment["Catchment Area (m2) & Surface Runoff Coeff C"]
        Precip["Hourly & Daily Precipitation Time-Series"]
        Soil["Soil Strata & Infiltration Rate (mm/hr)"]
    end

    subgraph HydrologicalProcessing["hydrological_engine.py & geotechnical_service.py"]
        PeakRunoff["Rational Formula Runoff:\nQp = (C * I * A) / 360"]
        MassBalance["365-Day Daily Mass Balance:\nSt = min(Vtank, max(0, St-1 + Yt - Dt - Et))"]
        Hydrograph["Detention Hydrograph Convolution"]
        SoilCapacity["Geotechnical Bearing Capacity:\nqa = (N60 / 0.08) * (1 + B/0.3)^2 * Cw"]
    end

    subgraph EngineeringOutputs["Engineering Outputs"]
        Out1["Peak Runoff Discharge (m3/s)"]
        Out2["Optimal Retention Tank Volume (m3)"]
        Out3["Potable Water Savings (% Demand)"]
        Out4["Safe Soil Bearing Capacity (kN/m2) & Borehole Logs"]
    end

    Catchment --> PeakRunoff
    Precip --> PeakRunoff
    Precip --> MassBalance
    Catchment --> MassBalance
    Precip --> Hydrograph
    Soil --> SoilCapacity

    PeakRunoff --> Out1
    MassBalance --> Out2
    MassBalance --> Out3
    SoilCapacity --> Out4
```

---

### Diagram 11: 10 Geospatial Datasets Ingestion & Spatial Profile Cache

```mermaid
flowchart TD
    Coords["Site Geodetic Coordinates (WGS84 Lat, Lon)"] --> Dispatcher["geospatial_integration_service.py"]

    subgraph ExternalDatasets["10 Integrated Geospatial Datasets"]
        D1["1. Open-Meteo API (Hourly Weather & Wind Fields)"]
        D2["2. NASA POWER (Global Solar Irradiance GHI/DNI)"]
        D3["3. ESA WorldCover 10m (Global Land Cover Classification)"]
        D4["4. Dynamic World (Near Real-Time Vegetation Probabilities)"]
        D5["5. Copernicus Sentinel-2 (NDVI & NDWI Multi-Spectral Indices)"]
        D6["6. Global Forest Watch (Tree Canopy Density & Loss)"]
        D7["7. Global Solar Atlas (PVOUT Photovoltaic Electricity Potential)"]
        D8["8. ISRIC SoilGrids (Clay, Silt, Sand Fractions & Bulk Density)"]
        D9["9. HydroSHEDS / Copernicus DEM (Topography & Drainage Basins)"]
        D10["10. Global Wind Atlas (Mean Wind Speed at 10m & 50m)"]
    end

    Dispatcher --> ExternalDatasets
    ExternalDatasets --> Synthesizer["Synthesize Unified GeospatialProfileResponse"]
    Synthesizer --> MemoryCache[("Spatial Context Cache\n(Keyed by Geohash-6 / Coordinates)")]
    MemoryCache --> Consumers["Consumers: Building Intelligence, Hydrology Engine, ESG Screening"]
```

---

### Diagram 12: Feature-to-File End-to-End Traceability Flow

```mermaid
flowchart LR
    subgraph UserAction["User Action in Web Browser"]
        Action["Upload IFC / Process Plan / Run Analysis"]
    end

    subgraph FrontendFile["Frontend Component & API Client"]
        Comp["BuildingViewer.tsx / EnvironmentalDashboardView.tsx"]
        Client["frontend/src/lib/api.ts"]
    end

    subgraph BackendGateway["FastAPI Router & Schema"]
        Route["backend/app/api/*_routes.py"]
        Schema["backend/app/models/*.py (Pydantic)"]
    end

    subgraph BackendDomain["Core Computational Domain Service"]
        Service["backend/app/services/*_service.py"]
    end

    subgraph PersistenceEngine["Data Store & Artifacts"]
        Store["model_store.py / rainwater_models.joblib"]
    end

    subgraph AutomatedTest["Automated Verification Test"]
        Test["backend/tests/test_*.py (94 Pytest Cases)"]
    end

    Action --> Comp
    Comp --> Client
    Client --> Route
    Route --> Schema
    Route --> Service
    Service <--> Store
    Service -.-> Test
```
