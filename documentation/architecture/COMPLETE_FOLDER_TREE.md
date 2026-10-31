# InfraTwin AI: Complete Hierarchical Folder & Source File Tree
**Version:** 2.4.0 (Hackathon Technical Jury Edition)  
**Total Source Code Volume:** 31,343 lines across Python & TypeScript  
**Total Test Volume:** 2,310 lines across 14 pytest suites (94 passing tests)  
**Generated On:** October 31, 2026

---

## 1. Top-Level Repository Structure

```
building-optimizer/
├── backend/                        # FastAPI Backend Application (Python 3.14/3.11+)
│   ├── app/                        # Application Source Code
│   │   ├── api/                    # 12 Modular REST API Routers
│   │   ├── core/                   # Global Settings & Configuration
│   │   ├── data/                   # ML Datasets (CSV)
│   │   ├── fixtures/               # Seed IFC Models
│   │   ├── ml_models/              # Serialized Scikit-Learn Joblib Artifacts
│   │   ├── models/                 # 13 Pydantic V2 Domain Data Schemas
│   │   ├── services/               # 19 Domain Engineering & Analytics Services
│   │   └── main.py                 # FastAPI Application Factory & Lifespan Handler
│   ├── tests/                      # 14 Pytest Test Suites (94 Tests Total)
│   └── requirements.txt            # Python Dependencies Specification
├── frontend/                       # React 18 + Vite Single Page Application
│   ├── src/                        # TypeScript & React Application Source
│   │   ├── components/             # 21 Modular UI & 3D Visualization Components
│   │   ├── lib/                    # Shared Utilities, API Client & 3D Geometry Helpers
│   │   ├── types/                  # 11 TypeScript Type Definition Interfaces
│   │   ├── App.tsx                 # Main Navigation, State Management & Layout Host
│   │   ├── main.tsx                # React DOM Mount Entrypoint
│   │   └── vite-env.d.ts           # Vite Environment Type Augmentation
│   ├── index.html                  # HTML5 SPA Entry Template
│   ├── package.json                # Frontend NPM Package Manifest & Scripts
│   ├── tailwind.config.js          # Tailwind CSS Theme & Styling Config
│   ├── tsconfig.json               # TypeScript Compiler Settings
│   └── vite.config.ts              # Vite Bundler & Development Server Config
├── docs/                           # High-Level Architecture & Concept Guides
│   ├── architecture.md             # System Overview & Component Responsibilities
│   ├── building-intelligence.md    # Multi-Domain Interventions Specification
│   ├── data-flow.md                # Data Ingestion & Transformation Flows
│   ├── esg-framework.md            # ESG & Green Certification Taxonomy
│   ├── model-ingestion.md          # IFC Parsing Specification
│   └── security-and-limitations.md # Current Security Model & Constraints
├── documentation/                  # Deep Hackathon Jury Architecture Documentation Suite
│   └── architecture/               # (Current Output Directory)
├── README.md                       # Master Project Readme & Quickstart Instructions
├── run.sh                          # Unified Startup Shell Script (Backend + Frontend)
└── .gitignore                      # Git Version Control Exclusions
```

---

## 2. Backend Detailed File Hierarchy (`backend/app/`)

### 2.1 Core & Entrypoint
| Relative Path | Lines | Key Classes / Functions | Primary Responsibility | Collaborators |
| :--- | :--- | :--- | :--- | :--- |
| `backend/app/main.py` | 74 | `create_app()`, `lifespan()`, `root()`, `health()` | Application factory, lifespan initialization, CORS middleware registration, and router mounting. | All API Routers, `ModelStore` |
| `backend/app/core/config.py` | 19 | `Settings` (Pydantic BaseSettings) | Global runtime environment configurations (API prefix, project title, CORS origins). | `main.py` |

### 2.2 API Routers (`backend/app/api/`)
| Relative Path | Lines | Key Endpoints / Handlers | Primary Responsibility | Backed Service |
| :--- | :--- | :--- | :--- | :--- |
| `backend/app/api/city_routes.py` | 126 | `GET /city/sample`, `GET /city/district`, `POST /city/import` | Endpoints for LOD1 urban districts, spatial queries, and multi-format GIS CAD uploads. | `city_service.py`, `city_import_service.py` |
| `backend/app/api/environmental_routes.py` | 67 | `POST /environmental/analyze`, `GET /environmental/weather` | Climate indicator retrieval, microclimate analysis, and bioclimatic recommendations. | `environmental_service.py`, `location_climate_service.py` |
| `backend/app/api/floorplan_routes.py` | 138 | `POST /floorplans/process`, `POST /floorplans/extrude-3d` | 2D raster floor plan ingestion, OpenCV boundary extraction, and extrusion to 3D geometry. | `floorplan_processor.py`, `floorplan_to_3d_service.py` |
| `backend/app/api/furniture_routes.py` | 138 | `POST /furniture/generate`, `GET /furniture/catalog` | Automated architectural room classification and 3D furniture placement. | `interior_furnishing_service.py` |
| `backend/app/api/geospatial_routes.py` | 83 | `GET /geospatial/datasets`, `POST /geospatial/query` | Unified gateway to 10 satellite, soil, elevation, and climate datasets for given WGS84 coordinates. | `geospatial_integration_service.py` |
| `backend/app/api/geotechnical_routes.py` | 28 | `GET /geotechnical/site`, `POST /geotechnical/boreholes` | Subsurface soil strata analysis, borehole log generation, and foundation bearing capacity. | `geotechnical_service.py` |
| `backend/app/api/ml_routes.py` | 39 | `POST /ml/predict-energy`, `GET /ml/model-info` | Energy consumption forecasting and structural performance estimation. | `ml_prediction_service.py` |
| `backend/app/api/model_routes.py` | 221 | `POST /models/upload`, `GET /models/{id}`, `GET /models` | Native IFC file ingestion, geometry parsing, element metadata retrieval, and model registry. | `ifc_parser.py`, `model_store.py` |
| `backend/app/api/rainwater_routes.py` | 153 | `POST /rainwater/analyze`, `POST /rainwater/recommendations` | Hydrological mass balance simulation, ML yield prediction, and 7-alternative RWH ranking. | `hydrological_engine.py`, `rainwater_recommendation_service.py` |
| `backend/app/api/routes.py` | 112 | `POST /building/optimize`, `GET /building/sample` | Legacy core building optimization and parametric design generation endpoints. | `recommendation_engine.py`, `model_store.py` |
| `backend/app/api/scenario_routes.py` | 31 | `POST /scenarios/evaluate`, `GET /scenarios/catalog` | Parametric scenario comparison and what-if design simulations. | `scenario_service.py` |
| `backend/app/api/sustainability_routes.py` | 34 | `POST /sustainability/screen`, `GET /sustainability/metrics` | ESG screening, carbon footprint estimation, and green rating certification checks. | `sustainability_service.py`, `esg_engine.py` |

### 2.3 Domain Services (`backend/app/services/`)
| Relative Path | Lines | Key Classes / Functions | Primary Responsibility |
| :--- | :--- | :--- | :--- |
| `backend/app/services/building_feature_service.py` | 363 | `BuildingFeatureService`, `extract_envelope_metrics()` | Calculates building surface-to-volume ratio, fenestration ratios, and thermal envelope metrics. |
| `backend/app/services/city_import_service.py` | 875 | `CityImportService`, `import_file()`, `parse_geojson()`, `parse_cityjson()`, `parse_shapefile()`, `parse_geopackage()`, `parse_dxf()` | Ingests 5 geospatial formats, extracts building footprints, height attributes, and converts to LOD1 city district models. |
| `backend/app/services/city_service.py` | 613 | `CityService`, `get_sample_city()`, `get_district_summary()`, `filter_by_typology()` | Manages urban district data structures, infrastructure network layers, and spatial indexing. |
| `backend/app/services/cost_engine.py` | 123 | `CostEngine`, `estimate_intervention_costs()`, `calculate_roi()` | Capital cost estimation using Schedule of Rates / CPWD benchmarks and financial payback modeling. |
| `backend/app/services/dataset_registry.py` | 254 | `DatasetRegistry`, `get_dataset_metadata()`, `list_available_sources()` | Catalog and provenance metadata for integrated geospatial, weather, and environmental datasets. |
| `backend/app/services/environmental_protection_service.py` | 263 | `EnvironmentalProtectionService`, `assess_ecological_impact()` | Evaluates urban biodiversity, green corridor preservation, and tree protection requirements. |
| `backend/app/services/environmental_service.py` | 710 | `EnvironmentalService`, `analyze_location()`, `calculate_microclimate()` | Synthesizes weather observations, solar radiation profiles, and wind roses for given site coordinates. |
| `backend/app/services/esg_engine.py` | 509 | `ESGEngine`, `screen_esg_compliance()`, `evaluate_eu_taxonomy()` | Assesses compliance against EU Taxonomy, LEED, BREEAM, and GRI sustainability disclosure standards. |
| `backend/app/services/floorplan_processor.py` | 1425 | `FloorplanProcessor`, `process_image()`, `detect_walls()`, `find_rooms()` | Computer vision pipeline using OpenCV for image normalization, Hough line wall detection, and room polygonization. |
| `backend/app/services/floorplan_to_3d_service.py` | 950 | `FloorplanTo3DService`, `extrude_floorplan()`, `generate_3d_walls()` | Converts 2D metric wall contours and room polygons into 3D manifold meshes with window/door cutouts. |
| `backend/app/services/geospatial_integration_service.py` | 1558 | `GeospatialIntegrationService`, `fetch_location_profile()`, `fetch_worldcover()`, `fetch_soilgrids()` | Connects to 10 real-world APIs and raster data sources (ESA WorldCover, Open-Meteo, NASA POWER, SoilGrids). |
| `backend/app/services/geotechnical_service.py` | 242 | `GeotechnicalService`, `analyze_subsurface()`, `generate_borehole_log()` | Subsurface soil strata modeling, SPT N-value interpolation, groundwater table depth, and safe bearing capacity. |
| `backend/app/services/hydrological_engine.py` | 701 | `HydrologicalEngine`, `simulate_daily_balance()`, `calculate_peak_runoff()` | Rational Method peak runoff calculation and 365-day tank mass balance simulation. |
| `backend/app/services/ifc_parser.py` | 713 | `IfcParserService`, `parse_ifc()`, `extract_georeferencing()`, `_fix_schema_header()` | IfcOpenShell BIM parser with `IFC4X3_RC2` $\rightarrow$ `IFC4X3_ADD2` adaptation, georeferencing extraction, and mesh triangulation. |
| `backend/app/services/impact_estimator.py` | 200 | `ImpactEstimator`, `calculate_net_benefits()` | Quantifies carbon reduction, potable water savings, and energy grid load reduction. |
| `backend/app/services/intelligence_engine.py` | 555 | `IntelligenceEngine`, `audit_model()`, `detect_risks()` | Evaluates building structural and thermal risks, geometry completeness, and missing property sets. |
| `backend/app/services/interior_furnishing_service.py` | 999 | `InteriorFurnishingService`, `furnish_building()`, `classify_room_typology()` | Architectural heuristic rule engine for room classification and 3D furniture synthesis with clearance constraints. |
| `backend/app/services/location_climate_service.py` | 243 | `LocationClimateService`, `get_weather_data()`, `get_climate_summary()` | Open-Meteo API wrapper fetching temperature, solar irradiance, and rainfall data for geocoded sites. |
| `backend/app/services/ml_prediction_service.py` | 167 | `MLPredictionService`, `predict_building_energy()` | Predicts building Energy Use Intensity (EUI in $\text{kWh/m}^2/\text{year}$) using building form factor. |
| `backend/app/services/model_store.py` | 201 | `ModelStore`, `save_model()`, `get_model()`, `list_models()`, `get_default_model()` | In-memory singleton registry storing parsed building models and loading pre-packaged IFC fixtures. |
| `backend/app/services/quality_engine.py` | 247 | `QualityEngine`, `evaluate_model_quality()`, `audit_materials()` | Inspects model geometric integrity, material provenance ledger, and prediction confidence metrics. |
| `backend/app/services/rainwater_dataset_generator.py` | 190 | `generate_synthetic_rainwater_data()` | Generates synthetic training datasets combining climate variations and roof catchment areas. |
| `backend/app/services/rainwater_ml_service.py` | 199 | `RainwaterMLService`, `predict_yield()`, `train_models()` | Scikit-Learn model inference and training pipeline for harvestable rainwater yield and runoff mitigation. |
| `backend/app/services/rainwater_recommendation_service.py` | 187 | `RainwaterRecommendationService`, `rank_alternatives()` | Multi-criteria decision analysis (MCDA) ranking 7 physical RWH alternatives based on site constraints. |
| `backend/app/services/recommendation_engine.py` | 177 | `RecommendationEngine`, `generate_recommendations()` | Synthesizes multi-domain sustainability recommendations and assembles the 3 optimal comparison bundles. |
| `backend/app/services/scenario_service.py` | 354 | `ScenarioService`, `simulate_scenario()` | Evaluates parametric building retrofit scenarios (glazing replacement, insulation, solar PV). |
| `backend/app/services/sustainability_service.py` | 442 | `SustainabilityService`, `screen_sustainability()` | Multi-criteria green building screening evaluating water, energy, materials, and indoor quality. |

### 2.4 Pydantic Data Models (`backend/app/models/`)
| Relative Path | Lines | Key Schemas Defined | Primary Responsibility |
| :--- | :--- | :--- | :--- |
| `backend/app/models/building.py` | 91 | `BuildingCreate`, `BuildingResponse`, `BuildingOptimizationResult` | Legacy building form input and optimization parameter schemas. |
| `backend/app/models/city.py` | 69 | `CityModel`, `DistrictSummary`, `CityImportRequest` | Schemas for urban districts, LOD1 city models, and GIS import responses. |
| `backend/app/models/digital_twin.py` | 220 | `BuildingModelDetail`, `BuildingElement`, `SpatialHierarchyNode`, `Intervention3DComponent` | Comprehensive data model representing the complete digital twin, mesh arrays, and 3D interventions. |
| `backend/app/models/environmental.py` | 97 | `EnvironmentalAnalysisRequest`, `MicroclimateReport`, `WeatherData` | Schemas for site microclimate metrics, wind rose, and solar radiance profiles. |
| `backend/app/models/floorplan.py` | 148 | `FloorplanProcessingResult`, `RoomPolygon`, `WallSegment`, `Opening` | Computer vision schemas describing detected rooms, wall segments, and doors/windows. |
| `backend/app/models/furniture.py` | 94 | `FurnitureItem`, `RoomFurnishingPlan`, `FurnitureCatalogItem` | 3D furniture item placement specifications (coordinates, rotation, typology, dimensions). |
| `backend/app/models/geospatial_profile.py` | 107 | `GeospatialProfileResponse`, `LandCoverMetrics`, `SolarAtlasData` | Structured schema for the 10 integrated geospatial and environmental datasets. |
| `backend/app/models/geotechnical.py` | 65 | `GeotechnicalProfile`, `SoilStrataLayer`, `BoreholeLog` | Subsurface soil stratification, borehole SPT N-values, and geotechnical bearing capacities. |
| `backend/app/models/ml_energy.py` | 78 | `MLEnergyPredictionRequest`, `MLEnergyPredictionResponse` | Schemas for machine learning energy forecasting and EUI breakdown. |
| `backend/app/models/rainwater.py` | 162 | `RainwaterHarvestingAnalysis`, `RainwaterAlternative`, `TankMassBalance` | Detailed schemas for 7 physical RWH alternatives, daily mass balance, and storage tank sizing. |
| `backend/app/models/recommendations.py` | 80 | `RecommendationItem`, `OptimizationBundle`, `DesignComparisonModel` | Multi-domain recommendation schemas and baseline vs proposed comparison bundles. |
| `backend/app/models/scenarios.py` | 40 | `ScenarioRequest`, `ScenarioResponse`, `ScenarioEvaluation` | Schemas for what-if scenario configurations and comparative payback metrics. |
| `backend/app/models/sustainability.py` | 44 | `SustainabilityReport`, `CarbonMetrics`, `GreenRatingScore` | Schemas for ESG screening, carbon footprint estimates, and green certification scores. |

### 2.5 Pytest Test Suites (`backend/tests/`)
| Relative Path | Lines | Tests Count | Focus Area |
| :--- | :--- | :--- | :--- |
| `backend/tests/test_building.py` | 75 | 5 | Core building optimization endpoints and validation. |
| `backend/tests/test_city_import.py` | 105 | 4 | GIS CAD multi-format ingestion (GeoJSON, CityJSON, Shapefile, GPKG, DXF). |
| `backend/tests/test_core_intelligence.py` | 304 | 12 | Building envelope metrics, feature extraction, and quality audit engines. |
| `backend/tests/test_environmental.py` | 128 | 6 | Microclimate analysis and Open-Meteo weather integration. |
| `backend/tests/test_esg.py` | 68 | 3 | EU Taxonomy screening and ESG score calculation. |
| `backend/tests/test_floorplan_processing.py` | 233 | 8 | OpenCV image filtering, wall detection, and 3D extrusion. |
| `backend/tests/test_geospatial_integration.py` | 196 | 7 | 10 geospatial datasets integration and spatial profile synthesis. |
| `backend/tests/test_health.py` | 12 | 1 | Basic FastAPI health check endpoint. |
| `backend/tests/test_ifc_ingestion.py` | 168 | 6 | IfcOpenShell parsing, `IFC4X3_RC2` schema adaptation, and georeferencing extraction. |
| `backend/tests/test_intelligence.py` | 245 | 9 | Structural and thermal risk detection and missing property audits. |
| `backend/tests/test_interior_furnishing.py` | 311 | 11 | Architectural room classification, clearance verification, and 3D furniture placement. |
| `backend/tests/test_nextgen_platform.py` | 118 | 5 | Integrated platform workflow from location to digital twin. |
| `backend/tests/test_rainwater_engine.py` | 200 | 9 | Hydrological engine mass balance, Scikit-learn inference, and MCDA ranking. |
| `backend/tests/test_recommendations.py` | 147 | 8 | Multi-domain sustainability recommendation and comparison bundle generation. |

---

## 3. Frontend Detailed File Hierarchy (`frontend/src/`)

### 3.1 App Root & Entrypoint
| Relative Path | Lines | Key Components / Logic | Primary Responsibility |
| :--- | :--- | :--- | :--- |
| `frontend/src/App.tsx` | 1051 | `App` Component | Root navigation state machine, workspace management, 3-pillar mode switching, and modal coordinator. |
| `frontend/src/main.tsx` | 11 | `ReactDOM.createRoot` | Mounts the React application tree into the HTML DOM. |
| `frontend/src/vite-env.d.ts` | 9 | Vite type declarations | Declares client-side environment variable typings. |

### 3.2 Visual & Functional UI Components (`frontend/src/components/`)
| Relative Path | Lines | Primary UI Responsibility | Key Three.js / Leaflet / React Hooks |
| :--- | :--- | :--- | :--- |
| `BuildingViewer.tsx` | 2675 | Interactive 3D WebGL viewer supporting 6 rendering modes: Skeleton, Exterior, Furnished Interior (Dollhouse), Exploded Storey Stack, Subsurface Geotechnical Boreholes, and Physical 3D Interventions. | `useRef`, `useEffect`, `useState`, Three.js `Scene`, `PerspectiveCamera`, `WebGLRenderer`, `OrbitControls`, `Raycaster` |
| `DesignComparison.tsx` | 508 | Synchronized dual-camera side-by-side or overlay comparison between Baseline authentic IFC geometry and Proposed design with active interventions. | Synchronized `OrbitControls` event listeners, Three.js dual viewport management |
| `CityViewer.tsx` | 756 | LOD1 urban district viewer with typology coloring, cadastral parcel visualization, and multi-format GIS CAD import modal. | Three.js scene, camera controls, parcel raycasting, GIS file dropzone |
| `EnvironmentalDashboardView.tsx` | 1101 | Leaflet interactive map, geodetic site search, solar irradiance rose, wind speed charts, and bioclimatic comfort indicators. | Leaflet map instance, `L.tileLayer`, `L.marker`, Lucide icons, weather state |
| `RainwaterRecommendationView.tsx` | 664 | 7-alternative RWH ranking dashboard, 365-day tank mass balance simulation charts, and Scikit-Learn ML validation metrics breakdown. | React state, tabular ranking, bar graphs, ML confidence indicators |
| `FloorplanUploadModal.tsx` | 347 | Upload modal for raster 2D floor plans (PNG, JPG, PDF) with scale calibration input ($m/\text{pixel}$). | File input drag-and-drop, scale factor slider, preview canvas |
| `FloorplanCorrectionEditor.tsx` | 798 | Interactive 2D canvas editor allowing manual correction of OpenCV-detected wall segments, room boundaries, and openings. | HTML5 Canvas 2D context, mouse event dragging, vertex snapping |
| `QualityReportView.tsx` | 482 | BIM model geometric completeness audit, Material Provenance Ledger, and Model Accuracy & Prediction Confidence breakdown. | Tabular audit view, progress bars, material taxonomy cards |
| `GeotechnicalIntelligenceView.tsx` | 282 | Subsurface geotechnical dashboard displaying soil strata cross-sections, borehole SPT N-values, and bearing capacities. | SVG soil strata diagrams, borehole depth sliders |
| `ScenarioIntelligenceView.tsx` | 345 | Interactive what-if scenario configurator (glazing type, insulation thickness, solar PV area) with real-time ROI estimates. | Form inputs, comparative delta cards, payback charts |
| `MLEnergyOptimizerView.tsx` | 274 | Machine learning energy optimization dashboard displaying EUI predictions, heating/cooling breakdowns, and decarbonization paths. | Metric cards, energy distribution charts |
| `IntelligenceDashboardView.tsx` | 529 | Comprehensive building intelligence summary displaying structural and thermal risks, compliance scores, and spatial metrics. | Risk severity badges, radar charts, compliance indicators |
| `EsgDashboardView.tsx` | 218 | ESG screening dashboard benchmarking against EU Taxonomy, LEED, and BREEAM sustainability pillars. | Category score rings, ESG disclosure checklist |
| `IfcUploadModal.tsx` | 184 | Modal for uploading authentic IFC files with progress indicator and sample model one-click loader. | File upload handler, sample model selector |
| `HomePage.tsx` | 373 | Platform welcome page and project wizard guiding users into BIM Twin, Geolocation, or City Twin workflows. | Card navigation, feature showcases |
| `RecommendationList.tsx` | 222 | Tabular list of prioritized sustainability recommendations with cost, savings, and payback period. | Accordion view, filter toggles |
| `InterventionToggle.tsx` | 143 | Floating control panel enabling users to toggle individual 3D interventions on/off in the active 3D viewer. | Checkbox toggles, category badges |
| `ElementInspector.tsx` | 396 | Sidebar inspector displaying properties, dimensions, and material properties of clicked 3D building elements. | Property tree, geometric bounding box inspector |
| `ImpactModal.tsx` | 181 | Detailed modal presenting environmental lifecycle benefits (carbon avoided, water saved, energy generated). | Impact metric cards, visual equivalence gauges |
| `BudgetSummary.tsx` | 105 | Financial summary showing total CAPEX, annual operational savings, and net present value (NPV). | Cost calculation cards, currency formatters |
| `ApiStatus.tsx` | 58 | Non-intrusive indicator showing backend API connectivity status and response latency. | Heartbeat ping hook, connectivity badge |

### 3.3 Core Libraries & Helpers (`frontend/src/lib/`)
| Relative Path | Lines | Key Exports | Primary Responsibility |
| :--- | :--- | :--- | :--- |
| `frontend/src/lib/api.ts` | 695 | `apiClient`, `fetchWithTimeout()`, 35+ typed API methods | Unified HTTP communication layer communicating with FastAPI backend endpoints. |
| `frontend/src/lib/furniture3d.ts` | 416 | `createFurniture3D()`, `getFurnitureColor()` | Three.js procedural geometry builder generating lightweight 3D furniture meshes (desks, chairs, tables). |
| `frontend/src/lib/validation.ts` | 70 | `validateCoordinates()`, `validateFileSize()` | Client-side input validation for coordinates, file formats, and physical building dimensions. |

### 3.4 TypeScript Interfaces (`frontend/src/types/`)
| Relative Path | Lines | Primary TypeScript Interfaces Defined |
| :--- | :--- | :--- |
| `frontend/src/types/building.ts` | 43 | `BuildingParams`, `OptimizationResult`, `BuildingElementProps` |
| `frontend/src/types/city.ts` | 67 | `CityDistrict`, `BuildingParcel`, `InfrastructureLayer`, `CityImportPayload` |
| `frontend/src/types/digital_twin.ts` | 191 | `BuildingModel`, `BuildingElement`, `SpatialHierarchyNode`, `Intervention3DComponent` |
| `frontend/src/types/environmental.ts` | 99 | `LocationCoordinates`, `WeatherMetrics`, `MicroclimateData`, `SolarPotential` |
| `frontend/src/types/floorplan.ts` | 137 | `FloorplanResult`, `DetectedRoom`, `WallPolyline`, `FloorplanOpening` |
| `frontend/src/types/furniture.ts` | 89 | `PlacedFurniture`, `RoomLayout`, `FurnitureAssetDefinition` |
| `frontend/src/types/geotechnical.ts` | 56 | `SoilLayer`, `BoreholeData`, `GeotechnicalSiteAssessment` |
| `frontend/src/types/ml_energy.ts` | 54 | `EnergyPredictionInput`, `EnergyPredictionOutput`, `CarbonBreakdown` |
| `frontend/src/types/rainwater.ts` | 159 | `RainwaterAnalysisResult`, `RWHAlternative`, `WaterBalanceSimulation` |
| `frontend/src/types/recommendations.ts` | 73 | `InterventionRecommendation`, `OptimizationBundleData`, `ComparisonState` |
| `frontend/src/types/scenarios.ts` | 33 | `RetrofitScenario`, `ScenarioEvaluationResult` |
| `frontend/src/types/sustainability.ts` | 35 | `EsgScreeningResult`, `CertificationBenchmark` |
