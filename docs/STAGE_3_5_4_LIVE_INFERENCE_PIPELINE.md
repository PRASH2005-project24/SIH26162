# Stage 3.5.4: Live Inference Pipeline

This document outlines the architecture, properties, and failure modes of the automated end-to-end Live Inference Pipeline designed for NASA FIRMS thermal events in the SIH26162 application.

## 1. Overview

The Live Inference Pipeline orchestrates the automated data flow from thermal event ingestion to spatial enrichment, machine learning inference, and database persistence. It ensures that any new active fire data is instantaneously processed and classified without manual intervention or frontend dependency.

**Pipeline Flow:**
1. **FIRMS Polling (`firms_collector.py`)**: Fetches active fire data for the Indian bounding box and identifies newly detected events while eliminating duplicates (`dedup_key`).
2. **Spatial Enrichment (`GISEnrichmentEngine`)**: Enhances thermal events with context from OSM (Industrial, Water) and Google Dynamic World (Land Cover) APIs using the event coordinates.
3. **Classification & Persistence (`ClassifierEngine`)**:
   - Executes frozen machine learning feature engineering on the enriched data.
   - Computes event persistence based on historical fire activity within a 1km radius (preventing temporal leakage).
   - Generates predictions via the frozen Random Forest (`final_model.joblib`).
   - Assigns a final SIH category using post-processing business rules.
   - Upserts final decisions into the `event_classifications` table.

## 2. Idempotent Properties

The pipeline incorporates strong idempotency at both the data ingestion and processing tiers, ensuring it can be rerun safely on the same dataset without unintended side effects.

- **Deduplication Key**: Each raw thermal event has a globally unique `dedup_key` formed by `(latitude_rounded, longitude_rounded, acquisition_time, satellite)`. If an event matches an existing key, the ingestion engine logs a duplicate count and skips insertion.
- **Enrichment Upserts**: The `GISEnrichmentEngine` executes upserts via `ON CONFLICT (event_id) DO UPDATE` to gracefully handle redundant processing requests.
- **Classification Upserts**: The `ClassifierEngine` utilizes `ON CONFLICT (event_id) DO UPDATE`, overriding previous metadata if re-evaluated but not duplicating rows in the `event_classifications` table.
- **Idempotency Validated**: Validated through `test_pipeline_e2e.py` demonstrating zero duplicate rows when processing operations are re-invoked on the same ID.

## 3. Failure Isolation & Graceful Degradation

The pipeline operates with isolation guarantees to handle external provider outages or processing errors without failing the overall ingestion flow.

- **GIS Provider Isolation**: 
  - If Google Earth Engine or OSM Overpass APIs time out or throw errors (e.g., missing credentials or network issues), the enrichment engine assigns predefined default values (e.g., `is_industrial=False`, `distance_to_water=1000`).
  - This allows the ML model to continue its inference process with slightly degraded but predictable accuracy rather than blocking the ingestion entirely.
- **Classification Status Check**:
  - Events that are missing enrichment context still proceed through classification. Their final status is registered as `success` and mapping to valid classes like "Unknown / Other" or "Industrial Fire" proceeds unaffected.
- **Temporal Safety Guarantee**:
  - The `ClassifierEngine`'s calculation of "persistence" explicitly restricts its database query to events with an `acquisition_time` strictly less than or equal to the target event's time. Future events can never pollute the classification of historical events.

## 4. API Endpoints

- **`GET /api/v1/events`**: Summarizes events seamlessly reading from the materialized `event_classifications` output without requiring batch inference at runtime.
- **`GET /api/v1/events/stats`**: Serves pre-calculated SIH statistics and processing times securely from the database instead of the dynamic feature store.
- **`GET /api/v1/ml/predict?event_id={id}`**: Deprecated/Used as diagnostic fallback since predictions are preemptively computed during ingestion.

## 5. Conclusion

The Stage 3.5.4 Live Inference Pipeline successfully delivers a robust, hands-free integration between raw remote sensing anomalies and automated machine-learning-driven classifications, ready for operational staging.
