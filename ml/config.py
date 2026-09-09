"""
ML Pipeline Configuration - Stage 2
Centralized settings for training, inference, and time-window analysis
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Tuple
import os


class TimeWindow(Enum):
    """Centralized time-window definitions for analysis"""
    TODAY = "TODAY"
    LAST_24_HOURS = "LAST_24_HOURS"
    LAST_7_DAYS = "LAST_7_DAYS"
    LAST_30_DAYS = "LAST_30_DAYS"

    def get_start_time(self, reference_time: datetime = None) -> datetime:
        """Get start of time window relative to reference_time (defaults to now)"""
        if reference_time is None:
            reference_time = datetime.utcnow()

        if self == TimeWindow.TODAY:
            # Start of today (UTC)
            return reference_time.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self == TimeWindow.LAST_24_HOURS:
            return reference_time - timedelta(hours=24)
        elif self == TimeWindow.LAST_7_DAYS:
            return reference_time - timedelta(days=7)
        elif self == TimeWindow.LAST_30_DAYS:
            return reference_time - timedelta(days=30)

    def get_end_time(self, reference_time: datetime = None) -> datetime:
        """Get end of time window (always reference_time)"""
        return reference_time if reference_time else datetime.utcnow()

    def get_sql_filter(self, column_name: str = "acquisition_time", reference_time: datetime = None) -> Tuple[str, dict]:
        """
        Get SQL WHERE clause and parameters for time window filtering
        Returns (where_clause, params_dict)
        """
        start = self.get_start_time(reference_time)
        end = self.get_end_time(reference_time)

        where_clause = f"{column_name} >= :start_time AND {column_name} <= :end_time"
        params = {
            "start_time": start,
            "end_time": end
        }
        return where_clause, params


class MLConfig:
    """ML pipeline configuration"""

    # ========================================================================
    # Random seed for reproducibility
    # ========================================================================
    RANDOM_SEED: int = 42

    # ========================================================================
    # Model paths
    # ========================================================================
    MODEL_DIR: str = os.getenv("ML_MODEL_DIR", "models/fire_source_classifier")
    DATA_DIR: str = os.getenv("ML_DATA_DIR", "data")

    # ========================================================================
    # Training configuration
    # ========================================================================
    TRAIN_TEST_SPLIT_RATIO: float = 0.8  # 80% train+val, 20% test
    TRAIN_VAL_SPLIT_RATIO: float = 0.75  # Of train+val: 75% train, 25% val
    # Effective: 60% train, 20% val, 20% test

    # ========================================================================
    # Class weights for imbalanced data
    # ========================================================================
    CLASS_WEIGHTS: dict = {
        "Industrial Fire": 1.0,
        "Wildfire / Natural Fire": 1.0,
        "Agricultural Fire": 1.0,
        "Persistent Thermal Source": 1.2,  # Slightly upweight persistent
        "Unknown / Other": 1.0,
    }

    # ========================================================================
    # Feature scaling
    # ========================================================================
    FEATURE_SCALER_TYPE: str = "standard"  # StandardScaler

    # ========================================================================
    # Random Forest hyperparameters
    # ========================================================================
    RF_N_ESTIMATORS: int = 100
    RF_MAX_DEPTH: int = 15
    RF_MIN_SAMPLES_SPLIT: int = 5
    RF_MIN_SAMPLES_LEAF: int = 2
    RF_CLASS_WEIGHT: str = "balanced"

    # ========================================================================
    # XGBoost hyperparameters
    # ========================================================================
    XGB_N_ESTIMATORS: int = 100
    XGB_MAX_DEPTH: int = 6
    XGB_LEARNING_RATE: float = 0.1
    XGB_SUBSAMPLE: float = 0.8
    XGB_COLSAMPLE_BYTREE: float = 0.8

    # ========================================================================
    # Default time window for analysis
    # ========================================================================
    DEFAULT_TIME_WINDOW: TimeWindow = TimeWindow.LAST_24_HOURS

    # ========================================================================
    # Five fire classification classes
    # ========================================================================
    FIRE_CLASSES: list = [
        "Industrial Fire",
        "Wildfire / Natural Fire",
        "Agricultural Fire",
        "Persistent Thermal Source",
        "Unknown / Other",
    ]

    # ========================================================================
    # Feature column names (from CSV)
    # ========================================================================
    FIRMS_FEATURES: list = [
        "frp",
        "brightness_temperature_k",
        "firms_confidence",
        "scan_km",
        "track_km",
        "day_night",
        "satellite",
    ]

    OSM_FEATURES: list = [
        "nearest_facility_type",
        "nearest_facility_distance_m",
        "industrial_context_score",
        "nearest_water_distance_m",
    ]

    DYNAMIC_WORLD_FEATURES: list = [
        "dw_water",
        "dw_trees",
        "dw_grass",
        "dw_flooded_vegetation",
        "dw_crops",
        "dw_shrub_scrub",
        "dw_built",
        "dw_bare",
        "dw_snow_ice",
        "dw_dominant_class",
        "dw_confidence",
    ]

    PERSISTENCE_FEATURES: list = [
        "detections_24h",
        "detections_3d",
        "detections_7d",
        "active_days",
        "persistence_duration_days",
        "mean_frp",
        "max_frp",
    ]

    LOCATION_FEATURES: list = [
        "latitude",
        "longitude",
    ]

    TEMPORAL_FEATURES: list = [
        "acquisition_datetime",
    ]
