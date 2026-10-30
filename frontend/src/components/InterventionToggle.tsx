import React from 'react';
import { InterventionId } from '../types/building';
import { InterventionItem } from '../types/recommendations';
import { formatINR } from '../lib/validation';
import { Sun, Shield, Sparkles, Layers, Check, Plus } from 'lucide-react';

interface InterventionToggleProps {
  selectedInterventions: InterventionId[];
  onToggle: (id: InterventionId) => void;
  availableItems?: InterventionItem[];
  budget: number;
}

const INTERVENTIONS_CONFIG: Array<{
  id: InterventionId;
  name: string;
  icon: React.FC<{ className?: string }>;
  tag: string;
}> = [
  {
    id: 'external_shading',
    name: 'External Window Louvers',
    icon: Sun,
    tag: 'Window Shading',
  },
  {
    id: 'reflective_roof',
    name: 'High-Albedo Cool Roof',
    icon: Sparkles,
    tag: 'Reflective Surface',
  },
  {
    id: 'roof_insulation',
    name: 'Over-Deck Roof Insulation',
    icon: Layers,
    tag: '50mm XPS Slab',
  },
  {
    id: 'solar_pv',
    name: 'Rooftop Solar PV Array',
    icon: Shield,
    tag: 'Clean Generation',
  },
];

export const InterventionToggle: React.FC<InterventionToggleProps> = ({
  selectedInterventions,
  onToggle,
  availableItems = [],
  budget,
}) => {
  const itemMap = new Map<string, InterventionItem>(
    availableItems.map((item) => [item.id, item])
  );

  return (
    <div className="bg-white rounded-xl border border-charcoal-200 p-4 shadow-xs space-y-3">
      <div className="flex items-center justify-between pb-2 border-b border-charcoal-100">
        <h3 className="text-xs font-semibold text-charcoal-900 uppercase tracking-wider">
          Design Interventions (3D Toggles)
        </h3>
        <span className="text-[11px] text-charcoal-500 font-medium">
          {selectedInterventions.length} of {INTERVENTIONS_CONFIG.length} applied
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        {INTERVENTIONS_CONFIG.map(({ id, name, icon: Icon, tag }) => {
          const isSelected = selectedInterventions.includes(id);
          const itemData = itemMap.get(id);
          const cost = itemData ? itemData.estimated_cost_inr : 0;
          const fitsBudget = itemData ? itemData.fits_budget : (cost <= budget);
          const isEligible = itemData ? itemData.is_eligible : true;

          return (
            <div
              key={id}
              onClick={() => isEligible && onToggle(id)}
              className={`p-3 rounded-lg border text-left transition-all cursor-pointer select-none flex flex-col justify-between ${
                !isEligible
                  ? 'bg-stone-50 border-stone-200 opacity-60 cursor-not-allowed'
                  : isSelected
                  ? 'bg-emerald-50/70 border-emerald-400 ring-1 ring-emerald-400/40'
                  : 'bg-white border-charcoal-200 hover:border-charcoal-300 hover:bg-stone-50/50'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2">
                  <div
                    className={`p-1.5 rounded-md ${
                      isSelected
                        ? 'bg-emerald-600 text-white'
                        : 'bg-charcoal-100 text-charcoal-700'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs font-semibold text-charcoal-900 leading-tight">
                      {name}
                    </h4>
                    <span className="text-[10px] text-charcoal-500">{tag}</span>
                  </div>
                </div>

                {/* Status Toggle Pill */}
                <div
                  className={`w-5 h-5 rounded-md flex items-center justify-center transition-colors ${
                    isSelected
                      ? 'bg-emerald-600 text-white'
                      : 'border border-charcoal-300 text-charcoal-400 hover:border-charcoal-400'
                  }`}
                >
                  {isSelected ? <Check className="w-3.5 h-3.5" /> : <Plus className="w-3 h-3" />}
                </div>
              </div>

              {/* Cost & Feasibility Indicator */}
              <div className="mt-2.5 pt-2 border-t border-charcoal-100 flex items-center justify-between text-[11px]">
                <span className="font-mono text-charcoal-800 font-medium">
                  {cost > 0 ? formatINR(cost) : 'Estimating...'}
                </span>
                {itemData && !isEligible ? (
                  <span className="text-[10px] font-medium text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200">
                    Not Eligible
                  </span>
                ) : fitsBudget ? (
                  <span className="text-[10px] font-medium text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-200">
                    Fits Budget
                  </span>
                ) : (
                  <span className="text-[10px] font-medium text-rose-700 bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
                    Exceeds
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
