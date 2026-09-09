#!/usr/bin/env python3
"""
Test script for ML prediction endpoint
"""

import asyncio
import os

# Set environment variables
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://postgres:postgres@localhost:5432/sih26162'
os.environ['DEMO_MODE'] = 'true'
os.environ['FIRMS_MAP_KEY'] = 'test_key'

async def test_ml_predict_imports():
    """Test that all necessary modules can be imported"""
    try:
        from backend.api.ml_predict import compute_features_from_event, get_classifier, get_feature_engineer
        from backend.database import Database
        from ml.features.engineering import FeatureEngineer
        from ml.models.inference import FireSourceClassifier
        print("All imports successful")
        return True
    except Exception as e:
        print("Import failed: {}".format(e))
        return False

async def test_compute_features_function():
    """Test the compute_features_from_event function signature"""
    try:
        from backend.api.ml_predict import compute_features_from_event
        import inspect

        sig = inspect.signature(compute_features_from_event)
        params = list(sig.parameters.keys())

        expected_params = ['event_id', 'db']
        if params == expected_params:
            print("compute_features_from_event has correct signature")
            return True
        else:
            print("compute_features_from_event has incorrect signature. Expected {}, got {}".format(expected_params, params))
            return False
    except Exception as e:
        print("Failed to check compute_features_from_event signature: {}".format(e))
        return False

async def test_prediction_request_model():
    """Test the PredictionRequest model"""
    try:
        from backend.api.ml_predict import PredictionRequest

        # Test with event_id
        req1 = PredictionRequest(event_id="test-event-id")
        assert req1.event_id == "test-event-id"
        assert req1.features is None

        # Test with features
        req2 = PredictionRequest(features={"test": 1})
        assert req2.features == {"test": 1}
        assert req2.event_id is None

        print("PredictionRequest model works correctly")
        return True
    except Exception as e:
        print("PredictionRequest model test failed: {}".format(e))
        return False

async def main():
    """Run all tests"""
    print("Testing ML Prediction endpoint components...")

    tests = [
        test_ml_predict_imports(),
        test_compute_features_function(),
        test_prediction_request_model()
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