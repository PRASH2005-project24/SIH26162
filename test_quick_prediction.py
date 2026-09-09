"""
Quick test: Load model and make a single prediction
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ml.models.inference import FireSourceClassifier
from ml.config import MLConfig

# Load model
print("Loading model...")
classifier = FireSourceClassifier(MLConfig.MODEL_DIR)
print(f"[OK] Model loaded from {MLConfig.MODEL_DIR}")

# Test features (Industrial Fire characteristics)
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

print("\nMaking prediction...")
prediction = classifier.predict(test_features)

print("\n" + "="*70)
print("PREDICTION RESULT")
print("="*70)
print(f"Predicted Class: {prediction['predicted_class']}")
print(f"Confidence:      {prediction['confidence']:.4f} ({prediction['confidence']*100:.2f}%)")
print(f"Model Type:      {prediction['model_type']}")
print(f"\nClass Probabilities:")
for cls, prob in prediction["class_probabilities"].items():
    bar = "#" * int(prob * 50)
    print(f"  {cls:<35} {prob:.4f} {bar}")
print("="*70)
print("\n[OK] Model inference working correctly!")
