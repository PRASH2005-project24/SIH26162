/**
 * Statistics Service
 * Provides dashboard summary statistics
 * Calculates or fetches aggregated data
 */

import { getConfig } from '../config.js';
import * as mockAdapter from '../adapters/mockAdapter.js';
import * as apiAdapter from '../adapters/apiAdapter.js';

/**
 * Get dashboard statistics
 * Returns: { totalDetections, industrialCount, highRiskCount, lowRiskCount, averageRiskScore, demoMode }
 */
export async function getStatistics(events = null) {
    const config = getConfig();

    try {
        if (config.isDemoMode) {
            // Return mock statistics
            return new Promise(resolve => {
                setTimeout(() => {
                    const stats = mockAdapter.getMockStatistics();
                    console.log('[DEMO] Loaded mock statistics');
                    resolve(stats);
                }, 100);
            });
        } else {
            // Fetch from real API
            const stats = await apiAdapter.getStatisticsFromAPI(config.apiBaseUrl);
            console.log('[API] Loaded statistics from backend');
            return stats;
        }
    } catch (error) {
        console.error('Error fetching statistics:', error);
        // Return safe fallback
        return {
            totalDetections: 0,
            industrialCount: 0,
            highRiskCount: 0,
            lowRiskCount: 0,
            averageRiskScore: 0,
            demoMode: config.isDemoMode,
            error: true
        };
    }
}

/**
 * Calculate statistics from events array
 * Useful for client-side calculation if needed
 */
export function calculateStatisticsFromEvents(events) {
    if (!Array.isArray(events) || events.length === 0) {
        return {
            totalDetections: 0,
            industrialCount: 0,
            highRiskCount: 0,
            lowRiskCount: 0,
            averageRiskScore: 0
        };
    }

    const industrial = events.filter(e =>
        e.classification === 'Industrial Fire' ||
        e.classification === 'Persistent Thermal Source'
    );

    const highRisk = events.filter(e =>
        e.risk_level === 'critical' || e.risk_level === 'high'
    );

    const lowRisk = events.filter(e =>
        e.risk_level === 'low'
    );

    const avgScore = events.reduce((sum, e) => sum + (e.risk_score || 0), 0) / events.length;

    return {
        totalDetections: events.length,
        industrialCount: industrial.length,
        highRiskCount: highRisk.length,
        lowRiskCount: lowRisk.length,
        averageRiskScore: Math.round(avgScore)
    };
}

/**
 * Get change indicators (percentage changes)
 * This is typically stored/calculated server-side
 */
export function getChangeIndicators() {
    // Mock change data - would come from time-series analysis
    return {
        detectionsTrend: { value: 22, unit: '%', direction: 'up' },
        industrialTrend: { value: 2, unit: '%', direction: 'up' },
        weatherRiskTrend: { value: 20, unit: '%', direction: 'up' }
    };
}
