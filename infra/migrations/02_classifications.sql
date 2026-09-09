CREATE TABLE IF NOT EXISTS event_classifications (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    event_id TEXT NOT NULL UNIQUE,

    -- ML Raw Output (3-class Random Forest)
    ml_predicted_class TEXT,
    ml_confidence NUMERIC,
    ml_probabilities_json JSONB,
    
    -- Persistence Analysis
    is_persistent BOOLEAN,
    persistence_date_count INTEGER,
    persistence_duration_days INTEGER,

    -- Final SIH Classification
    final_sih_category TEXT,
    
    -- Status and Metadata
    classification_status TEXT NOT NULL DEFAULT 'success', -- 'success', 'failed'
    inference_error TEXT,
    pipeline_version TEXT,
    
    classification_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_event FOREIGN KEY (event_id) REFERENCES thermal_events(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_classifications_event_id ON event_classifications(event_id);
CREATE INDEX IF NOT EXISTS idx_classifications_status ON event_classifications(classification_status);
CREATE INDEX IF NOT EXISTS idx_classifications_timestamp ON event_classifications(classification_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_classifications_sih_category ON event_classifications(final_sih_category);
