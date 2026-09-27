ALTER TABLE thermal_events
    ADD COLUMN IF NOT EXISTS bright_ti5 NUMERIC,
    ADD COLUMN IF NOT EXISTS confidence_class TEXT,
    ADD COLUMN IF NOT EXISTS model_satellite TEXT,
    ADD COLUMN IF NOT EXISTS source_satellite TEXT;