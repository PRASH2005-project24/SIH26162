import { useState, useEffect } from 'react';
import { useTheme } from '@/context/ThemeContext';
import { useFilters, type TimeRangeOption } from '@/hooks/useFilters';
import { SlidersHorizontal, Clock, Satellite, Sun, Moon } from 'lucide-react';

interface HeaderProps {
  onToggleSidebar: () => void;
}

export const Header = ({ onToggleSidebar }: HeaderProps) => {
  const { theme, toggleTheme } = useTheme();
  const { filters, setFilters } = useFilters();
  const [currentTime, setCurrentTime] = useState(new Date());

  // Update time every minute
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 60000);
    return () => clearInterval(timer);
  }, []);

  const handleTimeRangeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value as TimeRangeOption;
    setFilters({ ...filters, timeRange: value });
  };

  const dateStr = currentTime.toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });

  const dayName = currentTime.toLocaleDateString('en-US', { weekday: 'long' });
  const timeStr = currentTime.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  }).toLowerCase();

  const isDark = theme === 'dark';

  return (
    <header className="bg-white/85 dark:bg-[#0c101c]/85 backdrop-blur-md border-b border-gray-200/80 dark:border-slate-800/80 px-4 sm:px-6 py-2.5 transition-colors z-30">
      <div className="flex items-center justify-between">
        {/* Left Side: Menu button + FIREXIS Logo text + Date/Time display */}
        <div className="flex items-center gap-3 sm:gap-3.5">
          {/* Three lines sidebar drawer button */}
          <button
            onClick={onToggleSidebar}
            className="p-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-white/80 dark:bg-slate-800/80 hover:bg-gray-50 dark:hover:bg-slate-700 text-gray-700 dark:text-gray-200 shadow-xs transition-colors flex items-center gap-2 cursor-pointer group active:scale-95"
            aria-label="Toggle navigation menu"
            title="Open navigation menu"
          >
            <svg className="w-5 h-5 text-gray-600 dark:text-gray-300 group-hover:text-red-500 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
            <span className="text-xs font-bold hidden sm:inline text-gray-700 dark:text-gray-200">
              Menu
            </span>
          </button>

          {/* Logo as Only FIREXIS Text */}
          <span className="text-sm sm:text-base font-black tracking-wider text-gray-900 dark:text-white select-none">
            FIREXIS
          </span>

          {/* Live Date/Time */}
          <div className="flex items-center gap-2 pl-2 border-l border-gray-200/80 dark:border-slate-800">
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
                {dateStr}
              </div>
              <div className="text-[11px] text-gray-400">
                {dayName} {timeStr}
              </div>
            </div>
          </div>
        </div>

        {/* Center: Stitch LEO Orbital Sensor Pass Indicator */}
        <div className="hidden lg:flex items-center gap-2 px-3 py-1 bg-gray-50/80 dark:bg-slate-900/70 border border-gray-200/80 dark:border-slate-800/80 rounded-full text-[11px] font-mono select-none">
          <Satellite className="w-3.5 h-3.5 text-cyan-600 dark:text-cyan-400 shrink-0" />
          <span className="w-2 h-2 rounded-full bg-emerald-500 relative flex items-center justify-center">
            <span className="absolute w-3.5 h-3.5 rounded-full bg-emerald-500/40 animate-radar-ping" />
          </span>
          <span className="text-gray-700 dark:text-gray-300 font-semibold">LEO ORBITAL PASS:</span>
          <span className="text-cyan-600 dark:text-cyan-400 font-bold">VIIRS / SENTINEL-2 ACTIVE</span>
        </div>

        {/* Right Side: Min Confidence Slider + Time Horizon Dropdown + Dark Mode Toggle */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Min Confidence Modern Interactive Slider with Progress Status */}
          <div className="flex items-center gap-2 px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-200/90 dark:border-gray-700/90 rounded-2xl shadow-xs transition-all hover:border-red-300 dark:hover:border-red-900/60">
            <div className="flex items-center gap-1.5 text-xs font-semibold text-gray-700 dark:text-gray-200 select-none">
              <SlidersHorizontal className="w-3.5 h-3.5 text-red-500 shrink-0" />
              <span className="hidden sm:inline">Confidence:</span>
            </div>

            {/* Range Slider with Dynamic Filled Progress Track */}
            <div className="relative flex items-center">
              <input
                type="range"
                min="0"
                max="90"
                step="5"
                value={filters.minConfidence}
                onChange={(e) => {
                  const minConfidence = Number(e.target.value);
                  setFilters((previous) => ({ ...previous, minConfidence }));
                }}
                className="w-16 sm:w-24 md:w-28 h-2 rounded-lg appearance-none cursor-pointer focus:outline-none [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3.5 [&::-webkit-slider-thumb]:h-3.5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white [&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-red-500 [&::-webkit-slider-thumb]:shadow-md [&::-webkit-slider-thumb]:transition-transform [&::-webkit-slider-thumb]:hover:scale-125 [&::-webkit-slider-thumb]:active:scale-95 [&::-moz-range-thumb]:w-3.5 [&::-moz-range-thumb]:h-3.5 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-white [&::-moz-range-thumb]:border-2 [&::-moz-range-thumb]:border-red-500 [&::-moz-range-thumb]:shadow-md [&::-moz-range-thumb]:cursor-pointer"
                style={{
                  background: isDark
                    ? `linear-gradient(to right, #ef4444 0%, #f97316 ${Math.round((filters.minConfidence / 90) * 100)}%, #334155 ${Math.round((filters.minConfidence / 90) * 100)}%, #334155 100%)`
                    : `linear-gradient(to right, #ef4444 0%, #f97316 ${Math.round((filters.minConfidence / 90) * 100)}%, #e2e8f0 ${Math.round((filters.minConfidence / 90) * 100)}%, #e2e8f0 100%)`,
                }}
                title={`Confidence threshold: ${filters.minConfidence}% (slide to adjust)`}
              />
            </div>

            {/* Dynamic Progress Status Badge */}
            <div
              className={`px-2 py-0.5 rounded-lg text-[11px] font-mono font-bold tracking-tight transition-all flex items-center gap-1 shrink-0 ${
                filters.minConfidence === 0
                  ? 'bg-gray-100 dark:bg-gray-700/60 text-gray-600 dark:text-gray-300'
                  : filters.minConfidence < 50
                  ? 'bg-amber-50 dark:bg-amber-950/50 text-amber-600 dark:text-amber-400 border border-amber-200/80 dark:border-amber-900/50'
                  : 'bg-red-50 dark:bg-red-950/50 text-red-600 dark:text-red-400 border border-red-200/80 dark:border-red-900/50'
              }`}
            >
              <span>{filters.minConfidence === 0 ? 'All (0%)' : `≥${filters.minConfidence}%`}</span>
            </div>
          </div>

          {/* Time range selector dropdown with clean Clock icon */}
          <div className="relative">
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-2.5 text-gray-400">
              <Clock className="w-3.5 h-3.5" />
            </div>
            <select
              value={filters.timeRange}
              onChange={handleTimeRangeChange}
              className="appearance-none bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/60 border border-gray-200 dark:border-gray-700 rounded-xl pl-8 pr-7 py-1.5 text-xs font-semibold text-gray-800 dark:text-gray-200 cursor-pointer focus:outline-none transition-colors"
            >
              <option value="live">Live Feed</option>
              <option value="24h">Past 24 Hours</option>
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="all">All Records</option>
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2 text-gray-400">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>

          {/* Dark Mode Toggle Button */}
          <button
            onClick={toggleTheme}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/60 text-xs font-semibold text-gray-700 dark:text-gray-200 shadow-xs transition-colors cursor-pointer"
            aria-label="Toggle Theme"
          >
            {isDark ? (
              <>
                <Sun className="w-4 h-4 text-amber-400" />
                <span className="hidden sm:inline">Light</span>
              </>
            ) : (
              <>
                <Moon className="w-4 h-4 text-gray-700 dark:text-gray-300" />
                <span className="hidden sm:inline">Dark</span>
              </>
            )}
          </button>
        </div>
      </div>
    </header>
  );
};