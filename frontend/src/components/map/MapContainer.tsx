import { useMemo, useEffect, useRef } from 'react';
import { MapContainer as LeafletMapContainer, TileLayer, ZoomControl, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import { useEvents } from '@/hooks/useEvents';
import { EventMarker } from './EventMarker';
import { useSelectedEventContext } from '@/context/SelectedEventContext';
import { useFilters, ALL_SIH_CATEGORIES } from '@/hooks/useFilters';
import type { NormalizedEvent } from '@/types/normalized';

function MapResizer() {
  const map = useMap();
  useEffect(() => {
    map.invalidateSize();
    const timer = setTimeout(() => map.invalidateSize(), 250);
    return () => clearTimeout(timer);
  }, [map]);
  return null;
}

// Automatically smoothly zoom into clicked dot area
function MapViewController({ selectedEvent }: { selectedEvent: NormalizedEvent | null }) {
  const map = useMap();
  const prevIdRef = useRef<string | null>(null);

  useEffect(() => {
    if (selectedEvent && selectedEvent.event_id !== prevIdRef.current) {
      prevIdRef.current = selectedEvent.event_id;
      map.flyTo([selectedEvent.latitude, selectedEvent.longitude], 9, {
        animate: true,
        duration: 1.0,
        easeLinearity: 0.25,
      });
    } else if (!selectedEvent) {
      prevIdRef.current = null;
    }
  }, [selectedEvent, map]);

  return null;
}

// India approximate boundary
const INDIA_CENTER: L.LatLngTuple = [22.5, 82.0];
const INDIA_ZOOM = 5;
const INDIA_BOUNDS = L.latLngBounds(
  L.latLng(6.5, 68.0),
  L.latLng(37.0, 98.0)
);

// Click on empty map area closes opened details drawer AND zooms out to normal initial zoom position
function MapClickHandler({ onMapClick }: { onMapClick: () => void }) {
  const map = useMap();
  useMapEvents({
    click: () => {
      onMapClick();
      map.flyTo(INDIA_CENTER, INDIA_ZOOM, {
        animate: true,
        duration: 1.0,
        easeLinearity: 0.25,
      });
    },
  });
  return null;
}

const SIH_CATEGORIES_LEGEND = [
  { name: 'Industrial Fire', color: '#ef4444' },
  { name: 'Wildfire / Natural', color: '#f97316' },
  { name: 'Agricultural Fire', color: '#eab308' },
  { name: 'Persistent Thermal', color: '#3b82f6' },
  { name: 'Unknown / Other', color: '#6b7280' },
];

export const MapContainer = () => {
  const { data: fetchedEvents, isLoading } = useEvents();
  const { selectedEvent, clearSelection } = useSelectedEventContext();
  const { filters, setFilters } = useFilters();

  const events = useMemo(() => fetchedEvents?.events || [], [fetchedEvents?.events]);
  const isLiveActive = filters.timeRange === 'live' || filters.timeRange === 'today' || filters.timeRange === '24h';

  const toggleLiveMode = (live: boolean) => {
    setFilters({
      ...filters,
      timeRange: live ? 'live' : 'all',
    });
  };

  // Category multi-select & isolate logic:
  // - If all are selected, clicking one isolates to ONLY that category
  // - If a subset is selected, clicking toggles that category in/out
  // - If all are unchecked, reverts back to all 5 active
  const toggleCategory = (catName: string) => {
    const officialName =
      catName === 'Wildfire / Natural'
        ? 'Wildfire / Natural Fire'
        : catName === 'Persistent Thermal'
        ? 'Persistent Thermal Source'
        : catName;

    const allSelected = filters.categories.length === ALL_SIH_CATEGORIES.length;

    if (allSelected) {
      // User was seeing all fires, clicks one: isolate to ONLY this category!
      setFilters({ ...filters, categories: [officialName] });
    } else {
      const exists = filters.categories.includes(officialName);
      if (exists) {
        const remaining = filters.categories.filter((c) => c !== officialName);
        if (remaining.length === 0) {
          // If unchecking the last active category, restore all
          setFilters({ ...filters, categories: [...ALL_SIH_CATEGORIES] });
        } else {
          setFilters({ ...filters, categories: remaining });
        }
      } else {
        const updated = [...filters.categories, officialName];
        setFilters({ ...filters, categories: updated });
      }
    }
  };

  const selectAllCategories = () => {
    setFilters({ ...filters, categories: [...ALL_SIH_CATEGORIES] });
  };

  // Reliable OpenStreetMap basemap tiles (dynamically styled via CSS in dark mode to never go blank or black)
  const tileUrl = 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png';
  const tileAttribution =
    '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

  const isAllCategoriesSelected = filters.categories.length === ALL_SIH_CATEGORIES.length;

  return (
    <div className="relative h-full w-full min-h-0 overflow-hidden bg-gray-50 dark:bg-gray-900 flex-1">
      {/* Floating SIH Category Legend with Professional Modern Checkboxes */}
      <div className="absolute top-4 left-4 z-[1000] flex flex-col gap-2 pointer-events-auto">
        <div className="bg-white/95 dark:bg-gray-900/95 backdrop-blur-md px-3.5 py-3 rounded-2xl shadow-lg border border-gray-100 dark:border-gray-800 w-56">
          <div className="text-[10px] font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2.5 flex items-center justify-between">
            <span>Fire Categories (SIH)</span>
            {!isAllCategoriesSelected ? (
              <button
                onClick={selectAllCategories}
                className="text-[10px] text-red-500 dark:text-red-400 font-bold hover:underline cursor-pointer"
                title="Show all fire categories"
              >
                Show All
              </button>
            ) : (
              <span className="text-[9px] text-gray-400 font-normal">All Visible</span>
            )}
          </div>

          {/* 5 Categories List with Modern Professional Checkboxes */}
          <div className="space-y-1.5 text-[11px]">
            {SIH_CATEGORIES_LEGEND.map((cat) => {
              const officialName =
                cat.name === 'Wildfire / Natural'
                  ? 'Wildfire / Natural Fire'
                  : cat.name === 'Persistent Thermal'
                  ? 'Persistent Thermal Source'
                  : cat.name;
              const isEnabled = filters.categories.includes(officialName);

              return (
                <button
                  key={cat.name}
                  onClick={() => toggleCategory(cat.name)}
                  className="w-full flex items-center justify-between py-1 px-1.5 rounded-lg hover:bg-gray-100/70 dark:hover:bg-gray-800/70 transition-all cursor-pointer text-left group"
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    {/* Modern Professional Checkbox */}
                    <div
                      className={`w-4 h-4 rounded-md flex items-center justify-center border transition-all flex-shrink-0 ${
                        isEnabled
                          ? 'border-transparent text-white shadow-xs'
                          : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800'
                      }`}
                      style={{
                        backgroundColor: isEnabled ? cat.color : undefined,
                      }}
                    >
                      {isEnabled && (
                        <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth="3">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </div>

                    {/* Category Name */}
                    <span
                      className={`truncate text-[11px] font-medium transition-colors ${
                        isEnabled
                          ? 'text-gray-900 dark:text-gray-100 font-semibold'
                          : 'text-gray-400 dark:text-gray-500'
                      }`}
                    >
                      {cat.name}
                    </span>
                  </div>

                  {/* Color pill indicator */}
                  <span
                    className="w-2 h-2 rounded-full flex-shrink-0 ml-1.5"
                    style={{ backgroundColor: cat.color }}
                  />
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Top Right Bar: Live vs Past Mode Toggle + Event Count */}
      <div className="absolute top-4 right-4 z-[1000] flex items-center gap-2 pointer-events-auto">
        {/* Live vs Historical Quick Mode Pills */}
        <div className="bg-white/95 dark:bg-gray-900/95 backdrop-blur-xs p-1 rounded-xl shadow-md border border-gray-100 dark:border-gray-800 flex items-center gap-1">
          <button
            onClick={() => toggleLiveMode(true)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              isLiveActive
                ? 'bg-red-500 text-white shadow-xs'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${isLiveActive ? 'bg-white animate-pulse' : 'bg-red-400'}`} />
            <span>Live Feed</span>
          </button>
          <button
            onClick={() => toggleLiveMode(false)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              !isLiveActive
                ? 'bg-gray-800 dark:bg-gray-700 text-white shadow-xs'
                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
            }`}
          >
            <span>All Records</span>
          </button>
        </div>

        {/* Count Badge */}
        <div className="bg-white/95 dark:bg-gray-900/95 backdrop-blur-xs px-3 py-1.5 rounded-xl shadow-md border border-gray-100 dark:border-gray-800 flex items-center gap-1.5 text-xs">
          <span className="font-bold text-gray-900 dark:text-white">{events.length}</span>
          <span className="text-gray-500 dark:text-gray-400">
            {isLiveActive ? 'live' : 'records'}
          </span>
        </div>
      </div>

      {isLoading && events.length === 0 ? (
        <div className="h-full w-full flex items-center justify-center bg-gray-50 dark:bg-gray-900">
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping" />
            <span>Loading India thermal detections...</span>
          </div>
        </div>
      ) : (
        <LeafletMapContainer
          center={INDIA_CENTER}
          zoom={INDIA_ZOOM}
          scrollWheelZoom={true}
          zoomControl={false}
          maxBounds={INDIA_BOUNDS}
          maxBoundsViscosity={0.8}
          minZoom={4}
          maxZoom={18}
          preferCanvas={true}
          style={{ height: '100%', width: '100%' }}
        >
          {/* Reliable OpenStreetMap basemap tiles */}
          <TileLayer
            key="osm-tiles"
            url={tileUrl}
            attribution={tileAttribution}
            subdomains="abc"
            maxZoom={19}
          />

          {/* Invalidate size on mount / resize */}
          <MapResizer />

          {/* Smooth zoom to clicked dot */}
          <MapViewController selectedEvent={selectedEvent} />

          {/* Click on empty map area deselects details AND flies back to normal initial zoom */}
          <MapClickHandler onMapClick={clearSelection} />

          {/* Zoom + - Control positioned at Bottom Right */}
          <ZoomControl position="bottomright" />

          {/* Fire event markers */}
          {events.map((event) => (
            <EventMarker
              key={event.event_id}
              event={event}
              isSelected={selectedEvent?.event_id === event.event_id}
            />
          ))}
        </LeafletMapContainer>
      )}
    </div>
  );
};