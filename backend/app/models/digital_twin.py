from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class BoundingBox3D(BaseModel):
    min_x: float
    min_y: float
    min_z: float
    max_x: float
    max_y: float
    max_z: float
    center_x: float
    center_y: float
    center_z: float
    width: float
    height: float
    depth: float

class ElementGeometry(BaseModel):
    format: str = Field(
        default="indexed_mesh",
        description="Geometry serialization format: 'indexed_mesh' (triangulated), 'bbox', or 'none'"
    )
    vertices: List[float] = Field(
        default_factory=list,
        description="Flat array of vertex coordinates [x0, y0, z0, x1, y1, z1, ...]"
    )
    faces: List[int] = Field(
        default_factory=list,
        description="Flat array of triangle vertex indices [i0, i1, i2, j0, j1, j2, ...]"
    )
    normals: Optional[List[float]] = Field(
        default=None,
        description="Optional flat array of vertex or face normals"
    )
    vertex_count: int = 0
    face_count: int = 0

class BuildingElement(BaseModel):
    element_id: str
    source_global_id: Optional[str] = None
    element_type: str
    name: str
    storey_id: Optional[str] = None
    storey_name: Optional[str] = None
    geometry: Optional[ElementGeometry] = None
    bounding_box: Optional[BoundingBox3D] = None
    source_properties: Dict[str, Any] = Field(default_factory=dict)
    materials: List[str] = Field(default_factory=list)
    classifications: List[str] = Field(default_factory=list)
    relationships: Dict[str, Any] = Field(default_factory=dict)
    quantity_estimates: Dict[str, float] = Field(default_factory=dict)
    property_provenance: Dict[str, str] = Field(default_factory=dict)
    structural_role: str = Field(
        default="unspecified",
        description="'load_bearing', 'structural_framing', 'non_load_bearing_partition', 'aperture', 'spatial_volume', or 'unspecified'"
    )
    is_load_bearing: Optional[bool] = None
    structural_material_grade: Optional[str] = None
    fire_rating: Optional[str] = None
    confidence_status: str = Field(
        default="imported",
        description="Data confidence status: 'imported', 'inferred', or 'unverified'"
    )

class StoreyInfo(BaseModel):
    storey_id: str
    name: str
    elevation_m: Optional[float] = None
    element_count: int = 0

class ProjectLocation(BaseModel):
    address: str = Field(default="New Delhi, Delhi, India", description="Human-readable project address or place name")
    latitude: float = Field(default=28.6139, description="Project latitude in decimal degrees WGS84")
    longitude: float = Field(default=77.2090, description="Project longitude in decimal degrees WGS84")
    elevation_m: Optional[float] = Field(default=216.0, description="Elevation above mean sea level in meters")
    is_confirmed: bool = Field(default=True, description="Whether location has been explicitly confirmed by project team")
    climate_zone: str = Field(default="Composite / Semi-Arid (Hot summers, Monsoon rains)", description="Köppen / NBC climate zone")
    georeferenced_source: str = Field(default="confirmed_project", description="'ifc_site', 'user_confirmed', or 'default_project'")
    local_to_world_transform: Dict[str, Any] = Field(default_factory=dict, description="Documented local-to-world coordinate transformation matrix")

class BuildingModel(BaseModel):
    model_id: str
    building_id: Optional[str] = Field(default=None, description="Unique building asset identifier")
    version: str = Field(default="1.0-baseline", description="Configuration or revision version")
    source_type: str = Field(default="ifc", description="'ifc', 'dxf', or 'sample'")
    source_filename: str
    import_timestamp: str
    schema_version: Optional[str] = None
    units: Dict[str, str] = Field(default_factory=dict)
    project_name: Optional[str] = None
    site_name: Optional[str] = None
    building_name: Optional[str] = None
    project_location: Optional[ProjectLocation] = Field(default=None, description="Associated confirmed geographical project location")
    storeys: List[StoreyInfo] = Field(default_factory=list)
    element_counts_by_type: Dict[str, int] = Field(default_factory=dict)
    total_element_count: int = 0
    available_properties: List[str] = Field(default_factory=list)
    missing_data: List[str] = Field(default_factory=list)
    structural_audit: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Structural property completeness, load-bearing breakdown, and missing documentation notices"
    )
    bounding_box: Optional[BoundingBox3D] = None
    georeferencing: Dict[str, Any] = Field(
        default_factory=dict,
        description="IFC map conversion, projected CRS, site coordinates, and true north orientation"
    )
    provenance_metadata: Dict[str, Any] = Field(default_factory=dict)

class BuildingModelDetail(BuildingModel):
    elements: List[BuildingElement] = Field(default_factory=list)

class QualityFinding(BaseModel):
    finding_id: str
    severity: str = Field(..., description="'info', 'warning', 'error', or 'critical'")
    category: str = Field(..., description="'hierarchy', 'geometry', 'identifier', 'material', 'coordination', 'completeness'")
    affected_element_ids: List[str] = Field(default_factory=list)
    description: str
    evidence: str
    limitation: str
    recommended_action: str

class ModelQualityReport(BaseModel):
    model_id: str
    total_findings: int
    by_severity: Dict[str, int] = Field(default_factory=dict)
    findings: List[QualityFinding] = Field(default_factory=list)
    data_completeness_ratio: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Ratio of elements having complete spatial and dimensional attributes"
    )
    summary: str

class EsgItem(BaseModel):
    criterion_id: str
    category: str = Field(..., description="'environmental', 'social', or 'governance'")
    criterion_name: str
    result_status: str = Field(
        ...,
        description="'assessed', 'estimated', 'potential_concern', 'insufficient_data', 'not_assessed', 'requires_professional_review'"
    )
    metric_value: Optional[Any] = None
    unit: Optional[str] = None
    evidence_available: str
    data_used: List[str] = Field(default_factory=list)
    calculation_or_rule_applied: str
    assumptions: List[str] = Field(default_factory=list)
    missing_inputs: List[str] = Field(default_factory=list)
    source_or_provenance: str
    recommended_action: str
    confidence_status: str = Field(..., description="'high', 'medium', 'low', or 'not_applicable'")

class EsgAssessmentReport(BaseModel):
    model_id: str
    disclaimer: str = (
        "Preliminary digital-twin ESG screening for hackathon exploration. "
        "Does not constitute third-party green building certification (e.g. LEED, BREEAM, GRIHA) "
        "or validated structural engineering compliance."
    )
    environmental: List[EsgItem] = Field(default_factory=list)
    social: List[EsgItem] = Field(default_factory=list)
    governance: List[EsgItem] = Field(default_factory=list)
    status_counts: Dict[str, int] = Field(default_factory=dict)

class ImportSummaryResponse(BaseModel):
    model_id: str
    source_filename: str
    schema_version: Optional[str] = None
    import_status: str = Field(..., description="'success', 'partial', or 'failed'")
    element_counts_by_type: Dict[str, int] = Field(default_factory=dict)
    total_elements: int = 0
    available_properties: List[str] = Field(default_factory=list)
    units: Dict[str, str] = Field(default_factory=dict)
    coordinate_metadata: Dict[str, Any] = Field(default_factory=dict)
    parsing_warnings: List[str] = Field(default_factory=list)
    missing_information_summary: List[str] = Field(default_factory=list)

class MaterialDistributionItem(BaseModel):
    material_name: str
    element_count: int
    approx_volume_m3: float
    percentage: float

class StoreyDistributionItem(BaseModel):
    storey_id: str
    storey_name: str
    element_count: int
    percentage: float

class IntelligenceFinding(BaseModel):
    finding_id: str
    title: str
    severity: str = Field(..., description="'Information', 'Warning', or 'High'")
    category: str = Field(..., description="'property', 'material', 'connectivity', 'identifier', 'spatial', 'geometry'")
    affected_element_id: str
    affected_element_name: str
    affected_global_id: Optional[str] = None
    affected_element_type: str
    flagged_reason: str
    evidence: str
    source_properties: Dict[str, Any] = Field(default_factory=dict)
    recommended_action: str

class EvidenceBasedRecommendation(BaseModel):
    id: str
    title: str
    category: str
    priority: str = Field(..., description="'high', 'medium', or 'low'")
    detected_issue: str
    explanation: str
    supporting_evidence: str
    proposed_intervention: str
    expected_benefit: str
    estimated_cost_inr: Optional[float] = None
    confidence: str = Field(default="high", description="'high', 'medium', or 'insufficient_data'")
    calculation_method: str
    limitations: str

class BuildingIntelligenceReport(BaseModel):
    model_id: str
    total_elements: int
    element_counts_by_category: Dict[str, int] = Field(default_factory=dict)
    material_distribution: List[MaterialDistributionItem] = Field(default_factory=list)
    model_completeness_pct: float
    findings_by_severity: Dict[str, int] = Field(default_factory=dict)
    storey_distribution: List[StoreyDistributionItem] = Field(default_factory=list)
    findings: List[IntelligenceFinding] = Field(default_factory=list)
    recommendations: List[EvidenceBasedRecommendation] = Field(default_factory=list)
    summary: str
