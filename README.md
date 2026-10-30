# InfraTwinAI: Building Digital Twin, CAD/BIM Ingestion & ESG Foundation

A locally runnable, production-grade architectural and engineering platform demonstrating **InfraTwinAI**: an AI-assisted, budget-aware building digital twin and sustainable infrastructure planning assistant for architects, civil engineers, building performance consultants, and small builders.

The platform provides a dual-mode workflow:
1. **BIM Digital Twin Mode**: Ingests industry-standard Industry Foundation Classes (IFC4 / IFC2x3) files, normalizes units, extracts spatial hierarchies and property sets, reconstructs triangulated 3D surface meshes using `IfcOpenShell`, audits data quality and model completeness, conducts evidence-based ESG assessments (ICE v3, CEA 2023, NBC 2016, ECBC 2017), and provides an interactive 3D raycast element inspector.
2. **Parametric Design Mode**: Allows users to parameterize building dimensions, visualize real-time procedural 3D massing using Three.js, toggle energy-saving interventions, and receive deterministic, explainable recommendations bounded strictly by a financial budget in Indian Rupees (INR).

---

## 1. Key Architectural Features

- **Building Intelligence & Risk Analysis (Phase 4)**: Automated audit engine evaluating 6 core rules: missing properties/statutory fire ratings, missing materials, unconnected apertures/framing, duplicate GUID conflicts, missing storey containment, and geometric clashing ($\ge 85\%$ volumetric collision) or dimensional anomalies.
- **Bi-Directional 3D Finding Visualization**: Interactive link between the Intelligence Dashboard and Three.js viewer: clicking a finding immediately isolates and highlights the affected element in 3D (Rose for High, Amber for Warning), while clicking any 3D element opens its Inspector displaying associated findings, topological relationships (`hosted_in`, `hosts`, `connected_to`), and classifications.
- **Model-Derived Intelligence Dashboard**: Clean metrics derived strictly from the imported IFC file: total elements, category distribution, material distribution (with real volumes and %), model completeness %, severity breakdown, and storey-wise distribution.
- **Open-Standard BIM Ingestion**: Industrial-grade parser powered by `IfcOpenShell 0.9.0` supporting IFC4 and IFC2x3 STEP physical files (ISO 10303-21). Extracts 8 element categories: Columns, Beams, Walls, Slabs, Footings/Foundations, Doors & Windows, Roofs, and Storeys & Spaces.
- **Evidence-Based ESG Assessment**: Rejects opaque composite scores. Evaluates discrete, verifiable criteria across Environmental (Embodied carbon via ICE v3, Scope 2 operational carbon via CEA 2023, Window-to-Wall ratio via ECBC 2017, Rooftop solar PV potential), Social (Universal door accessibility per NBC 2016 / ADA, natural ventilation IAQ potential via `SOC-04`, daylighting aperture ratio, fire egress stairs), and Governance (ISO 19650 BIM lineage, standard Pset coverage, statutory approval readiness).
- **Interactive Operational Recalculation**: Input real-time utility electricity consumption ($\text{kWh/year}$) in the ESG dashboard to immediately recalculate operational carbon ($\text{tCO}_2\text{e/year}$) without re-uploading files.
- **Parametric Building Optimizer (Phase 1 Preserved)**: Instant procedural 3D building synthesis, CPWD DSR 2023 cost benchmarks, multi-factor transparent recommendation scoring, greedy budget packing, and side-by-side design comparison.
- **Zero API Keys & Offline Operation**: Runs 100% locally with zero cloud dependencies, zero external AI service subscriptions, and zero paid API keys.

---

## 2. Monorepo Project Structure

```text
building-optimizer/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ApiStatus.tsx             # Real-time backend connectivity heartbeat & retry
│   │   │   ├── BuildingForm.tsx          # Parametric geometry & budget inputs with validation
│   │   │   ├── BuildingViewer.tsx        # Unified Three.js WebGL scene (BIM meshes & parametric massing)
│   │   │   ├── BudgetSummary.tsx         # Financial allocation progress meter & deficit alerts
│   │   │   ├── DesignComparison.tsx      # Proposed, Baseline, and Dual Side-by-Side viewports
│   │   │   ├── ElementInspector.tsx      # Click-to-inspect flyout drawer for BIM element metadata & Psets
│   │   │   ├── EsgDashboardView.tsx      # Multi-pillar ESG screening dashboard with kWh recalculation
│   │   │   ├── IfcUploadModal.tsx        # Drag & drop IFC uploader (<50MB, STEP checks) & sample twin loader
│   │   │   ├── ImpactModal.tsx           # Scientific disclosures & honest carbon calculation
│   │   │   ├── IntelligenceDashboardView.tsx # Building Intelligence & Risk Analysis Dashboard (Phase 4)
│   │   │   ├── InterventionToggle.tsx    # 3D visual toggles with unit rates & budget badges
│   │   │   ├── QualityReportView.tsx     # Model completeness audit dashboard with severity breakdown
│   │   │   └── RecommendationList.tsx    # Ranked recommendations with explainability & bundle actions
│   │   ├── lib/
│   │   │   ├── api.ts                    # Strict TypeScript fetch client with typed digital twin API
│   │   │   └── validation.ts             # Client-side spatial validation & Indian Rupee (INR) formatting
│   │   ├── types/
│   │   │   ├── building.ts               # Parametric building schema & spatial geometry interfaces
│   │   │   ├── digital_twin.ts           # Canonical BIM model, element geometry, quality, & ESG interfaces
│   │   │   └── recommendations.ts        # Intervention & cost recommendation data models
│   │   ├── App.tsx                       # Root dashboard orchestrator (Mode & Subtab navigation)
│   │   ├── main.tsx                      # React DOM mount point
│   │   └── index.css                     # Tailwind CSS base styles
│   ├── package.json                      # Frontend scripts & dependencies
│   ├── tsconfig.json                     # Strict TypeScript compiler options
│   └── vite.config.ts                    # Vite build configuration (Port 5173)
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── model_routes.py           # Digital twin endpoints (/models, /import/ifc, /quality, /esg)
│   │   │   └── routes.py                 # Parametric design endpoints (/health, /validate, /recommendations)
│   │   ├── core/
│   │   │   └── config.py                 # Configuration & restricted CORS settings
│   │   ├── fixtures/
│   │   │   └── sample_office_building.ifc # Valid IFC4 multi-storey office fixture (17 elements, Psets)
│   │   ├── models/
│   │   │   ├── building.py               # Pydantic v2 parametric building schemas
│   │   │   ├── digital_twin.py           # Canonical digital twin, mesh, quality, & ESG schemas
│   │   │   └── recommendations.py        # Cost and recommendation schemas
│   │   ├── services/
│   │   │   ├── cost_engine.py            # CPWD DSR / MNRE unit rate calculations
│   │   │   ├── esg_engine.py             # Evidence-based ESG evaluation engine (ICE v3, CEA, NBC)
│   │   │   ├── ifc_parser.py             # IfcOpenShell 0.9.0 parsing & 3D mesh tessellation engine
│   │   │   ├── impact_estimator.py       # CEA grid factor baseline & solar yield estimations
│   │   │   ├── intelligence_engine.py    # 6-rule building intelligence & risk detection engine (Phase 4)
│   │   │   ├── model_store.py            # In-memory thread-safe digital twin repository
│   │   │   └── recommendation_engine.py  # Transparent multi-factor scoring & greedy budget packing
│   │   └── main.py                       # FastAPI application & sanitized error handlers
│   ├── tests/
│   │   ├── test_building.py              # Dimension validation & geometric plausibility tests
│   │   ├── test_esg.py                   # ESG screening criteria & quality audit tests
│   │   ├── test_health.py                # Service readiness tests
│   │   ├── test_ifc_ingestion.py         # IFC upload validation, STEP headers, parsing, & pagination
│   │   ├── test_intelligence.py          # Intelligence rules, collisions, & metric tests (Phase 4)
│   │   └── test_recommendations.py       # Budget filtering, ranking, & honest estimation tests
│   └── requirements.txt                  # Python dependencies (FastAPI, IfcOpenShell, ezdxf, Pydantic v2)
├── docs/
│   ├── architecture.md                   # System architecture, component duties & trade-offs
│   ├── building-intelligence.md          # 6-rule issue detection, risk classifications & metrics (Phase 4)
│   ├── data-flow.md                      # Data flow diagrams & sequence specifications (BIM & Parametric)
│   ├── esg-framework.md                  # Comprehensive ESG assessment methodology & standards
│   ├── model-ingestion.md                # IFC parsing pipeline, entity extraction & security controls
│   └── security-and-limitations.md       # Implemented controls, scientific limits & production roadmap
└── README.md
```

---

## 3. Prerequisites

- **Node.js**: `v18.0.0` or higher (verified with `v24.15.0`)
- **npm**: `v9.0.0` or higher (verified with `v11.12.1`)
- **Python**: `3.11` or higher (verified with `Python 3.14.7`)

---

## 4. Local Setup and Execution

### Step A: Start the FastAPI Backend (Port 8000)

#### On macOS / Linux:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### On Windows PowerShell:
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

*The backend will be available at `http://127.0.0.1:8000` with interactive Swagger OpenAPI documentation at `http://127.0.0.1:8000/docs`.*

---

### Step B: Start the Vite Frontend (Port 5173)

Open a second terminal window:

#### On macOS / Linux / Windows:
```bash
cd frontend
npm install
npm run dev
```

*The frontend application will start at `http://localhost:5173/`.*

---

## 5. Automated Tests

### Run Backend Tests (Pytest)
```bash
cd backend
source .venv/bin/activate
pytest -v
```

**Verification Results (21 of 21 tests passing):**
- `test_health.py`: Verifies `/health` returns status `ok`, application name (`InfraTwinAI`), and version.
- `test_building.py`: Verifies positive dimensions, rejects zero/negative dimensions, rejects invalid floor counts, and asserts window count vs wall surface limits.
- `test_recommendations.py`: Asserts ₹0 budget returns zero feasible recommendations, asserts individual over-budget items are rejected, verifies greedy package packing, and verifies unestimated passive cooling transparency.
- `test_ifc_ingestion.py`:
  - Enforces STEP header validation (rejects non-STEP files with HTTP 400).
  - Enforces 50MB file size limits (HTTP 413).
  - Tests valid IFC file upload and parsing into canonical model hierarchy.
  - Tests model detail retrieval and bounding box calculation.
  - Tests element pagination, category filtering, and storey filtering.
- `test_esg.py`:
  - Verifies model completeness score and quality finding generation.
  - Verifies ESG report generation (10 criteria across ENV, SOC, GOV).
  - Verifies dynamic operational Scope 2 carbon calculation with supplied vs missing kWh.

### Run Frontend Typecheck & Production Build
```bash
cd frontend
npm run build
```
*Compiles TypeScript with strict type checking (`tsc`) and verifies Rollup production asset bundling (`vite build`).*

---

## 6. API Reference

### Digital Twin & BIM Ingestion Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/models` | List all imported digital twin models with summary metrics. |
| `POST` | `/api/v1/models/import/ifc` | Upload and parse an IFC file (multipart/form-data, max 50MB). |
| `GET` | `/api/v1/models/{id}` | Retrieve canonical model details, storeys, and bounding envelope. |
| `GET` | `/api/v1/models/{id}/elements` | Paginated element retrieval with triangulated 3D mesh vertices and faces. |
| `GET` | `/api/v1/models/{id}/quality` | Retrieve data completeness audit report and severity findings. |
| `GET` | `/api/v1/models/{id}/esg` | Retrieve evidence-based ESG assessment report (optional `?annual_kwh=...`). |

### Parametric Optimization Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health probe returning status and version. |
| `POST` | `/api/v1/building/validate` | Authoritative server-side validation; returns normalized metrics (Roof area, GFA, WWR). |
| `POST` | `/api/v1/recommendations` | Ranks eligible interventions and packs an optimal bundle within user budget. |
| `POST` | `/api/v1/estimate` | Returns itemized cost breakdown and honest carbon estimates (requires measured kWh). |

---

## 7. Frontend Verification Checklist

- [x] **Mode Navigation**: Seamlessly switch between **BIM Digital Twin** and **Parametric Design** modes.
- [x] **Sample Digital Twin Pre-Loaded**: 1-click loading of `sample-office-twin` (IFC4, 17 elements, 2 storeys, Psets).
- [x] **BIM 3D Viewport & Raycasting**: Orbit, rotate, and zoom around imported IFC meshes. Clicking any element opens the **Element Inspector** drawer displaying GlobalId (with copy button), dimensions, materials, and attached property sets.
- [x] **Storey & Category Filtering**: Filter visible elements by storey (e.g. `Ground Floor`, `First Floor`) or by architectural category (`IfcWall`, `IfcDoor`, `IfcWindow`, `IfcSlab`, `IfcColumn`).
- [x] **Model Completeness Audit**: Dedicated **Quality Audit** subtab displaying data completeness ratio, severity badge breakdowns (Critical, Warning, Info), entity counts, and actionable remediation cards.
- [x] **Evidence-Based ESG Screening**: Dedicated **ESG Screening** subtab with Environmental, Social, and Governance pillars. Includes live utility electricity input ($\text{kWh/year}$) to immediately re-evaluate operational carbon.
- [x] **Preserved Parametric Optimizer**: 100% of Phase 1 functionality preserved: procedural 3D massing, intervention toggles (louvers, cool roof, insulation, solar PV), budget allocation progress bar, and side-by-side design comparison.
- [x] **Scientific Integrity Disclosures**: Official citations for ICE v3, CEA 2023 grid factors ($0.716\text{ kg CO}_2\text{e/kWh}$), NBC 2016 accessibility, and ECBC 2017 thermal envelope standards.

---

## 8. Troubleshooting

- **FastAPI shows CORS error**: Verify that `backend/app/core/config.py` contains `http://localhost:5173` and `http://127.0.0.1:5173` in `ALLOWED_ORIGINS`.
- **Uploaded IFC fails validation**: Ensure the file begins with standard STEP physical encoding `ISO-10303-21;` and does not exceed the 50MB file size limit.
- **Port 8000 or 5173 already occupied**:
  - For backend: run `uvicorn app.main:app --port 8001` and update `frontend/.env` with `VITE_API_BASE_URL=http://localhost:8001`.
  - For frontend: run `npm run dev -- --port 5174`.
- **Three.js canvas appears black or blank**: Verify WebGL is enabled in your browser settings (Chrome: `chrome://settings/system` -> "Use graphics acceleration when available").