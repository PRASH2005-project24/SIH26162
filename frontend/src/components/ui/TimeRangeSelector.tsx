import type { TimeRangeOption } from '@/hooks/useFilters';

interface TimeRangeSelectorProps {
  timeRange: TimeRangeOption;
  onTimeRangeChange: (timeRange: TimeRangeOption) => void;
}

export const TimeRangeSelector = ({ timeRange, onTimeRangeChange }: TimeRangeSelectorProps) => {
  const timeRanges: Array<{ label: string; value: TimeRangeOption; badge?: string }> = [
    { label: 'Live (12h)', value: 'live', badge: 'Active' },
    { label: '24 Hours', value: '24h' },
    { label: '7 Days', value: '7d' },
    { label: '30 Days', value: '30d' },
    { label: 'All Records', value: 'all' },
    { label: 'Custom Date', value: 'custom' },
  ];

  return (
    <div className="space-y-1.5">
      <span className="text-xs font-bold text-gray-700 dark:text-gray-300">Time Range:</span>
      <div className="flex flex-wrap gap-1.5">
        {timeRanges.map(({ label, value }) => {
          const isSelected = timeRange === value;
          return (
            <button
              key={value}
              type="button"
              onClick={() => onTimeRangeChange(value)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-xl border transition-all cursor-pointer ${
                isSelected
                  ? 'bg-red-500 border-red-500 text-white shadow-xs'
                  : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700/50'
              }`}
            >
              {label}
            </button>
          );
        })}
      </div>
    </div>
  );
};