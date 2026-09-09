"""
Model Training - Stage 2 ML Pipeline
Random Forest + XGBoost baseline models
"""

import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import json
from datetime import datetime
from typing import Tuple, Dict, Any
import os

try:
    import xgboost as xgb
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    logging.warning("XGBoost not available, will use RandomForest only")

logger = logging.getLogger(__name__)


class ModelTrainer:
    """Train and manage ML models"""

    def __init__(self, model_dir: str = "models/fire_source_classifier"):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)

        self.rf_model = None
        self.xgb_model = None
        self.label_encoder = LabelEncoder()
        self.selected_model = None
        self.selected_model_name = None

    def train(
        self,
        X_train: np.ndarray,
        y_train: pd.Series,
        X_val: np.ndarray,
        y_val: pd.Series,
        feature_names: list,
        class_names: list = None
    ) -> Dict[str, Any]:
        """
        Train RandomForest and XGBoost models
        Returns training metadata
        """
        logger.info("Starting model training...")

        # Encode labels
        y_train_encoded = self.label_encoder.fit_transform(y_train)
        y_val_encoded = self.label_encoder.transform(y_val)

        if class_names is None:
            class_names = self.label_encoder.classes_.tolist()

        metadata = {
            "timestamp": datetime.utcnow().isoformat(),
            "random_seed": 42,
            "class_names": class_names,
            "n_classes": len(class_names),
            "train_samples": len(X_train),
            "val_samples": len(X_val),
            "n_features": X_train.shape[1],
        }

        # ====================================================================
        # Random Forest
        # ====================================================================
        logger.info("Training RandomForest...")
        self.rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=42,
            n_jobs=-1,
            verbose=0
        )

        self.rf_model.fit(X_train, y_train_encoded)

        rf_train_score = self.rf_model.score(X_train, y_train_encoded)
        rf_val_score = self.rf_model.score(X_val, y_val_encoded)

        logger.info(f"RandomForest - Train: {rf_train_score:.4f}, Val: {rf_val_score:.4f}")

        metadata["rf_train_accuracy"] = rf_train_score
        metadata["rf_val_accuracy"] = rf_val_score

        # ====================================================================
        # XGBoost (if available)
        # ====================================================================
        if XGB_AVAILABLE:
            logger.info("Training XGBoost...")
            try:
                self.xgb_model = xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    tree_method="hist",  # GPU-compatible if CUDA available
                    device="cuda",  # Try GPU first
                    eval_metric="mlogloss",
                    verbosity=0
                )
            except Exception as e:
                logger.warning(f"XGBoost GPU failed, falling back to CPU: {e}")
                self.xgb_model = xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    eval_metric="mlogloss",
                    verbosity=0
                )

            self.xgb_model.fit(
                X_train, y_train_encoded,
                eval_set=[(X_val, y_val_encoded)],
                verbose=False
            )

            xgb_train_score = self.xgb_model.score(X_train, y_train_encoded)
            xgb_val_score = self.xgb_model.score(X_val, y_val_encoded)

            logger.info(f"XGBoost - Train: {xgb_train_score:.4f}, Val: {xgb_val_score:.4f}")

            metadata["xgb_train_accuracy"] = xgb_train_score
            metadata["xgb_val_accuracy"] = xgb_val_score

            # Select best model based on validation score
            if xgb_val_score >= rf_val_score:
                self.selected_model = self.xgb_model
                self.selected_model_name = "xgboost"
                metadata["selected_model"] = "xgboost"
            else:
                self.selected_model = self.rf_model
                self.selected_model_name = "random_forest"
                metadata["selected_model"] = "random_forest"
        else:
            self.selected_model = self.rf_model
            self.selected_model_name = "random_forest"
            metadata["selected_model"] = "random_forest"

        logger.info(f"Selected model: {self.selected_model_name}")

        return metadata

    def save_model(self, feature_names: list, class_names: list):
        """Save trained model and metadata"""
        if self.selected_model is None:
            raise ValueError("No model trained")

        # Save model
        model_path = os.path.join(self.model_dir, f"model_{self.selected_model_name}.joblib")
        joblib.dump(self.selected_model, model_path)
        logger.info(f"Model saved to {model_path}")

        # Save label encoder
        label_encoder_path = os.path.join(self.model_dir, "label_encoder.joblib")
        joblib.dump(self.label_encoder, label_encoder_path)
        logger.info(f"Label encoder saved to {label_encoder_path}")

        # Save metadata
        metadata = {
            "model_type": self.selected_model_name,
            "class_names": class_names,
            "feature_names": feature_names,
            "n_features": len(feature_names),
            "n_classes": len(class_names),
            "timestamp": datetime.utcnow().isoformat(),
        }

        metadata_path = os.path.join(self.model_dir, "model_metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Metadata saved to {metadata_path}")

        return {
            "model_path": model_path,
            "label_encoder_path": label_encoder_path,
            "metadata_path": metadata_path,
        }
