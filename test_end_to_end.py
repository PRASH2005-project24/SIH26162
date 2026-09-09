#!/usr/bin/env python3
"""
End-to-end test for STAGE 3.3 backend operational API with SIH classification
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from backend.ml.sih_classifier import map_to_sih_category
from backend.api.events import PersistenceResponse

def test_end_to_end_sih_classification():
    """Test end-to-end SIH classification workflow"""
    print("Testing End-to-End SIH Classification Workflow...")
    print("=" * 60)

    # Simulate ML prediction from frozen model
    ml_predictions = [
        {
            "category": "industrial",
            "confidence": 0.92,
            "probabilities": {"industrial": 0.92, "agricultural": 0.05, "wildfire": 0.03},
            "model_type": "RandomForestClassifier"
        },
        {
            "category": "wildfire",
            "confidence": 0.78,
            "probabilities": {"industrial": 0.1, "agricultural": 0.12, "wildfire": 0.78},
            "model_type": "RandomForestClassifier"
        },
        {
            "category": "agricultural",
            "confidence": 0.45,  # Low confidence
            "probabilities": {"industrial": 0.2, "agricultural": 0.45, "wildfire": 0.35},
            "model_type": "RandomForestClassifier"
        }
    ]

    # Test cases with different persistence scenarios
    persistence_scenarios = [
        {
            "name": "Persistent Source",
            "persistence": PersistenceResponse(
                is_persistent=True,
                date_count=15,
                duration_days=45,
                persistence_date_count=15,
                persistence_duration_days=45
            )
        },
        {
            "name": "Non-Persistent Source",
            "persistence": PersistenceResponse(
                is_persistent=False,
                date_count=2,
                duration_days=5,
                persistence_date_count=2,
                persistence_duration_days=5
            )
        },
        {
            "name": "No Historical Data",
            "persistence": PersistenceResponse(
                is_persistent=False,
                date_count=0,
                duration_days=0,
                persistence_date_count=0,
                persistence_duration_days=0
            )
        }
    ]

    print("\nTesting different combinations:")
    print("-" * 60)

    for i, ml_pred in enumerate(ml_predictions):
        print(f"\nML Prediction {i+1}: {ml_pred['category']} (confidence: {ml_pred['confidence']:.2f})")

        for scenario in persistence_scenarios:
            result = map_to_sih_category(ml_pred, scenario["persistence"])

            print(f"  {scenario['name']:20} -> SIH: {result['sih_category']:25} "
                  f"(conf: {result['sih_confidence']:.2f}, persistent: {result['is_persistent']})")

            # Verify that original ML probabilities are preserved
            assert "ml_probabilities" in result
            assert result["ml_probabilities"] == ml_pred["probabilities"]
            assert result["ml_category"] == ml_pred["category"]
            assert result["ml_confidence"] == ml_pred["confidence"]

    print("\n" + "=" * 60)
    print("All end-to-end tests passed!")
    return True

if __name__ == "__main__":
    try:
        test_end_to_end_sih_classification()
        print("\nEnd-to-end SIH classification workflow is working correctly.")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)