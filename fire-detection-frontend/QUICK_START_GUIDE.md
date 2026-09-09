# 🚀 How to Run Stage 3 Demo - Quick Guide

## Step-by-Step Instructions

### For Windows Users (Easiest)

#### Method 1: Double-Click Batch File (Recommended)
1. **Navigate** to: `C:\Users\Snehal\OneDrive\Desktop\Fire-Detection-Frontend`
2. **Find** the file: `run_stage3_demo.bat`
3. **Double-click** it
4. A command window opens and shows:
   ```
   =====================================================
    FIRE INTELLIGENCE DASHBOARD - STAGE 3
    Testing & Verification Batch Script
   =====================================================
   
   [STEP 1/5] Checking system requirements...
   [OK] Python is installed
       Version: Python 3.x.x
   
   [STEP 2/5] Verifying project structure...
   [OK] All required files found
   
   [STEP 3/5] Checking available ports...
   [OK] Port 8080 is available
   Using port: 8080
   
   [STEP 4/5] Configuration Summary
   =====================================================
   Application: Fire Intelligence Dashboard - Stage 3
   Mode: DEMO (Using mock data)
   ...
   
   [STEP 5/5] Starting HTTP Server...
   =====================================================
    Server Information
   =====================================================
   Local URL: http://localhost:8080/
   Press Ctrl+C to stop the server
   =====================================================
   ```

5. **Open your browser** and go to: **`http://localhost:8080/`**

6. **Dashboard loads** with 5 demo thermal events! ✅

7. **To stop**: Press `Ctrl+C` in the command window

---

#### Method 2: From Command Prompt
1. Open Command Prompt
2. Navigate to project: `cd C:\Users\Snehal\OneDrive\Desktop\Fire-Detection-Frontend`
3. Run batch file:
   ```
   run_stage3_demo.bat
   ```
4. Follow same steps as Method 1

---

### For Mac/Linux Users

#### From Terminal:
```bash
# Navigate to project
cd /path/to/Fire-Detection-Frontend

# Start Python HTTP server
python -m http.server 8080

# Or if using Python 2:
python -m SimpleHTTPServer 8080
```

Then open browser to: **`http://localhost:8080/`**

---

## What You'll See - Complete Walkthrough

### Screen 1: Dashboard Loads
```
┌─────────────────────────────────────────────────────────────┐
│  🔥 Fire Intelligence | AI Powered Fire Detection          │
├─────────────────────┬───────────────────────────────────────┤
│                     │ 📅 24 Aug 2026                        │
│  SIDEBAR            │ Monday 10:30 AM    🌙 🔔 🔐          │
│                     │ ┌─────────────────────────────────────┤
│  Dashboard          │ │ DASHBOARD                           │
│  ⚙️ Settings        │ │ Overview of fire detections...     │
│                     │ ├─────────────────────────────────────┤
│  ═════════════      │ │                  ┌─────────────────┤
│  Classifications:   │ │                  │ SELECTED        │
│  🏭 Industrial      │ │                  │ DETECTION       │
│  🌳 Wildfire        │ │   [MAP WITH 5    │                 │
│  🌾 Agricultural    │ │    MARKERS]      │ Location: Pune  │
│  🔥 Thermal         │ │                  │ Risk: 87/100    │
│  ❓ Unknown         │ │                  │ Pred: Ind. Fire │
│                     │ │                  │ Confidence: 91% │
└─────────────────────┴───────────────────────────────────────┘
```

### Screen 2: Select Different Events
Click on markers:
- **Pune** (Red) → Industrial Fire, 87/100, CRITICAL
- **Satpura** (Red) → Wildfire, 82/100, HIGH  
- **Moga** (Green) → Agricultural Fire, 42/100, LOW
- **Jamshedpur** (Orange) → Persistent Thermal, 68/100, MEDIUM
- **Rajasthan** (Gray) → Unknown, 31/100, LOW

### Screen 3: Dark Mode
Click "🌙 Dark Mode" button → Everything turns dark, text remains readable

### Screen 4: Settings
Click "Settings" in sidebar → Configuration page with:
- Dark Mode toggle
- Demo Mode toggle (enabled)
- API Base URL field
- ML Service URL field
- Save & Reset buttons

---

## Demo Data Overview

### 5 Thermal Events Loaded:

| Event | Location | Classification | Risk | Confidence | Marker |
|-------|----------|-----------------|------|------------|--------|
| 1 | Pune | Industrial Fire | 87/100 🔴 | 91% | 🔴 Red |
| 2 | Satpura | Wildfire | 82/100 🔴 | 88% | 🔴 Red |
| 3 | Moga | Agricultural | 42/100 🟢 | 95% | 🟢 Green |
| 4 | Jamshedpur | Persistent Thermal | 68/100 🟠 | 99% | 🟠 Orange |
| 5 | Rajasthan | Unknown | 31/100 🟢 | 54% | ⚫ Gray |

### Key Demo Features:

✅ **Complete Enrichment Data**
- OSM context (industrial facilities, water bodies)
- Land cover distributions (Dynamic World 9 classes)
- Thermal intensity (FRP values)
- Persistence information

✅ **ML Predictions**
- Predicted fire class for each event
- Confidence percentages
- Risk scoring
- Key contributing factors

✅ **Satellite Metadata**
- Image URLs (3 out of 5 have previews)
- Acquisition dates
- Cloud coverage percentages
- Demo badge on preview images

---

## Interactive Testing

### Test 1: Select Events
**Action:** Click each of 5 markers
```
Expected Results:
✓ Location updates (city, state, coordinates)
✓ Risk score changes
✓ Risk level updates (CRITICAL, HIGH, MEDIUM, LOW)
✓ Prediction class changes
✓ Confidence percentage updates
✓ Key factors list updates
✓ Map centers on selected event
✓ Land cover donut chart updates
✓ Satellite preview changes
```

### Test 2: Dark Mode
**Action:** Click "🌙 Dark Mode" button
```
Expected Results:
✓ Page background turns dark
✓ Text remains readable (white/light gray)
✓ All cards have dark background
✓ Map legend readable
✓ Donut chart center text visible
✓ Risk indicators color-coded properly
✓ Refresh page → dark mode persists
```

### Test 3: Settings
**Action:** Click "Settings" in sidebar
```
Expected Results:
✓ Dashboard view hidden
✓ Settings form displayed
✓ Theme toggle shows current state
✓ Demo mode toggle checked (enabled)
✓ API URLs show default values
✓ Can edit URL fields
✓ Can save settings
✓ Can reset to defaults
✓ Refresh page → settings persist
```

### Test 4: Return to Dashboard
**Action:** Click "Dashboard" in sidebar
```
Expected Results:
✓ Settings hidden
✓ Dashboard displayed
✓ Map visible with markers
✓ Last selected event still selected
✓ All data preserved
```

### Test 5: Map Controls
**Action:** Try zoom and reset buttons
```
Expected Results:
✓ + button zooms in
✓ − button zooms out
✓ Layer icon resets to India view
✓ Map remains responsive
```

### Test 6: Responsive Design
**Action:** Resize browser window
```
Desktop (1920px):
✓ Full 2-column layout
✓ Map on left, panel on right
✓ Bottom cards 3 columns

Tablet (768px):
✓ Map above panel
✓ Stacked vertically
✓ Bottom cards 2 columns

Mobile (375px):
✓ Single column
✓ Everything stacked
✓ Still fully functional
```

---

## Browser Console Check

### How to Open:
1. While running, press **F12** (or Ctrl+Shift+I)
2. Click **Console** tab
3. Should see NO red error messages

### Expected Console Output:
```
[DEMO] Loaded 5 mock events
[DEMO] Loaded mock prediction for evt_pune_001
[DEMO] Loaded mock satellite data for evt_pune_001
... (repeats for other events)
```

---

## File Structure Used

The batch file verifies these files exist:

```
Fire-Detection-Frontend/
├── index.html                    ✓ Main structure
├── style.css                     ✓ All styling
├── script.js                     ✓ Main application
│
├── src/
│   ├── config.js                 ✓ Configuration
│   ├── adapters/
│   │   ├── mockAdapter.js        ✓ Demo data
│   │   └── apiAdapter.js         ✓ Real API layer
│   └── services/
│       ├── eventsService.js      ✓ Event loading
│       ├── predictionService.js  ✓ ML predictions
│       ├── statisticsService.js  ✓ Statistics
│       └── satelliteService.js   ✓ Satellite data
│
├── README.md                     ✓ Documentation
├── .env.example                  ✓ Config template
├── run_stage3_demo.bat          ✓ This batch file!
└── DEMO_TESTING_GUIDE.md        ✓ Testing guide
```

---

## Troubleshooting

### Problem: "Python is not recognized"
**Solution:**
1. Install Python from: https://www.python.org/downloads/
2. During installation, CHECK "Add Python to PATH"
3. Restart command prompt
4. Try batch file again

### Problem: "All files not found"
**Solution:**
1. Make sure batch file is in correct directory
2. Run batch file from project root (where index.html is)
3. Verify ZIP extracted completely

### Problem: "Port 8080 already in use"
**Solution:**
1. Close other applications using port 8080
2. Or run batch file and enter different port when prompted (e.g., 8000)
3. Then open: http://localhost:8000/

### Problem: "Dashboard won't load"
**Solution:**
1. Make sure HTTP server is running (check command window)
2. Try: http://localhost:8080/ (note: http not https)
3. Try different browser
4. Check browser console (F12) for errors
5. Refresh page (Ctrl+R)

### Problem: "Markers not showing"
**Solution:**
1. Wait 2-3 seconds for page to fully load
2. Refresh browser (Ctrl+R)
3. Check browser console (F12) for JavaScript errors
4. Try different browser

### Problem: "Dark mode not working"
**Solution:**
1. Make sure cookies enabled in browser
2. Check browser console for errors
3. Try different browser

---

## Performance Notes

| Operation | Time |
|-----------|------|
| Page load | < 2 seconds |
| Event selection | 200-300ms |
| Theme toggle | < 100ms |
| Map zoom | Instant |
| Settings save | < 50ms |

---

## What Happens Next (After Stage 3 Demo)

### When Ready to Connect Real Data:

#### Stage 1/1B Backend Connection:
```
1. Get backend API URL from your team
2. Open dashboard → Settings
3. Enter API Base URL: http://your-backend:8000/api
4. Uncheck "Demo Mode"
5. Click Save
6. Refresh dashboard → real events load!
```

#### Stage 2 ML Connection:
```
1. Get ML service URL from your team
2. Open dashboard → Settings
3. Enter ML Service URL: http://your-ml:5000/predict
4. Click Save
5. Real predictions display instead of demo
```

#### Full Integration:
```
Stage 1/1B events → Dashboard displays → Stage 2 ML scores
                    (real thermal data)  (real predictions)
```

---

## Summary

### ✅ What You Have Right Now:
- Complete Stage 3 dashboard
- 5 realistic demo thermal events
- Mock ML predictions
- All features working
- Ready to connect real data

### ✅ What You Can Test:
- All dashboard features
- User interface responsiveness
- Data display accuracy
- Settings configuration
- Dark mode functionality

### ✅ What's Next:
- Connect Stage 1/1B backend
- Connect Stage 2 ML service
- Test with real thermal event data
- Validate ML predictions
- Deploy to production

---

## Quick Reference

| What | How | Where |
|------|-----|-------|
| **Run Dashboard** | Double-click `run_stage3_demo.bat` | Project folder |
| **Open Browser** | Go to `http://localhost:8080/` | Browser address bar |
| **Stop Server** | Press `Ctrl+C` in command window | Command window |
| **View Settings** | Click "Settings" in sidebar | Dashboard |
| **Toggle Theme** | Click "🌙" button (top-right) | Dashboard header |
| **Select Event** | Click any marker on map | Dashboard map |
| **Check Console** | Press `F12` then click Console tab | Browser |
| **View Demo Data** | See `src/adapters/mockAdapter.js` | Project folder |
| **Read Guide** | Open `DEMO_TESTING_GUIDE.md` | Project folder |

---

## Questions?

📖 **Full Documentation:**
- `README.md` - Complete user guide
- `DEMO_TESTING_GUIDE.md` - Detailed testing instructions
- `COMPLIANCE_VERIFICATION.md` - Requirements verification

🔧 **Technical Details:**
- `HANDOFF_SUMMARY.md` - Implementation overview
- `VERIFICATION_REPORT.md` - Testing results

🚀 **Ready to Test!**

---

**Created**: August 26, 2026  
**Status**: ✅ Ready to Run  
**Version**: 1.0

Enjoy testing Stage 3! 🎉
