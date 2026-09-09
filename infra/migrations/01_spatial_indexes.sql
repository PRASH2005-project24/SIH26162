-- ============================================================================
-- Stage 1A: Spatial Indexes and Performance Tuning
-- Run after 00_init_schema.sql
-- ============================================================================

-- Cluster thermal_events by spatial proximity for faster range queries
-- (Only if index exists)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE indexname = 'idx_thermal_events_geom'
  ) THEN
    CLUSTER thermal_events USING idx_thermal_events_geom;
  END IF;
END
$$;

-- Cluster contextual_features by geometry for faster joins
-- (Only if index exists)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE indexname = 'idx_contextual_features_geom'
  ) THEN
    CLUSTER contextual_features USING idx_contextual_features_geom;
  END IF;
END
$$;

-- Add functional index for rapid time-based range queries
CREATE INDEX IF NOT EXISTS idx_thermal_events_date_bucket
  ON thermal_events(DATE_TRUNC('hour', acquisition_time));

-- Add index for status filtering (common in API queries)
CREATE INDEX IF NOT EXISTS idx_thermal_events_status
  ON thermal_events(status, created_at DESC);

-- Partial index for active (non-archived) events only
CREATE INDEX IF NOT EXISTS idx_thermal_events_active
  ON thermal_events(acquisition_time DESC)
  WHERE status = 'active';

-- GiST index for geographic range queries (point in bbox)
CREATE INDEX IF NOT EXISTS idx_thermal_events_bbox
  ON thermal_events
  USING GIST(ST_Expand(point, 0.01))
  WHERE status = 'active';

-- Analyze schema statistics for query planner
ANALYZE thermal_events;
ANALYZE contextual_features;
ANALYZE ingestion_runs;
ANALYZE raw_payloads;
ANALYZE source_health;
