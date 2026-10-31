# InfraTwin AI: Comprehensive Technology Stack & Dependencies Audit
**Version:** 2.4.0 (Hackathon Technical Jury Edition)  
**Author:** InfraTwin AI Engineering Team  
**Date:** October 31, 2026

This document presents a complete audit of all programming languages, web frameworks, 3D/computational engines, machine learning libraries, system-level dependencies, and external geospatial APIs utilized across the InfraTwin AI platform.

---

## 1. Core Technology Matrix

| Subsystem | Core Technology | Installed Version | Primary Architectural Function |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | React | 18.3.1 | Component-based interactive Single Page Application (SPA). |
| **Frontend Language** | TypeScript | 5.6.3 | Static typing, interface contracts, and compile-time error checking. |
| **Frontend Build Tool** | Vite | 5.4.10 | High-performance ES-module development server and rollup packager. |
| **Frontend Styling** | Tailwind CSS | 3.4.14 | Utility-first responsive design, dark-theme layout, and CSS grid styling. |
| **3D WebGL Engine** | Three.js | 0.169.0 | WebGL scene graph, PBR shaders, OrbitControls, and custom mesh buffers. |
| **2D Cartography** | Leaflet | 1.9.4 | Interactive map viewer, satellite tile layers, and coordinate pickers. |
| **UI Iconography** | Lucide React | 1.16.0 | Modern SVG interface icons. |
| **Backend Framework** | FastAPI | 0.162.0 | High-performance asynchronous REST API gateway and OpenAPI generator. |
| **Backend Runtime** | Python (CPython) | 3.14.7 | Computational backend execution environment. |
| **ASGI Server** | Uvicorn (standard) | 0.54.0 | High-throughput asynchronous HTTP/WebSocket server. |
| **Data Validation** | Pydantic V2 | 2.14.2 | Strict schema validation, JSON serialization, and data coercion. |
| **BIM Parser** | IfcOpenShell | 0.9.0.post1 | C++ OpenCascade-based Industry Foundation Classes (IFC) parser. |
| **Computer Vision** | OpenCV Headless | 5.0.0.93 | Grayscale filtering, adaptive thresholding, and Hough line transforms. |
| **Computational Geometry** | Shapely | 2.2.0 | 2D/3D polygon operations, planar offsets, intersections, and buffering. |
| **CAD Parsing** | ezdxf | 1.4.5 | DXF CAD drawing parser for architectural footprints and district layouts. |
| **GIS Shapefile Engine** | pyshp (`shapefile`) | 3.1.6 | Ingestion of ESRI Shapefile vector geometry (.shp, .shx, .dbf). |
| **PDF Rendering** | pypdfium2 | 5.14.0 | Rasterization of multi-page architectural PDF drawings for CV processing. |
| **Scientific Computing** | NumPy / SciPy | 2.5.4 / 1.18.1 | High-speed multidimensional array arithmetic and hydrograph convolution. |
| **Machine Learning** | Scikit-Learn | 1.9.1 | GradientBoostingRegressor and RandomForestClassifier training and inference. |
| **Model Serialization** | Joblib | 1.6.0 | Serialized ML model pipeline loading (`rainwater_models.joblib`). |
| **Automated Testing** | Pytest | 9.2.0 | Test runner for 14 test suites and 94 automated unit/integration tests. |

---

## 2. Python Backend Virtual Environment Manifest

```
annotated-doc==0.0.5          # Documentation annotation utilities
anyio==4.15.1                 # Asynchronous event loop abstraction
click==8.5.0                  # Command-line interface utilities
cloudpickle==3.1.2            # Extended object serialization
ezdxf==1.4.5                  # AutoCAD DXF format reading and writing
fastapi==0.162.0              # Modern, fast web framework for APIs
fonttools==4.68.0             # Font manipulation library
h11==0.16.0                   # Pure-Python HTTP/1.1 protocol implementation
httpcore==1.0.9               # Minimal low-level HTTP client
httptools==0.9.0              # Fast HTTP parser written in C
httpx==0.28.1                 # Async HTTP client for external API requests
ifcopenshell==0.9.0.post1     # IFC file parsing and geometric triangulation
isodate==0.7.2                # ISO 8601 date/time parsing
joblib==1.6.0                 # Lightweight pipelining and model serialization
lark==1.3.1                   # Parsing toolkit for context-free grammars
narwhals==2.28.0              # Lightweight dataframe compatibility layer
numpy==2.5.4                  # N-dimensional array processing
opencv-python-headless==5.0.0.93  # Computer vision algorithms without GUI dependencies
pillow==13.0.0                # Python Imaging Library (PIL fork)
pydantic==2.14.2              # Data validation using Python type annotations
pydantic_core==2.50.2         # Core validation logic implemented in Rust
pypdfium2==5.14.0             # Fast PDF rasterization engine
pyshp==3.1.6                  # Pure Python ESRI Shapefile reader/writer
pytest==9.2.0                 # Robust Python testing framework
python-multipart==0.0.32      # Multipart form data streaming parser
PyYAML==6.0.3                 # YAML parser and emitter
scikit-learn==1.9.1           # Machine learning algorithms and preprocessing
scipy==1.18.1                 # Scientific algorithms and optimization routines
shapely==2.2.0                # Manipulation and analysis of geometric objects
starlette==1.10.0             # Lightweight ASGI framework / toolkit
uvicorn==0.54.0               # Lightning-fast ASGI server implementation
watchfiles==1.3.0             # File watcher for hot-reload in development
websockets==17.3              # WebSocket protocol implementation
```

---

## 3. Frontend Package Manifest (`package.json`)

```json
{
  "name": "building-optimizer-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "dependencies": {
    "@types/leaflet": "^1.9.22",
    "leaflet": "^1.9.4",
    "lucide-react": "^1.16.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "three": "^0.169.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@types/three": "^0.169.0",
    "@vitejs/plugin-react": "^4.3.3",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.14",
    "typescript": "^5.6.3",
    "vite": "^5.4.10"
  }
}
```

---

## 4. Machine Learning Model Artifacts & Datasets

### Serialized ML Model (`backend/app/ml_models/rainwater_models.joblib`)
- **File Size:** ~1,006,451 bytes (1.0 MB)
- **Serialized Architecture:**
  1. `scaler`: `StandardScaler` fitted on 5 physical input features (`catchment_area`, `annual_rainfall_mm`, `runoff_coefficient`, `tank_capacity_m3`, `water_demand_m3_day`).
  2. `regressor`: `GradientBoostingRegressor(n_estimators=150, learning_rate=0.05, max_depth=4, random_state=42)`
     - **Target:** Annual harvestable rainwater yield ($m^3/\text{year}$).
     - **Evaluation:** $R^2 = 0.964$, $MAE = 11.8\text{ m}^3$, $RMSE = 18.2\text{ m}^3$.
  3. `classifier`: `RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)`
     - **Target:** Stormwater flood risk category (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`).
     - **Evaluation:** Overall accuracy $94.2\%$, macro F1-score $0.938$.
  4. `feature_names`: `['catchment_area', 'annual_rainfall_mm', 'runoff_coefficient', 'tank_capacity_m3', 'water_demand_m3_day']`.
  5. `metadata`: Training timestamp, cross-validation metrics, and provenance hashes.

### Training Dataset (`backend/app/data/rainwater_dataset.csv`)
- **Generated Via:** `backend/app/services/rainwater_dataset_generator.py`.
- **Dimensions:** 1,200 rows $\times$ 9 attributes.
- **Coverage:** Synthetic and empirical data representing tropical, arid, temperate, and continental climate zones with roof catchments from $100\text{ m}^2$ to $15,000\text{ m}^2$.

---

## 5. Seed BIM Fixtures

The platform includes pre-parsed BIM fixtures in `backend/app/fixtures/`:
1. `sample_office_building.ifc` (~1.4 MB): A multi-storey commercial office building featuring structural framing, concrete floor slabs, exterior curtain walls, interior partitions, doors, windows, and formal georeferencing metadata.
2. `sample_office_building_placed.ifc` (~1.4 MB): Positioned spatial variant.
3. `sample_office_building_enriched.ifc` (~1.4 MB): Enriched variant including thermal property sets and material specifications.

---

## 6. External Geospatial & Environmental APIs

| Dataset / API | Provider | Query Method | Protocol | Authentication | Data Ingested |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Open-Meteo API** | Open-Meteo GmbH | REST API (`api.open-meteo.com`) | HTTP GET | Open (No Key) | Hourly temperature, rainfall, relative humidity, wind speed & direction. |
| **NASA POWER** | NASA Langley Research Center | REST API (`power.larc.nasa.gov`) | HTTP GET | Open (No Key) | Surface solar irradiance (GHI, DNI, DHI) and atmospheric clearance index. |
| **ESA WorldCover** | European Space Agency | WMS / STAC API | HTTP GET | Open / Copernicus | 10-meter global land-cover classification. |
| **Dynamic World** | Google / WRI | REST Endpoint | HTTP GET | Open | Near real-time vegetation, tree cover, and built-up land probabilities. |
| **Copernicus Sentinel-2** | European Space Agency | STAC Catalog | HTTP GET | Copernicus Data Hub | Multi-spectral NDVI vegetation index and NDWI water indices. |
| **Global Solar Atlas** | World Bank Group / Solargis | Spatial API | HTTP GET | Open Data | Photovoltaic electricity potential ($PVOUT$ in $\text{kWh/kWp}$). |
| **ISRIC SoilGrids** | ISRIC - World Soil Information | REST API (`rest.isric.org`) | HTTP GET | Open Access | Soil texture fractions (clay %, silt %, sand %), bulk density, and pH. |
| **HydroSHEDS** | WWF / USGS | Geotiff / Raster | File / Stream | Open Data | Elevation contours, drainage basins, and hydrological flow directions. |
| **Global Wind Atlas** | DTU Wind Energy / World Bank | Spatial API | HTTP GET | Open Access | Mean annual wind speeds at $10\text{ m}$ and $50\text{ m}$ heights. |
| **OpenStreetMap / Nominatim** | OpenStreetMap Foundation | REST API (`nominatim.openstreetmap.org`) | HTTP GET | User-Agent Header | Forward geocoding (address to coordinates) and reverse geocoding. |
