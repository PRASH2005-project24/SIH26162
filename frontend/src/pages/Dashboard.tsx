import { useState, useMemo, useEffect } from 'react';
import { MapContainer } from '@/components/map/MapContainer';
import { SelectedDetectionCard } from '@/components/dashboard/SelectedDetectionCard';
import { ThermalContextCard } from '@/components/dashboard/ThermalContextCard';
import { LandCoverCard } from '@/components/dashboard/LandCoverCard';
import { SatellitePreviewCard } from '@/components/dashboard/SatellitePreviewCard';
import { RiskDialGauge } from '@/components/dashboard/RiskDialGauge';
import { SiHCategoryBadge } from '@/components/ui/SiHCategoryBadge';
import { useSelectedEventContext } from '@/context/SelectedEventContext';
import type { SIHCategory } from '@/types/index';
import { LayoutDashboard, Crosshair, Radio, Globe, Satellite } from 'lucide-react';

type ActiveTab = 'all' | 'detection' | 'thermal' | 'landcover' | 'satellite';

export const Dashboard = () => {
  const { selectedEvent, clearSelection } = useSelectedEventContext();
  const [activeTab, setActiveTab] = useState<ActiveTab>('all');
  const [copiedCoords, setCopiedCoords] = useState(false);

  // Close side panel when user presses Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && selectedEvent) {
        clearSelection();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedEvent, clearSelection]);

  // Determine dominant land cover label from the selected event
  const dominantLabel = useMemo(() => {
    if (!selectedEvent?.land_cover) return selectedEvent?.raw?.dynamic_world?.land_cover_label ?? null;
    const lc = selectedEvent.land_cover;
    let max = 0;
    let label = selectedEvent.raw?.dynamic_world?.land_cover_label ?? 'Built';
    for (const [key, val] of Object.entries(lc)) {
      if (typeof val === 'number' && val > max) {
        max = val;
        label = key;
      }
    }
    return label;
  }, [selectedEvent]);

  // Calculate dynamic risk score if not directly set
  const riskScore = useMemo(() => {
    if (!selectedEvent) return 50;
    if (selectedEvent.raw?.risk_score) return Number(selectedEvent.raw.risk_score);
    const conf = selectedEvent.confidence <= 1 ? selectedEvent.confidence * 100 : selectedEvent.confidence;
    const frpVal = Number(selectedEvent.frp || 40);
    const isPersistent = Boolean(selectedEvent.persistence_details?.is_persistent);
    return Math.min(98, Math.max(30, Math.round(conf * 0.5 + Math.min(120, frpVal) * 0.35 + (isPersistent ? 10 : 0))));
  }, [selectedEvent]);

  // Copy coordinates to clipboard
  const handleCopyCoords = async () => {
    if (!selectedEvent) return;
    try {
      await navigator.clipboard.writeText(`${selectedEvent.latitude.toFixed(5)}, ${selectedEvent.longitude.toFixed(5)}`);
      setCopiedCoords(true);
      setTimeout(() => setCopiedCoords(false), 2000);
    } catch {
      // Fallback
    }
  };

  return (
    <div className="relative h-full w-full flex-1 flex flex-col overflow-hidden">
      {/* Whole Map on the Whole Screen */}
      <div className="absolute inset-0 z-0">
        <MapContainer />
      </div>

      {/* Mobile Backdrop for quick dismissal */}
      {selectedEvent && (
        <div
          className="sm:hidden fixed inset-0 z-[1050] bg-black/40 backdrop-blur-xs transition-opacity duration-200"
          onClick={clearSelection}
          aria-hidden="true"
        />
      )}

      {/* Slide-over Inspection Panel (Stitch Aerospace Telemetry Console) */}
      {selectedEvent && (
        <aside
          className="absolute top-0 right-0 bottom-0 z-[1100] w-full sm:w-[480px] lg:w-[520px] 2xl:w-[560px] bg-white/95 dark:bg-[#0c101c]/95 backdrop-blur-xl shadow-[-12px_0_35px_rgba(0,0,0,0.25)] border-l border-gray-200/90 dark:border-slate-800 flex flex-col overflow-hidden animate-drawer-in"
          aria-label="Detection Intelligence Panel"
        >
          {/* Top Dossier Bar */}
          <div className="px-5 py-3 border-b border-gray-200/90 dark:border-slate-800 bg-gray-50/90 dark:bg-slate-900/80 flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* Pulsing Radar LED */}
              <span className="w-2.5 h-2.5 rounded-full bg-red-500 relative flex items-center justify-center">
                <span className="absolute w-4 h-4 rounded-full bg-red-500/40 animate-radar-ping" />
              </span>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-gray-900 dark:text-white tracking-tight leading-tight">
                    {selectedEvent.location?.city || 'India Station'}, {selectedEvent.location?.state || 'India'}
                  </span>
                  <span className="font-mono text-[10px] text-gray-400 dark:text-gray-500 bg-gray-200/60 dark:bg-slate-800/80 px-1.5 py-0.5 rounded-md">
                    #{selectedEvent.event_id}
                  </span>
                </div>
                <div className="text-[10px] font-mono text-gray-500 dark:text-gray-400 flex items-center gap-1.5 mt-0.5">
                  <span>LEO PASS</span>
                  <span>•</span>
                  <span>{selectedEvent.latitude.toFixed(4)}°N, {selectedEvent.longitude.toFixed(4)}°E</span>
                </div>
              </div>
            </div>

            {/* Header Right: Category Badge & Close */}
            <div className="flex items-center gap-2">
              <SiHCategoryBadge category={(selectedEvent.classification as SIHCategory) || 'Unknown / Other'} />
              <button
                onClick={clearSelection}
                className="p-1.5 rounded-xl text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-200/70 dark:hover:bg-slate-800 transition-colors cursor-pointer group"
                title="Close inspector (Esc)"
                aria-label="Close"
              >
                <svg className="w-4 h-4 transition-transform group-hover:rotate-90 duration-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          {/* Stitch Aerospace Risk Dial Gauge (Pinned at top of drawer) */}
          <div className="px-5 pt-3.5 pb-2 bg-gradient-to-b from-gray-50/50 to-transparent dark:from-slate-900/40 dark:to-transparent">
            <RiskDialGauge
              score={riskScore}
              level={riskScore >= 75 ? 'critical' : riskScore >= 55 ? 'high' : riskScore >= 35 ? 'moderate' : 'low'}
              frp={selectedEvent.frp}
              isPersistent={Boolean(selectedEvent.persistence_details?.is_persistent)}
            />
          </div>

          {/* Pill Tab Navigation */}
          <div className="px-4 py-2 bg-white/60 dark:bg-slate-900/60 border-y border-gray-100 dark:border-slate-800/80 overflow-x-auto custom-scrollbar flex items-center gap-1.5">
            <button
              onClick={() => setActiveTab('all')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'all'
                  ? 'bg-red-500 text-white shadow-xs shadow-red-500/30'
                  : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-800/60'
              }`}
            >
              <LayoutDashboard className="w-3.5 h-3.5" />
              <span>All Overview</span>
            </button>
            <button
              onClick={() => setActiveTab('detection')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'detection'
                  ? 'bg-red-500 text-white shadow-xs shadow-red-500/30'
                  : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-800/60'
              }`}
            >
              <Crosshair className="w-3.5 h-3.5" />
              <span>Detection</span>
            </button>
            <button
              onClick={() => setActiveTab('thermal')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'thermal'
                  ? 'bg-red-500 text-white shadow-xs shadow-red-500/30'
                  : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-800/60'
              }`}
            >
              <Radio className="w-3.5 h-3.5" />
              <span>Thermal & GIS</span>
            </button>
            <button
              onClick={() => setActiveTab('landcover')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'landcover'
                  ? 'bg-red-500 text-white shadow-xs shadow-red-500/30'
                  : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-800/60'
              }`}
            >
              <Globe className="w-3.5 h-3.5" />
              <span>Land Cover</span>
            </button>
            <button
              onClick={() => setActiveTab('satellite')}
              className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all cursor-pointer flex items-center gap-1.5 ${
                activeTab === 'satellite'
                  ? 'bg-red-500 text-white shadow-xs shadow-red-500/30'
                  : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-slate-800/60'
              }`}
            >
              <Satellite className="w-3.5 h-3.5" />
              <span>Satellite</span>
            </button>
          </div>

          {/* Drawer Scrollable Content Canvas */}
          <div key={activeTab} className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4 animate-tab-fade">
            {/* Tab 1: Selected Detection Card */}
            {(activeTab === 'all' || activeTab === 'detection') && (
              <SelectedDetectionCard
                event={selectedEvent}
                onClose={clearSelection}
              />
            )}

            {/* Tab 2: Thermal & GIS Context Card */}
            {(activeTab === 'all' || activeTab === 'thermal') && (
              <ThermalContextCard event={selectedEvent} />
            )}

            {/* Tab 3: Dynamic World Land Cover Donut Card */}
            {(activeTab === 'all' || activeTab === 'landcover') && (
              <LandCoverCard
                landCover={selectedEvent?.land_cover}
                dominantLabel={dominantLabel}
              />
            )}

            {/* Tab 4: Sentinel-2 Satellite Optical Imagery Preview Card */}
            {(activeTab === 'all' || activeTab === 'satellite') && (
              <SatellitePreviewCard
                satellite={selectedEvent?.satellite}
                acquisitionDate={selectedEvent?.acquisition_time}
                cloudCoverage={selectedEvent?.satellite?.cloud_cover}
                coordinates={{
                  lat: selectedEvent.latitude,
                  lng: selectedEvent.longitude,
                }}
              />
            )}
          </div>

          {/* Tactical Action Dock Footer */}
          <div className="p-3 border-t border-gray-200/90 dark:border-slate-800 bg-gray-50/90 dark:bg-slate-900/90 flex items-center justify-between gap-2 text-xs">
            <button
              onClick={handleCopyCoords}
              className="flex-1 py-2 px-3 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-gray-100 dark:hover:bg-slate-700 text-gray-700 dark:text-gray-200 font-semibold flex items-center justify-center gap-1.5 transition-all cursor-pointer active:scale-95 shadow-xs"
              title="Copy GPS Latitude and Longitude"
            >
              <svg className="w-3.5 h-3.5 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              <span>{copiedCoords ? 'Coords Copied!' : 'Copy Coords'}</span>
            </button>

            <button
              onClick={clearSelection}
              className="py-2 px-4 rounded-xl bg-gray-200 dark:bg-slate-800 hover:bg-gray-300 dark:hover:bg-slate-700 text-gray-700 dark:text-gray-200 font-semibold transition-colors cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        </aside>
      )}
    </div>
  );
};