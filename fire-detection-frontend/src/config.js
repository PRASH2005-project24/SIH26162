/**
 * Stage 3 Configuration System
 * Manages runtime settings with localStorage persistence
 */

const DEFAULT_CONFIG = {
    isDemoMode: true,
    apiBaseUrl: "http://localhost:8000/api",
    mlServiceUrl: "http://localhost:5000/predict",
    mapDefaultCenter: [22.9734, 78.6569],
    mapDefaultZoom: 5,
    autoRefreshInterval: 300, // seconds (5 mins) or 0 (disabled)
    enableClustering: false,
    theme: "light"
};

const STORAGE_KEY = "fire-intelligence-config";

/**
 * Load configuration from localStorage or return defaults
 */
function loadConfig() {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) {
            return { ...DEFAULT_CONFIG, ...JSON.parse(stored) };
        }
    } catch (error) {
        console.warn("Failed to load config from localStorage:", error);
    }
    return { ...DEFAULT_CONFIG };
}

/**
 * Current configuration state
 */
let currentConfig = loadConfig();

/**
 * Get current configuration
 */
export function getConfig() {
    return { ...currentConfig };
}

/**
 * Update configuration and persist to localStorage
 */
export function setConfig(updates) {
    currentConfig = { ...currentConfig, ...updates };
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(currentConfig));
    } catch (error) {
        console.error("Failed to save config to localStorage:", error);
    }
    return { ...currentConfig };
}

/**
 * Reset configuration to defaults
 */
export function resetConfig() {
    currentConfig = { ...DEFAULT_CONFIG };
    try {
        localStorage.removeItem(STORAGE_KEY);
    } catch (error) {
        console.error("Failed to reset config:", error);
    }
    return { ...currentConfig };
}

/**
 * Get specific config value
 */
export function getConfigValue(key) {
    return currentConfig[key];
}

/**
 * Set specific config value
 */
export function setConfigValue(key, value) {
    return setConfig({ [key]: value });
}
