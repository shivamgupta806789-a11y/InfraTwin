import React from 'react';
import { RefreshCw, AlertTriangle, Radio } from 'lucide-react';
import { ApiHealthResponse } from '../types/recommendations';

interface ApiStatusProps {
  status: 'connected' | 'disconnected' | 'checking';
  healthData: ApiHealthResponse | null;
  errorMessage?: string | null;
  onRetry: () => void;
  className?: string;
}

export const ApiStatus: React.FC<ApiStatusProps> = ({
  status,
  healthData,
  errorMessage,
  onRetry,
  className = '',
}) => {
  return (
    <div className={`flex items-center space-x-2 text-xs ${className}`}>
      {status === 'connected' ? (
        <div className="flex items-center space-x-1.5 bg-emerald-50 text-emerald-800 border border-emerald-200 px-2.5 py-1 rounded-full">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="font-medium">Backend Connected</span>
          {healthData && (
            <span className="text-[10px] text-emerald-700/80 border-l border-emerald-200 pl-1.5 ml-1">
              v{healthData.version}
            </span>
          )}
        </div>
      ) : status === 'checking' ? (
        <div className="flex items-center space-x-1.5 bg-amber-50 text-amber-800 border border-amber-200 px-2.5 py-1 rounded-full">
          <Radio className="w-3 h-3 animate-spin text-amber-600" />
          <span className="font-medium">Checking API...</span>
        </div>
      ) : (
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1.5 bg-red-50 text-red-800 border border-red-200 px-2.5 py-1 rounded-full" title={errorMessage || 'Backend server is offline'}>
            <AlertTriangle className="w-3 h-3 text-red-600" />
            <span className="font-medium">Backend Offline</span>
          </div>
          <button
            onClick={onRetry}
            className="flex items-center space-x-1 text-charcoal-600 hover:text-charcoal-900 bg-white border border-charcoal-200 hover:border-charcoal-300 px-2 py-1 rounded-full transition-colors shadow-2xs text-[11px]"
            title="Retry connecting to FastAPI backend"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Retry</span>
          </button>
        </div>
      )}
    </div>
  );
};
