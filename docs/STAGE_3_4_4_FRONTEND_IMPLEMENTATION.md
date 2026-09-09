# Stage 3.4.4 Frontend Implementation

## Overview
This document describes the implementation of Stage 3.4.4 of the SIH26162 project, which involves creating a frontend for the fire detection and intelligence system. The frontend is built using React, TypeScript, Vite, Tailwind CSS, Leaflet, and Recharts.

## Implemented Features

### 1. Map Interface
- **World Map**: Displays a global map using Leaflet and OpenStreetMap tiles, centered on India by default.
- **Event Markers**: Thermal events from the backend API are displayed as markers on the map.
- **Marker Clustering**: Not implemented due to the use of vanilla Leaflet markers (leaflet.markercluster is a plugin that requires additional setup; however, the current implementation uses individual markers which is acceptable for moderate event volumes).
- **Category-Based Visualization**: Markers are color-coded and shaped according to the five SIH categories:
  - Industrial Fire (red rectangle)
  - Wildfire / Natural Fire (orange flame-like shape)
  - Agricultural Fire (yellow circle with white cross)
  - Persistent Thermal Source (blue circle with white dot)
  - Unknown / Other (gray flame-like shape with white center)
- **Marker Interaction**: Clicking a marker opens a popup with basic event info and selects the event, opening the intelligence panel.
- **Map Legend**: Shows the symbol and label for each category currently visible in the map view.
- **Map Controls**: Includes zoom controls and allows panning and zooming globally.

### 2. Event Listing and Filtering
- **Event List**: Displays a list of thermal events with key information (category, time, location, FRP, industrial zone, land cover).
- **Filters**:
  - Time Range: Today, Last 24 Hours, Last 7 Days, Last 30 Days, Custom (with date picker).
  - Categories: Checkboxes for each of the five SIH categories to filter events by their final SIH classification.
- **Live Updates**: The event list and map refresh every minute to reflect new detections.

### 3. Event Intelligence Panel
When an event is selected (by clicking its marker), a slide-in panel displays detailed information:

#### A. Final SIH Classification
- Prominently displays the final SIH category (one of the five) with a color-coded badge.

#### B. ML Information
- Shows the original ML prediction (Agricultural, Industrial, or Wildfire) derived from the model's class probabilities.
- Displays the confidence of the original ML prediction.
- Shows the probabilities for each of the three ML classes.

#### C. Event Location
- Latitude and longitude coordinates.

#### D. FIRMS Information
- Acquisition time, satellite, day/night, status, confidence, brightness temperature, and FRP.

#### E. Persistence Information
- Whether the event is classified as a persistent thermal source (based on duration >= 30 days and observations on >= 5 distinct dates).
- Number of unique observation dates.
- Duration in days.
- (If available) persistence date count and persistence duration days.

#### F. OSM Information
- Whether the event is inside an industrial zone.
- Distance to the nearest feature (if available).
- Count of features within 1km.
- Presence of nearby water.

#### G. Dynamic World Information
- Dominant land-cover label.
- Class probabilities for land cover (water, trees, grass, flooded vegetation, crops, shrub/scrub, built, bare, snow/ice).
- Acquisition and query dates.
- Coverage state.

#### H. Technical Details (Expandable)
- Raw FIRMS data (satellite, instrument, day/night, status, confidence, brightness, FRP).
- Raw OSM data (if available).
- Raw Dynamic World data (if available).
- Raw persistence data (if available).

### 4. Analytics Dashboard
- **Key Metrics**: Total detections, active detections, enriched events, average confidence.
- **Charts**:
  - Bar chart showing overview of detection counts (total, active, enriched, industrial, near water, last 24H).
  - Pie chart showing distribution of available categorized data (active detections, enriched events, industrial events, near water events).
- **Notes**: Explains that category-specific counts are not available in the statistics endpoint and that users should use filters for detailed category distribution.

### 5. Navigation and Layout
- **Persistent Sidebar**: Collapsible on smaller screens. Contains navigation links to:
  - Dashboard (placeholder)
  - Live Events
  - Historical Events
  - Analytics
  - Settings (placeholder)
- **Header**: Includes toggle for sidebar and theme (light/dark mode).
- **Responsive Design**: Layout adapts to different screen sizes (desktop, tablet, mobile).

### 6. Localization
- **Language Support**: English and Hindi (using the existing localization architecture; however, due to time constraints, the implementation currently uses English only. The structure is in place for easy integration of a localization library like i18next).
- **Theme Support**: Light and dark modes, with preference saved to localStorage and respect for system preference.

### 7. Loading, Error, and Empty States
- **Loading**: Shown while fetching data from the API.
- **Error**: Displayed if API requests fail.
- **Empty**: Shown when no events match the current filters.

### 8. API Integration
- **Centralized API Layer**: Uses `src/lib/api.ts` with Axios instance configured to the backend URL.
- **Endpoints Used**:
  - `GET /api/v1/events`: For listing events with filters (time, category, etc.).
  - `GET /api/v1/events/{id}`: For detailed event information (used in the intelligence panel).
  - `GET /api/v1/statistics`: For dashboard statistics.
- **Data Transformation**: The frontend expects the backend to return the SIH category in the `classification.category` field (which it does, as per the backend implementation).

## Validation Performed
- **TypeScript Check**: No errors (`npx tsc --noEmit`).
- **Development Server**: Started successfully and loads without runtime errors (in console).
- **Map Rendering**: Map loads and displays markers when events are available.
- **Event Selection**: Clicking a marker opens the intelligence panel with correct data.
- **Filtering**: Time range and category filters update the event list and map accordingly.
- **Responsive Layout**: Tested by resizing the browser window; sidebar collapses on smaller screens.
- **Dark/Light Mode**: Toggling theme changes the appearance and persists in localStorage.
- **Data Honesty**: No fake data is introduced; unavailable fields are shown as "N/A" or omitted.

## Known Limitations
- **Marker Clustering**: The current implementation uses individual markers which may cause performance issues with very large datasets. However, the use of backend filtering (time and geographic bounds) limits the number of events fetched.
- **Persistent Thermal Source Calculation**: The frontend relies on the backend's persistence calculation (via the `persistence` field in the event response). The frontend does not re-calculate persistence.
- **Localization**: The UI currently uses hardcoded English strings. The context for locale is set up but not fully integrated with a translation library. This is a known limitation that can be addressed in a future stage.
- **Dashboard Placeholders**: The Dashboard and Settings pages are placeholders and do not contain functional content beyond the statistics cards (in LiveEvents and HistoricalEvents).
- **Map Layers**: Only OpenStreetMap (standard) layer is implemented. Terrain and satellite imagery layers are not included due to the unavailability of free, legitimate global tile sources that comply with the requirement not to fabricate imagery. A note is shown if such layers were to be added in the future.

## Files Created or Modified
- `src/components/events/EventItem.tsx`: Updated to display SIH category and confidence.
- `src/components/details/SIHClassificationSection.tsx`: New component showing final SIH classification, original ML prediction, and class probabilities.
- `src/components/details/EventIntelligencePanel.tsx`: Updated to use SIHClassificationSection and adjust layout.
- `src/components/map/MapContainer.tsx`: Fixed category extraction for legend.
- `src/components/map/EventMarker.tsx`: No changes (but verified correct).
- `src/components/map/MapLegend.tsx`: No changes (but verified correct).
- `src/hooks/useEvents.ts`: Added category filtering and adjusted parameters.
- `src/hooks/useFilters.ts`: No changes (but verified correct).
- `src/components/ui/SiHCategoryBadge.tsx`: No changes (but verified correct).
- `src/pages/LiveEvents.tsx`: No changes (but verified correct).
- `src/pages/HistoricalEvents.tsx`: No changes (but verified correct).
- `src/pages/Analytics.tsx`: No changes (but verified correct).
- `src/context/ThemeContext.tsx`: No changes (but verified correct).
- `src/types/index.ts`: No changes (but verified correct).
- `src/types/api.ts`: No changes (but verified correct).
- `src/lib/api.ts`: No changes (but verified correct).
- `docs/STAGE_3_4_4_FRONTEND_IMPLEMENTATION.md`: New document.

## Backend API Endpoints Integrated
- `GET /api/v1/events` (with parameters: limit, include_ml, include_enrichment, since_hours, etc.)
- `GET /api/v1/events/{event_id}` (with parameters: include_enrichment, include_ml)
- `GET /api/v1/statistics`

## SIH Compliance Status
- [x] Five SIH categories are represented correctly.
- [x] Three-class ML semantics are preserved (original ML probabilities shown separately).
- [x] Persistent Thermal Source is post-processing (handled by backend, frontend displays the result).
- [x] Unknown / Other is represented correctly.
- [x] No five-class probability distribution is fabricated (only three-class probabilities shown).
- [x] FIRMS event data comes from backend.
- [x] Historical filtering is database/API-backed (via the `since_hours` parameter).
- [x] OSM information is contextual (displayed as raw data).
- [x] Dynamic World is contextual land-cover evidence (displayed as raw data).
- [x] Persistence evidence is backend-derived (displayed from the persistence field).
- [x] Satellite preview is not implemented (backend does not provide it; unavailable state would be shown if attempted).
- [x] India-wide operational scope is preserved (map defaults to India but allows global navigation).
- [x] World map navigation works (zoom and pan).
- [x] Selected event intelligence works (all sections populate with available data).
- [x] Analytics use supported statistics (from the /statistics endpoint).
- [x] No unsupported risk claims are presented (the statistics note explains that high/low risk counts are pseudo-metrics).
- [x] English works (default language).
- [ ] Hindi localization is not fully implemented (structure exists but no translations).
- [x] Dark/light mode works.
- [x] Responsive layout works (sidebar collapses, content adjusts).
- [x] Accessibility basics: semantic headings, labels, color contrast (buttons and badges have sufficient contrast), focus states (standard).
- [x] Loading/error/empty states work.
- [x] No silent demo fallback exists (the app shows errors if backend is unreachable).
- [x] No alerting was introduced.
- [x] No frozen ML artifacts were changed (frontend only).
- [x] frontend-old remains untouched.

## Readiness for Stage 3.5
The frontend is ready for Stage 3.5, which involves further refinement and integration with any additional backend features. The current implementation provides a solid foundation for displaying thermal events, their classifications, and associated contextual information in a GIS-centered, data-honest manner.

## Notes
The implementation adheres strictly to the SIH requirements, prioritizing correctness and data honesty over visual flourishes. The frontend is designed to be a usable operational tool for monitoring and investigating thermal events.