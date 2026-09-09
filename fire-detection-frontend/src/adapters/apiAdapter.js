/**
 * Real API Adapter
 * Integrates with Stage 1/1B backend and Stage 2 ML services
 * Handles request/response mapping and error handling
 */

const REQUEST_TIMEOUT = 10000; // 10 seconds

/**
 * Make authenticated fetch request with timeout
 */
async function fetchWithTimeout(url, options = {}) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);

    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        if (error.name === 'AbortError') {
            throw new Error('Request timeout');
        }
        throw error;
    } finally {
        clearTimeout(timeoutId);
    }
}

/**
 * Get events from Stage 1/1B backend
 * Actual endpoint: GET /api/v1/events?since_hours=24&limit=100
 * Real response: { events: [...], total, limit, offset, has_more }
 */
export async function getEventsFromAPI(baseUrl, timeWindow = 24) {
    try {
        // Convert time window to hours for backend
        const sinceHours = timeWindowToHours(timeWindow);

        // baseUrl should be: http://localhost:8000/api/v1
        // Construct full URL with query params
        const finalUrl = `${baseUrl}/events?since_hours=${sinceHours}&limit=500`;

        const response = await fetchWithTimeout(finalUrl);

        // Backend returns { events: [...], total, limit, offset, has_more }
        const events = Array.isArray(response) ? response : response.events || [];

        // Map backend fields to frontend expectations
        // Stage 1/1B provides: id, lat, lon, frp, confidence, brightness, satellite, day_night, status, etc.
        // Stage 2 ML provides: classification, risk_score, risk_level (not available yet in Live Mode)
        return events.map(event => ({
            event_id: event.id || event.event_id,
            latitude: parseFloat(event.latitude),
            longitude: parseFloat(event.longitude),
            acquisition_date: event.acquisition_time || event.created_at,
            frp: event.frp || null,
            brightness: event.brightness || null,
            confidence: event.confidence || 0,
            satellite: event.satellite || 'Unknown',
            day_night: event.day_night || null,
            status: event.status || 'active',

            // Stage 2 ML fields (not yet available in Stage 1/1B)
            classification: null, // Pending ML classification
            risk_score: null,     // Pending ML risk scoring
            risk_level: null,     // Pending ML classification

            // These come from Stage 1B enrichment (if computed)
            location: event.location || {},
            industrial_context: event.industrial_context || {},
            water_context: event.water_context || {},
            land_cover: event.land_cover || {},
            persistence: event.persistence || null,
            satellite_data: event.satellite_data || { available: false },

            // UI-friendly color (neutral until ML provides risk)
            color: event.risk_level ? getRiskColor(event.risk_level) : '#9ca3af' // gray for pending
        }));
    } catch (error) {
        console.error('Failed to fetch events from API:', error);
        throw error;
    }
}

/**
 * Get single event from API
 * Actual endpoint: GET /api/v1/events/{id}
 */
export async function getEventFromAPI(baseUrl, eventId) {
    try {
        const finalUrl = baseUrl.includes('/api/v1')
            ? `${baseUrl}/${eventId}`
            : `${baseUrl}/events/${eventId}`;

        const response = await fetchWithTimeout(finalUrl);

        // Response structure: { event: {...}, raw_payload_uri, ingestion_run_id, evidence, provenance }
        const event = response.event || response;

        return {
            event_id: event.id || event.event_id,
            latitude: parseFloat(event.latitude),
            longitude: parseFloat(event.longitude),
            acquisition_date: event.acquisition_time || event.created_at,
            frp: event.frp || null,
            brightness: event.brightness || null,
            confidence: event.confidence || 0,
            satellite: event.satellite || 'Unknown',
            day_night: event.day_night || null,
            status: event.status || 'active',

            // Stage 2 ML fields (not yet available)
            classification: null,
            risk_score: null,
            risk_level: null,

            // Enrichment (if available)
            location: event.location || {},
            industrial_context: event.industrial_context || {},
            water_context: event.water_context || {},
            land_cover: event.land_cover || {},
            persistence: event.persistence || null,

            // Provenance
            raw_payload_uri: response.raw_payload_uri || null,
            ingestion_run_id: response.ingestion_run_id || null,

            color: '#9ca3af' // neutral pending classification
        };
    } catch (error) {
        console.error('Failed to fetch event from API:', error);
        throw error;
    }
}

/**
 * Get ML prediction from Stage 2 service
 * Expected endpoint: POST /predict (or configurable ML service)
 * Expected response: { predicted_class, confidence, risk_score, risk_level, model_version, key_factors }
 */
export async function getPredictionFromAPI(mlServiceUrl, eventId, eventData) {
    try {
        const response = await fetchWithTimeout(`${mlServiceUrl}/predict`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                event_id: eventId,
                ...eventData
            })
        });

        return {
            event_id: eventId,
            predicted_class: response.predicted_class || 'Unknown',
            confidence: response.confidence || 0,
            risk_score: response.risk_score || 0,
            risk_level: response.risk_level || 'low',
            model_version: response.model_version || 'unknown',
            key_factors: response.key_factors || []
        };
    } catch (error) {
        console.error('Failed to fetch prediction from API:', error);
        throw error;
    }
}

/**
 * Get satellite data from backend
 * Expected endpoint: GET /api/events/{id}/satellite
 */
export async function getSatelliteFromAPI(baseUrl, eventId) {
    try {
        const response = await fetchWithTimeout(`${baseUrl}/events/${eventId}/satellite`);

        return {
            event_id: eventId,
            available: response.available || false,
            url: response.url || null,
            acquisition_date: response.acquisition_date || null,
            cloud_cover: response.cloud_cover || null
        };
    } catch (error) {
        console.error('Failed to fetch satellite data from API:', error);
        throw error;
    }
}

/**
 * Get enrichment data from backend
 * Actual endpoint: GET /api/v1/enrichment/enrichment-status/{event_id}
 */
export async function getEnrichmentFromAPI(baseUrl, eventId) {
    try {
        // Backend enrichment endpoint is under /api/v1/enrichment, not /api/v1/events
        const enrichmentBase = baseUrl.replace('/events', '').replace(/\/$/, '');
        const finalUrl = `${enrichmentBase}/enrichment/enrichment-status/${eventId}`;

        const response = await fetchWithTimeout(finalUrl);

        // Response: { status: "enriched" | "pending", enrichment: {...} }
        if (response.status === 'pending') {
            return {
                event_id: eventId,
                status: 'pending',
                location: {},
                industrial_context: {},
                water_context: {},
                land_cover: {},
                persistence: null
            };
        }

        const enrichment = response.enrichment || {};

        return {
            event_id: eventId,
            status: 'enriched',
            location: {},

            industrial_context: {
                inside_zone: enrichment.inside_industrial_zone || false,
                nearest_distance_m: enrichment.nearest_feature_distance_m || null,
                feature_count_1km: enrichment.feature_count_1km || 0
            },

            water_context: {
                nearby_water: enrichment.nearby_water || false
            },

            land_cover: {
                label: enrichment.land_cover_label || 'Unknown',
                probabilities: enrichment.land_cover_probabilities_json || {}
            },

            persistence: {
                query_date: enrichment.query_date || null,
                coverage: enrichment.coverage_state || 'unknown'
            }
        };
    } catch (error) {
        console.warn('Enrichment fetch failed (expected in Stage 1/1B before enrichment runs):', error);
        // Return empty enrichment - this is expected before enrichment is computed
        return {
            event_id: eventId,
            status: 'not_available',
            location: {},
            industrial_context: {},
            water_context: {},
            land_cover: {},
            persistence: null
        };
    }
}

/**
 * Get dashboard statistics
 * Actual endpoint: GET /api/v1/statistics
 */
export async function getStatisticsFromAPI(baseUrl) {
    try {
        const finalUrl = baseUrl.includes('/api/v1')
            ? `${baseUrl.replace('/events', '')}/statistics`
            : `${baseUrl}/statistics`;

        const response = await fetchWithTimeout(finalUrl);

        return {
            totalDetections: response.total_detections || 0,
            activeDetections: response.active_detections || 0,
            enrichedEvents: response.enriched_events || 0,
            industrialCount: response.industrial_count || 0,
            nearWaterCount: response.near_water_count || 0,
            last24h: response.last_24h || 0,
            highRiskCount: response.high_risk_count || 0,
            lowRiskCount: response.low_risk_count || 0,
            averageConfidence: response.average_confidence || 0,
            averageFRP: response.average_frp || 0,
            note: response.note || "Metrics from Stage 1/1B. Risk classification pending Stage 2 ML.",
            timestamp: response.timestamp || new Date().toISOString()
        };
    } catch (error) {
        console.warn('Statistics fetch failed:', error);
        // Return empty stats rather than crashing
        return {
            totalDetections: 0,
            industrialCount: 0,
            highRiskCount: 0,
            lowRiskCount: 0,
            averageRiskScore: 0,
            note: "Statistics unavailable - backend error",
            timestamp: new Date().toISOString()
        };
    }
}

/**
 * Helper: Convert time window filter to hours for backend API
 * Frontend uses: "today", "24", "week", "month"
 * Backend uses: since_hours parameter
 */
function timeWindowToHours(timeWindow) {
    const mapping = {
        'today': calculateHoursSinceToday(),
        '24': 24,
        'week': 168,      // 7 * 24
        '7d': 168,
        'month': 720,     // 30 * 24
        '30d': 720
    };
    return mapping[timeWindow] || 24; // default to 24 hours
}

/**
 * Helper: Calculate hours since today 00:00:00
 */
function calculateHoursSinceToday() {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const diffMs = now - today;
    return Math.ceil(diffMs / (1000 * 60 * 60));
}

/**
 * Helper: Determine color based on risk level
 */
function getRiskColor(riskLevel) {
    const colors = {
        'critical': '#ef4444',
        'high': '#ef4444',
        'medium': '#f97316',
        'low': '#22c55e',
        'pending': '#9ca3af'
    };
    return colors[riskLevel] || '#9ca3af'; // gray for unknown/pending
}

/**
 * Health check - verify API is accessible
 */
export async function checkAPIHealth(baseUrl) {
    try {
        const finalUrl = baseUrl.includes('/api/v1')
            ? `${baseUrl.replace('/events', '')}/health`
            : `${baseUrl.replace('/api/events', '/api/v1')}/health`;

        const response = await fetchWithTimeout(finalUrl);
        return response.status === 'healthy' || response.status === 'ok';
    } catch (error) {
        console.warn('API health check failed:', error);
        return false;
    }
}
