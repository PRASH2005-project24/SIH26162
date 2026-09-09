import { MapContainer } from '@/components/map/MapContainer';
import { EventList } from '@/components/events/EventList';
import { StatisticsCards } from '@/components/dashboard/StatisticsCards';
import { DateRangePicker } from '@/components/ui/DateRangePicker';
import { useStatistics } from '@/hooks/useStatistics';
import { useFilters } from '@/hooks/useFilters';

export const HistoricalEvents = () => {
  const { data: statistics } = useStatistics();
  const { filters, setFilters } = useFilters();

  const handleDateChange = (startDate: Date | null, endDate: Date | null) => {
    setFilters({
      ...filters,
      timeRange: 'custom',
      customStartDate: startDate,
      customEndDate: endDate,
    });
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
        Historical Events
      </h1>

      {/* Date Range Picker */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
        <DateRangePicker onDateChange={handleDateChange} />
      </div>

      {/* Map */}
      <div>
        <MapContainer />
      </div>

      {/* Statistics */}
      <StatisticsCards statistics={statistics ?? null} />

      {/* Event List */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
        <h2 className="text-lg font-semibold mb-4 text-gray-900 dark:text-gray-100">
          Historical Event Records
        </h2>
        <EventList />
      </div>
    </div>
  );
};