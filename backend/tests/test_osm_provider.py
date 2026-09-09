"""
Unit tests for OSM/Overpass provider
Tests India-wide coverage, caching, spatial calculations
"""

import pytest
from backend.gis.osm_provider import OSMProvider
from backend.config import Config
from backend.database import Database


class TestOSMProvider:
    """Test OSM provider functionality"""

    @pytest.fixture
    def config(self):
        """Create test config"""
        return Config()

    @pytest.fixture
    def provider(self, config):
        """Create OSM provider instance"""
        db = Database(config)
        return OSMProvider(db, config)

    def test_point_in_india_valid_locations(self, provider):
        """Test India boundary validation for valid locations"""
        # Pune
        assert provider._point_in_bbox(18.5, 73.8, (8.0, 68.0, 35.0, 97.0)) is True

        # Mumbai
        assert provider._point_in_bbox(19.1, 72.9, (8.0, 68.0, 35.0, 97.0)) is True

        # Delhi
        assert provider._point_in_bbox(28.7, 77.2, (8.0, 68.0, 35.0, 97.0)) is True

        # Kochi (South)
        assert provider._point_in_bbox(9.9, 76.3, (8.0, 68.0, 35.0, 97.0)) is True

    def test_point_in_india_invalid_locations(self, provider):
        """Test India boundary validation for invalid locations"""
        # Outside India
        assert provider._point_in_bbox(0, 0, (8.0, 68.0, 35.0, 97.0)) is False
        assert provider._point_in_bbox(45, 100, (8.0, 68.0, 35.0, 97.0)) is False
        assert provider._point_in_bbox(7, 70, (8.0, 68.0, 35.0, 97.0)) is False

    def test_expand_bbox(self, provider):
        """Test bounding box expansion"""
        lat, lon = 18.5, 73.8
        buffer_km = 5.0

        bbox = provider._expand_bbox(lat, lon, buffer_km)
        min_lat, min_lon, max_lat, max_lon = bbox

        # Check that bbox contains original point
        assert min_lat < lat < max_lat
        assert min_lon < lon < max_lon

        # Check approximate buffer size (should be roughly 5km in each direction)
        lat_diff = max_lat - min_lat
        assert 0.04 < lat_diff < 0.15  # Roughly 4-15 km

    def test_tile_from_point(self, provider):
        """Test tile coordinate calculation"""
        lat, lon = 18.5, 73.8
        zoom = 13

        tile_x, tile_y = provider._tile_from_point(lat, lon, zoom)

        # Verify tiles are valid (positive integers)
        assert isinstance(tile_x, int)
        assert isinstance(tile_y, int)
        assert tile_x >= 0
        assert tile_y >= 0
        assert tile_x < 2**zoom
        assert tile_y < 2**zoom

    def test_tile_key_format(self, provider):
        """Test tile cache key generation"""
        tile_x, tile_y, tile_z = 100, 200, 13

        key = provider._tile_key(tile_x, tile_y, tile_z)

        # Format should be z/x/y
        parts = key.split('/')
        assert len(parts) == 3
        assert parts[0] == str(tile_z)
        assert parts[1] == str(tile_x)
        assert parts[2] == str(tile_y)

    def test_parse_overpass_response_empty(self, provider):
        """Test parsing empty Overpass response"""
        response = {"elements": []}

        features = provider._parse_overpass_response(response)

        assert len(features) == 0

    def test_parse_overpass_response_valid(self, provider):
        """Test parsing valid Overpass response"""
        response = {
            "elements": [
                {
                    "id": 12345,
                    "type": "node",
                    "lat": 18.5,
                    "lon": 73.8,
                    "tags": {"name": "Factory A", "industrial": "factory"}
                },
                {
                    "id": 12346,
                    "type": "node",
                    "lat": 18.6,
                    "lon": 73.9,
                    "tags": {"name": "Factory B"}
                }
            ]
        }

        features = provider._parse_overpass_response(response)

        assert len(features) == 2
        assert features[0]["latitude"] == 18.5
        assert features[0]["longitude"] == 73.8
        assert features[0]["name"] == "Factory A"
        assert features[1]["name"] == "Factory B"

    def test_parse_overpass_response_missing_coords(self, provider):
        """Test parsing response with missing coordinates"""
        response = {
            "elements": [
                {
                    "id": 12345,
                    "type": "node",
                    "lat": 18.5,
                    "lon": 73.8,
                    "tags": {"name": "Factory A"}
                },
                {
                    "id": 12346,
                    "type": "node",
                    "tags": {"name": "Factory B"}  # No lat/lon
                }
            ]
        }

        features = provider._parse_overpass_response(response)

        # Only valid feature should be returned
        assert len(features) == 1
        assert features[0]["name"] == "Factory A"
