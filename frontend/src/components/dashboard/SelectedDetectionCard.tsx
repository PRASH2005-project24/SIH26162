import React from 'react';
import type { NormalizedEvent } from '@/types/normalized';
import { Factory, Trees, Wheat, Zap, HelpCircle, Sun, Moon, Droplets, ShieldCheck } from 'lucide-react';

interface SelectedDetectionCardProps {
  event: NormalizedEvent | null;
  onClose?: () => void;
}

const CATEGORY_STYLES: Record<string, { bg: string; text: string; border: string; Icon: React.ComponentType<{ className?: string }> }> = {
  'Industrial Fire': {
    bg: 'bg-red-50 dark:bg-red-950/40',
    text: 'text-red-600 dark:text-red-400',
    border: 'border-red-200 dark:border-red-800/50',
    Icon: Factory,
  },
  'Wildfire / Natural Fire': {
    bg: 'bg-orange-50 dark:bg-orange-950/40',
    text: 'text-orange-600 dark:text-orange-400',
    border: 'border-orange-200 dark:border-orange-800/50',
    Icon: Trees,
  },
  'Agricultural Fire': {
    bg: 'bg-amber-50 dark:bg-amber-950/40',
    text: 'text-amber-600 dark:text-amber-400',
    border: 'border-amber-200 dark:border-amber-800/50',
    Icon: Wheat,
  },
  'Persistent Thermal Source': {
    bg: 'bg-blue-50 dark:bg-blue-950/40',
    text: 'text-blue-600 dark:text-blue-400',
    border: 'border-blue-200 dark:border-blue-800/50',
    Icon: Zap,
  },
  'Unknown / Other': {
    bg: 'bg-gray-100 dark:bg-gray-800',
    text: 'text-gray-600 dark:text-gray-400',
    border: 'border-gray-200 dark:border-gray-700',
    Icon: HelpCircle,
  },
};

export const SelectedDetectionCard: React.FC<SelectedDetectionCardProps> = ({ event, onClose }) => {
  if (!event) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-2xl p-6 shadow-xs border border-gray-100 dark:border-gray-700 flex flex-col items-center justify-center h-full min-h-[420px] text-center">
        <div className="w-12 h-12 rounded-2xl bg-gray-50 dark:bg-gray-700/50 flex items-center justify-center text-gray-400 mb-3">
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </div>
        <h3 className="text-sm font-bold text-gray-700 dark:text-gray-200">No Detection Selected</h3>
        <p className="text-xs text-gray-400 mt-1 max-w-xs">
          Click any fire marker on the India map or an item from the event feed to inspect NASA FIRMS and ML details.
        </p>
      </div>
    );
  }

  const lat = event.latitude.toFixed(4);
  const lon = event.longitude.toFixed(4);
  const category = event.classification || 'Unknown / Other';
  const categoryStyle = CATEGORY_STYLES[category] || CATEGORY_STYLES['Unknown / Other'];

  const confidencePercent = Math.round(
    event.confidence <= 1 ? event.confidence * 100 : event.confidence
  );

  const locationTitle = event.location
    ? `${event.location.city}, ${event.location.state}`
    : 'India Station';

  const acqDate = event.acquisition_time
    ? new Date(event.acquisition_time).toLocaleString('en-IN', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    : '--';

  const isDay = event.day_night === 'D';
  const isNight = event.day_night === 'N';

  // ML probabilities breakdown if available
  const mlProbs = event.prediction?.ml_probabilities;

  return (
    <div className="bg-white/85 dark:bg-slate-900/70 backdrop-blur-md rounded-2xl p-5 shadow-xs border border-gray-200/80 dark:border-slate-800/80 flex flex-col justify-between space-y-4">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between pb-3 border-b border-gray-100 dark:border-slate-800/80">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
            <h2 className="text-sm font-bold text-gray-900 dark:text-white tracking-tight">
              Selected Detection
            </h2>
            <span className="text-[11px] font-mono text-gray-400 dark:text-gray-500">
              #{event.event_id}
            </span>
          </div>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              aria-label="Close details"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        {/* Location & Time */}
        <div className="mt-3 flex items-start justify-between">
          <div>
            <div className="text-sm font-bold text-gray-900 dark:text-white leading-tight">
              {locationTitle}
            </div>
            <div className="text-[11px] text-gray-400 font-mono mt-0.5">
              {lat}° N, {lon}° E
            </div>
          </div>
          <div className="text-right">
            <div className="text-[11px] font-medium text-gray-700 dark:text-gray-300">
              {acqDate}
            </div>
            {(isDay || isNight) && (
              <div className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5 flex items-center justify-end gap-1 font-medium">
                {isDay ? <Sun className="w-3 h-3 text-amber-500" /> : <Moon className="w-3 h-3 text-indigo-400" />}
                <span>{isDay ? 'Day Pass' : 'Night Pass'}</span>
              </div>
            )}
          </div>
        </div>

        {/* SIH Category Classification */}
        <div className="mt-4">
          <div className="text-[10px] font-bold text-gray-400 dark:text-gray-400 tracking-wider uppercase mb-1.5">
            SIH CLASSIFICATION
          </div>
          <div
            className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl border ${categoryStyle.bg} ${categoryStyle.border}`}
          >
            <div className="flex items-center gap-2">
              <categoryStyle.Icon className={`w-4 h-4 ${categoryStyle.text}`} />
              <span className={`text-xs font-bold ${categoryStyle.text}`}>
                {category}
              </span>
            </div>
            <div className="text-right">
              <div className="text-xs font-bold text-gray-900 dark:text-white">
                {confidencePercent}%
              </div>
              <div className="text-[9px] text-gray-400 uppercase font-semibold">Confidence</div>
            </div>
          </div>
        </div>

        {/* ML Probabilities Distribution (if available) */}
        {mlProbs && (
          <div className="mt-3 space-y-1.5">
            <div className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">
              Source Probabilities (ML Stage 2)
            </div>
            <div className="space-y-1">
              {Object.entries(mlProbs).map(([key, val]) => {
                const pct = Math.round(val * 100);
                const label = key.charAt(0).toUpperCase() + key.slice(1);
                return (
                  <div key={key} className="space-y-0.5">
                    <div className="flex justify-between text-[11px]">
                      <span className="text-gray-500 dark:text-gray-400">{label}</span>
                      <span className="font-semibold text-gray-700 dark:text-gray-300">{pct}%</span>
                    </div>
                    <div className="h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full transition-all ${
                          key === 'industrial'
                            ? 'bg-red-500'
                            : key === 'wildfire'
                            ? 'bg-orange-500'
                            : 'bg-amber-500'
                        }`}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* NASA FIRMS Thermal Sensor Metrics */}
      <div className="pt-3 border-t border-gray-100 dark:border-gray-700/60">
        <div className="text-[10px] font-bold text-gray-400 tracking-wider uppercase mb-2">
          NASA FIRMS SENSOR DATA
        </div>
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="bg-gray-50 dark:bg-gray-700/40 p-2.5 rounded-xl border border-gray-100 dark:border-gray-700/50">
            <div className="text-[10px] text-gray-400 font-medium">Thermal Intensity (FRP)</div>
            <div className="text-sm font-bold text-gray-900 dark:text-white mt-0.5">
              {event.frp != null ? `${Number(event.frp).toFixed(1)} MW` : '--'}
            </div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-700/40 p-2.5 rounded-xl border border-gray-100 dark:border-gray-700/50">
            <div className="text-[10px] text-gray-400 font-medium">Brightness Temp</div>
            <div className="text-sm font-bold text-gray-900 dark:text-white mt-0.5">
              {event.brightness != null ? `${Number(event.brightness).toFixed(1)} K` : '--'}
            </div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-700/40 p-2.5 rounded-xl border border-gray-100 dark:border-gray-700/50 col-span-2 flex items-center justify-between">
            <div>
              <div className="text-[10px] text-gray-400 font-medium">Satellite & Instrument</div>
              <div className="text-xs font-semibold text-gray-800 dark:text-gray-200 mt-0.5">
                {event.satellite_name} {event.instrument ? `(${event.instrument})` : ''}
              </div>
            </div>
            <span className="text-[10px] px-2 py-0.5 rounded-full font-medium bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-200">
              NASA FIRMS
            </span>
          </div>
        </div>
      </div>

      {/* GIS Enrichment & Context */}
      <div className="pt-3 border-t border-gray-100 dark:border-gray-700/60 space-y-2 text-xs">
        <div className="text-[10px] font-bold text-gray-400 tracking-wider uppercase mb-1">
          GIS CONTEXT & EVIDENCE
        </div>

        <div className="flex items-center justify-between text-[11px]">
          <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
            <Factory className="w-3.5 h-3.5 text-rose-500 shrink-0" /> Industrial Proximity
          </span>
          <span className="font-semibold text-gray-800 dark:text-gray-200 truncate max-w-[170px]">
            {event.industrial_context?.osm_proximity || '--'}
          </span>
        </div>

        <div className="flex items-center justify-between text-[11px]">
          <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
            <Droplets className="w-3.5 h-3.5 text-blue-500 shrink-0" /> Water Body
          </span>
          <span className="font-semibold text-gray-800 dark:text-gray-200">
            {event.water_context?.proximity || '--'}
          </span>
        </div>

        <div className="flex items-center justify-between text-[11px]">
          <span className="text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-500 shrink-0" /> Temporal Persistence
          </span>
          <span className="font-semibold text-gray-800 dark:text-gray-200">
            {event.persistence || 'Single observation'}
          </span>
        </div>
      </div>
    </div>
  );
};
