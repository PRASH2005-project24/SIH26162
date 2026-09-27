import React from 'react';
import type { LandCoverBreakdown } from '@/types/normalized';

interface LandCoverCardProps {
  landCover?: LandCoverBreakdown | null;
  dominantLabel?: string | null;
}

export const LandCoverCard: React.FC<LandCoverCardProps> = ({
  landCover,
  dominantLabel,
}) => {
  const lc = landCover || {
    Built: 0,
    Trees: 0,
    Grass: 0,
    Crops: 0,
    Bare: 0,
    Water: 0,
    'Snow & ice': 0,
    'Flooded vegetation': 0,
    'Shrub & scrub': 0,
  };

  const legendItems = [
    { label: 'Built', percent: lc.Built || 0, color: '#ef4444' },
    { label: 'Trees', percent: lc.Trees || 0, color: '#22c55e' },
    { label: 'Crops', percent: lc.Crops || 0, color: '#f59e0b' },
    { label: 'Grass', percent: lc.Grass || 0, color: '#84cc16' },
    { label: 'Bare', percent: lc.Bare || 0, color: '#d97706' },
    { label: 'Water', percent: lc.Water || 0, color: '#3b82f6' },
    { label: 'Shrub', percent: lc['Shrub & scrub'] || 0, color: '#a855f7' },
  ].filter((item) => item.percent > 0);

  // Compute dominant if not provided
  let topLabel = dominantLabel || (landCover ? 'Built' : 'Not available');
  let topPercent = 0;
  Object.entries(lc).forEach(([k, v]) => {
    if (typeof v === 'number' && v > topPercent) {
      topPercent = v;
      topLabel = k;
    }
  });

  // Calculate SVG donut stroke dash arrays
  const radius = 40;
  const circumference = 2 * Math.PI * radius;

  let accumulatedPercent = 0;
  const donutSegments = legendItems.map((item) => {
    const strokeDasharray = `${(item.percent / 100) * circumference} ${circumference}`;
    const strokeDashoffset = -((accumulatedPercent / 100) * circumference);
    accumulatedPercent += item.percent;
    return {
      ...item,
      strokeDasharray,
      strokeDashoffset,
    };
  });

  return (
    <div className="bg-white/85 dark:bg-slate-900/70 backdrop-blur-md rounded-2xl p-5 shadow-xs border border-gray-200/80 dark:border-slate-800/80 flex flex-col justify-between">
      <div className="flex items-center justify-between">
        <div className="flex items-baseline gap-1.5">
          <h2 className="text-sm font-bold text-gray-900 dark:text-white tracking-tight">
            Land Cover
          </h2>
          <span className="text-[11px] font-medium text-gray-400">
            (Dynamic World GEE)
          </span>
        </div>
        <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-800">
          Google Earth Engine
        </span>
      </div>

      <div className="flex items-center justify-between gap-4 mt-2">
        {/* Donut Chart */}
        <div className="relative flex items-center justify-center flex-shrink-0 w-32 h-32">
          <svg className="w-32 h-32 transform -rotate-90" viewBox="0 0 100 100">
            {/* Background circle */}
            <circle
              cx="50"
              cy="50"
              r={radius}
              fill="transparent"
              stroke="#f3f4f6"
              strokeWidth="11"
              className="dark:stroke-gray-700"
            />
            {/* Colored segments */}
            {donutSegments.map((segment) => (
              <circle
                key={segment.label}
                cx="50"
                cy="50"
                r={radius}
                fill="transparent"
                stroke={segment.color}
                strokeWidth="11"
                strokeDasharray={segment.strokeDasharray}
                strokeDashoffset={segment.strokeDashoffset}
                strokeLinecap="butt"
              />
            ))}
          </svg>
          {/* Donut Center text */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-center px-1">
            <span className="text-xl font-extrabold text-gray-900 dark:text-white leading-none">
              {topPercent > 0 ? `${topPercent}%` : '--'}
            </span>
            <span className="text-[10px] font-semibold text-gray-400 mt-1 truncate max-w-[70px]">
              {topLabel}
            </span>
          </div>
        </div>

        {/* Legend */}
        <div className="flex-1 space-y-1.5 pl-2 max-h-36 overflow-y-auto">
          {legendItems.length > 0 ? (
            legendItems.map((item) => (
              <div key={item.label} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span
                    className="w-2 h-2 rounded-[2px] flex-shrink-0"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-gray-600 dark:text-gray-400 text-[11px]">
                    {item.label}
                  </span>
                </div>
                <span className="font-semibold text-gray-800 dark:text-gray-200 text-[11px]">
                  {item.percent}%
                </span>
              </div>
            ))
          ) : (
            <div className="text-xs text-gray-400 py-4 text-center">
              No land cover probabilities available
            </div>
          )}
        </div>
      </div>

      <div className="text-[10px] text-gray-400 mt-2 pt-2 border-t border-gray-100 dark:border-gray-700/60 flex items-center justify-between">
        <span>Sentinel-2 10m Near-Real-Time LULC</span>
        <span className="font-medium text-gray-600 dark:text-gray-300">Dynamic World</span>
      </div>
    </div>
  );
};
