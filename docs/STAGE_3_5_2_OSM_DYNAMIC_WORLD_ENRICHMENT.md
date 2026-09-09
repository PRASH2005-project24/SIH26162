# Stage 3.5.2: OSM & Dynamic World Enrichment Reliability

## Overview
This stage hardens the GIS enrichment pipeline (OSM and Google Dynamic World) to operate reliably on India-wide data in a production context, completing Stage 3.5.2.

## Implementation Details

1. **Integrated Ingestion Pipeline**
   - Modified `backend/firms_collector.py` to trigger batch GIS enrichment sequentially on all newly ingested FIRMS events.
   - This ensures enrichment occurs continuously in the background alongside event ingestion, instead of relying solely on on-demand frontend triggers.

2. **OSM Caching and Error Handling**
   - Fixed `OSMProvider` caching logic. Since `osm_cache` lacked a unique constraint on tile properties, the `ON CONFLICT DO NOTHING` statement was quietly failing to update expired cache entries. We implemented a manual `UPDATE` with a fallback `INSERT`.
   - Modified OSM queries (`OSM_INDUSTRIAL_QUERY` and `OSM_WATER_QUERY`) to enforce `[out:json][bbox:...];` effectively on a single line. The API returned XML by default which crashed the parser.
   - Hardened `_execute_overpass_query` to handle `429 Too Many Requests` specifically with a prolonged backoff sleep duration to respect Overpass public API limits.

3. **Dynamic World Caching and Graceful Fallback**
   - Introduced the `db: Database` dependency into `DynamicWorldProvider`.
   - Reused the `osm_cache` PostgreSQL schema to create a unified caching layer for Dynamic World land cover results. The cache is deterministically keyed by tile coordinate and acquisition year/month (`dw_YYYY_MM`).
   - Hardened the credential fallback. In production mode (`DEMO_MODE=False`), missing credentials or provider failure will no longer silently fabricate fake data. Instead, it correctly returns a `source_unavailable` coverage state which the downstream ML model handles cleanly.

4. **Database Resilience**
   - Fixed `nearest_feature_id` parsing in `GISEnrichmentEngine` which previously threw an `asyncpg.exceptions.DataError` when attempting to insert large OSM integers into a PostgreSQL `VARCHAR` column.

## Operational Constraints Maintained
- **No Overlapping Schedulers**: Enrichment is orchestrated at the end of the existing `FIRMSCollector.poll_once()` lifecycle, maintaining a single polling loop and preventing race conditions.
- **Contextual Integrity**: Provider failure does not hallucinate data. Missing information is stored correctly and the 15-feature contract degrades gracefully.
- **India-wide Scope**: The providers continue to serve the India bounding box and cache hits will drastically reduce remote API calls during wide-area FIRMS polling.
