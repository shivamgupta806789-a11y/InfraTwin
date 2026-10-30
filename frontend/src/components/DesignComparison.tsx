import React, { useState } from 'react';
import { BuildingParams } from '../types/building';
import { BuildingViewer } from './BuildingViewer';
import { formatINR } from '../lib/validation';
import { Columns } from 'lucide-react';

interface DesignComparisonProps {
  params: BuildingParams;
  totalCost: number;
  className?: string;
}

export const DesignComparison: React.FC<DesignComparisonProps> = ({
  params,
  totalCost,
  className = '',
}) => {
  // Modes: 'proposed' (full proposed viewer), 'baseline' (baseline only), 'split' (side by side)
  const [viewMode, setViewMode] = useState<'proposed' | 'baseline' | 'split'>('proposed');

  return (
    <div className={`flex flex-col space-y-3 ${className}`}>
      {/* View Switcher Controls */}
      <div className="flex items-center justify-between bg-white p-2 rounded-xl border border-charcoal-200 shadow-2xs">
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setViewMode('proposed')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              viewMode === 'proposed'
                ? 'bg-charcoal-900 text-white shadow-xs'
                : 'text-charcoal-600 hover:text-charcoal-900 hover:bg-charcoal-50'
            }`}
          >
            Proposed Design ({params.selected_interventions.length} Upgrades)
          </button>
          <button
            onClick={() => setViewMode('baseline')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              viewMode === 'baseline'
                ? 'bg-charcoal-900 text-white shadow-xs'
                : 'text-charcoal-600 hover:text-charcoal-900 hover:bg-charcoal-50'
            }`}
          >
            Baseline Design (Original)
          </button>
          <button
            onClick={() => setViewMode('split')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center space-x-1.5 ${
              viewMode === 'split'
                ? 'bg-charcoal-900 text-white shadow-xs'
                : 'text-charcoal-600 hover:text-charcoal-900 hover:bg-charcoal-50'
            }`}
          >
            <Columns className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Side-by-Side</span>
          </button>
        </div>

        {/* Selected Summary Pill */}
        <div className="flex items-center space-x-2 text-xs pr-2">
          <span className="text-charcoal-500 hidden md:inline">Proposed Cost:</span>
          <span className="font-mono font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
            {formatINR(totalCost)}
          </span>
        </div>
      </div>

      {/* 3D Viewport Rendering depending on viewMode */}
      {viewMode === 'split' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 min-h-[440px]">
          {/* Baseline Side */}
          <div className="flex flex-col space-y-1.5">
            <BuildingViewer
              params={params}
              isBaseline={true}
              label="Baseline Design"
              className="h-[440px]"
            />
            <div className="p-2 bg-white rounded-lg border border-charcoal-200 text-xs text-charcoal-600 flex items-center justify-between">
              <span className="font-medium text-stone-700">Pre-improvement state</span>
              <span className="font-mono text-charcoal-500">₹ 0 (Original)</span>
            </div>
          </div>

          {/* Proposed Side */}
          <div className="flex flex-col space-y-1.5">
            <BuildingViewer
              params={params}
              isBaseline={false}
              showInterventions={true}
              label="Proposed Design"
              className="h-[440px]"
            />
            <div className="p-2 bg-white rounded-lg border border-charcoal-200 text-xs text-charcoal-600 flex items-center justify-between">
              <span className="font-medium text-emerald-800">
                {params.selected_interventions.length > 0
                  ? `${params.selected_interventions.length} interventions applied`
                  : 'No interventions selected'}
              </span>
              <span className="font-mono font-semibold text-charcoal-900">
                {formatINR(totalCost)}
              </span>
            </div>
          </div>
        </div>
      ) : (
        <div className="relative min-h-[460px]">
          <BuildingViewer
            params={params}
            isBaseline={viewMode === 'baseline'}
            showInterventions={viewMode === 'proposed'}
            label={viewMode === 'baseline' ? 'Baseline (Original Model)' : 'Proposed Design (Interactive 3D)'}
            className="h-[480px]"
          />
        </div>
      )}
    </div>
  );
};
