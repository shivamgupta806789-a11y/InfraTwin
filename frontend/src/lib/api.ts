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

export { ApiError, API_BASE_URL };
