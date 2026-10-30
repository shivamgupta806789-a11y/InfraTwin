import React, { useState } from 'react';
import { EsgAssessmentReport, EsgItem } from '../types/digital_twin';
import { Leaf, Users, Shield, CheckCircle2, AlertTriangle, HelpCircle, AlertCircle, Scale, RefreshCw } from 'lucide-react';

interface EsgDashboardViewProps {
  report: EsgAssessmentReport | null;
  annualKwh: number;
  onKwhChange: (kwh: number) => void;
  onRefresh: () => void;
  isLoading: boolean;
  className?: string;
}

export const EsgDashboardView: React.FC<EsgDashboardViewProps> = ({
  report,
  annualKwh,
  onKwhChange,
  onRefresh,
  isLoading,
  className = '',
}) => {
  const [activeTab, setActiveTab] = useState<'environmental' | 'social' | 'governance'>('environmental');

  if (isLoading) {
    return (
      <div className={`bg-white rounded-xl border border-charcoal-200 p-8 text-center space-y-3 ${className}`}>
        <div className="w-8 h-8 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs text-charcoal-600 font-medium">Evaluating Environmental, Social & Governance criteria...</p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className={`bg-white rounded-xl border border-charcoal-200 p-8 text-center text-charcoal-500 text-xs ${className}`}>
        No ESG assessment available. Import an IFC digital twin to screen sustainability criteria.
      </div>
    );
  }

  const items = report[activeTab];

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'assessed':
        return <span className="text-[10px] uppercase font-bold bg-emerald-100 text-emerald-800 border border-emerald-300 px-2 py-0.5 rounded-full flex items-center space-x-1"><CheckCircle2 className="w-3 h-3" /><span>Assessed</span></span>;
      case 'estimated':
        return <span className="text-[10px] uppercase font-bold bg-blue-100 text-blue-800 border border-blue-300 px-2 py-0.5 rounded-full flex items-center space-x-1"><CheckCircle2 className="w-3 h-3" /><span>Estimated</span></span>;
      case 'potential_concern':
        return <span className="text-[10px] uppercase font-bold bg-amber-100 text-amber-800 border border-amber-300 px-2 py-0.5 rounded-full flex items-center space-x-1"><AlertTriangle className="w-3 h-3" /><span>Potential Concern</span></span>;
      case 'requires_professional_review':
        return <span className="text-[10px] uppercase font-bold bg-purple-100 text-purple-800 border border-purple-300 px-2 py-0.5 rounded-full flex items-center space-x-1"><AlertCircle className="w-3 h-3" /><span>Requires Review</span></span>;
      default:
        return <span className="text-[10px] uppercase font-medium bg-stone-100 text-stone-700 border border-stone-300 px-2 py-0.5 rounded-full flex items-center space-x-1"><HelpCircle className="w-3 h-3" /><span>Insufficient Data</span></span>;
    }
  };

  return (
    <div className={`bg-white rounded-xl border border-charcoal-200 p-5 shadow-xs space-y-5 ${className}`}>
      {/* Header & Preliminary Disclaimer */}
      <div className="space-y-2 pb-3 border-b border-charcoal-100">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <Scale className="w-5 h-5 text-emerald-800" />
            <h3 className="text-sm font-bold text-charcoal-900 tracking-tight">
              Evidence-Based ESG Assessment Framework
            </h3>
          </div>
          <div className="flex items-center space-x-2 text-[11px] text-charcoal-500">
            <span className="bg-stone-100 px-2.5 py-1 rounded-full border border-charcoal-200 font-medium">
              Zero Arbitrary Scoring • Strict Provenance
            </span>
          </div>
        </div>
        <p className="text-[11px] text-charcoal-500 bg-stone-50 p-2.5 rounded-lg border border-charcoal-200/80 leading-relaxed">
          <strong>Notice:</strong> {report.disclaimer}
        </p>
      </div>

      {/* Optional Metered Electricity Input */}
      <div className="bg-emerald-50/40 rounded-xl p-3.5 border border-emerald-200/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div>
          <label className="font-semibold text-charcoal-900 block text-xs">
            Operational Electricity Input (Scope 2 Footprint)
          </label>
          <span className="text-[11px] text-charcoal-600">
            National Grid Factor: 0.716 kg CO2e/kWh (CEA India Baseline 2023)
          </span>
        </div>
        <div className="flex items-center space-x-2">
          <input
            type="number"
            min="0"
            step="1000"
            placeholder="e.g. 24000"
            value={annualKwh || ''}
            onChange={(e) => onKwhChange(parseFloat(e.target.value) || 0)}
            className="w-32 px-2.5 py-1.5 text-xs bg-white border border-charcoal-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 font-mono"
          />
          <button
            onClick={onRefresh}
            className="p-1.5 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg transition-colors shadow-2xs"
            title="Recalculate Operational Emissions"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Pillar Tabs */}
      <div className="flex items-center space-x-2 border-b border-charcoal-200 pb-2">
        <button
          onClick={() => setActiveTab('environmental')}
          className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            activeTab === 'environmental'
              ? 'bg-emerald-800 text-white shadow-2xs'
              : 'text-charcoal-600 hover:bg-stone-50 hover:text-charcoal-900'
          }`}
        >
          <Leaf className="w-3.5 h-3.5" />
          <span>Environmental ({report.environmental.length})</span>
        </button>
        <button
          onClick={() => setActiveTab('social')}
          className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            activeTab === 'social'
              ? 'bg-blue-800 text-white shadow-2xs'
              : 'text-charcoal-600 hover:bg-stone-50 hover:text-charcoal-900'
          }`}
        >
          <Users className="w-3.5 h-3.5" />
          <span>Social ({report.social.length})</span>
        </button>
        <button
          onClick={() => setActiveTab('governance')}
          className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
            activeTab === 'governance'
              ? 'bg-purple-800 text-white shadow-2xs'
              : 'text-charcoal-600 hover:bg-stone-50 hover:text-charcoal-900'
          }`}
        >
          <Shield className="w-3.5 h-3.5" />
          <span>Governance ({report.governance.length})</span>
        </button>
      </div>

      {/* Criteria Cards List */}
      <div className="space-y-3">
        {items.map((criterion: EsgItem) => (
          <div
            key={criterion.criterion_id}
            className="bg-stone-50/60 rounded-xl border border-charcoal-200/80 p-4 text-xs space-y-2.5 hover:border-charcoal-300 transition-colors"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="font-mono text-[10px] font-bold text-charcoal-500 bg-white px-2 py-0.5 rounded border border-charcoal-200">
                    {criterion.criterion_id}
                  </span>
                  {getStatusBadge(criterion.result_status)}
                  <span className="text-[10px] font-semibold text-charcoal-600 bg-stone-100 px-2 py-0.5 rounded">
                    Confidence: {criterion.confidence_status}
                  </span>
                </div>
                <h4 className="text-xs font-bold text-charcoal-900">
                  {criterion.criterion_name}
                </h4>
              </div>

              {criterion.metric_value !== null && criterion.metric_value !== undefined && (
                <div className="text-right shrink-0 bg-white p-2 rounded-lg border border-charcoal-200/80">
                  <span className="font-mono text-sm font-bold text-emerald-900">
                    {criterion.metric_value}
                  </span>
                  {criterion.unit && (
                    <span className="block text-[10px] text-charcoal-500 font-medium">{criterion.unit}</span>
                  )}
                </div>
              )}
            </div>

            {/* Evidence & Methodology */}
            <div className="space-y-1.5 text-[11px] text-charcoal-600 pt-1 border-t border-charcoal-100">
              <div>
                <strong className="text-charcoal-800">Evidence Available:</strong> {criterion.evidence_available}
              </div>
              <div>
                <strong className="text-charcoal-800">Methodology / Standard:</strong> {criterion.calculation_or_rule_applied}
              </div>
              {criterion.assumptions.length > 0 && (
                <div>
                  <strong className="text-charcoal-800">Assumptions:</strong> {criterion.assumptions.join(' ')}
                </div>
              )}
              {criterion.missing_inputs.length > 0 && (
                <div className="bg-amber-50 text-amber-900 p-2 rounded border border-amber-200">
                  <strong>Missing Engineering Inputs:</strong> {criterion.missing_inputs.join(', ')}
                </div>
              )}
            </div>

            {/* Recommended Action */}
            <div className="bg-white rounded-lg p-2.5 border border-charcoal-200 text-[11px] text-emerald-950 flex items-start space-x-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700 shrink-0 mt-0.5" />
              <div>
                <strong>Recommended Next Action:</strong> {criterion.recommended_action}
              </div>
            </div>

            <div className="text-[10px] text-charcoal-400 flex justify-between pt-1">
              <span>Source: {criterion.source_or_provenance}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
