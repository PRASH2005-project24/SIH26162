"""
Model Inference - Stage 2 ML Pipeline
Load trained model and generate predictions
"""

import logging
import numpy as np
import pandas as pd
import joblib
import json
from typing import Dict, List, Any, Tuple
import os

logger = logging.getLogger(__name__)

# Project root: two levels up from this file (ml/models/inference.py -> project root)
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _resolve_model_dir(model_dir: str) -> str:
    """Resolve model_dir to an absolute path, anchored to the project root if relative."""
    if os.path.isabs(model_dir):
        return model_dir
    return os.path.join(_PROJECT_ROOT, model_dir)


class FireSourceClassifier:
    """Load and use trained fire classification model"""

    def __init__(self, model_dir: str = "models/fire_source_classifier"):
        self.model_dir = _resolve_model_dir(model_dir)
        self.model = None
        self.label_encoder = None
        self.preprocessing_pipeline = None
        self.feature_engineer = None  # Only created if preprocessing pipeline is missing
        self.metadata = {}

        self._load_model()

    def _load_model(self):
        """Load model, label encoder, and preprocessing pipeline"""
        logger.info(f"Loading model from {self.model_dir}")

        # Load metadata
        metadata_path = os.path.join(self.model_dir, "model_metadata.json")
        if not os.path.exists(metadata_path):
            raise FileNotFoundError(
                f"Model metadata not found at {metadata_path}. "
                f"Resolved model_dir: {self.model_dir}"
            )
        with open(metadata_path, "r") as f:
            self.metadata = json.load(f)

        # Normalize model_type for file lookup (e.g., "RandomForestClassifier" -> "random_forest")
        model_type_raw = self.metadata.get("model_type", "")
        logger.info(f"Model type: {model_type_raw}")

        # Try loading with the raw model_type first, then try common patterns
        model_path = os.path.join(self.model_dir, f"model_{model_type_raw}.joblib")
        if not os.path.exists(model_path):
            # Try "final_model.joblib" as fallback (stage2d naming)
            model_path = os.path.join(self.model_dir, "final_model.joblib")
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found. Tried: model_{model_type_raw}.joblib, "
                f"final_model.joblib in {self.model_dir}"
            )
        self.model = joblib.load(model_path)
        logger.info(f"Model loaded from {model_path}")

        # Load label encoder
        label_encoder_path = os.path.join(self.model_dir, "label_encoder.joblib")
        if not os.path.exists(label_encoder_path):
            raise FileNotFoundError(f"Label encoder not found at {label_encoder_path}")
        self.label_encoder = joblib.load(label_encoder_path)
        logger.info("Label encoder loaded")

        # Load preprocessing pipeline (primary path for stage2d models)
        pipeline_path = os.path.join(self.model_dir, "preprocessing_pipeline.joblib")
        if os.path.exists(pipeline_path):
            self.preprocessing_pipeline = joblib.load(pipeline_path)
            logger.info(f"Preprocessing pipeline loaded from {pipeline_path}")
        else:
            logger.warning(f"Preprocessing pipeline not found at {pipeline_path}")
            # Fallback: try loading FeatureEngineer from feature_schema.json
            # This only works if the schema contains scaler_mean/scaler_scale
            schema_path = os.path.join(self.model_dir, "feature_schema.json")
            if os.path.exists(schema_path):
                self._load_feature_engineer_from_schema(schema_path)
            else:
                logger.error(
                    f"No preprocessing_pipeline.joblib or feature_schema.json found "
                    f"in {self.model_dir}. Predictions will use raw features."
                )

    def _load_feature_engineer_from_schema(self, schema_path: str):
        """Load a FeatureEngineer from a feature schema file (fallback path)."""
        from ml.features.engineering import FeatureEngineer
        try:
            fe = FeatureEngineer()
            fe.load_schema(schema_path)
            if fe._is_fitted:
                self.feature_engineer = fe
                logger.info(f"FeatureEngineer loaded and fitted from {schema_path}")
            else:
                logger.warning(
                    f"Feature schema at {schema_path} has no scaler parameters. "
                    f"FeatureEngineer cannot be used for preprocessing. "
                    f"Predictions will use raw features."
                )
        except Exception as e:
            logger.error(f"Failed to load FeatureEngineer from {schema_path}: {e}")

    def predict(self, features_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict fire class from features
        features_dict: dict with feature columns (must match feature_schema.json)
        Returns: prediction dict with class, confidence, probabilities
        """
        # Convert to DataFrame
        X = pd.DataFrame([features_dict])

        # Apply preprocessing: prefer sklearn pipeline, then FeatureEngineer, then raw
        if self.preprocessing_pipeline is not None:
            X_processed = self.preprocessing_pipeline.transform(X)
        elif self.feature_engineer is not None and self.feature_engineer._is_fitted:
            X_processed = self.feature_engineer.transform(X)
        else:
            # Last resort: pass raw numeric values to the model
            logger.warning("No preprocessing available, using raw feature values")
            X_processed = X.select_dtypes(include=[np.number]).values

        # Predict
        y_pred_encoded = self.model.predict(X_processed)[0]
        y_pred_proba = self.model.predict_proba(X_processed)[0]

        # Decode
        predicted_class = self.label_encoder.inverse_transform([y_pred_encoded])[0]
        confidence = float(y_pred_proba[y_pred_encoded])

        # Map probabilities to class names
        class_probabilities = {}
        for i, class_name in enumerate(self.label_encoder.classes_):
            class_probabilities[class_name] = float(y_pred_proba[i])

        return {
            "predicted_class": predicted_class,
            "confidence": confidence,
            "class_probabilities": class_probabilities,
            "model_type": self.metadata.get("model_type", "unknown"),
        }

    def predict_batch(self, features_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Predict for multiple events"""
        results = []
        for features in features_list:
            results.append(self.predict(features))
        return results
