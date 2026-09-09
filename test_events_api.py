#!/usr/bin/env python3
"""
Test script for Events API endpoint
"""

import asyncio
import os

# Set environment variables
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://postgres:postgres@localhost:5432/sih26162'
os.environ['DEMO_MODE'] = 'true'
os.environ['FIRMS_MAP_KEY'] = 'test_key'

async def test_events_imports():
    """Test that all necessary modules can be imported"""
    try:
        from backend.api.events import (
            get_ml_prediction_for_event,
            get_persistence_info_for_event,
            ThermalEventResponse,
            EventDetailResponse,
            EventsListResponse
        )
        from backend.database import Database
        from backend.config import Config
        from backend.gis.enrichment_engine import GISEnrichmentEngine
        print("✅ All events API imports successful")
        return True
    except Exception as e:
        print("❌ Events API imports failed: {}".format(e))
        return False

async def test_response_models():
    """Test the response models"""
    try:
        from backend.api.events import (
            ThermalEventResponse,
            ClassificationResponse,
            PersistenceResponse,
            OsmContextResponse,
            DynamicWorldResponse
        )
        from datetime import datetime

        # Test ThermalEventResponse creation
        event_data = {
            "id": "test-event-id",
            "acquisition_time": datetime.utcnow(),
            "latitude": 20.0,
            "longitude": 77.0,
            "satellite": "NOAA-20",
            "status": "active",
            "pipeline_version": "1.0.0",
            "processed_at": datetime.utcnow()
        }

        event = ThermalEventResponse(**event_data)
        assert event.id == "test-event-id"
        assert event.latitude == 20.0
        assert event.longitude == 77.0

        print("✅ Events API response models work correctly")
        return True
    except Exception as e:
        print("❌ Events API response models test failed: {}".format(e))
        return False

async def main():
    """Run all tests"""
    print("Testing Events API endpoint components...")

    tests = [
        test_events_imports(),
        test_response_models()
    ]

    results = await asyncio.gather(*tests, return_exceptions=True)

    passed = 0
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print("Test {} failed with exception: {}".format(i+1, result))
        elif result:
            passed += 1

    print("\nResults: {}/{} tests passed".format(passed, len(tests)))

    if passed == len(tests):
        print("All tests passed!")
        return True
    else:
        print("Some tests failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)