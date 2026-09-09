import { useEffect } from 'react';
import { MapContainer } from '@/components/map/MapContainer';
import { SelectedDetectionCard } from '@/components/dashboard/SelectedDetectionCard';
import { QuickSummaryCard } from '@/components/dashboard/QuickSummaryCard';
import { LandCoverCard } from '@/components/dashboard/LandCoverCard';
import { SatellitePreviewCard } from '@/components/dashboard/SatellitePreviewCard';
import { useEvents } from '@/hooks/useEvents';
import { useStatistics } from '@/hooks/useStatistics';
import { useSelectedEventContext } from '@/context/SelectedEventContext';

export const Dashboard = () => {
  const { data: eventsData } = useEvents();
  const { data: statistics } = useStatistics();
  const { selectedEvent, selectEvent, clearSelection } = useSelectedEventContext();

  const events = eventsData?.events || [];

  // Automatically select the first / most critical event on first load if none is selected
  useEffect(() => {
    if (!selectedEvent && events.length > 0) {
      // Find event with highest risk score or FRP, or default to first
      const topEvent = [...events].sort((a, b) => (b.risk_score ?? 0) - (a.risk_score ?? 0))[0] || events[0];
      selectEvent(topEvent);
    }
  }, [events, selectedEvent, selectEvent]);

  return (
    <div className="p-5 space-y-5 max-w-[1600px] mx-auto">
      {/* Top Row: Map (Col 8) + Selected Detection (Col 4) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left: Map */}
        <div className="lg:col-span-8">
          <MapContainer />
        </div>

        {/* Right: Selected Detection */}
        <div className="lg:col-span-4">
          <SelectedDetectionCard
            event={selectedEvent}
            onClose={clearSelection}
          />
        </div>
      </div>

      {/* Bottom Row: 3 Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Card 1: Quick Summary */}
        <QuickSummaryCard statistics={statistics} />

        {/* Card 2: Land Cover (Dynamic World) */}
        <LandCoverCard
          landCover={selectedEvent?.land_cover}
          dominantLabel="Built"
        />

        {/* Card 3: Satellite Image (Sentinel-2) */}
        <SatellitePreviewCard
          satellite={selectedEvent?.satellite}
          acquisitionDate={selectedEvent?.raw?.acquisition_time}
          cloudCoverage={selectedEvent?.satellite?.cloud_cover ?? 20}
        />
      </div>
    </div>
  );
};