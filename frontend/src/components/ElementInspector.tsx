import React from 'react';
import { BuildingElement, IntelligenceFinding } from '../types/digital_twin';
import {
  Box,
  Layers,
  Copy,
  Check,
  ShieldCheck,
  Tag,
  Network,
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle2,
  FolderTree,
} from 'lucide-react';

interface ElementInspectorProps {
  element: BuildingElement | null;
  findings?: IntelligenceFinding[];
  onClose: () => void;
  className?: string;
}

export const ElementInspector: React.FC<ElementInspectorProps> = ({
  element,
  findings = [],
  onClose,
  className = '',
}) => {
  const [copied, setCopied] = React.useState(false);

  if (!element) return null;

  const handleCopyGuid = () => {
    if (element.source_global_id) {
      navigator.clipboard.writeText(element.source_global_id);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const psetEntries = Object.entries(element.source_properties || {});

  // Find findings specifically affecting this element
  const elementFindings = findings.filter(
    (f) =>
      f.affected_element_id === element.element_id ||
      (element.source_global_id && f.affected_global_id === element.source_global_id)
  );

  const classifications = element.classifications || {};
  const classificationEntries = Object.entries(classifications);

  const relationships = element.relationships || {};
  const hasRelationships =
    Boolean(relationships.hosted_in) ||
    Boolean(relationships.hosts && relationships.hosts.length > 0) ||
    Boolean(relationships.connected_to && relationships.connected_to.length > 0);

  return (
    <div
      className={`bg-white rounded-xl border border-charcoal-200 p-4 shadow-lg text-xs space-y-4 max-h-[85vh] overflow-y-auto ${className}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between pb-3 border-b border-charcoal-100">
        <div className="space-y-1">
          <div className="flex items-center space-x-2">
            <span className="font-mono text-[10px] font-semibold bg-charcoal-900 text-white px-2 py-0.5 rounded">
              {element.element_type}
            </span>
            <span
              className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${
                element.confidence_status === 'imported'
                  ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                  : 'bg-amber-50 text-amber-800 border border-amber-200'
              }`}
            >
              {element.confidence_status}
            </span>
          </div>
          <h3 className="text-sm font-bold text-charcoal-900 tracking-tight">
            {element.name}
          </h3>
          <p className="text-[11px] text-charcoal-500">
            Internal ID: <span className="font-mono">{element.element_id}</span>
          </p>
        </div>
        <button
          onClick={onClose}
          className="text-charcoal-400 hover:text-charcoal-700 p-1 rounded-md hover:bg-charcoal-50 font-bold"
          title="Close Inspector"
        >
          ✕
        </button>
      </div>

      {/* Intelligence & Risk Findings Banner */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[10px] uppercase font-semibold text-charcoal-500 tracking-wider flex items-center space-x-1">
            <AlertCircle className="w-3.5 h-3.5 text-charcoal-600" />
            <span>Associated Risk & Quality Findings</span>
          </span>
          <span
            className={`text-[10px] font-bold px-2 py-0.2 rounded-full ${
              elementFindings.length > 0
                ? 'bg-rose-100 text-rose-800 border border-rose-200'
                : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
            }`}
          >
            {elementFindings.length} {elementFindings.length === 1 ? 'Finding' : 'Findings'}
          </span>
        </div>

        {elementFindings.length > 0 ? (
          <div className="space-y-2.5">
            {elementFindings.map((finding) => (
              <div
                key={finding.finding_id}
                className={`p-2.5 rounded-lg border text-[11px] space-y-1.5 ${
                  finding.severity === 'High'
                    ? 'bg-rose-50/70 border-rose-200 text-rose-950'
                    : finding.severity === 'Warning'
                    ? 'bg-amber-50/70 border-amber-200 text-amber-950'
                    : 'bg-sky-50/70 border-sky-200 text-sky-950'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-xs flex items-center space-x-1">
                    {finding.severity === 'High' ? (
                      <AlertCircle className="w-3.5 h-3.5 text-rose-600 shrink-0" />
                    ) : finding.severity === 'Warning' ? (
                      <AlertTriangle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
                    ) : (
                      <Info className="w-3.5 h-3.5 text-sky-600 shrink-0" />
                    )}
                    <span>{finding.title}</span>
                  </span>
                  <span
                    className={`text-[9px] uppercase font-bold px-1.5 py-0.5 rounded ${
                      finding.severity === 'High'
                        ? 'bg-rose-600 text-white'
                        : finding.severity === 'Warning'
                        ? 'bg-amber-600 text-white'
                        : 'bg-sky-600 text-white'
                    }`}
                  >
                    {finding.severity}
                  </span>
                </div>

                <p className="text-[11px] text-charcoal-700 leading-snug">
                  <strong className="text-charcoal-900">Why flagged:</strong> {finding.flagged_reason || finding.why_flagged}
                </p>

                {finding.evidence && (
                  <div className="bg-white/80 p-1.5 rounded border border-charcoal-200/50 text-[10px]">
                    <span className="font-semibold text-charcoal-600 block">Evidence:</span>
                    <span className="font-mono text-charcoal-700">{finding.evidence}</span>
                  </div>
                )}

                {finding.source_properties && Object.keys(finding.source_properties).length > 0 && (
                  <div className="bg-white/80 p-1.5 rounded border border-charcoal-200/50 text-[10px] space-y-0.5">
                    <span className="font-semibold text-charcoal-600 block">Source Properties:</span>
                    {Object.entries(finding.source_properties).map(([k, v]) => (
                      <div key={k} className="flex justify-between font-mono text-charcoal-700">
                        <span>{k}:</span>
                        <span className="font-medium">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                )}

                <div className="text-[10px] bg-white/60 p-1.5 rounded text-charcoal-700">
                  <strong className="text-charcoal-900">Action:</strong> {finding.recommended_action}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-2 rounded-lg bg-emerald-50/60 border border-emerald-200 flex items-center space-x-2 text-emerald-800 text-[11px]">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
            <span>No data-quality or geometry issues flagged for this element.</span>
          </div>
        )}
      </div>

      {/* GlobalId */}
      {element.source_global_id && (
        <div className="bg-stone-50 p-2.5 rounded-lg border border-charcoal-200/80 flex items-center justify-between">
          <div className="space-y-0.5 overflow-hidden pr-2">
            <span className="text-[10px] uppercase font-semibold text-charcoal-500 tracking-wider block">
              IFC GlobalId (STEP GUID)
            </span>
            <span className="font-mono text-xs text-charcoal-800 truncate block">
              {element.source_global_id}
            </span>
          </div>
          <button
            onClick={handleCopyGuid}
            className="p-1.5 rounded-md hover:bg-white text-charcoal-600 border border-charcoal-200 transition-colors shrink-0"
            title="Copy GUID"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      )}

      {/* Storey Association */}
      <div className="flex items-center justify-between p-2.5 bg-stone-50 rounded-lg border border-charcoal-200/80">
        <span className="text-charcoal-600 flex items-center space-x-1.5">
          <Layers className="w-3.5 h-3.5 text-charcoal-500" />
          <span>Building Storey:</span>
        </span>
        <span className="font-medium text-charcoal-900">
          {element.storey_name || 'Unassigned / Global'}
        </span>
      </div>

      {/* Classifications */}
      {classificationEntries.length > 0 && (
        <div className="space-y-1.5">
          <span className="text-[10px] uppercase font-semibold text-charcoal-500 tracking-wider flex items-center space-x-1">
            <FolderTree className="w-3.5 h-3.5 text-charcoal-500" />
            <span>Classifications</span>
          </span>
          <div className="grid grid-cols-1 gap-1">
            {classificationEntries.map(([k, v]) => (
              <div key={k} className="flex justify-between bg-stone-50 p-1.5 rounded border border-charcoal-100 text-[11px]">
                <span className="text-charcoal-500 font-mono text-[10px]">{k}:</span>
                <span className="font-medium text-charcoal-800 font-mono text-[10px]">{String(v)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Relationships */}
      {hasRelationships && (
        <div className="space-y-1.5">
          <span className="text-[10px] uppercase font-semibold text-charcoal-500 tracking-wider flex items-center space-x-1">
            <Network className="w-3.5 h-3.5 text-charcoal-500" />
            <span>BIM Topological Relationships</span>
          </span>
          <div className="space-y-1 text-[11px]">
            {relationships.hosted_in && (
              <div className="p-1.5 bg-stone-50 rounded border border-charcoal-100 flex items-center justify-between">
                <span className="text-charcoal-500">Hosted In (Host Wall):</span>
                <span className="font-mono font-medium text-charcoal-800">{relationships.hosted_in}</span>
              </div>
            )}
            {relationships.hosts && relationships.hosts.length > 0 && (
              <div className="p-1.5 bg-stone-50 rounded border border-charcoal-100 space-y-1">
                <span className="text-charcoal-500 block">
                  Hosts ({relationships.hosts.length} apertures/fillings):
                </span>
                <div className="flex flex-wrap gap-1">
                  {relationships.hosts.map((h: string, i: number) => (
                    <span key={i} className="font-mono text-[10px] bg-white px-1.5 py-0.5 rounded border border-charcoal-200 text-charcoal-700">
                      {h}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {relationships.connected_to && relationships.connected_to.length > 0 && (
              <div className="p-1.5 bg-stone-50 rounded border border-charcoal-100 space-y-1">
                <span className="text-charcoal-500 block">
                  Connected Elements ({relationships.connected_to.length}):
                </span>
                <div className="flex flex-wrap gap-1">
                  {relationships.connected_to.map((c: string, i: number) => (
                    <span key={i} className="font-mono text-[10px] bg-white px-1.5 py-0.5 rounded border border-charcoal-200 text-charcoal-700">
                      {c}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Geometric Quantities */}
      <div className="space-y-2">
        <span className="text-[10px] uppercase font-semibold text-charcoal-500 tracking-wider flex items-center space-x-1">
          <Box className="w-3.5 h-3.5" />
          <span>Geometric Dimensions</span>
        </span>
        <div className="grid grid-cols-2 gap-2 text-[11px]">
          {element.bounding_box && (
            <>
              <div className="bg-stone-50 p-2 rounded border border-charcoal-100">
                <span className="text-charcoal-500 block text-[10px]">Width (X):</span>
                <span className="font-mono font-semibold text-charcoal-800">{element.bounding_box.width} m</span>
              </div>
              <div className="bg-stone-50 p-2 rounded border border-charcoal-100">
                <span className="text-charcoal-500 block text-[10px]">Plan Depth (Y):</span>
                <span className="font-mono font-semibold text-charcoal-800">{element.bounding_box.height} m</span>
              </div>
              <div className="bg-stone-50 p-2 rounded border border-charcoal-100">
                <span className="text-charcoal-500 block text-[10px]">Height (Z):</span>
                <span className="font-mono font-semibold text-charcoal-800">{element.bounding_box.depth} m</span>
              </div>
              <div className="bg-stone-50 p-2 rounded border border-charcoal-100">
                <span className="text-charcoal-500 block text-[10px]">Bounding Volume:</span>
                <span className="font-mono font-semibold text-charcoal-800">
                  {element.quantity_estimates.approx_volume_m3 ||
                    (element.bounding_box.width * element.bounding_box.height * element.bounding_box.depth).toFixed(2)}{' '}
                  m³
                </span>
              </div>
            </>
          )}
          {element.geometry && (
            <div className="col-span-2 bg-stone-50 p-2 rounded border border-charcoal-100 flex justify-between text-[11px]">
              <span className="text-charcoal-500">Tessellated Mesh Complexity:</span>
              <span className="font-mono text-charcoal-700">
                {element.geometry.vertex_count} vertices | {element.geometry.face_count} faces
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Materials */}
      <div className="space-y-1.5">
        <span className="text-[10px] uppercase font-semibold text-charcoal-500 tracking-wider flex items-center space-x-1">
          <Tag className="w-3.5 h-3.5" />
          <span>Assigned Materials</span>
        </span>
        {element.materials.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {element.materials.map((mat, i) => (
              <span
                key={i}
                className="bg-emerald-50 text-emerald-800 border border-emerald-200 px-2 py-0.5 rounded text-[11px] font-medium"
              >
                {mat}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-[11px] text-amber-700 bg-amber-50 p-2 rounded border border-amber-200">
            No IfcMaterial assigned. Embodied carbon calculation requires material specification.
          </p>
        )}
      </div>

      {/* Property Sets (Psets) */}
      <div className="space-y-2 pt-2 border-t border-charcoal-100">
        <span className="text-[10px] uppercase font-semibold text-charcoal-500 tracking-wider block">
          Property Sets ({psetEntries.length} Psets)
        </span>
        {psetEntries.length > 0 ? (
          <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
            {psetEntries.map(([psetName, psetData]) => (
              <div
                key={psetName}
                className="bg-stone-50 p-2 rounded border border-charcoal-200/70 text-[11px] space-y-1"
              >
                <span className="font-semibold text-charcoal-800 block text-[10px] text-emerald-900">
                  {psetName}
                </span>
                {typeof psetData === 'object' && psetData !== null ? (
                  <div className="space-y-0.5">
                    {Object.entries(psetData).map(([k, v]) => (
                      <div key={k} className="flex justify-between text-charcoal-600">
                        <span className="font-mono text-[10px] text-charcoal-500">{k}:</span>
                        <span className="font-mono text-charcoal-900 font-medium">{String(v)}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <span className="text-charcoal-700">{String(psetData)}</span>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-[11px] text-charcoal-400 italic">No custom property sets defined on this element.</p>
        )}
      </div>

      {/* Provenance Footer */}
      <div className="pt-2 border-t border-charcoal-100 text-[10px] text-charcoal-400 flex items-center justify-between">
        <span className="flex items-center space-x-1">
          <ShieldCheck className="w-3 h-3 text-emerald-600" />
          <span>Extracted via {element.property_provenance.source || 'IfcOpenShell'}</span>
        </span>
        <span>ISO 10303-21 Native</span>
      </div>
    </div>
  );
};