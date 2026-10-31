import React, { useState, useRef } from 'react';
import {
  extractFloorplanApi,
  extractSampleFloorplanApi,
  ApiError,
} from '../lib/api';
import { FloorPlanExtractionResponse } from '../types/floorplan';
import {
  UploadCloud,
  FileImage,
  AlertCircle,
  Sparkles,
  X,
  RotateCw,
} from 'lucide-react';

interface FloorplanUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onExtractionSuccess: (
    extraction: FloorPlanExtractionResponse,
    initialParams: {
      floors: number;
      floorHeight: number;
      buildingType: string;
      roofType: 'flat' | 'parapet' | 'gable';
    }
  ) => void;
}

export const FloorplanUploadModal: React.FC<FloorplanUploadModalProps> = ({
  isOpen,
  onClose,
  onExtractionSuccess,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [progressMsg, setProgressMsg] = useState<string | null>(null);

  const [showAdvancedOverrides, setShowAdvancedOverrides] = useState(false);
  const [floors, setFloors] = useState<number>(2);
  const [floorHeightM, setFloorHeightM] = useState<number>(3.0);
  const [knownDimensionM, setKnownDimensionM] = useState<string>('');
  const [buildingType, setBuildingType] = useState<string>('Commercial');
  const [roofType, setRoofType] = useState<'flat' | 'parapet' | 'gable'>('parapet');

  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleProcessFile = async (file: File) => {
    setErrorMsg(null);
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['png', 'jpg', 'jpeg', 'pdf', 'webp'].includes(ext || '')) {
      setErrorMsg('Invalid file format. Please upload a PNG, JPG, or PDF architectural drawing.');
      return;
    }

    if (file.size > 25 * 1024 * 1024) {
      setErrorMsg('File exceeds 25MB maximum upload limit for local prototype processing.');
      return;
    }

    setIsProcessing(true);
    setProgressMsg(`Step 2: Ingesting ${file.name} & automatically extracting building geometry...`);

    try {
      const dim = knownDimensionM ? parseFloat(knownDimensionM) : undefined;
      const extraction = await extractFloorplanApi(file, dim);
      
      const autoFloors = extraction.floorplan.detected_storeys || floors;
      const autoHeight = extraction.floorplan.detected_floor_height_m || floorHeightM;
      const autoType = extraction.floorplan.detected_building_typology || buildingType;

      setProgressMsg(`Extracted ${extraction.summary.wall_count} walls, ${extraction.summary.room_count} rooms, and ${autoFloors} storeys!`);
      setTimeout(() => {
        setIsProcessing(false);
        onExtractionSuccess(extraction, {
          floors: autoFloors,
          floorHeight: autoHeight,
          buildingType: autoType,
          roofType,
        });
        onClose();
      }, 500);
    } catch (err: any) {
      setIsProcessing(false);
      setProgressMsg(null);
      if (err instanceof ApiError) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg('Failed to process floor plan drawing. Ensure image contains distinct architectural wall lines.');
      }
    }
  };

  const handleLoadSample = async (sampleType: string = 'commercial') => {
    setErrorMsg(null);
    setIsProcessing(true);
    setProgressMsg('Loading pre-packaged commercial architectural drawing fixture...');

    try {
      const extraction = await extractSampleFloorplanApi(sampleType);
      const autoFloors = extraction.floorplan.detected_storeys || floors;
      const autoHeight = extraction.floorplan.detected_floor_height_m || floorHeightM;
      const autoType = extraction.floorplan.detected_building_typology || buildingType;

      setProgressMsg(`Extracted ${extraction.summary.wall_count} walls and ${extraction.summary.room_count} rooms!`);
      setTimeout(() => {
        setIsProcessing(false);
        onExtractionSuccess(extraction, {
          floors: autoFloors,
          floorHeight: autoHeight,
          buildingType: autoType,
          roofType,
        });
        onClose();
      }, 500);
    } catch (err: any) {
      setIsProcessing(false);
      setProgressMsg(null);
      if (err instanceof ApiError) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg('Failed to load sample drawing fixture.');
      }
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleProcessFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-charcoal-950/60 backdrop-blur-xs overflow-y-auto">
      <div className="bg-white rounded-2xl border border-charcoal-200 max-w-lg w-full p-6 shadow-2xl space-y-5 animate-in fade-in duration-150 my-6">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-charcoal-100">
          <div className="flex items-center space-x-2">
            <div className="p-2 bg-stone-100 text-charcoal-900 rounded-lg border border-charcoal-200">
              <FileImage className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-charcoal-900 tracking-tight">
                2D Architectural Drawing to 3D BIM
              </h3>
              <p className="text-xs text-charcoal-500">
                Automatic Feature Extraction • Clarification Questions • 3D BIM Synthesis
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isProcessing}
            className="text-charcoal-400 hover:text-charcoal-700 p-1 rounded-md"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Workflow Guidance Strip */}
        <div className="bg-stone-50 border border-charcoal-200 p-2.5 rounded-lg text-[11px] text-charcoal-600 flex items-center justify-between">
          <span className="font-semibold text-charcoal-900">Step 1 of 7:</span>
          <span>Upload architectural plan, elevation, or colony layout</span>
        </div>

        {/* Upload Zone (Primary First Action) */}
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => !isProcessing && fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
            isDragging
              ? 'border-charcoal-900 bg-stone-100 scale-[1.01]'
              : 'border-charcoal-300 hover:border-charcoal-900 bg-stone-50/50 hover:bg-stone-50'
          } ${isProcessing ? 'pointer-events-none opacity-60' : ''}`}
        >
          <input
            type="file"
            ref={fileInputRef}
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                handleProcessFile(e.target.files[0]);
              }
            }}
            accept=".png,.jpg,.jpeg,.pdf,.webp,.dxf"
            className="hidden"
          />

          <div className="flex flex-col items-center justify-center space-y-2.5">
            <div className="p-3 bg-white rounded-full shadow-2xs border border-charcoal-200 text-charcoal-900">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <p className="text-xs font-bold text-charcoal-900">
                Click to upload or drag & drop architectural drawing
              </p>
              <p className="text-[11px] text-charcoal-500 font-mono">
                PDF, DXF, PNG, JPG, or JPEG (Max 25MB)
              </p>
            </div>
            <div className="flex flex-wrap items-center justify-center gap-1.5 pt-1">
              <span className="text-[10px] px-2 py-0.5 rounded bg-stone-100 text-charcoal-600 border border-charcoal-200">
                Floor Plans
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-stone-100 text-charcoal-600 border border-charcoal-200">
                Elevations
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-stone-100 text-charcoal-600 border border-charcoal-200">
                Colony / Site Layouts
              </span>
            </div>
          </div>
        </div>

        {/* Optional Manual Overrides Toggle */}
        <div className="border border-charcoal-200 rounded-xl overflow-hidden">
          <button
            type="button"
            onClick={() => setShowAdvancedOverrides(!showAdvancedOverrides)}
            className="w-full px-3.5 py-2 text-left bg-stone-50 hover:bg-stone-100 text-xs font-semibold text-charcoal-700 flex items-center justify-between transition-colors"
          >
            <span>Optional Manual Scale / Typology Overrides</span>
            <span className="text-[11px] font-normal text-charcoal-500">
              {showAdvancedOverrides ? 'Hide Overrides' : 'Auto-detection will infer if omitted'}
            </span>
          </button>

          {showAdvancedOverrides && (
            <div className="p-3.5 bg-white border-t border-charcoal-200 space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-semibold text-charcoal-700 block mb-1">
                    Storeys Override
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="50"
                    value={floors}
                    onChange={(e) => setFloors(parseInt(e.target.value) || 1)}
                    className="w-full bg-stone-50 border border-charcoal-200 rounded p-1.5 text-xs font-semibold"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-charcoal-700 block mb-1">
                    Floor Height (m)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="2.2"
                    max="6.0"
                    value={floorHeightM}
                    onChange={(e) => setFloorHeightM(parseFloat(e.target.value) || 3.0)}
                    className="w-full bg-stone-50 border border-charcoal-200 rounded p-1.5 text-xs font-semibold"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-charcoal-700 block mb-1">
                    Known Reference Width (m)
                  </label>
                  <input
                    type="number"
                    step="0.5"
                    placeholder="Auto-inferred if empty"
                    value={knownDimensionM}
                    onChange={(e) => setKnownDimensionM(e.target.value)}
                    className="w-full bg-stone-50 border border-charcoal-200 rounded p-1.5 text-xs font-semibold"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-charcoal-700 block mb-1">
                    Roof Geometry Type
                  </label>
                  <select
                    value={roofType}
                    onChange={(e) => setRoofType(e.target.value as any)}
                    className="w-full bg-stone-50 border border-charcoal-200 rounded p-1.5 text-xs font-semibold"
                  >
                    <option value="parapet">Parapet (Commercial Flat)</option>
                    <option value="flat">Flat Slab</option>
                    <option value="gable">Pitched Gable (22°)</option>
                  </select>
                </div>
                <div className="col-span-2">
                  <label className="text-[11px] font-semibold text-charcoal-700 block mb-1">
                    Typology Override
                  </label>
                  <select
                    value={buildingType}
                    onChange={(e) => setBuildingType(e.target.value)}
                    className="w-full bg-stone-50 border border-charcoal-200 rounded p-1.5 text-xs font-semibold"
                  >
                    <option value="Commercial">Commercial / Office</option>
                    <option value="Residential">Residential</option>
                    <option value="Educational">Educational</option>
                    <option value="Healthcare">Healthcare</option>
                  </select>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Progress or Error Banner */}
        {progressMsg && (
          <div className="bg-stone-100 border border-charcoal-300 p-3 rounded-xl flex items-center space-x-2 text-xs text-charcoal-900 animate-in fade-in">
            <RotateCw className="w-4 h-4 text-charcoal-900 animate-spin shrink-0" />
            <span>{progressMsg}</span>
          </div>
        )}

        {errorMsg && (
          <div className="bg-red-50 border border-red-200 p-3 rounded-xl flex items-start space-x-2 text-xs text-red-900 animate-in fade-in">
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-semibold">Processing Failed:</span>
              <p className="text-red-800">{errorMsg}</p>
            </div>
          </div>
        )}

        {/* 1-Click Sample Fixture Action */}
        <div className="pt-2 border-t border-charcoal-100 flex items-center justify-between">
          <div className="text-[11px] text-charcoal-500">
            No drawing file on hand?
          </div>
          <button
            onClick={() => handleLoadSample('commercial')}
            disabled={isProcessing}
            className="flex items-center space-x-1.5 text-xs text-charcoal-900 bg-stone-100 hover:bg-stone-200 font-semibold px-3 py-1.5 rounded-lg border border-charcoal-200 transition-colors shadow-2xs"
          >
            <Sparkles className="w-3.5 h-3.5 text-charcoal-700" />
            <span>Load Sample Commercial Plan</span>
          </button>
        </div>
      </div>
    </div>
  );
};
