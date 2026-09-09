/**
 * Fire Intelligence Dashboard - Main Application
 * Stage 3: Dashboard/Application Layer
 */

import { getConfig, setConfig, setConfigValue, getConfigValue, resetConfig } from './src/config.js';
import * as eventsService from './src/services/eventsService.js';
import * as predictionService from './src/services/predictionService.js';
import * as statisticsService from './src/services/statisticsService.js';
import * as satelliteService from './src/services/satelliteService.js';

// =====================================================
// GLOBAL STATE
// =====================================================

let map = null;
let markerLayer = null;
let allEvents = [];
let selectedEvent = null;
let isLoadingPrediction = false;
let isLoadingSatellite = false;
let filteredEvents = [];
let currentClassificationFilter = null;

// Dynamic World color map
const DW_COLORS = {
    "Built": "#ef4444",
    "Trees": "#22c55e",
    "Grass": "#84cc16",
    "Flooded vegetation": "#06b6d4",
    "Crops": "#eab308",
    "Shrub & scrub": "#a16207",
    "Water": "#3b82f6",
    "Bare": "#d6b48a",
    "Snow & ice": "#e2e8f0"
};

// =====================================================
// INITIALIZATION
// =====================================================

document.addEventListener('DOMContentLoaded', async function () {
    console.log('Fire Intelligence Dashboard - Initializing...');

    // Initialize theme
    initializeTheme();

    // Initialize filter menu
    initializeFilterMenu();

    // Initialize classification filters
    initializeClassificationFilters();

    // Initialize navigation
    initializeNavigation();

    // Initialize map
    initializeMap();

    // Load and display events
    await loadAndDisplayEvents();

    // Initialize settings form
    initializeSettings();

    // Start live date/time updates
    updateDateTime();
    setInterval(updateDateTime, 1000);

    console.log('Fire Intelligence Dashboard - Ready!');
});

// =====================================================
// THEME MANAGEMENT
// =====================================================

function initializeTheme() {
    const config = getConfig();
    const savedTheme = localStorage.getItem("theme") || config.theme;

    if (savedTheme === "dark") {
        document.body.classList.add("dark-mode");
        updateThemeIcon(true);
    } else {
        document.body.classList.remove("dark-mode");
        updateThemeIcon(false);
    }
}

function toggleTheme() {
    const isDark = document.body.classList.toggle("dark-mode");
    localStorage.setItem("theme", isDark ? "dark" : "light");
    setConfigValue("theme", isDark ? "dark" : "light");
    updateThemeIcon(isDark);
}

function updateThemeIcon(isDark) {
    const themeIcon = document.querySelector(".theme-toggle i");
    const themeText = document.querySelector(".theme-toggle span");

    if (themeIcon) {
        themeIcon.className = isDark ? "fa-solid fa-sun" : "fa-solid fa-moon";
    }

    if (themeText) {
        themeText.textContent = isDark ? "Light Mode" : "Dark Mode";
    }
}

// =====================================================
// FILTER MENU MANAGEMENT
// =====================================================

function toggleFilterMenu() {
    const filterMenu = document.getElementById("filter-menu");
    if (filterMenu) {
        filterMenu.classList.toggle("show");
    }
}

function initializeFilterMenu() {
    const filterBtn = document.getElementById("filter-btn");
    const filterMenu = document.getElementById("filter-menu");
    const filterOptions = document.querySelectorAll(".filter-option");

    // Toggle menu when button clicked
    if (filterBtn) {
        filterBtn.addEventListener("click", function (e) {
            e.stopPropagation();
            toggleFilterMenu();
        });
    }

    // Handle option selection
    filterOptions.forEach(option => {
        option.addEventListener("click", function (e) {
            e.stopPropagation();
            const filter = this.getAttribute("data-filter");
            console.log(`Filter selected: ${filter}`);

            // Update active state
            filterOptions.forEach(opt => opt.classList.remove("active"));
            this.classList.add("active");

            // Close menu
            if (filterMenu) {
                filterMenu.classList.remove("show");
            }

            // Log filter selection
            if (filter === "today") {
                console.log("Filtering events from today");
            } else if (filter === "24hours") {
                console.log("Filtering events from last 24 hours");
            } else if (filter === "1week") {
                console.log("Filtering events from last 1 week");
            }
        });
    });

    // Close menu when clicking outside
    document.addEventListener("click", function (e) {
        const filterBtn = document.getElementById("filter-btn");
        const filterMenu = document.getElementById("filter-menu");

        if (filterMenu && filterBtn) {
            if (!filterBtn.contains(e.target) && !filterMenu.contains(e.target)) {
                filterMenu.classList.remove("show");
            }
        }
    });
}

// =====================================================
// CLASSIFICATION FILTER
// =====================================================

function initializeClassificationFilters() {
    const fireTypes = document.querySelectorAll(".fire-type");

    fireTypes.forEach(fireType => {
        fireType.addEventListener("click", function (e) {
            e.preventDefault();

            const classification = this.getAttribute("data-classification");

            if (currentClassificationFilter === classification) {
                currentClassificationFilter = null;
                fireTypes.forEach(ft => {
                    ft.style.opacity = "1";
                    ft.style.fontWeight = "normal";
                });
            } else {
                currentClassificationFilter = classification;

                fireTypes.forEach(ft => {
                    if (ft.getAttribute("data-classification") === classification) {
                        ft.style.opacity = "1";
                        ft.style.fontWeight = "bold";
                    } else {
                        ft.style.opacity = "0.5";
                        ft.style.fontWeight = "normal";
                    }
                });
            }

            filterEventsByClassification();
        });
    });
}

function filterEventsByClassification() {
    if (currentClassificationFilter === null) {
        filteredEvents = [...allEvents];
    } else {
        filteredEvents = allEvents.filter(event => {
            const eventClassification = event.classification.toLowerCase().replace(/\s+/g, '_');
            return eventClassification.includes(currentClassificationFilter);
        });
    }

    console.log(`Filtered to ${filteredEvents.length} events (${currentClassificationFilter || 'all'})`);
    displayMarkersOnMap(filteredEvents);

    if (filteredEvents.length > 0) {
        selectEvent(filteredEvents[0]);
    }
}

// =====================================================
// NAVIGATION
// =====================================================

function initializeNavigation() {
    const menuItems = document.querySelectorAll(".menu-item");
    const dashboardView = document.getElementById("dashboard-view");
    const settingsView = document.getElementById("settings-view");

    menuItems.forEach(item => {
        item.addEventListener("click", function (e) {
            e.preventDefault();

            menuItems.forEach(m => m.classList.remove("active"));
            this.classList.add("active");

            const target = this.getAttribute("data-view") || "dashboard";

            if (target === "dashboard") {
                dashboardView.style.display = "block";
                settingsView.style.display = "none";
            } else if (target === "settings") {
                dashboardView.style.display = "none";
                settingsView.style.display = "block";
            }
        });
    });

    if (menuItems.length > 0) {
        menuItems[0].classList.add("active");
        menuItems[0].setAttribute("data-view", "dashboard");
        menuItems[1].setAttribute("data-view", "settings");
    }
}

// =====================================================
// MAP INITIALIZATION
// =====================================================

function initializeMap() {
    const config = getConfig();

    map = L.map("map", {
        zoomControl: false
    }).setView(config.mapDefaultCenter, config.mapDefaultZoom);

    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 19,
            attribution: "&copy; OpenStreetMap contributors"
        }
    ).addTo(map);

    markerLayer = L.layerGroup().addTo(map);

    window.zoomIn = () => map.zoomIn();
    window.zoomOut = () => map.zoomOut();
    window.resetMap = () => {
        const config = getConfig();
        map.setView(config.mapDefaultCenter, config.mapDefaultZoom);
    };
}

// =====================================================
// DATA LOADING AND DISPLAY
// =====================================================

async function loadAndDisplayEvents() {
    try {
        showLoading("events");

        allEvents = await eventsService.getEvents();
        filteredEvents = [...allEvents];
        console.log(`Loaded ${allEvents.length} events`);

        displayMarkersOnMap(filteredEvents);

        await updateSummaryStatistics(allEvents);

        hideLoading("events");
    } catch (error) {
        console.error("Error loading events:", error);
        showError("events", `Failed to load events: ${error.message}`);
    }
}

function displayMarkersOnMap(events) {
    if (!markerLayer) return;

    markerLayer.clearLayers();

    if (events.length === 0) {
        console.warn("No events to display");
        return;
    }

    events.forEach(event => {
        const marker = L.circleMarker(
            [event.latitude, event.longitude],
            {
                radius: 8,
                fillColor: event.color || "#ef4444",
                color: "#ffffff",
                weight: 2,
                opacity: 1,
                fillOpacity: 0.9
            }
        );

        marker.bindPopup(`
            <div style="min-width: 200px; font-family: Arial, sans-serif;">
                <strong style="font-size: 14px; color: #111827;">
                    ${event.location.city || 'Unknown'}, ${event.location.state || ''}
                </strong>
                <br><br>
                <span style="font-size: 12px;">
                    <strong>Classification:</strong> ${event.classification}
                </span>
                <br>
                <span style="font-size: 12px;">
                    <strong>Risk:</strong> ${event.risk_level.toUpperCase()} (${event.risk_score}/100)
                </span>
                <br>
                <span style="font-size: 12px;">
                    <strong>Confidence:</strong> ${predictionService.getConfidencePercentage(event.confidence)}%
                </span>
            </div>
        `);

        marker.on("click", function () {
            selectEvent(event);
        });

        marker.addTo(markerLayer);
    });
}

// =====================================================
// EVENT SELECTION AND DETAIL DISPLAY
// =====================================================

async function selectEvent(event) {
    selectedEvent = event;
    console.log(`Selected event: ${event.event_id}`);

    updateLocationDisplay(event);
    updateRiskDisplay(event);

    await loadAndDisplayPrediction(event);
    await loadAndDisplaySatellite(event);

    updateLandCoverChart(event.land_cover);

    map.flyTo([event.latitude, event.longitude], 8, { duration: 1 });
}

function updateLocationDisplay(event) {
    const locationName = document.querySelector(".location strong");
    const coordinates = document.querySelector(".location span");

    if (locationName) {
        const city = event.location.city || 'Unknown';
        const state = event.location.state || '';
        const country = event.location.country || 'India';
        locationName.textContent = `${city}${state ? ', ' + state : ''}, ${country}`;
    }

    if (coordinates) {
        coordinates.textContent = `${event.latitude.toFixed(4)}, ${event.longitude.toFixed(4)}`;
    }
}

function updateRiskDisplay(event) {
    const riskScore = document.querySelector(".risk-score strong");
    const criticalLabel = document.querySelector(".critical b");
    const fireCircle = document.querySelector(".fire-circle");

    if (riskScore) {
        riskScore.innerHTML = `${event.risk_score} <small>/ 100</small>`;
    }

    if (criticalLabel) {
        const label = event.risk_level === 'critical' ? 'CRITICAL' :
                      event.risk_level === 'high' ? 'HIGH' :
                      event.risk_level === 'medium' ? 'MEDIUM' : 'LOW';
        criticalLabel.textContent = label;

        const color = event.risk_level === 'critical' ? '#ef4444' :
                      event.risk_level === 'high' ? '#ef4444' :
                      event.risk_level === 'medium' ? '#f97316' : '#22c55e';
        criticalLabel.style.color = color;
    }

    if (fireCircle) {
        const bgColor = event.risk_level === 'critical' ? '#fee2e2' :
                        event.risk_level === 'high' ? '#fee2e2' :
                        event.risk_level === 'medium' ? '#ffedd5' : '#dcfce7';
        fireCircle.style.background = bgColor;
    }
}

async function loadAndDisplayPrediction(event) {
    try {
        isLoadingPrediction = true;
        showPredictionLoading();

        const prediction = await predictionService.getPrediction(event.event_id, {
            latitude: event.latitude,
            longitude: event.longitude,
            classification: event.classification,
            risk_score: event.risk_score
        });

        updatePredictionDisplay(prediction);
        updateKeyFactorsDisplay(prediction.key_factors);

        isLoadingPrediction = false;
        hidePredictionLoading();
    } catch (error) {
        console.error("Error loading prediction:", error);
        showPredictionError(error.message);
        isLoadingPrediction = false;
    }
}

function updatePredictionDisplay(prediction) {
    const predictionElement = document.querySelector(".prediction strong");
    const confidenceElement = document.querySelector(".confidence strong");

    if (predictionElement) {
        predictionElement.textContent = prediction.predicted_class || 'Unknown';
    }

    if (confidenceElement) {
        const confidencePercent = predictionService.getConfidencePercentage(prediction.confidence);
        confidenceElement.textContent = `${confidencePercent}%`;

        if (confidencePercent >= 90) {
            confidenceElement.style.color = '#22c55e';
        } else if (confidencePercent >= 75) {
            confidenceElement.style.color = '#f97316';
        } else {
            confidenceElement.style.color = '#ef4444';
        }
    }
}

function updateKeyFactorsDisplay(keyFactors) {
    const factorsContainer = document.querySelector(".factors");
    if (!factorsContainer) return;

    let factorsList = factorsContainer.querySelector(".factors-list");
    if (!factorsList) {
        factorsList = document.createElement("div");
        factorsList.className = "factors-list";
        factorsContainer.appendChild(factorsList);
    }

    factorsList.innerHTML = '';

    if (!keyFactors || keyFactors.length === 0) {
        factorsList.innerHTML = '<div class="factor"><span>No factors available</span></div>';
        return;
    }

    keyFactors.forEach(factor => {
        const factorDiv = document.createElement("div");
        factorDiv.className = "factor";
        factorDiv.innerHTML = `
            <span><i class="fa-solid fa-circle"></i> ${factor.name || 'Unknown'}</span>
            <b>${factor.value || '—'}</b>
        `;
        factorsList.appendChild(factorDiv);
    });
}

async function loadAndDisplaySatellite(event) {
    try {
        isLoadingSatellite = true;
        showSatelliteLoading();

        const satellite = await satelliteService.getSatelliteData(event.event_id);

        updateSatelliteDisplay(satellite);

        isLoadingSatellite = false;
        hideSatelliteLoading();
    } catch (error) {
        console.error("Error loading satellite:", error);
        showSatelliteError();
        isLoadingSatellite = false;
    }
}

function updateSatelliteDisplay(satellite) {
    const satelliteImage = document.getElementById("satellite-image");

    if (!satelliteImage) return;

    if (satellite && satellite.image_url) {
        satelliteImage.style.background = `url('${satellite.image_url}') center/cover`;
        satelliteImage.innerHTML = '<div class="sat-overlay" style="background: rgba(0,0,0,0);"></div>';
    } else {
        generateSatelliteVisualization(satelliteImage, satellite);
    }

    const satFooter = document.querySelector(".sat-footer");
    if (satFooter && satellite) {
        const dateSpan = satFooter.querySelector("span");
        const cloudSpan = satFooter.querySelectorAll("span")[1];

        if (dateSpan) {
            dateSpan.textContent = `Date: ${satellite.acquisition_date || 'Unknown'}`;
        }

        if (cloudSpan) {
            cloudSpan.innerHTML = `<i class="fa-solid fa-cloud"></i> ${satellite.cloud_cover || '0'}%`;
        }
    }
}

function generateSatelliteVisualization(element, satellite) {
    if (!element) return;

    const lat = selectedEvent ? selectedEvent.latitude : 22.97;
    const lng = selectedEvent ? selectedEvent.longitude : 78.65;

    const colors = ['#e0f2fe', '#bae6fd', '#7dd3fc', '#38bdf8', '#0ea5e9', '#06b6d4'];
    const randomColor = colors[Math.floor(Math.random() * colors.length)];

    element.style.background = `linear-gradient(135deg, ${randomColor} 0%, #f0f9ff 50%, #e0f2fe 100%)`;
    element.innerHTML = `
        <div class="sat-overlay" style="background: rgba(0,0,0,0); display: flex; align-items: center; justify-content: center; flex-direction: column; gap: 10px;">
            <div style="font-size: 14px; color: #0369a1; font-weight: bold;">Satellite View</div>
            <div style="font-size: 11px; color: #0ea5e9;">Lat: ${lat.toFixed(3)}°, Lng: ${lng.toFixed(3)}°</div>
        </div>
    `;
}

function updateLandCoverChart(landCover) {
    if (!landCover || Object.keys(landCover).length === 0) return;

    let totalPercentage = 0;
    const gradientStops = [];
    let currentDegree = 0;

    Object.entries(landCover).forEach(([key, value]) => {
        const percentage = parseFloat(value) || 0;
        const color = DW_COLORS[key] || '#d1d5db';
        const degreesForThisSegment = (percentage / 100) * 360;

        gradientStops.push(`${color} ${currentDegree}deg ${currentDegree + degreesForThisSegment}deg`);
        currentDegree += degreesForThisSegment;
        totalPercentage += percentage;
    });

    const donut = document.querySelector(".donut");
    if (donut) {
        donut.style.background = `conic-gradient(${gradientStops.join(', ')})`;

        const donutContent = donut.querySelector("div");
        if (donutContent) {
            const maxKey = Object.keys(landCover).reduce((a, b) =>
                parseFloat(landCover[a]) > parseFloat(landCover[b]) ? a : b
            );
            donutContent.innerHTML = `
                <strong>${Math.round(landCover[maxKey])}%</strong>
                <span>${maxKey}</span>
            `;
        }
    }

    const landList = document.querySelector(".land-list");
    if (landList) {
        landList.innerHTML = '';

        Object.entries(landCover).forEach(([key, value]) => {
            const percentage = Math.round(parseFloat(value)) || 0;
            const color = DW_COLORS[key] || '#d1d5db';

            const item = document.createElement("div");
            item.innerHTML = `
                <span class="land-color" style="background-color: ${color}; display: inline-block; width: 12px; height: 12px; border-radius: 3px;"></span>
                ${key}
                <b>${percentage}%</b>
            `;
            landList.appendChild(item);
        });
    }
}

async function updateSummaryStatistics(events) {
    try {
        const stats = await statisticsService.getStatistics();

        const summaryPanel = document.querySelector(".summary-panel");
        if (!summaryPanel) return;

        const items = summaryPanel.querySelectorAll(".summary-item");
        if (items.length >= 4) {
            items[0].querySelector("strong").textContent = stats.totalDetections || 0;
            items[1].querySelector("strong").textContent = stats.industrialCount || 0;
            items[2].querySelector("strong").textContent = stats.highRiskCount || 0;
            items[3].querySelector("strong").textContent = stats.lowRiskCount || 0;
        }
    } catch (error) {
        console.error("Error updating statistics:", error);
    }
}

// =====================================================
// LOADING/ERROR STATES
// =====================================================

function showLoading(type) {
    const element = type === 'events' ? document.querySelector('.map-card') : null;
    if (!element) return;

    const loader = document.createElement('div');
    loader.className = 'loader-overlay';
    loader.innerHTML = '<div class="spinner"></div>';
    element.style.position = 'relative';
    element.appendChild(loader);
}

function hideLoading(type) {
    const loader = document.querySelector('.loader-overlay');
    if (loader) loader.remove();
}

function showError(type, message) {
    console.error(message);
}

function showPredictionLoading() {
    const pred = document.querySelector(".prediction strong");
    if (pred) pred.textContent = 'Loading...';
}

function hidePredictionLoading() {
}

function showPredictionError(message) {
    const pred = document.querySelector(".prediction strong");
    if (pred) pred.textContent = 'Error loading prediction';
    const conf = document.querySelector(".confidence strong");
    if (conf) conf.textContent = '—';
}

function showSatelliteLoading() {
    const sat = document.querySelector(".satellite-image");
    if (sat) sat.innerHTML = '<div class="sat-overlay"><i class="fa-solid fa-spinner fa-spin"></i> Loading...</div>';
}

function hideSatelliteLoading() {
}

function showSatelliteError() {
    const sat = document.querySelector(".satellite-image");
    if (sat) {
        sat.style.background = '#f3f4f6';
        sat.innerHTML = '<div class="sat-overlay" style="background: rgba(0,0,0,0); color: #6b7280;">Image not available</div>';
    }
}

// =====================================================
// UTILITIES
// =====================================================

function updateDateTime() {
    const dateBox = document.querySelector(".date-box strong");
    const timeBox = document.querySelector(".date-box span");

    if (dateBox || timeBox) {
        const now = new Date();
        const dateStr = now.toLocaleDateString('en-IN', {
            day: 'numeric',
            month: 'short',
            year: 'numeric'
        });
        const dayStr = now.toLocaleDateString('en-IN', { weekday: 'long' });
        const timeStr = now.toLocaleTimeString('en-IN', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
        });

        if (dateBox) dateBox.textContent = dateStr;
        if (timeBox) timeBox.textContent = `${dayStr} ${timeStr}`;
    }
}

// Settings initialization
function initializeSettings() {
    const saveBtn = document.getElementById("settings-save");
    const resetBtn = document.getElementById("settings-reset");
    const themeToggle = document.getElementById("theme-toggle");
    const dataModeToggle = document.getElementById("data-mode-toggle");
    const apiUrlInput = document.getElementById("api-base-url");
    const mlUrlInput = document.getElementById("ml-service-url");

    if (themeToggle) {
        themeToggle.checked = document.body.classList.contains("dark-mode");
        themeToggle.addEventListener("change", toggleTheme);
    }

    if (saveBtn) {
        saveBtn.addEventListener("click", function () {
            const config = {
                isDemoMode: dataModeToggle.checked,
                apiBaseUrl: apiUrlInput.value,
                mlServiceUrl: mlUrlInput.value
            };
            setConfig(config);
            alert("Settings saved!");
        });
    }

    if (resetBtn) {
        resetBtn.addEventListener("click", function () {
            if (confirm("Reset to default settings?")) {
                resetConfig();
                location.reload();
            }
        });
    }
}

window.resetDetection = function () {
    if (filteredEvents.length > 0) {
        selectEvent(filteredEvents[0]);
    }
};

window.toggleTheme = toggleTheme;
window.toggleFilterMenu = toggleFilterMenu;
