import { useFilters, type TimeRangeOption } from '@/hooks/useFilters';
import { SiHCategoryCheckbox } from '@/components/ui/SiHCategoryCheckbox';
import { TimeRangeSelector } from '@/components/ui/TimeRangeSelector';
import { DateRangePicker } from '@/components/ui/DateRangePicker';
import type { SIHCategory } from '@/types/index';

export const EventFilters = () => {
  const { filters, setFilters } = useFilters();

  return (
    <div className="bg-white/80 dark:bg-slate-900/60 backdrop-blur-md border border-gray-200/80 dark:border-slate-800/80 rounded-2xl p-5 mb-5 shadow-xs">
      <div className="space-y-4">
        {/* Time Range Selector */}
        <div className="flex flex-wrap items-center gap-4">
          <TimeRangeSelector
            timeRange={filters.timeRange}
            onTimeRangeChange={(timeRange: TimeRangeOption) => {
              setFilters({
                ...filters,
                timeRange,
                // Reset custom dates when switching away from custom
                ...(timeRange !== 'custom' ? { customStartDate: null, customEndDate: null } : {}),
              });
            }}
          />
          {filters.timeRange === 'custom' && (
            <DateRangePicker
              onDateChange={(startDate, endDate) => {
                setFilters({
                  ...filters,
                  customStartDate: startDate,
                  customEndDate: endDate,
                });
              }}
            />
          )}
        </div>

        {/* Categories Checkbox Grid */}
        <div className="pt-3 border-t border-gray-100 dark:border-gray-700/60">
          <span className="text-xs font-bold text-gray-700 dark:text-gray-300 block mb-2">
            Categories (SIH):
          </span>
          <div className="flex flex-wrap gap-2">
            {[
              'Industrial Fire',
              'Wildfire / Natural Fire',
              'Agricultural Fire',
              'Persistent Thermal Source',
              'Unknown / Other',
            ].map((category) => (
              <SiHCategoryCheckbox
                key={category}
                category={category as SIHCategory}
                checked={filters.categories.includes(category)}
                onChange={(cat: SIHCategory, checked: boolean) => {
                  const newCategories = checked
                    ? [...filters.categories, cat]
                    : filters.categories.filter((catItem) => catItem !== cat);
                  setFilters({
                    ...filters,
                    categories: newCategories,
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