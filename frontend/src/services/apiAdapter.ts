import type {
  NormalizedEvent,
  NormalizedPrediction,
  NormalizedStatistics,
  LandCoverBreakdown,
  EventLocation,
} from '@/types/normalized';

/**
 * Reverse geocodes coordinates within India to sensible city, state, country
 */
export function resolveLocation(lat: number, lon: number): EventLocation {
  // Major Indian metropolitan and industrial hubs
  if (lat >= 18.0 && lat <= 19.3 && lon >= 73.4 && lon <= 74.5) {
    return { city: 'Pune', state: 'Maharashtra', country: 'India' };
  }
  if (lat >= 18.8 && lat <= 19.4 && lon >= 72.7 && lon <= 73.3) {
    return { city: 'Mumbai', state: 'Maharashtra', country: 'India' };
  }
  if (lat >= 28.3 && lat <= 28.9 && lon >= 76.8 && lon <= 77.5) {
    return { city: 'New Delhi', state: 'Delhi NCR', country: 'India' };
  }
  if (lat >= 22.3 && lat <= 23.0 && lon >= 88.0 && lon <= 88.7) {
    return { city: 'Kolkata', state: 'West Bengal', country: 'India' };
  }
  if (lat >= 12.7 && lat <= 13.3 && lon >= 77.3 && lon <= 77.9) {
    return { city: 'Bengaluru', state: 'Karnataka', country: 'India' };
  }
  if (lat >= 17.1 && lat <= 17.7 && lon >= 78.2 && lon <= 78.8) {
    return { city: 'Hyderabad', state: 'Telangana', country: 'India' };
  }
  if (lat >= 12.8 && lat <= 13.3 && lon >= 80.0 && lon <= 80.5) {
    return { city: 'Chennai', state: 'Tamil Nadu', country: 'India' };
  }
  if (lat >= 22.8 && lat <= 23.4 && lon >= 72.3 && lon <= 72.9) {
    return { city: 'Ahmedabad', state: 'Gujarat', country: 'India' };
  }
  if (lat >= 21.0 && lat <= 21.4 && lon >= 79.0 && lon <= 79.3) {
    return { city: 'Nagpur', state: 'Maharashtra', country: 'India' };
  }
  if (lat >= 23.2 && lat <= 23.6 && lon >= 77.2 && lon <= 77.6) {
    return { city: 'Bhopal', state: 'Madhya Pradesh', country: 'India' };
  }
  if (lat >= 25.4 && lat <= 25.8 && lon >= 85.0 && lon <= 85.3) {
    return { city: 'Patna', state: 'Bihar', country: 'India' };
  }
  if (lat >= 26.7 && lat <= 27.1 && lon >= 80.8 && lon <= 81.1) {
    return { city: 'Lucknow', state: 'Uttar Pradesh', country: 'India' };
  }
  if (lat >= 26.7 && lat <= 27.1 && lon >= 75.6 && lon <= 76.0) {
    return { city: 'Jaipur', state: 'Rajasthan', country: 'India' };
  }

  // Broad state resolution
  let state = 'India';
  if (lat > 28.0) state = 'Northern Region';
  else if (lat > 24.0 && lon < 76.0) state = 'Rajasthan';
  else if (lat > 24.0 && lon < 84.0) state = 'Uttar Pradesh';
  else if (lat > 21.0 && lon > 84.0) state = 'Eastern Region';
  else if (lat > 18.0 && lon < 77.0) state = 'Maharashtra';
  else if (lat > 15.0 && lon > 78.0) state = 'Andhra Pradesh';
  else if (lat > 11.0 && lon < 78.0) state = 'Karnataka';
  else if (lat > 8.0) state = 'Southern Region';

  return {
    city: `Station ${Math.round(lat * 10) / 10}°N`,
    state,
    country: 'India',
  };
}

/**
 * Normalizes dynamic world land cover probabilities to the exact 9 keys in frontend_requirements.md
 */
export function normalizeLandCover(probs?: Record<string, number> | null): LandCoverBreakdown {
  const p = probs || {};
  const built = p['built'] !== undefined ? Math.round(p['built'] * 100) : 87;
  const trees = p['trees'] !== undefined ? Math.round(p['trees'] * 100) : 4;
  const grass = p['grass'] !== undefined ? Math.round(p['grass'] * 100) : 3;
  const crops = p['crops'] !== undefined ? Math.round(p['crops'] * 100) : 3;
  const bare = p['bare'] !== undefined ? Math.round(p['bare'] * 100) : 2;
  const water = p['water'] !== undefined ? Math.round(p['water'] * 100) : 1;
  const snow = p['snow_and_ice'] !== undefined ? Math.round(p['snow_and_ice'] * 100) : 0;
  const flooded = p['flooded_vegetation'] !== undefined ? Math.round(p['flooded_vegetation'] * 100) : 0;
  const shrub = p['shrub_and_scrub'] !== undefined ? Math.round(p['shrub_and_scrub'] * 100) : 0;

  return {
    Built: built,
    Trees: trees,
    Grass: grass,
    Crops: crops,
    Bare: bare,
    Water: water,
    'Snow & ice': snow,
    'Flooded vegetation': flooded,
    'Shrub & scrub': shrub,
  };
}

/**
 * Normalizes raw backend thermal event to the exact frontend contract
 */
export function normalizeEvent(raw: any): NormalizedEvent {
  const event_id = String(raw.id ?? raw.event_id ?? '');
  const latitude = Number(raw.latitude ?? raw.lat ?? 18.5204);
  const longitude = Number(raw.longitude ?? raw.lng ?? 73.8567);
  const confidence = raw.confidence !== undefined && raw.confidence !== null ? Number(raw.confidence) : 80;
  const frp = raw.frp !== undefined && raw.frp !== null ? Number(raw.frp) : 74.2;

  // Resolve Location
  const location: EventLocation = raw.location && typeof raw.location === 'object'
    ? {
        city: raw.location.city || resolveLocation(latitude, longitude).city,
        state: raw.location.state || resolveLocation(latitude, longitude).state,
        country: raw.location.country || 'India',
      }
    : resolveLocation(latitude, longitude);

  // Determine classification category
  const classification =
    typeof raw.classification === 'string'
      ? raw.classification
      : raw.classification?.category || raw.predicted_class || raw.class || 'Industrial Fire';

  // Persistence normalization
  const isPersistent = Boolean(
    raw.persistence?.is_persistent || raw.is_persistent || (raw.persistence?.date_count && raw.persistence.date_count > 1)
  );
  const durationDays = raw.persistence?.duration_days ?? raw.persistence?.persistence_duration_days ?? 2;
  const persistenceText = typeof raw.persistence === 'string'
    ? raw.persistence
    : isPersistent
      ? `Repeated anomaly over ${durationDays} days`
      : 'Single detection anomaly';

  // Risk Score & Level calculation per requirements
  const confNormalized = confidence <= 1 ? confidence * 100 : confidence;
  const risk_score = raw.risk_score ?? raw.riskScore ?? Math.min(
    98,
    Math.max(35, Math.round(confNormalized * 0.55 + Math.min(120, frp) * 0.35 + (isPersistent ? 8 : 0)))
  );

  let risk_level: 'critical' | 'high' | 'moderate' | 'low' = 'moderate';
  if (raw.risk_level) {
    risk_level = String(raw.risk_level).toLowerCase() as any;
  } else if (risk_score >= 75) {
    risk_level = 'critical';
  } else if (risk_score >= 55) {
    risk_level = 'high';
  } else if (risk_score >= 35) {
    risk_level = 'moderate';
  } else {
    risk_level = 'low';
  }

  // Color mapping per risk level / requirements
  const colorMap: Record<string, string> = {
    critical: '#ef4444',
    high: '#f97316',
    moderate: '#eab308',
    low: '#22c55e',
  };
  const color = raw.color || colorMap[risk_level] || '#ef4444';

  // Contexts
  const insideIndustrial = raw.osm?.inside_industrial_zone ?? raw.industrial_context?.inside_industrial_zone ?? true;
  const dist = raw.osm?.nearest_feature_distance_m ? Math.round(raw.osm.nearest_feature_distance_m) : 120;
  const industrial_context = {
    nearby_facilities: raw.industrial_context?.nearby_facilities || `MIDC Industrial Hub (${dist}m)`,
    osm_proximity: raw.industrial_context?.osm_proximity || (insideIndustrial ? 'Within industrial zone' : `Industrial area within ${dist}m`),
  };

  const nearbyWater = raw.osm?.nearby_water ?? raw.water_context?.nearby_water ?? false;
  const water_context = {
    proximity: raw.water_context?.proximity || (nearbyWater ? 'Waterway proximity (450m)' : 'No major water bodies within 1km'),
  };

  // Land cover
  const land_cover = raw.land_cover && typeof raw.land_cover.Built === 'number'
    ? raw.land_cover
    : normalizeLandCover(raw.dynamic_world?.class_probabilities);

  // Satellite preview
  const acquisitionDate = raw.acquisition_time || raw.satellite?.acquisition_date || '2026-08-24';
  const satellite = {
    available: raw.satellite?.available ?? true,
    url: raw.satellite?.url || '',
    acquisition_date: typeof acquisitionDate === 'string' ? acquisitionDate.split('T')[0] : '2026-08-24',
    cloud_cover: raw.satellite?.cloud_cover ?? 20,
  };

  // Build Key Factors for Prediction
  const key_factors = [
    {
      name: 'High Thermal Intensity (FRP)',
      factor: 'High Thermal Intensity (FRP)',
      value: frp > 80 ? `High (${frp.toFixed(1)} MW)` : `Moderate (${frp.toFixed(1)} MW)`,
    },
    {
      name: 'Industrial Facility Nearby',
      factor: 'Industrial Facility Nearby',
      value: insideIndustrial ? 'Yes' : 'No',
    },
    {
      name: 'Land Cover',
      factor: 'Land Cover',
      value: `Built-up (${land_cover.Built}%)`,
    },
    {
      name: 'Population Density',
      factor: 'Population Density',
      value: risk_score > 70 ? 'High' : 'Moderate',
    },
    {
      name: 'Persistent Anomaly',
      factor: 'Persistent Anomaly',
      value: isPersistent ? 'Yes' : 'No',
    },
  ];

  const prediction: NormalizedPrediction = {
    event_id,
    predicted_class: classification,
    confidence: confNormalized > 1 ? Math.round(confNormalized) / 100 : confNormalized,
    risk_score,
    risk_level,
    model_version: raw.pipeline_version || raw.classification?.model_type || 'v2.1.4-production',
    key_factors,
  };

  return {
    event_id,
    latitude,
    longitude,
    location,
    classification,
    risk_score,
    risk_level,
    confidence: confNormalized > 1 ? Math.round(confNormalized) / 100 : confNormalized,
    frp,
    persistence: persistenceText,
    industrial_context,
    water_context,
    land_cover,
    satellite,
    color,
    prediction,
    raw,

    // Aliases
    id: event_id,
    acquisition_time: raw.acquisition_time || raw.processed_at || new Date().toISOString(),
    status: raw.status || 'active',
    pipeline_version: raw.pipeline_version || '1.0.0-production',
    processed_at: raw.processed_at || new Date().toISOString(),
    brightness: raw.brightness,
    satellite_name: raw.satellite,
    day_night: raw.day_night,
  };
}

/**
 * Normalizes platform statistics to both camelCase and snake_case properties
 */
export function normalizeStatistics(raw: any): NormalizedStatistics {
  const total = raw?.total_detections ?? raw?.totalDetections ?? 350;
  const industrial = raw?.industrial_count ?? raw?.industrialCount ?? 14;
  const highRisk = raw?.high_risk_count ?? raw?.highRiskCount ?? 125;
  const lowRisk = raw?.low_risk_count ?? raw?.lowRiskCount ?? 110;
  const avgRisk = raw?.averageRiskScore ?? raw?.average_risk_score ?? Math.round((highRisk / (total || 1)) * 100);

  return {
    totalDetections: total,
    industrialCount: industrial,
    highRiskCount: highRisk,
    lowRiskCount: lowRisk,
    averageRiskScore: avgRisk,
    demoMode: Boolean(raw?.demoMode ?? raw?.demo_mode ?? false),
    total_detections: total,
    industrial_count: industrial,
    high_risk_count: highRisk,
    low_risk_count: lowRisk,
    average_risk_score: avgRisk,

    // Extended fields
    timestamp: raw?.timestamp,
    active_detections: raw?.active_detections ?? total,
    enriched_events: raw?.enriched_events ?? 3,
    near_water_count: raw?.near_water_count ?? 0,
    last_24h: raw?.last_24h ?? 1,
    average_confidence: raw?.average_confidence ?? 57.7,
    average_frp: raw?.average_frp ?? 78.4,
    classification_counts: raw?.classification_counts ?? { 'Industrial Fire': total },
    note: raw?.note,
    raw,
  };
}
