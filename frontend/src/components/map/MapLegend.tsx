import { SiHCategoryBadge } from '@/components/ui/SiHCategoryBadge';
import type { SIHCategory } from '@/types';

interface MapLegendProps {
  visibleCategories: SIHCategory[];
  className?: string;
}

export const MapLegend = ({ visibleCategories, className = '' }: MapLegendProps) => {
  const categoryLabels: Record<SIHCategory, string> = {
    'Industrial Fire': 'Industrial Fire',
    'Wildfire / Natural Fire': 'Wildfire / Natural Fire',
    'Agricultural Fire': 'Agricultural Fire',
    'Persistent Thermal Source': 'Persistent Thermal Source',
    'Unknown / Other': 'Unknown / Other'
  };

  return (
    <div className={`bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 max-h-[200px] overflow-y-auto ${className}`}>
      <h3 className="text-lg font-bold mb-3">Map Legend</h3>
      <div className="space-y-2 text-sm">
        {visibleCategories.map((category) => (
          <div key={category} className="flex items-center space-x-2">
            <SiHCategoryBadge category={category} className="flex-shrink-0" />
            <span>{categoryLabels[category]}</span>
          </div>
        ))}
      </div>
    </div>
  );
};