/**
 * Satellite Service
 * Handles Sentinel-2 satellite imagery metadata and preview
 */

import { getConfig } from '../config.js';
import * as mockAdapter from '../adapters/mockAdapter.js';
import * as apiAdapter from '../adapters/apiAdapter.js';

/**
 * Get satellite data for a thermal event
 * Returns: { available, url, acquisition_date, cloud_cover, is_demo }
 */
export async function getSatelliteData(eventId) {
    const config = getConfig();

    try {
        if (config.isDemoMode) {
            // Return mock satellite data
            return new Promise(resolve => {
                setTimeout(() => {
                    const satData = mockAdapter.getMockSatelliteData(eventId);
                    console.log(`[DEMO] Loaded mock satellite data for ${eventId}`);
                    resolve(satData);
                }, 150);
            });
        } else {
            // Fetch from real API
            const satData = await apiAdapter.getSatelliteFromAPI(config.apiBaseUrl, eventId);
            console.log(`[API] Loaded satellite data for ${eventId}`);
            return satData;
        }
    } catch (error) {
        console.error(`Error fetching satellite data for ${eventId}:`, error);
        // Return safe fallback
        return {
            event_id: eventId,
            available: false,
            url: null,
            acquisition_date: null,
            cloud_cover: null,
            error: true
        };
    }
}

/**
 * Get image URL for display
 * Validates URL format and fallback
 */
export function getImageUrl(satData) {
    if (!satData || !satData.available || !satData.url) {
        return null;
    }

    // Validate URL format
    try {
        new URL(satData.url);
        return satData.url;
    } catch (e) {
        console.warn('Invalid satellite image URL:', satData.url);
        return null;
    }
}

/**
 * Format cloud cover percentage for display
 */
export function formatCloudCover(cloudCover) {
    if (cloudCover === null || cloudCover === undefined) {
        return 'N/A';
    }
    return `${Math.round(cloudCover)}%`;
}

/**
 * Format acquisition date
 */
export function formatAcquisitionDate(dateString) {
    if (!dateString) return 'Unknown';

    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch (e) {
        return dateString;
    }
}

/**
 * Get satellite preview state string
 */
export function getSatelliteState(satData) {
    if (!satData) return 'unknown';
    if (satData.error) return 'error';
    if (!satData.available) return 'unavailable';
    if (!satData.url) return 'no-image';
    return 'available';
}

/**
 * Get display message for satellite state
 */
export function getSatelliteStateMessage(state) {
    const messages = {
        'available': 'Sentinel-2 satellite imagery',
        'unavailable': 'No satellite imagery available',
        'no-image': 'Preview not available for this location',
        'error': 'Failed to load satellite data',
        'unknown': 'Satellite data status unknown'
    };
    return messages[state] || 'Loading...';
}
