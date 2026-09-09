"""
Stage 1B: GIS Enrichment Pipeline
Matches thermal events with OSM features and land cover data
Populates event_spatial_enrichment table with confidence scoring
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from uuid import uuid4
import math
import json

from backend.database import Database
from backend.config import Config
from backend.gis.osm_provider import OSMProvider
from backend.gis.dynamic_world_provider import DynamicWorldProvider

logger = logging.getLogger(__name__)


class GISEnrichmentEngine:
    """
    Core enrichment engine that:
    1. Queries OSM for nearby industrial zones and water features
    2. Queries Dynamic World for land cover classification
    3. Computes spatial metrics and confidence scores
    4. Stores results in event_spatial_enrichment table
    """

    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config
        self.osm_provider = OSMProvider(db, config)
        self.dw_provider = DynamicWorldProvider(db, config)

    async def enrich_event(self, event_id: str) -> Dict[str, Any]:
        """
        Enrich a single thermal event with GIS data.
        Returns enrichment result with confidence scores.
        """
        try:
            # Fetch event from database
            event = await self.db.execute_one(
                """
                SELECT id, latitude, longitude, acquisition_time, brightness, frp, confidence
                FROM thermal_events
                WHERE id = :event_id
                """,
                {"event_id": event_id}
            )

            if not event:
                logger.warning(f"Event {event_id} not found")
                return {"status": "error", "reason": "event_not_found"}

            # Extract event data and convert Decimal to float
            event_lat = float(event["latitude"])
            event_lon = float(event["longitude"])
            acq_time = event["acquisition_time"]
            brightness = float(event["brightness"])
            frp = float(event["frp"])
            event_confidence = int(event["confidence"])

            logger.info(f"Enriching event {event_id} at ({event_lat}, {event_lon})")

            # Query OSM data
            industrial_data = await self.osm_provider.get_industrial_features(
                event_lat, event_lon, buffer_km=5.0
            )
            water_data = await self.osm_provider.get_water_features(
                event_lat, event_lon, buffer_km=2.0
            )

            # Query land cover
            land_cover_data = await self.dw_provider.get_land_cover(
                event_lat, event_lon, acq_time
            )

            # Analyze industrial zone proximity
            inside_industrial = self._check_inside_industrial(
                event_lat, event_lon, industrial_data["features"]
            )
            nearest_feature, nearest_distance = self._find_nearest_feature(
                event_lat, event_lon, industrial_data["features"]
            )
            feature_count_1km = self._count_features_within(
                event_lat, event_lon, industrial_data["features"], 1.0
            )

            # Check for water proximity
            nearby_water = len(water_data.get("features", [])) > 0

            # Extract land cover
            land_cover_label = land_cover_data.get("land_cover_label")
            land_cover_probs = land_cover_data.get("class_probabilities", {})

            # Compute enrichment confidence score
            confidence_score = self._compute_enrichment_confidence(
                brightness=brightness,
                frp=frp,
                event_confidence=event_confidence,
                inside_industrial=inside_industrial,
                nearest_distance=nearest_distance,
                land_cover_label=land_cover_label,
                has_water=nearby_water,
                osm_coverage=industrial_data.get("coverage_state"),
                dw_coverage=land_cover_data.get("coverage_state")
            )

            # Store enrichment result
            enrichment_id = str(uuid4())
            await self.db.execute_update(
                """
                INSERT INTO event_spatial_enrichment (
                    id, event_id, source_name,
                    inside_industrial_zone,
                    nearest_feature_id,
                    nearest_feature_distance_m,
                    feature_count_1km,
                    nearby_water,
                    land_cover_label,
                    land_cover_probabilities_json,
                    acquisition_date,
                    query_date,
                    coverage_state,
                    provider_version,
                    computation_time_ms,
                    rule_version
                ) VALUES (
                    :id, :event_id, 'gis_enrichment',
                    :inside_industrial,
                    :nearest_feature_id,
                    :nearest_distance,
                    :feature_count_1km,
                    :nearby_water,
                    :land_cover_label,
                    :land_cover_probs,
                    :acq_date,
                    :query_date,
                    :coverage_state,
                    '1.0.0',
                    :computation_time,
                    '1.0.0'
                )
                """,
                {
                    "id": enrichment_id,
                    "event_id": event_id,
                    "inside_industrial": inside_industrial,
                    "nearest_feature_id": str(nearest_feature["osm_id"]) if nearest_feature else None,
                    "nearest_distance": nearest_distance,
                    "feature_count_1km": feature_count_1km,
                    "nearby_water": nearby_water,
                    "land_cover_label": land_cover_label,
                    "land_cover_probs": json.dumps(land_cover_probs) if land_cover_probs else "{}",
                    "acq_date": acq_time,
                    "query_date": datetime.utcnow().isoformat(),
                    "coverage_state": f"osm:{industrial_data.get('coverage_state')},dw:{land_cover_data.get('coverage_state')}",
                    "computation_time": 0  # Would be measured in real implementation
                }
            )

            logger.info(
                f"✓ Enriched event {event_id} - "
                f"industrial:{inside_industrial}, water:{nearby_water}, "
                f"land_cover:{land_cover_label}, confidence:{confidence_score:.2f}"
            )

            return {
                "status": "success",
                "event_id": event_id,
                "enrichment_id": enrichment_id,
                "inside_industrial": inside_industrial,
                "nearby_water": nearby_water,
                "land_cover_label": land_cover_label,
                "nearest_distance_m": nearest_distance,
                "confidence_score": confidence_score,
                "osm_coverage": industrial_data.get("coverage_state"),
                "dw_coverage": land_cover_data.get("coverage_state")
            }

        except Exception as e:
            logger.error(f"Error enriching event {event_id}: {e}", exc_info=True)
            return {"status": "error", "reason": str(e)}

    async def enrich_batch(self, event_ids: list = None, limit: int = 100) -> Dict[str, Any]:
        """
        Enrich a batch of events.
        If event_ids is None, processes unenriched events.
        """
        try:
            # Get unenriched events if none specified
            if event_ids is None:
                query = """
                    SELECT te.id
                    FROM thermal_events te
                    LEFT JOIN event_spatial_enrichment ese ON te.id = ese.event_id
                    WHERE ese.id IS NULL AND te.status = 'active'
                    LIMIT :limit
                """
                results = await self.db.execute(query, {"limit": limit})
                event_ids = [r["id"] for r in results]

            logger.info(f"Processing enrichment batch for {len(event_ids)} events")

            results = []
            for event_id in event_ids:
                result = await self.enrich_event(event_id)
                results.append(result)

            successful = sum(1 for r in results if r["status"] == "success")
            failed = sum(1 for r in results if r["status"] == "error")

            logger.info(
                f"Batch enrichment complete: {successful} successful, {failed} failed"
            )

            return {
                "batch_size": len(event_ids),
                "successful": successful,
                "failed": failed,
                "results": results
            }

        except Exception as e:
            logger.error(f"Error in batch enrichment: {e}", exc_info=True)
            return {"status": "error", "reason": str(e)}

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _check_inside_industrial(
        self,
        event_lat: float,
        event_lon: float,
        features: list,
        threshold_m: float = 100.0
    ) -> bool:
        """
        Check if event is inside industrial zone (within threshold distance).
        """
        for feature in features:
            if feature.get("latitude") is None or feature.get("longitude") is None:
                continue

            distance = self._haversine_distance(
                event_lat, event_lon,
                feature["latitude"], feature["longitude"]
            )

            if distance <= threshold_m:
                return True

        return False

    def _find_nearest_feature(
        self,
        event_lat: float,
        event_lon: float,
        features: list
    ) -> Tuple[Optional[Dict], Optional[float]]:
        """
        Find the nearest industrial feature to the event.
        Returns (feature_dict, distance_m) or (None, None).
        """
        if not features:
            return None, None

        min_distance = float('inf')
        nearest_feature = None

        for feature in features:
            if feature.get("latitude") is None or feature.get("longitude") is None:
                continue

            distance = self._haversine_distance(
                event_lat, event_lon,
                feature["latitude"], feature["longitude"]
            )

            if distance < min_distance:
                min_distance = distance
                nearest_feature = feature

        if nearest_feature is None:
            return None, None

        return nearest_feature, min_distance

    def _count_features_within(
        self,
        event_lat: float,
        event_lon: float,
        features: list,
        radius_km: float
    ) -> int:
        """
        Count features within a given radius (in km).
        """
        count = 0
        radius_m = radius_km * 1000.0

        for feature in features:
            if feature.get("latitude") is None or feature.get("longitude") is None:
                continue

            distance = self._haversine_distance(
                event_lat, event_lon,
                feature["latitude"], feature["longitude"]
            )

            if distance <= radius_m:
                count += 1

        return count

    def _compute_enrichment_confidence(
        self,
        brightness: float,
        frp: float,
        event_confidence: int,
        inside_industrial: bool,
        nearest_distance: Optional[float],
        land_cover_label: Optional[str],
        has_water: bool,
        osm_coverage: str,
        dw_coverage: str
    ) -> float:
        """
        Compute composite confidence score for enrichment result.
        Combines event confidence, spatial context, and data availability.
        """
        # Start with event confidence (0-1)
        base_score = event_confidence / 100.0

        # Adjust based on thermal intensity
        # Higher FRP = more likely to be real thermal event
        frp_factor = min(1.0, frp / 100.0)  # Normalize to 0-1
        base_score *= (0.7 + 0.3 * frp_factor)

        # Boost if inside industrial zone
        if inside_industrial:
            base_score *= 1.1  # 10% boost

        # Adjust based on nearest feature distance
        # Closer = more likely to be from industrial activity
        if nearest_distance is not None and nearest_distance < 10000:  # 10 km threshold
            proximity_factor = 1.0 - (nearest_distance / 10000.0)
            base_score *= (0.9 + 0.1 * proximity_factor)

        # Reduce confidence if no nearby water (unusual for false positives)
        if not has_water:
            base_score *= 0.95

        # Apply data availability penalty
        if osm_coverage not in ["live", "cached"]:
            base_score *= 0.9
        if dw_coverage not in ["live", "demo_mode", "cached"]:
            base_score *= 0.9

        # Clamp to [0, 1]
        return min(1.0, max(0.0, base_score))

    @staticmethod
    def _haversine_distance(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Calculate distance between two points on Earth using Haversine formula.
        Returns distance in meters.
        """
        R = 6371000  # Earth's radius in meters

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)

        a = (
            math.sin(dlat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        return R * c
