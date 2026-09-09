interface TimeRangeSelectorProps {
  timeRange: 'today' | '24h' | '7d' | '30d' | 'custom';
  onTimeRangeChange: (timeRange: 'today' | '24h' | '7d' | '30d' | 'custom') => void;
}

export const TimeRangeSelector = ({ timeRange, onTimeRangeChange }: TimeRangeSelectorProps) => {
  const timeRanges: Array<{label: string, value: 'today' | '24h' | '7d' | '30d' | 'custom'}> = [
    { label: 'Today', value: 'today' },
    { label: 'Last 24 Hours', value: '24h' },
    { label: 'Last 7 Days', value: '7d' },
    { label: 'Last 30 Days', value: '30d' },
    { label: 'Custom', value: 'custom' }
  ];

  const handleChange = (value: 'today' | '24h' | '7d' | '30d' | 'custom') => {
    onTimeRangeChange(value);
  };

  return (
    <div className="space-y-2">
      <span className="text-sm font-medium text-gray-700 dark:text-gray-400">Time Range:</span>
      <div className="flex flex-wrap gap-2">
        {timeRanges.map(({ label, value }) => (
          <button
            key={label}
            onClick={() => handleChange(value)}
            className={`px-3 py-1 text-sm rounded border border-gray-300 ${timeRange === value ? 'bg-blue-500 text-white' : 'bg-white text-gray-700 dark:bg-gray-800 dark:text-gray-300'} hover:bg-gray-50 dark:hover:bg-gray-700`}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
};