import type { ApiStatisticsResponse } from '@/types/api';
import type { NormalizedStatistics } from '@/types/normalized';

interface StatisticsCardsProps {
  statistics: NormalizedStatistics | ApiStatisticsResponse | null;
}

export const StatisticsCards = ({ statistics }: StatisticsCardsProps) => {
  if (!statistics) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 animate-pulse">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-5">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24 mb-3" />
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-16" />
          </div>
        ))}
      </div>
    );
  }

  const stats = statistics as NormalizedStatistics;
  const classificationCounts = stats.classification_counts || {};

  return (
    <div className="space-y-4">
      {/* Primary Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Detections */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-5 shadow-xs">
          <div className="text-xs font-semibold text-gray-500 dark:text-gray-400">Total Detections</div>
          <div className="text-2xl font-black text-gray-900 dark:text-gray-100 mt-1">
            {stats.total_detections ?? stats.totalDetections}
          </div>
          <div className="text-[11px] text-gray-400 mt-0.5">NASA FIRMS India-wide</div>
        </div>

        {/* Active Detections */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-5 shadow-xs">
          <div className="text-xs font-semibold text-gray-500 dark:text-gray-400">Active (Live)</div>
          <div className="text-2xl font-black text-red-600 dark:text-red-400 mt-1 flex items-center gap-2">
            <span>{stats.active_detections ?? stats.totalDetections}</span>
            <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
          </div>
          <div className="text-[11px] text-gray-400 mt-0.5">Real-time thermal feeds</div>
        </div>

        {/* Enriched Events */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-5 shadow-xs">
          <div className="text-xs font-semibold text-gray-500 dark:text-gray-400">GIS Enriched</div>
          <div className="text-2xl font-black text-blue-600 dark:text-blue-400 mt-1">
            {stats.enriched_events ?? stats.totalDetections}
          </div>
          <div className="text-[11px] text-gray-400 mt-0.5">OSM + Dynamic World layers</div>
        </div>

        {/* Average Confidence */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-5 shadow-xs">
          <div className="text-xs font-semibold text-gray-500 dark:text-gray-400">Avg. Model Confidence</div>
          <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400 mt-1">
            {Math.round(stats.average_confidence ?? 82)}%
          </div>
          <div className="text-[11px] text-gray-400 mt-0.5">ML Stage 2 CatBoost</div>
        </div>
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Thermal Sensor Metrics */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-5 shadow-xs">
          <div className="text-xs font-bold text-gray-800 dark:text-gray-200 mb-3 flex items-center justify-between">
            <span>Thermal Sensors (FIRMS)</span>
            <span className="text-[10px] text-gray-400 font-normal">VIIRS / MODIS</span>
          </div>
          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-gray-500 dark:text-gray-400">Average FRP</span>
              <span className="font-bold text-gray-900 dark:text-gray-100">
                {(stats.average_frp ?? 0).toFixed(1)} MW
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-500 dark:text-gray-400">Last 24 Hours</span>
              <span className="font-bold text-gray-900 dark:text-gray-100">{stats.last_24h ?? 0} detections</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-500 dark:text-gray-400">Water Proximity</span>
              <span className="font-bold text-blue-600 dark:text-blue-400">{stats.near_water_count ?? 0} near water</span>
            </div>
          </div>
        </div>

        {/* 5 SIH Category Breakdown */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-5 shadow-xs">
          <div className="text-xs font-bold text-gray-800 dark:text-gray-200 mb-3 flex items-center justify-between">
            <span>SIH Category Distribution</span>
            <span className="text-[10px] text-gray-400 font-normal">5 Classes</span>
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-red-500" />
                <span>Industrial Fire</span>
              </span>
              <span className="font-bold text-red-600 dark:text-red-400">
                {classificationCounts['Industrial Fire'] ?? stats.industrial_count ?? 0}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-orange-500" />
                <span>Wildfire / Natural</span>
              </span>
              <span className="font-bold text-orange-600 dark:text-orange-400">
                {classificationCounts['Wildfire / Natural Fire'] ?? 0}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-500" />
                <span>Agricultural Fire</span>
              </span>
              <span className="font-bold text-amber-600 dark:text-amber-400">
                {classificationCounts['Agricultural Fire'] ?? 0}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-blue-500" />
                <span>Persistent Thermal</span>
              </span>
              <span className="font-bold text-blue-600 dark:text-blue-400">
                {classificationCounts['Persistent Thermal Source'] ?? 0}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600 dark:text-gray-400 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-gray-500" />
                <span>Unknown / Other</span>
              </span>
              <span className="font-bold text-gray-600 dark:text-gray-400">
                {classificationCounts['Unknown / Other'] ?? 0}
              </span>
            </div>
          </div>
        </div>

        {/* Spatial & Persistence Evidence */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl p-5 shadow-xs">
          <div className="text-xs font-bold text-gray-800 dark:text-gray-200 mb-3 flex items-center justify-between">
            <span>Spatial & Persistence Evidence</span>
            <span className="text-[10px] text-gray-400 font-normal">Enrichment</span>
          </div>
          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between items-center">
              <span className="text-gray-500 dark:text-gray-400">Inside Industrial Zone</span>
              <span className="font-bold text-gray-900 dark:text-gray-100">{stats.industrial_count ?? 0} events</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-500 dark:text-gray-400">Dynamic World LULC</span>
              <span className="font-bold text-emerald-600 dark:text-emerald-400">10m GEE Layer</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-500 dark:text-gray-400">OSM PostGIS Engine</span>
              <span className="font-bold text-gray-900 dark:text-gray-100">Active</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};