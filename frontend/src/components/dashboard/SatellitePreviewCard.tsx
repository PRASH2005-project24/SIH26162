import React from 'react';
import type { SatelliteInfo } from '@/types/normalized';

interface SatellitePreviewCardProps {
  satellite?: SatelliteInfo | null;
  acquisitionDate?: string | null;
  cloudCoverage?: number | null;
}

export const SatellitePreviewCard: React.FC<SatellitePreviewCardProps> = ({
  satellite,
  acquisitionDate,
  cloudCoverage = 20,
}) => {
  const dateVal = satellite?.acquisition_date || acquisitionDate;
  const cloudVal = satellite?.cloud_cover ?? cloudCoverage;
  const imageUrl = satellite?.url;
  const isAvailable = satellite?.available ?? true;

  const displayDate = dateVal
    ? new Date(dateVal).toLocaleDateString('en-GB', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    : '24 Aug 2026';

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 h-full flex flex-col justify-between">
      <div className="flex items-baseline gap-1.5">
        <h2 className="text-sm font-bold text-gray-900 dark:text-white tracking-tight">
          Satellite Image
        </h2>
        <span className="text-[11px] font-normal text-gray-400">
          (Sentinel-2)
        </span>
      </div>

      {/* Satellite Imagery Preview Screen */}
      <div className="relative mt-3 h-32 rounded-xl overflow-hidden bg-gradient-to-br from-[#293d2c] via-[#3a4d38] to-[#1c2c1f] flex items-center justify-center border border-emerald-950/20 shadow-inner group">
        {/* Render image if available and URL valid, per frontend_requirements.md */}
        {isAvailable && imageUrl ? (
          <img
            src={imageUrl}
            alt="Sentinel-2 observation preview"
            className="w-full h-full object-cover"
          />
        ) : (
          <>
            {/* Subtle terrain / grid pattern */}
            <div
              className="absolute inset-0 opacity-25"
              style={{
                backgroundImage:
                  'radial-gradient(#8ca384 1px, transparent 1px), radial-gradient(#5a7353 1px, transparent 1px)',
                backgroundSize: '20px 20px',
                backgroundPosition: '0 0, 10px 10px',
              }}
            />

            {/* Center icon & text */}
            <div className="relative z-10 flex flex-col items-center gap-1.5 text-white/90">
              <div className="p-2 rounded-lg bg-black/20 backdrop-blur-xs">
                <svg className="w-6 h-6 text-white/90" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="1.75"
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>
              <span className="text-xs font-semibold tracking-wide text-white/90 drop-shadow-sm">
                Satellite Preview
              </span>
            </div>
          </>
        )}
      </div>

      {/* Footer Bar */}
      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mt-3 pt-2">
        <span className="text-[11px]">
          Date: <span className="font-medium text-gray-700 dark:text-gray-300">{displayDate}</span>
        </span>
        <div className="flex items-center gap-1 text-[11px]">
          <svg className="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"
            />
          </svg>
          <span className="font-medium text-gray-700 dark:text-gray-300">{cloudVal}%</span>
        </div>
      </div>
    </div>
  );
};
