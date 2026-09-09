// SIH Categories
export type SIHCategory =
  | 'Industrial Fire'
  | 'Wildfire / Natural Fire'
  | 'Agricultural Fire'
  | 'Persistent Thermal Source'
  | 'Unknown / Other';

// Original ML Model Classes (3-class)
export type MLModelClass =
  | 'agricultural'
  | 'industrial'
  | 'wildfire';

// Thermal Event from backend
export interface ThermalEvent {
  id: string;
  acquisition_time: string;
  latitude: number;
  longitude: number;
  brightness?: number;
  frp?: number;
  confidence?: number;
  satellite: string;
  day_night?: string;
  status: string;
  pipeline_version: string;
  processed_at: string;

  // Optional enrichment and ML data
  classification?: ClassificationResponse;
  persistence?: PersistenceResponse;
  osm?: OsmContextResponse;
  dynamic_world?: DynamicWorldResponse;
}

// ML Classification Response (3-class probabilities)
export interface ClassificationResponse {
  category: string; // One of MLModelClass
  confidence: number;
  probabilities: Record<string, number>; // Should sum to ~1.0 for the 3 classes
  model_type?: string;
}

// Persistence Information
export interface PersistenceResponse {
  is_persistent: boolean;
  date_count: number;
  duration_days: number;
  persistence_date_count?: number; // For backward compatibility
  persistence_duration_days?: number; // For backward compatibility
}

// OSM Context
export interface OsmContextResponse {
  inside_industrial_zone?: boolean;
  nearest_feature_distance_m?: number;
  feature_count_1km?: number;
  nearby_water?: boolean;
}

// Dynamic World Context
export interface DynamicWorldResponse {
  land_cover_label?: string;
  class_probabilities?: Record<string, number>;
  acquisition_date?: string;
  query_date?: string;
  coverage_state?: string;
}

// Events List Response
export interface EventsListResponse {
  events: ThermalEvent[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

// Event Detail Response
export interface EventDetailResponse {
  event: ThermalEvent;
  raw_payload_uri?: string;
  ingestion_run_id?: string;
  evidence: Record<string, any>;
  provenance: Record<string, any>;
}

// Recent Events Response
export interface RecentEventsResponse {
  events: ThermalEvent[];
  count: number;
  query_hours: number;
  timestamp: string;
}

// Statistics Response
export interface StatisticsResponse {
  timestamp: string;
  total_detections: number;
  active_detections: number;
  enriched_events: number;
  industrial_count: number;
  near_water_count: number;
  last_24h: number;
  high_risk_count: number; // Pseudo-metric
  low_risk_count: number; // Pseudo-metric
  average_confidence: number;
  average_frp: number;
  note: string;
}

// Health Check Response
export interface HealthResponse {
  status: string;
  version: string;
  database: {
    status: string;
  };
}

// ML Prediction Request
export interface MLPredictionRequest {
  event_id?: string;
  features?: Record<string, any>;
}

// ML Prediction Response
export interface MLPredictionResponse {
  predicted_class: string; // SIH category
  confidence: number;
  class_probabilities: Record<string, number>; // Original 3-class probabilities
  model_type?: string;
}

// API Error Response
export interface APIErrorResponse {
  message: string;
  status?: number;
}