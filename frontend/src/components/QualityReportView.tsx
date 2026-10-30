import React, { useState } from 'react';
import { ModelQualityReport } from '../types/digital_twin';
import { ShieldCheck, AlertTriangle, AlertOctagon, Info, CheckCircle2, Filter } from 'lucide-react';

interface QualityReportViewProps {
  report: ModelQualityReport | null;
  isLoading: boolean;
  onSelectElement?: (elementId: string) => void;
  className?: string;
}

export const QualityReportView: React.FC<QualityReportViewProps> = ({
  report,
  isLoading,
  onSelectElement,
  className = '',
}) => {
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');

  if (isLoading) {
    return (
      <div className={`bg-white rounded-xl border border-charcoal-200 p-8 text-center space-y-3 ${className}`}>
        <div className="w-8 h-8 border-2 border-charcoal-300 border-t-charcoal-800 rounded-full animate-spin mx-auto" />
        <p className="text-xs text-charcoal-600 font-medium">Running model completeness & data quality audit...</p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className={`bg-white rounded-xl border border-charcoal-200 p-8 text-center text-charcoal-500 text-xs ${className}`}>
        No quality report available. Import an IFC digital twin to audit data completeness.
      </div>
    );
  }

  const { findings, by_severity, data_completeness_ratio, summary } = report;

  const filteredFindings = selectedSeverity === 'all'
    ? findings
    : findings.filter((f) => f.severity.toLowerCase() === selectedSeverity.toLowerCase());

  const getSeverityBadge = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return (
          <span className="text-[10px] uppercase font-bold bg-rose-100 text-rose-800 border border-rose-300 px-2 py-0.5 rounded-full flex items-center space-x-1">
            <AlertOctagon className="w-3 h-3" />
            <span>Critical</span>
          </span>
        );
      case 'error':
        return (
          <span className="text-[10px] uppercase font-bold bg-red-100 text-red-800 border border-red-300 px-2 py-0.5 rounded-full flex items-center space-x-1">
            <AlertTriangle className="w-3 h-3" />
            <span>Error</span>
          </span>
        );
      case 'warning':
        return (
          <span className="text-[10px] uppercase font-semibold bg-amber-100 text-amber-800 border border-amber-300 px-2 py-0.5 rounded-full flex items-center space-x-1">
            <AlertTriangle className="w-3 h-3" />
            <span>Warning</span>
          </span>
        );
      default:
        return (
          <span className="text-[10px] uppercase font-semibold bg-blue-100 text-blue-800 border border-blue-300 px-2 py-0.5 rounded-full flex items-center space-x-1">
            <Info className="w-3 h-3" />
            <span>Info</span>
          </span>
        );
    }
  };

  const getFindingTypePill = (desc: string) => {
    if (desc.includes('[Missing BIM Data]')) {
      return (
        <span className="text-[10px] font-semibold bg-blue-50 text-blue-800 border border-blue-200 px-2 py-0.5 rounded-md">
          Missing Model Data (BIM Omission)
        </span>
      );
    }
    if (desc.includes('[Geometry Defect]')) {
      return (
        <span className="text-[10px] font-semibold bg-amber-50 text-amber-800 border border-amber-300 px-2 py-0.5 rounded-md">
          Geometric / Model Defect
        </span>
      );
    }
    if (desc.includes('[Schema Violation]')) {
      return (
        <span className="text-[10px] font-semibold bg-rose-50 text-rose-800 border border-rose-200 px-2 py-0.5 rounded-md">
          Schema Violation
        </span>
      );
    }
    if (desc.includes('[Unsupported Entity]')) {
      return (
        <span className="text-[10px] font-semibold bg-purple-50 text-purple-800 border border-purple-200 px-2 py-0.5 rounded-md">
          Unsupported Entity (Skipped)
        </span>
      );
    }
    return null;
  };

  return (
    <div className={`bg-white rounded-xl border border-charcoal-200 p-5 shadow-xs space-y-5 ${className}`}>
      {/* Header & Completeness Meter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-charcoal-100 gap-3">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-emerald-800" />
            <h3 className="text-sm font-bold text-charcoal-900 tracking-tight">
              Model Completeness & Data Quality Audit
            </h3>
          </div>
          <p className="text-xs text-charcoal-500">
            {summary}
          </p>
        </div>

        {/* Completeness Badge */}
        <div className="flex items-center space-x-3 bg-stone-50 px-3 py-2 rounded-xl border border-charcoal-200/80 shrink-0">
          <div className="text-right">
            <span className="text-[10px] uppercase font-semibold text-charcoal-500 tracking-wider block">
              Completeness
            </span>
            <span className="font-mono text-sm font-bold text-emerald-900">
              {(data_completeness_ratio * 100).toFixed(0)}%
            </span>
          </div>
          <div className="w-9 h-9 rounded-full border-2 border-emerald-600 flex items-center justify-center font-mono text-xs font-bold text-emerald-800">
            ✓
          </div>
        </div>
      </div>

      {/* Severity Filter Tabs */}
      <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 text-xs">
        <span className="text-[11px] text-charcoal-500 flex items-center space-x-1 mr-1">
          <Filter className="w-3 h-3" />
          <span>Filter:</span>
        </span>
        <button
          onClick={() => setSelectedSeverity('all')}
          className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
            selectedSeverity === 'all'
              ? 'bg-charcoal-900 text-white shadow-2xs'
              : 'bg-stone-50 text-charcoal-600 border border-charcoal-200 hover:bg-stone-100'
          }`}
        >
          All ({findings.length})
        </button>
        {['critical', 'error', 'warning', 'info'].map((sev) => {
          const count = by_severity[sev] || 0;
          if (count === 0) return null;
          return (
            <button
              key={sev}
              onClick={() => setSelectedSeverity(sev)}
              className={`px-2.5 py-1 rounded-lg capitalize font-medium transition-colors ${
                selectedSeverity === sev
                  ? 'bg-charcoal-900 text-white shadow-2xs'
                  : 'bg-stone-50 text-charcoal-600 border border-charcoal-200 hover:bg-stone-100'
              }`}
            >
              {sev} ({count})
            </button>
          );
        })}
      </div>

      {/* Findings List */}
      <div className="space-y-3">
        {filteredFindings.length > 0 ? (
          filteredFindings.map((finding) => (
            <div
              key={finding.finding_id}
              className="bg-stone-50/60 rounded-xl border border-charcoal-200/80 p-4 text-xs space-y-2 hover:border-charcoal-300 transition-colors"
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex flex-wrap items-center gap-1.5">
                  <span className="font-mono text-[10px] font-bold text-charcoal-500 bg-white px-2 py-0.5 rounded border border-charcoal-200">
                    {finding.finding_id}
                  </span>
                  {getSeverityBadge(finding.severity)}
                  {getFindingTypePill(finding.description)}
                  <span className="text-[10px] uppercase font-semibold text-charcoal-600 bg-stone-100 px-2 py-0.5 rounded border border-stone-200">
                    {finding.category}
                  </span>
                </div>
              </div>

              <h4 className="text-xs font-bold text-charcoal-900">
                {finding.description}
              </h4>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] text-charcoal-600">
                <div>
                  <strong className="text-charcoal-800">Evidence:</strong> {finding.evidence}
                </div>
                <div>
                  <strong className="text-charcoal-800">Limitation:</strong> {finding.limitation}
                </div>
              </div>

              {finding.affected_element_ids.length > 0 && (
                <div className="flex flex-wrap items-center gap-1 text-[10px] text-charcoal-500 pt-1">
                  <strong className="text-charcoal-600">Affected Elements:</strong>
                  {finding.affected_element_ids.slice(0, 6).map((id) => (
                    <button
                      key={id}
                      onClick={() => onSelectElement && onSelectElement(id)}
                      className="font-mono bg-white hover:bg-charcoal-100 text-charcoal-700 px-1.5 py-0.5 rounded border border-charcoal-200"
                    >
                      {id}
                    </button>
                  ))}
                  {finding.affected_element_ids.length > 6 && (
                    <span>+{finding.affected_element_ids.length - 6} more</span>
                  )}
                </div>
              )}

              <div className="bg-white rounded-lg p-2.5 border border-charcoal-200 text-[11px] text-emerald-950 flex items-start space-x-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700 shrink-0 mt-0.5" />
                <div>
                  <strong>Recommended Action:</strong> {finding.recommended_action}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="p-6 text-center text-charcoal-500 text-xs">
            No findings match the selected severity filter.
          </div>
        )}
      </div>
    </div>
  );
};
