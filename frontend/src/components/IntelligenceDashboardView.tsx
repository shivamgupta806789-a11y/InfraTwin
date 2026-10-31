import React, { useState } from 'react';
import { BuildingIntelligenceReport, IntelligenceFinding } from '../types/digital_twin';
import {
  AlertOctagon,
  AlertTriangle,
  Info,
  Layers,
  Boxes,
  CheckCircle2,
  Filter,
  Eye,
  Activity,
  SlidersHorizontal,
  Award,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

interface IntelligenceDashboardViewProps {
  report: BuildingIntelligenceReport | null;
  isLoading: boolean;
  onSelectElement?: (elementId: string) => void;
  onSelectFinding?: (finding: IntelligenceFinding) => void;
  onFilterCategory?: (category: string) => void;
  className?: string;
}

export const IntelligenceDashboardView: React.FC<IntelligenceDashboardViewProps> = ({
  report,
  isLoading,
  onSelectElement,
  onSelectFinding,
  onFilterCategory,
  className = '',
}) => {
  const [selectedSeverity, setSelectedSeverity] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [expandedRecId, setExpandedRecId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className={`bg-white rounded-xl border border-charcoal-200 p-12 text-center space-y-3 ${className}`}>
        <div className="w-8 h-8 border-2 border-charcoal-300 border-t-emerald-800 rounded-full animate-spin mx-auto" />
        <p className="text-xs text-charcoal-600 font-medium">Running deep building intelligence and risk analysis...</p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className={`bg-white rounded-xl border border-charcoal-200 p-8 text-center text-charcoal-500 text-xs ${className}`}>
        No building intelligence report available. Ingest an IFC digital twin to analyze elements and detect issues.
      </div>
    );
  }

  const {
    total_elements,
    element_counts_by_category,
    model_completeness_pct,
    findings_by_severity,
    storey_distribution,
    findings,
    summary,
  } = report;

  // Filter findings
  const filteredFindings = findings.filter((f) => {
    if (selectedSeverity !== 'all' && f.severity !== selectedSeverity) return false;
    if (selectedCategory !== 'all' && f.category !== selectedCategory) return false;
    if (searchTerm) {
      const q = searchTerm.toLowerCase();
      const matchTitle = f.title.toLowerCase().includes(q);
      const matchElem = f.affected_element_name.toLowerCase().includes(q) || (f.affected_global_id && f.affected_global_id.toLowerCase().includes(q));
      const matchReason = f.flagged_reason.toLowerCase().includes(q);
      if (!matchTitle && !matchElem && !matchReason) return false;
    }
    return true;
  });

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'High':
        return (
          <span className="text-[10px] font-bold uppercase tracking-wider bg-rose-50 text-rose-800 border border-rose-300 px-2 py-0.5 rounded-full flex items-center space-x-1 shrink-0">
            <AlertOctagon className="w-3 h-3 text-rose-600" />
            <span>High Risk</span>
          </span>
        );
      case 'Warning':
        return (
          <span className="text-[10px] font-semibold uppercase tracking-wider bg-amber-50 text-amber-800 border border-amber-300 px-2 py-0.5 rounded-full flex items-center space-x-1 shrink-0">
            <AlertTriangle className="w-3 h-3 text-amber-600" />
            <span>Warning</span>
          </span>
        );
      default:
        return (
          <span className="text-[10px] font-semibold uppercase tracking-wider bg-blue-50 text-blue-800 border border-blue-300 px-2 py-0.5 rounded-full flex items-center space-x-1 shrink-0">
            <Info className="w-3 h-3 text-blue-600" />
            <span>Information</span>
          </span>
        );
    }
  };

  const categories = ['all', 'property', 'material', 'connectivity', 'identifier', 'spatial', 'geometry'];

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Top Intelligence KPI Summary Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Total Elements */}
        <div className="bg-white p-4 rounded-xl border border-charcoal-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-charcoal-500">
            <span className="text-[10px] uppercase font-semibold tracking-wider">Total Elements</span>
            <Boxes className="w-4 h-4 text-charcoal-600" />
          </div>
          <div className="font-mono text-xl font-bold text-charcoal-900">{total_elements}</div>
          <p className="text-[10px] text-charcoal-500">{Object.keys(element_counts_by_category).length} IFC entity types</p>
        </div>

        {/* Model Completeness */}
        <div className="bg-white p-4 rounded-xl border border-charcoal-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-charcoal-500">
            <span className="text-[10px] uppercase font-semibold tracking-wider">Completeness</span>
            <Activity className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="font-mono text-xl font-bold text-emerald-800">{model_completeness_pct}%</div>
          <p className="text-[10px] text-charcoal-500">Valid geom, GUID & material</p>
        </div>

        {/* High Severity Findings */}
        <div className={`p-4 rounded-xl border shadow-2xs space-y-1 ${findings_by_severity['High'] > 0 ? 'bg-rose-50/50 border-rose-300' : 'bg-white border-charcoal-200'}`}>
          <div className="flex items-center justify-between text-rose-800">
            <span className="text-[10px] uppercase font-semibold tracking-wider">High Risk</span>
            <AlertOctagon className="w-4 h-4 text-rose-600" />
          </div>
          <div className="font-mono text-xl font-bold text-rose-900">{findings_by_severity['High'] || 0}</div>
          <p className="text-[10px] text-rose-700">Conflicts / collisions</p>
        </div>

        {/* Warning Findings */}
        <div className={`p-4 rounded-xl border shadow-2xs space-y-1 ${findings_by_severity['Warning'] > 0 ? 'bg-amber-50/50 border-amber-300' : 'bg-white border-charcoal-200'}`}>
          <div className="flex items-center justify-between text-amber-800">
            <span className="text-[10px] uppercase font-semibold tracking-wider">Warnings</span>
            <AlertTriangle className="w-4 h-4 text-amber-600" />
          </div>
          <div className="font-mono text-xl font-bold text-amber-900">{findings_by_severity['Warning'] || 0}</div>
          <p className="text-[10px] text-amber-700">Missing data / anomalies</p>
        </div>

        {/* Info Notices */}
        <div className="bg-white p-4 rounded-xl border border-charcoal-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-blue-700">
            <span className="text-[10px] uppercase font-semibold tracking-wider">Information</span>
            <Info className="w-4 h-4 text-blue-600" />
          </div>
          <div className="font-mono text-xl font-bold text-blue-900">{findings_by_severity['Information'] || 0}</div>
          <p className="text-[10px] text-charcoal-500">Advisory notes</p>
        </div>

        {/* Total Findings */}
        <div className="bg-white p-4 rounded-xl border border-charcoal-200 shadow-2xs space-y-1">
          <div className="flex items-center justify-between text-charcoal-500">
            <span className="text-[10px] uppercase font-semibold tracking-wider">Total Issues</span>
            <SlidersHorizontal className="w-4 h-4 text-charcoal-600" />
          </div>
          <div className="font-mono text-xl font-bold text-charcoal-900">{findings.length}</div>
          <p className="text-[10px] text-charcoal-500">Evaluated in model</p>
        </div>
      </div>

      {/* Summary Disclaimer Note */}
      <div className="bg-stone-50 border border-charcoal-200 rounded-xl p-3 text-xs text-charcoal-600 flex items-center justify-between gap-3">
        <p className="text-[11px] leading-relaxed">
          <strong>Intelligence Summary:</strong> {summary}
        </p>
        <span className="shrink-0 text-[10px] bg-white px-2 py-0.5 rounded border border-charcoal-200 text-charcoal-500 font-mono">
          Model-Derived (Zero Fake Data)
        </span>
      </div>

      {/* 2-Column Distribution Breakdown: Category & Storey (Material provenance moved to Quality Audit) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Breakdown */}
        <div className="bg-white rounded-xl border border-charcoal-200 p-4 shadow-2xs space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-charcoal-100">
            <div className="flex items-center space-x-2">
              <Boxes className="w-4 h-4 text-charcoal-700" />
              <h4 className="text-xs font-bold text-charcoal-900 uppercase tracking-wider">
                Category Distribution
              </h4>
            </div>
            <span className="text-[11px] font-mono text-charcoal-500">{total_elements} Elements</span>
          </div>

          <div className="space-y-2 text-xs">
            {Object.entries(element_counts_by_category).map(([cat, count]) => {
              const pct = ((count / Math.max(1, total_elements)) * 100).toFixed(1);
              return (
                <div
                  key={cat}
                  className="space-y-1 cursor-pointer hover:bg-stone-50 p-1 rounded transition-colors"
                  onClick={() => onFilterCategory?.(cat)}
                  title={`Filter 3D view to ${cat}`}
                >
                  <div className="flex items-center justify-between text-[11px]">
                    <span className="font-medium text-charcoal-800 hover:text-emerald-800">{cat}</span>
                    <span className="font-mono text-charcoal-500">{count} ({pct}%)</span>
                  </div>
                  <div className="w-full bg-stone-100 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-charcoal-800 h-1.5 rounded-full transition-all"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Storey Distribution */}
        <div className="bg-white rounded-xl border border-charcoal-200 p-4 shadow-2xs space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-charcoal-100">
            <div className="flex items-center space-x-2">
              <Layers className="w-4 h-4 text-blue-800" />
              <h4 className="text-xs font-bold text-charcoal-900 uppercase tracking-wider">
                Storey Distribution
              </h4>
            </div>
            <span className="text-[11px] font-mono text-charcoal-500">{storey_distribution.length} Levels</span>
          </div>

          <div className="space-y-2 text-xs">
            {storey_distribution.map((st) => (
              <div key={st.storey_id} className="space-y-1">
                <div className="flex items-center justify-between text-[11px]">
                  <span className="font-medium text-charcoal-800 truncate max-w-[170px]">
                    {st.storey_name}
                  </span>
                  <span className="font-mono text-charcoal-500">
                    {st.element_count} ({st.percentage}%)
                  </span>
                </div>
                <div className="w-full bg-stone-100 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-blue-700 h-1.5 rounded-full transition-all"
                    style={{ width: `${st.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="pt-2 border-t border-charcoal-100 text-[11px] text-charcoal-500 flex items-center justify-between">
            <span>Material Provenance & Bill of Materials:</span>
            <span className="text-emerald-800 font-semibold">Available in BIM Quality Audit tab</span>
          </div>
        </div>
      </div>

      {/* Evidence-Based Architectural & Sustainability Recommendations */}
      <div className="bg-white rounded-xl border border-charcoal-200 p-5 shadow-2xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-charcoal-100 gap-2">
          <div>
            <div className="flex items-center space-x-2">
              <Award className="w-4 h-4 text-emerald-800" />
              <h3 className="text-sm font-bold text-charcoal-900 tracking-tight">
                Evidence-Based Architectural & Energy Recommendations
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-200">
                {report.recommendations?.length || 0} Opportunities
              </span>
            </div>
            <p className="text-xs text-charcoal-500 mt-0.5">
              Derived from BIM envelope geometry, materials, WWR calculations, and documented engineering codes (No fabricated claims).
            </p>
          </div>
        </div>

        {(!report.recommendations || report.recommendations.length === 0) ? (
          <div className="p-8 text-center text-charcoal-500 text-xs border border-dashed border-charcoal-200 rounded-xl">
            No recommendations generated. Ensure building geometry and storeys are available in the model.
          </div>
        ) : (
          <div className="space-y-3">
            {report.recommendations.map((rec) => {
              const isExpanded = expandedRecId === rec.id;
              return (
                <div
                  key={rec.id}
                  className="p-4 rounded-xl border border-charcoal-200 hover:border-emerald-300 transition-all bg-white space-y-3 shadow-2xs"
                >
                  <div
                    onClick={() => setExpandedRecId(isExpanded ? null : rec.id)}
                    className="flex items-start justify-between cursor-pointer gap-3"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span
                          className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded border ${
                            rec.priority === 'high'
                              ? 'bg-rose-50 text-rose-800 border-rose-200'
                              : rec.priority === 'medium'
                              ? 'bg-amber-50 text-amber-800 border-amber-200'
                              : 'bg-stone-50 text-stone-700 border-stone-200'
                          }`}
                        >
                          {rec.priority} Priority
                        </span>
                        <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-stone-100 text-charcoal-600 border border-stone-200">
                          {rec.category.replace('_', ' ')}
                        </span>
                        <h4 className="text-xs font-bold text-charcoal-900">{rec.title}</h4>
                      </div>
                      <p className="text-xs text-charcoal-700 leading-relaxed">{rec.detected_issue}</p>
                    </div>

                    <button
                      type="button"
                      className="p-1 text-charcoal-400 hover:text-charcoal-700 rounded transition-colors shrink-0"
                    >
                      {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>
                  </div>

                  {/* Expanded Engineering Evidence & Benefit */}
                  {isExpanded && (
                    <div className="pt-3 border-t border-charcoal-100 grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      <div className="p-3 bg-stone-50 rounded-lg space-y-1 border border-charcoal-100">
                        <span className="text-[10px] uppercase font-bold text-charcoal-500 tracking-wider">
                          Supporting BIM Evidence
                        </span>
                        <p className="text-charcoal-800 text-[11px] leading-relaxed">
                          {rec.supporting_evidence}
                        </p>
                      </div>

                      <div className="p-3 bg-emerald-50/50 rounded-lg space-y-1 border border-emerald-100">
                        <span className="text-[10px] uppercase font-bold text-emerald-800 tracking-wider">
                          Proposed Intervention & Benefit
                        </span>
                        <p className="text-charcoal-800 text-[11px] leading-relaxed">
                          {rec.proposed_intervention} — <strong>{rec.expected_benefit}</strong>
                        </p>
                      </div>

                      <div className="p-3 bg-stone-50 rounded-lg space-y-1 border border-charcoal-100">
                        <span className="text-[10px] uppercase font-bold text-charcoal-500 tracking-wider">
                          Cost Estimate & Calculation Method
                        </span>
                        <p className="text-charcoal-900 font-mono text-[11px] font-semibold">
                          {rec.estimated_cost_inr ? `Approx ₹${rec.estimated_cost_inr.toLocaleString()}` : 'Custom Quotation'}
                        </p>
                        <p className="text-charcoal-500 text-[10px]">
                          Method: {rec.calculation_method}
                        </p>
                      </div>

                      <div className="p-3 bg-amber-50/50 rounded-lg space-y-1 border border-amber-200">
                        <span className="text-[10px] uppercase font-bold text-amber-800 tracking-wider flex items-center space-x-1">
                          <AlertTriangle className="w-3 h-3 text-amber-600" />
                          <span>Engineering Limitations</span>
                        </span>
                        <p className="text-charcoal-700 text-[11px] leading-relaxed">
                          {rec.limitations}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Issue Detection and Risk Analysis Section */}
      <div className="bg-white rounded-xl border border-charcoal-200 p-5 shadow-2xs space-y-4">
        {/* Header and Controls */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-charcoal-100 gap-3">
          <div>
            <h3 className="text-sm font-bold text-charcoal-900 tracking-tight flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-amber-700" />
              <span>Potential Design, Quality & Performance Concerns</span>
            </h3>
            <p className="text-xs text-charcoal-500">
              Showing {filteredFindings.length} of {findings.length} detected concerns. Click any issue to inspect and highlight in 3D.
            </p>
          </div>

          {/* Search Input */}
          <div className="w-full sm:w-64">
            <input
              type="text"
              placeholder="Search issues, elements, GUID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full text-xs px-3 py-1.5 rounded-lg border border-charcoal-200 focus:outline-none focus:ring-1 focus:ring-charcoal-800"
            />
          </div>
        </div>

        {/* Severity & Category Filters */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          {/* Severity filter buttons */}
          <div className="flex items-center space-x-1 border-r border-charcoal-200 pr-3">
            <span className="text-[11px] text-charcoal-500 flex items-center space-x-1 mr-1">
              <Filter className="w-3 h-3" />
              <span>Severity:</span>
            </span>
            {['all', 'High', 'Warning', 'Information'].map((sev) => {
              const count = sev === 'all' ? findings.length : (findings_by_severity[sev] || 0);
              return (
                <button
                  key={sev}
                  onClick={() => setSelectedSeverity(sev)}
                  className={`px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors ${
                    selectedSeverity === sev
                      ? 'bg-charcoal-900 text-white'
                      : 'bg-stone-50 text-charcoal-600 hover:bg-stone-100 border border-charcoal-200'
                  }`}
                >
                  {sev} ({count})
                </button>
              );
            })}
          </div>

          {/* Category filter buttons */}
          <div className="flex items-center space-x-1 overflow-x-auto">
            <span className="text-[11px] text-charcoal-500 mr-1">Category:</span>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-2 py-0.5 rounded capitalize text-[10px] font-medium transition-colors ${
                  selectedCategory === cat
                    ? 'bg-emerald-800 text-white'
                    : 'bg-stone-50 text-charcoal-600 hover:bg-stone-100 border border-charcoal-200'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        {/* Findings List */}
        <div className="space-y-3">
          {filteredFindings.length > 0 ? (
            filteredFindings.map((finding) => (
              <div
                key={finding.finding_id}
                className="bg-stone-50/70 hover:bg-stone-50 rounded-xl border border-charcoal-200 p-4 text-xs space-y-2.5 transition-colors"
              >
                {/* Finding Header */}
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-[10px] font-bold text-charcoal-500 bg-white px-2 py-0.5 rounded border border-charcoal-200">
                      {finding.finding_id}
                    </span>
                    {getSeverityBadge(finding.severity)}
                    <span className="text-[10px] uppercase font-semibold text-charcoal-600 bg-stone-100 px-2 py-0.5 rounded border border-stone-200">
                      {finding.category}
                    </span>
                    <span className="font-mono text-[10px] bg-charcoal-900 text-white px-1.5 py-0.5 rounded">
                      {finding.affected_element_type}
                    </span>
                  </div>

                  {/* 3D Highlight Button */}
                  <button
                    onClick={() => {
                      if (onSelectFinding) onSelectFinding(finding);
                      if (onSelectElement) onSelectElement(finding.affected_element_id);
                    }}
                    className="flex items-center space-x-1 text-[11px] font-semibold text-emerald-800 hover:text-emerald-950 bg-emerald-50 hover:bg-emerald-100 border border-emerald-300 px-2.5 py-1 rounded-md transition-colors"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>Locate & Highlight in 3D</span>
                  </button>
                </div>

                {/* Finding Title & Target Element */}
                <div>
                  <h4 className="text-xs font-bold text-charcoal-900">{finding.title}</h4>
                  <p className="text-[11px] text-charcoal-600 pt-0.5">
                    Target Element: <strong>{finding.affected_element_name}</strong> • Internal ID: <span className="font-mono">{finding.affected_element_id}</span>
                    {finding.affected_global_id && (
                      <span> • IFC GUID: <span className="font-mono">{finding.affected_global_id}</span></span>
                    )}
                  </p>
                </div>

                {/* Why Flagged & Evidence */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-[11px] text-charcoal-700 bg-white p-2.5 rounded-lg border border-charcoal-200/80">
                  <div>
                    <strong className="text-charcoal-900 block mb-0.5">Why Flagged:</strong>
                    <span>{finding.flagged_reason}</span>
                  </div>
                  <div>
                    <strong className="text-charcoal-900 block mb-0.5">Evidence & Properties:</strong>
                    <span>{finding.evidence}</span>
                  </div>
                </div>

                {/* Recommended Action */}
                <div className="bg-emerald-50/50 rounded-lg p-2.5 border border-emerald-200 text-[11px] text-emerald-950 flex items-start space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-700 shrink-0 mt-0.5" />
                  <div>
                    <strong>Recommended Next Action:</strong> {finding.recommended_action}
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="p-8 text-center text-charcoal-500 text-xs">
              No concerns match the active filter or search term.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
