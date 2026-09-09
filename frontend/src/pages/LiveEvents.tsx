import { MapContainer } from '@/components/map/MapContainer';
import { EventList } from '@/components/events/EventList';
import { StatisticsCards } from '@/components/dashboard/StatisticsCards';
import { useStatistics } from '@/hooks/useStatistics';

export const LiveEvents = () => {
  const { data: statistics } = useStatistics();

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
        Live Events
      </h1>

      {/* Map */}
      <div>
        <MapContainer />
      </div>

      {/* Statistics */}
      <StatisticsCards statistics={statistics ?? null} />

      {/* Event List */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
        <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">
          Live Event Feed
        </h2>
        <EventList />
      </div>
    </div>
  );
};