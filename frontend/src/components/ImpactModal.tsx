import React from 'react';
import { EstimateResponse } from '../types/recommendations';
import { CheckCircle, XCircle, Scale } from 'lucide-react';

interface ImpactModalProps {
  isOpen: boolean;
  onClose: () => void;
  estimate: EstimateResponse | null;
  annualKwh: number;
  onKwhChange: (kwh: number) => void;
  className?: string;
}

export const ImpactModal: React.FC<ImpactModalProps> = ({
  isOpen,
  onClose,
  estimate,
  annualKwh,
  onKwhChange,
  className = '',
}) => {
  if (!isOpen) return null;

  return (
    <div className={`fixed inset-0 z-50 flex items-center justify-center p-4 bg-charcoal-950/60 backdrop-blur-xs ${className}`}>
      <div className="bg-white rounded-2xl border border-charcoal-200 max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl flex flex-col">
        {/* Header */}
        <div className="sticky top-0 bg-white/95 backdrop-blur-sm px-6 py-4 border-b border-charcoal-100 flex items-center justify-between z-10">
          <div className="flex items-center space-x-2">
            <Scale className="w-5 h-5 text-emerald-800" />
            <div>
              <h3 className="text-base font-bold text-charcoal-900">
                Scientific Honesty & Impact Calculations
              </h3>
              <p className="text-xs text-charcoal-500">
                Transparent verification methodology distinguishing engineering facts from visual demonstration.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-charcoal-400 hover:text-charcoal-700 p-1.5 rounded-lg hover:bg-charcoal-50 text-sm font-semibold"
          >
            ✕
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6">
          {/* Optional Baseline Utility Bill Input */}
          <div className="bg-stone-50 border border-charcoal-200 rounded-xl p-4 space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-charcoal-800">
                Optional: Measured Annual Grid Electricity (kWh/yr)
              </label>
              <span className="text-[11px] text-charcoal-500">
                Indian Grid Factor: 0.716 kg CO2e / kWh (CEA 2023)
              </span>
            </div>
            <div className="flex items-center space-x-3">
              <input
                type="number"
                min="0"
                step="500"
                placeholder="e.g. 12000"
                value={annualKwh || ''}
                onChange={(e) => onKwhChange(parseFloat(e.target.value) || 0)}
                className="w-48 px-3 py-1.5 text-sm bg-white border border-charcoal-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono"
              />
              <span className="text-xs text-charcoal-600">
                {annualKwh > 0 ? (
                  <span>
                    Baseline Carbon: <strong>{((annualKwh * 0.716) / 1000).toFixed(2)} tonnes CO2e/year</strong>
                  </span>
                ) : (
                  <span className="text-charcoal-500 italic">
                    Enter actual utility kWh to compute baseline carbon emissions.
                  </span>
                )}
              </span>
            </div>
          </div>

          {/* Impact Estimates from API */}
          {estimate && (
            <div className="space-y-4">
              <h4 className="text-xs font-semibold text-charcoal-900 uppercase tracking-wider">
                Impact Calculation Status
              </h4>

              <div className="space-y-3">
                {estimate.impact_estimates.map((impact, idx) => (
                  <div
                    key={idx}
                    className={`p-4 rounded-xl border ${
                      impact.is_estimated
                        ? 'bg-emerald-50/40 border-emerald-200'
                        : 'bg-stone-50 border-charcoal-200'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-bold text-charcoal-900">
                            {impact.metric}
                          </span>
                          {impact.is_estimated ? (
                            <span className="inline-flex items-center space-x-1 text-[10px] font-medium text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full">
                              <CheckCircle className="w-3 h-3" />
                              <span>Calculated</span>
                            </span>
                          ) : (
                            <span className="inline-flex items-center space-x-1 text-[10px] font-medium text-amber-800 bg-amber-100 px-2 py-0.5 rounded-full">
                              <XCircle className="w-3 h-3" />
                              <span>Not Estimated</span>
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-charcoal-600">
                          <strong>Formula / Method:</strong> {impact.calculation_method}
                        </p>
                      </div>

                      {impact.is_estimated && impact.value !== null && impact.value !== undefined && (
                        <div className="text-right shrink-0">
                          <span className="text-lg font-mono font-bold text-emerald-900">
                            {impact.value.toLocaleString()}
                          </span>
                          <span className="text-xs text-emerald-700 ml-1">{impact.unit}</span>
                        </div>
                      )}
                    </div>

                    {/* Assumptions & Limitations list */}
                    <div className="mt-3 pt-2 border-t border-charcoal-200/60 text-[11px] space-y-1 text-charcoal-600">
                      <div>
                        <strong>Assumptions:</strong> {impact.assumptions.join(' ')}
                      </div>
                      <div>
                        <strong>Data Source:</strong> {impact.source_provenance}
                      </div>
                      <div>
                        <strong>Scientific Boundary:</strong> {impact.evidence_limitations}
                      </div>
                      {impact.missing_inputs.length > 0 && (
                        <div className="text-amber-800 bg-amber-50/80 p-2 rounded mt-1 border border-amber-200">
                          <strong>Missing Inputs Required for Validation:</strong>{' '}
                          {impact.missing_inputs.join(', ')}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Architectural Disclosures */}
          <div className="bg-stone-50 rounded-xl p-4 border border-charcoal-200 text-xs text-charcoal-600 space-y-2">
            <h4 className="font-semibold text-charcoal-900">Architectural Disclosures & Code Compliance</h4>
            <ul className="list-disc list-inside space-y-1 text-[11px] leading-relaxed">
              <li><strong>Zero Fabricated Savings:</strong> We deliberately do not fabricate fixed percentage reductions (e.g. "Save 30% energy!") because real cooling loads depend on microclimate weather (EPW), HVAC efficiency (COP), and occupant schedules.</li>
              <li><strong>Indian Benchmark Rates:</strong> Cost figures are derived from standard CPWD Delhi Schedule of Rates (DSR 2023), BEE ECBC specifications, and MNRE benchmark rooftop solar capital cost guidelines.</li>
              <li><strong>Structural Caution:</strong> Solar arrays and screed-protected roof insulation add dead load (15-40 kg/m²); small builders must consult a licensed structural engineer prior to terrace installation.</li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-stone-50 px-6 py-3 border-t border-charcoal-100 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-charcoal-900 text-white rounded-lg text-xs font-semibold hover:bg-charcoal-800 transition-colors shadow-2xs"
          >
            Close Disclosures
          </button>
        </div>
      </div>
    </div>
  );
};
