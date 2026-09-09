/**
 * Normalized Frontend Data Contract
 * Derived directly from frontend/frontend_requirements.md
 */

export interface EventLocation {
  city: string;
  state: string;
  country: string;
}

export interface IndustrialContext {
  nearby_facilities: string;
  osm_proximity: string;
}

export interface WaterContext {
  proximity: string;
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
  predicted_class: string;
  confidence: number;
  risk_score: number;
  risk_level: 'critical' | 'high' | 'moderate' | 'low';
  model_version: string;
  key_factors: KeyFactor[];
}

export interface NormalizedEvent {
  event_id: string;
  latitude: number;
  longitude: number;
  location: EventLocation;
  classification: string;
  risk_score: number;
  risk_level: 'critical' | 'high' | 'moderate' | 'low';
  confidence: number;
  frp: number;
  persistence: string;
  industrial_context: IndustrialContext;
  water_context: WaterContext;
  land_cover: LandCoverBreakdown;
  satellite: SatelliteInfo;
  color: string;
  prediction?: NormalizedPrediction;
  raw?: any;

  // Backwards-compatible aliases
  id?: string;
  acquisition_time?: string;
  status?: string;
  pipeline_version?: string;
  processed_at?: string;
  brightness?: number | null;
  satellite_name?: string;
  day_night?: string | null;
}

export interface NormalizedStatistics {
  totalDetections: number;
  industrialCount: number;
  highRiskCount: number;
  lowRiskCount: number;
  averageRiskScore: number;
  demoMode: boolean;

  // Snake_case aliases per requirements
  total_detections?: number;
  industrial_count?: number;
  high_risk_count?: number;
  low_risk_count?: number;
  average_risk_score?: number;

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
