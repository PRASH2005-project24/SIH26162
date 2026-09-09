import { useTheme } from '@/context/ThemeContext';
import { useFilters } from '@/hooks/useFilters';

interface HeaderProps {
  onToggleSidebar: () => void;
}

export const Header = ({ onToggleSidebar }: HeaderProps) => {
  const { theme, toggleTheme } = useTheme();
  const { filters, setFilters } = useFilters();

  const handleTimeRangeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value as '24h' | '7d' | '30d' | 'custom';
    setFilters({ ...filters, timeRange: value });
  };

  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-100 dark:border-gray-700/80 px-6 py-3.5">
      <div className="flex items-center justify-between">
        {/* Left Side: Mobile toggle + Date display matching screenshot */}
        <div className="flex items-center gap-3">
          {/* Mobile sidebar toggle */}
          <button
            onClick={onToggleSidebar}
            className="md:hidden p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300"
            aria-label="Toggle sidebar"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>

          {/* Calendar Icon + Date */}
          <div className="flex items-center gap-2.5">
            <div className="text-gray-400">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
            </div>
            <div>
              <div className="text-xs font-bold text-gray-900 dark:text-white leading-tight">
                9 Sept 2026
              </div>
              <div className="text-[11px] text-gray-400">
                Wednesday 11:40 am
              </div>
            </div>
          </div>
        </div>

        {/* Right Side: Filter Icon + Time Range Dropdown + Dark Mode Button */}
        <div className="flex items-center gap-3">
          {/* Filter icon button */}
          <button
            className="p-2 rounded-xl text-gray-500 hover:text-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/60 transition-colors"
            aria-label="Filter"
            title="Filter Detections"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M10 18h4v-2h-4v2zM3 6v2h18V6H3zm3 7h12v-2H6v2z" />
            </svg>
          </button>

          {/* Time range selector dropdown: '1 week ago' in screenshot */}
          <div className="relative">
            <select
              value={filters.timeRange}
              onChange={handleTimeRangeChange}
              className="appearance-none bg-transparent hover:bg-gray-50 dark:hover:bg-gray-700/40 border border-gray-200 dark:border-gray-700 rounded-xl px-3.5 py-1.5 pr-8 text-xs font-medium text-gray-700 dark:text-gray-200 cursor-pointer focus:outline-none transition-colors"
            >
              <option value="24h">24 hours</option>
              <option value="7d">1 week ago</option>
              <option value="30d">1 month ago</option>
              <option value="custom">All time</option>
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2.5 text-gray-400">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>

          {/* Dark Mode Toggle Pill Button */}
          <button
            onClick={toggleTheme}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/60 text-xs font-medium text-gray-700 dark:text-gray-200 shadow-xs transition-colors"
          >
            {theme === 'dark' ? (
              <svg className="w-3.5 h-3.5 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            ) : (
              <svg className="w-3.5 h-3.5 text-gray-700" fill="currentColor" viewBox="0 0 24 24">
                <path d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
            <span>Dark Mode</span>
          </button>
        </div>
      </div>
    </header>
  );
};