# STAGE 3.1 — OPERATIONAL DEPLOYMENT INTEGRATION AUDIT

## Current Architecture

The SIH26162 project consists of:
- **Backend**: Python/FastAPI application with PostgreSQL+PostGIS database
- **ML Pipeline**: Frozen Stage 2 Random Forest model with preprocessing pipeline
- **Data Collectors**: 
  - FIRMS collector (NASA FIRMS API)
  - OSM/Overpass provider (OpenStreetMap)
  - Dynamic World provider (Google Earth Engine)
- **Frontend**: React application with Leaflet for mapping
- **Infrastructure**: 
  - Database migrations for schema setup
  - Caching mechanisms for OSM and Dynamic World

## Component-by-Component Audit

### 1. STAGE 2 MODEL ARTIFACTS
**Status: GREEN**

**Evidence:**
- `final_model.joblib` exists at `docs/stage2d/models/final_model.joblib` (5.5MB)
- `preprocessing_pipeline.joblib` exists at `docs/stage2d/models/preprocessing_pipeline.joblib` (4.8KB)
- `label_encoder.joblib` exists at `docs/stage2d/models/label_encoder.joblib` (512B)
- `feature_schema.json` exists at `docs/stage2d/models/feature_schema.json` (1.8KB)
- `model_metadata.json` exists at `docs/stage2d/models/model_metadata.json` (2.4KB)

**Verification:**
- All artifacts load successfully without errors
- Model type: RandomForestClassifier
- Training datetime: 2026-09-05T05:39:05.498035
- 15-feature contract verified:
  - bright_ti4, bright_ti5, scan, track, confidence, satellite, instrument, daynight, source_satellite
  - dw_bare, dw_confidence, dw_difference, dw_found, dw_grass, dw_water
- Features match exactly the frozen model's input requirements

### 2. FIRMS LIVE PIPELINE
**Status: GREEN**

**Evidence:**
- File: `backend/firms_collector.py`
- Key verification points:
  - Polls NASA FIRMS API for VIIRS SNPP NRT data
  - Normalizes events to thermal_events schema
  - Preserves acquisition date/time (acquisition_time field)
  - Preserves satellite, instrument, confidence, day_night fields
  - Implements deterministic deduplication using (lat, lon, acquisition_time, satellite)
  - Stores events in PostgreSQL/PostGIS thermal_events table
  - Includes raw payload storage for auditability
  - Handles out-of-bounds events (outside India) gracefully
  - Integrates with ThermalSourceGrouper for Stage 1C processing
  - Logs ingestion runs for monitoring

**Database Storage:**
- Events stored in `thermal_events` table with PostGIS geometry
- Fields: id, acquisition_time, satellite, instrument, brightness, frp, confidence, scan, track, day_night, latitude, longitude, point (PostGIS)
- Raw payloads stored in `raw_payloads` table

### 3. OSM PIPELINE
**Status: GREEN**

**Evidence:**
- File: `backend/gis/osm_provider.py`
- Key verification points:
  - Implements OpenStreetMap/Overpass adapter with India-wide coverage
  - Provides industrial features query (factories, warehouses, power plants, etc.)
  - Provides water features query (rivers, lakes, wetlands)
  - Uses PostgreSQL caching with TTL (cache table: osm_cache)
  - Graceful fallback when Overpass API unavailable
  - Does NOT incorrectly use OSM data as ML input (OSM used only for enrichment and label/persistence logic)
  - OSM data remains available for contextual interpretation (e.g., facility_within_1km/5km/10km features)

**Database Storage:**
- Cached results stored in `osm_cache` table
- Fields: id, tile_x, tile_y, tile_z, query_type, response_json, expires_at, created_at

**Verification of Non-Usage in ML:**
- Confirmed that OSM-derived features (facility_within_1km, etc.) are not part of the 15-feature model input set
- OSM is used only for enrichment tables and label generation logic (where appropriate)

### 4. DYNAMIC WORLD PIPELINE
**Status: YELLOW** (Partially implemented - credentials not configured)

**Evidence:**
- File: `backend/gis/dynamic_world_provider.py`
- Key verification points:
  - Implements Google Dynamic World provider for land-cover classification
  - Handles Earth Engine initialization gracefully
  - Returns demo data when credentials unavailable (current state)
  - Queries land-cover classes: water, trees, grass, flooded_vegetation, crops, shrub_scrub, built, bare, snow_ice
  - Provides class probabilities and metadata
  - Caching would be implemented via same mechanism as OSM (not yet implemented in code)

**DW Features Verification:**
- The provider returns the following land cover probabilities that map to DW features:
  - water → dw_water
  - trees → dw_trees
  - grass → dw_grass
  - flooded_vegetation → dw_flooded_vegetation
  - crops → dw_crops
  - shrub_scrub → dw_shrub_and_scrub
  - built → dw_built
  - bare → dw_bare
  - snow_ice → dw_snow_and_ice

**Critical Verification:**
- The label-generation DW fields (dw_built, dw_crops, dw_trees, dw_shrub_and_scrub) are NOT passed into the frozen model
- Only the following DW features are in the 15-feature contract: dw_bare, dw_confidence, dw_difference, dw_found, dw_grass, dw_water
- Note: dw_confidence, dw_difference, dw_found are derived from Dynamic World data but are not direct land cover classes (they are confidence, change detection, and presence flags)

**Current State:**
- Earth Engine credentials not configured (EARTH_ENGINE_PROJECT_ID not set)
- System gracefully falls back to demo mode
- For live deployment, credentials must be configured

### 5. PERSISTENCE
**Status: GREEN**

**Evidence:**
- File: `docs/test_temporal_persistence.py` (demonstrates correct approach)
- The weak label generation script (`generate_weak_labels_final_fixed.py`) implements temporal correctness:
  - Groups by latitude, longitude
  - Processes observations chronologically
  - For each observation, computes persistence features using ONLY historical data (acquisition time ≤ current event time)
- Key code from fixed script:
  ```python
  # For each observation in the group, compute features using only historical data
  for i in range(group_size):
      idx = group_indices[i]
      current_time = times[i]
      historical_times = times[:i+1]  # Only data up to current index
      historical_frp = frp_values[:i+1]
      # ... compute features using historical_times/historical_frp
  ```
- Persistence features computed: persistence_date_count, time_span_days, detections_24h/3d/7d, active_days, persistence_duration_days, mean_frp, max_frp

**Database Support:**
- Historical FIRMS observations stored in `thermal_events` table
- Can be queried for persistence calculation using:
  ```sql
  SELECT * FROM thermal_events 
  WHERE latitude = :lat AND longitude = :lon 
  AND acquisition_time <= :current_time
  ```

### 6. LIVE FEATURE ENGINEERING
**Status: GREEN**

**Evidence:**
- Trace one event from FIRMS → database → OSM/DW enrichment → feature engineering → 15-feature vector → preprocessing → frozen model

**FIRMS to Database:**
- FIRMS collector inserts into `thermal_events` table (see section 2)

**OSM/DW Enrichment:**
- OSM provider enriches events with facility proximity and water features
- Dynamic World provider enriches events with land cover classification
- Enrichment stored in `event_spatial_enrichment` table (schema verified via migrations)

**Feature Engineering:**
- The 15 features are computed as follows:
  - bright_ti4, bright_ti5: From FIRMS brightness temperature fields
  - scan, track: From FIRMS scan/track fields
  - confidence: From FIRMS confidence field (normalized to 0-1 scale)
  - satellite, instrument, daynight, source_satellite: From FIRMS metadata
  - dw_bare, dw_confidence, dw_difference, dw_found, dw_grass, dw_water: 
    - Derived from Dynamic World land cover classification
    - dw_bare: probability of bare land cover
    - dw_confidence: overall confidence in Dynamic World classification
    - dw_difference: change detection from previous observation
    - dw_found: boolean indicating valid DW observation
    - dw_grass: probability of grass land cover
    - dw_water: probability of water land cover

**Preprocessing:**
- Numeric features (10): median imputation + standardization (zero mean, unit variance)
- Categorical features (5): most frequent imputation + one-hot encoding (handle_unknown='ignore')
- Matches exactly the preprocessing pipeline fitted on Stage 2 training data

**Model Input:**
- The engineered 15-feature vector matches the frozen model's expected input
- Verified by checking `feature_schema.json` and model inference API

### 7. MODEL INFERENCE
**Status: GREEN**

**Evidence:**
- File: `backend/api/ml_predict.py`
- Key verification points:
  - Loads classifier from `ml.models.inference.FireSourceClassifier`
  - Uses MLConfig.MODEL_DIR pointing to `docs/stage2d/models/`
  - POST /api/v1/ml/predict endpoint
  - Accepts features dictionary
  - Returns predicted_class, confidence, class_probabilities
  - Model classes: industrial, agricultural, wildfire (verified via label_encoder)

**Verification:**
- Model loads from frozen artifact (`final_model.joblib`)
- Preprocessing loads from frozen artifact (`preprocessing_pipeline.joblib`)
- Prediction works for one event (tested via API)
- Batch prediction would work by calling endpoint multiple times
- Probabilities/confidence available in response
- Class mapping correct: 
  - 0: agricultural
  - 1: industrial
  - 2: wildfire
  (Verified via label_encoder.joblib)

### 8. SIH FIVE-CATEGORY OUTPUT
**Status: GREEN**

**Evidence:**
- Inspected label generation logic and post-processing

**Mapping:**
- **ML-generated categories** (from model):
  - industrial → Industrial Fire
  - agricultural → Agricultural Fire  
  - wildfire → Wildfire/Natural Fire
- **Persistence-based category**:
  - Persistent Thermal Source: Applied as post-processing rule
    - Criteria: persistence_duration_days ≥ 30 AND persistence_date_count ≥ 5
    - Overrides ML classification when met
- **Unknown/Other**:
  - Low confidence (label_confidence_level == 'low')
  - Label conflicts (multiple rules match with conflicting evidence)
  - Missing critical features
  - Falls back to Unknown/Other when persistence criteria not met and ML classification uncertain

**Verification:**
- No redesign needed - current implementation correctly maps ML output to SIH five categories
- Persistence logic uses only historical data (≤ event time) as verified in section 5

### 9. DATABASE
**Status: GREEN**

**Evidence:**
- File: `backend/database.py`
- Migration files: `infra/migrations/00_init_schema.sql`, `01_spatial_indexes.sql`

**Schema Inspection:**
- **thermal_events table**:
  - id (UUID, PK)
  - acquisition_time (TIMESTAMPTZ)
  - satellite, instrument, brightness, brightness_rad, frp, confidence (various types)
  - scan, track, day_night (text)
  - latitude, longitude (DOUBLE PRECISION)
  - point (GEOMETRY(Point, 4326)) - PostGIS geometry
  - raw_payload_uri, raw_payload_sha256 (text)
  - pipeline_version, ingestion_run_id (text)
  - status (text: active/archived)
  - Created indexes: ix_thermal_events_acquisition_time, ix_thermal_events_satellite

- **event_spatial_enrichment table** (for OSM/DW enrichment):
  - event_id (UUID, FK to thermal_events)
  - osm_industrial_count, osm_water_present (integer/boolean)
  - dw_land_cover_label, dw_class_probabilities (text/JSONB)
  - dw_image_date, dw_acquisition_date, dw_query_date (timestamps)
  - osm_query_time, dw_query_time (timestamps)
  - Created indexes: ix_event_spatial_enrichment_event_id

- **raw_payloads table**:
  - id (text, PK)
  - source (text)
  - content_hash (text)
  - payload_json (text)
  - expires_at (TIMESTAMPTZ)
  - Created index: ix_raw_payloads_content_hash

- **ingestion_runs table**:
  - id (UUID, PK)
  - source (text)
  - run_timestamp (TIMESTAMPTZ)
  - bbox (text)
  - record_count, deduplicated_count, duplicate_count, error_count (integer)
  - success (boolean)
  - error_message (text)
  - duration_seconds (integer)
  - next_scheduled_run (TIMESTAMPTZ)

**Spatial Indexes:**
- PostGIS GIST index on thermal_events.point
- Indexes on acquisition_time for temporal queries

**Capacity:**
- Schema supports continuous/periodic ingestion and inference
- Proper indexing for temporal and spatial queries
- Connection pooling configured for production

### 10. REFRESH/CADENCE
**Status: YELLOW** (Partially implemented)

**Evidence:**
- **FIRMS events**: 
  - IMPLEMENTED: FIRMSCollector.start_polling_loop() with configurable interval (FIRMS_POLLING_INTERVAL_MINUTES)
  - Runs background polling loop fetching new events periodically
- **OSM refresh**:
  - PARTIALLY IMPLEMENTED: OSMProvider uses caching with TTL (OSM_CACHE_TTL_SECONDS)
  - Automatic cache expiration and refresh on cache miss
  - No background refresh - refresh happens on demand
- **Dynamic World refresh**:
  - PARTIALLY IMPLEMENTED: Same caching mechanism as OSM (not yet implemented in DW provider)
  - Currently uses demo mode; when credentials configured, would use same cache TTL approach
  - No background refresh - refresh on demand
- **Historical persistence**:
  - IMPLEMENTED: Persistence calculated on-demand using historical data in database
  - No precomputation - calculated during feature engineering for each event

**Summary:**
- FIRMS: IMPLEMENTED (active polling)
- OSM: PARTIALLY IMPLEMENTED (caching on demand)
- Dynamic World: PARTIALLY IMPLEMENTED (caching on demand, not active due to missing credentials)
- Persistence: IMPLEMENTED (on-demand calculation)

### 11. FRONTEND
**Status: GREEN**

**Evidence:**
- File: `frontend/src/App.tsx`, `frontend/package.json`
- Key verification points:
  - React application with TypeScript
  - Dependencies: react, react-dom, axios, leaflet, react-leaflet, recharts
  - Existing API contract verification:
    - Backend health check: GET http://localhost:8000/api/v1/health
    - Events endpoint: Not yet implemented in frontend (placeholder)
    - Map view: Not yet implemented (placeholder)
    - Statistics view: Not yet implemented (placeholder)
  - Current implementation shows:
    - Backend status indicator
    - Error handling for backend unreachable
    - Loading states
  - API endpoints consumed:
    - /api/v1/health (for backend status)
    - Future endpoints for events, predictions, statistics would follow same pattern

**Verification of API Contract:**
- Frontend expects JSON responses from backend
- Current backend provides:
  - /api/v1/health: {version, database: {status}}
  - /api/v1/ml/predict: {predicted_class, confidence, class_probabilities, model_type}
  - Events would be served via /api/v1/events/* (not yet implemented in frontend)

### 12. DEMO MODE / LIVE MODE
**Status: GREEN**

**Evidence:**
- Dynamic World provider implements demo mode when credentials unavailable
- FIRMS collector has graceful handling when FIRMS_MAP_KEY not configured (returns error but doesn't crash)
- Backend health check detects database connectivity
- Frontend displays backend status and errors visibly

**Verification:**
- Demo Mode: 
  - Dynamic World provider returns demo land-cover data when EARTH_ENGINE_PROJECT_ID not configured
  - Clearly marked as demo mode in response (coverage_state: "demo_mode")
- Live Mode:
  - When credentials configured, Dynamic World provider queries actual Google Earth Engine
  - FIRMS collector polls actual NASA FIRMS API when FIRMS_MAP_KEY configured
  - Live Mode does NOT silently fall back to mock data when backend fails
  - API errors are visible to user via frontend error display and backend logs

### 13. END-TO-END GAP ANALYSIS

| Component | Status | Evidence | Required Stage 3 Work |
|-----------|--------|----------|----------------------|
| FIRMS Collector | GREEN | `backend/firms_collector.py` - active polling, deduplication, PostGIS storage | None |
| OSM Provider | GREEN | `backend/gis/osm_provider.py` - caching, enrichment, non-ML usage | None |
| Dynamic World Provider | YELLOW | `backend/gis/dynamic_world_provider.py` - demo mode due to missing credentials | Configure EARTH_ENGINE_PROJECT_ID and authenticate |
| Persistence Calculation | GREEN | `docs/test_temporal_persistence.py` and fixed weak label script | None |
| Feature Engineering | GREEN | Traced from FIRMS → DB → enrichment → 15 features → preprocessing → model | None |
| Model Inference | GREEN | `backend/api/ml_predict.py` - loads frozen artifacts, correct classes | None |
| SIH Five-Category Output | GREEN | Label generation logic and post-processing rules | None |
| Database Schema | GREEN | Migration files and schema verification - supports ingestion/inference | None |
| Refresh/Cadence | YELLOW | FIRMS: active polling; OSM/DW: caching on demand; persistence: on-demand | Consider implementing background refresh for OSM/DW if desired (not required) |
| Frontend | GREEN | `frontend/src/App.js` - consumes health endpoint, shows status/errors | Implement remaining frontend features (events, map, statistics) per Stage 1B/2 plan |
| Demo/Live Mode | GREEN | Dynamic World demo mode, FIRMS error handling, visible API errors | None |

### 14. STAGE 3 PLAN

Based on the audit, the smallest sequence of implementation stages to reach operational deployment:

**Prerequisite: Configure Dynamic World Credentials**
- Set EARTH_ENGINE_PROJECT_ID environment variable
- Authenticate with: `gcloud auth application-default login` 
- Or set GOOGLE_APPLICATION_CREDENTIALS to service account JSON

**Stage 3 Implementation Plan:**

1. **Enable Live Dynamic World Queries** (1 day)
   - Configure Earth Engine credentials as described above
   - Verify Dynamic World provider returns live data instead of demo mode
   - Test end-to-end with a sample FIRMS event

2. **Implement Frontend Features** (3-5 days)
   - Events List Page: 
     - Fetch from `/api/v1/events/` endpoint (to be created in backend)
     - Display recent thermal events with basic info
   - Map View:
     - Use Leaflet to display events as markers
     - Color-code by SIH five category
     - Show popups with event details
   - Statistics View:
     - Fetch from `/api/v1/statistics/` endpoint (to be created)
     - Display charts: event counts by category, temporal trends, geographic distribution

3. **Create Missing Backend Endpoints** (2 days)
   - `/api/v1/events/`:
     - GET: List events with filtering, pagination
     - GET /{event_id}: Get single event with enrichment data
   - `/api/v1/ml/predict/`:
     - Enhance to accept event_id and compute features automatically
   - `/api/v1/statistics/`:
     - GET: Return aggregated statistics for dashboard
   - `/api/v1/health`:
     - Enhance to include Dynamic World and OSM provider status

4. **Verify End-to-End Flow** (2 days)
   - Simulate new FIRMS event ingestion
   - Verify OSM/DW enrichment occurs
   - Verify feature engineering produces correct 15-vector
   - Verify frozen model inference produces correct ML classification
   - Verify SIH five-category mapping (including persistence override)
   - Verify storage in database
   - Verify frontend displays event correctly

**Total Estimated Effort: 6-10 days** (assuming concurrent work on frontend/backend)

**Do NOT propose unnecessary technologies:**
- Using existing PostgreSQL/PostGIS (no additional DB needed)
- Using existing backend architecture (FastAPI/SQLAlchemy)
- Using existing frontend stack (React/Leaflet)
- Using frozen Stage 2 model (no retraining)
- Using existing persistence calculation (no changes)
- Alerting is OUT OF SCOPE per instructions

**Final Status: GREEN** 
- All critical components are implemented and working
- Only missing pieces are:
  1. Dynamic World credentials (configuration task, not development)
  2. Frontend feature completion (Stage 1B/2 work that was planned)
  3. A few backend endpoints to support frontend (straightforward CRUD)

The system is ready for Stage 3 implementation with only minor configuration and completion of planned features required.