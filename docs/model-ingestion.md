# BIM / CAD Ingestion Pipeline: InfraTwinAI

## 1. Overview

InfraTwinAI Phase 2 introduces native, open-standard **Building Information Modeling (BIM)** ingestion based on the **Industry Foundation Classes (IFC)** standard (ISO 10303-21 STEP physical format). The pipeline ingests physical files, validates schema and file integrity, extracts spatial hierarchies and property sets, reconstructs triangulated 3D surface meshes using `IfcOpenShell`, and maps entities to a canonical digital twin schema.

```mermaid
flowchart TD
    Upload[User Uploads .ifc File] --> SecurityCheck{Security & Header Validation}
    SecurityCheck -->|Fails (>50MB, Malformed STEP)| ErrorResp[Return HTTP 400/413/422 Sanitized Error]
    SecurityCheck -->|Valid STEP Header| TempFile[Safe Server-Side Temp Storage]
    
    TempFile --> Parser[IfcOpenShell 0.9.0 Engine]
    Parser --> Hierarchy[Extract Project, Site, Building & Storeys]
    Parser --> Units[Normalize Units to Metric Metres]
    Parser --> Elements[Extract Walls, Slabs, Columns, Doors, Windows, Roofs, Stairs]
    
    Elements --> GeomEngine{Tessellate Geometry?}
    GeomEngine -->|Supported Shape| Mesh[Extract Triangulated Vertices & Indices]
    GeomEngine -->|Missing / Corrupt| BBox[Bounding Box Fallback + Quality Warning]
    
    Mesh --> Canonical[Construct Canonical BuildingModelDetail]
    BBox --> Canonical
    Hierarchy --> Canonical
    
    Canonical --> Quality[Run Quality Completeness Audit]
    Canonical --> ESG[Run Preliminary ESG Assessment]
    Canonical --> SessionStore[(In-Memory Session ModelStore)]
    
    SessionStore --> Client[Deliver JSON Payload to Frontend Three.js Viewer]
    Client --> Raycast[Interactive 3D Raycasting & Element Inspector]
```

---

## 2. Supported IFC Entity Types

The parser natively extracts and renders the following building elements:

| IFC Entity | Canonical Classification | Visual Material Representation | Quantity Extractions |
| :--- | :--- | :--- | :--- |
| **`IfcWall` / `IfcWallStandardCase`** | Exterior & Interior Partition Walls | Architectural warm plaster (`#e2e5e9`) | Length, height, thickness, bounding volume |
| **`IfcSlab`** | Ground Slabs, Inter-Floor Decks, Terrace Slabs | Structural cast concrete (`#94a3b8`) | Area, perimeter, deck depth, volume |
| **`IfcColumn`** | Structural Vertical Loadbearing Columns | Structural column grey (`#64748b`) | Profile dimensions, height, volume |
| **`IfcBeam`** | Structural Horizontal Spanning Beams | Structural beam slate (`#475569`) | Span length, cross-section, volume |
| **`IfcWindow`** | Glazed Apertures & Curtain Windows | Transparent cyan glazing (`#38bdf8`, opacity 0.55) | Width, height, thermal transmittance (U-value) |
| **`IfcDoor`** | Circulation & Egress Openings | Warm architectural timber (`#b45309`) | Clear opening width, height, accessibility rating |
| **`IfcStair`** | Vertical Circulation & Fire Egress Flights | Terracotta stone (`#d97706`) | Number of risers/treads, vertical connection |
| **`IfcRoof`** | Roof Assemblies & Sloped Terraces | Dark terrace slate (`#334155`) | Projected footprint area, solar PV capacity |
| **`IfcFooting`** | Foundation & Plinth Substructures | Foundation dark slate (`#52525b`) | Substructure footprint |
| **`IfcBuildingElementProxy`** | Bespoke or Generic BIM Components | Accent teal (`#0d9488`) | Bounding envelope |

---

## 3. Geometry Extraction & Unit Normalization

1. **Length Unit Standardization**:
   - The parser inspects `IfcUnitAssignment`. If imperial (feet/inches) or non-standard metric (millimeters/centimeters) are encountered, coordinates are multiplied by an exact scale factor (e.g. `0.001` for millimeters, `0.3048` for feet).
   - All client-side Three.js geometry attributes use unified **metres (m)**.
2. **Triangulated Mesh Representation**:
   - Real 3D geometry is extracted via `ifcopenshell.geom.create_shape` with `USE_WORLD_COORDS=True`.
   - Extracted shapes are serialized as compact flat arrays (`vertices` [x,y,z] and triangle `faces` [v0,v1,v2]), directly consumable by Three.js `BufferGeometry`.
   - **Tessellation Decimation**: To protect client WebGL contexts from memory exhaustion, complex high-poly shapes are safely decimated if they exceed 4,500 faces per component.
3. **Bounding Box & Centering**:
   - A global bounding box is calculated. The center coordinates $(x_c, y_c, z_c)$ are preserved in `provenance_metadata` to allow the Three.js orbit camera to frame the model smoothly.

---

## 4. File Ingestion Security Controls

- **Size Cap**: Maximum allowed file size is strictly capped at **50 MB** (`HTTP 413 Entity Too Large`).
- **File Type & Extension Allowlist**: Only `.ifc`, `.ifcxml`, and `.ifczip` are accepted. Arbitrary executables or scripts are rejected (`HTTP 400 Bad Request`).
- **STEP Header Validation**: Standard physical IFC files are required to begin with `ISO-10303-21;`. Disguised text or binary files are rejected before passing to the parser.
- **Path Traversal Protection**: Filenames are sanitized with `os.path.basename`. Files are processed in safe system temporary directories via `tempfile.NamedTemporaryFile` and deleted immediately in `finally:` blocks.
- **Zero Local Path Leakage**: Internal host filesystem paths are never returned in client API responses.

---

## 5. DXF & 2D CAD Roadmap (Future Extension)

The project includes `ezdxf` in `backend/requirements.txt`. A planned future extension will provide 2D polyline extrusion:
- Ingestion of `.dxf` layers (`WALLS`, `DOORS`, `WINDOWS`).
- Closed polyline extrusion along a user-specified floor height into canonical `IfcWall` and `IfcDoor` entities.
