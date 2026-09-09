"""
Data loading and validation for Stage 2 ML pipeline
Integrates with PostgreSQL/PostGIS database
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Tuple, Dict, List, Optional
import os

logger = logging.getLogger(__name__)


class DataLoader:
    """Load and manage training data from CSV and PostgreSQL"""

    def __init__(self):
        self.df = None
        self.feature_columns = None
        self.target_column = "target_class"

    def load_csv(self, csv_path: str) -> pd.DataFrame:
        """Load CSV file and perform basic validation"""
        logger.info(f"Loading CSV from {csv_path}")

        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV not found: {csv_path}")

        df = pd.read_csv(csv_path)
        logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")

        # Validate required columns
        required_cols = [
            "latitude", "longitude", "acquisition_datetime",
            "frp", "brightness_temperature_k", "firms_confidence",
            "scan_km", "track_km", "day_night", "satellite",
            "nearest_facility_distance_m", "industrial_context_score", "nearest_water_distance_m",
            "dw_water", "dw_trees", "dw_grass", "dw_flooded_vegetation", "dw_crops",
            "dw_shrub_scrub", "dw_built", "dw_bare", "dw_snow_ice", "dw_confidence",
            "detections_24h", "detections_3d", "detections_7d", "active_days",
            "persistence_duration_days", "mean_frp", "max_frp",
            "target_class", "is_demo", "dataset_type"
        ]

        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing columns: {missing_cols}")

        logger.info(f"Schema validation passed")
        self.df = df
        return df

    def validate_data(self) -> Dict:
        """Validate data integrity"""
        if self.df is None:
            raise ValueError("No data loaded")

        stats = {
            "total_rows": len(self.df),
            "total_columns": len(self.df.columns),
            "classes": {},
            "missing_values": {},
            "coordinate_errors": 0,
            "timestamp_errors": 0,
            "duplicates": 0,
        }

        # Class distribution
        for cls in self.df[self.target_column].unique():
            count = len(self.df[self.df[self.target_column] == cls])
            stats["classes"][cls] = count
            logger.info(f"  {cls}: {count} ({100*count/len(self.df):.1f}%)")

        # Missing values
        for col in self.df.columns:
            missing_count = self.df[col].isna().sum()
            if missing_count > 0:
                stats["missing_values"][col] = missing_count

        if stats["missing_values"]:
            logger.warning(f"Missing values: {stats['missing_values']}")

        # Coordinate validation
        invalid_coords = (
            (self.df["latitude"] < 8.0) | (self.df["latitude"] > 35.0) |
            (self.df["longitude"] < 68.0) | (self.df["longitude"] > 97.0)
        ).sum()
        stats["coordinate_errors"] = invalid_coords
        if invalid_coords > 0:
            logger.warning(f"Invalid coordinates: {invalid_coords}")

        # Duplicate check (lat, lon, datetime, satellite)
        if "satellite" in self.df.columns:
            df_dup = self.df.round({"latitude": 4, "longitude": 4})
            duplicates = df_dup.duplicated(
                subset=["latitude", "longitude", "acquisition_datetime", "satellite"],
                keep=False
            ).sum()
            stats["duplicates"] = duplicates
            if duplicates > 0:
                logger.warning(f"Potential duplicates: {duplicates}")

        logger.info(f"Validation complete: {stats}")
        return stats

    def prepare_features_and_target(self) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare feature matrix and target for ML"""
        if self.df is None:
            raise ValueError("No data loaded")

        # Drop rows with missing target
        df_clean = self.df.dropna(subset=[self.target_column])
        initial_rows = len(self.df)
        rows_after = len(df_clean)
        logger.info(f"Dropped {initial_rows - rows_after} rows with missing target")

        # Feature columns: exclude metadata and target
        exclude_cols = {
            "event_id", "dataset_type", "is_demo", "target_class",
            "nearest_facility_type", "dw_dominant_class"  # Categorical, handled separately
        }

        X_cols = [col for col in df_clean.columns if col not in exclude_cols]

        # Handle missing values in features: forward-fill then backward-fill then median
        X = df_clean[X_cols].copy()
        for col in X.columns:
            if X[col].isna().any():
                # Use median for numeric columns
                if X[col].dtype in ["float64", "int64"]:
                    X[col].fillna(X[col].median(), inplace=True)
                else:
                    X[col].fillna(X[col].mode()[0] if len(X[col].mode()) > 0 else "unknown", inplace=True)

        y = df_clean[self.target_column].copy()

        logger.info(f"Features shape: {X.shape}, Target shape: {y.shape}")

        return X, y, X_cols

    def temporal_train_val_test_split(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        train_ratio: float = 0.6,
        val_ratio: float = 0.2,
        seed: int = 42
    ) -> Tuple[Tuple, Tuple, Tuple]:
        """
        Split data by time to prevent temporal leakage
        Returns (X_train, y_train), (X_val, y_val), (X_test, y_test)
        """
        np.random.seed(seed)

        # Add index for sorting
        df_combined = pd.DataFrame({
            "X_idx": range(len(X)),
            "features": [X.iloc[i].values for i in range(len(X))],
            "target": y.values,
            "datetime": X["acquisition_datetime"] if "acquisition_datetime" in X.columns else [datetime.utcnow()] * len(X)
        })

        # Sort by datetime
        df_combined = df_combined.sort_values("datetime").reset_index(drop=True)

        # Temporal split
        n = len(df_combined)
        train_end = int(n * train_ratio)
        val_end = int(n * (train_ratio + val_ratio))

        train_idx = df_combined.iloc[:train_end]["X_idx"].values
        val_idx = df_combined.iloc[train_end:val_end]["X_idx"].values
        test_idx = df_combined.iloc[val_end:]["X_idx"].values

        X_train, y_train = X.iloc[train_idx], y.iloc[train_idx]
        X_val, y_val = X.iloc[val_idx], y.iloc[val_idx]
        X_test, y_test = X.iloc[test_idx], y.iloc[test_idx]

        logger.info(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
        logger.info(f"Class distribution - Train: {y_train.value_counts().to_dict()}")

        return (X_train, y_train), (X_val, y_val), (X_test, y_test)


def load_demo_data(csv_path: str) -> Tuple[pd.DataFrame, pd.Series, List[str]]:
    """High-level function to load and prepare demo data"""
    loader = DataLoader()
    df = loader.load_csv(csv_path)

    stats = loader.validate_data()
    logger.info(f"Data validation stats: {stats}")

    X, y, feature_cols = loader.prepare_features_and_target()

    return X, y, feature_cols
