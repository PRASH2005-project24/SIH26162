"""
Feature Engineering Pipeline for Stage 2
Centralized preprocessing used by both training and inference
"""

import logging
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from datetime import datetime
import json
from typing import Dict, List, Tuple, Any
import os

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Centralized feature engineering pipeline
    Used identically in training and inference to prevent leakage
    """

    def __init__(self):
        self.scaler = StandardScaler()
        self.feature_names = []
        self.feature_schema = {}
        self._is_fitted = False

    def fit(self, X: pd.DataFrame) -> "FeatureEngineer":
        """
        Learn feature transformations from training data
        X: input features (DataFrame)
        """
        logger.info("Fitting feature engineer...")

        # Create engineered features
        X_eng = self._engineer_features(X.copy(), fit_mode=True)

        # Fit scaler
        self.scaler.fit(X_eng)

        self.feature_names = X_eng.columns.tolist()
        self.feature_schema = {
            "feature_names": self.feature_names,
            "scaler_mean": self.scaler.mean_.tolist(),
            "scaler_scale": self.scaler.scale_.tolist(),
            "version": "1.0",
            "fit_datetime": datetime.utcnow().isoformat(),
        }

        self._is_fitted = True
        logger.info(f"Feature engineer fitted. Features: {len(self.feature_names)}")
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """
        Apply learned transformations to data
        Returns scaled feature matrix (numpy array)
        """
        if not self._is_fitted:
            raise ValueError("FeatureEngineer not fitted. Call fit() first.")

        X_eng = self._engineer_features(X.copy(), fit_mode=False)

        # Ensure columns match fitted schema
        X_eng = X_eng[self.feature_names]

        # Scale
        X_scaled = self.scaler.transform(X_eng)

        return X_scaled

    def _engineer_features(self, X: pd.DataFrame, fit_mode: bool = False) -> pd.DataFrame:
        """
        Create engineered features from raw data
        fit_mode: if True, learn any parameters; if False, apply learned params
        """
        X_out = X.copy()

        # ====================================================================
        # FIRMS Features
        # ====================================================================
        # FRP: log transform
        if "frp" in X_out.columns:
            X_out["frp_log"] = np.log1p(X_out["frp"])

        # Brightness: standardize to 0-1
        if "brightness_temperature_k" in X_out.columns:
            X_out["brightness_norm"] = (X_out["brightness_temperature_k"] - 273.15) / 100.0
            X_out["brightness_norm"] = X_out["brightness_norm"].clip(0, 1)

        # Confidence: already 0-100, normalize to 0-1
        if "firms_confidence" in X_out.columns:
            X_out["confidence_norm"] = X_out["firms_confidence"] / 100.0

        # Scan and track: already normalized (0-2 range), keep as-is
        if "scan_km" in X_out.columns:
            X_out["scan_norm"] = X_out["scan_km"] / 2.0
        if "track_km" in X_out.columns:
            X_out["track_norm"] = X_out["track_km"] / 2.0

        # Day/night: one-hot encoding
        if "day_night" in X_out.columns:
            X_out["day_night_D"] = (X_out["day_night"] == "D").astype(float)
            X_out["day_night_N"] = (X_out["day_night"] == "N").astype(float)

        # Satellite: one-hot encoding
        if "satellite" in X_out.columns:
            X_out["satellite_VIIRS"] = (X_out["satellite"] == "VIIRS").astype(float)
            X_out["satellite_MODIS"] = (X_out["satellite"] == "MODIS").astype(float)

        # ====================================================================
        # OSM Features
        # ====================================================================
        # Nearest facility distance: log transform
        if "nearest_facility_distance_m" in X_out.columns:
            X_out["facility_distance_log"] = np.log1p(X_out["nearest_facility_distance_m"])

        # Industrial context score: already 0-1
        if "industrial_context_score" in X_out.columns:
            X_out["industrial_context"] = X_out["industrial_context_score"]

        # Nearest water distance: log transform
        if "nearest_water_distance_m" in X_out.columns:
            X_out["water_distance_log"] = np.log1p(X_out["nearest_water_distance_m"])

        # ====================================================================
        # Dynamic World Features (9 land cover classes) - direct use, no normalization
        # ====================================================================
        dw_cols = [
            "dw_water", "dw_trees", "dw_grass", "dw_flooded_vegetation",
            "dw_crops", "dw_shrub_scrub", "dw_built", "dw_bare", "dw_snow_ice"
        ]

        # Keep DW columns as-is (already probabilities 0-1)
        for col in dw_cols:
            if col in X_out.columns:
                # Ensure they're numeric
                X_out[col] = pd.to_numeric(X_out[col], errors='coerce').fillna(0)

        # DW confidence: already 0-1
        if "dw_confidence" in X_out.columns:
            X_out["dw_confidence"] = pd.to_numeric(X_out["dw_confidence"], errors='coerce').fillna(0)

        # ====================================================================
        # Temporal/Persistence Features
        # ====================================================================
        # Detection counts: log transform
        for col in ["detections_24h", "detections_3d", "detections_7d"]:
            if col in X_out.columns:
                X_out[f"{col}_log"] = np.log1p(X_out[col])

        # Active days: already count, log transform
        if "active_days" in X_out.columns:
            X_out["active_days_log"] = np.log1p(X_out["active_days"])

        # Persistence duration: log transform
        if "persistence_duration_days" in X_out.columns:
            X_out["persistence_log"] = np.log1p(X_out["persistence_duration_days"])

        # Mean and max FRP: log transform
        if "mean_frp" in X_out.columns:
            X_out["mean_frp_log"] = np.log1p(X_out["mean_frp"])
        if "max_frp" in X_out.columns:
            X_out["max_frp_log"] = np.log1p(X_out["max_frp"])

        # ====================================================================
        # Temporal features from datetime
        # ====================================================================
        if "acquisition_datetime" in X_out.columns:
            # Parse datetime
            X_out["datetime"] = pd.to_datetime(X_out["acquisition_datetime"], errors="coerce")

            # Hour (0-23)
            X_out["hour"] = X_out["datetime"].dt.hour

            # Hour as circular (sin/cos encoding)
            X_out["hour_sin"] = np.sin(2 * np.pi * X_out["hour"] / 24.0)
            X_out["hour_cos"] = np.cos(2 * np.pi * X_out["hour"] / 24.0)

            # Day of week (0-6)
            X_out["day_of_week"] = X_out["datetime"].dt.dayofweek

            # Day of week as circular
            X_out["dow_sin"] = np.sin(2 * np.pi * X_out["day_of_week"] / 7.0)
            X_out["dow_cos"] = np.cos(2 * np.pi * X_out["day_of_week"] / 7.0)

            # Month (0-11)
            X_out["month"] = X_out["datetime"].dt.month - 1

            # Month as circular
            X_out["month_sin"] = np.sin(2 * np.pi * X_out["month"] / 12.0)
            X_out["month_cos"] = np.cos(2 * np.pi * X_out["month"] / 12.0)

        # ====================================================================
        # Select final feature columns (NO DUPLICATES)
        # ====================================================================
        final_cols = [
            "frp_log", "brightness_norm", "confidence_norm", "scan_norm", "track_norm",
            "day_night_D", "day_night_N", "satellite_VIIRS", "satellite_MODIS",
            "facility_distance_log", "industrial_context", "water_distance_log",
            "dw_water", "dw_trees", "dw_grass", "dw_flooded_vegetation", "dw_crops",
            "dw_shrub_scrub", "dw_built", "dw_bare", "dw_snow_ice", "dw_confidence",
            "detections_24h_log", "detections_3d_log", "detections_7d_log",
            "active_days_log", "persistence_log", "mean_frp_log", "max_frp_log",
            "hour_sin", "hour_cos", "dow_sin", "dow_cos", "month_sin", "month_cos"
        ]

        # Filter to columns that exist
        final_cols = [col for col in final_cols if col in X_out.columns]

        return X_out[final_cols]

    def get_schema(self) -> Dict[str, Any]:
        """Get feature schema for saving/loading"""
        return self.feature_schema

    def save_schema(self, filepath: str):
        """Save feature schema to JSON"""
        with open(filepath, "w") as f:
            json.dump(self.feature_schema, f, indent=2)
        logger.info(f"Feature schema saved to {filepath}")

    def load_schema(self, filepath: str):
        """Load feature schema from JSON"""
        with open(filepath, "r") as f:
            schema = json.load(f)

        # Handle both old and new schema formats
        if "feature_names" in schema:
            self.feature_names = schema["feature_names"]
        elif "model_input_features" in schema:
            self.feature_names = schema["model_input_features"]
        else:
            raise ValueError("Schema must contain either 'feature_names' or 'model_input_features'")

        # If scaler parameters are present, load them
        if "scaler_mean" in schema and "scaler_scale" in schema:
            self.scaler.mean_ = np.array(schema["scaler_mean"])
            self.scaler.scale_ = np.array(schema["scaler_scale"])
            self._is_fitted = True
        else:
            # If no scaler parameters, we are not fitted
            self._is_fitted = False
            logger.warning("No scaler parameters found in schema. FeatureEngineer is not fitted.")

        self.feature_schema = schema
        logger.info(f"Feature schema loaded from {filepath}")
