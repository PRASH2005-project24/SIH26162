import { useMemo } from 'react';
import { MapContainer as LeafletMapContainer, TileLayer } from 'react-leaflet';
import { useEvents } from '@/hooks/useEvents';
import { EventMarker } from './EventMarker';
import { useSelectedEventContext } from '@/context/SelectedEventContext';

export const MapContainer = () => {
  const { data: fetchedEvents, isLoading, error } = useEvents();
  const { selectedEvent } = useSelectedEventContext();

  const events = useMemo(() => fetchedEvents?.events || [], [fetchedEvents]);

  if (isLoading && events.length === 0) {
    return (
      <div className="h-[420px] rounded-2xl border border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50 flex items-center justify-center">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
          <span>Loading live detections...</span>
        </div>
      </div>
    );
  }

  if (error && events.length === 0) {
    return (
      <div className="h-[420px] rounded-2xl border border-red-100 dark:border-red-900/30 bg-red-50/50 dark:bg-red-950/20 flex items-center justify-center p-6 text-center">
        <div className="text-red-500 text-xs">Error loading map: {error.message}</div>
      </div>
    );
  }

  return (
    <div className="relative h-[420px] w-full rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
      {/* Floating Risk Level Legend (matches screenshot top-left) */}
      <div className="absolute top-4 left-4 z-[1000] bg-white/95 dark:bg-gray-900/95 backdrop-blur-xs px-3.5 py-3 rounded-xl shadow-md border border-gray-100 dark:border-gray-800">
        <div className="text-[11px] font-bold text-gray-800 dark:text-gray-200 mb-2">
          Risk Level
        </div>
        <div className="space-y-1.5 text-[11px]">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#ef4444]" />
            <span className="text-gray-600 dark:text-gray-400">High</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#f97316]" />
            <span className="text-gray-600 dark:text-gray-400">Medium</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#22c55e]" />
            <span className="text-gray-600 dark:text-gray-400">Low</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#6366f1]" />
            <span className="text-gray-600 dark:text-gray-400">Cluster</span>
          </div>
        </div>
      </div>

      <LeafletMapContainer
        center={[22.5, 79.5]}
        zoom={4.8}
        scrollWheelZoom={true}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
        {events.map((event) => (
          <EventMarker
            key={event.event_id}
            event={event}
            isSelected={selectedEvent?.event_id === event.event_id}
          />
        ))}
      </LeafletMapContainer>
    </div>
  );
};