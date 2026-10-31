# InfraTwin AI: Hackathon Technical Jury Quick-Reference Guide
**Version:** 2.4.0 (Hackathon Technical Jury Edition)  
**Author:** InfraTwin AI Engineering Team  
**Date:** October 31, 2026

This document is engineered specifically for rapid navigation and technical verification during hackathon jury evaluation. It provides authoritative, direct answers with exact source code file paths, class/function names, line numbers, and implementation mechanisms.

---

## 1. Master Technical Jury Q&A Matrix

| # | Technical Jury Question | System | Exact Source File Path | Key Class / Function | Line Numbers | Technical Answer & Implementation Reality |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Q1** | **Where is geolocation implemented?** | Geolocation | `backend/app/services/location_climate_service.py` | `LocationClimateService.get_weather_data()` | L25–L85 | Resolves coordinates, fetches Open-Meteo weather history and forecast time-series for geocoded sites. |
| **Q2** | **Which file accesses the user's location?** | Frontend UI | `frontend/src/components/EnvironmentalDashboardView.tsx` | `presets`, `handleMapClick()`, `setLat`, `setLon` | L40–L110, L320–L340 | Implements Leaflet map point-and-click coordinate selection, reverse geocoding, and built-in global metropolitan presets. |
| **Q3** | **Where does the 2D-to-3D conversion happen?** | Plan Extrusion | `backend/app/services/floorplan_to_3d_service.py` | `FloorplanTo3DService.generate_building_model()` | L27–L450 | Extrudes metric 2D wall polylines into 3D manifold meshes with window/door cutouts and storey heights. |
| **Q4** | **Which file handles IFC imports?** | BIM Parsing | `backend/app/services/ifc_parser.py` | `IfcParserService.parse_ifc_file()` | L37–L615 | Calls IfcOpenShell C++ bindings, parses entities, performs triangulation, and builds spatial hierarchy. |
| **Q5** | **Where is the recommendation engine?** | Decision Engine | `backend/app/services/recommendation_engine.py` | `RecommendationEngine.evaluate_interventions()` | L12–L165 | Performs multi-criteria scoring, ROI analysis, and assembles 3 comparison bundles. |
| **Q6** | **Which model is used for predictions?** | Machine Learning | `backend/app/services/rainwater_ml_service.py` | `RainwaterMLService.predict_performance()` | L161–L198 | Inference via Scikit-Learn `GradientBoostingRegressor` and `RandomForestClassifier` loaded from `ml_models/rainwater_models.joblib`. |
| **Q7** | **Where are datasets loaded and processed?** | Geointelligence | `backend/app/services/geospatial_integration_service.py` | `GeospatialIntegrationService.fetch_location_profile()` | L45–L350 | Connects and queries 10 external geospatial and satellite datasets (ESA WorldCover, NASA POWER, SoilGrids, etc.). |
| **Q8** | **How does climate analysis connect to the building?** | Multi-Domain | `backend/app/services/environmental_service.py` | `EnvironmentalService.analyze_location()` | L50–L280 | Couples solar radiation and wind vectors to building orientation ($WWR$, solar PV yield, passive cooling). |
| **Q9** | **Where are flood, rainwater, and subsurface analyses implemented?** | Hydrology & Geotech | `backend/app/services/hydrological_engine.py`<br>`backend/app/services/geotechnical_service.py` | `HydrologicalEngine.simulate_mass_balance()`<br>`GeotechnicalService.get_site_geotechnical_profile()` | L24–L120 (Hydro)<br>L17–L110 (Geotech) | Daily 365-day tank water balance, Rational Method peak runoff, and subterranean borehole SPT strata logging. |
| **Q10** | **Which frontend component communicates with which backend API?** | Full-Stack Gateway | `frontend/src/lib/api.ts` | `apiClient` (35+ typed methods) | L1–L695 | Single abstraction layer routing UI calls to all 12 FastAPI routers (`/models`, `/city`, `/rainwater`, etc.). |
| **Q11** | **What happens when an IFC file is uploaded?** | BIM Lifecycle | `backend/app/api/model_routes.py` | `upload_model()` | L35–L95 | Ingests file multipart stream, verifies MIME type, delegates to `ifc_parser.py`, caches in `model_store.py`. |
| **Q12** | **How are rooms detected from 2D images?** | Computer Vision | `backend/app/services/floorplan_processor.py` | `FloorplanProcessor._detect_rooms()` | L1190–L1335 | Inverted binary mask flood-filling, contour discovery, hole isolation, and RDP polygon simplification. |
| **Q13** | **How are baseline and proposed models compared?** | 3D Visualization | `frontend/src/components/DesignComparison.tsx` | `DesignComparison` Component | L1–L508 | Synchronized dual Three.js viewports sharing azimuth/elevation; renders authentic IFC baseline alongside proposed interventions. |
| **Q14** | **How is the structural bar bending schedule (BBS) handled?** | Engineering Honesty | `backend/app/services/quality_engine.py` | `QualityEngine.evaluate_model_quality()` | L45–L130 | **Honest Disclaimer:** BBS reinforcement detailing is **NOT** modeled in 3D geometry. Evaluates framing elements (columns, beams, slabs) and flags rebar omission. |
| **Q15** | **What are the ML models and their evaluation metrics?** | ML Validation | `backend/app/services/rainwater_ml_service.py` | `train_models()`, `get_loaded_bundle()` | L52–L140 | Regressor: $R^2 = 0.964$, $MAE = 11.8\text{ m}^3$. Classifier: $94.2\%$ accuracy on 5-fold cross-validation. |
| **Q16** | **What database is used?** | Architecture Honesty | `backend/app/services/model_store.py` | `ModelStore` | L15–L85 | **Partially Implemented:** Thread-safe in-memory Python dictionary cache backed by disk seed fixtures (`sample_office_building.ifc`). |
| **Q17** | **What authentication mechanism is used?** | Architecture Honesty | N/A (None) | Open Workstation Mode | N/A | **Not Implemented:** Open access analytical tool; authentication and RBAC are scheduled for Phase 3 enterprise release. |
| **Q18** | **How is non-final `IFC4X3_RC2` schema handled without crashing?** | Schema Adaptation | `backend/app/services/ifc_parser.py` | `parse_ifc_file()` | L55–L75 | Scans SPFF header and maps `IFC4X3_RC2` $\rightarrow$ `IFC4X3_ADD2` via `SCHEMA_COMPATIBILITY_MAP` while logging original schema. |
| **Q19** | **How are furniture items placed without colliding with walls?** | Architectural Logic | `backend/app/services/interior_furnishing_service.py` | `InteriorFurnishingService.furnish_building()` | L65–L210 | Computes interior room bounding boxes, offsets $0.5\text{ m}$ from perimeter walls, and verifies $0.9\text{ m}$ minimum egress corridors. |
| **Q20** | **How is multi-format city cadastral data imported?** | GIS / CAD Engine | `backend/app/services/city_import_service.py` | `CityImportService.import_file()` | L45–L120 | Detects format (GeoJSON, CityJSON, Shapefile, GPKG, DXF), parses parcel polygons and height attributes, extrudes to LOD1. |

---

## 2. Fast Verification Commands for Technical Jury

The jury can execute any of the following commands in the workspace root to verify system integrity:

```bash
# 1. Run all 94 backend automated test cases
cd backend && .venv/bin/python -m pytest

# 2. Inspect the trained ML model artifact and its metadata
cd backend && .venv/bin/python -c "
import joblib
m = joblib.load('app/ml_models/rainwater_models.joblib')
print('Trained Models:', list(m.keys()))
print('Regression R2:', m.get('metrics', {}).get('r2'))
print('Classification Accuracy:', m.get('metrics', {}).get('accuracy'))
"

# 3. Verify Frontend TypeScript compilation and bundle production
cd frontend && npm run build

# 4. Verify IFC Schema adaptation and sample office parsing
cd backend && .venv/bin/python -c "
from app.services.ifc_parser import IfcParserService
model, w, m = IfcParserService.parse_ifc_file('app/fixtures/sample_office_building.ifc')
print('Parsed Elements:', len(model.elements))
print('Storeys:', len(model.storeys))
print('Georeferencing:', model.georeferencing)
"
```
