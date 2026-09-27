--
-- PostgreSQL database dump
--

\restrict TRBb80RdZuUpzlfjVzAacynPqH9KdhthQXEYSz9UrE8byAh2h0lT3bojOKKeiGT

-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: postgis; Type: EXTENSION; Schema: -; Owner: -
--




--
-- Name: EXTENSION postgis; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION postgis IS 'PostGIS geometry and geography spatial types and functions';


--
-- Name: copy_thermal_event_to_history(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.copy_thermal_event_to_history() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
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
$$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: contextual_features; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.contextual_features (
    id text NOT NULL,
    source_name text NOT NULL,
    feature_type text NOT NULL,
    feature_id text,
    name text,
    latitude numeric,
    longitude numeric,
    bounds_minlat numeric,
    bounds_minlon numeric,
    bounds_maxlat numeric,
    bounds_maxlon numeric,
    properties_json text,
    imported_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    source_freshness text
);


--
-- Name: event_classifications; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.event_classifications (
    id text DEFAULT (gen_random_uuid())::text NOT NULL,
    event_id text NOT NULL,
    ml_predicted_class text,
    ml_confidence numeric,
    ml_probabilities_json jsonb,
    is_persistent boolean,
    persistence_date_count integer,
    persistence_duration_days integer,
    final_sih_category text,
    classification_status text DEFAULT 'success'::text NOT NULL,
    inference_error text,
    pipeline_version text,
    classification_timestamp timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: event_spatial_enrichment; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.event_spatial_enrichment (
    id text NOT NULL,
    event_id text NOT NULL,
    source_name text NOT NULL,
    inside_industrial_zone boolean,
    nearest_feature_id text,
    nearest_feature_distance_m numeric,
    feature_count_1km integer,
    nearby_water boolean,
    land_cover_label text,
    land_cover_probabilities_json text,
    acquisition_date text,
    query_date text,
    coverage_state text,
    provider_version text,
    computation_time_ms numeric,
    rule_version text DEFAULT '1.0.0'::text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: historical_data; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.historical_data (
    event_id text NOT NULL,
    acquisition_time timestamp with time zone NOT NULL,
    satellite text NOT NULL,
    instrument text,
    brightness numeric,
    brightness_rad numeric,
    frp numeric,
    confidence integer,
    scan numeric,
    track numeric,
    day_night text,
    latitude numeric(10,6) NOT NULL,
    longitude numeric(11,6) NOT NULL,
    point public.geometry(Point,4326) NOT NULL,
    raw_payload_uri text,
    raw_payload_sha256 text,
    pipeline_version text,
    ingestion_run_id text,
    status text,
    source_created_at timestamp with time zone,
    copied_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: ingestion_runs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ingestion_runs (
    id text NOT NULL,
    source text NOT NULL,
    run_timestamp timestamp without time zone NOT NULL,
    bbox text,
    record_count integer DEFAULT 0,
    deduplicated_count integer DEFAULT 0,
    duplicate_count integer DEFAULT 0,
    error_count integer DEFAULT 0,
    success boolean DEFAULT false,
    error_message text,
    duration_seconds integer,
    next_scheduled_run timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: osm_cache; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.osm_cache (
    id text NOT NULL,
    tile_x integer,
    tile_y integer,
    tile_z integer,
    query_type text,
    response_json text,
    expires_at timestamp without time zone,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: raw_payloads; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.raw_payloads (
    id text NOT NULL,
    source text NOT NULL,
    content_hash text,
    payload_json text,
    retention_days integer DEFAULT 365,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    expires_at timestamp without time zone
);


--
-- Name: source_health; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.source_health (
    id text NOT NULL,
    source_name text NOT NULL,
    status text DEFAULT 'unknown'::text NOT NULL,
    last_check timestamp without time zone,
    last_success timestamp without time zone,
    error_message text,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: thermal_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.thermal_events (
    id text NOT NULL,
    acquisition_time timestamp without time zone NOT NULL,
    satellite text NOT NULL,
    latitude numeric,
    longitude numeric,
    brightness numeric,
    frp numeric,
    confidence integer,
    day_night text,
    instrument text,
    scan numeric,
    track numeric,
    brightness_rad numeric,
    raw_payload_uri text,
    raw_payload_sha256 text,
    pipeline_version text DEFAULT '1.0.0'::text,
    processed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    ingestion_run_id text,
    status text DEFAULT 'active'::text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    point public.geometry(Point,4326),
    bright_ti5 numeric,
    confidence_class text,
    model_satellite text,
    source_satellite text
);


--
-- Name: thermal_source_events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.thermal_source_events (
    id text NOT NULL,
    source_id text NOT NULL,
    event_id text NOT NULL,
    associated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: thermal_sources; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.thermal_sources (
    id text NOT NULL,
    centroid_lat numeric NOT NULL,
    centroid_lon numeric NOT NULL,
    spatial_extent_meters numeric,
    first_detected timestamp without time zone NOT NULL,
    last_detected timestamp without time zone NOT NULL,
    active_days integer DEFAULT 1,
    event_count integer DEFAULT 1,
    detection_count integer DEFAULT 1,
    avg_frp numeric,
    max_frp numeric,
    avg_confidence numeric,
    spatial_threshold_meters integer DEFAULT 300,
    temporal_threshold_hours integer DEFAULT 48,
    source_type text DEFAULT 'uncertain'::text,
    confidence_score numeric DEFAULT 0.5,
    status text DEFAULT 'active'::text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


--
-- Name: contextual_features contextual_features_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.contextual_features
    ADD CONSTRAINT contextual_features_pkey PRIMARY KEY (id);


--
-- Name: event_classifications event_classifications_event_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_classifications
    ADD CONSTRAINT event_classifications_event_id_key UNIQUE (event_id);


--
-- Name: event_classifications event_classifications_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_classifications
    ADD CONSTRAINT event_classifications_pkey PRIMARY KEY (id);


--
-- Name: event_spatial_enrichment event_spatial_enrichment_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_spatial_enrichment
    ADD CONSTRAINT event_spatial_enrichment_pkey PRIMARY KEY (id);


--
-- Name: historical_data historical_data_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.historical_data
    ADD CONSTRAINT historical_data_pkey PRIMARY KEY (event_id);


--
-- Name: ingestion_runs ingestion_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingestion_runs
    ADD CONSTRAINT ingestion_runs_pkey PRIMARY KEY (id);


--
-- Name: osm_cache osm_cache_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.osm_cache
    ADD CONSTRAINT osm_cache_pkey PRIMARY KEY (id);


--
-- Name: raw_payloads raw_payloads_content_hash_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.raw_payloads
    ADD CONSTRAINT raw_payloads_content_hash_key UNIQUE (content_hash);


--
-- Name: raw_payloads raw_payloads_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.raw_payloads
    ADD CONSTRAINT raw_payloads_pkey PRIMARY KEY (id);


--
-- Name: source_health source_health_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.source_health
    ADD CONSTRAINT source_health_pkey PRIMARY KEY (id);


--
-- Name: source_health source_health_source_name_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.source_health
    ADD CONSTRAINT source_health_source_name_key UNIQUE (source_name);


--
-- Name: thermal_events thermal_events_latitude_longitude_acquisition_time_satellit_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.thermal_events
    ADD CONSTRAINT thermal_events_latitude_longitude_acquisition_time_satellit_key UNIQUE (latitude, longitude, acquisition_time, satellite);


--
-- Name: thermal_events thermal_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.thermal_events
    ADD CONSTRAINT thermal_events_pkey PRIMARY KEY (id);


--
-- Name: thermal_source_events thermal_source_events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.thermal_source_events
    ADD CONSTRAINT thermal_source_events_pkey PRIMARY KEY (id);


--
-- Name: thermal_source_events thermal_source_events_source_id_event_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.thermal_source_events
    ADD CONSTRAINT thermal_source_events_source_id_event_id_key UNIQUE (source_id, event_id);


--
-- Name: thermal_sources thermal_sources_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.thermal_sources
    ADD CONSTRAINT thermal_sources_pkey PRIMARY KEY (id);


--
-- Name: idx_classifications_event_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_classifications_event_id ON public.event_classifications USING btree (event_id);


--
-- Name: idx_classifications_sih_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_classifications_sih_category ON public.event_classifications USING btree (final_sih_category);


--
-- Name: idx_classifications_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_classifications_status ON public.event_classifications USING btree (classification_status);


--
-- Name: idx_classifications_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_classifications_time ON public.event_classifications USING btree (classification_timestamp DESC);


--
-- Name: idx_classifications_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_classifications_timestamp ON public.event_classifications USING btree (classification_timestamp DESC);


--
-- Name: idx_historical_data_acquisition_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_historical_data_acquisition_time ON public.historical_data USING btree (acquisition_time DESC);


--
-- Name: idx_historical_data_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_historical_data_geom ON public.historical_data USING gist (point);


--
-- Name: idx_ingestion_runs_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_ingestion_runs_source ON public.ingestion_runs USING btree (source);


--
-- Name: idx_thermal_events_acq_time; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_thermal_events_acq_time ON public.thermal_events USING btree (acquisition_time DESC);


--
-- Name: idx_thermal_events_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_thermal_events_active ON public.thermal_events USING btree (acquisition_time DESC) WHERE (status = 'active'::text);


--
-- Name: idx_thermal_events_bbox; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_thermal_events_bbox ON public.thermal_events USING gist (public.st_expand(point, (0.01)::double precision)) WHERE (status = 'active'::text);


--
-- Name: idx_thermal_events_date_bucket; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_thermal_events_date_bucket ON public.thermal_events USING btree (date_trunc('hour'::text, acquisition_time));


--
-- Name: idx_thermal_events_geom; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_thermal_events_geom ON public.thermal_events USING gist (point);

ALTER TABLE public.thermal_events CLUSTER ON idx_thermal_events_geom;


--
-- Name: idx_thermal_events_lat_lon; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_thermal_events_lat_lon ON public.thermal_events USING btree (latitude, longitude);


--
-- Name: idx_thermal_events_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_thermal_events_status ON public.thermal_events USING btree (status);


--
-- Name: idx_thermal_source_events_event; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_thermal_source_events_event ON public.thermal_source_events USING btree (event_id);


--
-- Name: idx_thermal_source_events_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_thermal_source_events_source ON public.thermal_source_events USING btree (source_id);


--
-- Name: idx_thermal_sources_location; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_thermal_sources_location ON public.thermal_sources USING btree (centroid_lat, centroid_lon);


--
-- Name: idx_thermal_sources_temporal; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_thermal_sources_temporal ON public.thermal_sources USING btree (first_detected DESC, last_detected DESC);


--
-- Name: thermal_events thermal_events_history_insert; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER thermal_events_history_insert AFTER INSERT ON public.thermal_events FOR EACH ROW EXECUTE FUNCTION public.copy_thermal_event_to_history();


--
-- Name: event_classifications fk_event; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.event_classifications
    ADD CONSTRAINT fk_event FOREIGN KEY (event_id) REFERENCES public.thermal_events(id) ON DELETE CASCADE;


--
-- Name: historical_data fk_historical_event; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.historical_data
    ADD CONSTRAINT fk_historical_event FOREIGN KEY (event_id) REFERENCES public.thermal_events(id) ON DELETE CASCADE;


--
-- Name: thermal_source_events thermal_source_events_event_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.thermal_source_events
    ADD CONSTRAINT thermal_source_events_event_id_fkey FOREIGN KEY (event_id) REFERENCES public.thermal_events(id);


--
-- Name: thermal_source_events thermal_source_events_source_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.thermal_source_events
    ADD CONSTRAINT thermal_source_events_source_id_fkey FOREIGN KEY (source_id) REFERENCES public.thermal_sources(id);


--
-- PostgreSQL database dump complete
--

\unrestrict TRBb80RdZuUpzlfjVzAacynPqH9KdhthQXEYSz9UrE8byAh2h0lT3bojOKKeiGT

