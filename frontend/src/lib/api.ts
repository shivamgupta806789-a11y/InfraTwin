import { BuildingParams, BuildingValidationResult } from '../types/building';
import {
  RecommendationResponse,
  EstimateResponse,
  ApiHealthResponse,
  AppliedInterventionsRequest,
  AppliedInterventionsResponse,
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
import {
  RainwaterRecommendationReport,
  BuildingUnifiedFeatures,
  LocationClimateProfile,
} from '../types/rainwater';
import {
  BuildingFurnishingPlan,
  FurnitureItem,
  FurnitureUpdateRequest,
  FurnitureAddRequest,
  FurnitureCatalogCategory,
} from '../types/furniture';

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

async function fetchWithTimeout(url: string, options: RequestInit = {}, timeoutMs: number = REQUEST_TIMEOUT_MS): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData;
    const defaultHeaders: Record<string, string> = {
      Accept: 'application/json',
      ...(!isFormData ? { 'Content-Type': 'application/json' } : {}),
    };
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        ...defaultHeaders,
        ...(options.headers || {}),
      },
    });
    return response;
  } catch (error: any) {
    if (error.name === 'AbortError') {
      throw new ApiError(`Request to ${url} timed out after ${timeoutMs / 1000}s`);
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

export async function importCityFileApi(
  file: File,
  districtName?: string,
  districtType: string = 'Commercial Center'
): Promise<CityModel> {
  const formData = new FormData();
  formData.append('file', file);
  if (districtName && districtName.trim()) {
    formData.append('district_name', districtName.trim());
  }
  formData.append('district_type', districtType);

  const response = await fetchWithTimeout(`${API_BASE_URL}/api/v1/city/import-file`, {
    method: 'POST',
    body: formData,
  }, 45000);

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to import city/district file', response.status);
  }
  return data as CityModel;
}

export async function restoreSampleCityApi(): Promise<CityModel> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/v1/city/restore-sample`, {
    method: 'POST',
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to restore default sample city', response.status);
  }
  return data as CityModel;
}

export async function fetchCitySupportedFormatsApi(): Promise<Record<string, string>> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/v1/city/supported-formats`, {
    method: 'GET',
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    return {
      '.geojson': 'GeoJSON FeatureCollection',
      '.cityjson': 'CityJSON 3D Model',
      '.zip': 'Shapefile Archive (.shp, .shx, .dbf)',
      '.gpkg': 'GeoPackage Database',
      '.dxf': 'AutoCAD Drawing Exchange Format',
    };
  }
  return data as Record<string, string>;
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

export async function fetchRainwaterRecommendationsApi(
  buildingId: string = 'sample-office-twin',
  latitude?: number,
  longitude?: number,
  buildingType?: string,
  occupancy?: number
): Promise<RainwaterRecommendationReport> {
  const params = new URLSearchParams();
  params.append('building_id', buildingId);
  if (latitude != null) params.append('latitude', latitude.toString());
  if (longitude != null) params.append('longitude', longitude.toString());
  if (buildingType) params.append('building_type', buildingType);
  if (occupancy != null) params.append('occupancy', occupancy.toString());

  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/rainwater/recommendations?${params.toString()}`,
    { method: 'GET' }
  );
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to fetch rainwater recommendations', response.status);
  }
  return data as RainwaterRecommendationReport;
}

export async function fetchRainwaterFeaturesApi(
  buildingId: string = 'sample-office-twin',
  latitude?: number,
  longitude?: number
): Promise<BuildingUnifiedFeatures> {
  const params = new URLSearchParams();
  params.append('model_id', buildingId);
  if (latitude != null) params.append('latitude', latitude.toString());
  if (longitude != null) params.append('longitude', longitude.toString());

  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/rainwater/features?${params.toString()}`,
    { method: 'GET' }
  );
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to fetch building unified features', response.status);
  }
  return data as BuildingUnifiedFeatures;
}

export async function fetchRainwaterClimateApi(
  latitude: number = 28.6139,
  longitude: number = 77.2090
): Promise<LocationClimateProfile> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/rainwater/climate-profile?latitude=${latitude}&longitude=${longitude}`,
    { method: 'GET' }
  );
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to fetch location climate profile', response.status);
  }
  return data as LocationClimateProfile;
}

export async function fetchRainwaterMlMetricsApi(): Promise<any> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/rainwater/ml-metrics`,
    { method: 'GET' }
  );
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to fetch ML model evaluation metrics', response.status);
  }
  return data;
}

export async function fetchBuildingFurnishingPlanApi(
  modelId: string,
  autoGenerate: boolean = true
): Promise<BuildingFurnishingPlan> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/furniture/plan/${encodeURIComponent(modelId)}?auto_generate=${autoGenerate}`,
    { method: 'GET' }
  );
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to fetch building furnishing plan', response.status);
  }
  return data as BuildingFurnishingPlan;
}

export async function generateBuildingFurnishingPlanApi(
  modelId: string,
  customRoomTypes?: Record<string, string>,
  forceRegenerate: boolean = true
): Promise<BuildingFurnishingPlan> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/furniture/plan/${encodeURIComponent(modelId)}/generate?force_regenerate=${forceRegenerate}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(customRoomTypes || {}),
    }
  );
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to generate building furnishing plan', response.status);
  }
  return data as BuildingFurnishingPlan;
}

export async function updateFurnitureItemApi(
  modelId: string,
  furnitureId: string,
  update: FurnitureUpdateRequest
): Promise<FurnitureItem> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/furniture/plan/${encodeURIComponent(modelId)}/item/${encodeURIComponent(furnitureId)}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(update),
    }
  );
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to update furniture item', response.status);
  }
  return data as FurnitureItem;
}

export async function removeFurnitureItemApi(
  modelId: string,
  furnitureId: string
): Promise<{ status: string; message: string }> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/furniture/plan/${encodeURIComponent(modelId)}/item/${encodeURIComponent(furnitureId)}`,
    { method: 'DELETE' }
  );
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to delete furniture item', response.status);
  }
  return data;
}

export async function addFurnitureItemApi(
  modelId: string,
  request: FurnitureAddRequest
): Promise<FurnitureItem> {
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/furniture/plan/${encodeURIComponent(modelId)}/item`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    }
  );
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to add furniture item', response.status);
  }
  return data as FurnitureItem;
}

export async function fetchFurnitureCatalogApi(): Promise<{ categories: FurnitureCatalogCategory[] }> {
  const response = await fetchWithTimeout(`${API_BASE_URL}/api/v1/furniture/catalog`, {
    method: 'GET',
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to fetch furniture catalog', response.status);
  }
  return data;
}

export async function generateAppliedInterventionsApi(
  request: AppliedInterventionsRequest
): Promise<AppliedInterventionsResponse> {
  const modelIdPart = request.model_id ? encodeURIComponent(request.model_id) : 'sample-office-twin';
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/api/v1/models/${modelIdPart}/interventions`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    }
  );
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(data?.detail || 'Failed to generate applied interventions', response.status);
  }
  return data as AppliedInterventionsResponse;
}

export { ApiError, API_BASE_URL };
