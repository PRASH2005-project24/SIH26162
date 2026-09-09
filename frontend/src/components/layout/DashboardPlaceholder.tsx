export const DashboardPlaceholder = () => {
  return (
    <div className="flex-1 p-8">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">
        FireGuard Dashboard
      </h1>
      <p className="text-gray-600 mb-4">
        Dashboard coming soon. This is the foundation for the permanent frontend.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Map View</h2>
          <p className="text-gray-500">
            Interactive India-wide thermal event map with Leaflet
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Events List</h2>
          <p className="text-gray-500">
            Filterable and paginated list of thermal events
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-semibold mb-4">Event Details</h2>
          <p className="text-gray-500">
            Detailed view of selected event with ML classification and persistence data
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Statistics</h2>
          <p className="text-gray-500">
            Dashboard showing key metrics and analytics
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">System Status</h2>
          <p className="text-gray-500">
            Live/Demo/Offline indicators and backend health
          </p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Analytics</h2>
          <p className="text-gray-500">
            Charts and graphs for trend analysis
          </p>
        </div>
      </div>
    </div>
  );
};