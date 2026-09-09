/**
 * Prediction Service
 * Handles Stage 2 ML model predictions
 * Integrates with ML service for fire classification and risk assessment
 */

import { getConfig } from '../config.js';
import * as mockAdapter from '../adapters/mockAdapter.js';
import * as apiAdapter from '../adapters/apiAdapter.js';

/**
 * Get ML prediction for a thermal event
 * Returns: { predicted_class, confidence, risk_score, risk_level, model_version, key_factors }
 */
export async function getPrediction(eventId, eventData = {}) {
    const config = getConfig();

    try {
        if (config.isDemoMode) {
            // Return mock prediction with delay
            return new Promise(resolve => {
                setTimeout(() => {
                    const prediction = mockAdapter.getMockPrediction(eventId);
                    console.log(`[DEMO] Loaded mock prediction for ${eventId}`);
                    resolve(prediction);
                }, 200);
            });
        } else {
            // Fetch from real ML service
            const prediction = await apiAdapter.getPredictionFromAPI(
                config.mlServiceUrl,
                eventId,
                eventData
            );
            console.log(`[API] Loaded prediction from ML service for ${eventId}`);
            return prediction;
        }
    } catch (error) {
        console.error(`Error fetching prediction for ${eventId}:`, error);
        // Return a safe fallback that doesn't crash the UI
        return {
            event_id: eventId,
            predicted_class: 'Unknown',
            confidence: 0,
            risk_score: 0,
            risk_level: 'low',
            model_version: 'error',
            key_factors: [
                { factor: 'Error', value: error.message }
            ],
            error: true
        };
    }
}

/**
 * Validate prediction data structure
 */
export function validatePrediction(prediction) {
    if (!prediction) return false;
    return (
        prediction.predicted_class &&
        typeof prediction.confidence === 'number' &&
        typeof prediction.risk_score === 'number' &&
        prediction.risk_level &&
        Array.isArray(prediction.key_factors)
    );
}

/**
 * Get display-friendly confidence percentage
 */
export function getConfidencePercentage(confidence) {
    if (typeof confidence !== 'number') return 0;
    // If confidence is already a percentage (0-100), return as-is
    // If it's a decimal (0-1), convert to percentage
    return confidence > 1 ? Math.round(confidence) : Math.round(confidence * 100);
}

/**
 * Get risk level from risk score
 */
export function getRiskLevelFromScore(score) {
    if (score >= 75) return 'critical';
    if (score >= 50) return 'medium';
    return 'low';
}
