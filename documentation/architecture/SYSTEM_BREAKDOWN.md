# InfraTwin AI: Comprehensive 19-System Engineering Breakdown
**Version:** 2.4.0 (Hackathon Technical Jury Edition)  
**Author:** InfraTwin AI Engineering Team  
**Date:** October 31, 2026

---

## System Index

1. [Frontend / User Interface](#1-frontend--user-interface)
2. [Authentication & User Management](#2-authentication--user-management)
3. [Building Data Input Subsystem](#3-building-data-input-subsystem)
4. [Geolocation & Spatial Context Subsystem](#4-geolocation--spatial-context-subsystem)
5. [BIM Digital Twin Engine](#5-bim-digital-twin-engine)
6. [2D Building Plan Processing Subsystem](#6-2d-building-plan-processing-subsystem)
7. [2D-to-3D Plan Extrusion Engine](#7-2d-to-3d-plan-extrusion-engine)
8. [IFC BIM Ingestion & Schema Adaptation Subsystem](#8-ifc-bim-ingestion--schema-adaptation-subsystem)
9. [Computer Vision Engine](#9-computer-vision-engine)
10. [Building Geometry & Structural Audit Subsystem](#10-building-geometry--structural-audit-subsystem)
11. [Climate & Environmental Analysis Subsystem](#11-climate--environmental-analysis-subsystem)
12. [Rainwater Harvesting Analysis Subsystem](#12-rainwater-harvesting-analysis-subsystem)
13. [Subsurface & Geotechnical Analysis Subsystem](#13-subsurface--geotechnical-analysis-subsystem)
14. [Flood Risk & Stormwater Hydrology Subsystem](#14-flood-risk--stormwater-hydrology-subsystem)
15. [AI/ML Prediction & Validation Engine](#15-aiml-prediction--validation-engine)
16. [Recommendation & Multi-Domain Optimization Engine](#16-recommendation--multi-domain-optimization-engine)
17. [Database & Fixture Storage Subsystem](#17-database--fixture-storage-subsystem)
18. [Backend REST API Gateway Subsystem](#18-backend-rest-api-gateway-subsystem)
19. [Visualization & Performance Reporting Subsystem](#19-visualization--performance-reporting-subsystem)

---

### 1. Frontend / User Interface
- **Purpose & Role:** Delivers a responsive, hardware-accelerated 3D WebGL and 2D GIS client experience for architectural, structural, and environmental analysis.
- **Implementation Status:** **IMPLEMENTED**
- **Primary Files:**
  - `frontend/src/App.tsx` (1,051 lines)
  - `frontend/src/components/BuildingViewer.tsx` (2,675 lines)
  - `frontend/src/components/DesignComparison.tsx` (508 lines)
  - `frontend/src/components/CityViewer.tsx` (756 lines)
  - `frontend/src/components/EnvironmentalDashboardView.tsx` (1,101 lines)
- **Inputs:** User mouse/touch gestures, IFC/CAD/image file uploads, slider values for exploded floor stack and interventions.
- **Internal Logic & Algorithms:**
  - Three.js WebGL scene graph, perspective camera frustum calculations, raycasting for element inspection, directional shadows, and CSS3D/canvas 2D overlays.
  - OrbitControls event synchronization between dual side-by-side viewports.
- **Outputs:** Interactive 60fps 3D rendering, analytical charts, interactive Leaflet map, CSV/PDF summary downloads.
- **Connected APIs:** Communicates with all 12 backend REST routers via `frontend/src/lib/api.ts`.
- **Dependencies:** React 18, Three.js 0.160, Leaflet 1.9, Lucide React, Tailwind CSS.
- **Limitations & Roadmap:** Add WebGPU renderer backend and VR/AR immersive walkthrough support.

---

### 2. Authentication & User Management
- **Purpose & Role:** User authentication, identity management, multi-tenancy, and role-based access control (RBAC).
- **Implementation Status:** **NOT IMPLEMENTED**
- **Primary Files:** None (No JWT middleware or user tables currently exist).
- **Inputs:** N/A.
- **Internal Logic & Algorithms:** Open access; the frontend and backend operate as an open, single-tenant analytical workstation.
- **Outputs:** N/A.
- **Connected APIs:** None.
- **Dependencies:** None.
- **Limitations & Roadmap:** Essential for multi-tenant enterprise deployment. Planned integration: OAuth2 with PKCE, JWT access/refresh token validation, and RBAC roles (`viewer`, `sustainability_engineer`, `bim_manager`, `system_admin`).

---

### 3. Building Data Input Subsystem
- **Purpose & Role:** Ingests heterogeneous building information across parametric user inputs, industry-standard IFC files, and raster 2D floor plans.
- **Implementation Status:** **IMPLEMENTED**
- **Primary Files:**
  - `frontend/src/components/IfcUploadModal.tsx` (184 lines)
  - `frontend/src/components/FloorplanUploadModal.tsx` (347 lines)
  - `frontend/src/components/BuildingForm.tsx` (251 lines)
  - `backend/app/api/model_routes.py` (221 lines)
  - `backend/app/api/floorplan_routes.py` (138 lines)
- **Inputs:** Multipart form data (`.ifc`, `.png`, `.jpg`, `.pdf`) and JSON payloads describing dimensions and occupancy.
- **Internal Logic & Algorithms:**
  - MIME type verification, file size boundary checks (up to 100MB), temporary disk buffering, and stream forwarding to parsing services.
- **Outputs:** Ingested model identifiers (`model_id`), parsed metadata summaries, and spatial hierarchy descriptors.
- **Connected APIs:** `POST /api/models/upload`, `POST /api/floorplans/process`.
- **Dependencies:** Python `multipart`, FastAPI `UploadFile`.

---

### 4. Geolocation & Spatial Context Subsystem
- **Purpose & Role:** Determines the exact physical location of the building project, extracts georeferencing from IFC headers, and connects the model to real-world spatial coordinates.
- **Implementation Status:** **IMPLEMENTED**
- **Primary Files:**
  - `frontend/src/components/EnvironmentalDashboardView.tsx` (1,101 lines)
  - `backend/app/services/location_climate_service.py` (243 lines)
  - `backend/app/services/geospatial_integration_service.py` (1,558 lines)
  - `backend/app/services/ifc_parser.py` (713 lines)
- **Inputs:** WGS84 coordinates ($Latitude, Longitude$), site address strings, or native `IfcSite` georeferencing.
- **Internal Logic & Algorithms:**
  - Browser Geolocation API (`navigator.geolocation.getCurrentPosition`).
  - Nominatim OpenStreetMap forward/reverse geocoding.
  - Native `IfcSite` coordinate parser: decodes `RefLatitude` and `RefLongitude` expressed as compound tuples (degrees, minutes, seconds, millionths of a second) into decimal degrees.
  - Formal geodetic mapping via `IfcMapConversion` and `IfcProjectedCRS`.
- **Outputs:** Geodetic coordinates, elevation above mean sea level ($AMSL$), climate zone classification, and address string.
- **Connected APIs:** `GET /api/environmental/weather`, `POST /api/geospatial/query`.
- **Dependencies:** Leaflet, Open-Meteo REST API, Nominatim.

---

### 5. BIM Digital Twin Engine
- **Purpose & Role:** Constructs, manages, and renders the 3D digital twin of the building envelope, internal structural framing, and spatial storeys.
- **Implementation Status:** **IMPLEMENTED**
- **Primary Files:**
  - `frontend/src/components/BuildingViewer.tsx` (2,675 lines)
  - `backend/app/services/ifc_parser.py` (713 lines)
  - `backend/app/models/digital_twin.py` (220 lines)
- **Inputs:** `BuildingModelDetail` JSON containing element arrays, vertex buffers, face indices, and transform matrices.
- **Internal Logic & Algorithms:**
  - Supports 6 distinct visualization modes:
    1. **Skeleton View:** Transparent envelope showing structural columns, beams, and slabs.
    2. **Exterior View:** Opaque façade materials with PBR metallic-roughness shading.
    3. **Furnished Interior View:** Dollhouse architectural section with visible interior walls, doors, and placed furniture.
    4. **Exploded Floor Stack:** Procedural vertical offset ($Z$ translation) separating storeys for isolated spatial review.
    5. **Subsurface Borehole Mode:** Subterranean strata cylinders visualizing soil layers and water table.
    6. **3D Interventions Overlay:** Solar PV arrays, RWH storage tanks, and green roof layers attached to building geometry.
  - Object selection and property inspection via GPU raycasting.
- **Outputs:** Interactive WebGL canvas, element property tables, and camera perspective state.
- **Connected APIs:** `GET /api/models/{model_id}`.
- **Dependencies:** Three.js, WebGL2.

---

### 6. 2D Building Plan Processing Subsystem
- **Purpose & Role:** Ingests architectural raster floor plans, removes graphical noise, and detects structural elements.
- **Implementation Status:** **IMPLEMENTED**
- **Primary Files:**
  - `backend/app/services/floorplan_processor.py` (1,425 lines)
  - `frontend/src/components/FloorplanCorrectionEditor.tsx` (798 lines)
  - `backend/app/api/floorplan_routes.py` (138 lines)
- **Inputs:** High-resolution architectural raster images (PNG, JPEG, scanned PDF).
- **Internal Logic & Algorithms:**
  - Contrast Limited Adaptive Histogram Equalization (CLAHE).
  - Adaptive Gaussian thresholding to binarize wall lines against background noise.
  - Morphological opening and closing kernels to remove dimension lines, hatching, and text annotations.
  - Probabilistic Hough Line Transform (`cv2.HoughLinesP`) to identify structural wall vectors.
  - Colinear line segment clustering and orthogonal angle snapping ($0^\circ, 90^\circ, 180^\circ, 270^\circ$).
- **Outputs:** Wall polylines, room boundary polygons, and door/window opening intervals.
- **Connected APIs:** `POST /api/floorplans/process`.
- **Dependencies:** OpenCV (`cv2`), NumPy, Shapely.

---

### 7. 2D-to-3D Plan Extrusion Engine
- **Purpose & Role:** Converts 2D planar vector data into fully manifold 3D architectural geometry.
- **Implementation Status:** **IMPLEMENTED**
- **Primary Files:**
  - `backend/app/services/floorplan_to_3d_service.py` (950 lines)
  - `backend/app/services/interior_furnishing_service.py` (999 lines)
  - `frontend/src/lib/furniture3d.ts` (416 lines)
- **Inputs:** `FloorplanProcessingResult` (metric wall polylines, room polygons, scale calibration factor).
- **Internal Logic & Algorithms:**
  - Scale transformation: converts pixel coordinates to metric coordinates ($m$) based on calibrated scale.
  - Wall extrusion: computes 2D polygon offset buffers for wall thickness ($0.2\text{ m}$) and extrudes vertically to storey height ($2.8\text{ m}$).
  - Boolean substraction: punches openings for doors ($2.1\text{ m}$ height) and windows ($1.2\text{ m}$ sill height, $1.4\text{ m}$ opening height).
  - Room classification: evaluates room aspect ratio, area ($m^2$), and connectivity to assign typologies (`office`, `conference_room`, `restroom`, `corridor`).
  - Clearance-aware furniture placement: places 3D furniture models adhering to $0.9\text{ m}$ egress clear corridors.
- **Outputs:** Standard `BuildingModelDetail` containing 3D vertex buffers, floor slabs, wall meshes, and placed furniture elements.
- **Connected APIs:** `POST /api/floorplans/extrude-3d`, `POST /api/furniture/generate`.
- **Dependencies:** Shapely, NumPy, Three.js procedural builders.

---

### 8. IFC BIM Ingestion & Schema Adaptation Subsystem
- **Purpose & Role:** Parses Industry Foundation Classes (IFC) files, extracts semantic attributes, and adapts pre-release schemas.
- **Implementation Status:** **IMPLEMENTED**
- **Primary Files:**
  - `backend/app/services/ifc_parser.py` (713 lines)
  - `backend/app/api/model_routes.py` (221 lines)
- **Inputs:** IFC files adhering to `IFC2X3`, `IFC4`, `IFC4X3`, or `IFC4X3_RC2`.
- **Internal Logic & Algorithms:**
  - **Schema Adaptation Engine:** Automatically inspects the SPFF header (`FILE_SCHEMA`). If a non-final schema such as `IFC4X3_RC2` is detected, dynamically transforms the header token to `IFC4X3_ADD2` to prevent IfcOpenShell schema lookup failures while maintaining original schema metadata.
  - **Georeferencing Decoder:** Traverses `IfcSite` to extract `RefLatitude`, `RefLongitude`, and `RefElevation`. Reads `IfcMapConversion` and `IfcProjectedCRS` to obtain true EPSG geodetic projection parameters.
  - **Geometric Triangulation:** Calls `ifcopenshell.geom.create_shape` with world coordinate resolution (`USE_WORLD_COORDS=True`) to convert B-Rep, CSG, and extruded profile solids into triangulated index buffers.
  - **Semantic Spatial Hierarchy:** Builds tree linking `IfcProject` $\rightarrow$ `IfcSite` $\rightarrow$ `IfcBuilding` $\rightarrow$ `IfcBuildingStorey` $\rightarrow$ `IfcProduct`.
- **Outputs:** `BuildingModelDetail` domain model containing spatial hierarchy and element arrays.
- **Connected APIs:** `POST /api/models/upload`, `GET /api/models/{id}`.
- **Dependencies:** IfcOpenShell 0.9.0.post1, Python regex.

---

### 9. Computer Vision Engine
- **Purpose & Role:** Standalone image processing pipeline handling architectural raster analysis, boundary discovery, and spatial morphology.
- **Implementation Status:** **IMPLEMENTED**
- **Primary Files:**
  - `backend/app/services/floorplan_processor.py` (1,425 lines)
- **Inputs:** Raw bitmap images (grayscale or RGB matrices).
- **Internal Logic & Algorithms:**
  - Bilateral filtering to preserve structural edge gradients while suppressing texture noise.
  - Canny edge detection followed by dilation/erosion morphological sequences.
  - Flood-fill hole discovery for closed boundary detection.
  - Polygon simplification using the Ramer-Douglas-Peucker (RDP) algorithm with $\epsilon = 2.0\text{ pixels}$.
- **Outputs:** Simplified 2D polygons and directional orientation vectors.
- **Connected APIs:** `POST /api/floorplans/process`.
- **Dependencies:** OpenCV (`cv2`), NumPy, SciPy.

---

### 10. Building Geometry & Structural Audit Subsystem
- **Purpose & Role:** Audits BIM geometric validity, missing property sets, thermal envelope ratios, and material provenance.
- **Implementation Status:** **IMPLEMENTED** *(Disclaimer: Bar Bending Schedule detailing is NOT implemented in 3D geometry)*
- **Primary Files:**
  - `backend/app/services/quality_engine.py` (247 lines)
  - `backend/app/services/intelligence_engine.py` (555 lines)
  - `backend/app/services/building_feature_service.py` (363 lines)
  - `frontend/src/components/QualityReportView.tsx` (482 lines)
- **Inputs:** `BuildingModelDetail` data structures.
- **Internal Logic & Algorithms:**
  - Surface-to-volume ratio ($S/V$) and window-to-wall ratio ($WWR$) per façade orientation.
  - Model completeness scoring evaluating presence of storey associations, material assignments, and fire ratings.
  - Material Provenance Ledger tracking whether materials are parsed from authentic IFC property sets or inferred via architectural defaults.
  - Model accuracy scoring and prediction confidence intervals.
- **Outputs:** Quality audit reports, risk flags (`HIGH`, `MEDIUM`, `LOW`), and material provenance breakdown.
- **Connected APIs:** `GET /api/models/{id}/quality`, `GET /api/models/{id}/intelligence`.
- **Dependencies:** NumPy, Shapely.

---

### 11. Climate & Environmental Analysis Subsystem
- **Purpose & Role:** Harvests microclimate data, computes solar irradiation, and models urban heat island (UHI) vulnerability.
- **Implementation Status:** **IMPLEMENTED**
- **Primary Files:**
  - `backend/app/services/geospatial_integration_service.py` (1,558 lines)
  - `backend/app/services/location_climate_service.py` (243 lines)
  - `backend/app/services/environmental_service.py` (710 lines)
  - `frontend/src/components/EnvironmentalDashboardView.tsx` (1,101 lines)
- **Inputs:** Geodetic coordinates ($WGS84$), elevation, and building orientation.
- **Internal Logic & Algorithms:**
  - Open-Meteo REST integration fetching hourly historical and projected meteorological time-series.
  - Solar geometry formulas (solar zenith, azimuth angle, extraterrestrial radiation) computing direct normal irradiance ($DNI$) and diffuse horizontal irradiance ($DHI$).
  - Wind rose calculation binning wind velocities into 16 cardinal compass directions.
  - Bioclimatic comfort indexing (temperature-humidity index and passive cooling feasibility).
- **Outputs:** Hourly weather profiles, monthly climate summaries, solar potential maps, and passive design strategies.
- **Connected APIs:** `POST /api/environmental/analyze`, `GET /api/environmental/weather`.
- **Dependencies:** Open-Meteo API, SciPy, NumPy.

---

### 12. Rainwater Harvesting Analysis Subsystem
- **Purpose & Role:** Evaluates roof catchment potential, computes daily tank mass balance, and sizes rainwater retention systems.
- **Implementation Status:** **IMPLEMENTED**
- **Primary Files:**
  - `backend/app/services/hydrological_engine.py` (701 lines)
  - `backend/app/services/rainwater_ml_service.py` (199 lines)
  - `backend/app/services/rainwater_recommendation_service.py` (187 lines)
  - `frontend/src/components/RainwaterRecommendationView.tsx` (664 lines)
- **Inputs:** Roof catchment area ($m^2$), roof surface material, local rainfall time-series, and building occupancy count.
- **Internal Logic & Algorithms:**
  - Annual harvestable yield equation:
    $$Y = A \cdot P \cdot C_r \cdot \eta_{\text{filter}}$$
    where $A$ is roof area, $P$ is annual precipitation, $C_r$ is roof runoff coefficient (0.90 for metal/concrete, 0.70 for tiles, 0.50 for green roofs), and $\eta_{\text{filter}}$ is first-flush efficiency ($0.90$).
  - Daily mass balance continuous simulation over 365 days tracking tank storage level, daily non-potable flushing/irrigation demand, and overflow volume.
  - Tank sizing optimization balancing volumetric reliability ($85\%-95\%$) against capital excavation costs.
- **Outputs:** Harvestable volume ($m^3/\text{year}$), optimal tank capacity ($m^3$), potable water offset percentage, and 365-day storage time-series.
- **Connected APIs:** `POST /api/rainwater/analyze`, `POST /api/rainwater/recommendations`.
- **Dependencies:** NumPy, Pandas, Scikit-Learn.

---

### 13. Subsurface & Geotechnical Analysis Subsystem
- **Purpose & Role:** Evaluates subterranean soil strata, Standard Penetration Test ($SPT$) N-values, groundwater table depth, and bearing capacity.
- **Implementation Status:** **IMPLEMENTED**
- **Primary Files:**
  - `backend/app/services/geotechnical_service.py` (242 lines)
  - `frontend/src/components/GeotechnicalIntelligenceView.tsx` (282 lines)
  - `backend/app/api/geotechnical_routes.py` (28 lines)
- **Inputs:** Geodetic coordinates and site soil classifications.
- **Internal Logic & Algorithms:**
  - Soil strata layering interpolation (topsoil, silty sand, medium clay, weathered rock).
  - Depth-dependent $SPT$ N-value profiling and safe bearing capacity calculation:
    $$q_a = \frac{N_{60}}{0.08} \cdot \left(1 + \frac{B}{0.3}\right)^2 \cdot C_w$$
  - Groundwater table elevation mapping and basement waterproofing risk determination.
- **Outputs:** Geotechnical profile, borehole log visualization, bearing capacity ($kN/m^2$), and foundation recommendations.
- **Connected APIs:** `GET /api/geotechnical/site`, `POST /api/geotechnical/boreholes`.
- **Dependencies:** NumPy, Three.js subterranean borehole visualizer.

---

### 14. Flood Risk & Stormwater Hydrology Subsystem
- **Purpose & Role:** Computes peak surface runoff, models stormwater attenuation hydrographs, and evaluates urban flood vulnerability.
- **Implementation Status:** **IMPLEMENTED**
- **Primary Files:**
  - `backend/app/services/hydrological_engine.py` (701 lines)
  - `backend/app/services/environmental_protection_service.py` (263 lines)
  - `backend/app/api/rainwater_routes.py` (153 lines)
- **Inputs:** Site area, composite runoff coefficient, time of concentration ($t_c$), and design storm intensity ($I$).
- **Internal Logic & Algorithms:**
  - Rational Method peak runoff rate ($Q_p$ in $m^3/s$).
  - Triangular unit hydrograph convolution modeling peak flow attenuation via detention storage and permeable infiltration surfaces.
  - Flood risk classification categorized into `LOW`, `MODERATE`, `HIGH`, or `CRITICAL` risk zones.
- **Outputs:** Peak runoff discharge ($m^3/s$), runoff volume hydrographs, required detention volume ($m^3$), and flood mitigation recommendations.
- **Connected APIs:** `POST /api/rainwater/analyze`.
- **Dependencies:** NumPy, SciPy.

---

### 15. AI/ML Prediction & Validation Engine
- **Purpose & Role:** Executes machine learning inference for rainwater yield estimation and risk classification, reporting cross-validated metrics.
- **Implementation Status:** **IMPLEMENTED**
- **Primary Files:**
  - `backend/app/services/rainwater_ml_service.py` (199 lines)
  - `backend/app/services/ml_prediction_service.py` (167 lines)
  - `backend/app/ml_models/rainwater_models.joblib` (Trained model artifact)
  - `backend/app/data/rainwater_dataset.csv` (Synthetic training dataset)
  - `backend/app/api/ml_routes.py` (39 lines)
- **Inputs:** Catchment area, rainfall, runoff coefficient, tank capacity, and non-potable demand.
- **Internal Logic & Algorithms:**
  - `GradientBoostingRegressor`: 150 estimators, learning rate 0.05, max depth 4. Predicts annual yield with $R^2 = 0.964$, $MAE = 11.8\text{ m}^3$.
  - `RandomForestClassifier`: 100 trees. Predicts flood risk category with $94.2\%$ accuracy.
  - Model provenance and accuracy metrics exposed directly via API for jury transparency.
- **Outputs:** Predicted yield, predicted risk category, model confidence interval, and validation metrics.
- **Connected APIs:** `POST /api/ml/predict-energy`, `POST /api/rainwater/analyze`.
- **Dependencies:** Scikit-Learn 1.4+, Joblib.

---

### 16. Recommendation & Multi-Domain Optimization Engine
- **Purpose & Role:** Evaluates multi-domain interventions, applies Multi-Criteria Decision Analysis (MCDA), and synthesizes comparison bundles.
- **Implementation Status:** **IMPLEMENTED**
- **Primary Files:**
  - `backend/app/services/recommendation_engine.py` (177 lines)
  - `backend/app/services/rainwater_recommendation_service.py` (187 lines)
  - `backend/app/services/cost_engine.py` (123 lines)
  - `backend/app/services/esg_engine.py` (509 lines)
  - `frontend/src/components/DesignComparison.tsx` (508 lines)
- **Inputs:** Building geometry, location profile, microclimate data, and budgetary constraints.
- **Internal Logic & Algorithms:**
  - MCDA weighted scoring matrix evaluating 7 physical alternatives across 5 criteria: capital expenditure (CAPEX), operational savings (OPEX), environmental impact, spatial footprint, and maintenance complexity.
  - Assembles 3 distinct engineering bundles:
    1. **Balanced Optimization Bundle**
    2. **Maximum Sustainability Bundle**
    3. **Cost-Optimized Bundle**
  - Generates exact 3D intervention components (`Intervention3DComponent`) positioned on the building model (solar panels on roofs, water tanks on foundations).
- **Outputs:** Prioritized recommendation list, financial ROI, carbon offset metrics, and 3D intervention components.
- **Connected APIs:** `POST /api/rainwater/recommendations`, `POST /api/routes/building/optimize`.
- **Dependencies:** NumPy, Pydantic.

---

### 17. Database & Fixture Storage Subsystem
- **Purpose & Role:** Manages persistence, in-memory caching of parsed digital twins, and pre-packaged architectural benchmarks.
- **Implementation Status:** **PARTIALLY IMPLEMENTED (STATELESS IN-MEMORY CACHE)**
- **Primary Files:**
  - `backend/app/services/model_store.py` (201 lines)
  - `backend/app/fixtures/sample_office_building.ifc`
  - `backend/app/fixtures/sample_office_building_enriched.ifc`
- **Inputs:** Parsed `BuildingModelDetail` instances and model UUIDs.
- **Internal Logic & Algorithms:**
  - Thread-safe in-memory Python dictionary keyed by UUID strings.
  - Startup lifespan hook loads and pre-parses seed IFC models from `backend/app/fixtures/` so the application is instantly testable.
- **Outputs:** Stored building models and element indexes.
- **Connected APIs:** `GET /api/models`, `GET /api/models/{id}`.
- **Dependencies:** Standard library (`threading.Lock`, `uuid`).
- **Limitations & Roadmap:** Data resets upon process restart. Production roadmap: Replace with PostgreSQL + PostGIS database using SQLAlchemy 2.0 ORM.

---

### 18. Backend REST API Gateway Subsystem
- **Purpose & Role:** Central routing gateway hosting 12 specialized sub-routers, enforcing CORS policy, and managing request lifecycle.
- **Implementation Status:** **IMPLEMENTED**
- **Primary Files:**
  - `backend/app/main.py` (74 lines)
  - `backend/app/core/config.py` (19 lines)
  - 12 router files in `backend/app/api/` (1,157 lines total)
- **Inputs:** HTTP GET, POST, OPTIONS requests with JSON bodies or multipart file streams.
- **Internal Logic & Algorithms:**
  - FastAPI dependency injection, Pydantic request/response validation, automatic OpenAPI / Swagger documentation generation at `/docs`.
- **Outputs:** Structured JSON responses with standard HTTP status codes (200, 400, 404, 422, 500).
- **Connected APIs:** All application routes.
- **Dependencies:** FastAPI, Uvicorn, Starlette.

---

### 19. Visualization & Performance Reporting Subsystem
- **Purpose & Role:** Compiles building intelligence, material provenance, quality audits, and ESG compliance into interactive visual dashboards.
- **Implementation Status:** **IMPLEMENTED**
- **Primary Files:**
  - `frontend/src/components/QualityReportView.tsx` (482 lines)
  - `frontend/src/components/IntelligenceDashboardView.tsx` (529 lines)
  - `frontend/src/components/EsgDashboardView.tsx` (218 lines)
  - `frontend/src/components/ScenarioIntelligenceView.tsx` (345 lines)
  - `frontend/src/components/MLEnergyOptimizerView.tsx` (274 lines)
- **Inputs:** Quality scores, risk assessments, ESG criteria, and scenario simulation outputs.
- **Internal Logic & Algorithms:**
  - Material Provenance Ledger visualization distinguishing IFC-extracted properties from inferred defaults.
  - EU Taxonomy green classification radar diagrams.
  - Parametric scenario delta cards showing energy and cost payback trajectories.
- **Outputs:** Visual performance dashboards, SVG charts, and interactive audit cards.
- **Connected APIs:** `GET /api/models/{id}/quality`, `GET /api/models/{id}/intelligence`, `POST /api/sustainability/screen`.
- **Dependencies:** React, Lucide React, Tailwind CSS.
