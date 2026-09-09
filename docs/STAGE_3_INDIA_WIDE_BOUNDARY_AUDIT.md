# STAGE 3 — INDIA-WIDE BOUNDARY AUDIT REPORT

## Executive Summary
This audit examines the SIH26162 Thermal Event Intelligence Platform to convert from Pune-specific geographic restrictions to India-wide operational boundaries while preserving Pune as an optional test/development/user-filter location.

**Status: NEEDS ACTION** 🟡

The platform contains India-wide boundary infrastructure (INDIA_BBOX) but currently defaults to Pune-specific boundaries for production operations. Changes required to make India-wide the production default while maintaining test flexibility.

## Findings Summary

### 🔴 Production Restrictions (Require India-wide Change)
These references restrict production operations to Pune/Maharashtra and must be changed to India-wide defaults:

1. **Environment Variables (.env)**
   - `PILOT_BBOX=17.35,73.50,19.00,75.50` (line 2)
   - `PILOT_NAME=pune_maharashtra` (line 3)
   - `FIRMS_BBOX=17.35,73.50,19.00,75.50` (line 4 in .env.example, but actual .env may have it)

2. **Backend Configuration (backend/config.py)**
   - Line 64: `FIRMS_BBOX: str = os.getenv("FIRMS_BBOX", "17.35,73.50,19.00,75.50")`
   - Line 100: `PILOT_BBOX: str = os.getenv("PILOT_BBOX", "17.35,73.50,19.00,75.50")`
   - Line 101: `PILOT_NAME: str = os.getenv("PILOT_NAME", "pune_maharashtra")`

3. **Demo Data Generation (backend/demo_data.py)**
   - Lines 57-58: Uses `config.pilot_bbox_tuple` for mock event generation
   - Lines 64-69: Hardcoded Pune industrial hotspots

### 🟡 Demo/Test/Documentation (Can Remain as-is)
These references can remain as they serve educational/demo purposes:

1. **README.md**
   - Pilot region documentation and examples
   - Serves as user guidance for optional Pune filtering

2. **Frontend Files (fire-detection-frontend/)**
   - Mock data examples, testing guides, verification reports
   - Represent optional user-filter capabilities and demo scenarios
   - Files like DEMO_TESTING_GUIDE.md, EXPECTED_OUTPUT_GUIDE.txt, etc.

3. **Test Files (Selective)**
   - Tests that validate specific functionality using Pune as a known test case
   - Should be complemented with India-wide tests but can remain for regression

### 🟢 Already India-Wide (No Change Needed)
These components already support India-wide operations:

1. **Infrastructure in backend/config.py**
   - `INDIA_BBOX: str = os.getenv("INDIA_BBOX", "8.0,68.0,35.0,97.0")` (line 102)
   - `india_bbox_tuple` property (lines 115-124)

2. **Stage 3.2 Dynamic World Integration**
   - Verified working across multiple Indian locations (test_india_wide.py)
   - Live Dynamic World data successfully retrieved for Kashmir, Delhi, Mumbai, Pune, etc.

3. **FIRMS Collector**
   - Capable of India-wide ingestion when configured with India-wide bbox

## Required Changes

### 1. Environment Variables (.env)
**Change from:**
```
PILOT_BBOX=17.35,73.50,19.00,75.50
PILOT_NAME=pune_maharashtra
FIRMS_BBOX=17.35,73.50,19.00,75.50  # if present
```

**Change to:**
```
# For production: India-wide operational boundary
PILOT_BBOX=8.0,68.0,35.0,97.0
PILOT_NAME=india
FIRMS_BBOX=8.0,68.0,35.0,97.0

# For Pune-specific testing (optional override):
# PILOT_BBOX=17.35,73.50,19.00,75.50
# PILOT_NAME=pune_maharashtra
```

### 2. Backend Configuration (backend/config.py)
**Change from:**
```python
FIRMS_BBOX: str = os.getenv("FIRMS_BBOX", "17.35,73.50,19.00,75.50")
PILOT_BBOX: str = os.getenv("PILOT_BBOX", "17.35,73.50,19.00,75.50")
PILOT_NAME: str = os.getenv("PILOT_NAME", "pune_maharashtra")
```

**Change to:**
```python
FIRMS_BBOX: str = os.getenv("FIRMS_BBOX", "8.0,68.0,35.0,97.0")
PILOT_BBOX: str = os.getenv("PILOT_BBOX", "8.0,68.0,35.0,97.0")
PILOT_NAME: str = os.getenv("PILOT_NAME", "india")
```

### 3. Demo Data Generation (backend/demo_data.py)
**Change from:**
```python
# Pune region coordinates
min_lat, min_lon, max_lat, max_lon = config.pilot_bbox_tuple

# Industrial hotspots in Pune (mock locations)
hotspots = [
    {"name": "Pimpri Industrial Area", "lat": 18.6298, "lon": 73.8007},
    {"name": "Chinchwad Industrial Area", "lat": 18.6359, "lon": 73.7997},
    {"name": "Talegaon MIDC", "lat": 18.7830, "lon": 73.4637},
    {"name": "Marunji Area", "lat": 18.6642, "lon": 73.6667},
]
```

**Change to:**
```python
# India-wide region coordinates
min_lat, min_lon, max_lat, max_lon = config.india_bbox_tuple

# Industrial hotspots across India (mock locations)
hotspots = [
    {"name": "Pimpri Industrial Area, Pune", "lat": 18.6298, "lon": 73.8007},
    {"name": "Vadodara Industrial Zone, Gujarat", "lat": 22.3072, "lon": 73.1812},
    {"name": "Gurgaon Industrial Area, Haryana", "lat": 28.4595, "lon": 77.0266},
    {"name": "Coimbatore Industrial Zone, Tamil Nadu", "lat": 11.0168, "lon": 76.9558},
    {"name": "Howrah Industrial Belt, West Bengal", "lat": 22.5964, "lon": 88.2631},
]
```

### 4. Selective Test File Updates
**Update test_ee_final.py (line 41-43):**
```python
# Test locations across India (using the INDIA_BBOX)
test_locations = [
    {"name": "Kashmir (North)", "lat": 34.0, "lon": 74.5},
    {"name": "Delhi (North Central)", "lat": 28.6, "lon": 77.2},
    {"name": "Rajasthan (West)", "lat": 26.9, "lon": 75.8},
    {"name": "Gujarat (West)", "lat": 22.3, "lon": 71.0},
    {"name": "Mumbai (West Coast)", "lat": 19.0, "lon": 72.8},
    {"name": "Pune (Central)", "lat": 18.5, "lon": 73.8},
    {"name": "Hyderabad (South Central)", "lat": 17.4, "lon": 78.5},
    {"name": "Karnataka (South)", "lat": 15.3, "lon": 75.7},
    {"name": "Tamil Nadu (South)", "lat": 13.0, "lon": 80.2},
    {"name": "Kerala (South West)", "lat": 10.0, "lon": 76.3},
    {"name": "West Bengal (East)", "lat": 22.5, "lon": 88.4},
    {"name": "Assam (North East)", "lat": 26.2, "lon": 91.5},
]
```

## Impact Assessment

### ✅ Benefits of Changes
1. **Production Ready**: FIRMS ingestion, OSM enrichment, Dynamic World queries will operate across India by default
2. **Backward Compatible**: Pune-specific testing still available via environment variable overrides
3. **Demo Flexibility**: Demo data generation now represents national industrial hotspots
4. **Infrastructure Reuse**: Leverages existing INDIA_BBOX and india_bbox_tuple properties

### 🔧 Implementation Effort
- **Low**: Changes confined to configuration files and demo data generator
- **No Core Logic Changes**: Existing GIS providers, enrichment engine, and ML pipeline already support India-wide operations
- **Test Coverage**: Existing test_india_wide.py validates India-wide functionality

## Verification Steps

After implementing changes:

1. **Backend Startup Verification**
   ```bash
   # Should show India-wide bounds in logs
   python -c "from backend.config import Config; c=Config(); print(c.pilot_bbox_tuple)"
   # Expected: (8.0, 68.0, 35.0, 97.0)
   ```

2. **FIRMS Ingestion Test**
   - Verify FIRMS collector pulls events from across India (not just Pune region)

3. **Dynamic World Validation**
   - Run test_india_wide.py to confirm live data retrieval across multiple Indian states

4. **Demo Data Check**
   - Verify generated demo events span India-wide locations

5. **Frontend Functionality**
   - Confirm map defaults to India-wide view with optional Pune filtering

## Conclusion
The SIH26162 platform has the foundational infrastructure for India-wide operations (INDIA_BBOX, Dynamic World validation across India). The primary barrier is production-default configuration pointing to Pune-specific boundaries.

By updating the default values in .env, config.py, and demo_data.py to use India-wide boundaries while preserving Pune-specific overrides for testing/demo, we achieve:
- **Production**: India-wide operational scope
- **Development**: Continued Pune-specific testing capability
- **Demonstration**: National-scale demo data representing diverse Indian industrial zones
- **Compliance**: Meets requirement of "Entire India as production scope, Pune only as optional test/development location"

**Recommended Action**: Implement the configuration changes outlined above and run verification tests.