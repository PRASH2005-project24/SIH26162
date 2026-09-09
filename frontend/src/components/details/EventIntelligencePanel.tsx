import { useState } from 'react';
import type { ApiThermalEvent } from '@/types/api';
import type { SIHCategory } from '@/types';
import { FIRMSSection } from './FIRMSSection';
import { OSMSection } from './OSMSection';
import { DynamicWorldSection } from './DynamicWorldSection';
import { PersistenceSection } from './PersistenceSection';
import { SIHClassificationSection } from '@/components/details/SIHClassificationSection';
import { SiHCategoryBadge } from '@/components/ui/SiHCategoryBadge';

interface EventIntelligencePanelProps {
  event: ApiThermalEvent | null;
  onClose: () => void;
}

export const EventIntelligencePanel = ({ event, onClose }: EventIntelligencePanelProps) => {
  const [activeSection, setActiveSection] = useState<'firms' | 'osm' | 'dynamic_world' | 'persistence' | 'technical' | null>(null);

  if (!event) {
    return null;
  }

  const { classification, persistence, osm, dynamic_world, latitude, longitude, acquisition_time, brightness, frp, confidence, satellite, day_night, status } = event;

  // Determine final SIH category (from classification or fallback)
  const category = classification?.category;
  const sihCategory: SIHCategory = category === 'Industrial Fire'
    || category === 'Agricultural Fire'
    || category === 'Persistent Thermal Source'
    || category === 'Wildfire / Natural Fire'
    || category === 'Wildfire/Natural Fire'
    ? category === 'Wildfire/Natural Fire' ? 'Wildfire / Natural Fire' : category
    : 'Unknown / Other';

  // Determine ML prediction (original 3-class)
  const mlPrediction = classification?.category || 'Unknown';

  return (
    <div className="fixed inset-0 z-50 flex items-end bg-black bg-opacity-50">
      <div className="relative w-full max-w-xl max-h-[90vh] overflow-y-auto bg-white dark:bg-gray-900 p-6">
        <div className="flex justify-between items-start mb-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Event Details</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
            &times;
          </button>
        </div>

        {/* Level 1: Immediate Understanding */}
        <div className="space-y-4">
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:bg-gray-800/50 p-4 rounded-lg">
            <div className="flex items-center space-x-3 mb-2">
              <SiHCategoryBadge category={sihCategory} />
              <div>
                <h3 className="font-medium text-gray-900 dark:text-gray-100">{sihCategory}</h3>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  Final SIH Classification
                </p>
              </div>
            </div>

            {classification && (
              <div className="border-t border-gray-200 dark:border-gray-700 pt-3 mt-3">
                <div className="flex items-center space-x-3 mb-1">
                  <div className="w-5 h-5 bg-green-200 dark:bg-green-700 rounded flex items-center justify-center text-xs font-medium">
                    ML
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{mlPrediction}</p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">ML Source Prediction</p>
                  </div>
                </div>
                <div className="flex items-center space-x-3">
                  <div className="w-5 h-5 bg-purple-200 dark:bg-purple-700 rounded flex items-center justify-center text-xs font-medium">
                    %
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {Math.round(classification.confidence * 100)}%
                    </p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">Confidence</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="space-y-3">
            <div className="flex items-center space-x-3 text-sm text-gray-600 dark:text-gray-400">
              <div className="w-5 h-5 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center text-xs font-medium">
                📅
              </div>
              <span>{new Date(acquisition_time).toLocaleString()}</span>
            </div>

            <div className="flex items-center space-x-3 text-sm text-gray-600 dark:text-gray-400">
              <div className="w-5 h-5 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center text-xs font-medium">
                🔥
              </div>
              <span>
                {frp !== null && frp !== undefined
                  ? frp.toFixed(2) + ' MW'
                  : 'N/A'}
              </span>
            </div>

            <div className="flex items-center space-x-3 text-sm text-gray-600 dark:text-gray-400">
              <div className="w-5 h-5 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center text-xs font-medium">
                📍
              </div>
              <span>
                {latitude !== null && longitude !== null
                  ? `${latitude.toFixed(4)}°, ${longitude.toFixed(4)}°`
                  : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        {/* Level 2: Evidence */}
        <div className="space-y-6">
          <SIHClassificationSection event={event} />
          <FIRMSSection event={event} />
          <OSMSection event={event} />
          <DynamicWorldSection event={event} />
          <PersistenceSection event={event} />
        </div>

        {/* Level 3: Technical Details (Expandable) */}
        <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">Technical Details</h3>
            <button
              onClick={() => setActiveSection(prev => (prev === null ? 'technical' : null))}
              className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300"
            >
              {activeSection === 'technical' ? 'Hide Details' : 'Show Details'}
            </button>
          </div>

          {activeSection === 'technical' && (
            <div className="space-y-4 text-sm text-gray-600 dark:text-gray-400">
              <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-3">
                <h4 className="font-medium mb-2">Raw FIRMS Data</h4>
                <div className="space-y-1">
                  <div className="flex justify-between">
                    <span>Satellite:</span>
                    <span>{satellite}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Instrument:</span>
                    <span>{satellite}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Day/Night:</span>
                    <span>{day_night === 'D' ? 'Day' : day_night === 'N' ? 'Night' : 'Unknown'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Status:</span>
                    <span className={status === 'active' ? 'text-green-600' : status === 'duplicate' ? 'text-yellow-600' : 'text-gray-600'}>
                      {status}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Confidence:</span>
                    <span>{confidence !== null ? confidence + '%' : 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Brightness Temperature:</span>
                    <span>
                      {brightness !== null && brightness !== undefined
                        ? brightness.toFixed(1) + ' K'
                        : 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Fire Radiative Power (FRP):</span>
                    <span>
                      {frp !== null && frp !== undefined
                        ? frp.toFixed(2) + ' MW'
                        : 'N/A'}
                    </span>
                  </div>
                </div>
              </div>

              {osm && (
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 mt-4">
                  <h4 className="font-medium mb-2">OSM Raw Data</h4>
                  <div className="space-y-1">
                    <div className="flex justify-between">
                      <span>Inside Industrial Zone:</span>
                      <span>{osm.inside_industrial_zone ?? false
                        ? 'Yes'
                        : 'No'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Nearest Feature Distance:</span>
                      <span>
                        {osm.nearest_feature_distance_m !== null && osm.nearest_feature_distance_m !== undefined
                          ? osm.nearest_feature_distance_m.toFixed(0) + ' m'
                          : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Feature Count (1km):</span>
                      <span>
                        {osm.feature_count_1km !== null && osm.feature_count_1km !== undefined
                          ? osm.feature_count_1km.toString()
                          : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Nearby Water:</span>
                      <span>{osm.nearby_water ?? false
                        ? 'Yes'
                        : 'No'}</span>
                    </div>
                  </div>
                </div>
              )}

              {dynamic_world && (
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 mt-4">
                  <h4 className="font-medium mb-2">Dynamic World Raw Data</h4>
                  <div className="space-y-1">
                    <div className="flex justify-between">
                      <span>Label:</span>
                      <span>{dynamic_world.land_cover_label ?? 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Acquisition Date:</span>
                      <span>{dynamic_world.acquisition_date ?? 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Query Date:</span>
                      <span>{dynamic_world.query_date ?? 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Coverage State:</span>
                      <span>{dynamic_world.coverage_state ?? 'N/A'}</span>
                    </div>
                    {dynamic_world.class_probabilities && Object.keys(dynamic_world.class_probabilities).length > 0 && (
                      <div className="mt-2">
                        <span className="font-medium">Class Probabilities:</span>
                        <div className="mt-1 space-y-1 text-xs">
                          {Object.entries(dynamic_world.class_probabilities).map(([className, prob]) => {
                            const probability = prob as number;
                            return (
                              <div key={className} className="flex justify-between">
                                <span>{className}</span>
                                <span>{(probability * 100).toFixed(1)}%</span>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {persistence && (
                <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 mt-4">
                  <h4 className="font-medium mb-2">Persistence Raw Data</h4>
                  <div className="space-y-1">
                    <div className="flex justify-between">
                      <span>Is Persistent:</span>
                      <span className={persistence.is_persistent ? 'text-green-600' : 'text-gray-600'}>
                        {persistence.is_persistent ? 'Yes' : 'No'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Observation Dates:</span>
                      <span>{persistence.date_count} unique dates</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Duration:</span>
                      <span>{persistence.duration_days} days</span>
                    </div>
                    {persistence.persistence_date_count !== undefined && (
                      <div className="flex justify-between">
                        <span>Persistence Date Count:</span>
                        <span>{persistence.persistence_date_count}</span>
                      </div>
                    )}
                    {persistence.persistence_duration_days !== undefined && (
                      <div className="flex justify-between">
                        <span>Persistence Duration:</span>
                        <span>{persistence.persistence_duration_days} days</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};