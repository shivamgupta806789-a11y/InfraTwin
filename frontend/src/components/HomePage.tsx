import React from 'react';
import {
  Boxes,
  FileImage,
  Upload,
  Globe,
  Award,
  ArrowRight,
  TrendingDown,
  ShieldCheck,
  Zap,
  MapPin,
  Calendar,
  Compass,
  Droplets,
} from 'lucide-react';
import { CityModel } from '../types/city';
import { BuildingModelDetail } from '../types/digital_twin';

interface HomePageProps {
  onNavigate: (view: 'home' | 'city_twin' | 'digital_twin' | 'parametric' | 'geolocation_climate' | 'scenarios') => void;
  onOpenIfcModal: () => void;
  onOpenFloorplanModal: () => void;
  activeModel?: BuildingModelDetail | null;
  cityModel?: CityModel | null;
}

export const HomePage: React.FC<HomePageProps> = ({
  onNavigate,
  onOpenIfcModal,
  onOpenFloorplanModal,
  activeModel,
  cityModel,
}) => {
  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Hero Welcome Banner */}
      <section className="bg-white rounded-2xl border border-charcoal-200 p-6 sm:p-8 shadow-xs">
        <div className="max-w-4xl space-y-4">
          <div className="inline-flex items-center space-x-2 bg-stone-100 text-charcoal-800 px-3 py-1 rounded-full text-xs font-semibold border border-charcoal-200">
            <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse" />
            <span>InfraTwinAI Platform v2.0 • Geospatially Aware Urban Digital Twins</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-charcoal-900 tracking-tight leading-tight">
            Integrated Digital Twin, Geointelligence & Sustainable Infrastructure Platform
          </h1>
          <p className="text-sm sm:text-base text-charcoal-600 leading-relaxed max-w-3xl">
            Unify Building Information Modeling (BIM), city-scale multi-building masterplans, 
            3D geotechnical subsurface stratigraphy, and machine-learning energy optimization 
            into a single continuous engineering workflow.
          </p>

          {/* Core Quick Action Buttons */}
          <div className="flex flex-wrap items-center gap-3 pt-2">
            <button
              onClick={() => onNavigate('digital_twin')}
              className="bg-charcoal-900 hover:bg-black text-white text-xs sm:text-sm font-semibold px-4 py-2.5 rounded-xl transition-all shadow-xs flex items-center space-x-2"
            >
              <Boxes className="w-4 h-4 text-emerald-400" />
              <span>Open Active Digital Twin</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>

            <button
              onClick={() => onNavigate('city_twin')}
              className="bg-white hover:bg-stone-50 text-charcoal-800 text-xs sm:text-sm font-semibold px-4 py-2.5 rounded-xl border border-charcoal-300 transition-all shadow-2xs flex items-center space-x-2"
            >
              <Globe className="w-4 h-4 text-sky-600" />
              <span>Explore City-Scale District</span>
            </button>

            <button
              onClick={onOpenIfcModal}
              className="bg-white hover:bg-stone-50 text-charcoal-800 text-xs sm:text-sm font-semibold px-4 py-2.5 rounded-xl border border-charcoal-300 transition-all shadow-2xs flex items-center space-x-2"
            >
              <Upload className="w-4 h-4 text-charcoal-700" />
              <span>Import IFC Model</span>
            </button>

            <button
              onClick={onOpenFloorplanModal}
              className="bg-white hover:bg-stone-50 text-charcoal-800 text-xs sm:text-sm font-semibold px-4 py-2.5 rounded-xl border border-charcoal-300 transition-all shadow-2xs flex items-center space-x-2"
            >
              <FileImage className="w-4 h-4 text-emerald-700" />
              <span>2D Drawing to 3D</span>
            </button>
          </div>
        </div>
      </section>

      {/* Platform Key Metrics Strip */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-charcoal-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-charcoal-500 text-xs font-medium">
            <span>Operational Carbon Delta</span>
            <TrendingDown className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-xl font-bold font-mono text-charcoal-900">-42.5%</div>
          <div className="text-[11px] text-emerald-700 font-medium">CEA India Grid baseline v19 offset</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-charcoal-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-charcoal-500 text-xs font-medium">
            <span>Renewable Solar Fraction</span>
            <Zap className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-xl font-bold font-mono text-charcoal-900">54.8%</div>
          <div className="text-[11px] text-charcoal-500">Rooftop Monocrystalline PERC</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-charcoal-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-charcoal-500 text-xs font-medium">
            <span>Subsurface Stratigraphy</span>
            <Compass className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-xl font-bold font-mono text-charcoal-900">4 Strata Layers</div>
          <div className="text-[11px] text-charcoal-500">3 Core Boreholes active</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-charcoal-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-charcoal-500 text-xs font-medium">
            <span>IFC Model Quality</span>
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-xl font-bold font-mono text-charcoal-900">98.4%</div>
          <div className="text-[11px] text-emerald-700 font-medium">Zero geometric coordinate collisions</div>
        </div>
      </section>

      {/* Main Content Grid: Recent Digital Twin Projects & Live Intelligence Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Recent Projects (8 Cols) */}
        <section className="lg:col-span-8 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-charcoal-900 tracking-tight">
                Digital Twin Projects & Masterplans
              </h2>
              <p className="text-xs text-charcoal-500">
                Active building models, multi-building campuses, and site plans available in this session.
              </p>
            </div>
            <span className="text-xs font-mono bg-stone-100 text-charcoal-700 px-2 py-0.5 rounded border border-charcoal-200">
              4 Models Ready
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Project Card 1: NetZero Center */}
            <div
              onClick={() => onNavigate('digital_twin')}
              className="bg-white rounded-xl border border-charcoal-200 hover:border-charcoal-400 p-5 transition-all shadow-2xs hover:shadow-xs cursor-pointer group flex flex-col justify-between space-y-4"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 px-2 py-0.5 rounded">
                    ACTIVE BIM MODEL
                  </span>
                  <span className="text-xs text-charcoal-400 flex items-center space-x-1">
                    <Calendar className="w-3 h-3" />
                    <span>IFC4 Native</span>
                  </span>
                </div>
                <h3 className="text-sm font-bold text-charcoal-900 group-hover:text-black tracking-tight">
                  {activeModel?.building_name || 'NetZero Innovation Center'}
                </h3>
                <p className="text-xs text-charcoal-600 leading-relaxed">
                  2-storey commercial office facility with detailed triangulated structural walls, slabs, columns,
                  and low-E fenestration.
                </p>
              </div>

              <div className="pt-2 border-t border-charcoal-100 flex items-center justify-between text-xs">
                <div className="flex items-center space-x-3 text-charcoal-500 font-mono text-[11px]">
                  <span>{activeModel?.storeys.length || 2} Storeys</span>
                  <span>•</span>
                  <span>{activeModel?.total_element_count || 21} Elements</span>
                </div>
                <span className="text-charcoal-900 font-semibold group-hover:translate-x-1 transition-transform flex items-center space-x-1">
                  <span>Open BIM</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </div>

            {/* Project Card 2: TechCity District */}
            <div
              onClick={() => onNavigate('city_twin')}
              className="bg-white rounded-xl border border-charcoal-200 hover:border-charcoal-400 p-5 transition-all shadow-2xs hover:shadow-xs cursor-pointer group flex flex-col justify-between space-y-4"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold bg-sky-50 text-sky-800 border border-sky-200 px-2 py-0.5 rounded">
                    CITY-SCALE DISTRICT
                  </span>
                  <span className="text-xs text-charcoal-400 flex items-center space-x-1">
                    <MapPin className="w-3 h-3" />
                    <span>28.61°N, 77.20°E</span>
                  </span>
                </div>
                <h3 className="text-sm font-bold text-charcoal-900 group-hover:text-black tracking-tight">
                  {cityModel?.name || 'TechCity Smart Innovation District'}
                </h3>
                <p className="text-xs text-charcoal-600 leading-relaxed">
                  Hierarchical urban district encompassing 8 buildings, 4 sites, primary road spine,
                  and subsurface 11kV microgrid rings.
                </p>
              </div>

              <div className="pt-2 border-t border-charcoal-100 flex items-center justify-between text-xs">
                <div className="flex items-center space-x-3 text-charcoal-500 font-mono text-[11px]">
                  <span>8 Buildings</span>
                  <span>•</span>
                  <span>3.38 Hectares</span>
                </div>
                <span className="text-charcoal-900 font-semibold group-hover:translate-x-1 transition-transform flex items-center space-x-1">
                  <span>View City</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </div>

            {/* Project Card 3: Parametric Optimization */}
            <div
              onClick={() => onNavigate('parametric')}
              className="bg-white rounded-xl border border-charcoal-200 hover:border-charcoal-400 p-5 transition-all shadow-2xs hover:shadow-xs cursor-pointer group flex flex-col justify-between space-y-4"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold bg-amber-50 text-amber-800 border border-amber-200 px-2 py-0.5 rounded">
                    BUDGET & ENERGY OPTIMIZER
                  </span>
                  <span className="text-xs text-charcoal-400">Parametric v1.0</span>
                </div>
                <h3 className="text-sm font-bold text-charcoal-900 group-hover:text-black tracking-tight">
                  Parametric Design Alternatives & Comparison
                </h3>
                <p className="text-xs text-charcoal-600 leading-relaxed">
                  Consume active BIM geometry as baseline, alter envelope parameters, test green interventions,
                  and compare cost vs ROI side-by-side.
                </p>
              </div>

              <div className="pt-2 border-t border-charcoal-100 flex items-center justify-between text-xs">
                <div className="flex items-center space-x-3 text-charcoal-500 font-mono text-[11px]">
                  <span>Baseline v1.0</span>
                  <span>•</span>
                  <span>Pareto Active</span>
                </div>
                <span className="text-charcoal-900 font-semibold group-hover:translate-x-1 transition-transform flex items-center space-x-1">
                  <span>Optimize</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </div>

            {/* Project Card 4: Future Scenario Analysis */}
            <div
              onClick={() => onNavigate('scenarios')}
              className="bg-white rounded-xl border border-charcoal-200 hover:border-charcoal-400 p-5 transition-all shadow-2xs hover:shadow-xs cursor-pointer group flex flex-col justify-between space-y-4"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold bg-purple-50 text-purple-800 border border-purple-200 px-2 py-0.5 rounded">
                    SCENARIOS 2026-2050
                  </span>
                  <span className="text-xs text-charcoal-400">IPCC Sensitivity</span>
                </div>
                <h3 className="text-sm font-bold text-charcoal-900 group-hover:text-black tracking-tight">
                  Multi-Scenario Lifecycle & Climate Projections
                </h3>
                <p className="text-xs text-charcoal-600 leading-relaxed">
                  Project building performance across 2026, 2035, and 2050 under Low-Carbon, Water-Resilient,
                  and Climate Extreme scenarios.
                </p>
              </div>

              <div className="pt-2 border-t border-charcoal-100 flex items-center justify-between text-xs">
                <div className="flex items-center space-x-3 text-charcoal-500 font-mono text-[11px]">
                  <span>5 Scenarios</span>
                  <span>•</span>
                  <span>3 Horizons</span>
                </div>
                <span className="text-charcoal-900 font-semibold group-hover:translate-x-1 transition-transform flex items-center space-x-1">
                  <span>Explore Scenarios</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* Right Column: Sustainability Insights & Intelligence Feeds (4 Cols) */}
        <section className="lg:col-span-4 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-charcoal-900 tracking-tight flex items-center space-x-1.5">
              <Award className="w-4 h-4 text-emerald-800" />
              <span>Sustainability Intelligence</span>
            </h2>
            <button
              onClick={() => onNavigate('digital_twin')}
              className="text-xs text-charcoal-600 hover:text-charcoal-900 font-semibold"
            >
              View All
            </button>
          </div>

          <div className="bg-white rounded-xl border border-charcoal-200 p-4 shadow-2xs space-y-3.5">
            {/* Insight 1 */}
            <div className="p-3 bg-stone-50 rounded-lg border border-charcoal-200/80 space-y-1">
              <div className="flex items-center justify-between text-[11px]">
                <span className="font-semibold text-emerald-800">A. Environmental Sustainability</span>
                <span className="text-charcoal-400 font-mono">REC-ENV-001</span>
              </div>
              <h4 className="text-xs font-bold text-charcoal-900">
                Rooftop Solar PV (29.6 kWp Array)
              </h4>
              <p className="text-[11px] text-charcoal-600 leading-relaxed">
                4.85 kWh/m²/day GHI solar insolation offsets ~30.7 t CO₂e annually.
              </p>
            </div>

            {/* Insight 2 */}
            <div className="p-3 bg-stone-50 rounded-lg border border-charcoal-200/80 space-y-1">
              <div className="flex items-center justify-between text-[11px]">
                <span className="font-semibold text-amber-800">B. Geotechnical Suitability</span>
                <span className="text-charcoal-400 font-mono">REC-GEO-003</span>
              </div>
              <h4 className="text-xs font-bold text-charcoal-900">
                Hydrostatic Uplift & Raft Barrier
              </h4>
              <p className="text-[11px] text-charcoal-600 leading-relaxed">
                Measured water table sits at 4.2m below finished ground in Core Borehole #BH-01.
              </p>
            </div>

            {/* Insight 3 */}
            <div className="p-3 bg-stone-50 rounded-lg border border-charcoal-200/80 space-y-1">
              <div className="flex items-center justify-between text-[11px]">
                <span className="font-semibold text-sky-800">C. Infrastructure Resilience</span>
                <span className="text-charcoal-400 font-mono">REC-RES-005</span>
              </div>
              <h4 className="text-xs font-bold text-charcoal-900">
                District SuDS Retention Vault (450 m³)
              </h4>
              <p className="text-[11px] text-charcoal-600 leading-relaxed">
                Absorbs 50-year peak monsoon cloudburst volume without stormwater backflow.
              </p>
            </div>

            {/* Rainwater 3D shortcut button */}
            <button
              onClick={() => onNavigate('geolocation_climate')}
              className="w-full bg-sky-50 hover:bg-sky-100 text-sky-900 font-semibold text-xs py-2 rounded-lg transition-colors border border-sky-200 flex items-center justify-center space-x-1.5 cursor-pointer shadow-2xs"
            >
              <Droplets className="w-3.5 h-3.5 text-sky-600" />
              <span>Launch 3D Rainwater & Stormwater Engine</span>
            </button>

            {/* Subsurface shortcut button */}
            <button
              onClick={() => onNavigate('geolocation_climate')}
              className="w-full bg-stone-100 hover:bg-stone-200 text-charcoal-800 font-semibold text-xs py-2 rounded-lg transition-colors border border-charcoal-200 flex items-center justify-center space-x-1.5"
            >
              <Compass className="w-3.5 h-3.5 text-blue-600" />
              <span>Inspect Subsurface Boreholes & Soil Strata</span>
            </button>
          </div>
        </section>
      </div>
    </div>
  );
};
