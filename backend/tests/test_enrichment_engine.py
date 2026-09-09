"""
Unit tests for GIS enrichment engine
Tests spatial calculations, confidence scoring
"""

import pytest
from backend.gis.enrichment_engine import GISEnrichmentEngine
from backend.config import Config
from backend.database import Database


class TestSpatialCalculations:
    """Test spatial calculation functions"""

    @pytest.fixture
    def engine(self):
        config = Config()
        db = Database(config)
        return GISEnrichmentEngine(db, config)

    def test_haversine_distance_same_point(self, engine):
        """Test Haversine distance for same point"""
        distance = engine._haversine_distance(18.5, 73.8, 18.5, 73.8)

        assert distance == 0.0

    def test_haversine_distance_different_points(self, engine):
        """Test Haversine distance for different points"""
        # Pune to Mumbai (roughly 180 km)
        distance = engine._haversine_distance(18.5, 73.8, 19.1, 72.9)

        # Should be around 100-200 km
        assert 50000 < distance < 200000  # in meters

    def test_inside_industrial_threshold(self, engine):
        """Test industrial zone detection"""
        event_lat, event_lon = 18.5, 73.8
        features = [
            {
                "latitude": 18.5,
                "longitude": 73.8,
                "name": "Factory at exact location"
            }
        ]

        inside = engine._check_inside_industrial(event_lat, event_lon, features, threshold_m=100)

        assert inside is True

    def test_inside_industrial_outside_threshold(self, engine):
        """Test industrial detection fails for distant features"""
        event_lat, event_lon = 18.5, 73.8
        features = [
            {
                "latitude": 19.0,  # ~50+ km away
                "longitude": 74.0,
                "name": "Distant factory"
            }
        ]

        inside = engine._check_inside_industrial(event_lat, event_lon, features, threshold_m=100)

        assert inside is False

    def test_find_nearest_feature_empty(self, engine):
        """Test nearest feature search with no features"""
        event_lat, event_lon = 18.5, 73.8
        features = []

        nearest, distance = engine._find_nearest_feature(event_lat, event_lon, features)

        assert nearest is None
        assert distance is None

    def test_find_nearest_feature_single(self, engine):
        """Test nearest feature search with single feature"""
        event_lat, event_lon = 18.5, 73.8
        features = [
            {
                "osm_id": 123,
                "latitude": 18.51,
                "longitude": 73.81,
                "name": "Factory"
            }
        ]

        nearest, distance = engine._find_nearest_feature(event_lat, event_lon, features)

        assert nearest is not None
        assert nearest["osm_id"] == 123
        assert distance > 0

    def test_find_nearest_feature_multiple(self, engine):
        """Test nearest feature search returns closest"""
        event_lat, event_lon = 18.5, 73.8
        features = [
            {
                "osm_id": 123,
                "latitude": 18.6,  # ~11 km away
                "longitude": 73.9,
                "name": "Factory 1"
            },
            {
                "osm_id": 124,
                "latitude": 18.51,  # ~1.2 km away
                "longitude": 73.81,
                "name": "Factory 2"
            }
        ]

        nearest, distance = engine._find_nearest_feature(event_lat, event_lon, features)

        # Should find the closer one
        assert nearest["osm_id"] == 124

    def test_count_features_within_radius(self, engine):
        """Test feature counting within radius"""
        event_lat, event_lon = 18.5, 73.8
        features = [
            {
                "latitude": 18.5,
                "longitude": 73.8,
                "name": "Factory 1"  # At event location
            },
            {
                "latitude": 18.51,
                "longitude": 73.81,
                "name": "Factory 2"  # ~1.2 km away
            },
            {
                "latitude": 19.0,
                "longitude": 74.0,
                "name": "Factory 3"  # ~50+ km away
            }
        ]

        count = engine._count_features_within(event_lat, event_lon, features, radius_km=1.0)

        # First two should be within 1km
        assert count == 2


class TestConfidenceScoring:
    """Test enrichment confidence scoring"""

    @pytest.fixture
    def engine(self):
        config = Config()
        db = Database(config)
        return GISEnrichmentEngine(db, config)

    def test_confidence_base_score(self, engine):
        """Test confidence score starts with event confidence"""
        score = engine._compute_enrichment_confidence(
            brightness=300.0,
            frp=0.0,
            event_confidence=80,
            inside_industrial=False,
            nearest_distance=None,
            land_cover_label="built",
            has_water=False,
            osm_coverage="live",
            dw_coverage="live"
        )

        # Should be between 0 and 1, influenced by 80% confidence
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # 80% confidence should result in > 50% score

    def test_confidence_industrial_boost(self, engine):
        """Test industrial zone boost"""
        score_without = engine._compute_enrichment_confidence(
            brightness=300.0,
            frp=50.0,
            event_confidence=80,
            inside_industrial=False,
            nearest_distance=15000,
            land_cover_label="built",
            has_water=True,
            osm_coverage="live",
            dw_coverage="live"
        )

        score_with = engine._compute_enrichment_confidence(
            brightness=300.0,
            frp=50.0,
            event_confidence=80,
            inside_industrial=True,  # Only difference
            nearest_distance=15000,
            land_cover_label="built",
            has_water=True,
            osm_coverage="live",
            dw_coverage="live"
        )

        # Industrial boost should increase score
        assert score_with > score_without

    def test_confidence_proximity_boost(self, engine):
        """Test proximity to features boosts score"""
        score_far = engine._compute_enrichment_confidence(
            brightness=300.0,
            frp=50.0,
            event_confidence=80,
            inside_industrial=False,
            nearest_distance=50000,  # 50km away
            land_cover_label="built",
            has_water=True,
            osm_coverage="live",
            dw_coverage="live"
        )

        score_close = engine._compute_enrichment_confidence(
            brightness=300.0,
            frp=50.0,
            event_confidence=80,
            inside_industrial=False,
            nearest_distance=1000,  # 1km away
            land_cover_label="built",
            has_water=True,
            osm_coverage="live",
            dw_coverage="live"
        )

        # Closer proximity should boost score
        assert score_close > score_far

    def test_confidence_data_availability_penalty(self, engine):
        """Test penalty for unavailable data"""
        score_available = engine._compute_enrichment_confidence(
            brightness=300.0,
            frp=50.0,
            event_confidence=80,
            inside_industrial=False,
            nearest_distance=5000,
            land_cover_label="built",
            has_water=True,
            osm_coverage="live",
            dw_coverage="live"
        )

        score_unavailable = engine._compute_enrichment_confidence(
            brightness=300.0,
            frp=50.0,
            event_confidence=80,
            inside_industrial=False,
            nearest_distance=5000,
            land_cover_label="built",
            has_water=True,
            osm_coverage="source_unavailable",  # Unavailable
            dw_coverage="live"
        )

        # Unavailable data should reduce score
        assert score_unavailable < score_available

    def test_confidence_clamped_to_range(self, engine):
        """Test score is clamped to [0, 1]"""
        # Try to get a very high score
        score = engine._compute_enrichment_confidence(
            brightness=1000.0,
            frp=1000.0,
            event_confidence=100,
            inside_industrial=True,
            nearest_distance=10,
            land_cover_label="built",
            has_water=False,
            osm_coverage="live",
            dw_coverage="live"
        )

        # Should never exceed 1.0
        assert 0.0 <= score <= 1.0
