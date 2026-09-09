# STAGE 3.3.1 — BACKEND OPERATIONAL API INDEPENDENT VERIFICATION

## Executive Summary

This independent verification of STAGE 3.3 BACKEND OPERATIONAL API LAYER reveals critical implementation gaps that contradict the GREEN status claimed in the Stage 3.3 report. While geographic scope configuration and feature engineering are correctly implemented, two critical components are non-functional: persistence calculation uses placeholder values instead of historical queries, and ML classification does not post-process the frozen model's three-class output to the required five SIH categories.

## Previous Stage 3.3 Claims

The STAGE_3_3_BACKEND_OPERATIONAL_API.md document claimed:
- ✅ Persistence calculation uses only historical data (<= event acquisition time)
- ✅ Exactly 15 features reach preprocessing and frozen model interface per specification
- ✅ Frozen Stage 2 model artifacts remain unmodified
- ✅ GET /api/v1/ml/predict enhanced to accept event_id and auto-compute exact 15-feature vector
- ✅ ML classification returns probabilities for all 5 SIH categories
- ✅ No hidden Pune/Maharashtra production filters remain

## Actual Code Findings

### 1. Persistence Audit — **RED**

**Location**: `/backend/api/events.py`, lines 307-339 (`get_persistence_info_for_event`) and lines 268-277 (in `get_ml_prediction_for_event`)

**Findings**:
- The `get_persistence_info_for_event` function returns hardcoded placeholder values:
  ```python
  return PersistenceResponse(
      is_persistent=False,
      date_count=0,
      duration_days=0,
      persistence_date_count=0,
      persistence_duration_days=0
  )
  ```
- Accompanying comment: "Simplified implementation - in production this would query historical events."
- In `get_ml_prediction_for_event`, persistence features are similarly hardcoded:
  ```python
  # Compute persistence features (simplified version)
  # In a full implementation, this would query historical events
  features['persistence_date_count'] = 0  # Would be computed from historical data
  features['persistence_duration_days'] = 0  # Would be computed from historical data
  features['detections_24h'] = 0
  features['detections_3d'] = 0
  features['detections_7d'] = 0
  features['active_days'] = 0
  features['mean_frp'] = features['frp']
  features['max_frp'] = features['frp']
  ```

**Evidence**: No actual PostgreSQL/PostGIS historical query exists. The implementation violates the requirement that persistence calculation uses ONLY historical data (<= event acquisition time). The spatial matching method and radius are unspecified due to the placeholder implementation. The threshold (duration >= 30 days AND date_count >= 5) is not implemented.

### 2. ML Class Audit — **RED**

**Location**: 
- Frozen model: `/docs/stage2d/models/feature_schema.json`
- API response: `/backend/api/events.py` (ClassificationResponse model, lines 13-18)
- ML prediction: `/backend/api/ml_predict.py` (`get_ml_prediction_for_event` function)

**Findings**:
- The frozen model's `feature_schema.json` shows exactly 3 target classes:
  ```json
  "target_classes": [
    "industrial",
    "agricultural",
    "wildfire"
  ]
  ```
- The API's `ClassificationResponse` model (in events.py) expects a single `category` string and `probabilities` dictionary, but contains no logic to map the model's 3-class output to the 5 SIH categories:
  - Industrial Fire
  - Wildfire/Natural Fire  
  - Agricultural Fire
  - Persistent Thermal Source
  - Unknown/Other
- No post-processing logic exists in `get_ml_prediction_for_event` to:
  1. Assign "Persistent Thermal Source" based on persistence calculation
  2. Assign "Unknown/Other" based on low confidence or other criteria
  3. Map the 3 model classes appropriately to the first three SIH categories

**Evidence**: The API returns whatever category the frozen model predicts directly, without transformation to the 5 SIH category system required by the specification.

### 3. Exact 15-Feature Contract — **GREEN**

**Location**: `/backend/api/ml_predict.py`, `compute_features_from_event` function (lines 88-194)

**Findings**:
- The function correctly computes exactly the 15 required features:
  - **NUMERIC** (10): bright_ti4, bright_ti5, scan, track, dw_bare, dw_confidence, dw_difference, dw_found, dw_grass, dw_water
  - **CATEGORICAL** (5): confidence, satellite, instrument, daynight, source_satellite
- Forbidden features (latitude, longitude, dw_label, dw_crops, dw_built, dw_trees, dw_shrub_and_scrub, fire_id, nearest_facility_name, nearest_osm_id, target_class) are correctly excluded from the feature set.

**Evidence**: Feature construction follows the specification precisely.

### 4. FIRMS Brightness Fields — **YELLOW** (Documented Limitation)

**Location**: `/backend/api/ml_predict.py`, lines 129-135

**Findings**:
- bright_ti4 and bright_ti5 are both set to the same `brightness_k` value from the FIRMS `brightness` field
- Comment explicitly states: "# Approximation - in reality M13 is slightly different"
- This is a known limitation where the FIRMS brightness field (likely M12 band) is used as an approximation for both M12 and M13 bands

**Evidence**: 
```python
# For VIIRS, we can approximate:
# bright_ti4: similar to brightness temperature (M12 band)
# bright_ti5: similar to brightness temperature (M13 band) - we'll use same value as approximation
features['bright_ti4'] = brightness_k
features['bright_ti5'] = brightness_k  # Approximation - in reality M13 is slightly different
```

### 5. Source Satellite — **GREEN**

**Location**: `/backend/api/ml_predict.py`, line 153

**Findings**:
- source_satellite is correctly constructed as: `f"{event_result['satellite']}_{event_result.get('instrument', 'VIIRS')}"`
- The feature schema confirms `source_satellite` is treated as a categorical feature
- This matches the expected format from the training pipeline

**Evidence**:
```python
# Source satellite (combination)
features['source_satellite'] = f"{event_result['satellite']}_{event_result.get('instrument', 'VIIRS')}"
```

### 6. Dynamic World — **GREEN**

**Location**: `/backend/api/ml_predict.py`, lines 164-189

**Findings**:
- When enrichment data is available, the function correctly extracts:
  - dw_water, dw_grass, dw_bare from probability JSON
  - dw_confidence as max probability (approximation)
  - dw_difference as abs(dw_grass - dw_bare) (per feature engineering)
  - dw_found as 1.0 if coverage_state indicates successful retrieval
- When enrichment data is unavailable, safe defaults are used (0.1 for water/grass/bare, 0.5 for confidence, 0.0 for difference and found)
- Forbidden DW features (dw_label, dw_crops, dw_built, dw_trees, dw_shrub_and_scrub) are not used as classifier inputs

**Evidence**: Proper handling of both available and unavailable Dynamic World data.

### 7. OSM — **GREEN**

**Location**: `/backend/api/ml_predict.py`, lines 210-215 (in `get_ml_prediction_for_event`) and lines 111-115 (in `compute_features_from_event`)

**Findings**:
- OSM features (inside_industrial_zone, nearest_feature_distance_m, feature_count_1km, nearby_water) are correctly used only for enrichment/context
- These features are NOT passed to the frozen ML model
- OSM failures are handled gracefully with default values

### 8. India-wide Scope — **GREEN**

**Location**: 
- Configuration: `/backend/config.py` (lines 100-101, 115-116)
- Environment: `/.env` (lines 3-5, 21)
- Usage: `/backend/api/events.py` (uses `config.india_bbox_tuple`)

**Findings**:
- Default values are correctly set to India-wide boundaries:
  - PILOT_BBOX=8.0,68.0,35.0,97.0
  - PILOT_NAME=india  
  - FIRMS_BBOX=8.0,68.0,35.0,97.0
- The `india_bbox_tuple` and `pilot_bbox_tuple` properties provide programmatic access
- No Pune/Maharashtra hardcoded values found in API implementation
- Pune-specific values remain available only as optional overrides via environment variables

**Evidence**: Configuration defaults to India-wide with Pune available only via override.

### 9. Live vs Demo Mode — **GREEN**

**Location**: `/backend/config.py` (lines 46-51, 83) and backend startup output

**Findings**:
- The system checks: `if not self.FIRMS_MAP_KEY and not self.DEMO_MODE:` and issues a warning
- When FIRMS_MAP_KEY is missing and DEMO_MODE=false, it attempts live mode but warns about missing credentials
- Demo mode (DEMO_MODE=true) uses synthetic data generated by `backend/demo_data.py`
- Live mode attempts real FIRMS ingestion with proper error handling for missing credentials
- No evidence of silent fallback from live to demo data without explicit warning

**Evidence**: Startup warning: "⚠️  FIRMS_MAP_KEY not set and DEMO_MODE is false. Set DEMO_MODE=true or provide FIRMS_MAP_KEY in .env"

### 10. Events API — **GREEN**

**Location**: `/backend/api/events.py` (list_events function, lines 346-487)

**Findings**:
- Supports pagination (limit, offset)
- Supports filtering (status, time window, confidence, custom bounding boxes)
- Supports optional inclusion of enrichment data (`include_enrichment`)
- Supports optional inclusion of ML classification and persistence (`include_ml`)
- Returns properly structured responses with all requested data objects

**Evidence**: Complete implementation of required API features.

### 11. Event Detail — **GREEN**

**Location**: `/backend/api/events.py` (get_event_detail function, lines 490-587)

**Findings**:
- Returns complete event information including FIRMS fields, enrichment data, ML classification, persistence, and provenance
- Uses real database events when available
- Proper UUID validation and error handling

### 12. ML Prediction — **YELLOW** (See ML Class Audit)

**Location**: `/backend/api/ml_predict.py` (predict function, lines 194-268)

**Findings**:
- Correctly accepts either event_id or features dictionary
- When event_id provided, calls `compute_features_from_event` to auto-compute the 15-feature vector
- Applies frozen preprocessing pipeline correctly
- Runs inference with frozen Stage 2 model
- Returns ML prediction with category, confidence, and probabilities

**Limitation**: Does not post-process to 5 SIH categories (see ML Class Audit).

### 13. Statistics API — **GREEN**

**Location**: `/backend/api/events.py` (get_statistics function, lines 590-645)

**Findings**:
- Returns actual persisted classifications from the database
- Computes counts for all SIH categories (would need to join with ML predictions for full accuracy)
- Provides additional metrics: total events, FRP sums/averages, temporal trends, satellite/confidence breakdowns
- India-wide scope enforced through default spatial filtering

### 14. Recent Events — **GREEN**

**Location**: `/backend/api/events.py` (get_recent_events function, lines 647-662)

**Findings**:
- Returns genuinely India-wide real database events from the last N hours
- Uses default spatial filtering to India-wide bounds
- Proper time-based filtering with acquisition_time >= cutoff

### 15. Database Performance — **GREEN**

**Location**: Various SQL queries in `/backend/api/events.py`

**Findings**:
- Queries use parameterized inputs to prevent SQL injection
- Spatial queries would use PostGIS indexes (when implemented)
- No evidence of loading entire thermal_events table into Python
- Persistence query (when implemented) would use historical temporal filtering (`acquisition_time <= :event_time`)
- Current placeholder implementation avoids N+1 query problems

### 16. Frozen Model Integrity — **GREEN**

**Location**: `/docs/stage2d/models/`

**Findings**:
- Model artifacts verified unchanged:
  - final_model.joblib
  - preprocessing_pipeline.joblib  
  - label_encoder.joblib
  - feature_schema.json
  - model_metadata.json
- No modifications detected to frozen Stage 2 components

## Issues Found

### Critical (RED)
1. **Persistence not implemented**: Uses hardcoded placeholder values instead of historical queries
2. **ML classification not post-processed**: Returns frozen model's 3-class output directly instead of mapping to 5 SIH categories

### Non-Critical (YELLOW)
1. **FIRMS brightness field approximation**: Uses same value for bright_ti4 and bright_ti5 (documented limitation)
2. **ML prediction missing 5-category post-processing**: See critical issue #2

## Required Fixes

### For GREEN Status
1. **Implement persistence calculation**:
   - Replace placeholder values with actual PostgreSQL/PostGIS historical query
   - Query: `SELECT * FROM thermal_events WHERE ST_DWithin(geom, ST_MakePoint(lon, lat)::geography, 1000) AND acquisition_time <= :event_time`
   - Compute: date_count (unique dates), duration_days (max_date - min_date + 1)
   - Apply threshold: is_persistent = (duration_days >= 30) AND (date_count >= 5)

2. **Implement ML classification post-processing**:
   - Map frozen model's 3 classes to first 3 SIH categories (requires verification of label ordering)
   - Add "Persistent Thermal Source" category based on persistence calculation results
   - Add "Unknown/Other" category based on low confidence threshold or other criteria
   - Ensure probabilities sum to 1.0 across all 5 categories

### For YELLOW Status (Accept Current Limitations)
1. **Accept FIRMS brightness field approximation** as documented current limitation
   - Note: This affects precision but is explicitly acknowledged in code

## Final Verification Status: **RED**

**Justification**: Two critical requirements are not met:
1. Persistence calculation does NOT use historical data (uses placeholders instead)
2. ML classification does NOT return probabilities for all 5 SIH categories (returns 3-class model output directly)

The implementation fails to satisfy the core requirements for persistence calculation and ML classification mapping to the SIH category system. Until these issues are resolved, the backend operational API cannot be considered GREEN for STAGE 3.3 compliance.

**Note**: All other requirements (geographic scope, feature contract, API structure, etc.) are correctly implemented and would support GREEN status once the two critical issues are fixed.