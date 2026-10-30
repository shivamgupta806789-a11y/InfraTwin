export interface BoundingBox3D {
  min_x: number;
  min_y: number;
  min_z: number;
  max_x: number;
  max_y: number;
  max_z: number;
  center_x: number;
  center_y: number;
  center_z: number;
  width: number;
  height: number;
  depth: number;
}

export interface ElementGeometry {
  format: 'indexed_mesh' | 'bbox' | 'none';
  vertices: number[];
  faces: number[];
  normals?: number[];
  vertex_count: number;
  face_count: number;
}

export interface BuildingElement {
  element_id: string;
  source_global_id?: string | null;
  element_type: string;
  name: string;
  storey_id?: string | null;
  storey_name?: string | null;
  geometry?: ElementGeometry | null;
  bounding_box?: BoundingBox3D | null;
  source_properties: Record<string, any>;
  materials: string[];
  classifications?: string[];
  relationships?: Record<string, any>;
  quantity_estimates: Record<string, number>;
  property_provenance: Record<string, string>;
  confidence_status: 'imported' | 'inferred' | 'unverified';
}

export interface StoreyInfo {
  storey_id: string;
  name: string;
  elevation_m?: number | null;
  element_count: number;
}

export interface BuildingModel {
  model_id: string;
  source_type: 'ifc' | 'dxf' | 'sample';
  source_filename: string;
  import_timestamp: string;
  schema_version?: string | null;
  units: Record<string, string>;
  project_name?: string | null;
  site_name?: string | null;
  building_name?: string | null;
  storeys: StoreyInfo[];
  element_counts_by_type: Record<string, number>;
  total_element_count: number;
  available_properties: string[];
  missing_data: string[];
  bounding_box?: BoundingBox3D | null;
  provenance_metadata: Record<string, any>;
}

export interface BuildingModelDetail extends BuildingModel {
  elements: BuildingElement[];
}

export interface QualityFinding {
  finding_id: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  category: 'hierarchy' | 'geometry' | 'identifier' | 'material' | 'coordination' | 'completeness';
  affected_element_ids: string[];
  description: string;
  evidence: string;
  limitation: string;
  recommended_action: string;
}

export interface ModelQualityReport {
  model_id: string;
  total_findings: number;
  by_severity: Record<string, number>;
  findings: QualityFinding[];
  data_completeness_ratio: number;
  summary: string;
}

export interface EsgItem {
  criterion_id: string;
  category: 'environmental' | 'social' | 'governance';
  criterion_name: string;
  result_status: 'assessed' | 'estimated' | 'potential_concern' | 'insufficient_data' | 'not_assessed' | 'requires_professional_review';
  metric_value?: any;
  unit?: string | null;
  evidence_available: string;
  data_used: string[];
  calculation_or_rule_applied: string;
  assumptions: string[];
  missing_inputs: string[];
  source_or_provenance: string;
  recommended_action: string;
  confidence_status: 'high' | 'medium' | 'low' | 'not_applicable';
}

export interface EsgAssessmentReport {
  model_id: string;
  disclaimer: string;
  environmental: EsgItem[];
  social: EsgItem[];
  governance: EsgItem[];
  status_counts: Record<string, number>;
}

export interface ImportSummaryResponse {
  model_id: string;
  source_filename: string;
  schema_version?: string | null;
  import_status: 'success' | 'partial' | 'failed';
  element_counts_by_type: Record<string, number>;
  total_elements: number;
  available_properties: string[];
  units: Record<string, string>;
  coordinate_metadata: Record<string, any>;
  parsing_warnings: string[];
  missing_information_summary: string[];
}

export interface MaterialDistributionItem {
  material_name: string;
  element_count: number;
  approx_volume_m3: number;
  percentage: number;
}

export interface StoreyDistributionItem {
  storey_id: string;
  storey_name: string;
  element_count: number;
  percentage: number;
}

export interface IntelligenceFinding {
  finding_id: string;
  title: string;
  severity: 'Information' | 'Warning' | 'High';
  category: 'property' | 'material' | 'connectivity' | 'identifier' | 'spatial' | 'geometry';
  affected_element_id: string;
  affected_element_name: string;
  affected_global_id?: string | null;
  affected_element_type: string;
  flagged_reason: string;
  why_flagged?: string;
  evidence: string;
  source_properties?: Record<string, any>;
  recommended_action: string;
}

export interface BuildingIntelligenceReport {
  model_id: string;
  total_elements: number;
  element_counts_by_category: Record<string, number>;
  material_distribution: MaterialDistributionItem[];
  model_completeness_pct: number;
  findings_by_severity: Record<string, number>;
  storey_distribution: StoreyDistributionItem[];
  findings: IntelligenceFinding[];
  summary: string;
}
