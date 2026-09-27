import { useEffect } from 'react';
import { MapContainer } from '@/components/map/MapContainer';
import { EventList } from '@/components/events/EventList';
import { StatisticsCards } from '@/components/dashboard/StatisticsCards';
import { useStatistics } from '@/hooks/useStatistics';
import { useFilters } from '@/hooks/useFilters';
import { useEvents } from '@/hooks/useEvents';

export const LiveEvents = () => {
  const { data: statistics } = useStatistics();
  const { setFilters } = useFilters();
  const { data: eventsData } = useEvents();

  // Set filter to live on mount
  useEffect(() => {
    setFilters((prev) => ({ ...prev, timeRange: 'live' }));
  }, [setFilters]);

  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping" />
            <h1 className="text-2xl font-black text-gray-900 dark:text-gray-100 tracking-tight">
              Live Fire Detections
            </h1>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Real-time NASA FIRMS thermal anomaly feed across India (last 12 hours)
          </p>
        </div>
        <span className="text-xs font-bold px-3 py-1.5 rounded-xl bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800">
          {eventsData?.events?.length ?? 0} Active Events
        </span>
      </div>

      {/* Map */}
      <MapContainer />

      {/* Statistics */}
      <StatisticsCards statistics={statistics ?? null} />

      {/* Event List */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/80 rounded-2xl p-6 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-bold text-gray-900 dark:text-gray-100 tracking-tight">
            Active Detections Stream
          </h2>
          <span className="text-xs text-gray-400">
            Auto-refreshing every 30s
          </span>
        </div>
        <EventList />
      </div>
    </div>
  );
};