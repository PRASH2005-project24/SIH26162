"""
Google Dynamic World provider for Stage 1B GIS enrichment
Queries land-cover classification via Google Earth Engine
Graceful fallback when credentials unavailable
"""

import logging
import json
from datetime import datetime, timedelta
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

    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.ee_client = None
        self.credentials_available = False
        self.cache_ttl = 30 * 24 * 3600  # 30 days cache for land cover
        self._initialize_earth_engine()

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
        
        if cached_data:
            logger.debug(f"Dynamic World cache hit for {cache_key} {qtype}")
            return cached_data

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
            
            # Cache the result
            if result.get("coverage_state") != "source_unavailable":
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

            # Filter by date (within 30 days of acquisition)
            start_date = (acq_dt - timedelta(days=15)).strftime("%Y-%m-%d")
            end_date = (acq_dt + timedelta(days=15)).strftime("%Y-%m-%d")

            # Apply filters
            dw_filtered = (
                dw
                .filterDate(start_date, end_date)
                .filterBounds(buffered_point)
            )

            # Check if we have any images
            size = dw_filtered.size().getInfo()
            if size == 0:
                logger.warning(
                    f"No Dynamic World data available for {event_lat},{event_lon} "
                    f"near {acquisition_date}"
                )
                return {
                    "source": "google_dynamic_world",
                    "land_cover_label": None,
                    "class_probabilities": {},
                    "coverage_state": "coverage_unknown",
                    "provider_version": "1.0.0"
                }

            # Get the first image
            dw_image = dw_filtered.first()

            # Additional safety check
            if dw_image is None:
                logger.warning(
                    f"Dynamic World collection size > 0 but first() returned None for {event_lat},{event_lon}"
                )
                return {
                    "source": "google_dynamic_world",
                    "land_cover_label": None,
                    "class_probabilities": {},
                    "coverage_state": "coverage_unknown",
                    "provider_version": "1.0.0"
                }

            # Sample classification at point using reduceRegion
            # Based on our test, Dynamic World returns the actual class probabilities as direct band values
            # and a 'label' band with the classification index
            sample = dw_image.reduceRegion(
                reducer=ee.Reducer.first(),
                geometry=point,
                scale=10,  # 10m scale
                bestEffort=True
            )

            # Extract results
            results = sample.getInfo()

            # Parse results and extract dominant class and probabilities
            label, probs = self._parse_dw_results(results)

            # Get image date
            image_date = ee.Image(dw_image).date().format('YYYY-MM-dd').getInfo()

            return {
                "source": "google_dynamic_world",
                "land_cover_label": label,
                "class_probabilities": probs,
                "image_date": image_date,
                "acquisition_date": acquisition_date,
                "query_date": datetime.utcnow().isoformat(),
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

            # Extract probability values for each class
            # The actual band names in the response match our LAND_COVER_CLASSES
            # with minor naming differences we need to handle
            class_probs = {}
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
                else:
                    # If the exact band name isn't found, try without mapping
                    prob_value = results.get(class_label)
                    if prob_value is not None:
                        if isinstance(prob_value, list) and len(prob_value) > 0:
                            prob_value = float(prob_value[0])
                        else:
                            prob_value = float(prob_value)
                        class_probs[class_label] = round(prob_value, 4)
                    else:
                        class_probs[class_label] = 0.0

            # Normalize probabilities to sum to 1.0 (they should already sum to ~1.0)
            total_prob = sum(class_probs.values())
            if total_prob > 0:
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