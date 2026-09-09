"""
FIRMS (Fire Information Management System) data collector
Polls NASA FIRMS API and ingests thermal events with deterministic deduplication
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from uuid import uuid4
import hashlib
import json

import aiohttp
from dateutil import parser as date_parser

from backend.database import Database
from backend.config import Config
from backend.gis.thermal_source_grouper import ThermalSourceGrouper

logger = logging.getLogger(__name__)

# FIRMS API endpoint (VIIRS-375m and MODIS-1km available)
FIRMS_API_BASE = "https://firms.modaps.eosdis.nasa.gov/api/v1"


class FIRMSCollector:
    """Polls NASA FIRMS API and ingests thermal events"""

    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config
        self.polling_active = False

    async def poll_once(self) -> Dict:
        """
        Fetch thermal events from FIRMS API for the configured bounding box.
        Ingest with deduplication, enrich with GIS, and group into thermal sources.
        Returns ingestion run summary.
        """
        run_id = str(uuid4())
        run_start = datetime.utcnow()

        try:
            logger.info(f"🔄 Starting FIRMS poll (run_id={run_id})")

            if not self.config.FIRMS_MAP_KEY:
                msg = "FIRMS_MAP_KEY not configured"
                logger.warning(f"⚠️  {msg}. Skipping real API call.")
                await self._log_ingestion_run(
                    run_id=run_id,
                    success=False,
                    error_message=msg,
                    duration_seconds=0
                )
                return {
                    "success": False,
                    "reason": msg,
                    "run_id": run_id
                }

            # Fetch from FIRMS API
            events = await self._fetch_firms_events()
            logger.info(f"✓ Fetched {len(events)} raw FIRMS records")

            # Ingest with deduplication
            result = await self._ingest_events(events, run_id)

            # Group events into thermal sources (Stage 1C)
            grouper = ThermalSourceGrouper(self.db, self.config)

            # Fetch newly ingested events for grouping
            ingested_event_ids = await self._fetch_newly_ingested_events(run_id)
            if ingested_event_ids:
                ingested_events = await self._fetch_events_by_ids(ingested_event_ids)
                grouping_result = await grouper.group_events(ingested_events)
                logger.info(
                    f"✓ Thermal source grouping: "
                    f"created={grouping_result['sources_created']}, "
                    f"updated={grouping_result['sources_updated']}, "
                    f"grouped={grouping_result['events_grouped']}"
                )
                result.update({"thermal_grouping": grouping_result})

                # Trigger GIS enrichment for new events
                from backend.gis.enrichment_engine import GISEnrichmentEngine
                enrichment_engine = GISEnrichmentEngine(self.db, self.config)
                logger.info(f"🔄 Starting GIS enrichment for {len(ingested_event_ids)} new events")
                enrich_result = await enrichment_engine.enrich_batch(ingested_event_ids)
                logger.info(
                    f"✓ GIS enrichment complete: "
                    f"success={enrich_result.get('successful', 0)}, "
                    f"failed={enrich_result.get('failed', 0)}"
                )
                result.update({"enrichment": {"successful": enrich_result.get("successful", 0), "failed": enrich_result.get("failed", 0)}})

                # Trigger ML Classification for new events
                from backend.ml.classifier_engine import ClassifierEngine
                classifier_engine = ClassifierEngine(self.db, self.config)
                logger.info(f"🔄 Starting ML Classification for {len(ingested_event_ids)} new events")
                classification_result = await classifier_engine.classify_batch(ingested_event_ids)
                logger.info(
                    f"✓ ML Classification complete: "
                    f"success={classification_result.get('successful', 0)}, "
                    f"failed={classification_result.get('failed', 0)}"
                )
                result.update({"classification": {"successful": classification_result.get("successful", 0), "failed": classification_result.get("failed", 0)}})


            # Log ingestion run
            run_duration = (datetime.utcnow() - run_start).total_seconds()
            await self._log_ingestion_run(
                run_id=run_id,
                success=True,
                record_count=len(events),
                deduplicated_count=result.get("deduplicated_count", 0),
                duplicate_count=result.get("duplicate_count", 0),
                error_count=result.get("error_count", 0),
                duration_seconds=int(run_duration)
            )

            logger.info(
                f"✓ FIRMS poll complete: "
                f"fetched={len(events)}, "
                f"deduplicated={result.get('deduplicated_count', 0)}, "
                f"duplicates={result.get('duplicate_count', 0)}, "
                f"errors={result.get('error_count', 0)}, "
                f"duration={run_duration:.1f}s"
            )

            return {
                "success": True,
                "run_id": run_id,
                **result
            }

        except Exception as e:
            logger.error(f"❌ FIRMS poll failed: {e}", exc_info=True)

            # Log failed run
            run_duration = (datetime.utcnow() - run_start).total_seconds()
            await self._log_ingestion_run(
                run_id=run_id,
                success=False,
                error_message=str(e),
                duration_seconds=int(run_duration)
            )

            return {
                "success": False,
                "run_id": run_id,
                "error": str(e)
            }

    async def _fetch_firms_events(self) -> List[Dict]:
        """Fetch events from FIRMS API with retry/backoff logic"""
        min_lat, min_lon, max_lat, max_lon = self.config.firms_bbox_tuple

        # Use VIIRS 375m for higher resolution (available globally)
        url = (
            f"{FIRMS_API_BASE}/data/VIIRS_SNPP_NRT/"
            f"csv/{self.config.FIRMS_MAP_KEY}?"
            f"north={max_lat}&south={min_lat}&"
            f"east={max_lon}&west={min_lon}"
        )

        logger.debug(f"Fetching from FIRMS: bbox=({min_lat},{min_lon},{max_lat},{max_lon})")

        max_retries = 3
        backoff_seconds = 1

        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                        if resp.status == 200:
                            csv_text = await resp.text()
                            logger.info(f"✓ FIRMS API response received (attempt {attempt + 1})")

                            # Store raw payload
                            await self._store_raw_payload(csv_text)

                            # Parse CSV
                            events = self._parse_firms_csv(csv_text)
                            return events

                        elif resp.status in (429, 504):
                            # Rate limit or gateway error - retry
                            error_text = await resp.text()
                            logger.warning(
                                f"FIRMS API returned {resp.status} (attempt {attempt + 1}/{max_retries}): {error_text[:100]}"
                            )
                            if attempt < max_retries - 1:
                                await asyncio.sleep(backoff_seconds)
                                backoff_seconds *= 2
                                continue
                            else:
                                raise Exception(f"FIRMS API returned {resp.status} after {max_retries} retries")

                        else:
                            raise Exception(f"FIRMS API returned {resp.status}: {await resp.text()}")

            except asyncio.TimeoutError:
                logger.warning(f"FIRMS API request timed out (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(backoff_seconds)
                    backoff_seconds *= 2
                    continue
                else:
                    raise Exception(f"FIRMS API timeout after {max_retries} retries")

            except aiohttp.ClientError as e:
                logger.warning(f"FIRMS API client error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(backoff_seconds)
                    backoff_seconds *= 2
                    continue
                else:
                    raise

        raise Exception("FIRMS API fetch failed after all retries")

    async def _store_raw_payload(self, csv_text: str) -> Tuple[str, str]:
        """
        Store raw FIRMS CSV response in raw_payloads table.
        Returns (payload_uri, content_hash) for reference.
        """
        try:
            content_hash = hashlib.sha256(csv_text.encode()).hexdigest()
            payload_id = f"firms-{content_hash[:12]}"

            query = """
                INSERT INTO raw_payloads (
                    id, source, content_hash, payload_json, expires_at
                ) VALUES (
                    :id, 'FIRMS', :hash, :payload, :expires_at
                )
                ON CONFLICT(content_hash) DO NOTHING
            """

            expires_at = datetime.utcnow() + timedelta(days=365)

            await self.db.execute_update(query, {
                "id": payload_id,
                "hash": content_hash,
                "payload": csv_text,
                "expires_at": expires_at,
            })

            logger.debug(f"Stored raw FIRMS payload: {payload_id}")
            return (f"raw_payloads/{payload_id}", content_hash)

        except Exception as e:
            logger.warning(f"Failed to store raw payload: {e}")
            return (None, None)

    def _parse_firms_csv(self, csv_text: str) -> List[Dict]:
        """Parse FIRMS CSV response into event dictionaries"""
        lines = csv_text.strip().split("\n")
        if not lines:
            return []

        # First line is header
        header = lines[0].split(",")
        events = []

        for line in lines[1:]:
            if not line.strip():
                continue

            try:
                values = line.split(",")
                event = dict(zip(header, values))

                # Normalize field names (FIRMS uses specific headers)
                # Example: latitude, longitude, brightness, frp, confidence, acq_date, acq_time, etc.
                events.append(event)

            except Exception as e:
                logger.warning(f"Failed to parse FIRMS CSV line: {e}")
                continue

        return events

    def _is_point_in_india(self, latitude: float, longitude: float) -> bool:
        """
        Check if point is within India bounds.
        Returns True if within, False otherwise.
        """
        min_lat, min_lon, max_lat, max_lon = self.config.india_bbox_tuple
        return min_lat <= latitude <= max_lat and min_lon <= longitude <= max_lon

    async def _ingest_events(self, raw_events: List[Dict], run_id: str) -> Dict:
        """
        Ingest raw FIRMS events with deterministic deduplication.
        Dedup key: (latitude, longitude, acquisition_time, satellite)
        """
        deduplicated_count = 0
        duplicate_count = 0
        error_count = 0
        skipped_out_of_bounds = 0

        for raw_event in raw_events:
            try:
                # Normalize event
                event = self._normalize_event(raw_event, run_id)

                # Skip if outside India bounds
                if event is None:
                    skipped_out_of_bounds += 1
                    continue

                # Check for duplicate
                existing_event_id = await self._check_duplicate(event)

                if existing_event_id:
                    logger.debug(f"Duplicate detected: {event['dedup_key']}")
                    duplicate_count += 1

                    # Mark as duplicate in DB
                    await self._mark_duplicate(
                        canonical_id=existing_event_id,
                        dedup_key=event['dedup_key'],
                        run_id=run_id
                    )

                else:
                    # New canonical event
                    await self._insert_event(event, run_id)
                    deduplicated_count += 1

            except Exception as e:
                logger.warning(f"Error ingesting event: {e}")
                error_count += 1
                continue

        logger.info(f"Ingestion summary: deduplicated={deduplicated_count}, duplicates={duplicate_count}, errors={error_count}, out_of_bounds={skipped_out_of_bounds}")

        return {
            "deduplicated_count": deduplicated_count,
            "duplicate_count": duplicate_count,
            "error_count": error_count,
            "skipped_out_of_bounds": skipped_out_of_bounds
        }

    def _normalize_event(self, raw_event: Dict, run_id: str) -> Dict:
        """
        Normalize FIRMS CSV row to thermal_events schema.
        Handles missing fields gracefully.
        """
        # Parse acquisition time
        acq_date = raw_event.get("acq_date", "")
        acq_time = raw_event.get("acq_time", "")
        if acq_date and acq_time:
            acq_dt_str = f"{acq_date} {acq_time:0>4}"  # HHMM format
            try:
                acquisition_time = datetime.strptime(acq_dt_str, "%Y-%m-%d %H%M")
            except ValueError:
                acquisition_time = datetime.utcnow()
        else:
            acquisition_time = datetime.utcnow()

        latitude = float(raw_event.get("latitude", 0))
        longitude = float(raw_event.get("longitude", 0))

        # Validate event is within India bounds
        if not self._is_point_in_india(latitude, longitude):
            logger.debug(f"Event ({latitude}, {longitude}) outside India. Skipping.")
            return None

        # Dedup key: (lat, lon, acq_time, satellite)
        # Round to 4 decimals (~11m accuracy)
        dedup_key = f"{latitude:.4f},{longitude:.4f},{acquisition_time.isoformat()},{raw_event.get('satellite', 'unknown')}"

        brightness_val = raw_event.get("brightness") or raw_event.get("bright_ti4")
        brightness = float(brightness_val) if brightness_val else None

        frp = raw_event.get("frp")
        frp = float(frp) if frp else None

        confidence = raw_event.get("confidence")
        confidence = int(confidence) if confidence else None

        event = {
            "id": str(uuid4()),
            "acquisition_time": acquisition_time,  # Pass datetime object, not ISO string
            "satellite": raw_event.get("satellite", "unknown"),
            "instrument": raw_event.get("instrument", "VIIRS"),
            "brightness": brightness,
            "brightness_rad": raw_event.get("brightness_rad"),
            "frp": frp,
            "confidence": confidence,
            "scan": raw_event.get("scan"),
            "track": raw_event.get("track"),
            "day_night": raw_event.get("day_night", "N"),
            "latitude": latitude,
            "longitude": longitude,
            "point": f"POINT({longitude} {latitude})",
            "raw_payload_uri": None,  # Set after raw payload stored
            "raw_payload_sha256": None,
            "pipeline_version": "1.0.0",
            "ingestion_run_id": run_id,
            "dedup_key": dedup_key,
        }

        return event

    async def _check_duplicate(self, event: Dict) -> Optional[str]:
        """
        Check if event already exists by dedup key.
        Returns canonical event ID if exists, else None.
        """
        query = """
            SELECT id FROM thermal_events
            WHERE ROUND(latitude::NUMERIC, 4) = :lat
              AND ROUND(longitude::NUMERIC, 4) = :lon
              AND DATE_TRUNC('minute', acquisition_time) = DATE_TRUNC('minute', CAST(:acq_time AS TIMESTAMP))
              AND satellite = :satellite
              AND status != 'archived'
            LIMIT 1
        """

        result = await self.db.execute(query, {
            "lat": event["latitude"],
            "lon": event["longitude"],
            "acq_time": event["acquisition_time"],
            "satellite": event["satellite"],
        })

        return result[0]["id"] if result else None

    async def _insert_event(self, event: Dict, run_id: str):
        """Insert new canonical thermal event"""
        query = """
            INSERT INTO thermal_events (
                id, acquisition_time, satellite, instrument,
                brightness, brightness_rad, frp, confidence,
                scan, track, day_night,
                latitude, longitude,
                raw_payload_uri, raw_payload_sha256,
                pipeline_version, ingestion_run_id,
                status
            ) VALUES (
                :id, :acquisition_time, :satellite, :instrument,
                :brightness, :brightness_rad, :frp, :confidence,
                :scan, :track, :day_night,
                :latitude, :longitude,
                :raw_payload_uri, :raw_payload_sha256,
                :pipeline_version, :ingestion_run_id,
                'active'
            )
        """

        await self.db.execute_update(query, event)
        logger.debug(f"Inserted event: {event['id']}")

    async def _mark_duplicate(self, canonical_id: str, dedup_key: str, run_id: str):
        """Mark incoming duplicate event without creating new row"""
        logger.debug(f"Marking duplicate against canonical {canonical_id}")
        # In a full implementation, we'd create an event_duplicate_log table
        # For now, we just skip insertion

    async def _log_ingestion_run(
        self,
        run_id: str,
        success: bool,
        record_count: int = 0,
        deduplicated_count: int = 0,
        duplicate_count: int = 0,
        error_count: int = 0,
        error_message: str = None,
        duration_seconds: int = 0
    ):
        """Log FIRMS ingestion run metadata"""
        query = """
            INSERT INTO ingestion_runs (
                id, source, run_timestamp, bbox,
                record_count, deduplicated_count, duplicate_count, error_count,
                success, error_message, duration_seconds,
                next_scheduled_run
            ) VALUES (
                :id, 'FIRMS', :run_timestamp, :bbox,
                :record_count, :deduplicated_count, :duplicate_count, :error_count,
                :success, :error_message, :duration_seconds,
                :next_scheduled_run
            )
        """

        next_run = datetime.utcnow() + timedelta(
            minutes=self.config.FIRMS_POLLING_INTERVAL_MINUTES
        )

        await self.db.execute_update(query, {
            "id": run_id,
            "run_timestamp": datetime.utcnow(),
            "bbox": self.config.FIRMS_BBOX,
            "record_count": record_count,
            "deduplicated_count": deduplicated_count,
            "duplicate_count": duplicate_count,
            "error_count": error_count,
            "success": success,
            "error_message": error_message,
            "duration_seconds": duration_seconds,
            "next_scheduled_run": next_run,
        })

    async def start_polling_loop(self):
        """Start background polling loop"""
        self.polling_active = True
        logger.info(
            f"🔄 Starting FIRMS polling loop "
            f"(interval: {self.config.FIRMS_POLLING_INTERVAL_MINUTES} min)"
        )

        while self.polling_active:
            try:
                await self.poll_once()
                await asyncio.sleep(self.config.FIRMS_POLLING_INTERVAL_MINUTES * 60)
            except Exception as e:
                logger.error(f"Error in polling loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait before retry

    async def _fetch_newly_ingested_events(self, run_id: str) -> List[str]:
        """Fetch event IDs from a specific ingestion run"""
        query = """
            SELECT id FROM thermal_events
            WHERE ingestion_run_id = :run_id
            ORDER BY acquisition_time DESC
        """

        results = await self.db.execute(query, {"run_id": run_id})
        return [r["id"] for r in results] if results else []

    async def _fetch_events_by_ids(self, event_ids: List[str]) -> List[Dict]:
        """Fetch full event data by IDs"""
        if not event_ids:
            return []

        placeholders = ",".join([f"'{eid}'" for eid in event_ids])
        query = f"""
            SELECT id, latitude, longitude, acquisition_time, brightness, frp, confidence
            FROM thermal_events
            WHERE id IN ({placeholders})
        """

        results = await self.db.execute(query)
        return results if results else []
