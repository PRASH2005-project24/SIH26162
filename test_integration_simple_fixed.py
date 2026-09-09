#!/usr/bin/env python3
"""
Simple integration test for STAGE 3.3 components
"""

import os
import sys

# Set environment variables
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://postgres:postgres@localhost:5432/sih26162'
os.environ['DEMO_MODE'] = 'true'
os.environ['FIRMS_MAP_KEY'] = 'test_key'

def test_config_india_wide():
    """Test that configuration defaults to India-wide"""
    try:
        from backend.config import Config
        c = Config()

        # Check that defaults are India-wide
        assert c.PILOT_BBOX == "8.0,68.0,35.0,97.0"
        assert c.PILOT_NAME == "india"
        assert c.FIRMS_BBOX == "8.0,68.0,35.0,97.0"

        # Check that india_bbox_tuple property works
        india_bbox = c.india_bbox_tuple
        assert india_bbox == (8.0, 68.0, 35.0, 97.0)

        print("[PASS] Configuration test passed: India-wide defaults confirmed")
        return True
    except Exception as e:
        print("[FAIL] Configuration test failed: {}".format(e))
        return False

def test_api_imports():
    """Test that all APIs can be imported"""
    try:
        import backend.api.events
        import backend.api.ml_predict
        import backend.api.enrichment
        import backend.api.health

        print("[PASS] API imports test passed: All modules imported successfully")
        return True
    except Exception as e:
        print("[FAIL] API imports test failed: {}".format(e))
        return False

def test_ml_predict_structure():
    """Test ML prediction endpoint structure"""
    try:
        from backend.api.ml_predict import PredictionRequest, compute_features_from_event

        # Test PredictionRequest model
        req1 = PredictionRequest(event_id="test-123")
        assert req1.event_id == "test-123"
        assert req1.features is None

        req2 = PredictionRequest(features={"test": 1})
        assert req2.features == {"test": 1}
        assert req2.event_id is None

        # Test function signature
        import inspect
        sig = inspect.signature(compute_features_from_event)
        params = list(sig.parameters.keys())
        assert params == ['event_id', 'db']

        print("[PASS] ML Predict structure test passed")
        return True
    except Exception as e:
        print("[FAIL] ML Predict structure test failed: {}".format(e))
        return False

def main():
    """Run all integration tests"""
    print("Running STAGE 3.3 integration tests...")
    print("=" * 50)

    tests = [
        test_config_india_wide,
        test_api_imports,
        test_ml_predict_structure
    ]

    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()  # Empty line between tests

    print("=" * 50)
    print("Results: {}/{} tests passed".format(passed, len(tests)))

    if passed == len(tests):
        print("[PASS] All integration tests passed!")
        return True
    else:
        print("[FAIL] Some integration tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)