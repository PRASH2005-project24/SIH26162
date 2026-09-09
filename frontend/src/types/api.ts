import type {
  ThermalEvent,
  ClassificationResponse,
  PersistenceResponse,
  OsmContextResponse,
  DynamicWorldResponse,
  EventsListResponse,
  EventDetailResponse,
  StatisticsResponse,
  MLPredictionResponse
} from './index';

// Extended API response types with proper typing for nested objects
export interface ApiThermalEvent extends ThermalEvent {
  classification?: ClassificationResponse;
  persistence?: PersistenceResponse;
  osm?: OsmContextResponse;
  dynamic_world?: DynamicWorldResponse;
}

export interface ApiEventsListResponse extends EventsListResponse {
  events: ApiThermalEvent[];
}

export interface ApiEventDetailResponse extends EventDetailResponse {
  event: ApiThermalEvent;
}

// ML Prediction types
export interface ApiMLPredictionResponse extends MLPredictionResponse {
  // Already properly typed from base types
}

// Statistics types
export interface ApiStatisticsResponse extends StatisticsResponse {
  // Already properly typed from base types
}