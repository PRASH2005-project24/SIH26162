#!/usr/bin/env python3
"""
Test script to verify SIH classification post-processing logic
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.ml.sih_classifier import map_to_sih_category, get_sih_category_labels, is_valid_sih_category
from backend.api.events import PersistenceResponse

def test_sih_classifier():
    """Test the SIH classification logic"""
    print("Testing SIH Classification Post-Processing...")
    print("=" * 50)

    # Test 1: Valid SIH categories
    print("Test 1: Valid SIH categories")
    labels = get_sih_category_labels()
    expected_labels = [
        "Industrial Fire",
        "Wildfire/Natural Fire",
        "Agricultural Fire",
        "Persistent Thermal Source",
        "Unknown/Other"
    ]
    assert labels == expected_labels, f"Expected {expected_labels}, got {labels}"
    print("PASS: SIH category labels correct")

    # Test 2: Invalid category detection
    print("\nTest 2: Invalid category detection")
    assert is_valid_sih_category("Industrial Fire") == True
    assert is_valid_sih_category("Invalid Category") == False
    print("PASS: Category validation working")

    # Test 3: Persistent Thermal Source priority
    print("\nTest 3: Persistent Thermal Source priority")
    ml_pred = {
        "category": "industrial",
        "confidence": 0.9,
        "probabilities": {"industrial": 0.9, "agricultural": 0.05, "wildfire": 0.05},
        "model_type": "RandomForest"
    }
    persistence_info = PersistenceResponse(
        is_persistent=True,
        date_count=10,
        duration_days=45,
        persistence_date_count=10,
        persistence_duration_days=45
    )

    result = map_to_sih_category(ml_pred, persistence_info)
    assert result["sih_category"] == "Persistent Thermal Source"
    assert result["is_persistent"] == True
    assert result["ml_category"] == "industrial"
    print("PASS: Persistent Thermal Source correctly prioritized")

    # Test 4: High confidence ML mapping
    print("\nTest 4: High confidence ML mapping")
    ml_pred = {
        "category": "wildfire",
        "confidence": 0.85,
        "probabilities": {"industrial": 0.1, "agricultural": 0.05, "wildfire": 0.85},
        "model_type": "RandomForest"
    }
    persistence_info = PersistenceResponse(
        is_persistent=False,
        date_count=0,
        duration_days=0,
        persistence_date_count=0,
        persistence_duration_days=0
    )

    result = map_to_sih_category(ml_pred, persistence_info)
    assert result["sih_category"] == "Wildfire/Natural Fire"
    assert result["sih_confidence"] == 0.85
    assert result["ml_category"] == "wildfire"
    print("PASS: High confidence ML mapping correct")

    # Test 5: Low confidence -> Unknown/Other
    print("\nTest 5: Low confidence -> Unknown/Other")
    ml_pred = {
        "category": "industrial",
        "confidence": 0.4,  # Below threshold
        "probabilities": {"industrial": 0.4, "agricultural": 0.3, "wildfire": 0.3},
        "model_type": "RandomForest"
    }
    persistence_info = PersistenceResponse(
        is_persistent=False,
        date_count=0,
        duration_days=0,
        persistence_date_count=0,
        persistence_duration_days=0
    )

    result = map_to_sih_category(ml_pred, persistence_info)
    assert result["sih_category"] == "Unknown/Other"
    assert result["ml_category"] == "industrial"
    print("PASS: Low confidence correctly mapped to Unknown/Other")

    # Test 6: Default Unknown/Other
    print("\nTest 6: Default Unknown/Other")
    ml_pred = {
        "category": "unknown_model_class",  # Not in our mapping
        "confidence": 0.7,
        "probabilities": {"unknown_model_class": 0.7, "other": 0.3},
        "model_type": "RandomForest"
    }
    persistence_info = PersistenceResponse(
        is_persistent=False,
        date_count=0,
        duration_days=0,
        persistence_date_count=0,
        persistence_duration_days=0
    )

    result = map_to_sih_category(ml_pred, persistence_info)
    assert result["sih_category"] == "Unknown/Other"
    assert result["ml_category"] == "unknown_model_class"
    print("PASS: Unknown model class correctly mapped to Unknown/Other")

    print("\n" + "=" * 50)
    print("All SIH classification tests passed! PASS")
    return True

if __name__ == "__main__":
    try:
        test_sih_classifier()
        print("\nSIH Classification module is working correctly.")
    except Exception as e:
        print(f"\nFAIL: Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)