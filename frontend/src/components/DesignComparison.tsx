import React, { useState } from 'react';
import { BuildingParams } from '../types/building';
import { BuildingModelDetail } from '../types/digital_twin';
import { BuildingViewer, ViewerMode } from './BuildingViewer';
import { formatINR } from '../lib/validation';
import { Columns, Layers, Building2, Home } from 'lucide-react';

interface DesignComparisonProps {
  params: BuildingParams;
  totalCost: number;
  importedModel?: BuildingModelDetail | null;
  className?: string;
}

export const DesignComparison: React.FC<DesignComparisonProps> = ({
  params,
  totalCost,
  importedModel = null,
  className = '',
}) => {
  // Modes: 'proposed' (full proposed viewer), 'baseline' (baseline only), 'split' (side by side)
  const [viewMode, setViewMode] = useState<'proposed' | 'baseline' | 'split'>('proposed');
  const [sharedViewerMode, setSharedViewerMode] = useState<ViewerMode>('exterior');

  return (
    <div className={`flex flex-col space-y-3 ${className}`}>
      {/* View Switcher Controls */}
      <div className="flex flex-wrap items-center justify-between bg-white p-2.5 rounded-xl border border-charcoal-200 shadow-2xs gap-2">
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setViewMode('proposed')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              viewMode === 'proposed'
                ? 'bg-charcoal-900 text-white shadow-xs'
                : 'text-charcoal-600 hover:text-charcoal-900 hover:bg-stone-100'
            }`}
          >
            Proposed Design ({params.selected_interventions.length} Upgrades)
          </button>
          <button
            onClick={() => setViewMode('baseline')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              viewMode === 'baseline'
                ? 'bg-charcoal-900 text-white shadow-xs'
                : 'text-charcoal-600 hover:text-charcoal-900 hover:bg-stone-100'
            }`}
          >
            Baseline Design (Original BIM)
          </button>
          <button
            onClick={() => setViewMode('split')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center space-x-1.5 ${
              viewMode === 'split'
                ? 'bg-charcoal-900 text-white shadow-xs'
                : 'text-charcoal-600 hover:text-charcoal-900 hover:bg-stone-100'
            }`}
          >
            <Columns className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Side-by-Side</span>
          </button>
        </div>

        {/* Shared Viewer Mode Selector for Comparison */}
        <div className="flex items-center bg-stone-100 p-0.5 rounded-lg border border-charcoal-200 text-xs">
          <button
            onClick={() => setSharedViewerMode('skeleton')}
            className={`px-2.5 py-1 rounded-md font-medium transition-all flex items-center space-x-1 ${
              sharedViewerMode === 'skeleton' ? 'bg-charcoal-900 text-white shadow-2xs' : 'text-charcoal-600 hover:text-charcoal-900'
            }`}
            title="Structural wireframe mesh"
          >
            <Layers className="w-3 h-3" />
            <span>Skeleton</span>
          </button>
          <button
            onClick={() => setSharedViewerMode('exterior')}
            className={`px-2.5 py-1 rounded-md font-medium transition-all flex items-center space-x-1 ${
              sharedViewerMode === 'exterior' ? 'bg-charcoal-900 text-white shadow-2xs' : 'text-charcoal-600 hover:text-charcoal-900'
            }`}
            title="Solid architectural exterior"
          >
            <Building2 className="w-3 h-3" />
            <span>Exterior</span>
          </button>
          <button
            onClick={() => setSharedViewerMode('interior')}
            className={`px-2.5 py-1 rounded-md font-medium transition-all flex items-center space-x-1 ${
              sharedViewerMode === 'interior' ? 'bg-charcoal-900 text-white shadow-2xs' : 'text-charcoal-600 hover:text-charcoal-900'
            }`}
            title="Interior rooms & cutaway"
          >
            <Home className="w-3 h-3" />
            <span>Interior</span>
          </button>
        </div>

        {/* Selected Summary Pill */}
        <div className="flex items-center space-x-2 text-xs pr-1">
          <span className="text-charcoal-500 hidden md:inline">Proposed Cost:</span>
          <span className="font-mono font-semibold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded border border-emerald-200">
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
              importedModel={importedModel}
              isBaseline={true}
              viewerMode={sharedViewerMode}
              onViewerModeChange={setSharedViewerMode}
              label={importedModel ? `Original BIM (${importedModel.building_name || 'BIM Twin'})` : 'Baseline Design (Original)'}
              className="h-[440px]"
            />
            <div className="p-2.5 bg-white rounded-lg border border-charcoal-200 text-xs text-charcoal-600 flex items-center justify-between">
              <span className="font-medium text-stone-700">Pre-improvement baseline (v1.0)</span>
              <span className="font-mono text-charcoal-500">₹ 0 (Original)</span>
            </div>
          </div>

          {/* Proposed Side */}
          <div className="flex flex-col space-y-1.5">
            <BuildingViewer
              params={params}
              isBaseline={false}
              showInterventions={true}
              viewerMode={sharedViewerMode}
              onViewerModeChange={setSharedViewerMode}
              label="Proposed Design (Parametric Alternative)"
              className="h-[440px]"
            />
            <div className="p-2.5 bg-white rounded-lg border border-charcoal-200 text-xs text-charcoal-600 flex items-center justify-between">
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
            importedModel={viewMode === 'baseline' ? importedModel : null}
            isBaseline={viewMode === 'baseline'}
            showInterventions={viewMode === 'proposed'}
            viewerMode={sharedViewerMode}
            onViewerModeChange={setSharedViewerMode}
            label={viewMode === 'baseline' ? `Original BIM Baseline (${importedModel?.building_name || 'BIM Twin'})` : 'Proposed Design (Interactive 3D)'}
            className="h-[480px]"
          />
        </div>
      )}
    </div>
  );
};
