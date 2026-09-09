"""
Unit tests for thermal source grouping
Tests spatial-temporal clustering logic
"""

import pytest
from datetime import datetime, timedelta
from backend.gis.thermal_source_grouper import ThermalSourceGrouper
from backend.config import Config
from backend.database import Database


class TestThermalSourceGrouper:
    """Test thermal source grouping logic"""

    @pytest.fixture
    def config(self):
        """Create test config"""
        return Config()

    @pytest.fixture
    def grouper(self, config):
        """Create grouper instance"""
        db = Database(config)
        return ThermalSourceGrouper(db, config)

    def test_haversine_distance_same_point(self, grouper):
        """Test distance calculation for same point"""
        distance = grouper._haversine_distance(18.5, 73.8, 18.5, 73.8)

        assert distance == 0.0

    def test_haversine_distance_known_values(self, grouper):
        """Test distance calculation with known values"""
        # Pune to Delhi (roughly 1100 km)
        distance = grouper._haversine_distance(18.5, 73.8, 28.7, 77.2)

        # Should be roughly 1000-1200 km
        assert 900000 < distance < 1300000  # in meters

    def test_spatial_temporal_matching_within_threshold(self, grouper):
        """Test event matching within spatial-temporal thresholds"""
        # Set loose thresholds for testing
        grouper.spatial_threshold_m = 1000  # 1 km
        grouper.temporal_threshold_h = 48  # 48 hours

        event = {
            "id": "event1",
            "latitude": 18.5,
            "longitude": 73.8,
            "acquisition_time": datetime.utcnow().isoformat()
        }

        existing_source = {
            "id": "source1",
            "centroid_lat": 18.50,
            "centroid_lon": 73.80,
            "last_detected": datetime.utcnow().isoformat()
        }

        # Should match (within 1km and 48 hours)
        matching = grouper._find_matching_source(event, [existing_source])

        assert matching == "source1"

    def test_spatial_temporal_matching_outside_spatial_threshold(self, grouper):
        """Test no match when spatial threshold exceeded"""
        grouper.spatial_threshold_m = 1000  # 1 km
        grouper.temporal_threshold_h = 48

        event = {
            "id": "event1",
            "latitude": 18.5,
            "longitude": 73.8,
            "acquisition_time": datetime.utcnow().isoformat()
        }

        existing_source = {
            "id": "source1",
            "centroid_lat": 19.0,  # ~50+ km away
            "centroid_lon": 74.0,
            "last_detected": datetime.utcnow().isoformat()
        }

        # Should not match (outside 1 km threshold)
        matching = grouper._find_matching_source(event, [existing_source])

        assert matching is None

    def test_spatial_temporal_matching_outside_temporal_threshold(self, grouper):
        """Test no match when temporal threshold exceeded"""
        grouper.spatial_threshold_m = 1000  # 1 km
        grouper.temporal_threshold_h = 24  # 24 hours

        current_time = datetime.utcnow()
        old_time = (current_time - timedelta(days=2)).isoformat()

        event = {
            "id": "event1",
            "latitude": 18.5,
            "longitude": 73.8,
            "acquisition_time": current_time.isoformat()
        }

        existing_source = {
            "id": "source1",
            "centroid_lat": 18.50,
            "centroid_lon": 73.80,
            "last_detected": old_time  # 2 days old
        }

        # Should not match (outside 24 hour threshold)
        matching = grouper._find_matching_source(event, [existing_source])

        assert matching is None

    def test_multiple_sources_picks_closest(self, grouper):
        """Test matching picks closest source when multiple available"""
        grouper.spatial_threshold_m = 10000  # 10 km
        grouper.temporal_threshold_h = 48

        event = {
            "id": "event1",
            "latitude": 18.5,
            "longitude": 73.8,
            "acquisition_time": datetime.utcnow().isoformat()
        }

        existing_sources = [
            {
                "id": "source1",
                "centroid_lat": 18.6,  # ~11 km away
                "centroid_lon": 73.9,
                "last_detected": datetime.utcnow().isoformat()
            },
            {
                "id": "source2",
                "centroid_lat": 18.51,  # ~1.2 km away
                "centroid_lon": 73.81,
                "last_detected": datetime.utcnow().isoformat()
            }
        ]

        # Should match the closer source
        matching = grouper._find_matching_source(event, existing_sources)

        assert matching == "source2"

    def test_configurable_thresholds(self, config):
        """Test that thresholds are configurable"""
        db = Database(config)
        grouper = ThermalSourceGrouper(db, config)

        # Default thresholds
        assert grouper.spatial_threshold_m == 300  # 300m default
        assert grouper.temporal_threshold_h == 48  # 48 hours default

        # Should be configurable via config
        config.THERMAL_SOURCE_SPATIAL_THRESHOLD_M = "500"
        grouper2 = ThermalSourceGrouper(db, config)
        assert grouper2.spatial_threshold_m == 500
