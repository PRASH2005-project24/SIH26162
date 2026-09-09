"""
Thermal Source Grouping - Stage 1C
Deterministic spatial-temporal clustering of thermal events
Groups repeated FIRMS observations into persistent thermal sources
"""

import logging
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from uuid import uuid4

from backend.database import Database
from backend.config import Config

logger = logging.getLogger(__name__)


class ThermalSourceGrouper:
    """
    Groups thermal events into persistent sources using deterministic
    spatial-temporal clustering (NOT ML-based).

    A thermal source represents repeated thermal detections in approximately
    the same location over multiple observations/days.
    """

    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config
        # Configuration in meters and hours
        self.spatial_threshold_m = int(
            config.__dict__.get("THERMAL_SOURCE_SPATIAL_THRESHOLD_M", 300)
        )
        self.temporal_threshold_h = int(
            config.__dict__.get("THERMAL_SOURCE_TEMPORAL_THRESHOLD_H", 48)
        )

    async def group_events(self, events: List[Dict]) -> Dict:
        """
        Group events into thermal sources.
        Performs spatial-temporal clustering on provided events.

        Returns dict with:
        - sources_created: int
        - sources_updated: int
        - events_grouped: int
        - errors: int
        """
        sources_created = 0
        sources_updated = 0
        events_grouped = 0
        errors = 0

        try:
            # Fetch all existing thermal sources
            existing_sources = await self._fetch_existing_sources()
            logger.info(f"Loaded {len(existing_sources)} existing thermal sources")

            # Process each event
            for event in events:
                try:
                    # Try to match to existing source
                    matching_source_id = await self._find_matching_source(
                        event, existing_sources
                    )

                    if matching_source_id:
                        # Assign to existing source
                        await self._assign_event_to_source(event, matching_source_id)
                        await self._update_source_statistics(matching_source_id)
                        sources_updated += 1
                        events_grouped += 1

                    else:
                        # Create new thermal source
                        new_source_id = await self._create_thermal_source(event)
                        if new_source_id:
                            sources_created += 1
                            events_grouped += 1
                            # Add to existing sources for future matching
                            existing_sources.append({
                                "id": new_source_id,
                                "centroid_lat": float(event["latitude"]),
                                "centroid_lon": float(event["longitude"]),
                                "first_detected": event["acquisition_time"],
                                "last_detected": event["acquisition_time"],
                            })

                except Exception as e:
                    logger.warning(f"Error grouping event {event.get('id')}: {e}")
                    errors += 1
                    continue

            logger.info(
                f"Grouping complete: "
                f"created={sources_created}, "
                f"updated={sources_updated}, "
                f"grouped={events_grouped}, "
                f"errors={errors}"
            )

            return {
                "sources_created": sources_created,
                "sources_updated": sources_updated,
                "events_grouped": events_grouped,
                "errors": errors,
            }

        except Exception as e:
            logger.error(f"Event grouping failed: {e}", exc_info=True)
            return {
                "sources_created": sources_created,
                "sources_updated": sources_updated,
                "events_grouped": events_grouped,
                "errors": errors + 1,
            }

    async def _fetch_existing_sources(self) -> List[Dict]:
        """Fetch all active thermal sources from database"""
        query = """
            SELECT id, centroid_lat, centroid_lon, first_detected, last_detected
            FROM thermal_sources
            WHERE status = 'active'
            ORDER BY last_detected DESC
        """

        results = await self.db.execute(query)
        return results if results else []

    async def _find_matching_source(
        self, event: Dict, existing_sources: List[Dict]
    ) -> Optional[str]:
        """
        Find if event matches any existing thermal source.
        Criteria:
        - Spatial: distance <= spatial_threshold_m
        - Temporal: time_diff <= temporal_threshold_h

        Returns source_id if match found, None otherwise.
        """
        event_lat = float(event["latitude"])
        event_lon = float(event["longitude"])
        event_time = event["acquisition_time"]

        for source in existing_sources:
            # Calculate spatial distance
            distance_m = self._haversine_distance(
                event_lat,
                event_lon,
                float(source["centroid_lat"]),
                float(source["centroid_lon"]),
            )

            # Check spatial threshold
            if distance_m > self.spatial_threshold_m:
                continue

            # Parse source last_detected time if string
            last_detected = source["last_detected"]
            if isinstance(last_detected, str):
                from dateutil import parser as date_parser
                last_detected = date_parser.isoparse(last_detected)

            # Calculate temporal difference
            if isinstance(event_time, str):
                from dateutil import parser as date_parser
                event_time = date_parser.isoparse(event_time)

            time_diff_h = abs((event_time - last_detected).total_seconds()) / 3600.0

            # Check temporal threshold
            if time_diff_h > self.temporal_threshold_h:
                continue

            # Match found!
            logger.debug(
                f"Event matched to source {source['id']}: "
                f"distance={distance_m:.1f}m, time_diff={time_diff_h:.1f}h"
            )
            return source["id"]

        return None

    async def _create_thermal_source(self, event: Dict) -> Optional[str]:
        """Create new thermal source from single event"""
        try:
            source_id = str(uuid4())
            acq_time = event["acquisition_time"]

            # Parse datetime if string
            if isinstance(acq_time, str):
                from dateutil import parser as date_parser
                acq_time = date_parser.isoparse(acq_time)

            query = """
                INSERT INTO thermal_sources (
                    id, centroid_lat, centroid_lon,
                    first_detected, last_detected, active_days,
                    event_count, detection_count,
                    avg_frp, max_frp, avg_confidence,
                    spatial_threshold_meters, temporal_threshold_hours,
                    source_type, confidence_score, status
                ) VALUES (
                    :id, :lat, :lon,
                    :first_det, :last_det, 1,
                    1, 1,
                    :frp, :frp, :confidence,
                    :spatial_thresh, :temporal_thresh,
                    'uncertain', 0.5, 'active'
                )
            """

            await self.db.execute_update(query, {
                "id": source_id,
                "lat": float(event["latitude"]),
                "lon": float(event["longitude"]),
                "first_det": acq_time,
                "last_det": acq_time,
                "frp": float(event.get("frp", 0)),
                "confidence": int(event.get("confidence", 50)),
                "spatial_thresh": self.spatial_threshold_m,
                "temporal_thresh": self.temporal_threshold_h,
            })

            # Link event to source
            await self._assign_event_to_source(event, source_id)

            logger.debug(f"Created new thermal source: {source_id}")
            return source_id

        except Exception as e:
            logger.warning(f"Failed to create thermal source: {e}")
            return None

    async def _assign_event_to_source(self, event: Dict, source_id: str):
        """Link thermal event to thermal source"""
        try:
            query = """
                INSERT INTO thermal_source_events (
                    id, source_id, event_id, associated_at
                ) VALUES (
                    :id, :source_id, :event_id, :assoc_at
                )
                ON CONFLICT DO NOTHING
            """

            await self.db.execute_update(query, {
                "id": str(uuid4()),
                "source_id": source_id,
                "event_id": event["id"],
                "assoc_at": datetime.utcnow(),
            })

        except Exception as e:
            logger.warning(f"Failed to assign event to source: {e}")

    async def _update_source_statistics(self, source_id: str):
        """Recalculate thermal source statistics from linked events"""
        try:
            query = """
                UPDATE thermal_sources
                SET
                    event_count = (
                        SELECT COUNT(*)
                        FROM thermal_source_events
                        WHERE source_id = :source_id
                    ),
                    first_detected = (
                        SELECT MIN(te.acquisition_time)
                        FROM thermal_source_events tse
                        JOIN thermal_events te ON tse.event_id = te.id
                        WHERE tse.source_id = :source_id
                    ),
                    last_detected = (
                        SELECT MAX(te.acquisition_time)
                        FROM thermal_source_events tse
                        JOIN thermal_events te ON tse.event_id = te.id
                        WHERE tse.source_id = :source_id
                    ),
                    active_days = (
                        SELECT COUNT(DISTINCT DATE(te.acquisition_time))
                        FROM thermal_source_events tse
                        JOIN thermal_events te ON tse.event_id = te.id
                        WHERE tse.source_id = :source_id
                    ),
                    avg_frp = (
                        SELECT AVG(te.frp)
                        FROM thermal_source_events tse
                        JOIN thermal_events te ON tse.event_id = te.id
                        WHERE tse.source_id = :source_id AND te.frp IS NOT NULL
                    ),
                    max_frp = (
                        SELECT MAX(te.frp)
                        FROM thermal_source_events tse
                        JOIN thermal_events te ON tse.event_id = te.id
                        WHERE tse.source_id = :source_id AND te.frp IS NOT NULL
                    ),
                    avg_confidence = (
                        SELECT AVG(te.confidence)
                        FROM thermal_source_events tse
                        JOIN thermal_events te ON tse.event_id = te.id
                        WHERE tse.source_id = :source_id AND te.confidence IS NOT NULL
                    ),
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :source_id
            """

            await self.db.execute_update(query, {"source_id": source_id})

        except Exception as e:
            logger.warning(f"Failed to update source statistics: {e}")

    def _haversine_distance(
        self, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Calculate great-circle distance between two points in meters.
        Uses Haversine formula for spherical Earth.
        """
        # Earth radius in meters
        R = 6371000.0

        # Convert to radians
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)

        # Differences
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad

        # Haversine formula
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        return R * c
