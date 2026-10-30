import React from 'react';
import { formatINR } from '../lib/validation';
import { Wallet, AlertTriangle } from 'lucide-react';

interface BudgetSummaryProps {
  budget: number;
  totalSelectedCost: number;
  selectedCount: number;
  className?: string;
}

export const BudgetSummary: React.FC<BudgetSummaryProps> = ({
  budget,
  totalSelectedCost,
  selectedCount,
  className = '',
}) => {
  const remaining = budget - totalSelectedCost;
  const isOverBudget = remaining < 0;
  const percentUsed = budget > 0 ? Math.min(100, (totalSelectedCost / budget) * 100) : 0;

  return (
    <div className={`bg-white rounded-xl border border-charcoal-200 p-4 shadow-xs ${className}`}>
      <div className="flex items-center justify-between pb-3 border-b border-charcoal-100">
        <div className="flex items-center space-x-2">
          <Wallet className="w-4 h-4 text-charcoal-700" />
          <h3 className="text-xs font-semibold text-charcoal-900 uppercase tracking-wider">
            Budget & Capital Outlay
          </h3>
        </div>
        <span className="text-[11px] text-charcoal-500 font-medium">
          {selectedCount} intervention{selectedCount !== 1 ? 's' : ''} active
        </span>
      </div>

      {/* Numerical Metrics */}
      <div className="grid grid-cols-3 gap-2 mt-3 text-center">
        <div className="bg-stone-50 p-2.5 rounded-lg border border-charcoal-100">
          <span className="block text-[10px] text-charcoal-500 uppercase tracking-wider font-medium">
            Available Budget
          </span>
          <span className="font-mono text-xs sm:text-sm font-semibold text-charcoal-900">
            {formatINR(budget)}
          </span>
        </div>

        <div className="bg-stone-50 p-2.5 rounded-lg border border-charcoal-100">
          <span className="block text-[10px] text-charcoal-500 uppercase tracking-wider font-medium">
            Proposed Outlay
          </span>
          <span className={`font-mono text-xs sm:text-sm font-semibold ${
            isOverBudget ? 'text-rose-600' : 'text-charcoal-900'
          }`}>
            {formatINR(totalSelectedCost)}
          </span>
        </div>

        <div className={`p-2.5 rounded-lg border ${
          isOverBudget
            ? 'bg-rose-50 border-rose-200 text-rose-800'
            : 'bg-emerald-50 border-emerald-200 text-emerald-800'
        }`}>
          <span className="block text-[10px] uppercase tracking-wider font-medium opacity-80">
            {isOverBudget ? 'Deficit' : 'Remaining'}
          </span>
          <span className="font-mono text-xs sm:text-sm font-semibold">
            {formatINR(Math.abs(remaining))}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mt-3">
        <div className="flex justify-between text-[11px] text-charcoal-500 mb-1">
          <span>Budget Utilization</span>
          <span className="font-mono font-medium text-charcoal-700">
            {percentUsed.toFixed(0)}%
          </span>
        </div>
        <div className="w-full bg-stone-200 h-2 rounded-full overflow-hidden">
          <div
            className={`h-full transition-all duration-300 ${
              isOverBudget
                ? 'bg-rose-500'
                : percentUsed > 90
                ? 'bg-amber-500'
                : 'bg-emerald-600'
            }`}
            style={{ width: `${percentUsed}%` }}
          />
        </div>
      </div>

      {/* Over Budget Notice */}
      {isOverBudget && (
        <div className="mt-3 p-2 bg-rose-50 border border-rose-200 rounded-lg flex items-start space-x-2 text-[11px] text-rose-800">
          <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold">Budget Exceeded:</span> Current selections exceed your target budget by {formatINR(Math.abs(remaining))}. Consider removing lower-priority options or applying the backend-recommended package.
          </div>
        </div>
      )}
    </div>
  );
};
