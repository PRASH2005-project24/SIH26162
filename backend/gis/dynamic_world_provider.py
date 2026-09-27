"""
Google Dynamic World provider for Stage 1B GIS enrichment
Queries land-cover classification via Google Earth Engine
Graceful fallback when credentials unavailable
"""

import logging
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)

# Earth Engine dataset identifier
DYNAMIC_WORLD_DATASET = "GOOGLE/DYNAMICWORLD/V1"

# Land cover class definitions
LAND_COVER_CLASSES = {
    0: "water",
    1: "trees",
    2: "grass",
    3: "flooded_vegetation",
    4: "crops",
    5: "shrub_scrub",
    6: "built",
    7: "bare",
    8: "snow_ice",
}


import math

class DynamicWorldProvider:
    """
    Google Dynamic World land-cover provider.
    Handles credentials gracefully, returns demo fixtures if unavailable.
    Includes PostgreSQL caching to avoid redundant EE calls.
    """

    def __init__(self, db=None, config=None):
        # Support both legacy usage (db, config) and the standalone verification
        # pattern used in tests (config only).
        if config is None:
            config = db
            db = None

        self.db = db
        self.config = config
        if self.config is None:
            raise ValueError("DynamicWorldProvider requires a Config instance")

        self.ee_client = None
        self.credentials_available = False
        self.cache_ttl = 30 * 24 * 3600  # 30 days cache for land cover
        self._initialize_earth_engine()

    @staticmethod
    def _has_usable_land_cover(data: Dict[str, Any]) -> bool:
        label = data.get("land_cover_label")
        probabilities = data.get("class_probabilities") or {}
        expected_classes = set(LAND_COVER_CLASSES.values())

        if label not in expected_classes or set(probabilities) != expected_classes:
            return False

        try:
            values = [float(probabilities[class_name]) for class_name in expected_classes]
        except (TypeError, ValueError):
            return False

        return all(math.isfinite(value) and 0.0 <= value <= 1.0 for value in values) and sum(values) > 0

    def _initialize_earth_engine(self):
        """
        Attempt to initialize Earth Engine client.
        Gracefully handle missing credentials.
        """
        try:
            import ee

            # Check if Earth Engine project ID is configured
            project_id = self.config.EARTH_ENGINE_PROJECT_ID
            if not project_id or project_id == "":
                logger.warning(
                    "⚠️  EARTH_ENGINE_PROJECT_ID not configured. "
                    "Dynamic World queries unavailable. Using demo mode."
                )
                self.credentials_available = False
                return

            try:
                # Try to authenticate using application default credentials
                ee.Initialize(
                    opt_url="https://earthengine-highvolume.googleapis.com",
                    project=project_id
                )
                self.ee_client = ee
                self.credentials_available = True
                logger.info(f"✓ Earth Engine initialized for project {project_id}")

            except ee.EEException as e:
                logger.warning(
                    f"⚠️  Earth Engine authentication failed: {e}\n"
                    f"To use Dynamic World queries:\n"
                    f"1. Set EARTH_ENGINE_PROJECT_ID environment variable\n"
                    f"2. Authenticate with: gcloud auth application-default login\n"
                    f"3. Or set GOOGLE_APPLICATION_CREDENTIALS to your service account JSON\n"
                    f"Using demo mode for now."
                )
                self.credentials_available = False

        except ImportError:
            logger.warning(
                "⚠️  Google Earth Engine Python package not installed.\n"
                "Install with: pip install earthengine-api\n"
                "Using demo mode for now."
            )
            self.credentials_available = False

        except Exception as e:
            logger.warning(f"⚠️  Error initializing Earth Engine: {e}")
            self.credentials_available = False

    async def get_land_cover(
        self,
        event_lat: float,
        event_lon: float,
        acquisition_date: str,
        buffer_km: float = 0.5
    ) -> Dict[str, Any]:
        """
        Get land-cover classification for a location from Dynamic World.
        Returns land-cover label, probabilities, and metadata.
        Gracefully returns demo data if credentials unavailable.
        Uses PostgreSQL cache.
        """
        # Create cache key
        tile_x, tile_y = self._tile_from_point(event_lat, event_lon, zoom=14)
        dt = datetime.fromisoformat(acquisition_date.replace('Z', '+00:00'))
        qtype = f"dw_{dt.year}_{dt.month}"
        
        cache_key = f"14/{tile_x}/{tile_y}"
        cached_data = await self._get_cache(cache_key, qtype)
        
        if cached_data and self._has_usable_land_cover(cached_data):
            logger.debug(f"Dynamic World cache hit for {cache_key} {qtype}")
            cached_result = dict(cached_data)
            cached_result["source_coverage_state"] = cached_data.get("coverage_state")
            cached_result["coverage_state"] = "cached"
            return cached_result
        if cached_data:
            logger.info(f"Ignoring unusable Dynamic World cache entry for {cache_key} {qtype}")

        if not self.credentials_available:
            if getattr(self.config, "DEMO_MODE", False):
                logger.debug("Using demo Dynamic World response (credentials unavailable)")
                return self._get_demo_land_cover(event_lat, event_lon, acquisition_date)
            else:
                logger.warning("Dynamic World queries unavailable (credentials missing) and DEMO_MODE is False.")
                return {
                    "source": "google_dynamic_world",
                    "land_cover_label": None,
                    "class_probabilities": {},
                    "coverage_state": "source_unavailable",
                    "provider_version": "1.0.0",
                    "error": "Earth Engine credentials not configured"
                }

        try:
            result = await self._query_dynamic_world(
                event_lat, event_lon, acquisition_date, buffer_km
            )
            
            # Cache only usable results so missing pixels do not suppress future retries.
            if result.get("coverage_state") == "live" and self._has_usable_land_cover(result):
                await self._set_cache(cache_key, qtype, result)
            
            return result

        except Exception as e:
            logger.error(f"Error querying Dynamic World: {e}")
            return {
                "source": "google_dynamic_world",
                "land_cover_label": None,
                "class_probabilities": {},
                "coverage_state": "source_unavailable",
                "provider_version": "1.0.0",
                "error": str(e)
            }

    async def _query_dynamic_world(
        self,
        event_lat: float,
        event_lon: float,
        acquisition_date: str,
        buffer_km: float = 0.5
    ) -> Dict[str, Any]:
        """
        Query Dynamic World dataset via Earth Engine.
        """
        import ee

        try:
            # Parse acquisition date
            acq_dt = datetime.fromisoformat(acquisition_date.replace('Z', '+00:00'))

            # Create point geometry
            point = ee.Geometry.Point([event_lon, event_lat])

            # Buffer for analysis
            buffer_m = buffer_km * 1000
            buffered_point = point.buffer(buffer_m)

            # Query Dynamic World
            dw = ee.ImageCollection(DYNAMIC_WORLD_DATASET)

            acquisition_ee_date = ee.Date(acq_dt.strftime("%Y-%m-%d"))

            def collection_for_window(window_days):
                start_date = (acq_dt - timedelta(days=window_days)).strftime("%Y-%m-%d")
                end_date = (acq_dt + timedelta(days=window_days + 1)).strftime("%Y-%m-%d")
                return (
                    dw
                    .filterDate(start_date, end_date)
                    .filterBounds(buffered_point)
                )

            def add_query_metadata(image):
                image = ee.Image(image)
                image_date = image.date()
                date_band = (
                    ee.Image.constant(image_date.millis())
                    .rename("dw_image_time")
                    .toInt64()
                    .updateMask(image.select("label").mask())
                )
                distance_days = image_date.difference(acquisition_ee_date, "day").abs()
                return image.addBands(date_band).set("_acquisition_distance_days", distance_days)

            query_date = datetime.utcnow().isoformat()
            def sample_collection(collection):
                # mosaic() uses the last unmasked pixel; sort farthest-first so
                # the closest valid scene to acquisition time has priority.
                image = (
                    collection
                    .map(add_query_metadata)
                    .sort("_acquisition_distance_days", False)
                    .mosaic()
                )

                for region, sampling_method in (
                    (point, "point"),
                    (point.buffer(30), "buffer_30m"),
                ):
                    sample = image.reduceRegion(
                        reducer=ee.Reducer.first(),
                        geometry=region,
                        scale=10,
                        bestEffort=True
                    )
                    sample_results = sample.getInfo() or {}
                    sample_label, sample_probs = self._parse_dw_results(sample_results)
                    if self._has_usable_land_cover({
                        "land_cover_label": sample_label,
                        "class_probabilities": sample_probs
                    }):
                        return sample_results, sample_label, sample_probs, sampling_method
                return None

            selected_window_days = 15
            selected_collection = collection_for_window(selected_window_days)
            has_scenes = selected_collection.size().getInfo() > 0
            sample_result = sample_collection(selected_collection) if has_scenes else None

            if sample_result is None:
                selected_window_days = 30
                selected_collection = collection_for_window(selected_window_days)
                has_scenes = selected_collection.size().getInfo() > 0
                sample_result = sample_collection(selected_collection) if has_scenes else None

            if sample_result is None:
                coverage_state = "no_valid_pixel" if has_scenes else "coverage_unknown"
                logger.info(
                    f"No usable Dynamic World pixel at {event_lat},{event_lon} "
                    f"within +/-{selected_window_days} days of {acquisition_date}"
                )
                return {
                    "source": "google_dynamic_world",
                    "land_cover_label": None,
                    "class_probabilities": {},
                    "acquisition_date": acquisition_date,
                    "query_date": query_date,
                    "coverage_state": coverage_state,
                    "temporal_window_days": selected_window_days,
                    "provider_version": "1.0.0",
                    "dataset_id": DYNAMIC_WORLD_DATASET
                }

            results, label, probs, sampling_method = sample_result

            image_timestamp = results.get("dw_image_time")
            if isinstance(image_timestamp, list):
                image_timestamp = image_timestamp[0] if image_timestamp else None
            image_date = (
                datetime.fromtimestamp(float(image_timestamp) / 1000, tz=timezone.utc)
                .strftime("%Y-%m-%d")
                if image_timestamp is not None else None
            )
            image_age_days = (
                abs((datetime.strptime(image_date, "%Y-%m-%d").date() - acq_dt.date()).days)
                if image_date is not None else None
            )

            return {
                "source": "google_dynamic_world",
                "land_cover_label": label,
                "class_probabilities": probs,
                "image_date": image_date,
                "acquisition_date": acquisition_date,
                "query_date": query_date,
                "sampling_method": sampling_method,
                "temporal_window_days": selected_window_days,
                "image_age_days": image_age_days,
                "coverage_state": "live",
                "provider_version": "1.0.0",
                "dataset_id": DYNAMIC_WORLD_DATASET
            }

        except Exception as e:
            logger.error(f"Error in Dynamic World query: {e}")
            raise

    def _parse_dw_results(self, results: Dict[str, Any]) -> Tuple[Optional[str], Dict[str, float]]:
        """
        Parse Earth Engine sample results to extract land-cover class and probabilities.

        Based on actual Dynamic World response format from our tests:
        {
            'label': [class_index],  # e.g., [6] for 'built'
            'water': [probability],
            'trees': [probability],
            'grass': [probability],
            'flooded_vegetation': [probability],
            'crops': [probability],
            'shrub_and_scrub': [probability],
            'built': [probability],
            'bare': [probability],
            'snow_and_ice': [probability]
        }

        Note: The class names in the actual response match our LAND_COVER_CLASSES values
        except for 'shrub_and_scrub' vs 'shrub_scrub' and 'snow_and_ice' vs 'snow_ice'
        """
        try:
            if not results:
                logger.debug("No results in Earth Engine response")
                return None, {}

            # Extract classification index (label band)
            classification_idx = results.get('label')
            if classification_idx is None:
                logger.debug("No classification data in Earth Engine response")
                return None, {}

            # Convert to int if it's a list
            if isinstance(classification_idx, list) and len(classification_idx) > 0:
                classification_idx = int(classification_idx[0])
            else:
                classification_idx = int(classification_idx)

            # Get dominant class label
            dominant_label = LAND_COVER_CLASSES.get(classification_idx, "unknown")
            if dominant_label == "unknown":
                return None, {}

            # Extract probability values for each class
            # The actual band names in the response match our LAND_COVER_CLASSES
            # with minor naming differences we need to handle
            class_probs = {}
            observed_probabilities = 0
            for class_idx, class_label in LAND_COVER_CLASSES.items():
                # Map our internal class names to the actual band names in Earth Engine response
                band_name_map = {
                    'shrub_scrub': 'shrub_and_scrub',
                    'snow_ice': 'snow_and_ice'
                }
                actual_band_name = band_name_map.get(class_label, class_label)

                prob_value = results.get(actual_band_name)

                if prob_value is not None:
                    if isinstance(prob_value, list) and len(prob_value) > 0:
                        prob_value = float(prob_value[0])
                    else:
                        prob_value = float(prob_value)
                    class_probs[class_label] = round(prob_value, 4)
                    observed_probabilities += 1
                else:
                    # If the exact band name isn't found, try without mapping
                    prob_value = results.get(class_label)
                    if prob_value is not None:
                        if isinstance(prob_value, list) and len(prob_value) > 0:
                            prob_value = float(prob_value[0])
                        else:
                            prob_value = float(prob_value)
                        class_probs[class_label] = round(prob_value, 4)
                        observed_probabilities += 1
                    else:
                        class_probs[class_label] = 0.0

            if observed_probabilities != len(LAND_COVER_CLASSES):
                logger.debug("Incomplete Dynamic World probability bands in Earth Engine response")
                return None, {}

            # Normalize probabilities to sum to 1.0 (they should already sum to ~1.0)
            total_prob = sum(class_probs.values())
            if total_prob <= 0:
                logger.debug("Dynamic World response contains no probability mass")
                return None, {}
            class_probs = {k: round(v / total_prob, 4) for k, v in class_probs.items()}

            logger.debug(
                f"Parsed Dynamic World results: "
                f"dominant={dominant_label} (idx={classification_idx}), "
                f"probs={class_probs}"
            )

            return dominant_label, class_probs

        except Exception as e:
            logger.debug(f"Error parsing Dynamic World results: {e}")
            return None, {}

    def _get_demo_land_cover(
        self,
        event_lat: float,
        event_lon: float,
        acquisition_date: str
    ) -> Dict[str, Any]:
        """
        Return demo land-cover data for testing/development.
        """
        # Simple demo logic: return different classes based on location
        import random

        # Pune industrial areas tend to have "built" classification
        if 18.5 < event_lat < 18.8 and 73.5 < event_lon < 74.0:
            demo_class = "built"
            demo_probs = {
                "water": 0.02,
                "trees": 0.05,
                "grass": 0.08,
                "flooded_vegetation": 0.01,
                "crops": 0.03,
                "shrub_scrub": 0.04,
                "built": 0.68,
                "bare": 0.07,
                "snow_ice": 0.02,
            }
        else:
            # Random demo data for other areas
            classes = list(LAND_COVER_CLASSES.values())
            demo_class = random.choice(classes)
            demo_probs = {c: random.uniform(0.05, 0.25) for c in classes}
            # Normalize probabilities
            total = sum(demo_probs.values())
            demo_probs = {c: (v / total) for c, v in demo_probs.items()}

        return {
            "source": "google_dynamic_world",
            "land_cover_label": demo_class,
            "class_probabilities": demo_probs,
            "acquisition_date": acquisition_date,
            "query_date": datetime.utcnow().isoformat(),
            "coverage_state": "demo_mode",
            "provider_version": "1.0.0",
            "note": "Demo data - Earth Engine credentials not configured"
        }

    async def _get_cache(self, cache_key: str, query_type: str) -> Optional[Dict]:
        """Get cached query result from PostgreSQL if not expired"""
        if self.db is None:
            return None

        try:
            result = await self.db.execute_one(
                """
                SELECT response_json, expires_at
                FROM osm_cache
                WHERE tile_x = :tile_x AND tile_y = :tile_y AND tile_z = :tile_z
                  AND query_type = :qtype
                """,
                {
                    "tile_x": int(cache_key.split('/')[1]),
                    "tile_y": int(cache_key.split('/')[2]),
                    "tile_z": int(cache_key.split('/')[0]),
                    "qtype": query_type
                }
            )

            if result:
                expires_at = datetime.fromisoformat(result["expires_at"])
                if datetime.utcnow() < expires_at:
                    return json.loads(result["response_json"])

            return None

        except Exception as e:
            logger.debug(f"Error retrieving Dynamic World cache: {e}")
            return None

    async def _set_cache(self, cache_key: str, query_type: str, data: Dict):
        """Store query result in PostgreSQL cache (using osm_cache table)"""
        if self.db is None:
            return

        try:
            tile_z, tile_x, tile_y = map(int, cache_key.split('/'))
            now_dt = datetime.utcnow()
            expires_at = now_dt + timedelta(seconds=self.cache_ttl)

            update_query = """
                UPDATE osm_cache
                SET response_json = :response, expires_at = :expires, created_at = :created
                WHERE tile_x = :tile_x AND tile_y = :tile_y AND tile_z = :tile_z AND query_type = :qtype
                RETURNING id
            """
            result = await self.db.execute(
                update_query,
                {
                    "tile_x": tile_x,
                    "tile_y": tile_y,
                    "tile_z": tile_z,
                    "qtype": query_type,
                    "response": json.dumps(data),
                    "expires": expires_at,
                    "created": now_dt
                }
            )

            if not result:
                insert_query = """
                    INSERT INTO osm_cache
                    (id, tile_x, tile_y, tile_z, query_type, response_json, expires_at, created_at)
                    VALUES (:id, :tile_x, :tile_y, :tile_z, :qtype, :response, :expires, :created)
                """
                await self.db.execute_update(
                    insert_query,
                    {
                        "id": str(uuid4()),
                        "tile_x": tile_x,
                        "tile_y": tile_y,
                        "tile_z": tile_z,
                        "qtype": query_type,
                        "response": json.dumps(data),
                        "expires": expires_at,
                        "created": now_dt
                    }
                )

        except Exception as e:
            logger.warning(f"Error caching Dynamic World data: {e}")

    @staticmethod
    def _tile_from_point(lat: float, lon: float, zoom: int = 15) -> Tuple[int, int]:
        """Convert a lat/lon point to a tile coordinate (tile_x, tile_y) at given zoom level"""
        n = 2 ** zoom
        x = int((lon + 180) / 360 * n)
        y = int((1 - (math.sin(math.radians(lat)) + 1) / 2) * n)
        return (x, y)