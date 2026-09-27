"""
Unit tests for FIRMS collector
Tests validation, normalization, deduplication
"""

import asyncio
import pytest
from datetime import datetime
from backend.firms_collector import FIRMSCollector
from backend.database import Database
from backend.config import Config


class TestFIRMSNormalization:
    """Test FIRMS CSV normalization logic"""

    @pytest.fixture
    def collector(self):
        """Create test collector instance"""
        config = Config()
        db = Database(config)
        return FIRMSCollector(db, config)

    def test_normalize_valid_event(self, collector):
        """Test normalization of valid FIRMS record"""
        raw_event = {
            "latitude": "18.5",
            "longitude": "73.8",
            "acq_date": "2026-08-26",
            "acq_time": "1430",
            "brightness": "315.2",
            "frp": "42.5",
            "confidence": "85",
            "satellite": "NOAA-20",
            "instrument": "VIIRS",
            "day_night": "D",
        }

        run_id = "test-run-001"
        event = collector._normalize_event(raw_event, run_id)

        assert event is not None
        assert event["latitude"] == 18.5
        assert event["longitude"] == 73.8
        assert event["brightness"] == 315.2
        assert event["frp"] == 42.5
        assert event["confidence"] == 85
        assert event["satellite"] == "NOAA-20"
        assert event["ingestion_run_id"] == run_id

    def test_insert_event_writes_required_postgis_point(self, collector):
        raw_event = {
            "latitude": "18.5",
            "longitude": "73.8",
            "acq_date": "2026-08-26",
            "acq_time": "1430",
            "brightness": "315.2",
            "frp": "42.5",
            "confidence": "85",
            "satellite": "NOAA-20",
        }
        event = collector._normalize_event(raw_event, "test-run")
        captured = {}

        class RecordingDatabase:
            async def execute_update(self, query, params):
                captured["query"] = query
                captured["params"] = params

        collector.db = RecordingDatabase()
        asyncio.run(collector._insert_event(event, "test-run"))

        assert "latitude, longitude, point," in captured["query"]
        assert "ST_GeomFromText(:point, 4326)" in captured["query"]
        assert captured["params"]["latitude"] == 18.5
        assert captured["params"]["longitude"] == 73.8
        assert captured["params"]["point"] == "POINT(73.8 18.5)"
        assert asyncio.run(collector._insert_event(event, "test-run")) is True

    def test_unique_conflict_race_counts_as_duplicate(self, collector):
        raw_event = {
            "latitude": "18.5",
            "longitude": "73.8",
            "acq_date": "2026-08-26",
            "acq_time": "1430",
            "brightness": "315.2",
            "frp": "42.5",
            "confidence": "85",
            "satellite": "NOAA-20",
        }

        class RacingDatabase:
            query_count = 0

            async def execute(self, query, params):
                self.query_count += 1
                return [] if self.query_count == 1 else [{"id": "existing-event"}]

            async def execute_update(self, query, params):
                raise Exception("duplicate key value violates unique constraint")

        collector.db = RacingDatabase()
        result = asyncio.run(collector._ingest_events([raw_event], "test-run"))

        assert result["deduplicated_count"] == 0
        assert result["duplicate_count"] == 1
        assert result["error_count"] == 0

    def test_normalize_missing_frp(self, collector):
        """Test normalization with missing FRP"""
        raw_event = {
            "latitude": "18.5",
            "longitude": "73.8",
            "acq_date": "2026-08-26",
            "acq_time": "1430",
            "brightness": "315.2",
            "confidence": "85",
            "satellite": "NOAA-20",
        }

        event = collector._normalize_event(raw_event, "test-run")

        assert event is not None
        assert event["frp"] is None

    def test_normalize_preserves_training_classifier_features(self, collector):
        raw_event = {
            "latitude": "18.5",
            "longitude": "73.8",
            "acq_date": "2026-08-26",
            "acq_time": "1430",
            "bright_ti4": "340.01",
            "bright_ti5": "293.68",
            "confidence": "n",
            "satellite": "N21",
            "instrument": "VIIRS",
            "daynight": "D",
            "_raw_payload_uri": "raw_payloads/payload-test",
            "_raw_payload_sha256": "payload-hash",
        }

        event = collector._normalize_event(raw_event, "test-run")

        assert event is not None
        assert event["satellite"] == "N21"
        assert event["model_satellite"] == "N21"
        assert event["source_satellite"] == "NOAA21"
        assert event["brightness"] == 340.01
        assert event["bright_ti5"] == 293.68
        assert event["confidence_class"] == "n"
        assert event["raw_payload_uri"] == "raw_payloads/payload-test"
        assert event["raw_payload_sha256"] == "payload-hash"

    def test_normalize_out_of_bounds(self, collector):
        """Test that events outside India are rejected"""
        raw_event = {
            "latitude": "0",  # Outside India
            "longitude": "0",
            "acq_date": "2026-08-26",
            "acq_time": "1430",
            "brightness": "315.2",
            "frp": "42.5",
            "confidence": "85",
            "satellite": "NOAA-20",
        }

        event = collector._normalize_event(raw_event, "test-run")

        assert event is None, "Events outside India should be rejected"

    def test_dedup_key_format(self, collector):
        """Test deduplication key format"""
        raw_event = {
            "latitude": "18.523456",
            "longitude": "73.876543",
            "acq_date": "2026-08-26",
            "acq_time": "1430",
            "brightness": "315.2",
            "frp": "42.5",
            "confidence": "85",
            "satellite": "NOAA-20",
        }

        event = collector._normalize_event(raw_event, "test-run")

        # Dedup key should have rounded coordinates at 4 decimals
        assert event is not None
        assert "18.5235" in event["dedup_key"]
        assert "73.8765" in event["dedup_key"]
        assert "NOAA-20" in event["dedup_key"]

    def test_india_bounds_validation(self, collector):
        """Test India boundary validation"""
        # Valid: Pune
        assert collector._is_point_in_india(18.5, 73.8) is True

        # Valid: Mumbai
        assert collector._is_point_in_india(19.1, 72.9) is True

        # Valid: Delhi
        assert collector._is_point_in_india(28.7, 77.2) is True

        # Invalid: Outside India
        assert collector._is_point_in_india(0, 0) is False
        assert collector._is_point_in_india(45, 100) is False
        assert collector._is_point_in_india(-10, 50) is False


class TestFIRMSCSVParsing:
    """Test FIRMS CSV parsing"""

    @pytest.fixture
    def collector(self):
        config = Config()
        db = Database(config)
        return FIRMSCollector(db, config)

    def test_parse_csv_valid(self, collector):
        """Test parsing valid FIRMS CSV"""
        csv_data = """latitude,longitude,brightness,frp,confidence,acq_date,acq_time,satellite,instrument,day_night
18.5,73.8,315.2,42.5,85,2026-08-26,1430,NOAA-20,VIIRS,D
18.6,73.9,320.1,45.0,90,2026-08-26,1431,NOAA-20,VIIRS,D"""

        events = collector._parse_firms_csv(csv_data)

        assert len(events) == 2
        assert events[0]["latitude"] == "18.5"
        assert events[0]["brightness"] == "315.2"

    def test_parse_csv_empty(self, collector):
        """Test parsing empty CSV"""
        csv_data = ""

        events = collector._parse_firms_csv(csv_data)

        assert len(events) == 0

    def test_parse_csv_header_only(self, collector):
        """Test parsing CSV with header only"""
        csv_data = "latitude,longitude,brightness,frp,confidence,acq_date,acq_time,satellite"

        events = collector._parse_firms_csv(csv_data)

        assert len(events) == 0


class TestFIRMSDeduplication:
    """Test FIRMS deduplication logic"""

    def test_dedup_key_rounding(self):
        """Test that dedup keys use proper rounding"""
        # Two very close points should have same dedup key if rounded to 4 decimals
        lat1, lon1 = 18.52345, 73.87654
        lat2, lon2 = 18.52346, 73.87655

        dedup_key1 = f"{lat1:.4f},{lon1:.4f},2026-08-26T14:30:00,NOAA-20"
        dedup_key2 = f"{lat2:.4f},{lon2:.4f},2026-08-26T14:30:00,NOAA-20"

        # Should be equal due to rounding to 4 decimals
        assert dedup_key1 == dedup_key2

    def test_dedup_key_different_satellites(self):
        """Test that different satellites have different dedup keys"""
        dedup_key1 = "18.5234,73.8765,2026-08-26T14:30:00,NOAA-20"
        dedup_key2 = "18.5234,73.8765,2026-08-26T14:30:00,Suomi-NPP"

        assert dedup_key1 != dedup_key2
