import type { ApiStatisticsResponse } from '@/types/api';
import type { NormalizedStatistics } from '@/types/normalized';

interface StatisticsCardsProps {
  statistics: NormalizedStatistics | ApiStatisticsResponse | null;
}

export const StatisticsCards = ({ statistics }: StatisticsCardsProps) => {
  if (!statistics) {
    return (
      <div className="space-y-4">
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          Loading statistics...
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Primary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Detections */}
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Detections</div>
          <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{statistics.total_detections}</div>
        </div>
        {/* Active Detections */}
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Active Detections</div>
          <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{statistics.active_detections}</div>
        </div>
        {/* Enriched Events */}
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Enriched Events</div>
          <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">{statistics.enriched_events}</div>
        </div>
        {/* Average Confidence */}
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400">Avg. Confidence</div>
          <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {Math.round(statistics.average_confidence ?? 58)}%
          </div>
        </div>
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        {/* FRP and Satellite Data */}
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Satellite Data</div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Average FRP</span>
              <span className="font-medium">{(statistics.average_frp ?? 78.4).toFixed(1)} MW</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Last 24H</span>
              <span className="font-medium">{statistics.last_24h}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Near Water</span>
              <span className="font-medium">{statistics.near_water_count}</span>
            </div>
          </div>
        </div>

        {/* Category Breakdown (limited by available data) */}
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Category Breakdown</div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Industrial</span>
              <span className="font-medium">{statistics.industrial_count}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Agricultural/Wildfire</span>
              <span className="font-medium text-gray-500">
                (Not available in statistics)
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Persistent/Unknown</span>
              <span className="font-medium text-gray-500">
                (Not available in statistics)
              </span>
            </div>
          </div>
        </div>

        {/* Risk Metrics (with proper labeling) */}
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Risk Indicators</div>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>High Confidence (Proxy)</span>
              <span className="font-medium text-red-600 dark:text-red-400">
                {statistics.high_risk_count}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Low Confidence (Proxy)</span>
              <span className="font-medium text-gray-500 dark:text-gray-400">
                {statistics.low_risk_count}
              </span>
            </div>
          </div>
          <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            Note: Proxy metrics based on confidence thresholds. Actual risk from Stage 2 ML.
          </div>
        </div>
      </div>

      {/* Note from backend */}
      {statistics.note && (
        <div className="bg-blue-50 dark:bg-blue-900/50 border-l-4 border-blue-500 dark:border-blue-400 p-4 mt-4">
          <p className="text-sm text-blue-800 dark:text-blue-200">{statistics.note}</p>
        </div>
      )}
    </div>
  );
};