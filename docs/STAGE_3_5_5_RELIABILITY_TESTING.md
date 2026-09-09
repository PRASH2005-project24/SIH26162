# Stage 3.5.5: Operational Reliability & Failure-Recovery Testing

## Objective
To ensure the pipeline is resilient to individual component failures, network timeouts, authentication issues, and duplicate processing, maintaining continuous operation without bringing down the system.

## Scenarios Tested & Handled

### 1. FIRMS Ingestion Failures
- **HTTP 500 & Timeouts:** Implemented robust retries via `aiohttp.ClientTimeout` and error trapping. If FIRMS is unreachable after 3 retries, the system logs the failure gracefully and continues the poll cycle.
- **Malformed CSV:** The ingestion engine safely handles corrupted data, gracefully skipping problematic rows while still processing the rest of the payload.

### 2. GIS Enrichment Failures (OSM & Dynamic World)
- **OSM Outages:** If Overpass API times out or returns a 502/503 error, the `OSMProvider` catches the exception and returns empty default features (e.g. `industrial: False`, `water: False`). This guarantees inference can still execute, relying solely on other features.
- **Dynamic World Auth Failure:** The Earth Engine client catches missing credentials and API errors, degrading smoothly to returning `land_cover_label: None` and proceeding with demo-mode/fallback without crashing the enrichment process.

### 3. ML Inference Failures
- **Corrupt Feature Vectors:** Handled via `try-except` in `ClassifierEngine.classify_batch()`. If inference throws an exception (e.g., `FeatureEngineer not fitted`), the event is marked with `classification_status = 'failed'` and an `inference_error` is saved, bypassing catastrophic pipeline termination.

### 4. Idempotency Attacks (Deduplication)
- **Repeated Polling:** Simulating rapid, concurrent FIRMS polling on the same bounding box proved that the deduplication logic (hashing the thermal event coordinate, satellite, and acquisition time) correctly limits ingestion. Duplicates are tagged without triggering redundant downstream processing.

### 5. Adversarial Temporal Leakage
- **Future Events Impersonating Past Events:** The ML Persistence calculation uses `ST_DWithin` and `acquisition_time <= event_time`. Inserting future observations into a bounding box does not artificially inflate the persistence metrics of historical events, preventing temporal data leakage.

## Current Status
- `scripts/test_pipeline_reliability.py` executes successfully.
- **ALL RELIABILITY TESTS PASSED GREEN.**
- Pipeline operations are hardened, correct, temporally safe, and idempotent. Stage 3.5.5 is complete.
