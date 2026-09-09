import React from 'react';
import type { NormalizedEvent } from '@/types/normalized';

interface SelectedDetectionCardProps {
  event: NormalizedEvent | null;
  onClose?: () => void;
}

export const SelectedDetectionCard: React.FC<SelectedDetectionCardProps> = ({ event, onClose }) => {
  const lat = event ? event.latitude.toFixed(4) : '18.5204';
  const lon = event ? event.longitude.toFixed(4) : '73.8567';

  // Format location string per requirements (city, state, country)
  const locationTitle = event?.location
    ? `${event.location.city}, ${event.location.state}, ${event.location.country}`
    : 'Pune, Maharashtra, India';

  // Risk score & level per requirements
  const riskScore = event?.risk_score ?? 87;
  const riskLevel = (event?.risk_level ?? 'critical').toUpperCase();

  // Prediction & Confidence
  const predictionCategory = event?.classification || event?.prediction?.predicted_class || 'Industrial Fire';
  const confidencePercent = event?.confidence !== undefined
    ? Math.round((event.confidence <= 1 ? event.confidence * 100 : event.confidence))
    : 91;

  // Key factors per requirements
  const keyFactors = event?.prediction?.key_factors || [
    { name: 'High Thermal Intensity (FRP)', value: 'High' },
    { name: 'Industrial Facility Nearby', value: 'Yes' },
    { name: 'Land Cover', value: 'Built-up (87%)' },
    { name: 'Population Density', value: 'High' },
    { name: 'Persistent Anomaly', value: 'Yes' },
  ];

  const getFactorIcon = (factorName: string) => {
    if (factorName.includes('Thermal') || factorName.includes('FRP')) return '🌡️';
    if (factorName.includes('Industrial') || factorName.includes('Facility')) return '🏭';
    if (factorName.includes('Land Cover')) return '🥞';
    if (factorName.includes('Population')) return '👥';
    if (factorName.includes('Persistent')) return '🛡️';
    return '📌';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 flex flex-col justify-between h-full">
      {/* Header */}
      <div>
        <div className="flex items-center justify-between pb-2 border-b border-gray-100 dark:border-gray-700/60">
          <h2 className="text-sm font-bold text-gray-900 dark:text-white tracking-tight">
            Selected Detection
          </h2>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors p-1"
              aria-label="Close details"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>

        {/* Location Row */}
        <div className="flex items-start gap-2.5 mt-3">
          <div className="mt-0.5 text-red-500">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
            </svg>
          </div>
          <div>
            <div className="text-xs font-bold text-gray-900 dark:text-white leading-tight">
              {locationTitle}
            </div>
            <div className="text-[11px] text-gray-400 font-mono mt-0.5">
              {lat}, {lon}
            </div>
          </div>
        </div>

        {/* RISK SCORE Section */}
        <div className="mt-4 pt-3 border-t border-gray-100 dark:border-gray-700/60">
          <div className="text-[10px] font-bold text-gray-400 tracking-wider uppercase">
            RISK SCORE
          </div>
          <div className="flex items-center justify-between mt-1">
            <div className="flex items-baseline gap-1">
              <span className="text-3xl font-extrabold text-gray-900 dark:text-white tracking-tight">
                {riskScore}
              </span>
              <span className="text-xs font-semibold text-gray-400">
                / 100
              </span>
            </div>
            <div
              className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold ${
                riskLevel === 'CRITICAL'
                  ? 'bg-red-50 dark:bg-red-950/50 text-red-500 border border-red-100 dark:border-red-900/40'
                  : riskLevel === 'HIGH'
                  ? 'bg-orange-50 dark:bg-orange-950/50 text-orange-500 border border-orange-100 dark:border-orange-900/40'
                  : 'bg-emerald-50 dark:bg-emerald-950/50 text-emerald-500 border border-emerald-100 dark:border-emerald-900/40'
              }`}
            >
              <span className="text-xs">🔥</span>
              <span>{riskLevel}</span>
            </div>
          </div>
        </div>

        {/* Prediction Section */}
        <div className="mt-4 pt-3 border-t border-gray-100 dark:border-gray-700/60 flex items-center justify-between">
          <div>
            <div className="text-[10px] text-gray-400 uppercase font-medium">Prediction</div>
            <div className="text-sm font-bold text-gray-900 dark:text-white mt-0.5">
              {predictionCategory}
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs font-bold text-emerald-500">
              {confidencePercent}%
            </div>
            <div className="text-[10px] text-gray-400 font-medium">Confidence</div>
          </div>
        </div>
      </div>

      {/* Key Factors Section */}
      <div className="mt-4 pt-3 border-t border-gray-100 dark:border-gray-700/60 space-y-2.5">
        <div className="text-[11px] font-bold text-gray-800 dark:text-gray-200">
          Key Factors
        </div>

        {keyFactors.map((item, idx) => {
          const factorLabel = item.name || item.factor || `Factor ${idx + 1}`;
          const factorIcon = getFactorIcon(factorLabel);

          return (
            <div key={factorLabel} className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                <span>{factorIcon}</span>
                <span>{factorLabel}</span>
              </div>
              <span className="font-semibold text-gray-800 dark:text-gray-200">
                {item.value}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};
