import React from 'react';
import type { NormalizedEvent } from '@/types/normalized';
import { Factory, MapPin, Building2, Droplets, ShieldCheck, Compass, Layers } from 'lucide-react';

interface ThermalContextCardProps {
  event: NormalizedEvent | null;
}

export const ThermalContextCard: React.FC<ThermalContextCardProps> = ({ event }) => {
  const isIndustrial = event?.industrial_context?.inside_industrial_zone;
  const nearestDist = event?.industrial_context?.nearest_feature_distance_m;
  const facilityCount = event?.industrial_context?.feature_count_1km;
  const waterProximity = event?.water_context?.proximity || 'Not available';
  const persistenceText = event?.persistence || 'Not available';
  const satellite = event?.satellite_name || 'Not available';
  const instrument = event?.instrument || 'Not available';
  const hasOsmContext = isIndustrial != null || nearestDist != null || facilityCount != null || event?.water_context?.nearby_water != null;

  const nearestDistFormatted =
    nearestDist != null
      ? `${Math.round(nearestDist)} meters`
      : 'Not available';

  return (
    <div className="bg-white/85 dark:bg-slate-900/70 backdrop-blur-md rounded-2xl p-5 shadow-xs border border-gray-200/80 dark:border-slate-800/80 flex flex-col justify-between h-full">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-gray-100 dark:border-slate-800/80">
        <div className="flex items-baseline gap-1.5">
          <h2 className="text-sm font-bold text-gray-900 dark:text-white tracking-tight">
            Thermal & GIS Context
          </h2>
          <span className="text-[11px] font-medium text-gray-400">
            (FIRMS + OSM)
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full font-bold bg-blue-50 dark:bg-blue-950/50 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800">
            <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
            PostGIS Layer
          </span>
        </div>
      </div>

      {/* Grid of GIS Attributes - evenly distributed to eliminate dead space */}
      <div className="flex-1 flex flex-col justify-between py-2 space-y-2 my-1">
        {/* Row 1: Industrial Proximity */}
        <div className="flex items-center justify-between p-2 rounded-xl bg-gray-50/80 dark:bg-gray-700/40 text-xs">
          <div className="flex items-center gap-2 text-gray-600 dark:text-gray-300">
            <Factory className="w-3.5 h-3.5 text-rose-500 shrink-0" />
            <span className="font-medium">Industrial Zone</span>
          </div>
          <span
            className={`font-bold px-2 py-0.5 rounded-md text-[11px] ${
              isIndustrial == null
                ? 'bg-gray-100 text-gray-500 dark:bg-gray-700 dark:text-gray-300'
                : isIndustrial
                ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
                : 'bg-gray-200 text-gray-700 dark:bg-gray-600 dark:text-gray-200'
            }`}
          >
            {isIndustrial == null ? 'Not available' : isIndustrial ? 'Inside Zone' : 'Outside Zone'}
          </span>
        </div>

        {/* Row 2: Nearest Facility */}
        <div className="flex items-center justify-between p-2 rounded-xl bg-gray-50/80 dark:bg-gray-700/40 text-xs">
          <div className="flex items-center gap-2 text-gray-600 dark:text-gray-300">
            <MapPin className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
            <span className="font-medium">Nearest Facility Distance</span>
          </div>
          <span className="font-semibold text-gray-900 dark:text-white text-[11px]">
            {nearestDistFormatted}
          </span>
        </div>

        {/* Row 3: Facilities within 1km */}
        <div className="flex items-center justify-between p-2 rounded-xl bg-gray-50/80 dark:bg-gray-700/40 text-xs">
          <div className="flex items-center gap-2 text-gray-600 dark:text-gray-300">
            <Building2 className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
            <span className="font-medium">Facilities within 1 km</span>
          </div>
          <span className="font-semibold text-gray-900 dark:text-white text-[11px]">
            {facilityCount != null ? `${facilityCount} facilities` : 'Not available'}
          </span>
        </div>

        {/* Row 4: Water Body */}
        <div className="flex items-center justify-between p-2 rounded-xl bg-gray-50/80 dark:bg-gray-700/40 text-xs">
          <div className="flex items-center gap-2 text-gray-600 dark:text-gray-300">
            <Droplets className="w-3.5 h-3.5 text-blue-500 shrink-0" />
            <span className="font-medium">Water Body Proximity</span>
          </div>
          <span className="font-semibold text-gray-900 dark:text-white text-[11px] truncate max-w-[170px]" title={waterProximity}>
            {waterProximity}
          </span>
        </div>

        {/* Row 5: Persistence */}
        <div className="flex items-center justify-between p-2 rounded-xl bg-gray-50/80 dark:bg-gray-700/40 text-xs">
          <div className="flex items-center gap-2 text-gray-600 dark:text-gray-300">
            <ShieldCheck className="w-3.5 h-3.5 text-amber-500 shrink-0" />
            <span className="font-medium">Thermal Persistence</span>
          </div>
          <span className="font-semibold text-gray-900 dark:text-white text-[11px] truncate max-w-[170px]" title={persistenceText}>
            {persistenceText}
          </span>
        </div>

        {/* Row 6: OSM Spatial Buffer */}
        <div className="flex items-center justify-between p-2 rounded-xl bg-gray-50/80 dark:bg-gray-700/40 text-xs">
          <div className="flex items-center gap-2 text-gray-600 dark:text-gray-300">
            <Compass className="w-3.5 h-3.5 text-cyan-500 shrink-0" />
            <span className="font-medium">Spatial Query Radius</span>
          </div>
          <span className="font-semibold text-gray-900 dark:text-white text-[11px]">
            1 km count radius
          </span>
        </div>

        {/* Row 7: PostGIS Indexing */}
        <div className="flex items-center justify-between p-2 rounded-xl bg-gray-50/80 dark:bg-gray-700/40 text-xs">
          <div className="flex items-center gap-2 text-gray-600 dark:text-gray-300">
            <Layers className="w-3.5 h-3.5 text-purple-500 shrink-0" />
            <span className="font-medium">PostGIS Geometry</span>
          </div>
          <span className="font-mono text-gray-700 dark:text-gray-300 text-[10px] bg-purple-50 dark:bg-purple-950/40 px-1.5 py-0.5 rounded border border-purple-200 dark:border-purple-800">
            EPSG:4326 (WGS 84)
          </span>
        </div>
      </div>

      {/* Footer */}
      <div className="text-[10px] text-gray-400 pt-2 border-t border-gray-100 dark:border-slate-800/80 flex items-center justify-between">
        <span>Sensor: {satellite} ({instrument})</span>
        <span className={`font-medium flex items-center gap-1 ${hasOsmContext ? 'text-gray-600 dark:text-gray-300' : 'text-gray-400'}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${hasOsmContext ? 'bg-emerald-500' : 'bg-gray-400'}`} />
          {hasOsmContext ? 'OSM data available' : 'OSM data unavailable'}
        </span>
      </div>
    </div>
  );
};
