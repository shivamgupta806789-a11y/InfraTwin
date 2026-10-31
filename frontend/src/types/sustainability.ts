export interface ComprehensiveRecommendation {
  id: string;
  category: 'environmental_sustainability' | 'geotechnical_suitability' | 'infrastructure_resilience' | 'urban_planning' | 'lifecycle_future_risk';
  category_title: string;
  hierarchical_level: 'city' | 'district' | 'site' | 'building' | 'element';
  target_entity_id?: string | null;
  priority: 'critical' | 'high' | 'medium' | 'low';
  title: string;
  detected_condition: string;
  evidence: string;
  explanation: string;
  proposed_intervention: string;
  expected_benefit: string;
  estimated_cost_inr?: number | null;
  time_horizon: 'immediate' | 'near_term_2026' | 'mid_term_2035' | 'long_term_2050';
  confidence: 'high' | 'medium' | 'insufficient_data';
  data_sources: string[];
  relevant_building_feature?: string | null;
  relevant_location_feature?: string | null;
  contributing_datasets?: string[];
  assumptions: string[];
  missing_information: string[];
  validation_requirements: string;
}

export interface SustainabilityAuditReport {
  target_entity_id: string;
  target_level: string;
  timestamp: string;
  summary_counts: Record<string, number>;
  recommendations: ComprehensiveRecommendation[];
  insufficient_data_warnings: string[];
  dataset_statuses?: Record<string, string>;
  location_profile?: any;
}
