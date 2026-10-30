import React, { useState, useRef } from 'react';
import { importIfcFileApi, ApiError } from '../lib/api';
import { UploadCloud, FileCode2, AlertCircle, Sparkles, X, CheckCircle2 } from 'lucide-react';

interface IfcUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportSuccess: (modelId: string) => void;
  onLoadSample: () => void;
}

export const IfcUploadModal: React.FC<IfcUploadModalProps> = ({
  isOpen,
  onClose,
  onImportSuccess,
  onLoadSample,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFileProcess = async (file: File) => {
    setErrorMsg(null);
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['ifc', 'ifcxml', 'ifczip'].includes(ext || '')) {
      setErrorMsg('Invalid file format. Please upload an official Industry Foundation Classes (.ifc) file.');
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      setErrorMsg('File exceeds 50MB maximum upload limit for local prototype processing.');
      return;
    }

    setIsUploading(true);
    setUploadProgress(`Parsing ${file.name} with IfcOpenShell...`);

    try {
      const summary = await importIfcFileApi(file);
      setUploadProgress(`Parsed ${summary.total_elements} BIM elements successfully!`);
      setTimeout(() => {
        setIsUploading(false);
        onImportSuccess(summary.model_id);
        onClose();
      }, 700);
    } catch (err: any) {
      setIsUploading(false);
      setUploadProgress(null);
      if (err instanceof ApiError) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg('Failed to process IFC file. Check that the file contains standard ISO 10303-21 STEP entities.');
      }
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileProcess(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-charcoal-950/60 backdrop-blur-xs">
      <div className="bg-white rounded-2xl border border-charcoal-200 max-w-lg w-full p-6 shadow-2xl space-y-5 animate-in fade-in duration-150">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-charcoal-100">
          <div className="flex items-center space-x-2">
            <div className="p-2 bg-emerald-50 text-emerald-800 rounded-lg border border-emerald-200">
              <FileCode2 className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-charcoal-900 tracking-tight">
                Import IFC Building Model
              </h3>
              <p className="text-xs text-charcoal-500">
                IFC4 & IFC2x3 OpenBIM CAD ingestion pipeline
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isUploading}
            className="text-charcoal-400 hover:text-charcoal-700 p-1 rounded-md"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Upload Zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => !isUploading && fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all flex flex-col items-center justify-center space-y-3 ${
            isDragging
              ? 'border-emerald-500 bg-emerald-50/50'
              : 'border-charcoal-300 hover:border-charcoal-400 bg-stone-50/50 hover:bg-stone-50'
          } ${isUploading ? 'pointer-events-none opacity-80' : ''}`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".ifc,.ifcxml,.ifczip"
            className="hidden"
            onChange={(e) => {
              if (e.target.files && e.target.files.length > 0) {
                handleFileProcess(e.target.files[0]);
              }
            }}
          />

          <div className="w-12 h-12 rounded-full bg-emerald-50 text-emerald-800 flex items-center justify-center border border-emerald-200">
            {isUploading ? (
              <div className="w-6 h-6 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin" />
            ) : (
              <UploadCloud className="w-6 h-6" />
            )}
          </div>

          <div>
            <p className="text-xs font-semibold text-charcoal-900">
              {isUploading ? 'Processing IFC Geometry...' : 'Click to upload or drag & drop IFC file'}
            </p>
            <p className="text-[11px] text-charcoal-500 mt-0.5">
              Supports IFC4 & IFC2x3 (.ifc, .ifcxml) up to 50MB
            </p>
          </div>

          {uploadProgress && (
            <p className="text-xs font-mono font-medium text-emerald-800 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200 flex items-center space-x-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>{uploadProgress}</span>
            </p>
          )}
        </div>

        {/* Error message */}
        {errorMsg && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-800 flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Fast Benchmarking Fallback: Load Sample IFC Twin */}
        <div className="bg-stone-50 rounded-xl p-3 border border-charcoal-200/80 flex items-center justify-between">
          <div className="space-y-0.5">
            <h4 className="text-xs font-semibold text-charcoal-900 flex items-center space-x-1">
              <Sparkles className="w-3.5 h-3.5 text-amber-600" />
              <span>Don't have an IFC file handy?</span>
            </h4>
            <p className="text-[11px] text-charcoal-500">
              Load our bundled demonstration digital twin (NetZero Innovation Center).
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              onLoadSample();
              onClose();
            }}
            disabled={isUploading}
            className="px-3 py-1.5 bg-charcoal-900 text-white rounded-lg text-xs font-medium hover:bg-charcoal-800 transition-colors shadow-2xs shrink-0"
          >
            Load Sample Twin
          </button>
        </div>

        {/* Privacy Note */}
        <p className="text-[10px] text-charcoal-400 text-center">
          Files are processed locally in safe temporary storage and never permanently stored or shared.
        </p>
      </div>
    </div>
  );
};
