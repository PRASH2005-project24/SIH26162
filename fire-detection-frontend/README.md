# Fire Intelligence Dashboard - Stage 3

**AI-Powered Thermal Event Intelligence Platform**

This is the Stage 3 implementation of the SIH26162 Thermal Event Intelligence Platform. It provides a comprehensive dashboard for visualizing, analyzing, and monitoring thermal fire events across India using satellite data, machine learning predictions, and GIS enrichment.

## Overview

The Fire Intelligence Dashboard displays:
- **Real-time thermal event markers** on an interactive India-focused map
- **Fire classification** (Industrial, Wildfire, Agricultural, Persistent Thermal Source, Unknown)
- **Risk assessment** with confidence scoring
- **Land cover analysis** using Dynamic World datasets
- **Satellite imagery preview** from Sentinel-2
- **ML-powered predictions** from Stage 2 models
- **Dashboard statistics** and summary insights

## Project Structure

```
fire-intelligence-dashboard/
├── index.html                 # Main HTML structure
├── style.css                  # All styling (light + dark mode)
├── script.js                  # Main application (ES Module)
│
├── src/
│   ├── config.js              # Configuration management
│   │
│   ├── adapters/
│   │   ├── mockAdapter.js     # Demo data provider
│   │   └── apiAdapter.js      # Real API integration
│   │
│   └── services/
│       ├── eventsService.js        # Thermal event fetching
│       ├── predictionService.js    # ML prediction integration
│       ├── statisticsService.js    # Dashboard statistics
│       └── satelliteService.js     # Sentinel-2 metadata
│
├── README.md                  # This file
└── .env.example               # Configuration template
```

## Installation & Setup

### Requirements
- **No build system required** - Pure vanilla HTML/CSS/JavaScript
- **Modern browser** - Chrome, Firefox, Safari, Edge (ES Modules support)
- **Local HTTP server** - Required to load ES Modules (file:// protocol won't work)

### Step 1: Extract Files
Extract the provided ZIP file to your desired location:
```bash
unzip fire-intelligence-dashboard.zip
cd fire-intelligence-dashboard
```

### Step 2: Start Local Server

**Option A: Python (built-in)**
```bash
# Python 3.x
python -m http.server 8080

# Python 2.x
python -m SimpleHTTPServer 8080
```

**Option B: Node.js**
```bash
npx serve .
# or
npx http-server
```

**Option C: Live Server (VS Code)**
- Install "Live Server" extension
- Right-click `index.html` → "Open with Live Server"

### Step 3: Open in Browser
Navigate to: `http://localhost:8080`

## Features

### Dashboard
- **Interactive Map**: Pan, zoom, and click thermal event markers to view details
- **Risk Visualization**: Color-coded markers (red=high, orange=medium, green=low)
- **Event Details Panel**: Location, risk score, ML predictions, key factors
- **Land Cover Chart**: Dynamic donut visualization of Dynamic World classes
- **Satellite Preview**: Sentinel-2 imagery with acquisition date and cloud cover
- **Summary Statistics**: Total detections, industrial areas, weather risk, low risk events
- **Dark Mode**: Toggle between light and dark themes with persistent preference

### Settings
- **Theme**: Light/Dark mode toggle
- **Data Mode**: Switch between Demo (mock data) and Live (real API)
- **API Configuration**: 
  - Primary backend URL (Stage 1/1B)
  - ML service URL (Stage 2)
- **Integration Info**: Display expected API contracts

## Demo Mode

**Demo mode is enabled by default.** It uses comprehensive mock data covering:
- 5 thermal events across India
- All fire classifications
- Complete enrichment data (OSM context, land cover, etc.)
- ML predictions with confidence scores
- Satellite metadata
- Dynamic World land cover distributions

### Switching to Live API

1. Click **Settings** in the sidebar
2. Uncheck **"Demo Mode (Uses Mock Data)"**
3. Update **API Base URL** and **ML Service URL** if different
4. Click **Save Settings**
5. Dashboard will reload with live data

**Note**: Live API mode requires Stage 1/1B backend and Stage 2 ML service to be running.

## API Integration

### Stage 1/1B Backend Integration

The dashboard expects the following endpoints from your Stage 1/1B backend:

#### GET /api/events
Returns list of thermal events
```json
{
    "events": [
        {
            "id": "evt_001",
            "latitude": 18.5204,
            "longitude": 73.8567,
            "location": {
                "city": "Pune",
                "state": "Maharashtra",
                "country": "India"
            },
            "classification": "Industrial Fire",
            "risk_score": 87,
            "risk_level": "critical",
            "confidence": 0.91,
            "frp": 74.2,
            "persistence": "5 days",
            "industrial_context": { ... },
            "water_context": { ... },
            "land_cover": { ... },
            "satellite": {
                "available": true,
                "url": "https://...",
                "acquisition_date": "2026-08-24",
                "cloud_cover": 20
            }
        }
    ]
}
```

#### GET /api/events/{id}/enrichment
Returns enrichment data for a specific event
```json
{
    "location": { ... },
    "industrial_context": { ... },
    "water_context": { ... },
    "land_cover": { ... },
    "persistence": "string",
    "frp": 74.2
}
```

#### GET /api/statistics
Returns aggregated dashboard statistics
```json
{
    "total_detections": 32,
    "industrial_count": 14,
    "high_risk_count": 8,
    "low_risk_count": 15,
    "average_risk_score": 62
}
```

### Stage 2 ML Service Integration

The dashboard expects the ML prediction service at the URL configured in Settings:

#### POST {ML_SERVICE_URL}/predict
Send thermal event data, receive ML prediction
```json
Request:
{
    "event_id": "evt_001",
    "latitude": 18.5204,
    "longitude": 73.8567,
    "frp": 74.2,
    ...
}

Response:
{
    "predicted_class": "Industrial Fire",
    "confidence": 0.91,
    "risk_score": 87,
    "risk_level": "critical",
    "model_version": "v2.1.4-production",
    "key_factors": [
        { "factor": "High Thermal Intensity (FRP)", "value": "High (74.2)" },
        { "factor": "Industrial Facility Nearby", "value": "Yes" },
        ...
    ]
}
```

## Configuration

Settings are persisted to browser `localStorage` and survive page refreshes.

### Available Settings (in `src/config.js`)

```javascript
{
    isDemoMode: true,                                  // Boolean
    apiBaseUrl: "http://localhost:8000/api",          // String
    mlServiceUrl: "http://localhost:5000/predict",    // String
    mapDefaultCenter: [22.9734, 78.6569],             // [lat, lng]
    mapDefaultZoom: 5,                                 // Number
    theme: "light"                                     // "light" | "dark"
}
```

### Programmatic Configuration

```javascript
import { setConfig, getConfig, setConfigValue } from './src/config.js';

// Get current config
const config = getConfig();

// Update entire config
setConfig({
    isDemoMode: false,
    apiBaseUrl: "http://my-server.com/api"
});

// Update single value
setConfigValue("theme", "dark");
```

## Fire Classifications

The dashboard supports five fire classifications (as per Stage 2 ML output):

1. **Industrial Fire** - Thermal signature near industrial facilities
2. **Wildfire / Natural Fire** - Thermal signature in forest/vegetation areas
3. **Agricultural Fire** - Thermal signature in cropland regions
4. **Persistent Thermal Source** - Long-duration thermal anomalies (industrial flares, etc.)
5. **Unknown / Other** - Unclassified thermal events

## Dynamic World Land Cover

The land cover chart displays Dynamic World classes:
- **Built** - Urban/developed areas
- **Trees** - Forests
- **Grass** - Grasslands
- **Flooded vegetation** - Wetlands
- **Crops** - Agricultural areas
- **Shrub & scrub** - Shrubland
- **Water** - Water bodies
- **Bare** - Bare soil/rock
- **Snow & ice** - Snow-covered areas

## Dark Mode

Click the **Dark Mode** button in the top-right header to toggle themes. Your preference is saved and persists across sessions.

All components are optimized for readability in both light and dark modes.

## Troubleshooting

### "Failed to load events"
- **Demo mode**: Check browser console for errors
- **Live API**: Verify Stage 1/1B backend is running and accessible
- **CORS**: If using real API, ensure backend has CORS headers configured

### "No events available"
- **Demo mode**: Mock data should always load
- **Live API**: Verify API endpoint returns data (test with curl or Postman)
- **Network**: Check browser DevTools → Network tab for request failures

### "Predictions not loading"
- **Demo mode**: Predictions load from mock data
- **Live API**: Verify ML service URL is correct and service is running
- **Timeout**: If ML service is slow, increase timeout in `src/adapters/apiAdapter.js`

### ES Module loading errors
- **File:// protocol**: Use local HTTP server (Python/Node)
- **Mixed content**: If backend is HTTP but frontend is HTTPS, enable mixed content in browser
- **CORS**: Backend APIs must set `Access-Control-Allow-Origin` headers

## Performance Notes

- **Map rendering**: Optimized for up to 1000 markers on-screen simultaneously
- **Data loading**: Async/await prevents UI blocking during API calls
- **localStorage**: Configuration stored locally, no server calls for settings
- **Lazy loading**: ML predictions and satellite data loaded on-demand per event

## Known Limitations

1. **No real-time updates**: Dashboard fetches data once on load. Implement polling or WebSocket for live updates.
2. **Single backend**: Currently supports one API endpoint. Multi-region support would require routing logic.
3. **No authentication**: Demo version has no user login. Implement auth layer for production use.
4. **Fixed India view**: Map initializes centered on India. Could be configurable per deployment.
5. **No historical data**: Only displays current events. Add time-range filtering for historical analysis.
6. **No alerts/notifications**: Dashboard is read-only. Add alert system for high-risk events.

## Browser Support

- **Chrome/Edge** 90+
- **Firefox** 88+
- **Safari** 15+
- **Mobile browsers**: Responsive design works, but better on 10"+ tablets

## Security Notes

- **No secrets in frontend**: All API URLs and ML service URLs configured via Settings (never committed)
- **No database credentials**: Frontend consumes APIs only
- **CORS required**: Backend must set appropriate CORS headers
- **HTTPS recommended**: Use HTTPS in production for secure data transmission

## Development

### Adding New Services

1. Create new service in `src/services/myService.js`
2. Export async functions that check `config.isDemoMode`
3. Route to mockAdapter or apiAdapter accordingly
4. Import in `script.js` and use alongside other services

### Adding New Adapters

1. Create adapter in `src/adapters/myAdapter.js`
2. Implement same method signatures as existing adapters
3. Handle errors gracefully with fallback values
4. Register in service files

### Modifying Styles

- Light mode: Edit existing CSS rules
- Dark mode: Add `body.dark-mode` prefixed rules
- Test in both themes

## Handoff Notes

This package is **self-contained and production-ready** for Stage 3.

**For integration with Stage 1/1B and Stage 2:**
1. Update API URLs in Settings
2. Point to real backend endpoints
3. Point to real ML service endpoints
4. Disable Demo Mode
5. Test with real data

**Expected integration timeline:**
1. User completes Stage 2 ML
2. User has Stage 1/1B backend running
3. User extracts this ZIP
4. User configures API URLs in Settings
5. System test with all three stages integrated

## Support & Documentation

- **Stage 3 Specification**: See `STAGE_3_SPECIFICATION.md`
- **Implementation Details**: See `STAGE_3_CLAUDE_CODE_PROMPT.md`
- **Mock Data**: See `src/adapters/mockAdapter.js`
- **Service Architecture**: See individual files in `src/services/`

## License

Part of SIH26162 - Thermal Event Intelligence Platform

---

**Version**: 1.0  
**Last Updated**: August 2026  
**Status**: Production Ready
