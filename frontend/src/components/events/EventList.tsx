import { useEvents } from '@/hooks/useEvents';
import { EventItem } from './EventItem';
import { EventFilters } from './EventFilters';
import type { NormalizedEvent } from '@/types/normalized';

export const EventList = () => {
  const { data, isLoading, error } = useEvents();

  if (isLoading) return <div className="p-4 text-xs text-gray-500">Loading events...</div>;
  if (error) return <div className="p-4 text-xs text-red-500">Error loading events: {error.message}</div>;

  const events = data?.events || [];

  if (events.length === 0) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-500 text-xs">No events found</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <EventFilters />
      <div className="space-y-2 max-h-[500px] overflow-y-auto pr-1">
        {events.map((event: NormalizedEvent) => (
          <EventItem key={event.event_id} event={event} />
        ))}
      </div>
    </div>
  );
};