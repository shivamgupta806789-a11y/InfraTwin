import React, { useState } from 'react';
import {
  FloorPlan2D,
  FloorPlan3DGenerateRequest,
  Wall2D,
  ClarificationQuestion,
} from '../types/floorplan';
import { generate3dFromFloorplanApi, ApiError } from '../lib/api';
import {
  Boxes,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  Eye,
  Sliders,
  X,
  Layers,
  Building,
  Plus,
  Trash2,
  HelpCircle,
  CheckCircle2,
} from 'lucide-react';

interface FloorplanCorrectionEditorProps {
  isOpen: boolean;
  onClose: () => void;
  floorplan: FloorPlan2D;
  previewOverlayBase64: string;
  summary: {
    wall_count: number;
    door_count: number;
    window_count: number;
    room_count: number;
    total_room_area_sqm: number;
    footprint_width_m: number;
    footprint_depth_m: number;
  };
  initialFloors?: number;
  initialFloorHeight?: number;
  initialBuildingType?: string;
  initialRoofType?: 'flat' | 'parapet' | 'gable';
  onGenerateSuccess: (modelId: string) => void;
}

export const FloorplanCorrectionEditor: React.FC<FloorplanCorrectionEditorProps> = ({
  isOpen,
  onClose,
  floorplan: initialFloorplan,
  previewOverlayBase64,
  summary,
  initialFloors = 2,
  initialFloorHeight = 3.0,
  initialBuildingType = 'Commercial',
  initialRoofType = 'parapet',
  onGenerateSuccess,
}) => {
  const [floorplan, setFloorplan] = useState<FloorPlan2D>(initialFloorplan);
  const [floors, setFloors] = useState<number>(initialFloorplan.detected_storeys || initialFloors);
  const [floorHeightM, setFloorHeightM] = useState<number>(initialFloorplan.detected_floor_height_m || initialFloorHeight);
  const [roofType, setRoofType] = useState<'flat' | 'parapet' | 'gable'>(initialRoofType);
  const [buildingType, setBuildingType] = useState<string>(initialFloorplan.detected_building_typology || initialBuildingType);
  const [buildingName, setBuildingName] = useState<string>('Extruded Digital Twin');

  const [clarifications, setClarifications] = useState<ClarificationQuestion[]>(
    initialFloorplan.clarification_questions || []
  );
  const [activeTab, setActiveTab] = useState<'preview' | 'clarifications' | 'walls' | 'openings' | '3d_settings'>(
    initialFloorplan.clarification_questions && initialFloorplan.clarification_questions.length > 0 ? 'clarifications' : 'preview'
  );
  const [isGenerating, setIsGenerating] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const pendingClarificationsCount = clarifications.filter((q) => q.status === 'pending').length;

  const handleAnswerClarification = (qId: string, answer: string) => {
    setClarifications((prev) =>
      prev.map((q) => (q.question_id === qId ? { ...q, user_answer: answer, status: 'confirmed' } : q))
    );

    const targetQ = clarifications.find((q) => q.question_id === qId);
    if (!targetQ) return;

    if (targetQ.field_key === 'floors') {
      const parsed = parseInt(answer);
      if (!isNaN(parsed) && parsed >= 1) setFloors(parsed);
    } else if (targetQ.field_key === 'floor_height_m') {
      const parsed = parseFloat(answer);
      if (!isNaN(parsed) && parsed >= 2.0) setFloorHeightM(parsed);
    } else if (targetQ.field_key === 'known_dimension_m') {
      const parsed = parseFloat(answer);
      if (!isNaN(parsed) && parsed > 0) {
        setFloorplan((prev) => ({
          ...prev,
          scale: { ...prev.scale, known_dimension_m: parsed },
          bounds_width_m: parsed,
        }));
      }
    }
  };

  // New wall state
  const [newWallStartX, setNewWallStartX] = useState<number>(0);
  const [newWallStartY, setNewWallStartY] = useState<number>(0);
  const [newWallEndX, setNewWallEndX] = useState<number>(5);
  const [newWallEndY, setNewWallEndY] = useState<number>(0);
  const [showAddWall, setShowAddWall] = useState(false);

  if (!isOpen) return null;

  const handleToggleWall = (wallId: string) => {
    setFloorplan((prev) => ({
      ...prev,
      walls: prev.walls.map((w) => (w.id === wallId ? { ...w, is_active: !w.is_active } : w)),
    }));
  };

  const handleToggleDoor = (doorId: string) => {
    setFloorplan((prev) => ({
      ...prev,
      doors: prev.doors.map((d) => (d.id === doorId ? { ...d, is_active: !d.is_active } : d)),
    }));
  };

  const handleToggleWindow = (winId: string) => {
    setFloorplan((prev) => ({
      ...prev,
      windows: prev.windows.map((w) => (w.id === winId ? { ...w, is_active: !w.is_active } : w)),
    }));
  };

  const handleAddManualWall = () => {
    const newId = `wall_user_${Date.now().toString().slice(-4)}`;
    const newWall: Wall2D = {
      id: newId,
      start: { x: Number(newWallStartX), y: Number(newWallStartY) },
      end: { x: Number(newWallEndX), y: Number(newWallEndY) },
      thickness_m: 0.2,
      confidence: 1.0,
      wall_type: 'interior',
      is_active: true,
    };
    setFloorplan((prev) => ({
      ...prev,
      walls: [...prev.walls, newWall],
    }));
    setShowAddWall(false);
  };

  const handleRemoveWall = (wallId: string) => {
    setFloorplan((prev) => ({
      ...prev,
      walls: prev.walls.filter((w) => w.id !== wallId),
    }));
  };

  const handleGenerate3D = async () => {
    setErrorMsg(null);
    setIsGenerating(true);

    try {
      const payload: FloorPlan3DGenerateRequest = {
        floorplan,
        floors: Math.max(1, Math.min(50, floors)),
        floor_height_m: Math.max(2.2, Math.min(8.0, floorHeightM)),
        building_type: buildingType,
        roof_type: roofType,
        building_name: buildingName,
      };

      const result = await generate3dFromFloorplanApi(payload);
      setIsGenerating(false);
      onGenerateSuccess(result.model_id);
      onClose();
    } catch (err: any) {
      setIsGenerating(false);
      if (err instanceof ApiError) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg('Failed to synthesize 3D building model. Check wall geometry.');
      }
    }
  };

  const activeWallsCount = floorplan.walls.filter((w) => w.is_active).length;
  const activeDoorsCount = floorplan.doors.filter((d) => d.is_active).length;
  const activeWindowsCount = floorplan.windows.filter((w) => w.is_active).length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-charcoal-950/70 backdrop-blur-xs overflow-y-auto">
      <div className="bg-white rounded-2xl border border-charcoal-200 max-w-4xl w-full p-6 shadow-2xl space-y-5 animate-in fade-in duration-150 my-6 max-h-[92vh] flex flex-col">
        {/* Modal Header */}
        <div className="flex items-center justify-between pb-4 border-b border-charcoal-100 shrink-0">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-emerald-50 text-emerald-800 rounded-lg border border-emerald-200 shadow-2xs">
              <Boxes className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-base font-bold text-charcoal-900 tracking-tight">
                  2D Floor Plan Review & 3D Synthesis
                </h3>
                <span className="text-[10px] font-semibold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded border border-emerald-200 flex items-center space-x-1">
                  <Sparkles className="w-3 h-3 text-emerald-600" />
                  <span>OpenCV Detection: {Math.round(floorplan.overall_confidence * 100)}%</span>
                </span>
              </div>
              <p className="text-xs text-charcoal-500">
                Review detected walls, doors, windows, and rooms. Correct any uncertain features before extruding into 3D.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isGenerating}
            className="text-charcoal-400 hover:text-charcoal-700 p-1 rounded-md"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Statistical Summary Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 bg-stone-50 p-3 rounded-xl border border-charcoal-200 text-xs shrink-0">
          <div>
            <div className="text-[10px] uppercase text-charcoal-500 font-semibold">Active Walls</div>
            <div className="font-bold text-charcoal-900 text-sm">{activeWallsCount} / {floorplan.walls.length}</div>
          </div>
          <div>
            <div className="text-[10px] uppercase text-charcoal-500 font-semibold">Openings</div>
            <div className="font-bold text-charcoal-900 text-sm">{activeDoorsCount} Doors • {activeWindowsCount} Windows</div>
          </div>
          <div>
            <div className="text-[10px] uppercase text-charcoal-500 font-semibold">Enclosed Rooms</div>
            <div className="font-bold text-charcoal-900 text-sm">{floorplan.rooms.length} Rooms ({summary.total_room_area_sqm} m²)</div>
          </div>
          <div>
            <div className="text-[10px] uppercase text-charcoal-500 font-semibold">Footprint Bounds</div>
            <div className="font-bold text-charcoal-900 text-sm">{floorplan.bounds_width_m}m × {floorplan.bounds_depth_m}m</div>
          </div>
          <div>
            <div className="text-[10px] uppercase text-charcoal-500 font-semibold">Scale Ratio</div>
            <div className="font-bold text-charcoal-900 text-sm">{floorplan.scale.pixels_per_meter} px/m ({floorplan.scale.method})</div>
          </div>
        </div>

        {/* Warnings Banner if any */}
        {floorplan.warnings && floorplan.warnings.length > 0 && (
          <div className="bg-amber-50 border border-amber-200 text-amber-900 text-xs p-2.5 rounded-lg flex items-start space-x-2 shrink-0">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div className="space-y-0.5">
              <span className="font-semibold">Detection Calibration Notes:</span>
              <ul className="list-disc list-inside text-[11px] text-amber-800">
                {floorplan.warnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Navigation Tabs */}
        <div className="flex items-center space-x-2 border-b border-charcoal-200 pb-2 text-xs shrink-0">
          <button
            onClick={() => setActiveTab('preview')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
              activeTab === 'preview'
                ? 'bg-charcoal-900 text-white shadow-2xs'
                : 'text-charcoal-600 hover:text-charcoal-900 bg-stone-100'
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Detection Overlay</span>
          </button>
          <button
            onClick={() => setActiveTab('clarifications')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
              activeTab === 'clarifications'
                ? 'bg-charcoal-900 text-white shadow-2xs'
                : 'text-charcoal-600 hover:text-charcoal-900 bg-stone-100'
            }`}
          >
            <HelpCircle className="w-3.5 h-3.5 text-amber-500" />
            <span>Clarifications</span>
            {pendingClarificationsCount > 0 && (
              <span className="ml-1 text-[10px] bg-amber-500 text-charcoal-950 font-bold px-1.5 py-0.2 rounded-full">
                {pendingClarificationsCount}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('walls')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
              activeTab === 'walls'
                ? 'bg-charcoal-900 text-white shadow-2xs'
                : 'text-charcoal-600 hover:text-charcoal-900 bg-stone-100'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Wall Segments ({activeWallsCount})</span>
          </button>
          <button
            onClick={() => setActiveTab('openings')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
              activeTab === 'openings'
                ? 'bg-charcoal-900 text-white shadow-2xs'
                : 'text-charcoal-600 hover:text-charcoal-900 bg-stone-100'
            }`}
          >
            <Sliders className="w-3.5 h-3.5" />
            <span>Doors & Windows ({activeDoorsCount + activeWindowsCount})</span>
          </button>
          <button
            onClick={() => setActiveTab('3d_settings')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg font-semibold transition-all ${
              activeTab === '3d_settings'
                ? 'bg-emerald-800 text-white shadow-2xs'
                : 'text-charcoal-600 hover:text-charcoal-900 bg-stone-100'
            }`}
          >
            <Building className="w-3.5 h-3.5" />
            <span>3D Parameters</span>
          </button>
        </div>

        {/* Tab Body */}
        <div className="flex-1 overflow-y-auto space-y-4 min-h-[260px]">
          {/* TAB 1: VISUAL DETECTION OVERLAY */}
          {activeTab === 'preview' && (
            <div className="space-y-3">
              <div className="relative border border-charcoal-200 rounded-xl overflow-hidden bg-charcoal-900/5 max-h-[380px] flex items-center justify-center p-2">
                {previewOverlayBase64 ? (
                  <img
                    src={previewOverlayBase64}
                    alt="Detected Floorplan Overlay"
                    className="max-h-[360px] max-w-full object-contain rounded-lg shadow-xs"
                  />
                ) : (
                  <div className="p-8 text-center text-charcoal-400 text-xs">No overlay preview available</div>
                )}
              </div>
              <div className="flex items-center justify-between text-[11px] text-charcoal-600 bg-stone-50 p-2.5 rounded-lg border border-charcoal-200">
                <div className="flex items-center space-x-4">
                  <span className="flex items-center space-x-1">
                    <span className="w-3 h-3 bg-slate-800 rounded-xs inline-block" />
                    <span>Walls</span>
                  </span>
                  <span className="flex items-center space-x-1">
                    <span className="w-3 h-3 bg-amber-500 rounded-full inline-block" />
                    <span>Doors</span>
                  </span>
                  <span className="flex items-center space-x-1">
                    <span className="w-3 h-3 bg-sky-400 rounded-full inline-block" />
                    <span>Windows</span>
                  </span>
                  <span className="flex items-center space-x-1">
                    <span className="w-3 h-3 bg-emerald-200 rounded-xs inline-block" />
                    <span>Enclosed Rooms</span>
                  </span>
                </div>
                <span className="text-charcoal-500 italic">Toggle individual elements in the tabs above</span>
              </div>
            </div>
          )}

          {/* TAB: TARGETED CLARIFICATION QUESTIONS */}
          {activeTab === 'clarifications' && (
            <div className="space-y-3">
              <div className="p-3 bg-stone-50 border border-charcoal-200 rounded-xl space-y-1">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-charcoal-900">
                    Targeted Ambiguity & Measurement Clarification
                  </span>
                  <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-stone-200 text-charcoal-700">
                    {clarifications.filter((q) => q.status === 'confirmed').length} / {clarifications.length} Resolved
                  </span>
                </div>
                <p className="text-[11px] text-charcoal-600">
                  InfraTwinAI detects geometric ambiguities and asks for targeted clarification rather than silently inventing measurements.
                </p>
              </div>

              {clarifications.length === 0 ? (
                <div className="p-8 text-center text-xs text-charcoal-500 border border-dashed border-charcoal-200 rounded-xl">
                  No pending uncertainties detected. All key dimensions and elements extracted with high confidence.
                </div>
              ) : (
                <div className="space-y-3">
                  {clarifications.map((q) => (
                    <div
                      key={q.question_id}
                      className={`p-4 rounded-xl border transition-all space-y-2.5 ${
                        q.status === 'confirmed'
                          ? 'bg-emerald-50/40 border-emerald-300'
                          : 'bg-white border-charcoal-200 shadow-2xs'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="space-y-1">
                          <div className="flex items-center space-x-2">
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-stone-100 text-charcoal-700 border border-charcoal-200">
                              {q.question_id}
                            </span>
                            <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200">
                              Confidence: {Math.round(q.confidence * 100)}%
                            </span>
                            {q.status === 'confirmed' && (
                              <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center space-x-1">
                                <CheckCircle2 className="w-3 h-3 text-emerald-700" />
                                <span>Confirmed</span>
                              </span>
                            )}
                          </div>
                          <h4 className="text-xs font-bold text-charcoal-900">{q.question_text}</h4>
                        </div>
                      </div>

                      <div className="p-2.5 bg-stone-50 rounded-lg border border-charcoal-100 text-[11px] text-charcoal-600 space-y-1">
                        <p>
                          <span className="font-semibold text-charcoal-700">Reason for asking:</span> {q.reason}
                        </p>
                        {q.detected_value && (
                          <p>
                            <span className="font-semibold text-charcoal-700">Current Extracted / Inferred Value:</span>{' '}
                            <span className="font-mono font-medium text-charcoal-900">{q.detected_value}</span>
                          </p>
                        )}
                      </div>

                      {/* Suggested quick answer options */}
                      {q.suggested_options && q.suggested_options.length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5 pt-1">
                          <span className="text-[10px] font-semibold text-charcoal-500 mr-1">Suggested:</span>
                          {q.suggested_options.map((opt) => (
                            <button
                              key={opt}
                              type="button"
                              onClick={() => handleAnswerClarification(q.question_id, opt)}
                              className={`text-[11px] px-2.5 py-1 rounded-md border font-medium transition-colors ${
                                q.user_answer === opt
                                  ? 'bg-charcoal-900 text-white border-charcoal-900'
                                  : 'bg-white hover:bg-stone-100 text-charcoal-700 border-charcoal-200'
                              }`}
                            >
                              {opt}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 2: WALL SEGMENTS LIST */}
          {activeTab === 'walls' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-charcoal-600 font-medium">
                  Review detected walls. Uncheck any false lines or add missing partitions.
                </span>
                <button
                  onClick={() => setShowAddWall(!showAddWall)}
                  className="flex items-center space-x-1 text-xs bg-stone-100 hover:bg-stone-200 text-charcoal-800 px-2.5 py-1 rounded-md font-semibold border border-charcoal-200"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>{showAddWall ? 'Cancel' : 'Add Manual Wall'}</span>
                </button>
              </div>

              {/* Add Manual Wall Panel */}
              {showAddWall && (
                <div className="bg-stone-50 border border-charcoal-200 p-3 rounded-xl grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs">
                  <div>
                    <label className="text-[10px] text-charcoal-500 font-semibold">Start X (m)</label>
                    <input
                      type="number"
                      step="0.5"
                      value={newWallStartX}
                      onChange={(e) => setNewWallStartX(parseFloat(e.target.value) || 0)}
                      className="w-full bg-white border border-charcoal-200 rounded p-1 text-xs"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-charcoal-500 font-semibold">Start Y (m)</label>
                    <input
                      type="number"
                      step="0.5"
                      value={newWallStartY}
                      onChange={(e) => setNewWallStartY(parseFloat(e.target.value) || 0)}
                      className="w-full bg-white border border-charcoal-200 rounded p-1 text-xs"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-charcoal-500 font-semibold">End X (m)</label>
                    <input
                      type="number"
                      step="0.5"
                      value={newWallEndX}
                      onChange={(e) => setNewWallEndX(parseFloat(e.target.value) || 0)}
                      className="w-full bg-white border border-charcoal-200 rounded p-1 text-xs"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-charcoal-500 font-semibold">End Y (m)</label>
                    <input
                      type="number"
                      step="0.5"
                      value={newWallEndY}
                      onChange={(e) => setNewWallEndY(parseFloat(e.target.value) || 0)}
                      className="w-full bg-white border border-charcoal-200 rounded p-1 text-xs"
                    />
                  </div>
                  <div className="flex items-end">
                    <button
                      onClick={handleAddManualWall}
                      className="w-full bg-emerald-700 hover:bg-emerald-800 text-white font-semibold py-1 rounded text-xs shadow-2xs"
                    >
                      Add Wall
                    </button>
                  </div>
                </div>
              )}

              {/* Walls Table */}
              <div className="border border-charcoal-200 rounded-xl overflow-hidden divide-y divide-charcoal-100 text-xs">
                {floorplan.walls.map((wall) => {
                  const len = Math.hypot(wall.end.x - wall.start.x, wall.end.y - wall.start.y).toFixed(2);
                  return (
                    <div
                      key={wall.id}
                      className={`flex items-center justify-between p-2.5 transition-colors ${
                        wall.is_active ? 'bg-white' : 'bg-stone-100/60 opacity-60'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={wall.is_active}
                          onChange={() => handleToggleWall(wall.id)}
                          className="rounded text-emerald-700 focus:ring-emerald-500"
                        />
                        <div>
                          <div className="font-semibold text-charcoal-900 flex items-center space-x-2">
                            <span>{wall.id}</span>
                            <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-stone-100 text-charcoal-700 border border-stone-200">
                              {wall.wall_type}
                            </span>
                            <span className={`text-[10px] font-mono px-1.5 py-0.2 rounded border ${
                              wall.detection_status === 'USER_CONFIRMED' ? 'bg-emerald-50 text-emerald-800 border-emerald-200' :
                              wall.detection_status === 'UNCERTAIN' ? 'bg-amber-50 text-amber-800 border-amber-200' :
                              'bg-stone-50 text-charcoal-600 border-charcoal-200'
                            }`}>
                              {wall.detection_status || 'DETECTED'}
                            </span>
                          </div>
                          <div className="text-[11px] text-charcoal-500 font-mono">
                            ({wall.start.x}, {wall.start.y}) → ({wall.end.x}, {wall.end.y}) • Length: {len}m • Thick: {wall.thickness_m}m
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center space-x-2">
                        <span className="text-[10px] text-charcoal-400">
                          {Math.round(wall.confidence * 100)}% conf
                        </span>
                        <button
                          onClick={() => handleRemoveWall(wall.id)}
                          className="text-charcoal-400 hover:text-red-600 p-1 rounded"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 3: DOORS AND WINDOWS */}
          {activeTab === 'openings' && (
            <div className="space-y-4">
              {/* Doors Section */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-charcoal-900 uppercase tracking-wider flex items-center space-x-1.5">
                  <span className="w-2.5 h-2.5 bg-amber-500 rounded-full inline-block" />
                  <span>Detected Doors ({activeDoorsCount})</span>
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                  {floorplan.doors.map((door) => (
                    <div
                      key={door.id}
                      className={`p-2.5 rounded-xl border flex items-center justify-between ${
                        door.is_active
                          ? 'bg-amber-500/5 border-amber-300'
                          : 'bg-stone-100 border-charcoal-200 opacity-60'
                      }`}
                    >
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={door.is_active}
                          onChange={() => handleToggleDoor(door.id)}
                          className="rounded text-amber-600 focus:ring-amber-500"
                        />
                        <div>
                          <div className="font-semibold text-charcoal-900 flex items-center space-x-1.5">
                            <span>{door.id}</span>
                            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-amber-50 text-amber-800 border border-amber-200">
                              {door.detection_status || 'DETECTED'}
                            </span>
                          </div>
                          <div className="text-[11px] text-charcoal-500 font-mono">
                            Pos: ({door.position.x}, {door.position.y}) • Width: {door.width_m}m
                          </div>
                        </div>
                      </div>
                      <span className="text-[10px] text-charcoal-400">
                        {Math.round(door.confidence * 100)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Windows Section */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-charcoal-900 uppercase tracking-wider flex items-center space-x-1.5">
                  <span className="w-2.5 h-2.5 bg-sky-500 rounded-full inline-block" />
                  <span>Detected Windows ({activeWindowsCount})</span>
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                  {floorplan.windows.map((win) => (
                    <div
                      key={win.id}
                      className={`p-2.5 rounded-xl border flex items-center justify-between ${
                        win.is_active
                          ? 'bg-sky-500/5 border-sky-300'
                          : 'bg-stone-100 border-charcoal-200 opacity-60'
                      }`}
                    >
                      <div className="flex items-center space-x-2">
                        <input
                          type="checkbox"
                          checked={win.is_active}
                          onChange={() => handleToggleWindow(win.id)}
                          className="rounded text-sky-600 focus:ring-sky-500"
                        />
                        <div>
                          <div className="font-semibold text-charcoal-900 flex items-center space-x-1.5">
                            <span>{win.id}</span>
                            <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-sky-50 text-sky-800 border border-sky-200">
                              {win.detection_status || 'DETECTED'}
                            </span>
                          </div>
                          <div className="text-[11px] text-charcoal-500 font-mono">
                            Pos: ({win.position.x}, {win.position.y}) • {win.width_m}m × {win.height_m}m
                          </div>
                        </div>
                      </div>
                      <span className="text-[10px] text-charcoal-400">
                        {Math.round(win.confidence * 100)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: 3D EXTRUSION PARAMETERS */}
          {activeTab === '3d_settings' && (
            <div className="bg-stone-50 border border-charcoal-200 p-4 rounded-xl space-y-4 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="font-semibold text-charcoal-900 block mb-1">
                    Number of Storeys (Floors)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="50"
                    value={floors}
                    onChange={(e) => setFloors(parseInt(e.target.value) || 1)}
                    className="w-full bg-white border border-charcoal-200 rounded-lg p-2 text-sm font-semibold"
                  />
                  <span className="text-[11px] text-charcoal-500">
                    Floor plan footprint is stacked across {floors} levels.
                  </span>
                </div>

                <div>
                  <label className="font-semibold text-charcoal-900 block mb-1">
                    Floor-to-Floor Height (meters)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="2.2"
                    max="8.0"
                    value={floorHeightM}
                    onChange={(e) => setFloorHeightM(parseFloat(e.target.value) || 3.0)}
                    className="w-full bg-white border border-charcoal-200 rounded-lg p-2 text-sm font-semibold"
                  />
                  <span className="text-[11px] text-charcoal-500">
                    Total building height: {(floors * floorHeightM).toFixed(1)} meters.
                  </span>
                </div>

                <div>
                  <label className="font-semibold text-charcoal-900 block mb-1">
                    Roof Architecture Type
                  </label>
                  <select
                    value={roofType}
                    onChange={(e) => setRoofType(e.target.value as any)}
                    className="w-full bg-white border border-charcoal-200 rounded-lg p-2 text-xs font-semibold"
                  >
                    <option value="parapet">Parapet (Commercial Flat with 0.8m Perimeter Wall)</option>
                    <option value="flat">Flat Slab (Minimalist Overhang)</option>
                    <option value="gable">Pitched Gable (Residential 22° Roof Prism)</option>
                  </select>
                </div>

                <div>
                  <label className="font-semibold text-charcoal-900 block mb-1">
                    Building Typology
                  </label>
                  <select
                    value={buildingType}
                    onChange={(e) => setBuildingType(e.target.value)}
                    className="w-full bg-white border border-charcoal-200 rounded-lg p-2 text-xs font-semibold"
                  >
                    <option value="Commercial">Commercial / Office</option>
                    <option value="Residential">Residential Multi-Family</option>
                    <option value="Educational">Educational / Campus</option>
                    <option value="Healthcare">Healthcare Clinic</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="font-semibold text-charcoal-900 block mb-1">
                  Digital Twin Name
                </label>
                <input
                  type="text"
                  value={buildingName}
                  onChange={(e) => setBuildingName(e.target.value)}
                  className="w-full bg-white border border-charcoal-200 rounded-lg p-2 text-xs"
                />
              </div>
            </div>
          )}
        </div>

        {/* Error message */}
        {errorMsg && (
          <div className="bg-red-50 border border-red-200 p-2.5 rounded-lg text-red-900 text-xs flex items-center space-x-2 shrink-0">
            <AlertTriangle className="w-4 h-4 text-red-600 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Modal Footer */}
        <div className="flex items-center justify-between pt-3 border-t border-charcoal-100 shrink-0">
          <button
            onClick={onClose}
            disabled={isGenerating}
            className="text-xs text-charcoal-600 hover:text-charcoal-900 font-semibold px-3 py-2 rounded-lg"
          >
            Cancel
          </button>

          <button
            onClick={handleGenerate3D}
            disabled={isGenerating || activeWallsCount === 0}
            className="flex items-center space-x-2 bg-emerald-800 hover:bg-emerald-900 text-white font-semibold text-xs px-5 py-2.5 rounded-xl shadow-xs transition-colors disabled:opacity-50"
          >
            {isGenerating ? (
              <>
                <RotateCcw className="w-4 h-4 animate-spin text-emerald-300" />
                <span>Extruding 3D Meshes...</span>
              </>
            ) : (
              <>
                <Boxes className="w-4 h-4 text-emerald-300" />
                <span>Generate 3D Building ({floors} Storeys)</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
