import React from 'react';
import type { LandCoverBreakdown } from '@/types/normalized';

interface LandCoverCardProps {
  landCover?: LandCoverBreakdown | null;
  dominantLabel?: string | null;
}

export const LandCoverCard: React.FC<LandCoverCardProps> = ({
  landCover,
  dominantLabel = 'Built',
}) => {
  // Use normalized land_cover properties per frontend_requirements.md:
  // Built, Trees, Grass, Crops, Bare, Water, etc.
  const built = landCover?.Built ?? 87;
  const trees = landCover?.Trees ?? 4;
  const grass = landCover?.Grass ?? 3;
  const crops = landCover?.Crops ?? 3;
  const bare = landCover?.Bare ?? 2;
  const water = landCover?.Water ?? 1;
  const others = Math.max(1, 100 - (built + trees + grass + crops + bare + water));

  const legendItems = [
    { label: 'Built', percent: built, color: '#ef4444' },
    { label: 'Trees', percent: trees, color: '#22c55e' },
    { label: 'Grass', percent: grass, color: '#84cc16' },
    { label: 'Crops', percent: crops, color: '#f97316' },
    { label: 'Bare', percent: bare, color: '#d97706' },
    { label: 'Water', percent: water, color: '#3b82f6' },
    { label: 'Others', percent: others, color: '#9ca3af' },
  ];

  // Calculate SVG donut stroke dash arrays
  const radius = 42;
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
    <div className="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 h-full flex flex-col justify-between">
      <div className="flex items-baseline gap-1.5">
        <h2 className="text-sm font-bold text-gray-900 dark:text-white tracking-tight">
          Land Cover
        </h2>
        <span className="text-[11px] font-normal text-gray-400">
          (Dynamic World)
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
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="text-xl font-black text-gray-900 dark:text-white leading-none">
              {built}%
            </span>
            <span className="text-[10px] font-medium text-gray-400 mt-0.5">
              {dominantLabel}
            </span>
          </div>
        </div>

        {/* Legend */}
        <div className="flex-1 space-y-1 pl-2">
          {legendItems.map((item) => (
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
          ))}
        </div>
      </div>
    </div>
  );
};
