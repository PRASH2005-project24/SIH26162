import type { NormalizedEvent } from '@/types/normalized';
import { SiHCategoryBadge } from '@/components/ui/SiHCategoryBadge';
import type { SIHCategory } from '@/types/index';
import { useSelectedEventContext } from '@/context/SelectedEventContext';

interface EventItemProps {
  event: NormalizedEvent;
}

export const EventItem = ({ event }: EventItemProps) => {
  const { selectEvent, selectedEvent } = useSelectedEventContext();
  const { event_id, latitude, longitude, frp, classification, confidence, location, risk_score, risk_level, industrial_context, land_cover, raw } = event;

  const sihCategory = classification || 'Unknown / Other';
  const isSelected = selectedEvent?.event_id === event_id;
  const acquisitionTime = raw?.acquisition_time || event.satellite?.acquisition_date || new Date().toISOString();

  return (
    <div
      onClick={() => selectEvent(event)}
      className={`border rounded-xl p-4 transition-all cursor-pointer ${
        isSelected
          ? 'border-red-500 bg-red-50/50 dark:bg-red-950/20 shadow-xs'
          : 'border-gray-200 dark:border-gray-700/80 hover:bg-gray-50 dark:hover:bg-gray-700/40 bg-white dark:bg-gray-800'
      }`}
    >
      <div className="flex justify-between items-start">
        <div>
          <div className="flex items-center gap-2">
            <SiHCategoryBadge category={sihCategory as SIHCategory} />
            <span className="text-xs font-bold text-gray-500">
              {location.city}, {location.state}
            </span>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {new Date(acquisitionTime).toLocaleString()}
          </p>
        </div>
        <div className="text-right">
          <div className="text-xs font-bold text-red-500">
            Score: {risk_score} ({risk_level})
          </div>
          {frp !== null && frp !== undefined && (
            <div className="text-xs text-gray-400 mt-0.5">
              FRP: {frp.toFixed(1)} MW
            </div>
          )}
        </div>
      </div>

      <div className="mt-3 text-xs text-gray-600 dark:text-gray-300 space-y-1">
        <div>
          <span className="font-semibold text-gray-700 dark:text-gray-200">Coordinates:</span> {latitude.toFixed(3)}°, {longitude.toFixed(3)}°
        </div>
        <div>
          <span className="font-semibold text-gray-700 dark:text-gray-200">Confidence:</span> {Math.round(confidence * 100)}%
        </div>
        <div>
          <span className="font-semibold text-gray-700 dark:text-gray-200">Industrial Proximity:</span> {industrial_context.osm_proximity}
        </div>
        <div>
          <span className="font-semibold text-gray-700 dark:text-gray-200">Land Cover (Built):</span> {land_cover.Built}%
        </div>
      </div>
    </div>
  );
};