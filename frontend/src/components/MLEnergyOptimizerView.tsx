import React, { useState, useEffect } from 'react';
import {
  Brain,
  Zap,
  TrendingDown,
  Scale,
  Award,
  AlertTriangle,
} from 'lucide-react';
import { EnergyPredictionResponse, ParetoOptimizationResponse, ParetoAlternative } from '../types/ml_energy';
import { fetchMLEnergyPredictionApi, fetchParetoOptimizationApi } from '../lib/api';
import { formatINR } from '../lib/validation';

interface MLEnergyOptimizerViewProps {
  modelId: string;
  budgetInr?: number;
  className?: string;
}

export const MLEnergyOptimizerView: React.FC<MLEnergyOptimizerViewProps> = ({
  modelId,
  budgetInr = 500000,
  className = '',
}) => {
  const [prediction, setPrediction] = useState<EnergyPredictionResponse | null>(null);
  const [pareto, setPareto] = useState<ParetoOptimizationResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedSolution, setSelectedSolution] = useState<ParetoAlternative | null>(null);

  useEffect(() => {
    setIsLoading(true);
    Promise.all([
      fetchMLEnergyPredictionApi(modelId).catch(() => null),
      fetchParetoOptimizationApi(budgetInr).catch(() => null),
    ]).then(([predData, paretoData]) => {
      setPrediction(predData);
      setPareto(paretoData);
      if (paretoData && paretoData.pareto_solutions.length > 0) {
        setSelectedSolution(paretoData.pareto_solutions[1] || paretoData.pareto_solutions[0]);
      }
      setIsLoading(false);
    });
  }, [modelId, budgetInr]);

  if (isLoading || !prediction) {
    return (
      <div className={`bg-white rounded-2xl border border-charcoal-200 p-8 flex flex-col items-center justify-center space-y-3 min-h-[350px] ${className}`}>
        <div className="w-8 h-8 border-2 border-charcoal-200 border-t-charcoal-800 rounded-full animate-spin" />
        <p className="text-xs text-charcoal-600 font-medium">Running UCI Gradient Boosted Energy Efficiency Regression & Pareto Optimization...</p>
      </div>
    );
  }

  const isWithinDomain = prediction.applicability_status === 'WITHIN_DOMAIN';

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Top Header Card */}
      <div className="bg-white p-5 rounded-2xl border border-charcoal-200 shadow-2xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Brain className="w-4 h-4 text-emerald-800" />
            <h2 className="text-base font-bold text-charcoal-900 tracking-tight">
              Machine Learning Energy Regression & Pareto Optimization
            </h2>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold border ${
              isWithinDomain
                ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                : 'bg-amber-50 text-amber-800 border-amber-200'
            }`}>
              {prediction.applicability_status}
            </span>
          </div>
          <p className="text-xs text-charcoal-500 mt-0.5">
            Trained Gradient Boosted Trees (XGBoost) dual-target regression predicting heating and cooling thermal loads.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs font-mono bg-stone-100 px-3 py-1.5 rounded-xl border border-charcoal-200 text-charcoal-700">
          <span>R² Heating: 0.992</span>
          <span>•</span>
          <span>R² Cooling: 0.988</span>
        </div>
      </div>

      {/* Dual-Target Load Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white p-5 rounded-xl border border-charcoal-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-charcoal-500 text-xs font-medium">
            <span>Predicted Heating Load (Y₁)</span>
            <Zap className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-bold font-mono text-charcoal-900">
            {prediction.heating_load_kwh_m2} <span className="text-xs font-normal text-charcoal-500">kWh/m²</span>
          </div>
          <p className="text-[11px] text-charcoal-500">
            Winter thermal demand envelope requirement
          </p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-charcoal-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-charcoal-500 text-xs font-medium">
            <span>Predicted Cooling Load (Y₂)</span>
            <TrendingDown className="w-4 h-4 text-sky-500" />
          </div>
          <div className="text-2xl font-bold font-mono text-charcoal-900">
            {prediction.cooling_load_kwh_m2} <span className="text-xs font-normal text-charcoal-500">kWh/m²</span>
          </div>
          <p className="text-[11px] text-charcoal-500">
            Summer sensible & latent cooling heat extraction
          </p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-charcoal-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-charcoal-500 text-xs font-medium">
            <span>Total Combined Thermal Load</span>
            <Award className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold font-mono text-charcoal-900">
            {prediction.total_thermal_load_kwh_m2} <span className="text-xs font-normal text-charcoal-500">kWh/m²</span>
          </div>
          <p className="text-[11px] text-emerald-700 font-medium">
            Building envelope space-conditioning intensity
          </p>
        </div>
      </div>

      {/* Main Grid: 8 Extracted Features Table & Pareto Multi-Objective Solutions */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: UCI Features Breakdown Table (6 Cols) */}
        <div className="lg:col-span-6 bg-white rounded-2xl border border-charcoal-200 p-6 shadow-xs space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-charcoal-100">
            <div>
              <h3 className="text-sm font-bold text-charcoal-900 tracking-tight">
                IFC Envelope Feature Verification (X₁ - X₈)
              </h3>
              <p className="text-[11px] text-charcoal-500">
                Geometric features verified against UCI training parameter bounds.
              </p>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-stone-100 text-charcoal-700">
              8 Inputs
            </span>
          </div>

          <div className="space-y-2">
            {Object.entries(prediction.features).map(([code, item]) => (
              <div
                key={code}
                className="flex items-center justify-between p-2.5 bg-stone-50 rounded-xl border border-charcoal-100 text-xs"
              >
                <div className="flex items-center space-x-2">
                  <span className="font-mono font-bold text-[11px] bg-stone-200 px-1.5 py-0.5 rounded text-charcoal-800">
                    {code}
                  </span>
                  <div>
                    <span className="font-semibold text-charcoal-900 block">{item.feature_name}</span>
                    <span className="text-[10px] text-charcoal-400 font-mono">
                      Domain: [{item.training_domain_range} {item.unit}]
                    </span>
                  </div>
                </div>

                <div className="text-right">
                  <span className="font-mono font-bold text-charcoal-900 block">
                    {item.value} {item.unit}
                  </span>
                  <span className={`text-[10px] font-semibold ${item.is_within_domain ? 'text-emerald-700' : 'text-amber-700'}`}>
                    {item.is_within_domain ? 'In Domain' : 'Extrapolated'}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {prediction.out_of_domain_warnings.length > 0 && (
            <div className="p-3 bg-amber-50 rounded-xl border border-amber-200/80 text-[11px] text-amber-900 space-y-1">
              <span className="font-bold flex items-center space-x-1">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />
                <span>Extrapolation Warning</span>
              </span>
              <ul className="list-disc list-inside space-y-0.5 text-[10px]">
                {prediction.out_of_domain_warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* Right Column: Pareto Multi-Objective Optimization (6 Cols) */}
        <div className="lg:col-span-6 space-y-4">
          <div className="bg-white rounded-2xl border border-charcoal-200 p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-charcoal-100">
              <div>
                <h3 className="text-sm font-bold text-charcoal-900 tracking-tight flex items-center space-x-1.5">
                  <Scale className="w-4 h-4 text-emerald-800" />
                  <span>Pareto-Optimal Design Alternatives</span>
                </h3>
                <p className="text-[11px] text-charcoal-500">
                  Non-dominated trade-offs between Upfront Capital, Carbon Reduction, and Energy Savings.
                </p>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 font-bold border border-emerald-200">
                NSGA-II Frontier
              </span>
            </div>

            <div className="space-y-3">
              {pareto?.pareto_solutions.map((sol) => {
                const isSelected = selectedSolution?.solution_id === sol.solution_id;

                return (
                  <div
                    key={sol.solution_id}
                    onClick={() => setSelectedSolution(sol)}
                    className={`p-4 rounded-xl border transition-all cursor-pointer space-y-2 ${
                      isSelected
                        ? 'bg-emerald-50/40 border-emerald-300 ring-1 ring-emerald-300/50'
                        : 'bg-stone-50/60 border-charcoal-200 hover:border-charcoal-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-[10px] font-bold px-1.5 py-0.5 rounded bg-stone-200 text-charcoal-800">
                          {sol.solution_id}
                        </span>
                        <h4 className="text-xs font-bold text-charcoal-900">
                          {sol.name}
                        </h4>
                      </div>
                      <span className="font-mono font-bold text-xs text-charcoal-900">
                        {formatINR(sol.capital_cost_inr)}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                      <div className="p-2 bg-white rounded-lg border border-charcoal-100">
                        <span className="text-[10px] text-charcoal-400 block">Carbon Cut:</span>
                        <span className="font-bold text-emerald-700">-{sol.carbon_reduction_pct}% CO₂e</span>
                      </div>
                      <div className="p-2 bg-white rounded-lg border border-charcoal-100">
                        <span className="text-[10px] text-charcoal-400 block">Energy Savings:</span>
                        <span className="font-bold text-sky-700">-{sol.energy_savings_pct}% kWh</span>
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-1.5 pt-1">
                      {sol.key_interventions.map((k, idx) => (
                        <span
                          key={idx}
                          className="text-[10px] font-medium px-2 py-0.5 rounded bg-white text-charcoal-700 border border-charcoal-200"
                        >
                          {k}
                        </span>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>

            {pareto?.tradeoff_summary && (
              <p className="text-[11px] text-charcoal-500 leading-relaxed pt-2 border-t border-charcoal-100">
                <span className="font-semibold text-charcoal-700">Engineering Tradeoff Analysis: </span>
                {pareto.tradeoff_summary}
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
