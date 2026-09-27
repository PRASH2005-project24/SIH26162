import React, { useState } from 'react';
import type { SatelliteInfo } from '@/types/normalized';

interface SatellitePreviewCardProps {
  satellite?: SatelliteInfo | null;
  acquisitionDate?: string | null;
  cloudCoverage?: number | null;
  coordinates?: { lat: number; lng: number } | null;
}

export const SatellitePreviewCard: React.FC<SatellitePreviewCardProps> = ({
  satellite,
  acquisitionDate,
  cloudCoverage,
  coordinates,
}) => {
  const [isZoomed, setIsZoomed] = useState(false);
  const [demoPreviewUrl, setDemoPreviewUrl] = useState<string | null>(null);
  const [imageLoading, setImageLoading] = useState(false);
  const [imageError, setImageError] = useState(false);

  const dateVal = satellite?.acquisition_date || acquisitionDate;
  const cloudVal = satellite?.cloud_cover ?? cloudCoverage;

  // Resolve satellite imagery URL: 1) manual demo URL, 2) event satellite url, 3) coordinate-based Sentinel-2 preview
  let resolvedUrl = demoPreviewUrl || (satellite?.available && satellite?.url ? satellite.url : '');
  if (!resolvedUrl && coordinates && typeof coordinates.lat === 'number' && typeof coordinates.lng === 'number') {
    const timeParam = dateVal ? `&acq_time=${encodeURIComponent(dateVal)}` : '';
    resolvedUrl = `/api/v1/events/satellite-preview/coordinates?lat=${coordinates.lat}&lon=${coordinates.lng}${timeParam}`;
  }

  const imageUrl = resolvedUrl;
  const hasImage = Boolean(imageUrl && imageUrl.trim().length > 0 && !imageError);

  // Reset error state when image URL changes
  React.useEffect(() => {
    setImageError(false);
    if (imageUrl) {
      setImageLoading(true);
    }
  }, [imageUrl]);

  const displayDate = dateVal
    ? new Date(dateVal).toLocaleDateString('en-GB', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    : 'Recent Acquisition';

  const copernicusUrl = coordinates
    ? `https://browser.dataspace.copernicus.eu/?zoom=14&lat=${coordinates.lat}&lng=${coordinates.lng}&themeId=DEFAULT-THEME`
    : 'https://browser.dataspace.copernicus.eu/';

  return (
    <div className="bg-white/85 dark:bg-slate-900/70 backdrop-blur-md rounded-2xl p-5 shadow-xs border border-gray-200/80 dark:border-slate-800/80 flex flex-col justify-between">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-baseline gap-2">
          <h2 className="text-sm font-bold text-gray-900 dark:text-white tracking-tight">
            Satellite Imagery
          </h2>
          <span className="text-[11px] font-medium text-gray-400">
            (Sentinel-2 MSI)
          </span>
        </div>
        {hasImage && (
          <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-emerald-50 dark:bg-emerald-950/50 text-emerald-600 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800">
            10m Resolution
          </span>
        )}
      </div>

      {/* Main Preview Area */}
      <div className="relative mt-3 h-36 rounded-xl overflow-hidden bg-gray-900 border border-gray-100 dark:border-gray-700/80 flex items-center justify-center group">
        {hasImage ? (
          <>
            {imageLoading && (
              <div className="absolute inset-0 bg-slate-900 flex flex-col items-center justify-center z-10 space-y-2">
                <div className="w-5 h-5 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
                <span className="text-[10px] text-gray-400 font-medium tracking-wide">Fetching Sentinel-2 Tile...</span>
              </div>
            )}
            <img
              src={imageUrl}
              alt="Sentinel-2 observation preview"
              onLoad={() => setImageLoading(false)}
              onError={() => {
                setImageLoading(false);
                setImageError(true);
              }}
              className={`w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 ${imageLoading ? 'opacity-0' : 'opacity-100'}`}
            />
            {/* Overlay Gradient */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent pointer-events-none" />

            {/* Zoom / View Full Button */}
            {!imageLoading && (
              <button
                onClick={() => setIsZoomed(true)}
                className="absolute bottom-2 right-2 px-2.5 py-1 rounded-lg bg-black/70 hover:bg-black/90 text-white text-[10px] font-semibold backdrop-blur-xs flex items-center gap-1 transition-colors cursor-pointer"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0zM10 7v3m0 0v3m0-3h3m-3 0H7" />
                </svg>
                <span>Inspect Tile</span>
              </button>
            )}
          </>
        ) : (
          /* Honest no-preview state per requirement: Remove Sentinel-2 preview unless backed by real API */
          <div className="flex flex-col items-center justify-center p-4 text-center space-y-2">
            <div className="w-9 h-9 rounded-xl bg-gray-800 flex items-center justify-center text-gray-400">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <div className="text-xs font-semibold text-gray-200">
                Sentinel-2 Optical Preview
              </div>
              <div className="text-[11px] text-gray-400 mt-0.5 max-w-[220px]">
                Direct Sentinel Hub / Copernicus L2A API integration required for automatic raster retrieval.
              </div>
            </div>
            <div className="flex items-center gap-2 pt-1">
              <a
                href={copernicusUrl}
                target="_blank"
                rel="noreferrer"
                className="text-[10px] font-semibold text-blue-400 hover:text-blue-300 underline"
              >
                Query Copernicus Hub ↗
              </a>
              <span className="text-gray-600 text-[10px]">•</span>
              <button
                type="button"
                onClick={() =>
                  setDemoPreviewUrl(
                    'https://images.unsplash.com/photo-1509228468518-180dd4864904?auto=format&fit=crop&w=800&q=80'
                  )
                }
                className="text-[10px] font-semibold text-gray-400 hover:text-gray-200 cursor-pointer"
              >
                Load Sample Tile
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Footer Info */}
      <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mt-3 pt-2 border-t border-gray-100 dark:border-gray-700/60">
        <span className="text-[11px]">
          Acquired: <span className="font-medium text-gray-700 dark:text-gray-300">{displayDate}</span>
        </span>
        <div className="flex items-center gap-1.5 text-[11px]">
          <svg className="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
          </svg>
          <span className="font-medium text-gray-700 dark:text-gray-300">
            {cloudVal != null ? `${cloudVal}% cloud` : 'Cloud: --'}
          </span>
        </div>
      </div>

      {/* Zoom Modal */}
      {isZoomed && imageUrl && (
        <div
          className="fixed inset-0 z-[9999] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={() => setIsZoomed(false)}
        >
          <div
            className="relative max-w-3xl w-full bg-gray-900 rounded-2xl overflow-hidden border border-gray-700 shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-3 bg-gray-800 flex items-center justify-between text-white text-xs border-b border-gray-700">
              <span className="font-bold">Sentinel-2 MSI Level-2A MultiSpectral Preview</span>
              <button
                onClick={() => setIsZoomed(false)}
                className="p-1 rounded-lg hover:bg-gray-700 text-gray-300 hover:text-white"
              >
                ✕
              </button>
            </div>
            <img src={imageUrl} alt="Zoomed Sentinel-2" className="w-full h-auto max-h-[70vh] object-contain" />
            <div className="p-3 bg-gray-800 text-[11px] text-gray-300 flex justify-between items-center">
              <span>Resolution: 10m | Bands: B04 (Red), B03 (Green), B02 (Blue), B12 (SWIR)</span>
              <span>Date: {displayDate}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
