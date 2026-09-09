/**
 * Events Service
 * Abstraction layer for fetching thermal events
 * Routes to mock or real API based on configuration
 */

import { getConfig } from '../config.js';
import * as mockAdapter from '../adapters/mockAdapter.js';
import * as apiAdapter from '../adapters/apiAdapter.js';

/**
 * Get all thermal events
 * Automatically routes to mock or real API based on config.isDemoMode
 */
export async function getEvents() {
    const config = getConfig();

    try {
        if (config.isDemoMode) {
            // Return mock data with a slight delay to simulate network
            return new Promise(resolve => {
                setTimeout(() => {
                    const events = mockAdapter.getMockEvents();
                    console.log(`[DEMO] Loaded ${events.length} mock events`);
                    resolve(events);
                }, 100);
            });
        } else {
            // Fetch from real API
            const events = await apiAdapter.getEventsFromAPI(config.apiBaseUrl);
            console.log(`[API] Loaded ${events.length} events from ${config.apiBaseUrl}`);
            return events;
        }
    } catch (error) {
        console.error('Error fetching events:', error);
        throw error;
    }
}

/**
 * Get single event by ID
 */
export async function getEvent(eventId) {
    const config = getConfig();

    try {
        if (config.isDemoMode) {
            return new Promise(resolve => {
                setTimeout(() => {
                    const event = mockAdapter.getMockEvent(eventId);
                    console.log(`[DEMO] Loaded mock event ${eventId}`);
                    resolve(event);
                }, 50);
            });
        } else {
            const event = await apiAdapter.getEventFromAPI(config.apiBaseUrl, eventId);
            console.log(`[API] Loaded event ${eventId}`);
            return event;
        }
    } catch (error) {
        console.error(`Error fetching event ${eventId}:`, error);
        throw error;
    }
}

/**
 * Get enrichment data for an event
 */
export async function getEnrichment(eventId) {
    const config = getConfig();

    try {
        if (config.isDemoMode) {
            return new Promise(resolve => {
                setTimeout(() => {
                    const enrichment = mockAdapter.getMockEnrichment(eventId);
                    resolve(enrichment);
                }, 50);
            });
        } else {
            return await apiAdapter.getEnrichmentFromAPI(config.apiBaseUrl, eventId);
        }
    } catch (error) {
        console.error(`Error fetching enrichment for ${eventId}:`, error);
        throw error;
    }
}
