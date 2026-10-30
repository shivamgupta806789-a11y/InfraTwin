import React, { useState, useEffect, useCallback, useRef } from 'react';
import { BuildingParams, InterventionId, BuildingFormErrors } from './types/building';
import {
  RecommendationResponse,
  EstimateResponse,
  ApiHealthResponse,
} from './types/recommendations';
import {
  BuildingModel,
  BuildingModelDetail,
  BuildingElement,
  ModelQualityReport,
  EsgAssessmentReport,
  BuildingIntelligenceReport,
} from './types/digital_twin';
import { validateBuildingParams } from './lib/validation';
import {
  checkApiHealth,
  getRecommendationsApi,
  getEstimateApi,
  fetchModelsApi,
  fetchModelDetailApi,
  fetchModelQualityApi,
  fetchModelEsgApi,
  fetchModelIntelligenceApi,
  fetchModelParametricBaselineApi,
  ApiError,
} from './lib/api';
import { BuildingForm } from './components/BuildingForm';
import { InterventionToggle } from './components/InterventionToggle';
import { BudgetSummary } from './components/BudgetSummary';
import { DesignComparison } from './components/DesignComparison';
import { RecommendationList } from './components/RecommendationList';
import { ApiStatus } from './components/ApiStatus';
import { ImpactModal } from './components/ImpactModal';
import { BuildingViewer } from './components/BuildingViewer';
import { IfcUploadModal } from './components/IfcUploadModal';
import { FloorplanUploadModal } from './components/FloorplanUploadModal';
import { FloorplanCorrectionEditor } from './components/FloorplanCorrectionEditor';
import { ElementInspector } from './components/ElementInspector';
import { QualityReportView } from './components/QualityReportView';
import { EsgDashboardView } from './components/EsgDashboardView';
import { IntelligenceDashboardView } from './components/IntelligenceDashboardView';
import { EnvironmentalDashboardView } from './components/EnvironmentalDashboardView';
import { FloorPlanExtractionResponse } from './types/floorplan';
import { HomePage } from './components/HomePage';
import { CityViewer } from './components/CityViewer';
import { ScenarioIntelligenceView } from './components/ScenarioIntelligenceView';
import { GeotechnicalIntelligenceView } from './components/GeotechnicalIntelligenceView';
import { MLEnergyOptimizerView } from './components/MLEnergyOptimizerView';
import { CityModel } from './types/city';
import { fetchCityModelApi } from './lib/api';
import {
  Leaf,
  Scale,
  ShieldAlert,
  Boxes,
  Building2,
  Upload,
  ShieldCheck,
  Layers,
  Filter,
  Sparkles,
  FileImage,
  Globe,
  Brain,
  Calendar,
  Compass,
  Home as HomeIcon,
} from 'lucide-react';

export type AppNavigationMode =
  | 'home'
  | 'city_twin'
  | 'digital_twin'
  | 'parametric'
  | 'scenarios'
  | 'geotechnical'
  | 'ml_optimizer';

const DEFAULT_SAMPLE_BUILDING: BuildingParams = {
  width_m: 12.0,
  length_m: 16.0,
  floor_height_m: 3.0,
  floors: 2,
  window_count: 16,
  budget_inr: 250000.0,
  selected_interventions: ['reflective_roof', 'external_shading'],
};

export const App: React.FC = () => {
  // Navigation Mode: Unified across Platform Phases 1-8
  const [activeMode, setActiveMode] = useState<AppNavigationMode>('home');

  // City-scale Digital Twin state (Phase 5)
  const [cityModel, setCityModel] = useState<CityModel | null>(null);
  const [isCityLoading, setIsCityLoading] = useState<boolean>(false);

  // Digital Twin state
  const [currentModelId, setCurrentModelId] = useState<string>('sample-office-twin');
  const [availableModels, setAvailableModels] = useState<BuildingModel[]>([]);
  const [importedModel, setImportedModel] = useState<BuildingModelDetail | null>(null);
  const [selectedElement, setSelectedElement] = useState<BuildingElement | null>(null);
  const [qualityReport, setQualityReport] = useState<ModelQualityReport | null>(null);
  const [esgReport, setEsgReport] = useState<EsgAssessmentReport | null>(null);
  const [intelligenceReport, setIntelligenceReport] = useState<BuildingIntelligenceReport | null>(null);
  const [highlightedElementIds, setHighlightedElementIds] = useState<string[]>([]);
  const [highlightSeverity, setHighlightSeverity] = useState<string | null>(null);
  const [isTwinLoading, setIsTwinLoading] = useState<boolean>(false);
  const [twinTab, setTwinTab] = useState<'3d_twin' | 'intelligence_dashboard' | 'quality_audit' | 'esg_assessment' | 'geolocation_climate'>('3d_twin');

  // Filter state for Digital Twin 3D view
  const [selectedStoreyId, setSelectedStoreyId] = useState<string | null>(null);
  const [visibleTypes, setVisibleTypes] = useState<string[]>([]);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState<boolean>(false);

  // 2D Floor Plan to 3D Generation State
  const [isFloorplanUploadOpen, setIsFloorplanUploadOpen] = useState<boolean>(false);
  const [isFloorplanEditorOpen, setIsFloorplanEditorOpen] = useState<boolean>(false);
  const [floorplanExtraction, setFloorplanExtraction] = useState<FloorPlanExtractionResponse | null>(null);
  const [floorplanInitialParams, setFloorplanInitialParams] = useState<{
    floors: number;
    floorHeight: number;
    buildingType: string;
    roofType: 'flat' | 'parapet' | 'gable';
  } | null>(null);

  // Parametric Building inputs state
  const [params, setParams] = useState<BuildingParams>(DEFAULT_SAMPLE_BUILDING);
  const [formErrors, setFormErrors] = useState<BuildingFormErrors>({});

  // Backend Connectivity state
  const [apiStatus, setApiStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');
  const [healthData, setHealthData] = useState<ApiHealthResponse | null>(null);
  const [apiErrorMessage, setApiErrorMessage] = useState<string | null>(null);

  // Recommendations and Estimations from backend
  const [recommendations, setRecommendations] = useState<RecommendationResponse | null>(null);
  const [estimate, setEstimate] = useState<EstimateResponse | null>(null);
  const [isLoadingRecommendations, setIsLoadingRecommendations] = useState<boolean>(false);
  const [recommendationsError, setRecommendationsError] = useState<string | null>(null);

  // Measured electricity kWh for honest impact estimation
  const [annualKwh, setAnnualKwh] = useState<number>(24000);
  const [isImpactModalOpen, setIsImpactModalOpen] = useState<boolean>(false);

  // 1. Initial Health Check on Mount
  const pingHealth = useCallback(async () => {
    setApiStatus('checking');
    setApiErrorMessage(null);
    try {
      const data = await checkApiHealth();
      setHealthData(data);
      setApiStatus('connected');
    } catch (err: any) {
      setApiStatus('disconnected');
      setApiErrorMessage(err.message || 'FastAPI backend unavailable on port 8000');
    }
  }, []);

  useEffect(() => {
    pingHealth();
  }, [pingHealth]);

  // 2. Load Digital Twin Model by ID
  const loadDigitalTwinModel = useCallback(async (modelId: string) => {
    setIsTwinLoading(true);
    setSelectedElement(null);
    try {
      const modelDetail = await fetchModelDetailApi(modelId);
      setImportedModel(modelDetail);
      setCurrentModelId(modelId);

      // Initialize filter with all present element types
      const types = Object.keys(modelDetail.element_counts_by_type || {});
      setVisibleTypes(types);

      // Fetch Quality, ESG, Intelligence reports, and Parametric Baseline
      const [qReport, eReport, iReport, pBaseline, mList] = await Promise.all([
        fetchModelQualityApi(modelId).catch(() => null),
        fetchModelEsgApi(modelId, annualKwh).catch(() => null),
        fetchModelIntelligenceApi(modelId).catch(() => null),
        fetchModelParametricBaselineApi(modelId).catch(() => null),
        fetchModelsApi().catch(() => []),
      ]);
      setQualityReport(qReport);
      setEsgReport(eReport);
      setIntelligenceReport(iReport);
      if (mList && mList.length > 0) {
        setAvailableModels(mList);
      }
      if (pBaseline) {
        setParams((prev) => ({
          ...prev,
          width_m: pBaseline.width_m,
          length_m: pBaseline.length_m,
          floor_height_m: pBaseline.floor_height_m,
          floors: pBaseline.floors,
          window_count: pBaseline.window_count,
        }));
      }
    } catch (err: any) {
      console.warn('Digital twin load notice:', err.message);
    } finally {
      setIsTwinLoading(false);
    }
  }, [annualKwh]);

  useEffect(() => {
    if (apiStatus === 'connected') {
      loadDigitalTwinModel(currentModelId);
      setIsCityLoading(true);
      fetchCityModelApi()
        .then((data) => setCityModel(data))
        .catch((err) => console.warn('City model fetch notice:', err))
        .finally(() => setIsCityLoading(false));
    }
  }, [apiStatus, currentModelId, loadDigitalTwinModel]);

  // Drilldown from City Model or Home Page into detailed Building BIM
  const handleSelectBuildingForBim = (buildingId: string) => {
    loadDigitalTwinModel(buildingId);
    setActiveMode('digital_twin');
    setTwinTab('3d_twin');
  };

  // 3. Fetch recommendations for parametric mode
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchRecommendations = useCallback(async (currentParams: BuildingParams) => {
    const { isValid, errors } = validateBuildingParams(currentParams);
    setFormErrors(errors);
    if (!isValid) return;

    setIsLoadingRecommendations(true);
    setRecommendationsError(null);

    try {
      const { data: recData, isStale: recStale } = await getRecommendationsApi(currentParams);
      if (!recStale) {
        setRecommendations(recData);
        setApiStatus('connected');
      }

      const { data: estData, isStale: estStale } = await getEstimateApi(currentParams, annualKwh);
      if (!estStale) {
        setEstimate(estData);
      }
    } catch (err: any) {
      if (err instanceof ApiError) {
        setRecommendationsError(err.message);
      } else {
        setRecommendationsError('Unable to connect to backend recommendation service.');
      }
      if (err.message && err.message.includes('Network error')) {
        setApiStatus('disconnected');
      }
    } finally {
      setIsLoadingRecommendations(false);
    }
  }, [annualKwh]);

  useEffect(() => {
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    debounceTimerRef.current = setTimeout(() => {
      fetchRecommendations(params);
    }, 300);

    return () => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    };
  }, [params, fetchRecommendations]);

  const handleParamChange = (updated: Partial<BuildingParams>) => {
    setParams((prev) => ({
      ...prev,
      ...updated,
    }));
  };

  const handleResetSample = () => {
    setParams(DEFAULT_SAMPLE_BUILDING);
  };

  const handleToggleIntervention = (id: InterventionId) => {
    setParams((prev) => {
      const exists = prev.selected_interventions.includes(id);
      const updatedInterventions = exists
        ? prev.selected_interventions.filter((i) => i !== id)
        : [...prev.selected_interventions, id];
      return {
        ...prev,
        selected_interventions: updatedInterventions,
      };
    });
  };

  const handleApplyRecommendedBundle = () => {
    if (!recommendations) return;
    const bundleIds = recommendations.ranked_recommendations.map((r) => r.id as InterventionId);
    setParams((prev) => ({
      ...prev,
      selected_interventions: bundleIds,
    }));
  };

  const handleToggleElementType = (type: string) => {
    setVisibleTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const totalSelectedCost = estimate ? estimate.total_cost_inr : 0;

  return (
    <div className="min-h-screen bg-stone-100 flex flex-col text-charcoal-900 selection:bg-emerald-100">
      {/* Top Header */}
      <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-charcoal-200 shadow-2xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-lg bg-charcoal-900 text-white flex items-center justify-center shadow-xs">
              <Leaf className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-sm sm:text-base font-bold text-charcoal-900 tracking-tight">
                  InfraTwinAI
                </h1>
                <span className="text-[10px] uppercase font-semibold bg-charcoal-100 text-charcoal-700 px-2 py-0.5 rounded border border-charcoal-200">
                  Building Digital Twin & ESG Platform
                </span>
              </div>
              <p className="text-[11px] text-charcoal-500 hidden sm:block">
                CAD/BIM Ingestion • Parametric Optimization • Evidence-Based ESG Screening
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* Unified Platform Navigation */}
            <nav className="flex items-center overflow-x-auto bg-stone-100 p-1 rounded-xl border border-charcoal-200 text-xs">
              {[
                { id: 'home', label: 'Home', icon: HomeIcon },
                { id: 'city_twin', label: 'City District', icon: Globe },
                { id: 'digital_twin', label: 'BIM Twin', icon: Boxes },
                { id: 'parametric', label: 'Parametric', icon: Building2 },
                { id: 'scenarios', label: 'Scenarios', icon: Calendar },
                { id: 'geotechnical', label: 'Subsurface', icon: Compass },
                { id: 'ml_optimizer', label: 'ML Energy', icon: Brain },
              ].map((tab) => {
                const Icon = tab.icon;
                const isActive = activeMode === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveMode(tab.id as AppNavigationMode)}
                    className={`flex items-center space-x-1 px-2.5 py-1 rounded-lg font-semibold whitespace-nowrap transition-all ${
                      isActive
                        ? 'bg-charcoal-900 text-white shadow-2xs'
                        : 'text-charcoal-600 hover:text-charcoal-900 hover:bg-stone-200/50'
                    }`}
                  >
                    <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-white' : 'text-charcoal-500'}`} />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </nav>

            {/* Scientific Disclosures Modal Button */}
            <button
              onClick={() => setIsImpactModalOpen(true)}
              className="hidden lg:flex items-center space-x-1.5 text-xs text-charcoal-700 bg-stone-50 hover:bg-stone-100 border border-charcoal-200 px-2.5 py-1.5 rounded-lg transition-colors shadow-2xs"
            >
              <Scale className="w-3.5 h-3.5 text-emerald-700" />
              <span>Scientific Honesty</span>
            </button>

            {/* Backend Connection Indicator */}
            <ApiStatus
              status={apiStatus}
              healthData={healthData}
              errorMessage={apiErrorMessage}
              onRetry={pingHealth}
            />
          </div>
        </div>
      </header>

      {/* Backend Offline Warning Banner if disconnected */}
      {apiStatus === 'disconnected' && (
        <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2 text-xs text-amber-900 flex items-center justify-between">
          <div className="max-w-7xl mx-auto w-full flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 text-amber-600 shrink-0" />
            <span>
              <strong>FastAPI backend is offline:</strong> The 3D viewer is active with local geometric feedback, but backend IFC parsing and ESG services are currently unavailable. Ensure Uvicorn is running on port 8000.
            </span>
          </div>
        </div>
      )}

      {/* Recommendations API Error Banner */}
      {recommendationsError && apiStatus === 'connected' && (
        <div className="bg-red-500/10 border-b border-red-500/20 px-4 py-2 text-xs text-red-900 flex items-center justify-between">
          <div className="max-w-7xl mx-auto w-full flex items-center space-x-2">
            <ShieldAlert className="w-4 h-4 text-red-600 shrink-0" />
            <span>
              <strong>Backend Evaluation Notice:</strong> {recommendationsError}
            </span>
          </div>
        </div>
      )}

      {/* Main Content Layout */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-6 w-full flex-1">
        {/* ========================================================================= */}
        {/* VIEW 0: INTEGRATED APPLICATION HOME PAGE (LANDING HUB) */}
        {/* ========================================================================= */}
        {activeMode === 'home' && (
          <HomePage
            onNavigate={(view) => setActiveMode(view)}
            onOpenIfcModal={() => setIsUploadModalOpen(true)}
            onOpenFloorplanModal={() => setIsFloorplanUploadOpen(true)}
            activeModel={importedModel}
            cityModel={cityModel}
          />
        )}

        {/* ========================================================================= */}
        {/* VIEW 1: CITY-SCALE DISTRICT INFRASTRUCTURE TWIN (3D MULTI-BUILDING) */}
        {/* ========================================================================= */}
        {activeMode === 'city_twin' && (
          <div className="space-y-6">
            <div className="bg-white p-4 rounded-xl border border-charcoal-200 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 bg-sky-50 text-sky-800 rounded-lg border border-sky-200">
                  <Globe className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h2 className="text-sm font-bold text-charcoal-900 tracking-tight">
                      {cityModel?.name || 'TechCity Smart District Masterplan'}
                    </h2>
                    <span className="text-[10px] font-mono bg-stone-100 text-stone-700 px-2 py-0.5 rounded border border-stone-200">
                      WGS84 Coordinates
                    </span>
                  </div>
                  <p className="text-xs text-charcoal-500">
                    City-scale model • {cityModel?.districts?.length || 2} Districts • {cityModel?.districts?.reduce((acc, d) => acc + (d.total_buildings_count || 0), 0) || 8} Multi-Typology Buildings • 3D Infrastructure Networks
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setActiveMode('digital_twin')}
                  className="bg-charcoal-900 hover:bg-black text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors flex items-center space-x-1.5 shadow-2xs cursor-pointer"
                >
                  <Boxes className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Open Active BIM Twin</span>
                </button>
              </div>
            </div>

            <CityViewer
              cityModel={cityModel}
              isLoading={isCityLoading}
              onSelectBuildingForBim={handleSelectBuildingForBim}
            />
          </div>
        )}

        {/* ========================================================================= */}
        {/* VIEW 2: BIM DIGITAL TWIN & ESG MODE */}
        {/* ========================================================================= */}
        {activeMode === 'digital_twin' && (
          <div className="space-y-6">
            {/* Top Twin Action Bar */}
            <div className="bg-white p-4 rounded-xl border border-charcoal-200 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 bg-emerald-50 text-emerald-800 rounded-lg border border-emerald-200">
                  <Boxes className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h2 className="text-sm font-bold text-charcoal-900 tracking-tight">
                      {importedModel?.building_name || importedModel?.project_name || 'Active Digital Twin'}
                    </h2>
                    <span className="text-[10px] font-mono bg-stone-100 text-stone-700 px-2 py-0.5 rounded border border-stone-200">
                      {importedModel?.schema_version || 'IFC4'}
                    </span>
                  </div>
                  <p className="text-xs text-charcoal-500">
                    Source: <span className="font-mono">{importedModel?.source_filename || 'sample_office_building.ifc'}</span> • {importedModel?.total_element_count || 0} Elements
                  </p>
                </div>
              </div>

              {/* View Tabs & Upload Action */}
              <div className="flex items-center space-x-2">
                <div className="flex items-center bg-stone-100 p-1 rounded-lg border border-charcoal-200 text-xs">
                  <button
                    onClick={() => setTwinTab('3d_twin')}
                    className={`px-3 py-1 rounded-md font-semibold transition-all ${
                      twinTab === '3d_twin'
                        ? 'bg-charcoal-900 text-white shadow-2xs'
                        : 'text-charcoal-600 hover:text-charcoal-900'
                    }`}
                  >
                    3D Digital Twin
                  </button>
                  <button
                    onClick={() => setTwinTab('intelligence_dashboard')}
                    className={`px-3 py-1 rounded-md font-semibold transition-all flex items-center space-x-1.5 ${
                      twinTab === 'intelligence_dashboard'
                        ? 'bg-charcoal-900 text-white shadow-2xs'
                        : 'text-charcoal-600 hover:text-charcoal-900'
                    }`}
                  >
                    <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                    <span>Intelligence & Risks</span>
                    {intelligenceReport && intelligenceReport.findings.length > 0 && (
                      <span className="ml-1 text-[10px] bg-rose-600 text-white px-1.5 py-0.2 rounded-full font-bold">
                        {intelligenceReport.findings.length}
                      </span>
                    )}
                  </button>
                  <button
                    onClick={() => setTwinTab('quality_audit')}
                    className={`px-3 py-1 rounded-md font-semibold transition-all flex items-center space-x-1 ${
                      twinTab === 'quality_audit'
                        ? 'bg-charcoal-900 text-white shadow-2xs'
                        : 'text-charcoal-600 hover:text-charcoal-900'
                    }`}
                  >
                    <ShieldCheck className="w-3.5 h-3.5" />
                    <span>Quality Audit</span>
                  </button>
                  <button
                    onClick={() => setTwinTab('esg_assessment')}
                    className={`px-3 py-1 rounded-md font-semibold transition-all flex items-center space-x-1 ${
                      twinTab === 'esg_assessment'
                        ? 'bg-charcoal-900 text-white shadow-2xs'
                        : 'text-charcoal-600 hover:text-charcoal-900'
                    }`}
                  >
                    <Scale className="w-3.5 h-3.5 text-emerald-400" />
                    <span>ESG Screening</span>
                  </button>
                  <button
                    onClick={() => setTwinTab('geolocation_climate')}
                    className={`px-3 py-1 rounded-md font-semibold transition-all flex items-center space-x-1 ${
                      twinTab === 'geolocation_climate'
                        ? 'bg-charcoal-900 text-white shadow-2xs'
                        : 'text-charcoal-600 hover:text-charcoal-900'
                    }`}
                  >
                    <Globe className="w-3.5 h-3.5 text-sky-400" />
                    <span>Geolocation & Climate</span>
                  </button>
                </div>

                <button
                  onClick={() => setIsUploadModalOpen(true)}
                  className="flex items-center space-x-1.5 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors shadow-2xs shrink-0"
                >
                  <Upload className="w-3.5 h-3.5" />
                  <span>Import IFC</span>
                </button>

                <button
                  onClick={() => setIsFloorplanUploadOpen(true)}
                  className="flex items-center space-x-1.5 bg-charcoal-900 hover:bg-charcoal-950 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors shadow-2xs shrink-0"
                >
                  <FileImage className="w-3.5 h-3.5 text-emerald-400" />
                  <span>2D Plan to 3D</span>
                </button>
              </div>
            </div>

            {/* Tab Body: 3D Twin Viewport */}
            {twinTab === '3d_twin' && (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
                {/* 3D Canvas + Filters (8 or 12 Cols depending on element inspection) */}
                <div className={`${selectedElement ? 'lg:col-span-8' : 'lg:col-span-12'} space-y-4`}>
                  {/* Category & Storey Filter Strip */}
                  <div className="bg-white p-3 rounded-xl border border-charcoal-200 text-xs flex flex-wrap items-center justify-between gap-3 shadow-2xs">
                    {/* Storey Selector */}
                    <div className="flex items-center space-x-2">
                      <span className="text-charcoal-500 font-medium flex items-center space-x-1">
                        <Layers className="w-3.5 h-3.5" />
                        <span>Storey:</span>
                      </span>
                      <select
                        value={selectedStoreyId || ''}
                        onChange={(e) => setSelectedStoreyId(e.target.value || null)}
                        className="bg-stone-50 border border-charcoal-200 rounded-lg px-2.5 py-1 text-xs text-charcoal-800 font-medium focus:outline-none focus:ring-1 focus:ring-emerald-500"
                      >
                        <option value="">All Storeys ({importedModel?.storeys.length || 0})</option>
                        {importedModel?.storeys.map((st) => (
                          <option key={st.storey_id} value={st.storey_id}>
                            {st.name} ({st.element_count} elems)
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Category Filter Pills */}
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="text-charcoal-500 font-medium flex items-center space-x-1 mr-1">
                        <Filter className="w-3.5 h-3.5" />
                        <span>Types:</span>
                      </span>
                      {Object.entries(importedModel?.element_counts_by_type || {}).map(([type, count]) => {
                        const isVisible = visibleTypes.includes(type);
                        return (
                          <button
                            key={type}
                            onClick={() => handleToggleElementType(type)}
                            className={`px-2 py-0.5 rounded text-[11px] font-medium border transition-colors ${
                              isVisible
                                ? 'bg-emerald-50 text-emerald-900 border-emerald-300'
                                : 'bg-stone-50 text-stone-400 border-stone-200 line-through'
                            }`}
                          >
                            {type.replace('Ifc', '')} ({count})
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Active Highlight Notification Pill if highlighted */}
                  {highlightedElementIds.length > 0 && (
                    <div className="bg-amber-500/10 border border-amber-300 rounded-lg px-3 py-1.5 text-xs text-amber-900 flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Sparkles className="w-4 h-4 text-amber-600 shrink-0" />
                        <span>
                          <strong>Finding Highlight Active:</strong> {highlightedElementIds.length} element isolated ({highlightSeverity || 'Severity'} severity).
                        </span>
                      </div>
                      <button
                        onClick={() => {
                          setHighlightedElementIds([]);
                          setHighlightSeverity(null);
                          setSelectedElement(null);
                        }}
                        className="text-amber-800 hover:text-amber-950 font-semibold underline text-[11px]"
                      >
                        Clear Highlight
                      </button>
                    </div>
                  )}

                  {/* 3D Canvas */}
                  <BuildingViewer
                    params={params}
                    importedModel={importedModel}
                    selectedElementId={selectedElement?.element_id}
                    highlightedElementIds={highlightedElementIds}
                    highlightSeverity={highlightSeverity}
                    onSelectElement={setSelectedElement}
                    onClearHighlight={() => {
                      setHighlightedElementIds([]);
                      setHighlightSeverity(null);
                    }}
                    visibleTypes={visibleTypes}
                    selectedStoreyId={selectedStoreyId}
                    label="IFC Digital Twin"
                    className="h-[520px]"
                  />
                </div>

                {/* Element Inspector Drawer (4 Cols if element selected) */}
                {selectedElement && (
                  <div className="lg:col-span-4 animate-in slide-in-from-right-3 duration-200">
                    <ElementInspector
                      element={selectedElement}
                      findings={intelligenceReport?.findings || []}
                      onClose={() => setSelectedElement(null)}
                    />
                  </div>
                )}
              </div>
            )}

            {/* Tab Body: Building Intelligence & Risk Analysis */}
            {twinTab === 'intelligence_dashboard' && (
              <IntelligenceDashboardView
                report={intelligenceReport}
                isLoading={isTwinLoading}
                onSelectFinding={(finding) => {
                  setHighlightedElementIds([finding.affected_element_id]);
                  setHighlightSeverity(finding.severity);
                  const elem = importedModel?.elements.find((e) => e.element_id === finding.affected_element_id) || null;
                  setSelectedElement(elem);
                  setTwinTab('3d_twin');
                }}
                onFilterCategory={(cat: string) => {
                  setVisibleTypes([cat]);
                  setTwinTab('3d_twin');
                }}
              />
            )}

            {/* Tab Body: Model Completeness & Quality Report */}
            {twinTab === 'quality_audit' && (
              <QualityReportView
                report={qualityReport}
                isLoading={isTwinLoading}
                onSelectElement={(elemId) => {
                  const elem = importedModel?.elements.find((e) => e.element_id === elemId) || null;
                  setSelectedElement(elem);
                  setTwinTab('3d_twin');
                }}
              />
            )}

            {/* Tab Body: Evidence-Based ESG Screening */}
            {twinTab === 'esg_assessment' && (
              <EsgDashboardView
                report={esgReport}
                annualKwh={annualKwh}
                onKwhChange={setAnnualKwh}
                onRefresh={() => loadDigitalTwinModel(currentModelId)}
                isLoading={isTwinLoading}
              />
            )}

            {/* Tab Body: Geolocation & Environmental Intelligence */}
            {twinTab === 'geolocation_climate' && (
              <EnvironmentalDashboardView modelDetail={importedModel} />
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* VIEW 2: PARAMETRIC DESIGN & BUDGET OPTIMIZER MODE */}
        {/* ========================================================================= */}
        {activeMode === 'parametric' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left Column: Input Form, Toggles & Budget Meter (5 Cols) */}
            <div className="lg:col-span-5 space-y-5">
              {/* Active BIM Baseline Selector Banner */}
              <div className="bg-white p-3.5 rounded-xl border border-charcoal-200 shadow-2xs space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Boxes className="w-4 h-4 text-charcoal-900" />
                    <span className="text-xs font-bold text-charcoal-900">Active BIM Baseline</span>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200">
                    v1.0-baseline
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <select
                    value={currentModelId}
                    onChange={(e) => loadDigitalTwinModel(e.target.value)}
                    className="flex-1 bg-stone-50 border border-charcoal-200 rounded-lg px-2.5 py-1.5 text-xs text-charcoal-800 font-medium focus:outline-none focus:ring-1 focus:ring-charcoal-900"
                  >
                    {availableModels.length > 0 ? (
                      availableModels.map((m) => (
                        <option key={m.model_id} value={m.model_id}>
                          {m.building_name || m.project_name || m.model_id} ({m.source_type.toUpperCase()})
                        </option>
                      ))
                    ) : (
                      <option value={currentModelId}>
                        {importedModel?.building_name || currentModelId}
                      </option>
                    )}
                  </select>
                </div>
                <p className="text-[11px] text-charcoal-500">
                  Parametric Design automatically consumes this BIM model as its geometric baseline. Design edits create proposed alternative scenarios without altering the original BIM model.
                </p>
              </div>

              <BuildingForm
                params={params}
                errors={formErrors}
                onChange={handleParamChange}
                onResetSample={handleResetSample}
              />

              <InterventionToggle
                selectedInterventions={params.selected_interventions}
                onToggle={handleToggleIntervention}
                availableItems={recommendations?.available_interventions}
                budget={params.budget_inr}
              />

              <BudgetSummary
                budget={params.budget_inr}
                totalSelectedCost={totalSelectedCost}
                selectedCount={params.selected_interventions.length}
              />
            </div>

            {/* Right Column: 3D Visualization & Recommendations (7 Cols) */}
            <div className="lg:col-span-7 space-y-5">
              <DesignComparison
                params={params}
                totalCost={totalSelectedCost}
                importedModel={importedModel}
              />

              <RecommendationList
                recommendations={recommendations}
                selectedInterventions={params.selected_interventions}
                onToggleIntervention={handleToggleIntervention}
                onApplyRecommendedBundle={handleApplyRecommendedBundle}
                isLoading={isLoadingRecommendations}
              />
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* VIEW 4: SCENARIO INTELLIGENCE & CLIMATE RESILIENCE (2026-2050) */}
        {/* ========================================================================= */}
        {activeMode === 'scenarios' && (
          <div className="space-y-6">
            <ScenarioIntelligenceView
              buildingId={currentModelId}
            />
          </div>
        )}

        {/* ========================================================================= */}
        {/* VIEW 5: GEOTECHNICAL & SUBSURFACE INTELLIGENCE */}
        {/* ========================================================================= */}
        {activeMode === 'geotechnical' && (
          <div className="space-y-6">
            <GeotechnicalIntelligenceView
              latitude={28.6139}
              longitude={77.2090}
              siteId="site-001"
            />
          </div>
        )}

        {/* ========================================================================= */}
        {/* VIEW 6: ML ENERGY REGRESSION & PARETO OPTIMIZER */}
        {/* ========================================================================= */}
        {activeMode === 'ml_optimizer' && (
          <div className="space-y-6">
            <MLEnergyOptimizerView
              modelId={currentModelId}
              budgetInr={params.budget_inr}
            />
          </div>
        )}

        {/* Concise Assumptions & Limitations Section */}
        <section className="mt-8 bg-white rounded-xl border border-charcoal-200 p-5 shadow-xs">
          <div className="flex items-center space-x-2 mb-3">
            <Scale className="w-4 h-4 text-emerald-800" />
            <h3 className="text-xs font-semibold text-charcoal-900 uppercase tracking-wider">
              Transparent Assumptions, Unit Rates & Limitations
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-charcoal-600">
            <div className="p-3 bg-stone-50 rounded-lg border border-charcoal-100">
              <h4 className="font-semibold text-charcoal-800 mb-1">BIM Tessellation & IFC Ingestion</h4>
              <p className="leading-relaxed text-[11px]">
                IFC geometry is extracted natively using IfcOpenShell. Meshes are converted into client-side triangulated geometries and normalized to metric coordinates. Visual 3D elements do not constitute a structural finite-element engineering model.
              </p>
            </div>
            <div className="p-3 bg-stone-50 rounded-lg border border-charcoal-100">
              <h4 className="font-semibold text-charcoal-800 mb-1">Scientific Emission Factors</h4>
              <p className="leading-relaxed text-[11px]">
                Grid operational emission calculations use the official CEA India Baseline Database Version 19 factor of <strong>0.716 kg CO2e/kWh</strong>. Embodied carbon uses ICE v3 benchmarks only where material volume and specification are confirmed.
              </p>
            </div>
            <div className="p-3 bg-stone-50 rounded-lg border border-charcoal-100">
              <h4 className="font-semibold text-charcoal-800 mb-1">Scope & Governance Limits</h4>
              <p className="leading-relaxed text-[11px]">
                The ESG assessment performs preliminary screening based on available geometry and properties. Final building certifications (LEED, GRIHA) and statutory fire life safety approvals require licensed professional sign-off.
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* IFC Upload Modal */}
      <IfcUploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onImportSuccess={(newModelId) => {
          loadDigitalTwinModel(newModelId);
          setActiveMode('digital_twin');
        }}
        onLoadSample={() => {
          loadDigitalTwinModel('sample-office-twin');
          setActiveMode('digital_twin');
        }}
      />

      {/* 2D Floor Plan Ingestion Modal */}
      <FloorplanUploadModal
        isOpen={isFloorplanUploadOpen}
        onClose={() => setIsFloorplanUploadOpen(false)}
        onExtractionSuccess={(extraction, params) => {
          setFloorplanExtraction(extraction);
          setFloorplanInitialParams(params);
          setIsFloorplanEditorOpen(true);
        }}
      />

      {/* 2D Floor Plan Correction & 3D Extrusion Editor */}
      {floorplanExtraction && (
        <FloorplanCorrectionEditor
          isOpen={isFloorplanEditorOpen}
          onClose={() => {
            setIsFloorplanEditorOpen(false);
            setFloorplanExtraction(null);
          }}
          floorplan={floorplanExtraction.floorplan}
          previewOverlayBase64={floorplanExtraction.preview_overlay_base64}
          summary={floorplanExtraction.summary}
          initialFloors={floorplanInitialParams?.floors || 2}
          initialFloorHeight={floorplanInitialParams?.floorHeight || 3.0}
          initialBuildingType={floorplanInitialParams?.buildingType || 'Commercial'}
          initialRoofType={floorplanInitialParams?.roofType || 'parapet'}
          onGenerateSuccess={(newModelId) => {
            loadDigitalTwinModel(newModelId);
            setActiveMode('digital_twin');
            setTwinTab('3d_twin');
          }}
        />
      )}

      {/* Disclosures Modal */}
      <ImpactModal
        isOpen={isImpactModalOpen}
        onClose={() => setIsImpactModalOpen(false)}
        estimate={estimate}
        annualKwh={annualKwh}
        onKwhChange={setAnnualKwh}
      />

      {/* Footer */}
      <footer className="mt-auto border-t border-charcoal-200 bg-white py-4 text-center text-xs text-charcoal-500">
        <p>InfraTwinAI • AI-Assisted Sustainable Building Design & Infrastructure Planning • Built with React, Three.js & FastAPI</p>
      </footer>
    </div>
  );
};

export default App;
