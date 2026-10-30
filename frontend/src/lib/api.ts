import { BuildingParams, BuildingValidationResult } from '../types/building';
import {
  RecommendationResponse,
  EstimateResponse,
  ApiHealthResponse,
} from '../types/recommendations';
import {
  BuildingModel,
  BuildingModelDetail,
  ImportSummaryResponse,
  ModelQualityReport,
  EsgAssessmentReport,
  BuildingIntelligenceReport,
} from '../types/digital_twin';
import {
  FloorPlanExtractionResponse,
  FloorPlan3DGenerateRequest,
} from '../types/floorplan';
import {
  EnvironmentalAnalysisRequest,
  EnvironmentalAnalysisResponse,
  LocationPreset,
  ClimateData,
} from '../types/environmental';
import { GeotechnicalSiteProfile } from '../types/geotechnical';
import { CityModel, CityBuildingSummary } from '../types/city';
import { SustainabilityAuditReport } from '../types/sustainability';
import { ScenarioComparisonReport } from '../types/scenarios';
import { EnergyPredictionResponse, ParetoOptimizationResponse } from '../types/ml_energy';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const REQUEST_TIMEOUT_MS = 8000;

class ApiError extends Error {
  status?: number;
  details?: string[];

  constructor(message: string, status?: number, details?: string[]) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.details = details;
  }
}

async function fetchWithTimeout(url: string, options: RequestInit = {}): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
        ...(options.headers || {}),
      },
    });
    return response;
  } catch (error: any) {
    if (error.name === 'AbortError') {
      throw new ApiError(`Request to ${url} timed out after ${REQUEST_TIMEOUT_MS / 1000}s`);
    }
    throw new ApiError(`Network error connecting to API: ${error.message || 'Server unreachable'}`);
  } finally {
    clearTimeout(id);
  }
}

export async function checkApiHealth(): Promise<ApiHealthResponse> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/health`, { method: 'GET' });
  if (!response.ok) {
    throw new ApiError(`Health check failed with HTTP ${response.status}`, response.status);
  }
  return response.json();
}

export async function validateBuildingApi(params: BuildingParams): Promise<BuildingValidationResult> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/v1/building/validate`, {
    method: 'POST',
    body: JSON.stringify(params),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const errorDetails = data?.errors || (data?.detail ? [data.detail] : ['Invalid building configuration']);
    throw new ApiError(errorDetails.join('; '), response.status, errorDetails);
  }

  return data as BuildingValidationResult;
}

// Token counter to prevent stale asynchronous responses from overriding newer user inputs
let latestRecommendationSeq = 0;

export async function getRecommendationsApi(
  params: BuildingParams
): Promise<{ data: RecommendationResponse; isStale: boolean }> {
  const currentSeq = ++latestRecommendationSeq;

  const response = await fetchWithTimeout(`${API_BASE_URL}/api/v1/recommendations`, {
    method: 'POST',
    body: JSON.stringify(params),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const errorDetails = data?.errors || (data?.detail ? [data.detail] : ['Failed to fetch recommendations']);
    throw new ApiError(errorDetails.join('; '), response.status, errorDetails);
  }

  return {
    data: data as RecommendationResponse,
    isStale: currentSeq !== latestRecommendationSeq,
  };
}

let latestEstimateSeq = 0;

export async function getEstimateApi(
  params: BuildingParams,
  annualElectricityKwh?: number
): Promise<{ data: EstimateResponse; isStale: boolean }> {
  const currentSeq = ++latestEstimateSeq;

  const payload: any = {
    ...params,
  };
  if (annualElectricityKwh !== undefined && annualElectricityKwh > 0) {
    payload.annual_electricity_kwh = annualElectricityKwh;
  }

  const response = await fetchWithTimeout(`${API_BASE_URL}/api/v1/estimate`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const errorDetails = data?.errors || (data?.detail ? [data.detail] : ['Failed to calculate impact estimate']);
    throw new ApiError(errorDetails.join('; '), response.status, errorDetails);
  }

  return {
    data: data as EstimateResponse,
    isStale: currentSeq !== latestEstimateSeq,
  };
}

export async function fetchModelsApi(): Promise<BuildingModel[]> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/v1/models`, { method: 'GET' });
  if (!response.ok) {
    throw new ApiError(`Failed to load models list (${response.status})`, response.status);
  }
  return response.json();
}

export async function importIfcFileApi(file: File): Promise<ImportSummaryResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), 60000); // 60s for geometry tessellation

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/models/import/ifc`, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
    });

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const msg = data?.detail || `IFC Import failed with HTTP ${response.status}`;
      throw new ApiError(msg, response.status);
    }

    return data as ImportSummaryResponse;
  } catch (error: any) {
    if (error.name === 'AbortError') {
      throw new ApiError('IFC parsing request timed out.');
    }
    throw error;
  } finally {
    clearTimeout(id);
  }
}

export async function fetchModelDetailApi(modelId: string): Promise<BuildingModelDetail> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/v1/models/${encodeURIComponent(modelId)}`, {
    method: 'GET',
  });
  if (!response.ok) {
    throw new ApiError(`Failed to load digital twin model (${response.status})`, response.status);
  }
  return response.json();
}

export async function fetchModelQualityApi(modelId: string): Promise<ModelQualityReport> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/v1/models/${encodeURIComponent(modelId)}/quality`, {
    method: 'GET',
  });
  if (!response.ok) {
    throw new ApiError(`Failed to load model quality report (${response.status})`, response.status);
  }
  return response.json();
}

export async function fetchModelEsgApi(modelId: string, annualKwh?: number): Promise<EsgAssessmentReport> {
  let url = `${API_BASE_URL}/api/v1/models/${encodeURIComponent(modelId)}/esg`;
  if (annualKwh !== undefined && annualKwh > 0) {
    url += `?annual_kwh=${annualKwh}`;
  }
  const response = await fetchWithTimeout(url, { method: 'GET' });
  if (!response.ok) {
    throw new ApiError(`Failed to load ESG assessment (${response.status})`, response.status);
  }
  return response.json();
}

export async function fetchModelIntelligenceApi(modelId: string): Promise<BuildingIntelligenceReport> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/v1/models/${encodeURIComponent(modelId)}/intelligence`, {
    method: 'GET',
  });
  if (!response.ok) {
    throw new ApiError(`Failed to load building intelligence report (${response.status})`, response.status);
  }
  return response.json();
}

export async function fetchModelParametricBaselineApi(modelId: string): Promise<any> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/v1/models/${encodeURIComponent(modelId)}/parametric-baseline`, {
    method: 'GET',
  });
  if (!response.ok) {
    throw new ApiError(`Failed to load parametric baseline for model (${response.status})`, response.status);
  }
  return response.json();
}

export async function extractFloorplanApi(
  file: File,
  knownDimensionM?: number
): Promise<FloorPlanExtractionResponse> {
  const formData = new FormData();
  formData.append('file', file);
  if (knownDimensionM !== undefined && knownDimensionM > 0) {
    formData.append('known_dimension_m', knownDimensionM.toString());
  }

  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), 45000); // 45s timeout for CV extraction

  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/floorplan/extract`, {
      method: 'POST',
      body: formData,
      signal: controller.signal,
    });

    const data = await response.json().catch(() => null);
    if (!response.ok) {
      const msg = data?.detail || `Floorplan extraction failed with HTTP ${response.status}`;
      throw new ApiError(msg, response.status);
    }
    return data as FloorPlanExtractionResponse;
  } catch (err: any) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(err.name === 'AbortError' ? 'Extraction request timed out' : err.message);
  } finally {
    clearTimeout(id);
  }
}

export async function extractSampleFloorplanApi(
  sampleName: string = 'commercial'
): Promise<FloorPlanExtractionResponse> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/v1/floorplan/sample/${sampleName}`, {
    method: 'POST',
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to extract sample drawing', response.status);
  }
  return data as FloorPlanExtractionResponse;
}

export async function generate3dFromFloorplanApi(
  req: FloorPlan3DGenerateRequest
): Promise<ImportSummaryResponse> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/v1/floorplan/generate-3d`, {
    method: 'POST',
    body: JSON.stringify(req),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to generate 3D building from floorplan', response.status);
  }
  return data as ImportSummaryResponse;
}

export async function analyzeEnvironmentalSuitabilityApi(
  req: EnvironmentalAnalysisRequest
): Promise<EnvironmentalAnalysisResponse> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/v1/environmental/analyze`, {
    method: 'POST',
    body: JSON.stringify(req),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Environmental analysis failed', response.status);
  }
  return data as EnvironmentalAnalysisResponse;
}

export async function searchLocationsApi(
  query: string
): Promise<Array<{ display_name: string; latitude: number; longitude: number; city?: string; state?: string; country?: string; type?: string }>> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/environmental/geocode?query=${encodeURIComponent(query)}`,
    { method: 'GET' }
  );
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Geocoding search failed', response.status);
  }
  return data || [];
}

export async function getLocationPresetsApi(): Promise<LocationPreset[]> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/v1/environmental/presets`, {
    method: 'GET',
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to fetch location presets', response.status);
  }
  return data || [];
}

export async function getClimateDataApi(
  latitude: number,
  longitude: number
): Promise<ClimateData> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/environmental/climate?latitude=${latitude}&longitude=${longitude}`,
    { method: 'GET' }
  );
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to fetch climate data', response.status);
  }
  return data as ClimateData;
}

export async function fetchGeotechnicalProfileApi(
  latitude: number = 28.6139,
  longitude: number = 77.2090,
  siteId: string = 'site-001'
): Promise<GeotechnicalSiteProfile> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/geotechnical/profile?latitude=${latitude}&longitude=${longitude}&site_id=${siteId}`,
    { method: 'GET' }
  );
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to fetch geotechnical profile', response.status);
  }
  return data as GeotechnicalSiteProfile;
}

export async function fetchCityModelApi(): Promise<CityModel> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/v1/city/model`, { method: 'GET' });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to fetch city-scale model', response.status);
  }
  return data as CityModel;
}

export async function fetchCityBuildingApi(buildingId: string): Promise<CityBuildingSummary> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/v1/city/buildings/${buildingId}`, { method: 'GET' });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || `Failed to fetch building ${buildingId}`, response.status);
  }
  return data as CityBuildingSummary;
}

export async function fetchSustainabilityReportApi(
  targetEntityId: string = 'sample-office-twin',
  level: string = 'building',
  latitude: number = 28.6139,
  longitude: number = 77.2090
): Promise<SustainabilityAuditReport> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/sustainability/report?target_entity_id=${targetEntityId}&level=${level}&latitude=${latitude}&longitude=${longitude}`,
    { method: 'GET' }
  );
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to fetch sustainability intelligence report', response.status);
  }
  return data as SustainabilityAuditReport;
}

export async function fetchScenarioComparisonApi(
  buildingId: string = 'sample-office-twin',
  timeHorizon: number = 2026
): Promise<ScenarioComparisonReport> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/scenarios/compare?building_id=${buildingId}&time_horizon=${timeHorizon}`,
    { method: 'GET' }
  );
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to fetch scenario comparison', response.status);
  }
  return data as ScenarioComparisonReport;
}

export async function fetchMLEnergyPredictionApi(
  modelId: string = 'sample-office-twin'
): Promise<EnergyPredictionResponse> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/ml/energy-prediction?model_id=${modelId}`,
    { method: 'GET' }
  );
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to compute ML energy predictions', response.status);
  }
  return data as EnergyPredictionResponse;
}

export async function fetchParetoOptimizationApi(
  budgetInr: number = 500000
): Promise<ParetoOptimizationResponse> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/ml/pareto-optimization?budget_inr=${budgetInr}`,
    { method: 'GET' }
  );
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to fetch Pareto optimization alternatives', response.status);
  }
  return data as ParetoOptimizationResponse;
}

export { ApiError, API_BASE_URL };
