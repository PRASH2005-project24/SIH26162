import { useFilters } from '@/hooks/useFilters';
import { SiHCategoryCheckbox } from '@/components/ui/SiHCategoryCheckbox';
import { TimeRangeSelector } from '@/components/ui/TimeRangeSelector';
import { DateRangePicker } from '@/components/ui/DateRangePicker';
import type { SIHCategory } from '@/types/index';

export const EventFilters = () => {
  const { filters, setFilters } = useFilters();

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4">
      <div className="space-y-4">
        <div className="flex flex-wrap gap-4">
          <TimeRangeSelector
            timeRange={filters.timeRange}
            onTimeRangeChange={(timeRange) => {
              setFilters({
                ...filters,
                timeRange,
                // Reset custom dates when switching from custom to preset
                ...(timeRange !== 'custom' ? { customStartDate: null, customEndDate: null } : {})
              });
            }}
          />
          {filters.timeRange === 'custom' && (
            <DateRangePicker
              onDateChange={(startDate, endDate) => {
                setFilters({
                  ...filters,
                  customStartDate: startDate,
                  customEndDate: endDate
                });
              }}
            />
          )}
        </div>
        <div className="space-x-3">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-400">Categories:</span>
          <div className="flex flex-wrap gap-2">
            {[
              'Industrial Fire',
              'Wildfire / Natural Fire',
              'Agricultural Fire',
              'Persistent Thermal Source',
              'Unknown / Other'
            ].map((category) => (
              <SiHCategoryCheckbox
                key={category}
                category={category as SIHCategory}
                checked={filters.categories.includes(category)}
                onChange={(cat: SIHCategory, checked: boolean) => {
                  const newCategories = checked
                    ? [...filters.categories, cat]
                    : filters.categories.filter(catItem => catItem !== cat);
                  setFilters({
                    ...filters,
                    categories: newCategories
                  });
                }}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};