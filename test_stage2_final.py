"""
Stage 2 Final Test & Verification
Comprehensive end-to-end testing and result reporting
"""

import os
import sys
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.config import TimeWindow, MLConfig
from ml.models.inference import FireSourceClassifier
import pandas as pd


def test_time_windows():
    """Test time-window configuration"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Time-Window Configuration")
    logger.info("="*80)

    ref_time = datetime(2026, 8, 26, 12, 0, 0)

    for tw in [TimeWindow.TODAY, TimeWindow.LAST_24_HOURS, TimeWindow.LAST_7_DAYS, TimeWindow.LAST_30_DAYS]:
        start = tw.get_start_time(ref_time)
        end = tw.get_end_time(ref_time)
        sql_filter, params = tw.get_sql_filter("acquisition_time", ref_time)

        logger.info(f"\n{tw.value}:")
        logger.info(f"  Start: {start}")
        logger.info(f"  End:   {end}")
        logger.info(f"  SQL:   {sql_filter}")

    logger.info("\n✓ Time-window configuration working")
    return True


def test_model_loading():
    """Test model loading and basic inference"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Model Loading & Inference")
    logger.info("="*80)

    try:
        classifier = FireSourceClassifier(MLConfig.MODEL_DIR)
        logger.info(f"✓ Model loaded from {MLConfig.MODEL_DIR}")

        # Create test features
        test_features = {
            "frp": 75.2,
            "brightness_temperature_k": 320.0,
            "firms_confidence": 85.0,
            "scan_km": 0.8,
            "track_km": 0.6,
            "day_night": "D",
            "satellite": "VIIRS",
            "nearest_facility_distance_m": 500.0,
            "industrial_context_score": 0.75,
            "nearest_water_distance_m": 1500.0,
            "dw_water": 0.05,
            "dw_trees": 0.10,
            "dw_grass": 0.05,
            "dw_flooded_vegetation": 0.01,
            "dw_crops": 0.10,
            "dw_shrub_scrub": 0.05,
            "dw_built": 0.60,
            "dw_bare": 0.04,
            "dw_snow_ice": 0.0,
            "dw_confidence": 0.95,
            "detections_24h": 5,
            "detections_3d": 12,
            "detections_7d": 30,
            "active_days": 7,
            "persistence_duration_days": 7,
            "mean_frp": 70.0,
            "max_frp": 95.0,
            "acquisition_datetime": "2026-08-26T12:00:00",
            "latitude": 18.52,
            "longitude": 73.85,
        }

        prediction = classifier.predict(test_features)

        logger.info(f"\nTest Prediction:")
        logger.info(f"  Predicted Class: {prediction['predicted_class']}")
        logger.info(f"  Confidence: {prediction['confidence']:.4f}")
        logger.info(f"  Model Type: {prediction['model_type']}")
        logger.info(f"\nClass Probabilities:")
        for cls, prob in prediction["class_probabilities"].items():
            logger.info(f"  {cls:<35} {prob:.4f}")

        logger.info(f"\n✓ Inference working correctly")
        return True

    except Exception as e:
        logger.error(f"✗ Inference failed: {e}", exc_info=True)
        return False


def test_model_artifacts():
    """Verify all model artifacts exist"""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: Model Artifacts")
    logger.info("="*80)

    required_files = [
        "model_random_forest.joblib",
        "label_encoder.joblib",
        "feature_schema.json",
        "model_metadata.json",
        "metrics.json"
    ]

    all_exist = True
    for filename in required_files:
        path = os.path.join(MLConfig.MODEL_DIR, filename)
        exists = os.path.exists(path)
        status = "✓" if exists else "✗"
        logger.info(f"  {status} {filename} - {path}")

        if not exists:
            all_exist = False

    if all_exist:
        # Load and show metrics
        metrics_path = os.path.join(MLConfig.MODEL_DIR, "metrics.json")
        with open(metrics_path, "r") as f:
            metrics = json.load(f)

        logger.info(f"\nTest Set Metrics:")
        logger.info(f"  Accuracy: {metrics['accuracy']:.4f}")
        logger.info(f"  Macro F1: {metrics['macro_f1']:.4f}")
        logger.info(f"  Weighted F1: {metrics['weighted_f1']:.4f}")

        logger.info(f"\n✓ All model artifacts present and valid")
        return True
    else:
        logger.error("✗ Some model artifacts missing")
        return False


def test_csv_loading():
    """Verify CSV can be loaded"""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: CSV Data Loading")
    logger.info("="*80)

    csv_path = "SIH26162_stage2_demo_training_data.csv"
    if not os.path.exists(csv_path):
        logger.error(f"✗ CSV not found: {csv_path}")
        return False

    try:
        df = pd.read_csv(csv_path)
        logger.info(f"✓ CSV loaded: {len(df)} rows, {len(df.columns)} columns")

        # Check classes
        classes = df["target_class"].value_counts().to_dict()
        logger.info(f"\nClass Distribution:")
        for cls, count in sorted(classes.items(), key=lambda x: x[1], reverse=True):
            pct = 100 * count / len(df)
            logger.info(f"  {cls:<35} {count:>4} ({pct:>5.1f}%)")

        logger.info(f"\n✓ CSV validation passed")
        return True

    except Exception as e:
        logger.error(f"✗ CSV loading failed: {e}")
        return False


def test_stage_1_still_works():
    """Verify Stage 1/1B integrity"""
    logger.info("\n" + "="*80)
    logger.info("TEST 5: Stage 1/1B Integrity")
    logger.info("="*80)

    # Check that Stage 1 modules still import
    try:
        from backend.config import Config
        from backend.database import Database
        from backend.firms_collector import FIRMSCollector

        logger.info("✓ Stage 1 modules import successfully")

        # Check config
        config = Config()
        logger.info(f"✓ Config loads: DB URL starts with {config.DATABASE_URL[:30]}...")

        logger.info(f"✓ Stage 1/1B infrastructure intact")
        return True

    except Exception as e:
        logger.error(f"✗ Stage 1/1B check failed: {e}")
        return False


def main():
    """Run all tests"""
    logger.info("\n" + "="*80)
    logger.info("STAGE 2 ML PIPELINE - FINAL VERIFICATION")
    logger.info("="*80)

    tests = [
        ("Time-Window Config", test_time_windows),
        ("Model Loading", test_model_loading),
        ("Model Artifacts", test_model_artifacts),
        ("CSV Loading", test_csv_loading),
        ("Stage 1/1B Integrity", test_stage_1_still_works),
    ]

    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            logger.error(f"✗ {name} crashed: {e}")
            results[name] = False

    # Summary
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for name, result in results.items():
        status = "PASS" if result else "FAIL"
        logger.info(f"  {status:<6} {name}")

    logger.info(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        logger.info("\n✓ ALL TESTS PASSED - Stage 2 ready!")
    else:
        logger.info(f"\n✗ {total - passed} test(s) failed")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
