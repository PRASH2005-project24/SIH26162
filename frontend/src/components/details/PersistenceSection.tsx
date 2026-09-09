import type { ApiThermalEvent } from '@/types/api';

interface PersistenceSectionProps {
  event: ApiThermalEvent;
}

export const PersistenceSection = ({ event }: PersistenceSectionProps) => {
  const { persistence } = event;

  if (!persistence) {
    return null;
  }

  const { is_persistent, date_count, duration_days } = persistence;

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-lg font-medium">Persistence Analysis</h3>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span>Is Persistent:</span>
          <span className={is_persistent ? 'text-green-600' : 'text-gray-600'}>
            {is_persistent ? 'Yes' : 'No'}
          </span>
        </div>
        <div className="flex justify-between">
          <span>Observation Dates:</span>
          <span>{date_count} unique dates</span>
        </div>
        <div className="flex justify-between">
          <span>Duration:</span>
          <span>{duration_days} days</span>
        </div>
        {/* Add more details if available */}
      </div>
    </div>
  );
};