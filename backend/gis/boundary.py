"""
India Sovereign Boundary validation utility
Uses prepared Shapely MultiPolygon loaded from data/india_boundary.geojson
for microsecond point-in-polygon verification.
"""

import os
import json
import logging
from shapely.geometry import shape, Point
from shapely.prepared import prep

logger = logging.getLogger(__name__)

_GEOJSON_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "india_boundary.geojson")
)

_prepared_boundary = None

# Rough bounding box for ultra-fast rejection
MIN_LON, MAX_LON = 68.1, 97.4
MIN_LAT, MAX_LAT = 6.7, 37.1


def get_india_boundary():
    """Load and prepare India boundary geometry"""
    global _prepared_boundary
    if _prepared_boundary is None:
        try:
            if os.path.exists(_GEOJSON_PATH):
                with open(_GEOJSON_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                raw_geom = shape(data["features"][0]["geometry"])
                _prepared_boundary = prep(raw_geom)
                logger.info(f"Loaded prepared India boundary from {_GEOJSON_PATH}")
            else:
                logger.warning(f"Boundary file not found at {_GEOJSON_PATH}")
        except Exception as e:
            logger.error(f"Failed to load India boundary geometry: {e}")
    return _prepared_boundary


def is_point_in_india(lat: float, lon: float) -> bool:
    """
    Check if (lat, lon) is strictly within Indian sovereign territory.
    Returns False for Tibet, Pakistan, Myanmar, Bangladesh, and open seas.
    """
    if lat < MIN_LAT or lat > MAX_LAT or lon < MIN_LON or lon > MAX_LON:
        return False

    boundary = get_india_boundary()
    if boundary is None:
        return True

    return boundary.contains(Point(lon, lat))
