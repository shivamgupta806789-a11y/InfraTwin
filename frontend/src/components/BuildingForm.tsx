import React from 'react';
import { BuildingParams, BuildingFormErrors } from '../types/building';
import { formatINR, formatArea } from '../lib/validation';
import { RotateCcw, AlertCircle, Sparkles, Building2, Sliders } from 'lucide-react';

interface BuildingFormProps {
  params: BuildingParams;
  errors: BuildingFormErrors;
  onChange: (updated: Partial<BuildingParams>) => void;
  onResetSample: () => void;
  className?: string;
}

export const BuildingForm: React.FC<BuildingFormProps> = ({
  params,
  errors,
  onChange,
  onResetSample,
  className = '',
}) => {
  const roofArea = params.width_m * params.length_m;
  const totalHeight = params.floors * params.floor_height_m;
  const grossFloorArea = roofArea * params.floors;
  const wallArea = 2 * (params.width_m + params.length_m) * totalHeight;
  const windowWallRatio = wallArea > 0 ? (params.window_count * 2.0) / wallArea : 0;

  return (
    <div className={`bg-white rounded-xl border border-charcoal-200 p-5 shadow-xs flex flex-col space-y-5 ${className}`}>
      {/* Panel Header */}
      <div className="flex items-center justify-between pb-3 border-b border-charcoal-100">
        <div className="flex items-center space-x-2">
          <Building2 className="w-5 h-5 text-charcoal-700" />
          <h2 className="text-sm font-semibold text-charcoal-900 tracking-tight">Building Parameters</h2>
        </div>
        <button
          onClick={onResetSample}
          className="flex items-center space-x-1 text-xs text-charcoal-600 hover:text-charcoal-900 px-2.5 py-1 rounded-md hover:bg-charcoal-50 border border-charcoal-200 transition-colors"
          title="Reset to default benchmark sample building"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Load Sample</span>
        </button>
      </div>

      {/* Geometry Dimensions Grid */}
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          {/* Width */}
          <div>
            <label className="block text-xs font-medium text-charcoal-700 mb-1">
              Width (m)
            </label>
            <input
              type="number"
              step="0.5"
              min="1"
              max="200"
              value={params.width_m || ''}
              onChange={(e) => onChange({ width_m: parseFloat(e.target.value) || 0 })}
              className={`w-full px-3 py-1.5 text-sm bg-stone-50 border rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-400 text-charcoal-900 ${
                errors.width_m ? 'border-red-400 bg-red-50/20' : 'border-charcoal-200'
              }`}
            />
            {errors.width_m && (
              <p className="mt-1 text-[11px] text-red-600 flex items-center space-x-1">
                <AlertCircle className="w-3 h-3 shrink-0" />
                <span>{errors.width_m}</span>
              </p>
            )}
          </div>

          {/* Length */}
          <div>
            <label className="block text-xs font-medium text-charcoal-700 mb-1">
              Length (m)
            </label>
            <input
              type="number"
              step="0.5"
              min="1"
              max="200"
              value={params.length_m || ''}
              onChange={(e) => onChange({ length_m: parseFloat(e.target.value) || 0 })}
              className={`w-full px-3 py-1.5 text-sm bg-stone-50 border rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-400 text-charcoal-900 ${
                errors.length_m ? 'border-red-400 bg-red-50/20' : 'border-charcoal-200'
              }`}
            />
            {errors.length_m && (
              <p className="mt-1 text-[11px] text-red-600 flex items-center space-x-1">
                <AlertCircle className="w-3 h-3 shrink-0" />
                <span>{errors.length_m}</span>
              </p>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {/* Floors */}
          <div>
            <label className="block text-xs font-medium text-charcoal-700 mb-1">
              Floors (count)
            </label>
            <input
              type="number"
              step="1"
              min="1"
              max="50"
              value={params.floors || ''}
              onChange={(e) => onChange({ floors: parseInt(e.target.value, 10) || 0 })}
              className={`w-full px-3 py-1.5 text-sm bg-stone-50 border rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-400 text-charcoal-900 ${
                errors.floors ? 'border-red-400 bg-red-50/20' : 'border-charcoal-200'
              }`}
            />
            {errors.floors && (
              <p className="mt-1 text-[11px] text-red-600 flex items-center space-x-1">
                <AlertCircle className="w-3 h-3 shrink-0" />
                <span>{errors.floors}</span>
              </p>
            )}
          </div>

          {/* Floor Height */}
          <div>
            <label className="block text-xs font-medium text-charcoal-700 mb-1">
              Floor Height (m)
            </label>
            <input
              type="number"
              step="0.1"
              min="1.5"
              max="10.0"
              value={params.floor_height_m || ''}
              onChange={(e) => onChange({ floor_height_m: parseFloat(e.target.value) || 0 })}
              className={`w-full px-3 py-1.5 text-sm bg-stone-50 border rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-400 text-charcoal-900 ${
                errors.floor_height_m ? 'border-red-400 bg-red-50/20' : 'border-charcoal-200'
              }`}
            />
            {errors.floor_height_m && (
              <p className="mt-1 text-[11px] text-red-600 flex items-center space-x-1">
                <AlertCircle className="w-3 h-3 shrink-0" />
                <span>{errors.floor_height_m}</span>
              </p>
            )}
          </div>
        </div>

        {/* Windows Count */}
        <div>
          <div className="flex items-center justify-between mb-1">
            <label className="block text-xs font-medium text-charcoal-700">
              Exterior Windows (count)
            </label>
            <span className="text-[11px] text-charcoal-500">
              ~{(windowWallRatio * 100).toFixed(1)}% WWR
            </span>
          </div>
          <input
            type="number"
            step="1"
            min="0"
            max="1000"
            value={params.window_count !== undefined ? params.window_count : ''}
            onChange={(e) => onChange({ window_count: parseInt(e.target.value, 10) || 0 })}
            className={`w-full px-3 py-1.5 text-sm bg-stone-50 border rounded-lg focus:outline-none focus:ring-2 focus:ring-stone-400 text-charcoal-900 ${
              errors.window_count ? 'border-red-400 bg-red-50/20' : 'border-charcoal-200'
            }`}
          />
          {errors.window_count && (
            <p className="mt-1 text-[11px] text-red-600 flex items-center space-x-1">
              <AlertCircle className="w-3 h-3 shrink-0" />
              <span>{errors.window_count}</span>
            </p>
          )}
        </div>

        {/* Improvement Budget (INR) */}
        <div className="pt-2 border-t border-charcoal-100">
          <div className="flex items-center justify-between mb-1">
            <label className="block text-xs font-semibold text-charcoal-900 flex items-center space-x-1">
              <Sparkles className="w-3.5 h-3.5 text-amber-600" />
              <span>Improvement Budget (INR)</span>
            </label>
            <span className="text-xs font-mono font-medium text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              {formatINR(params.budget_inr)}
            </span>
          </div>
          <input
            type="number"
            step="5000"
            min="0"
            max="1000000000"
            value={params.budget_inr !== undefined ? params.budget_inr : ''}
            onChange={(e) => onChange({ budget_inr: parseFloat(e.target.value) || 0 })}
            className={`w-full px-3 py-2 text-sm bg-white border rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono text-charcoal-900 ${
              errors.budget_inr ? 'border-red-400 bg-red-50/20' : 'border-charcoal-300'
            }`}
            placeholder="Enter available budget in ₹"
          />
          {errors.budget_inr && (
            <p className="mt-1 text-[11px] text-red-600 flex items-center space-x-1">
              <AlertCircle className="w-3 h-3 shrink-0" />
              <span>{errors.budget_inr}</span>
            </p>
          )}

          {/* Budget Presets */}
          <div className="flex items-center space-x-1.5 mt-2">
            {[50000, 150000, 250000, 500000].map((preset) => (
              <button
                key={preset}
                type="button"
                onClick={() => onChange({ budget_inr: preset })}
                className={`text-[10px] px-2 py-1 rounded border transition-colors ${
                  params.budget_inr === preset
                    ? 'bg-charcoal-900 text-white border-charcoal-900'
                    : 'bg-stone-50 text-charcoal-600 border-charcoal-200 hover:bg-charcoal-100'
                }`}
              >
                ₹{(preset / 100000).toFixed(preset >= 100000 ? 1 : 2)}L
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Derived Spatial Metrics Preview */}
      <div className="bg-stone-50 rounded-lg p-3 border border-charcoal-200/70 text-xs space-y-1.5 text-charcoal-600">
        <div className="flex items-center space-x-1 font-medium text-charcoal-800 mb-1 text-[11px] uppercase tracking-wider">
          <Sliders className="w-3 h-3" />
          <span>Calculated Geometry</span>
        </div>
        <div className="flex justify-between">
          <span>Terrace / Roof Area:</span>
          <span className="font-mono text-charcoal-900 font-medium">{formatArea(roofArea)}</span>
        </div>
        <div className="flex justify-between">
          <span>Total Building Height:</span>
          <span className="font-mono text-charcoal-900 font-medium">{totalHeight.toFixed(1)} m</span>
        </div>
        <div className="flex justify-between">
          <span>Gross Floor Area (GFA):</span>
          <span className="font-mono text-charcoal-900 font-medium">{formatArea(grossFloorArea)}</span>
        </div>
        <div className="flex justify-between">
          <span>Total Wall Facade Area:</span>
          <span className="font-mono text-charcoal-900 font-medium">{formatArea(wallArea)}</span>
        </div>
      </div>
    </div>
  );
};
