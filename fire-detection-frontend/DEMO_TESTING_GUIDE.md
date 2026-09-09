# Stage 3 Demo Testing Guide

**Fire Intelligence Dashboard - Stage 3**  
**Testing with Demo Data**

---

## Quick Start (30 seconds)

### Windows Users:
1. **Double-click** `run_stage3_demo.bat` in the project folder
2. Wait for the message "Local URL: http://localhost:8080/"
3. **Open browser** and go to: `http://localhost:8080/`
4. Dashboard loads with 5 demo thermal events

### Mac/Linux Users:
```bash
# Navigate to project directory
cd Fire-Detection-Frontend

# Start local HTTP server
python -m http.server 8080

# Open browser to:
# http://localhost:8080/
```

---

## What You'll See (Demo Mode)

### Initial Dashboard View
✅ **Fire Intelligence Branding** (Top-left)
- Logo with fire icon
- "Fire Intelligence" title
- "AI Powered Fire Detection" subtitle

✅ **Left Sidebar** (Full height)
- Navigation: Dashboard (active) | Settings
- Fire Classification section with all 5 types
  - Industrial Fire (red icon)
  - Wildfire / Natural Fire (green icon)
  - Agricultural Fire (yellow icon)
  - Persistent Thermal Source (orange icon)
  - Unknown / Other (gray icon)

✅ **Top Header** (Right side)
- Live date and time (updates every second)
- Dark Mode toggle button
- Notification bell icon (5 notifications)
- Login button

✅ **Orange Demo Banner** (Top of page)
- "🎯 DEMO MODE - Using mock data for demonstration"
- Clearly indicates this is not live data

---

## Map View (Center)

✅ **Interactive Map**
- Centered on India
- 5 thermal event markers visible:
  1. **Pune, Maharashtra** - Red marker (High Risk, Industrial Fire)
  2. **Satpura Forest** - Red marker (High Risk, Wildfire)
  3. **Moga, Punjab** - Green marker (Low Risk, Agricultural Fire)
  4. **Jamshedpur, Jharkhand** - Orange marker (Medium Risk, Persistent Thermal)
  5. **Thar Basin, Rajasthan** - Gray marker (Low Risk, Unknown)

✅ **Map Controls** (Top-right)
- **+** button (Zoom in)
- **−** button (Zoom out)
- **Layer icon** button (Reset to India view)

✅ **Risk Legend** (Bottom-left)
- High (Red dot)
- Medium (Orange dot)
- Low (Green dot)
- Cluster (Blue dot)

---

## Selected Detection Panel (Right Side)

When you **click any marker**, the right panel updates:

✅ **Location Section**
- City, State, Country
- Latitude and Longitude (coordinates)
- Example: "Pune, Maharashtra, India | 18.5204, 73.8567"

✅ **Risk Score Section**
- Numeric score: **87 / 100**
- Risk level label: **CRITICAL** (color-coded)
- Fire circle indicator (background color changes by risk)

✅ **Prediction Section** (ML Results)
- Predicted fire class: **Industrial Fire**
- Confidence: **91%** (color-coded: green=high confidence)

✅ **Key Factors Section** (Contributing factors)
- High Thermal Intensity (FRP): High (74.2)
- Industrial Facility Nearby: Yes (MIDC Hub)
- Land Cover: Built-up (87%)
- Population Density: High
- Persistent Anomaly: Yes (5 days)

Each factor has an icon:
- 🌡️ Temperature = Thermal Intensity
- 🏭 Factory = Industrial Facility
- 🗺️ Map = Land Cover
- 👥 People = Population Density
- 🛡️ Shield = Persistent Anomaly

---

## Bottom Panels

### Quick Summary (Left Bottom)
Four information cards:
1. **Total Detections** - 5 High Risk ↑ 22%
2. **Industrial Areas** - 2 Across India ↑ 2%
3. **Weather Risk** - 2 High ↑ 20%
4. **Low Risk** - 2 Safe Areas

### Land Cover Chart (Middle Bottom)
✅ **Dynamic World Donut Chart**
- Donut visualization with conic-gradient
- Center label: **87% Built** (largest category)
- Ring shows all 9 land cover classes with colors

✅ **Land Cover List** (Below chart)
- Built: 87%
- Trees: 4%
- Grass: 3%
- Crops: 3%
- Bare: 2%
- Water: 1%
- Others: 1%

### Satellite Preview (Right Bottom)
✅ **Satellite Image Card**
- Title: "Satellite Image (Sentinel-2)"
- Image preview area (gradient background in demo)
- **DEMO** badge (orange label) indicates mock data
- Metadata footer:
  - Date: 24 Aug 2026
  - Cloud: 20%

---

## Testing Interactions

### 1. Select Different Events
**Action:** Click different markers on the map
**Expected Results:**
- Location updates ✓
- Risk score changes ✓
- Prediction updates ✓
- Key factors update ✓
- Satellite metadata changes ✓
- Land cover chart updates ✓
- Map centers on selected event ✓

**Test All 5:**
- Pune (Industrial Fire, 87/100, CRITICAL)
- Satpura (Wildfire, 82/100, HIGH)
- Moga (Agricultural Fire, 42/100, LOW)
- Jamshedpur (Persistent Thermal, 68/100, MEDIUM)
- Rajasthan (Unknown, 31/100, LOW)

### 2. Dark Mode
**Action:** Click "Dark Mode" button (top-right)
**Expected Results:**
- Background turns dark ✓
- All text remains readable ✓
- Colors update for dark theme ✓
- Donut chart center is visible ✓
- Map legend readable ✓
- Cards have dark background ✓
- Toggle shows "Light Mode" when dark is active ✓

**Test:** Toggle multiple times, refresh page → theme persists

### 3. Settings Page
**Action:** Click "Settings" in sidebar
**Expected Results:**
- Dashboard view hidden ✓
- Settings view displayed ✓
- Settings title and description visible ✓

**Settings Form Contains:**
- Dark Mode toggle (checkbox)
- Demo Mode toggle (checked by default)
- API Base URL input field (http://localhost:8000/api)
- ML Service URL input field (http://localhost:5000/predict)
- Save Settings button
- Reset to Defaults button
- Integration Information section

**Test Interactions:**
- Uncheck "Demo Mode" → checkbox updates ✓
- Edit API Base URL → changes text ✓
- Click Save Settings → confirmation message ✓
- Click Reset to Defaults → form resets ✓
- Refresh page → settings persist ✓

### 4. Return to Dashboard
**Action:** Click "Dashboard" in sidebar
**Expected Results:**
- Settings view hidden ✓
- Dashboard view displayed ✓
- Map visible with markers ✓
- Last selected event still selected ✓

### 5. Map Controls
**Action:** Click zoom buttons
**Expected Results:**
- **+** button → map zooms in ✓
- **−** button → map zooms out ✓
- **Layer button** → resets to India view ✓

### 6. Responsive Design
**Action:** Resize browser window
**Expected Results:**
- **Wide (1920px):** Full 2-column layout (map + panel side-by-side)
- **Medium (1366px):** Bottom cards show 2 columns
- **Tablet (768px):** Map and panel stack vertically
- **Mobile (375px):** Single column, everything stacks
- Map remains functional at all sizes ✓
- All text remains readable ✓

---

## Demo Data Breakdown

### Event 1: Pune (Industrial Fire)
```
Location: Pune, Maharashtra, India
Coordinates: 18.5204, 73.8567
Classification: Industrial Fire
Risk Score: 87/100
Risk Level: CRITICAL
Confidence: 91%
FRP: 74.2
Persistence: Repeated anomaly over 5 days
Industrial Context: MIDC Industrial Hub (120m)
Water Proximity: Mutex Canal (920m)
Land Cover: Built (87%), Trees (4%), Grass (3%), Crops (3%), Bare (2%), Water (1%)
Satellite: Available | Date: 2026-08-24 | Cloud: 20%
```

### Event 2: Satpura (Wildfire)
```
Location: Satpura Forest Range, Madhya Pradesh
Coordinates: 22.4646, 78.1122
Classification: Wildfire / Natural Fire
Risk Score: 82/100
Risk Level: HIGH
Confidence: 88%
FRP: 142.5 (CRITICAL thermal intensity)
Persistence: New thermal manifestation
Industrial Context: None detected within 5km
Water Proximity: Denwa River (1.2km)
Land Cover: Trees (78%), Shrub & scrub (12%), Grass (6%), Crops (2%), Water (1%), Built (1%)
Satellite: Available | Date: 2026-08-25 | Cloud: 5%
```

### Event 3: Moga (Agricultural Fire)
```
Location: Moga Region, Punjab
Coordinates: 31.1471, 75.3412
Classification: Agricultural Fire
Risk Score: 42/100
Risk Level: LOW
Confidence: 95%
FRP: 35.1 (Low thermal intensity)
Persistence: Short-lived seasonal activity
Industrial Context: Farm co-op building (480m)
Water Proximity: Irrigation canal (150m)
Land Cover: Crops (84%), Bare (10%), Built (4%), Trees (2%)
Satellite: NOT Available (no image for this location)
```

### Event 4: Jamshedpur (Persistent Thermal)
```
Location: Jamshedpur, Jharkhand
Coordinates: 22.8046, 86.2029
Classification: Persistent Thermal Source
Risk Score: 68/100
Risk Level: MEDIUM
Confidence: 99%
FRP: 92.0 (STABLE thermal intensity)
Persistence: Continuous signal over 365 days
Industrial Context: Steel Processing Station (40m)
Water Proximity: Subarnarekha River (2.1km)
Land Cover: Built (92%), Bare (4%), Water (2%), Trees (2%)
Satellite: Available | Date: 2026-08-22 | Cloud: 45%
```

### Event 5: Rajasthan (Unknown/Other)
```
Location: Thar Basin, Rajasthan
Coordinates: 26.2389, 70.9624
Classification: Unknown / Other
Risk Score: 31/100
Risk Level: LOW
Confidence: 54% (LOW confidence - model uncertain)
FRP: 18.4 (Very low thermal intensity)
Persistence: Irregular anomaly
Industrial Context: None within 20km
Water Proximity: None (Arid desert region)
Land Cover: Bare (90%), Shrub & scrub (8%), Built (1%), Grass (1%)
Satellite: NOT Available
```

---

## What's NOT in Demo (For Later Integration)

### ❌ Not Connected (Will add later)
- **Stage 1/1B Backend**: Real event data from PostgreSQL/PostGIS
- **Stage 2 ML Service**: Real ML predictions from trained model
- **Real Satellite Images**: Actual Sentinel-2 imagery
- **Live Weather Data**: Real weather risk assessments
- **Historical Data**: Time-series thermal event history

### ✅ Infrastructure Ready (Just needs connection)
- API adapter layer (ready for endpoints)
- ML prediction service interface (ready for model)
- Satellite data service (ready for real URLs)
- Error handling for missing/slow services
- Fallback to demo data if backend unavailable

---

## Browser Console

### Expected Console Output (Demo Mode):
```
[DEMO] Loaded 5 mock events
[DEMO] Loaded mock prediction for evt_pune_001
[DEMO] Loaded mock satellite data for evt_pune_001
```

### Check for Errors:
- Open browser → Press **F12** (Developer Tools)
- Click **Console** tab
- Should see NO red error messages
- Demo log messages show data is loading

---

## Performance Expectations

| Action | Expected Time |
|--------|---|
| Initial page load | < 2 seconds |
| Click marker (select event) | 200-300ms |
| Theme toggle | < 100ms |
| Settings save | < 50ms |
| Map zoom | Instant |
| Responsive resize | Instant |

---

## Testing Checklist

Use this to verify everything works:

### Dashboard
- [ ] Dashboard loads without errors
- [ ] 5 markers visible on map
- [ ] Markers are color-coded (red/orange/green/gray)
- [ ] DEMO banner visible at top
- [ ] Dark mode can be toggled
- [ ] All panels visible and properly styled

### Interactions
- [ ] Click marker → panel updates
- [ ] All 5 events can be selected
- [ ] Risk level changes with each event
- [ ] Predictions display correctly
- [ ] Confidence percentages show
- [ ] Key factors update dynamically
- [ ] Land cover chart updates with percentages
- [ ] Satellite preview shows/hides correctly

### Settings
- [ ] Settings accessible from sidebar
- [ ] Theme toggle works
- [ ] Demo mode toggle present
- [ ] API URL fields editable
- [ ] Save button works
- [ ] Reset button works
- [ ] Settings persist on page refresh

### Dark Mode
- [ ] Toggle button changes appearance
- [ ] All text readable in dark mode
- [ ] Map legend visible in dark mode
- [ ] Cards have dark background
- [ ] Donut chart center text visible
- [ ] Theme persists on page refresh

### Responsive
- [ ] Desktop (1920px) - full layout
- [ ] Laptop (1366px) - bottom cards 2-column
- [ ] Tablet (768px) - stacked vertically
- [ ] Mobile (375px) - single column
- [ ] Map usable at all sizes
- [ ] No horizontal scroll needed

### Browser Console
- [ ] No red error messages
- [ ] Demo log messages appear
- [ ] No warnings about missing files

---

## Troubleshooting

### Issue: "Python is not recognized"
**Solution:**
- Install Python from https://www.python.org/downloads/
- Make sure to check "Add Python to PATH"
- Restart command prompt after installation

### Issue: "Port 8080 already in use"
**Solution:**
- Run batch file again, enter different port (e.g., 8000)
- Or stop other applications using port 8080

### Issue: "Files not found"
**Solution:**
- Run batch file from project root directory
- Make sure all files are extracted from ZIP

### Issue: "Markers not showing on map"
**Solution:**
- Refresh browser (Ctrl+R or Cmd+R)
- Check browser console for errors (F12)
- Make sure JavaScript is enabled

### Issue: "Settings don't save"
**Solution:**
- Check if cookies/storage enabled in browser
- Try in different browser
- Check browser console for errors

---

## Next Steps (For Stage Integration)

### When Stage 1/1B Backend Ready:
1. Get backend API URL
2. Go to Settings → enter API Base URL
3. Uncheck "Demo Mode"
4. Refresh dashboard → real events load

### When Stage 2 ML Service Ready:
1. Get ML service URL
2. Go to Settings → enter ML Service URL
3. Real predictions will display instead of mock

### Full System Test:
1. Stage 1/1B delivering events ✓
2. Stage 2 ML providing predictions ✓
3. Stage 3 dashboard displaying all ✓
4. User can analyze results ✓

---

## Questions?

### Dashboard Features
- See README.md for complete documentation
- See COMPLIANCE_VERIFICATION.md for requirements verification

### Integration Guides
- See README.md section "API Integration"
- See HANDOFF_SUMMARY.md for architecture overview

### Demo Data
- See src/adapters/mockAdapter.js for complete dataset

---

**Version**: 1.0  
**Date**: August 26, 2026  
**Status**: Ready for Testing

Happy testing! 🚀
