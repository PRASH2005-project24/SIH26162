# Dynamic World Live Enrichment Improvement Report

**Date:** 2026-09-27  
**Scope:** Google Earth Engine Dynamic World sampling and persisted GIS enrichment

## Summary

The live Dynamic World provider was improved to recover valid land-cover samples when the nearest scene or event pixel is masked, while distinguishing fresh Earth Engine results from cached results and rejecting incomplete responses as successful live coverage.

On the same 10-event cohort, usable persisted results increased from 1/10 to 4/10. The final cohort contained three confirmed fresh-live usable results (30%) and one cached usable result. This is a small pilot, not a production-wide success-rate estimate.

## Changes Completed

- Dynamic World scenes are mosaicked in acquisition-date proximity order, with the closest valid pixels given priority.
- Sampling first checks the event coordinate, then a 30 m neighborhood if the point is masked.
- The provider first searches within +/-15 days of acquisition. If that produces no usable sample, it retries with a bounded +/-30-day window.
- The selected imagery date, image age in days, temporal window, and sampling method are returned by the provider.
- A response is considered usable only if it has a recognized land-cover class and all nine probability bands with valid probability values.
- Empty or incomplete responses are reported as `no_valid_pixel` or `coverage_unknown`, not `live`.
- Only usable results are cached. A valid cache hit is labeled `cached`, with its original provider state retained separately.
- Added provider regression tests for valid/incomplete samples and cache-state semantics.

## Measured Results

### Same 10-Event Cohort

| Measurement | Result |
|---|---:|
| Initial usable outputs | 1/10 (10%) |
| Final usable outputs, including cache | 4/10 (40%) |
| Final confirmed fresh-live usable outputs | 3/10 (30%) |
| Final cached usable outputs | 1/10 |
| Persisted enrichment rows in final run | 10/10 |

The final cohort had five `no_valid_pixel` responses and one `coverage_unknown` response. Two newly recovered samples used imagery dated 16 and 26 days before their events. Their image ages are returned by the provider but are not yet persisted in `event_spatial_enrichment`.

### Current Database Snapshot

The latest-row-per-event query found 57 usable results among 128 events with a GIS enrichment row (44.5%). Across 577 eligible active events, 57 currently have usable Dynamic World data (9.9% coverage). These are completeness figures, not attempted-event failure rates.

The database includes legacy rows created before cache hits were distinguished from fresh queries. Therefore the aggregate cannot reliably be interpreted as a fresh-live rate. Use the post-change cohort for that comparison.

## Validation

- `python -m pytest backend/tests/test_dynamic_world_provider.py -q`: **6 passed**.
- `python test_ee_final.py`: real authenticated Earth Engine query returned a complete nine-class result with `coverage_state: live`.
- Direct live checks on two previously failing events returned valid nine-class samples using the +/-30-day fallback, with image ages of 26 and 16 days.
- The final database-backed cohort run processed all 10 events and persisted all 10 engine results. Engine success means a row was written; usable enrichment was counted separately from that status.
- `python -m pytest backend/tests/test_enrichment_engine.py -q`: **11 passed, 2 failed**. The failures concern the pre-existing feature-radius count and confidence proximity assertions, outside the Dynamic World provider changes.
- `git diff --check`: no whitespace errors; Git reported line-ending normalization warnings for unrelated working-tree files.

## Database Side Effects

The same 10-event cohort was processed through the enrichment engine three times during measurement. Each attempt inserts a new `event_spatial_enrichment` row, so these runs added 30 rows across those 10 events. They were left in place; no test-created enrichment rows were deleted.

## Remaining Work

- Persist the selected Dynamic World image date and age on each enrichment record so consumers can assess temporal staleness.
- Diagnose the remaining no-valid-pixel events; widening the date window further should be based on an explicit maximum-age policy.
- Run a larger, geographically and temporally varied cohort before publishing a production-wide live enrichment rate.
- Fix or revise the two unrelated enrichment-engine tests separately.

## Related Files

- `backend/gis/dynamic_world_provider.py`
- `backend/tests/test_dynamic_world_provider.py`
- `backend/gis/enrichment_engine.py`
- `FIREXIS_DOCUMENTATION.md`
