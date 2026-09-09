import type { ApiThermalEvent } from '@/types/api';

interface DynamicWorldSectionProps {
  event: ApiThermalEvent;
}

export const DynamicWorldSection = ({ event }: DynamicWorldSectionProps) => {
  const { dynamic_world } = event;

  if (!dynamic_world) {
    return null;
  }

  const { land_cover_label, class_probabilities, acquisition_date, query_date, coverage_state } = dynamic_world;

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex justify-between items-start mb-2">
        <h3 className="text-lg font-medium">Dynamic World Land Cover</h3>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span>Label:</span>
          <span>{land_cover_label || 'N/A'}</span>
        </div>
        <div className="flex justify-between">
          <span>Acquisition Date:</span>
          <span>{acquisition_date || 'N/A'}</span>
        </div>
        <div className="flex justify-between">
          <span>Query Date:</span>
          <span>{query_date || 'N/A'}</span>
        </div>
        <div className="flex justify-between">
          <span>Coverage State:</span>
          <span>{coverage_state || 'N/A'}</span>
        </div>

        {/* Show class probabilities if available */}
        {class_probabilities && Object.keys(class_probabilities).length > 0 && (
          <div className="mt-2">
            <span className="font-medium">Class Probabilities:</span>
            <div className="mt-1 space-y-1 text-xs">
              {Object.entries(class_probabilities).map(([className, prob]) => {
                const probability = prob as number;
                return (
                  <div key={className} className="flex justify-between">
                    <span>{className}</span>
                    <span>{(probability * 100).toFixed(1)}%</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};