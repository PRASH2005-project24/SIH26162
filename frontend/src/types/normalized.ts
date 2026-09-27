/**
 * Normalized Frontend Data Contract
 * Derived from SIH26162 requirements — strictly backend-supported fields only.
 *
 * ML prediction = 3 source classes (industrial, wildfire, agricultural)
 * SIH classification = 5 categories (Industrial Fire, Wildfire / Natural Fire,
 *   Agricultural Fire, Persistent Thermal Source, Unknown / Other)
 */

export interface EventLocation {
  city: string;
  state: string;
  country: string;
}

export interface IndustrialContext {
  nearby_facilities: string;
  osm_proximity: string;
  inside_industrial_zone?: boolean;
  nearest_feature_distance_m?: number;
  feature_count_1km?: number;
}

export interface WaterContext {
  proximity: string;
  nearby_water?: boolean;
}

export interface LandCoverBreakdown {
  Built: number;
  Trees: number;
  Grass: number;
  Crops: number;
  Bare: number;
  Water: number;
  'Snow & ice': number;
  'Flooded vegetation': number;
  'Shrub & scrub': number;
}

export interface SatelliteInfo {
  available: boolean;
  url: string;
  acquisition_date: string;
  cloud_cover: number;
}

export interface KeyFactor {
  name?: string;
  factor?: string;
  value: string;
}

export interface NormalizedPrediction {
  event_id: string;
  /** SIH 5-class classification */
  predicted_class: string;
  confidence: number;
  /** ML 3-class raw probabilities */
  ml_probabilities?: Record<string, number>;
  model_version: string;
  key_factors: KeyFactor[];
}

export interface NormalizedEvent {
  event_id: string;
  latitude: number;
  longitude: number;
  location: EventLocation;

  /** SIH 5-category classification */
  classification: string;
  /** ML 3-class prediction confidence (0–1) */
  confidence: number;

  // FIRMS thermal data
  frp: number | null;
  brightness: number | null;
  satellite_name: string;
  instrument?: string;
  day_night: string | null;
  acquisition_time: string;

  // Enrichment layers
  persistence: string;
  persistence_details?: {
    is_persistent: boolean;
    date_count: number;
    duration_days: number;
  };
  industrial_context: IndustrialContext;
  water_context: WaterContext;
  land_cover: LandCoverBreakdown | null;
  satellite: SatelliteInfo;

  // Marker color (by SIH category)
  color: string;

  prediction?: NormalizedPrediction;
  raw?: any;

  // Backwards-compatible aliases
  id?: string;
  status?: string;
  pipeline_version?: string;
  processed_at?: string;
}

export interface NormalizedStatistics {
  totalDetections: number;
  industrialCount: number;
  averageConfidence: number;
  averageFrp: number;
  demoMode: boolean;

  // Snake_case aliases
  total_detections?: number;
  industrial_count?: number;

  // Extended analytics fields
  timestamp?: string;
  active_detections?: number;
  enriched_events?: number;
  near_water_count?: number;
  last_24h?: number;
  average_confidence?: number;
  average_frp?: number;
  classification_counts?: Record<string, number>;
  note?: string;
  raw?: any;
}
