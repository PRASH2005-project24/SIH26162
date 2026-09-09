-- ============================================================================
-- Stage 1A: FIRMS Ingestion Schema
-- PostgreSQL + PostGIS initialization
-- ============================================================================

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;

-- ============================================================================
-- thermal_events table
-- Core normalized thermal detections from FIRMS
-- ============================================================================
CREATE TABLE IF NOT EXISTS thermal_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- FIRMS acquisition metadata
    acquisition_time TIMESTAMP WITH TIME ZONE NOT NULL,
    satellite TEXT NOT NULL, -- e.g., "NOAA-20", "Suomi NPP"
    instrument TEXT, -- e.g., "VIIRS", "MODIS"

    -- Thermal signal measurements
    brightness NUMERIC, -- K (Kelvin)
    brightness_rad NUMERIC, -- W/m2/sr
    frp NUMERIC, -- Fire Radiative Power (MW)
    confidence INTEGER, -- 0-100
    scan NUMERIC, -- scan angle (degrees)
    track NUMERIC, -- track angle (degrees)
    day_night TEXT, -- 'D' or 'N'

    -- Geometry (WGS84, EPSG:4326)
    point GEOMETRY(Point, 4326) NOT NULL,
    latitude NUMERIC(10, 6) NOT NULL,
    longitude NUMERIC(11, 6) NOT NULL,

    -- Raw payload tracking
    raw_payload_uri TEXT, -- object storage URI
    raw_payload_sha256 TEXT, -- content hash for dedup verification

    -- Pipeline provenance
    pipeline_version TEXT DEFAULT '1.0.0',
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ingestion_run_id UUID, -- FK to ingestion_runs

    -- Status and flags
    status TEXT DEFAULT 'active', -- 'active', 'archived', 'duplicate'
    is_duplicate BOOLEAN DEFAULT FALSE, -- detected duplicate
    duplicate_of_id UUID, -- if duplicate, points to canonical event

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_ingestion_run FOREIGN KEY (ingestion_run_id) REFERENCES ingestion_runs(id) ON DELETE SET NULL
);

-- Unique constraint for deterministic deduplication: (lat, lon, acq_time, satellite)
CREATE UNIQUE INDEX idx_thermal_events_dedup
  ON thermal_events (
    ROUND(latitude::NUMERIC, 4),
    ROUND(longitude::NUMERIC, 4),
    DATE_TRUNC('minute', acquisition_time),
    satellite
  )
  WHERE status != 'archived';

-- Spatial index for fast geographic queries
CREATE INDEX idx_thermal_events_geom ON thermal_events USING GIST(point);

-- Time-based index for recent events
CREATE INDEX idx_thermal_events_acquisition_time ON thermal_events(acquisition_time DESC);

-- ============================================================================
-- ingestion_runs table
-- Track FIRMS polling runs and their success/failure
-- ============================================================================
CREATE TABLE IF NOT EXISTS ingestion_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Run metadata
    source TEXT NOT NULL DEFAULT 'FIRMS', -- FIRMS, manual-import, replay, etc.
    run_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Results
    bbox TEXT, -- bounding box requested: "min_lat,min_lon,max_lat,max_lon"
    record_count INTEGER DEFAULT 0, -- records fetched
    deduplicated_count INTEGER DEFAULT 0, -- new canonical events
    duplicate_count INTEGER DEFAULT 0, -- duplicates detected
    error_count INTEGER DEFAULT 0, -- parse/ingest errors

    -- Status
    success BOOLEAN NOT NULL DEFAULT FALSE,
    error_message TEXT,

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,

    -- Scheduling
    next_scheduled_run TIMESTAMP WITH TIME ZONE,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for run history queries
CREATE INDEX idx_ingestion_runs_source_time ON ingestion_runs(source, run_timestamp DESC);

-- ============================================================================
-- raw_payloads table
-- Immutable store of raw FIRMS API responses for full reproducibility
-- ============================================================================
CREATE TABLE IF NOT EXISTS raw_payloads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Payload metadata
    source TEXT NOT NULL, -- "FIRMS", "manual-import", etc.
    source_type TEXT, -- "VIIRS-375m", "MODIS-1km", etc.
    ingestion_run_id UUID NOT NULL,

    -- Content tracking
    payload_uri TEXT NOT NULL, -- object storage URI
    content_sha256 TEXT NOT NULL UNIQUE, -- content hash for dedup
    content_type TEXT, -- e.g., "application/json", "text/csv"
    size_bytes INTEGER,

    -- Acquisition window (what this payload covers)
    acquired_start TIMESTAMP WITH TIME ZONE,
    acquired_end TIMESTAMP WITH TIME ZONE,
    bbox TEXT, -- "min_lat,min_lon,max_lat,max_lon"

    -- Timestamps
    fetched_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    retained_until TIMESTAMP WITH TIME ZONE, -- retention policy

    CONSTRAINT fk_ingestion_run FOREIGN KEY (ingestion_run_id) REFERENCES ingestion_runs(id) ON DELETE CASCADE
);

CREATE INDEX idx_raw_payloads_sha256 ON raw_payloads(content_sha256);
CREATE INDEX idx_raw_payloads_source_time ON raw_payloads(source, fetched_at DESC);

-- ============================================================================
-- source_health table
-- Track health/availability of data sources and adapters
-- ============================================================================
CREATE TABLE IF NOT EXISTS source_health (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    source_name TEXT NOT NULL UNIQUE, -- "FIRMS", "OSM-Overpass", "Bhuvan", etc.
    source_type TEXT, -- "API", "DB", "WFS", "manual-import"

    -- Status
    status TEXT NOT NULL DEFAULT 'unknown', -- 'healthy', 'degraded', 'unavailable', 'unknown'
    last_check TIMESTAMP WITH TIME ZONE,
    last_success TIMESTAMP WITH TIME ZONE,

    -- Coverage info
    coverage_bbox TEXT, -- "min_lat,min_lon,max_lat,max_lon" or NULL if global
    last_update TIMESTAMP WITH TIME ZONE,
    data_version TEXT, -- e.g., "2026-08-25" for OSM snapshot

    -- Metrics
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    error_log TEXT, -- last error message

    -- Notes
    notes TEXT,

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_source_health_status ON source_health(status);

-- ============================================================================
-- contextual_features table (stub for Stage 1B)
-- OSM/GIS features: factories, industrial zones, forests, water bodies, etc.
-- ============================================================================
CREATE TABLE IF NOT EXISTS contextual_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Feature metadata
    source TEXT NOT NULL, -- "OSM", "Bhuvan", "GeoJSON-import", etc.
    feature_type TEXT NOT NULL, -- "industrial_park", "factory", "forest", "water", etc.
    name TEXT,

    -- Geometry (normalized to WGS84)
    geom GEOMETRY(Geometry, 4326) NOT NULL,
    original_crs TEXT, -- e.g., "EPSG:4326"

    -- Source properties (JSON for flexibility)
    source_properties JSONB,

    -- Data version and provenance
    data_version TEXT,
    imported_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Spatial index helpers
    bbox_min_lat NUMERIC(10, 6),
    bbox_max_lat NUMERIC(10, 6),
    bbox_min_lon NUMERIC(11, 6),
    bbox_max_lon NUMERIC(11, 6),

    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_contextual_features_geom ON contextual_features USING GIST(geom);
CREATE INDEX idx_contextual_features_source_type ON contextual_features(source, feature_type);

-- ============================================================================
-- event_spatial_enrichment table (stub for Stage 1B)
-- Links events to nearby contextual features with distance/containment info
-- ============================================================================
CREATE TABLE IF NOT EXISTS event_spatial_enrichment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    event_id UUID NOT NULL,
    feature_id UUID NOT NULL,

    -- Spatial relationship
    inside_zone BOOLEAN, -- true if event inside feature polygon
    nearest_distance_meters NUMERIC, -- distance from event to feature
    overlap_area_sqm NUMERIC, -- area of overlap if applicable

    -- Rule version and provenance
    rule_version TEXT DEFAULT '1.0.0',
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_event FOREIGN KEY (event_id) REFERENCES thermal_events(id) ON DELETE CASCADE,
    CONSTRAINT fk_feature FOREIGN KEY (feature_id) REFERENCES contextual_features(id) ON DELETE CASCADE
);

CREATE INDEX idx_enrichment_event_id ON event_spatial_enrichment(event_id);
CREATE INDEX idx_enrichment_feature_id ON event_spatial_enrichment(feature_id);

-- ============================================================================
-- System metadata table
-- ============================================================================
CREATE TABLE IF NOT EXISTS system_metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Initialize system metadata
INSERT INTO system_metadata (key, value) VALUES ('schema_version', '1.0.0')
  ON CONFLICT (key) DO NOTHING;
INSERT INTO system_metadata (key, value) VALUES ('stage', 'stage_1a_firms_ingestion')
  ON CONFLICT (key) DO NOTHING;
INSERT INTO system_metadata (key, value) VALUES ('last_migration', '00_init_schema.sql')
  ON CONFLICT (key) DO NOTHING;

-- ============================================================================
-- Helper function: mark_duplicate_event
-- Deterministic deduplication logic
-- ============================================================================
CREATE OR REPLACE FUNCTION mark_duplicate_event(
    new_event_id UUID,
    canonical_event_id UUID
) RETURNS VOID AS $$
BEGIN
    UPDATE thermal_events
    SET is_duplicate = TRUE,
        duplicate_of_id = canonical_event_id,
        status = 'duplicate',
        updated_at = CURRENT_TIMESTAMP
    WHERE id = new_event_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Helper function: get_event_detail
-- Retrieve event with all enrichment context (for API response)
-- ============================================================================
CREATE OR REPLACE FUNCTION get_event_detail(event_uuid UUID)
RETURNS TABLE(
    event_id UUID,
    acquisition_time TIMESTAMP WITH TIME ZONE,
    latitude NUMERIC,
    longitude NUMERIC,
    brightness NUMERIC,
    frp NUMERIC,
    confidence INTEGER,
    satellite TEXT,
    point GEOMETRY,
    status TEXT,
    pipeline_version TEXT,
    processed_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        te.id,
        te.acquisition_time,
        te.latitude,
        te.longitude,
        te.brightness,
        te.frp,
        te.confidence,
        te.satellite,
        te.point,
        te.status,
        te.pipeline_version,
        te.processed_at
    FROM thermal_events te
    WHERE te.id = event_uuid;
END;
$$ LANGUAGE plpgsql;
