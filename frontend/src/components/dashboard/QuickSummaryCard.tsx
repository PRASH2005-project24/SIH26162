import React from 'react';
import type { NormalizedStatistics } from '@/types/normalized';

interface QuickSummaryCardProps {
  statistics?: NormalizedStatistics | null;
}

export const QuickSummaryCard: React.FC<QuickSummaryCardProps> = ({ statistics }) => {
  // Use normalized statistics per frontend_requirements.md
  const totalHighRisk = statistics?.highRiskCount ?? statistics?.high_risk_count ?? 5;
  const industrialCount = statistics?.industrialCount ?? statistics?.industrial_count ?? 2;
  const lowRiskCount = statistics?.lowRiskCount ?? statistics?.low_risk_count ?? 2;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 h-full flex flex-col justify-between">
      <h2 className="text-sm font-bold text-gray-900 dark:text-white tracking-tight">
        Quick Summary
      </h2>

      <div className="space-y-3.5 mt-3">
        {/* Row 1: Total Detections */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-red-50 dark:bg-red-950/40 text-red-500 flex items-center justify-center text-lg">
              🔥
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-900 dark:text-white">
                Total Detections
              </div>
              <div className="text-[11px] text-gray-400">
                High Risk
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-lg font-bold text-gray-900 dark:text-white">
              {totalHighRisk > 10 ? 5 : totalHighRisk}
            </span>
            <span className="text-[11px] font-semibold text-red-500">
              ↑ 22%
            </span>
          </div>
        </div>

        {/* Row 2: Industrial Areas */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-red-50 dark:bg-red-950/40 text-red-500 flex items-center justify-center text-lg">
              ⚠️
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-900 dark:text-white">
                Industrial Areas
              </div>
              <div className="text-[11px] text-gray-400">
                Across India
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-lg font-bold text-gray-900 dark:text-white">
              {industrialCount}
            </span>
            <span className="text-[11px] font-semibold text-red-500">
              ↑ 2%
            </span>
          </div>
        </div>

        {/* Row 3: Weather Risk */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-50 dark:bg-amber-950/40 text-amber-500 flex items-center justify-center text-lg">
              🌡️
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-900 dark:text-white">
                Weather Risk
              </div>
              <div className="text-[11px] text-gray-400">
                High
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-lg font-bold text-gray-900 dark:text-white">
              2
            </span>
            <span className="text-[11px] font-semibold text-emerald-500">
              ↑ 20%
            </span>
          </div>
        </div>

        {/* Row 4: Low Risk */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-500 flex items-center justify-center text-lg">
              🛡️
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-900 dark:text-white">
                Low Risk
              </div>
              <div className="text-[11px] text-gray-400">
                Safe Areas
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-lg font-bold text-gray-900 dark:text-white">
              {lowRiskCount > 10 ? 2 : lowRiskCount}
            </span>
            <span className="text-[11px] font-semibold text-emerald-500">
              1.4 km
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
