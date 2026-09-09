import { useStatistics } from '@/hooks/useStatistics';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

export const Analytics = () => {
  const { data: statistics, isLoading, error } = useStatistics();

  if (isLoading) return <div className="p-6">Loading analytics...</div>;
  if (error) return <div className="p-6">Error loading analytics</div>;

  if (!statistics) {
    return <div className="p-6">No statistics available</div>;
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Analytics Dashboard</h1>

      {/* Key Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <h3 className="text-lg font-medium mb-2">Total Detections</h3>
          <p className="text-3xl font-bold">{statistics.total_detections}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <h3 className="text-lg font-medium mb-2">Active Detections</h3>
          <p className="text-3xl font-bold text-green-600 dark:text-green-400">{statistics.active_detections}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <h3 className="text-lg font-medium mb-2">Enriched Events</h3>
          <p className="text-3xl font-bold">{statistics.enriched_events}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <h3 className="text-lg font-medium mb-2">Avg. Confidence</h3>
          <p className="text-3xl font-bold">
            {Math.round(statistics.average_confidence ?? 58)}%
          </p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Detection Trend (simulated with available data) */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <h3 className="text-lg font-medium mb-4">Detection Overview</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={[
              { name: 'Total', value: statistics.total_detections },
              { name: 'Active', value: statistics.active_detections },
              { name: 'Enriched', value: statistics.enriched_events },
              { name: 'Industrial', value: statistics.industrial_count },
              { name: 'Near Water', value: statistics.near_water_count },
              { name: 'Last 24H', value: statistics.last_24h },
            ]}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="value" fill="#4299e1" />
            </BarChart>
          </ResponsiveContainer>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            Overview of detection counts and key metrics
          </p>
        </div>

        {/* Category Distribution (limited by available data) */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <h3 className="text-lg font-medium mb-4">Available Data Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={[
                  { name: 'Active Detections', value: statistics.active_detections },
                  { name: 'Enriched Events', value: statistics.enriched_events },
                  { name: 'Industrial Events', value: statistics.industrial_count },
                  { name: 'Near Water Events', value: statistics.near_water_count },
                ]}
                cx="50%"
                cy="50%"
                innerRadius="60"
                outerRadius="120"
                labelLine={false}
                label={({ name, percent }) => (
                  <text
                    x={0}
                    y={0}
                    fill="#ffffff"
                    textAnchor="middle"
                    fontSize="12"
                  >
                    {name}: {percent}%
                  </text>
                )}
              >
                <Cell fill="#4299e1" />
                <Cell fill="#ed8936" />
                <Cell fill="#38a169" />
                <Cell fill="#e53e3e" />
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            Distribution of available categorized data
          </p>
        </div>
      </div>

      {/* Additional Info */}
      <div className="mt-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
        <h3 className="text-lg font-medium mb-3">Notes & Limitations</h3>
        <p className="text-sm text-gray-600 dark:text-gray-400">
          {statistics.note}
        </p>
        <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
          <strong>Note on Category Breakdown:</strong> The current API does not provide
          category-specific counts in the statistics endpoint. For detailed category
          distribution, please refer to the event listing with appropriate filters.
        </p>
      </div>
    </div>
  );
};