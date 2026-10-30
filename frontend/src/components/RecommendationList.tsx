import React from 'react';
import { RecommendationResponse } from '../types/recommendations';
import { InterventionId } from '../types/building';
import { formatINR } from '../lib/validation';
import { Award, Check, Plus, AlertCircle, Info, Sparkles } from 'lucide-react';

interface RecommendationListProps {
  recommendations: RecommendationResponse | null;
  selectedInterventions: InterventionId[];
  onToggleIntervention: (id: InterventionId) => void;
  onApplyRecommendedBundle: () => void;
  isLoading: boolean;
  className?: string;
}

export const RecommendationList: React.FC<RecommendationListProps> = ({
  recommendations,
  selectedInterventions,
  onToggleIntervention,
  onApplyRecommendedBundle,
  isLoading,
  className = '',
}) => {
  if (isLoading) {
    return (
      <div className={`bg-white rounded-xl border border-charcoal-200 p-6 shadow-xs flex flex-col items-center justify-center space-y-3 min-h-[260px] ${className}`}>
        <div className="w-8 h-8 border-2 border-charcoal-200 border-t-charcoal-800 rounded-full animate-spin" />
        <p className="text-xs text-charcoal-600 font-medium">Evaluating budget feasibility & ranking recommendations...</p>
      </div>
    );
  }

  if (!recommendations) {
    return (
      <div className={`bg-white rounded-xl border border-charcoal-200 p-6 shadow-xs text-center min-h-[200px] flex flex-col items-center justify-center ${className}`}>
        <Info className="w-8 h-8 text-charcoal-400 mb-2" />
        <h3 className="text-sm font-semibold text-charcoal-800">No Recommendations Available</h3>
        <p className="text-xs text-charcoal-500 max-w-sm mt-1">
          Adjust building dimensions or enter an improvement budget to query the backend recommendation engine.
        </p>
      </div>
    );
  }

  const { ranked_recommendations, available_interventions, total_recommended_cost_inr, remaining_budget_inr, budget_inr } = recommendations;

  const rankedIds = new Set(ranked_recommendations.map((r) => r.id));

  return (
    <div className={`bg-white rounded-xl border border-charcoal-200 p-5 shadow-xs space-y-5 ${className}`}>
      {/* Header & Quick Bundle Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-charcoal-100 gap-2">
        <div>
          <div className="flex items-center space-x-2">
            <Award className="w-4 h-4 text-emerald-700" />
            <h3 className="text-sm font-semibold text-charcoal-900 tracking-tight">
              Backend Optimization Recommendations
            </h3>
          </div>
          <p className="text-xs text-charcoal-500 mt-0.5">
            Ranked deterministically by affordability buffer, spatial suitability, and benchmark evidence.
          </p>
        </div>

        {ranked_recommendations.length > 0 && (
          <button
            onClick={onApplyRecommendedBundle}
            className="flex items-center justify-center space-x-1.5 bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-medium px-3 py-1.5 rounded-lg transition-colors shadow-2xs shrink-0"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Apply Optimal Bundle ({ranked_recommendations.length})</span>
          </button>
        )}
      </div>

      {/* Recommended Package Summary Callout */}
      {ranked_recommendations.length > 0 ? (
        <div className="bg-emerald-50/60 border border-emerald-200 rounded-lg p-3 text-xs flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
          <div>
            <span className="font-semibold text-emerald-950">Optimal Recommended Package: </span>
            <span className="text-emerald-800">
              {ranked_recommendations.map((r) => r.name).join(' + ')}
            </span>
          </div>
          <div className="flex items-center space-x-2 font-mono text-[11px] shrink-0">
            <span className="text-emerald-900 font-bold">{formatINR(total_recommended_cost_inr)}</span>
            <span className="text-emerald-700/80">({formatINR(remaining_budget_inr)} buffer remaining)</span>
          </div>
        </div>
      ) : (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-xs text-amber-800 flex items-start space-x-2">
          <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">No interventions fit the current budget of {formatINR(budget_inr)}.</span> Try increasing the budget or adjusting building parameters to expand feasible options.
          </div>
        </div>
      )}

      {/* Available Interventions Cards */}
      <div className="space-y-3">
        {available_interventions.map((item) => {
          const isSelected = selectedInterventions.includes(item.id);

          return (
            <div
              key={item.id}
              className={`rounded-lg border p-4 transition-all ${
                isSelected
                  ? 'bg-emerald-50/30 border-emerald-300 ring-1 ring-emerald-300/40'
                  : 'bg-white border-charcoal-200 hover:border-charcoal-300'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <h4 className="text-xs font-bold text-charcoal-900">
                      {item.name}
                    </h4>
                    {rankedIds.has(item.id) && (
                      <span className="text-[10px] font-semibold bg-emerald-700 text-white px-2 py-0.5 rounded shadow-2xs">
                        In Optimal Package
                      </span>
                    )}
                    {item.rank && (
                      <span className="text-[10px] font-semibold bg-charcoal-900 text-white px-1.5 py-0.5 rounded">
                        Rank #{item.rank}
                      </span>
                    )}
                    {item.score && (
                      <span className="text-[10px] font-mono text-emerald-800 bg-emerald-100/70 px-1.5 py-0.5 rounded">
                        Score: {item.score}/100
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-charcoal-600 leading-relaxed">
                    {item.description}
                  </p>
                </div>

                {/* Individual Toggle in 3D Button */}
                <button
                  onClick={() => item.is_eligible && onToggleIntervention(item.id)}
                  disabled={!item.is_eligible}
                  className={`flex items-center space-x-1 text-xs px-2.5 py-1.5 rounded-lg font-medium transition-colors shrink-0 ${
                    !item.is_eligible
                      ? 'bg-stone-100 text-stone-400 cursor-not-allowed border border-stone-200'
                      : isSelected
                      ? 'bg-emerald-700 text-white hover:bg-emerald-800 shadow-2xs'
                      : 'bg-white text-charcoal-700 border border-charcoal-300 hover:bg-charcoal-50'
                  }`}
                >
                  {isSelected ? (
                    <>
                      <Check className="w-3.5 h-3.5" />
                      <span>In 3D View</span>
                    </>
                  ) : (
                    <>
                      <Plus className="w-3.5 h-3.5" />
                      <span>Add to 3D</span>
                    </>
                  )}
                </button>
              </div>

              {/* Rate & Quantitative Sizing */}
              <div className="mt-2.5 pt-2 border-t border-charcoal-100 flex flex-wrap items-center justify-between gap-2 text-[11px]">
                <div className="flex items-center space-x-3 text-charcoal-600">
                  <span>
                    Calculated Qty:{' '}
                    <strong className="text-charcoal-900 font-mono">
                      {item.quantity} {item.quantity_unit}
                    </strong>
                  </span>
                  <span>|</span>
                  <span>
                    Estimated Cost:{' '}
                    <strong className="text-charcoal-900 font-mono">
                      {formatINR(item.estimated_cost_inr)}
                    </strong>
                  </span>
                </div>

                <div>
                  {item.fits_budget ? (
                    <span className="text-[10px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                      Within Budget
                    </span>
                  ) : (
                    <span className="text-[10px] font-medium text-rose-700 bg-rose-50 px-2 py-0.5 rounded border border-rose-200">
                      Exceeds Budget
                    </span>
                  )}
                </div>
              </div>

              {/* Explainability Text */}
              <div className="mt-2 bg-stone-50 rounded p-2 text-[11px] text-charcoal-700 border border-charcoal-200/50">
                <span className="font-semibold text-charcoal-800">Engine Evaluation: </span>
                <span>{item.explanation}</span>
              </div>

              {/* Evidence & Limitations */}
              <div className="mt-2 flex flex-col space-y-1 text-[10px] text-charcoal-500">
                <div>
                  <span className="font-medium text-charcoal-600">Evidence Benchmark: </span>
                  <span>{item.evidence_status}</span>
                </div>
                {item.limitations.length > 0 && (
                  <div>
                    <span className="font-medium text-charcoal-600">Limitations: </span>
                    <span>{item.limitations.join(' ')}</span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
