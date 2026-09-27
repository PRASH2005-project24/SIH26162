import { useState, useMemo, useEffect, useRef } from 'react';
import { useEvents } from '@/hooks/useEvents';
import { useFilters, ALL_SIH_CATEGORIES } from '@/hooks/useFilters';
import { SiHCategoryBadge } from '@/components/ui/SiHCategoryBadge';
import type { SIHCategory } from '@/types/index';
import type { NormalizedEvent } from '@/types/normalized';
import { SelectedDetectionCard } from '@/components/dashboard/SelectedDetectionCard';
import { ThermalContextCard } from '@/components/dashboard/ThermalContextCard';
import { LandCoverCard } from '@/components/dashboard/LandCoverCard';
import { SatellitePreviewCard } from '@/components/dashboard/SatellitePreviewCard';
import { Factory, Trees, Wheat, Zap, Sun, Moon, BarChart3, ChevronDown, ShieldCheck, Clock } from 'lucide-react';

export const HistoricalEvents = () => {
  const { data: eventsData, isLoading } = useEvents();
  const { filters, setFilters } = useFilters();

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'date_desc' | 'date_asc' | 'frp_desc' | 'conf_desc'>('date_desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(15);
  const [inspectEvent, setInspectEvent] = useState<NormalizedEvent | null>(null);
  const [isStatsOpen, setIsStatsOpen] = useState(false);
  const statsDropdownRef = useRef<HTMLDivElement>(null);

  // Set filter to 'all' records on mount and handle Escape key for modal inspector
  useEffect(() => {
    setFilters((prev) => ({ ...prev, timeRange: 'all' }));
  }, [setFilters]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && inspectEvent) {
        setInspectEvent(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [inspectEvent]);

  // Dismiss stats dropdown when clicked outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (statsDropdownRef.current && !statsDropdownRef.current.contains(e.target as Node)) {
        setIsStatsOpen(false);
      }
    };
    if (isStatsOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isStatsOpen]);

  const allEvents = eventsData?.events || [];

  // Filter and sort events
  const processedEvents = useMemo(() => {
    let list = [...allEvents];

    // Search query filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter(
        (e) =>
          e.event_id.toLowerCase().includes(q) ||
          e.location.city.toLowerCase().includes(q) ||
          e.location.state.toLowerCase().includes(q) ||
          e.classification.toLowerCase().includes(q)
      );
    }

    // Category filter
    if (selectedCategory !== 'all') {
      list = list.filter((e) => e.classification === selectedCategory);
    }

    // Sort
    list.sort((a, b) => {
      if (sortBy === 'date_desc') {
        return new Date(b.acquisition_time).getTime() - new Date(a.acquisition_time).getTime();
      }
      if (sortBy === 'date_asc') {
        return new Date(a.acquisition_time).getTime() - new Date(b.acquisition_time).getTime();
      }
      if (sortBy === 'frp_desc') {
        return (b.frp ?? 0) - (a.frp ?? 0);
      }
      if (sortBy === 'conf_desc') {
        return (b.confidence ?? 0) - (a.confidence ?? 0);
      }
      return 0;
    });

    return list;
  }, [allEvents, searchQuery, selectedCategory, sortBy]);

  // Pagination
  const totalPages = Math.ceil(processedEvents.length / pageSize) || 1;
  const paginatedEvents = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return processedEvents.slice(start, start + pageSize);
  }, [processedEvents, currentPage, pageSize]);

  // Statistics Summary
  const statsSummary = useMemo(() => {
    const total = allEvents.length;
    const industrial = allEvents.filter((e) => e.classification === 'Industrial Fire').length;
    const wildfire = allEvents.filter((e) => e.classification === 'Wildfire / Natural Fire').length;
    const agricultural = allEvents.filter((e) => e.classification === 'Agricultural Fire').length;
    const persistent = allEvents.filter((e) => e.classification === 'Persistent Thermal Source').length;
    const avgFrp = allEvents.reduce((s, e) => s + (e.frp || 0), 0) / (total || 1);
    const avgConf = allEvents.reduce((s, e) => s + (e.confidence <= 1 ? e.confidence * 100 : e.confidence), 0) / (total || 1);

    return { total, industrial, wildfire, agricultural, persistent, avgFrp, avgConf };
  }, [allEvents]);

  // CSV Export handler
  const handleExportCSV = () => {
    const headers = [
      'Event ID',
      'Acquisition Time',
      'City',
      'State',
      'Latitude',
      'Longitude',
      'SIH Classification',
      'Confidence %',
      'FRP (MW)',
      'Brightness (K)',
      'Satellite',
      'Instrument',
      'Day/Night',
      'Industrial Zone',
      'Persistence',
    ];

    const rows = processedEvents.map((e) => [
      e.event_id,
      e.acquisition_time,
      e.location.city,
      e.location.state,
      e.latitude,
      e.longitude,
      `"${e.classification}"`,
      Math.round(e.confidence <= 1 ? e.confidence * 100 : e.confidence),
      e.frp ?? '',
      e.brightness ?? '',
      e.satellite_name,
      e.instrument || '',
      e.day_night || '',
      e.industrial_context?.inside_industrial_zone == null
        ? 'Not available'
        : e.industrial_context.inside_industrial_zone ? 'Yes' : 'No',
      `"${e.persistence}"`,
    ]);

    const csvContent =
      'data:text/csv;charset=utf-8,' +
      [headers.join(','), ...rows.map((r) => r.join(','))].join('\n');

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `fireguard_historical_records_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="h-full w-full flex-1 flex flex-col overflow-y-auto bg-gray-50 dark:bg-gray-900 p-4 sm:p-6 space-y-5 max-w-[1600px] mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-gray-200 dark:border-gray-800">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-red-50 dark:bg-red-950/50 text-red-600 dark:text-red-400 flex items-center justify-center border border-red-200 dark:border-red-900/50">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 10h18M3 14h18m-9-4v8m-7 4h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h1 className="text-xl sm:text-2xl font-black text-gray-900 dark:text-white tracking-tight">
              Historical Thermal Records
            </h1>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            Database of archived NASA FIRMS thermal anomaly observations and Stage 2 ML predictions
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-bold px-3 py-1.5 rounded-xl bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 border border-gray-200 dark:border-gray-700 shadow-xs">
            {processedEvents.length} Records Found
          </span>
          <button
            onClick={handleExportCSV}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-red-500 hover:bg-red-600 text-white text-xs font-bold shadow-xs transition-colors cursor-pointer"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Filter & Toolbar Controls */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/80 rounded-2xl p-3.5 shadow-xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2.5 flex-1">
          {/* Search Box */}
          <div className="relative min-w-[200px] flex-1 sm:flex-none">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setCurrentPage(1);
              }}
              placeholder="Filter by city, state, or event ID..."
              className="w-full pl-8 pr-3 py-1.5 text-xs bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-800 dark:text-gray-200 placeholder-gray-400 focus:outline-none focus:border-red-500 transition-colors"
            />
            <svg className="w-3.5 h-3.5 text-gray-400 absolute left-2.5 top-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>

          {/* Category Dropdown */}
          <select
            value={selectedCategory}
            onChange={(e) => {
              setSelectedCategory(e.target.value);
              setCurrentPage(1);
            }}
            className="text-xs py-1.5 px-3 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-800 dark:text-gray-200 focus:outline-none cursor-pointer"
          >
            <option value="all">All SIH Categories</option>
            {ALL_SIH_CATEGORIES.map((cat) => (
              <option key={cat} value={cat}>
                {cat}
              </option>
            ))}
          </select>

          {/* Date Filter Component (Time Range) */}
          <div className="relative flex items-center">
            <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-2.5 text-gray-400">
              <Clock className="w-3.5 h-3.5" />
            </div>
            <select
              value={filters.timeRange}
              onChange={(e) => setFilters({ ...filters, timeRange: e.target.value as any })}
              className="appearance-none text-xs py-1.5 pl-8 pr-7 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-800 dark:text-gray-200 focus:outline-none cursor-pointer"
              title="Filter by observation date range"
            >
              <option value="all">All Records</option>
              <option value="30d">Last 30 Days</option>
              <option value="7d">Last 7 Days</option>
              <option value="24h">Past 24 Hours</option>
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2 text-gray-400">
              <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>

          {/* Combined Total Observations Dropdown Component (Side of Date Filter) */}
          <div className="relative" ref={statsDropdownRef}>
            <button
              onClick={() => setIsStatsOpen(!isStatsOpen)}
              className={`flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-xl border transition-all cursor-pointer ${
                isStatsOpen
                  ? 'bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 border-red-300 dark:border-red-800 shadow-xs'
                  : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 border-gray-200 dark:border-gray-700'
              }`}
              title="Click to view total observations and category statistics breakdown"
            >
              <BarChart3 className="w-3.5 h-3.5 text-red-500 shrink-0" />
              <span>Total Observations:</span>
              <span className="font-mono font-bold text-red-600 dark:text-red-400">
                {statsSummary.total}
              </span>
              <ChevronDown className={`w-3.5 h-3.5 text-gray-400 transition-transform duration-200 ${isStatsOpen ? 'rotate-180' : ''}`} />
            </button>

            {/* Total Observations Dropdown Menu Popover */}
            {isStatsOpen && (
              <div className="absolute left-0 mt-2 w-72 sm:w-80 bg-white/95 dark:bg-gray-800/95 backdrop-blur-xl border border-gray-200 dark:border-gray-700 rounded-2xl shadow-xl p-3.5 z-30 space-y-2.5 animate-in fade-in zoom-in-95 duration-150">
                <div className="flex items-center justify-between pb-2 border-b border-gray-100 dark:border-gray-700">
                  <div className="flex items-center gap-1.5">
                    <BarChart3 className="w-4 h-4 text-red-500" />
                    <span className="text-xs font-bold text-gray-900 dark:text-white">Observations Breakdown</span>
                  </div>
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-red-100 dark:bg-red-900/50 text-red-600 dark:text-red-300">
                    {statsSummary.total} Total
                  </span>
                </div>

                <div className="space-y-1.5 text-xs">
                  <div className="flex items-center justify-between p-2 rounded-xl bg-red-50/70 dark:bg-red-950/30 border border-red-100 dark:border-red-900/30">
                    <div className="flex items-center gap-2 text-red-600 dark:text-red-400 font-semibold">
                      <Factory className="w-3.5 h-3.5 shrink-0" />
                      <span>Industrial Fire</span>
                    </div>
                    <span className="font-bold font-mono text-red-700 dark:text-red-300">{statsSummary.industrial}</span>
                  </div>

                  <div className="flex items-center justify-between p-2 rounded-xl bg-orange-50/70 dark:bg-orange-950/30 border border-orange-100 dark:border-orange-900/30">
                    <div className="flex items-center gap-2 text-orange-600 dark:text-orange-400 font-semibold">
                      <Trees className="w-3.5 h-3.5 shrink-0" />
                      <span>Wildfire / Natural</span>
                    </div>
                    <span className="font-bold font-mono text-orange-700 dark:text-orange-300">{statsSummary.wildfire}</span>
                  </div>

                  <div className="flex items-center justify-between p-2 rounded-xl bg-amber-50/70 dark:bg-amber-950/30 border border-amber-100 dark:border-amber-900/30">
                    <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400 font-semibold">
                      <Wheat className="w-3.5 h-3.5 shrink-0" />
                      <span>Agricultural Fire</span>
                    </div>
                    <span className="font-bold font-mono text-amber-700 dark:text-amber-300">{statsSummary.agricultural}</span>
                  </div>

                  <div className="flex items-center justify-between p-2 rounded-xl bg-blue-50/70 dark:bg-blue-950/30 border border-blue-100 dark:border-blue-900/30">
                    <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400 font-semibold">
                      <Zap className="w-3.5 h-3.5 shrink-0" />
                      <span>Persistent Thermal</span>
                    </div>
                    <span className="font-bold font-mono text-blue-700 dark:text-blue-300">{statsSummary.persistent}</span>
                  </div>

                  <div className="flex items-center justify-between p-2 rounded-xl bg-emerald-50/70 dark:bg-emerald-950/30 border border-emerald-100 dark:border-emerald-900/30">
                    <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-semibold">
                      <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
                      <span>Avg. Confidence</span>
                    </div>
                    <span className="font-bold font-mono text-emerald-700 dark:text-emerald-300">{Math.round(statsSummary.avgConf)}%</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Date Sort Dropdown */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="text-xs py-1.5 px-3 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-700 rounded-xl text-gray-800 dark:text-gray-200 focus:outline-none cursor-pointer"
          >
            <option value="date_desc">Date: Newest First</option>
            <option value="date_asc">Date: Oldest First</option>
            <option value="frp_desc">Thermal Intensity (FRP)</option>
            <option value="conf_desc">Confidence</option>
          </select>
        </div>

        {/* Rows per page */}
        <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
          <span>Rows:</span>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setCurrentPage(1);
            }}
            className="text-xs py-1 px-2 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-800 dark:text-gray-200 cursor-pointer"
          >
            <option value={10}>10</option>
            <option value={15}>15</option>
            <option value={25}>25</option>
            <option value={50}>50</option>
          </select>
        </div>
      </div>

      {/* Historical Records Table */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700/80 rounded-2xl shadow-xs overflow-hidden flex-1 flex flex-col">
        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-gray-50 dark:bg-gray-700/50 border-b border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-300 font-bold uppercase text-[10px] tracking-wider">
                <th className="py-3 px-4">Event ID</th>
                <th className="py-3 px-4">Acquisition Time</th>
                <th className="py-3 px-4">Location</th>
                <th className="py-3 px-4">SIH Classification</th>
                <th className="py-3 px-4">Confidence</th>
                <th className="py-3 px-4">Thermal FRP</th>
                <th className="py-3 px-4">Brightness</th>
                <th className="py-3 px-4">Sensor / Sat</th>
                <th className="py-3 px-4">OSM Industrial</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700/60">
              {isLoading ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center text-gray-400">
                    <span className="inline-block w-4 h-4 border-2 border-red-500 border-t-transparent rounded-full animate-spin mr-2" />
                    Loading historical thermal records...
                  </td>
                </tr>
              ) : paginatedEvents.length === 0 ? (
                <tr>
                  <td colSpan={10} className="py-12 text-center text-gray-400">
                    No thermal detection records match the current filter criteria.
                  </td>
                </tr>
              ) : (
                paginatedEvents.map((event) => {
                  const confPct = Math.round(event.confidence <= 1 ? event.confidence * 100 : event.confidence);
                  const isDay = event.day_night === 'D';

                  return (
                    <tr
                      key={event.event_id}
                      onClick={() => setInspectEvent(event)}
                      className="hover:bg-gray-50/80 dark:hover:bg-gray-700/40 transition-colors cursor-pointer"
                    >
                      {/* ID */}
                      <td className="py-3 px-4 font-mono font-bold text-gray-900 dark:text-white">
                        #{event.event_id}
                      </td>

                      {/* Date / Time */}
                      <td className="py-3 px-4 text-gray-600 dark:text-gray-300 whitespace-nowrap">
                        <div className="font-semibold text-gray-800 dark:text-gray-200">
                          {new Date(event.acquisition_time).toLocaleDateString('en-IN', {
                            day: 'numeric',
                            month: 'short',
                            year: 'numeric',
                          })}
                        </div>
                        <div className="text-[10px] text-gray-400 flex items-center gap-1 mt-0.5">
                          <span className="inline-flex items-center gap-1 font-medium">
                            {isDay ? <Sun className="w-3 h-3 text-amber-500" /> : <Moon className="w-3 h-3 text-indigo-400" />}
                            <span>{isDay ? 'Day' : 'Night'}</span>
                          </span>
                          <span>•</span>
                          <span>
                            {new Date(event.acquisition_time).toLocaleTimeString('en-IN', {
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </span>
                        </div>
                      </td>

                      {/* Location */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        <div className="font-bold text-gray-900 dark:text-white">
                          {event.location.city}, {event.location.state}
                        </div>
                        <div className="text-[10px] text-gray-400 font-mono mt-0.5">
                          {event.latitude.toFixed(3)}°N, {event.longitude.toFixed(3)}°E
                        </div>
                      </td>

                      {/* Classification */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        <SiHCategoryBadge category={event.classification as SIHCategory} />
                      </td>

                      {/* Confidence */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className="font-bold text-emerald-600 dark:text-emerald-400">
                          {confPct}%
                        </span>
                      </td>

                      {/* FRP */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className="font-bold text-gray-900 dark:text-white">
                          {event.frp != null ? `${Number(event.frp).toFixed(1)} MW` : '--'}
                        </span>
                      </td>

                      {/* Brightness */}
                      <td className="py-3 px-4 whitespace-nowrap text-gray-600 dark:text-gray-300">
                        {event.brightness != null ? `${Number(event.brightness).toFixed(1)} K` : '--'}
                      </td>

                      {/* Sensor */}
                      <td className="py-3 px-4 whitespace-nowrap text-gray-600 dark:text-gray-300">
                        <div className="font-medium text-gray-800 dark:text-gray-200">{event.satellite_name}</div>
                        <div className="text-[10px] text-gray-400">{event.instrument || 'Not available'}</div>
                      </td>

                      {/* OSM Industrial */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span
                          className={`text-[10px] font-semibold px-2 py-0.5 rounded-md ${
                            event.industrial_context?.inside_industrial_zone == null
                              ? 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-300'
                              : event.industrial_context.inside_industrial_zone
                              ? 'bg-red-50 dark:bg-red-950/50 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-900/60'
                              : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300'
                          }`}
                        >
                          {event.industrial_context?.inside_industrial_zone == null
                            ? 'Not available'
                            : event.industrial_context.inside_industrial_zone ? 'Industrial Zone' : 'Outside Zone'}
                        </span>
                      </td>

                      {/* Action */}
                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setInspectEvent(event);
                          }}
                          className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-gray-100 dark:bg-gray-700 hover:bg-red-500 hover:text-white text-gray-700 dark:text-gray-200 transition-colors cursor-pointer"
                        >
                          Inspect
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Footer */}
        <div className="px-5 py-3 border-t border-gray-200 dark:border-gray-700/80 flex items-center justify-between text-xs bg-gray-50/60 dark:bg-gray-800/60">
          <div className="text-gray-500 dark:text-gray-400">
            Page <strong className="text-gray-900 dark:text-white">{currentPage}</strong> of{' '}
            <strong className="text-gray-900 dark:text-white">{totalPages}</strong> (
            {processedEvents.length} total records)
          </div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed font-semibold text-gray-700 dark:text-gray-200 cursor-pointer"
            >
              Previous
            </button>
            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1.5 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-40 disabled:cursor-not-allowed font-semibold text-gray-700 dark:text-gray-200 cursor-pointer"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Modal Inspector Drawer for Clicked Record */}
      {inspectEvent && (
        <div
          className="fixed inset-0 z-[9999] bg-black/60 backdrop-blur-xs flex items-center justify-center p-4 sm:p-6"
          onClick={() => setInspectEvent(null)}
        >
          <div
            className="bg-white/95 dark:bg-[#0c101c]/95 backdrop-blur-xl rounded-3xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl border border-gray-200/80 dark:border-slate-800 flex flex-col animate-drawer-in"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="px-6 py-4 border-b border-gray-200/80 dark:border-slate-800 flex items-center justify-between bg-gray-50/80 dark:bg-slate-900/80">
              <div className="flex items-center gap-2.5">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse" />
                <h3 className="text-base font-bold text-gray-900 dark:text-white">
                  Historical Record Analysis #{inspectEvent.event_id}
                </h3>
              </div>
              <button
                onClick={() => setInspectEvent(null)}
                className="p-1.5 rounded-xl text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-200/70 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                title="Close (Esc)"
              >
                ✕
              </button>
            </div>

            {/* Modal Content Cards */}
            <div className="p-6 overflow-y-auto custom-scrollbar space-y-5 flex-1">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <SelectedDetectionCard event={inspectEvent} onClose={() => setInspectEvent(null)} />
                <ThermalContextCard event={inspectEvent} />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <LandCoverCard landCover={inspectEvent.land_cover} />
                <SatellitePreviewCard
                  satellite={inspectEvent.satellite}
                  acquisitionDate={inspectEvent.acquisition_time}
                  cloudCoverage={inspectEvent.satellite?.cloud_cover}
                  coordinates={{ lat: inspectEvent.latitude, lng: inspectEvent.longitude }}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};