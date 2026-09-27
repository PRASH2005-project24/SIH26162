import React from 'react';
import { Zap, Wind, Satellite } from 'lucide-react';

interface RiskDialGaugeProps {
  score: number;
  level?: 'low' | 'moderate' | 'high' | 'critical' | string;
  frp?: number | null;
  rateOfSpread?: string;
  isPersistent?: boolean;
}

export const RiskDialGauge: React.FC<RiskDialGaugeProps> = ({
  score,
  level = 'moderate',
  frp,
  rateOfSpread = '1.8 km/h',
  isPersistent = false,
}) => {
  // Clamped score between 0 and 100
  const clampedScore = Math.min(100, Math.max(0, Math.round(score)));

  // Half-circle arc math: radius = 80, length = PI * 80 = ~251.32
  const arcLength = 251.32;
  const strokeDashoffset = arcLength * (1 - clampedScore / 100);

  // Status mapping
  const normalizedLevel = level.toLowerCase();
  const isCritical = normalizedLevel === 'critical' || clampedScore >= 75;
  const isHigh = !isCritical && (normalizedLevel === 'high' || clampedScore >= 55);
  const isModerate = !isCritical && !isHigh && (normalizedLevel === 'moderate' || clampedScore >= 35);

  const statusLabel = isCritical
    ? 'CRITICAL EXPANSION HAZARD'
    : isHigh
    ? 'HIGH THERMAL EXPANSION'
    : isModerate
    ? 'MODERATE ANOMALY RISK'
    : 'LOW / NOMINAL HAZARD';

  const statusColor = isCritical
    ? 'text-red-500 dark:text-red-400'
    : isHigh
    ? 'text-orange-500 dark:text-orange-400'
    : isModerate
    ? 'text-amber-500 dark:text-amber-400'
    : 'text-emerald-500 dark:text-emerald-400';

  const badgeBg = isCritical
    ? 'bg-red-500/15 border-red-500/40 text-red-600 dark:text-red-400'
    : isHigh
    ? 'bg-orange-500/15 border-orange-500/40 text-orange-600 dark:text-orange-400'
    : isModerate
    ? 'bg-amber-500/15 border-amber-500/40 text-amber-600 dark:text-amber-400'
    : 'bg-emerald-500/15 border-emerald-500/40 text-emerald-600 dark:text-emerald-400';

  return (
    <div className="p-4 rounded-2xl bg-white/70 dark:bg-slate-900/60 backdrop-blur-md border border-gray-200/80 dark:border-slate-800/80 shadow-xs relative overflow-hidden select-none">
      {/* Subtle top rim light */}
      <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-red-500/30 dark:via-cyan-500/30 to-transparent" />

      {/* Header */}
      <div className="flex justify-between items-center mb-1">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
          <span className="text-[10px] font-mono font-bold tracking-wider text-gray-500 dark:text-gray-400 uppercase">
            AGGREGATE DANGER MODEL
          </span>
        </div>
        <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${badgeBg}`}>
          {statusLabel}
        </span>
      </div>

      {/* Semi-circular radial dial gauge */}
      <div className="flex flex-col items-center justify-center pt-2 pb-1 relative">
        <svg className="w-52 h-28" viewBox="0 0 200 115">
          <defs>
            <linearGradient id="fireGuardDialGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#10b981" />
              <stop offset="35%" stopColor="#06b6d4" />
              <stop offset="70%" stopColor="#f59e0b" />
              <stop offset="100%" stopColor="#ef4444" />
            </linearGradient>
            <filter id="gaugeGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="0" stdDeviation="3" floodColor="#ff562c" floodOpacity="0.4" />
            </filter>
          </defs>

          {/* Background Track Arc */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="currentColor"
            className="text-gray-200 dark:text-slate-800"
            strokeLinecap="round"
            strokeWidth="11"
          />

          {/* Active Gradient Arc */}
          <path
            d="M 20 100 A 80 80 0 0 1 180 100"
            fill="none"
            stroke="url(#fireGuardDialGradient)"
            strokeLinecap="round"
            strokeWidth="11"
            strokeDasharray={arcLength}
            strokeDashoffset={strokeDashoffset}
            filter="url(#gaugeGlow)"
            className="transition-all duration-700 ease-out"
          />

          {/* Center Readout */}
          <text
            x="100"
            y="80"
            textAnchor="middle"
            className={`font-mono font-black text-3xl tracking-tight fill-current ${statusColor}`}
          >
            {clampedScore}
          </text>
          <text
            x="100"
            y="98"
            textAnchor="middle"
            className="text-[10px] font-mono tracking-widest fill-gray-400 dark:fill-gray-500 font-semibold"
          >
            / 100 RISK SCORE
          </text>
        </svg>
      </div>

      {/* Telemetry sub-chips */}
      <div className="grid grid-cols-3 gap-1.5 pt-2.5 mt-1 border-t border-gray-100 dark:border-slate-800/80 text-[10px] font-mono">
        <div className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400 bg-gray-50/80 dark:bg-slate-800/40 px-2 py-1.5 rounded-xl border border-gray-100 dark:border-slate-800/60">
          <Zap className="w-3 h-3 text-red-500 shrink-0" />
          <span className="truncate">
            FRP: <strong className="text-gray-900 dark:text-white font-bold">{frp != null ? `${Number(frp).toFixed(1)}M` : 'N/A'}</strong>
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400 bg-gray-50/80 dark:bg-slate-800/40 px-2 py-1.5 rounded-xl border border-gray-100 dark:border-slate-800/60">
          <Wind className="w-3 h-3 text-amber-500 shrink-0" />
          <span className="truncate">
            Spread: <strong className="text-gray-900 dark:text-white font-bold">{rateOfSpread}</strong>
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-gray-600 dark:text-gray-400 bg-gray-50/80 dark:bg-slate-800/40 px-2 py-1.5 rounded-xl border border-gray-100 dark:border-slate-800/60">
          <Satellite className="w-3 h-3 text-cyan-500 shrink-0" />
          <span className="truncate">
            LEO: <strong className="text-gray-900 dark:text-white font-bold">{isPersistent ? 'Multi' : 'Pass'}</strong>
          </span>
        </div>
      </div>
    </div>
  );
};
