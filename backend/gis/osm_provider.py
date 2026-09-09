"""
OpenStreetMap/Overpass adapter for Stage 1B GIS enrichment
India-wide coverage with PostgreSQL caching and graceful fallback
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from uuid import uuid4
import hashlib
import math

import aiohttp
from backend.config import Config
from backend.database import Database

logger = logging.getLogger(__name__)

# Overpass API endpoint
OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"

# User-Agent for Overpass API requests
OVERPASS_USER_AGENT = "SIH26162-ThermalIntelligence/1.0 (+https://github.com/sih26162)"

# OSM query templates for industrial/infrastructure features
OSM_INDUSTRIAL_QUERY = """
[out:json][bbox:{south},{west},{north},{east}];
(
  node["landuse"="industrial"];
  node["landuse"="commercial"];
  node["industrial"~"factory|works|plant|warehouse"];
  node["power"~"plant|generator|substation"];
  node["facility"~"factory|warehouse|industrial"];
  way["landuse"="industrial"];
  way["landuse"="commercial"];
  way["industrial"~"factory|works|plant|warehouse"];
  way["power"~"plant|generator|substation"];
  relation["landuse"="industrial"];
  relation["landuse"="commercial"];
  relation["industrial"~"factory|works|plant|warehouse"];
);
out center;
"""

OSM_WATER_QUERY = """
[out:json][bbox:{south},{west},{north},{east}];
(
  node["natural"="water"];
  node["natural"="wetland"];
  way["natural"="water"];
  way["natural"="wetland"];
  way["waterway"~"river|stream|canal"];
  relation["natural"="water"];
  relation["natural"="wetland"];
);
out center;
"""


class OSMProvider:
    """
    OpenStreetMap data provider with India-wide Overpass queries,
    PostgreSQL caching, and graceful fallback.
    """

    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config
        self.cache_ttl = config.OSM_CACHE_TTL_SECONDS

    async def get_industrial_features(
        self,
        event_lat: float,
        event_lon: float,
        buffer_km: float = 5.0
    ) -> Dict[str, Any]:
        """
        Get industrial features near an event location across India.
        Returns dict with features, source metadata, and coverage state.
        """
        # Convert Decimal to float if needed
        event_lat = float(event_lat)
        event_lon = float(event_lon)

        # Verify event is within India
        india_bbox = self.config.india_bbox_tuple
        if not self._point_in_bbox(event_lat, event_lon, india_bbox):
            logger.warning(
                f"Event ({event_lat}, {event_lon}) outside India. "
                f"Skipping Overpass query."
            )
            return {
                "source": "osm_industrial",
                "features": [],
                "count": 0,
                "coverage_state": "outside_india",
                "source_freshness": None,
                "provider_version": "1.0.0"
            }

        # Create search bbox around event
        search_bbox = self._expand_bbox(event_lat, event_lon, buffer_km)

        # Try cache first
        tile_x, tile_y = self._tile_from_point(event_lat, event_lon, zoom=13)
        cache_key = self._tile_key(tile_x, tile_y, 13)
        cached_data = await self._get_cache(cache_key, "industrial")

        if cached_data:
            logger.debug(f"OSM industrial cache hit for tile {cache_key}")
            return {
                "source": "osm_industrial",
                "features": cached_data.get("features", []),
                "count": len(cached_data.get("features", [])),
                "coverage_state": "cached",
                "source_freshness": cached_data.get("query_time"),
                "provider_version": "1.0.0"
            }

        # Query Overpass API with timeout and retry
        try:
            features = await self._query_overpass_industrial(search_bbox)
            query_time = datetime.utcnow().isoformat()

            # Cache result
            await self._set_cache(
                cache_key,
                "industrial",
                {"features": features, "query_time": query_time}
            )

            return {
                "source": "osm_industrial",
                "features": features,
                "count": len(features),
                "coverage_state": "live",
                "source_freshness": query_time,
                "provider_version": "1.0.0"
            }

        except asyncio.TimeoutError:
            logger.warning(f"Overpass API timeout for industrial query near ({event_lat}, {event_lon})")
            return {
                "source": "osm_industrial",
                "features": [],
                "count": 0,
                "coverage_state": "query_timeout",
                "source_freshness": None,
                "provider_version": "1.0.0"
            }

        except Exception as e:
            logger.error(f"Overpass API error for industrial query: {e}")
            return {
                "source": "osm_industrial",
                "features": [],
                "count": 0,
                "coverage_state": "source_unavailable",
                "source_freshness": None,
                "provider_version": "1.0.0",
                "error": str(e)
            }

    async def get_water_features(
        self,
        event_lat: float,
        event_lon: float,
        buffer_km: float = 2.0
    ) -> Dict[str, Any]:
        """
        Get water features (rivers, lakes, wetlands) near an event across India.
        """
        # Convert Decimal to float if needed
        event_lat = float(event_lat)
        event_lon = float(event_lon)

        # Verify event is within India
        india_bbox = self.config.india_bbox_tuple
        if not self._point_in_bbox(event_lat, event_lon, india_bbox):
            return {
                "source": "osm_water",
                "features": [],
                "has_water": False,
                "coverage_state": "outside_india",
                "provider_version": "1.0.0"
            }

        # Create search bbox
        search_bbox = self._expand_bbox(event_lat, event_lon, buffer_km)

        # Try cache
        tile_x, tile_y = self._tile_from_point(event_lat, event_lon, zoom=14)
        cache_key = self._tile_key(tile_x, tile_y, 14)
        cached_data = await self._get_cache(cache_key, "water")

        if cached_data:
            return {
                "source": "osm_water",
                "features": cached_data.get("features", []),
                "has_water": len(cached_data.get("features", [])) > 0,
                "coverage_state": "cached",
                "provider_version": "1.0.0"
            }

        # Query Overpass
        try:
            features = await self._query_overpass_water(search_bbox)
            query_time = datetime.utcnow().isoformat()

            await self._set_cache(
                cache_key,
                "water",
                {"features": features, "query_time": query_time}
            )

            return {
                "source": "osm_water",
                "features": features,
                "has_water": len(features) > 0,
                "coverage_state": "live",
                "provider_version": "1.0.0"
            }

        except Exception as e:
            logger.error(f"Overpass API error for water query: {e}")
            return {
                "source": "osm_water",
                "features": [],
                "has_water": False,
                "coverage_state": "source_unavailable",
                "provider_version": "1.0.0"
            }

    async def _query_overpass_industrial(self, bbox: Tuple[float, float, float, float]) -> List[Dict]:
        """Query Overpass API for industrial features"""
        min_lat, min_lon, max_lat, max_lon = bbox

        query = OSM_INDUSTRIAL_QUERY.format(
            south=min_lat,
            west=min_lon,
            north=max_lat,
            east=max_lon
        )

        return await self._execute_overpass_query(query, bbox)

    async def _query_overpass_water(self, bbox: Tuple[float, float, float, float]) -> List[Dict]:
        """Query Overpass API for water features"""
        min_lat, min_lon, max_lat, max_lon = bbox

        query = OSM_WATER_QUERY.format(
            south=min_lat,
            west=min_lon,
            north=max_lat,
            east=max_lon
        )

        return await self._execute_overpass_query(query, bbox)

    async def _execute_overpass_query(
        self,
        query: str,
        bbox: Tuple[float, float, float, float],
        retries: int = 2
    ) -> List[Dict]:
        """Execute Overpass query with timeout, retry, and error handling"""
        for attempt in range(retries):
            try:
                async with aiohttp.ClientSession() as session:
                    timeout = aiohttp.ClientTimeout(total=30)
                    async with session.post(
                        OVERPASS_API_URL,
                        data=query,
                        timeout=timeout,
                        headers={"User-Agent": OVERPASS_USER_AGENT}
                    ) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            if resp.status == 429:
                                logger.warning(f"Overpass returned 429 Too Many Requests. Retrying...")
                                # Sleep longer for rate limits
                                await asyncio.sleep(5 * (attempt + 1))
                            raise Exception(f"Overpass returned {resp.status}: {error_text[:200]}")

                        response = await resp.json()
                        return self._parse_overpass_response(response)

            except asyncio.TimeoutError:
                if attempt < retries - 1:
                    logger.warning(f"Overpass timeout, retry {attempt + 1}/{retries}")
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise

            except Exception as e:
                if attempt < retries - 1:
                    logger.warning(f"Overpass error: {e}, retry {attempt + 1}/{retries}")
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise

    def _parse_overpass_response(self, response: Dict[str, Any]) -> List[Dict]:
        """Parse Overpass JSON response into feature list"""
        features = []

        elements = response.get("elements", [])
        for element in elements:
            try:
                feature = {
                    "osm_id": element.get("id"),
                    "osm_type": element.get("type"),  # node, way, relation
                    "latitude": element.get("lat"),
                    "longitude": element.get("lon"),
                    "tags": element.get("tags", {}),
                    "name": element.get("tags", {}).get("name", "unnamed"),
                }

                if feature["latitude"] is not None and feature["longitude"] is not None:
                    features.append(feature)

            except Exception as e:
                logger.debug(f"Error parsing Overpass element: {e}")
                continue

        return features

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
            logger.debug(f"Error retrieving OSM cache: {e}")
            return None

    async def _set_cache(self, cache_key: str, query_type: str, data: Dict):
        """Store query result in PostgreSQL cache"""
        try:
            tile_z, tile_x, tile_y = map(int, cache_key.split('/'))
            now_dt = datetime.utcnow()
            expires_at = now_dt + timedelta(seconds=self.cache_ttl)

            # First try to update existing cache entry
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

            # If no rows updated, insert new
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
            logger.warning(f"Error caching OSM data: {e}")

    def _point_in_bbox(self, lat: float, lon: float, bbox: Tuple[float, float, float, float]) -> bool:
        """Check if point is inside bounding box"""
        min_lat, min_lon, max_lat, max_lon = bbox
        return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon

    def _expand_bbox(self, lat: float, lon: float, buffer_km: float) -> Tuple[float, float, float, float]:
        """Expand a point to a bounding box with given buffer"""
        # Rough approximation: 1 degree ≈ 111 km at equator
        lat_offset = buffer_km / 111.0
        lon_offset = buffer_km / (111.0 * abs(math.cos(math.radians(lat))))

        return (
            lat - lat_offset,
            lon - lon_offset,
            lat + lat_offset,
            lon + lon_offset
        )

    @staticmethod
    def _tile_from_point(lat: float, lon: float, zoom: int = 15) -> Tuple[int, int]:
        """Convert a lat/lon point to a tile coordinate (tile_x, tile_y) at given zoom level"""
        n = 2 ** zoom
        x = int((lon + 180) / 360 * n)
        y = int((1 - (math.sin(math.radians(lat)) + 1) / 2) * n)
        return (x, y)

    @staticmethod
    def _tile_key(tile_x: int, tile_y: int, tile_z: int) -> str:
        """Create a cache key for a tile"""
        return f"{tile_z}/{tile_x}/{tile_y}"
