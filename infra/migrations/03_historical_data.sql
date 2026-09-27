-- Keep an append-only copy of every canonical thermal detection.
-- The trigger below also covers imports and future ingestion paths that do not
-- go through FIRMSCollector.
CREATE TABLE IF NOT EXISTS historical_data (
    event_id TEXT PRIMARY KEY,
    acquisition_time TIMESTAMP WITH TIME ZONE NOT NULL,
    satellite TEXT NOT NULL,
    instrument TEXT,
    brightness NUMERIC,
    brightness_rad NUMERIC,
    frp NUMERIC,
    confidence INTEGER,
    scan NUMERIC,
    track NUMERIC,
    day_night TEXT,
    latitude NUMERIC(10, 6) NOT NULL,
    longitude NUMERIC(11, 6) NOT NULL,
    point GEOMETRY(Point, 4326) NOT NULL,
    raw_payload_uri TEXT,
    raw_payload_sha256 TEXT,
    pipeline_version TEXT,
    ingestion_run_id TEXT,
    status TEXT,
    source_created_at TIMESTAMP WITH TIME ZONE,
    copied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_historical_event
        FOREIGN KEY (event_id) REFERENCES thermal_events(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_historical_data_acquisition_time
    ON historical_data(acquisition_time DESC);

CREATE INDEX IF NOT EXISTS idx_historical_data_geom
    ON historical_data USING GIST(point);

INSERT INTO historical_data (
    event_id, acquisition_time, satellite, instrument,
    brightness, brightness_rad, frp, confidence, scan, track, day_night,
    latitude, longitude, point, raw_payload_uri, raw_payload_sha256,
    pipeline_version, ingestion_run_id, status, source_created_at
)
SELECT
    id, acquisition_time, satellite, instrument,
    brightness, brightness_rad, frp, confidence, scan, track, day_night,
    latitude, longitude, point, raw_payload_uri, raw_payload_sha256,
    pipeline_version, ingestion_run_id, status, created_at
FROM thermal_events
ON CONFLICT (event_id) DO NOTHING;

CREATE OR REPLACE FUNCTION copy_thermal_event_to_history()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO historical_data (
        event_id, acquisition_time, satellite, instrument,
        brightness, brightness_rad, frp, confidence, scan, track, day_night,
        latitude, longitude, point, raw_payload_uri, raw_payload_sha256,
        pipeline_version, ingestion_run_id, status, source_created_at
    ) VALUES (
        NEW.id, NEW.acquisition_time, NEW.satellite, NEW.instrument,
        NEW.brightness, NEW.brightness_rad, NEW.frp, NEW.confidence,
        NEW.scan, NEW.track, NEW.day_night,
        NEW.latitude, NEW.longitude, NEW.point, NEW.raw_payload_uri,
        NEW.raw_payload_sha256, NEW.pipeline_version, NEW.ingestion_run_id,
        NEW.status, NEW.created_at
    )
    ON CONFLICT (event_id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS thermal_events_history_insert ON thermal_events;

CREATE TRIGGER thermal_events_history_insert
AFTER INSERT ON thermal_events
FOR EACH ROW
EXECUTE FUNCTION copy_thermal_event_to_history();