import React, { useState, useEffect } from 'react';
import {
  Calendar,
  Scale,
  Sparkles,
  Info,
  CheckCircle2,
} from 'lucide-react';
import { ScenarioComparisonReport, DesignScenario } from '../types/scenarios';
import { fetchScenarioComparisonApi } from '../lib/api';
import { formatINR } from '../lib/validation';

interface ScenarioIntelligenceViewProps {
  buildingId: string;
  className?: string;
}

export const ScenarioIntelligenceView: React.FC<ScenarioIntelligenceViewProps> = ({
  buildingId,
  className = '',
}) => {
  const [horizon, setHorizon] = useState<number>(2026);
  const [report, setReport] = useState<ScenarioComparisonReport | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('SCEN-02-ENERGY-OPT');

  useEffect(() => {
    setIsLoading(true);
    fetchScenarioComparisonApi(buildingId, horizon)
      .then((data) => {
        setReport(data);
        setIsLoading(false);
      })
      .catch(() => setIsLoading(false));
  }, [buildingId, horizon]);

  if (isLoading || !report) {
    return (
      <div className={`bg-white rounded-2xl border border-charcoal-200 p-8 flex flex-col items-center justify-center space-y-3 min-h-[350px] ${className}`}>
        <div className="w-8 h-8 border-2 border-charcoal-200 border-t-charcoal-800 rounded-full animate-spin" />
        <p className="text-xs text-charcoal-600 font-medium">Computing multi-scenario lifecycle projections across {horizon}...</p>
      </div>
    );
  }

  const allScenarios: DesignScenario[] = [report.baseline_scenario, ...report.alternative_scenarios];
  const activeScenario = allScenarios.find((s) => s.scenario_id === selectedScenarioId) || report.alternative_scenarios[0];

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Top Header & Horizon Selector */}
      <div className="bg-white p-5 rounded-2xl border border-charcoal-200 shadow-2xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-purple-700" />
            <h2 className="text-base font-bold text-charcoal-900 tracking-tight">
              Future-Oriented Design Intelligence & Scenario Evaluation
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-purple-50 text-purple-800 border border-purple-200 font-semibold">
              IPCC AR6 Calibrated
            </span>
          </div>
          <p className="text-xs text-charcoal-500 mt-0.5">
            Compare lifecycle carbon, operating energy, water consumption, and extreme climate vulnerability.
          </p>
        </div>

        {/* Time Horizon Pills */}
        <div className="flex items-center bg-stone-100 p-1 rounded-xl border border-charcoal-200 text-xs">
          <span className="text-charcoal-500 font-medium px-2 flex items-center space-x-1">
            <Calendar className="w-3.5 h-3.5" />
            <span>Horizon:</span>
          </span>
          {[2026, 2035, 2050].map((year) => (
            <button
              key={year}
              onClick={() => setHorizon(year)}
              className={`px-3 py-1 rounded-lg font-semibold transition-all ${
                horizon === year
                  ? 'bg-charcoal-900 text-white shadow-2xs'
                  : 'text-charcoal-600 hover:text-black'
              }`}
            >
              {year} {year === 2026 ? '(Near)' : year === 2035 ? '(Mid)' : '(Long)'}
            </button>
          ))}
        </div>
      </div>

      {/* Scenario Cards Strip */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {allScenarios.map((scen) => {
          const isSelected = scen.scenario_id === selectedScenarioId;
          const isBaseline = scen.scenario_id === report.baseline_scenario.scenario_id;

          return (
            <button
              key={scen.scenario_id}
              onClick={() => setSelectedScenarioId(scen.scenario_id)}
              className={`text-left p-4 rounded-xl border transition-all flex flex-col justify-between space-y-3 ${
                isSelected
                  ? 'bg-charcoal-950 text-white border-charcoal-950 shadow-md ring-2 ring-charcoal-800/40'
                  : 'bg-white text-charcoal-900 border-charcoal-200 hover:border-charcoal-400 shadow-2xs'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded ${
                    isBaseline
                      ? isSelected ? 'bg-charcoal-800 text-stone-200' : 'bg-stone-100 text-charcoal-600'
                      : isSelected ? 'bg-emerald-950 text-emerald-300' : 'bg-emerald-50 text-emerald-800'
                  }`}>
                    {isBaseline ? 'BASELINE' : 'PROPOSED'}
                  </span>
                  <span className={`text-[10px] font-bold ${
                    scen.resilience_rating.startsWith('A')
                      ? 'text-emerald-500'
                      : scen.resilience_rating.startsWith('B')
                      ? 'text-sky-500'
                      : 'text-amber-500'
                  }`}>
                    {scen.resilience_rating.split(' - ')[0]}
                  </span>
                </div>
                <h4 className="text-xs font-bold leading-snug">
                  {scen.name}
                </h4>
              </div>

              <div className="space-y-1 text-[11px] pt-2 border-t border-charcoal-200/20 font-mono">
                <div className="flex justify-between">
                  <span className={isSelected ? 'text-charcoal-400' : 'text-charcoal-500'}>Energy:</span>
                  <span className="font-bold">{scen.operational_energy_kwh_m2_yr.value} kWh/m²</span>
                </div>
                <div className="flex justify-between">
                  <span className={isSelected ? 'text-charcoal-400' : 'text-charcoal-500'}>Carbon:</span>
                  <span className="font-bold">{scen.embodied_carbon_kg_co2e_m2.value} kg/m²</span>
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Selected Scenario Deep-Dive Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Scenario Metrics Details (8 Cols) */}
        <div className="lg:col-span-8 bg-white rounded-2xl border border-charcoal-200 p-6 shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-charcoal-100">
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-base font-bold text-charcoal-900 tracking-tight">
                  {activeScenario.name}
                </h3>
                <span className="text-xs font-semibold px-2 py-0.5 rounded bg-stone-100 text-charcoal-700 border border-charcoal-200">
                  Resilience: {activeScenario.resilience_rating}
                </span>
              </div>
              <p className="text-xs text-charcoal-600 mt-1 leading-relaxed">
                {activeScenario.description}
              </p>
            </div>
            {activeScenario.scenario_id !== report.baseline_scenario.scenario_id && (
              <span className="text-xs font-mono font-bold px-3 py-1 rounded bg-emerald-50 text-emerald-900 border border-emerald-200 shrink-0">
                Cost: {formatINR(activeScenario.capital_cost_inr.value)}
              </span>
            )}
          </div>

          {/* 6 Key Performance Indicators (KPIs) with Provenance */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            {/* Operational Energy */}
            <div className="p-3.5 bg-stone-50 rounded-xl border border-charcoal-200/80 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-charcoal-500 font-semibold uppercase tracking-wider">Operational Energy</span>
                <span className="text-[9px] font-mono font-bold px-1 rounded bg-blue-100 text-blue-800">
                  {activeScenario.operational_energy_kwh_m2_yr.provenance_type}
                </span>
              </div>
              <div className="text-lg font-bold font-mono text-charcoal-900">
                {activeScenario.operational_energy_kwh_m2_yr.value} {activeScenario.operational_energy_kwh_m2_yr.unit}
              </div>
              <p className="text-[10px] text-charcoal-500">
                {activeScenario.operational_energy_kwh_m2_yr.source_notes}
              </p>
            </div>

            {/* Embodied Carbon */}
            <div className="p-3.5 bg-stone-50 rounded-xl border border-charcoal-200/80 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-charcoal-500 font-semibold uppercase tracking-wider">Embodied Carbon</span>
                <span className="text-[9px] font-mono font-bold px-1 rounded bg-amber-100 text-amber-800">
                  {activeScenario.embodied_carbon_kg_co2e_m2.provenance_type}
                </span>
              </div>
              <div className="text-lg font-bold font-mono text-charcoal-900">
                {activeScenario.embodied_carbon_kg_co2e_m2.value} {activeScenario.embodied_carbon_kg_co2e_m2.unit}
              </div>
              <p className="text-[10px] text-charcoal-500">
                {activeScenario.embodied_carbon_kg_co2e_m2.source_notes}
              </p>
            </div>

            {/* Water Demand */}
            <div className="p-3.5 bg-stone-50 rounded-xl border border-charcoal-200/80 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-charcoal-500 font-semibold uppercase tracking-wider">Water Consumption</span>
                <span className="text-[9px] font-mono font-bold px-1 rounded bg-sky-100 text-sky-800">
                  {activeScenario.annual_water_demand_kl.provenance_type}
                </span>
              </div>
              <div className="text-lg font-bold font-mono text-charcoal-900">
                {activeScenario.annual_water_demand_kl.value} {activeScenario.annual_water_demand_kl.unit}
              </div>
              <p className="text-[10px] text-charcoal-500">
                Recycled on-site: {activeScenario.annual_water_recycled_kl.value} kL/yr
              </p>
            </div>

            {/* Annual Operating Cost */}
            <div className="p-3.5 bg-stone-50 rounded-xl border border-charcoal-200/80 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-charcoal-500 font-semibold uppercase tracking-wider">Annual Electricity</span>
                <span className="text-[9px] font-mono font-bold px-1 rounded bg-blue-100 text-blue-800">
                  {activeScenario.annual_operating_cost_inr.provenance_type}
                </span>
              </div>
              <div className="text-lg font-bold font-mono text-charcoal-900">
                {formatINR(activeScenario.annual_operating_cost_inr.value)}
              </div>
              <p className="text-[10px] text-charcoal-500">
                Commercial grid tariff assumption @ ₹8.50/kWh
              </p>
            </div>

            {/* Climate Vulnerability Score */}
            <div className="p-3.5 bg-stone-50 rounded-xl border border-charcoal-200/80 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-charcoal-500 font-semibold uppercase tracking-wider">Climate Hazard Risk</span>
                <span className="text-[9px] font-mono font-bold px-1 rounded bg-purple-100 text-purple-800">
                  {activeScenario.climate_vulnerability_score.provenance_type}
                </span>
              </div>
              <div className="text-lg font-bold font-mono text-charcoal-900">
                {activeScenario.climate_vulnerability_score.value} / 100
              </div>
              <p className="text-[10px] text-charcoal-500">
                Thermal heatwave & precipitation stress index
              </p>
            </div>

            {/* Capital Cost */}
            <div className="p-3.5 bg-stone-50 rounded-xl border border-charcoal-200/80 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-charcoal-500 font-semibold uppercase tracking-wider">Upfront Capital</span>
                <span className="text-[9px] font-mono font-bold px-1 rounded bg-stone-200 text-charcoal-800">
                  {activeScenario.capital_cost_inr.provenance_type}
                </span>
              </div>
              <div className="text-lg font-bold font-mono text-charcoal-900">
                {formatINR(activeScenario.capital_cost_inr.value)}
              </div>
              <p className="text-[10px] text-charcoal-500">
                {activeScenario.applied_interventions.length} packages included
              </p>
            </div>
          </div>

          {/* Applied Interventions List */}
          {activeScenario.applied_interventions.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-charcoal-800 uppercase tracking-wider">
                Integrated Engineering Interventions
              </h4>
              <div className="flex flex-wrap gap-2">
                {activeScenario.applied_interventions.map((item, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center space-x-1.5 text-xs font-semibold px-3 py-1 rounded-lg bg-emerald-50 text-emerald-900 border border-emerald-200"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    <span>{item}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Limitations & Provenance Notice */}
          <div className="p-3 bg-stone-50 rounded-xl border border-charcoal-100 text-xs text-charcoal-500 space-y-1">
            <span className="font-semibold text-charcoal-700">Methodology & Limitations: </span>
            <span>{activeScenario.methodology_limitations}</span>
          </div>
        </div>

        {/* Right Side: Comparative Summary & Scientific Disclosures (4 Cols) */}
        <div className="lg:col-span-4 space-y-4">
          <div className="bg-white rounded-2xl border border-charcoal-200 p-5 shadow-xs space-y-4">
            <div className="flex items-center space-x-2">
              <Scale className="w-4 h-4 text-emerald-800" />
              <h3 className="text-sm font-bold text-charcoal-900 tracking-tight">
                Horizon {horizon} Decarbonization Trajectory
              </h3>
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between items-center py-2 border-b border-charcoal-100">
                <span className="text-charcoal-600">Peak Energy Reduction:</span>
                <span className="font-bold font-mono text-emerald-700">
                  -{report.comparative_summary.max_energy_reduction_pct}%
                </span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-charcoal-100">
                <span className="text-charcoal-600">Max Embodied Carbon Cut:</span>
                <span className="font-bold font-mono text-emerald-700">
                  -{report.comparative_summary.max_carbon_reduction_pct}%
                </span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-charcoal-100">
                <span className="text-charcoal-600">Max Water Conservation:</span>
                <span className="font-bold font-mono text-sky-700">
                  -{report.comparative_summary.max_water_savings_pct}%
                </span>
              </div>
              <div className="flex justify-between items-center py-2 border-b border-charcoal-100">
                <span className="text-charcoal-600">Grid Carbon Factor:</span>
                <span className="font-mono text-charcoal-800 font-semibold">
                  {report.comparative_summary.grid_emission_factor_used}
                </span>
              </div>
            </div>

            <div className="p-3 bg-stone-50 rounded-xl border border-charcoal-200/80 text-[11px] text-charcoal-500 leading-relaxed">
              <div className="font-bold text-charcoal-700 mb-1 flex items-center space-x-1">
                <Info className="w-3.5 h-3.5 text-blue-600" />
                <span>Honest Science Notice</span>
              </div>
              {report.scientific_disclaimer}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
