import type { ApiThermalEvent } from '@/types/api';

interface OSMSectionProps {
  event: ApiThermalEvent;
}

export const OSMSection = ({ event }: OSMSectionProps) => {
  const { osm } = event;

  if (!osm) {
    return null;
  }

  const { inside_industrial_zone, nearest_feature_distance_m, feature_count_1km, nearby_water } = osm;

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-lg font-medium">OSM Context</h3>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span>Inside Industrial Zone:</span>
          <span>{inside_industrial_zone !== null && inside_industrial_zone !== undefined ? (inside_industrial_zone ? 'Yes' : 'No') : 'N/A'}</span>
        </div>
        <div className="flex justify-between">
          <span>Nearest Feature Distance:</span>
          <span>
            {nearest_feature_distance_m !== null && nearest_feature_distance_m !== undefined
              ? nearest_feature_distance_m.toFixed(0) + ' m'
              : 'N/A'}
          </span>
        </div>
        <div className="flex justify-between">
          <span>Feature Count (1km):</span>
          <span>
            {feature_count_1km !== null && feature_count_1km !== undefined
              ? feature_count_1km.toString()
              : 'N/A'}
          </span>
        </div>
        <div className="flex justify-between">
          <span>Nearby Water:</span>
          <span>{nearby_water !== null && nearby_water !== undefined ? (nearby_water ? 'Yes' : 'No') : 'N/A'}</span>
        </div>
      </div>
    </div>
  );
};