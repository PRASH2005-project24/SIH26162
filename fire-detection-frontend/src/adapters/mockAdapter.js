/**
 * Mock Data Adapter
 * Provides complete demo dataset for Stage 3 development
 * Covers all fire classifications and enrichment scenarios
 */

const MOCK_EVENTS = [
    {
        event_id: "evt_pune_001",
        latitude: 18.5204,
        longitude: 73.8567,
        location: {
            city: "Pune",
            state: "Maharashtra",
            country: "India"
        },
        classification: "Industrial Fire",
        risk_score: 87,
        risk_level: "critical",
        confidence: 0.91,
        frp: 74.2,
        persistence: "Repeated anomaly over 5 days",
        industrial_context: {
            nearby_facilities: "MIDC Industrial Hub (120m)",
            osm_proximity: "Within industrial zone"
        },
        water_context: {
            proximity: "Mutex Canal (920m)"
        },
        land_cover: {
            "Built": 87,
            "Trees": 4,
            "Grass": 3,
            "Crops": 3,
            "Bare": 2,
            "Water": 1,
            "Snow & ice": 0,
            "Flooded vegetation": 0,
            "Shrub & scrub": 0
        },
        satellite: {
            available: true,
            url: "https://images.unsplash.com/photo-1579546929518-9e396f3cc809?w=400&h=300&fit=crop",
            acquisition_date: "2026-08-24",
            cloud_cover: 20
        },
        prediction: {
            predicted_class: "Industrial Fire",
            confidence: 0.91,
            risk_score: 87,
            risk_level: "critical",
            model_version: "v2.1.4-production",
            key_factors: [
                { factor: "High Thermal Intensity (FRP)", value: "High (74.2)" },
                { factor: "Industrial Facility Nearby", value: "Yes (MIDC Hub)" },
                { factor: "Land Cover", value: "Built-up (87%)" },
                { factor: "Population Density", value: "High" },
                { factor: "Persistent Anomaly", value: "Yes (5 days)" }
            ]
        },
        color: "#ef4444"
    },
    {
        event_id: "evt_satpura_002",
        latitude: 22.4646,
        longitude: 78.1122,
        location: {
            city: "Satpura Forest Range",
            state: "Madhya Pradesh",
            country: "India"
        },
        classification: "Wildfire / Natural Fire",
        risk_score: 82,
        risk_level: "high",
        confidence: 0.88,
        frp: 142.5,
        persistence: "New thermal manifestation",
        industrial_context: {
            nearby_facilities: "None detected within 5km",
            osm_proximity: "Remote forest"
        },
        water_context: {
            proximity: "Denwa River (1.2km)"
        },
        land_cover: {
            "Trees": 78,
            "Shrub & scrub": 12,
            "Grass": 6,
            "Crops": 2,
            "Water": 1,
            "Built": 1,
            "Bare": 0,
            "Snow & ice": 0,
            "Flooded vegetation": 0
        },
        satellite: {
            available: true,
            url: "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=400&h=300&fit=crop",
            acquisition_date: "2026-08-25",
            cloud_cover: 5
        },
        prediction: {
            predicted_class: "Wildfire / Natural Fire",
            confidence: 0.88,
            risk_score: 82,
            risk_level: "high",
            model_version: "v2.1.4-production",
            key_factors: [
                { factor: "High Thermal Intensity (FRP)", value: "Critical (142.5)" },
                { factor: "Industrial Facility Nearby", value: "No" },
                { factor: "Land Cover", value: "Dense Forest (78% Trees)" },
                { factor: "Population Density", value: "Very Low" },
                { factor: "Water Proximity", value: "River 1.2km" }
            ]
        },
        color: "#ef4444"
    },
    {
        event_id: "evt_punjab_003",
        latitude: 31.1471,
        longitude: 75.3412,
        location: {
            city: "Moga Region",
            state: "Punjab",
            country: "India"
        },
        classification: "Agricultural Fire",
        risk_score: 42,
        risk_level: "low",
        confidence: 0.95,
        frp: 35.1,
        persistence: "Short-lived seasonal activity",
        industrial_context: {
            nearby_facilities: "Farm co-op building (480m)",
            osm_proximity: "Farmland"
        },
        water_context: {
            proximity: "Irrigation canal (150m)"
        },
        land_cover: {
            "Crops": 84,
            "Bare": 10,
            "Built": 4,
            "Trees": 2,
            "Water": 0,
            "Grass": 0,
            "Snow & ice": 0,
            "Flooded vegetation": 0,
            "Shrub & scrub": 0
        },
        satellite: {
            available: false,
            url: null,
            acquisition_date: "2026-08-26",
            cloud_cover: null
        },
        prediction: {
            predicted_class: "Agricultural Fire",
            confidence: 0.95,
            risk_score: 42,
            risk_level: "low",
            model_version: "v1.8-agricultural",
            key_factors: [
                { factor: "Seasonal Fire Activity", value: "Harvest season" },
                { factor: "Land Cover", value: "Active Crops (84%)" },
                { factor: "Thermal Intensity (FRP)", value: "Low (35.1)" },
                { factor: "Persistent Anomaly", value: "No (12 hrs)" }
            ]
        },
        color: "#22c55e"
    },
    {
        event_id: "evt_tata_004",
        latitude: 22.8046,
        longitude: 86.2029,
        location: {
            city: "Jamshedpur",
            state: "Jharkhand",
            country: "India"
        },
        classification: "Persistent Thermal Source",
        risk_score: 68,
        risk_level: "medium",
        confidence: 0.99,
        frp: 92.0,
        persistence: "Continuous signal over 365 days",
        industrial_context: {
            nearby_facilities: "Steel Processing Station (40m)",
            osm_proximity: "Heavy Industrial Zone"
        },
        water_context: {
            proximity: "Subarnarekha River (2.1km)"
        },
        land_cover: {
            "Built": 92,
            "Bare": 4,
            "Water": 2,
            "Trees": 2,
            "Grass": 0,
            "Crops": 0,
            "Snow & ice": 0,
            "Flooded vegetation": 0,
            "Shrub & scrub": 0
        },
        satellite: {
            available: true,
            url: "https://images.unsplash.com/photo-1518770660439-4636190af475?w=400&h=300&fit=crop",
            acquisition_date: "2026-08-22",
            cloud_cover: 45
        },
        prediction: {
            predicted_class: "Persistent Thermal Source",
            confidence: 0.99,
            risk_score: 68,
            risk_level: "medium",
            model_version: "v2.0-persistent",
            key_factors: [
                { factor: "High Persistence", value: "Constant (365+ days)" },
                { factor: "Industrial Context", value: "Steel Plant (40m)" },
                { factor: "FRP Stability", value: "Highly stable" },
                { factor: "Land Cover", value: "Built-up (92%)" }
            ]
        },
        color: "#f97316"
    },
    {
        event_id: "evt_thar_005",
        latitude: 26.2389,
        longitude: 70.9624,
        location: {
            city: "Thar Basin",
            state: "Rajasthan",
            country: "India"
        },
        classification: "Unknown / Other",
        risk_score: 31,
        risk_level: "low",
        confidence: 0.54,
        frp: 18.4,
        persistence: "Irregular anomaly",
        industrial_context: {
            nearby_facilities: "None within 20km"
        },
        water_context: {
            proximity: "None (Arid)"
        },
        land_cover: {
            "Bare": 90,
            "Shrub & scrub": 8,
            "Built": 1,
            "Grass": 1,
            "Trees": 0,
            "Crops": 0,
            "Water": 0,
            "Snow & ice": 0,
            "Flooded vegetation": 0
        },
        satellite: {
            available: false,
            url: null
        },
        prediction: {
            predicted_class: "Unknown / Other",
            confidence: 0.54,
            risk_score: 31,
            risk_level: "low",
            model_version: "v2.1.4-production",
            key_factors: [
                { factor: "Unknown Origin", value: "Low confidence" },
                { factor: "Land Cover", value: "Desert (90% Bare)" },
                { factor: "Thermal Intensity", value: "Very low" }
            ]
        },
        color: "#6b7280"
    }
];

/**
 * Get all mock events
 */
export function getMockEvents() {
    return JSON.parse(JSON.stringify(MOCK_EVENTS)); // Deep copy
}

/**
 * Get single mock event by ID
 */
export function getMockEvent(eventId) {
    const event = MOCK_EVENTS.find(e => e.event_id === eventId);
    return event ? JSON.parse(JSON.stringify(event)) : null;
}

/**
 * Get mock statistics based on events
 */
export function getMockStatistics() {
    const events = MOCK_EVENTS;
    return {
        totalDetections: events.length,
        industrialCount: events.filter(e =>
            e.classification === "Industrial Fire" ||
            e.classification === "Persistent Thermal Source"
        ).length,
        highRiskCount: events.filter(e => e.risk_level === "critical" || e.risk_level === "high").length,
        lowRiskCount: events.filter(e => e.risk_level === "low").length,
        averageRiskScore: Math.round(
            events.reduce((sum, e) => sum + e.risk_score, 0) / events.length
        ),
        demoMode: true
    };
}

/**
 * Get mock prediction for an event
 */
export function getMockPrediction(eventId) {
    const event = MOCK_EVENTS.find(e => e.event_id === eventId);
    if (!event) return null;

    return {
        event_id: event.event_id,
        predicted_class: event.prediction.predicted_class,
        confidence: event.prediction.confidence,
        risk_score: event.prediction.risk_score,
        risk_level: event.prediction.risk_level,
        model_version: event.prediction.model_version,
        key_factors: event.prediction.key_factors
    };
}

/**
 * Get mock satellite data for an event
 */
export function getMockSatelliteData(eventId) {
    const event = MOCK_EVENTS.find(e => e.event_id === eventId);
    if (!event) return null;

    return {
        event_id: event.event_id,
        available: event.satellite.available,
        url: event.satellite.url,
        acquisition_date: event.satellite.acquisition_date,
        cloud_cover: event.satellite.cloud_cover,
        is_demo: true
    };
}

/**
 * Get mock enrichment data for an event
 */
export function getMockEnrichment(eventId) {
    const event = MOCK_EVENTS.find(e => e.event_id === eventId);
    if (!event) return null;

    return {
        event_id: event.event_id,
        location: event.location,
        industrial_context: event.industrial_context,
        water_context: event.water_context,
        land_cover: event.land_cover,
        persistence: event.persistence,
        frp: event.frp
    };
}
