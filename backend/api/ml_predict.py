"""
ML Prediction API Endpoint - Stage 2
POST /api/v1/ml/predict
Enhanced to accept event_id and auto-compute features from stored data
"""

import logging
from typing import Optional, Dict, Any
import json
import os
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from backend.database import Database
from backend.ml.sih_classifier import map_to_sih_category

async def get_db() -> Database:
    """Dependency injection for database"""
    from backend.main import db
    return db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/ml", tags=["ml"])

# Resolve model directory to an absolute path once, anchored to the project root
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_STAGE2D_MODEL_DIR = os.path.join(_PROJECT_ROOT, "docs", "stage2d", "models")


class PredictionRequest(BaseModel):
    """Request for ML prediction"""
    event_id: Optional[str] = None
    features: Optional[Dict[str, Any]] = None


class PredictionResponse(BaseModel):
    """ML prediction response"""
    predicted_class: str
    confidence: float
    class_probabilities: Dict[str, float]
    model_type: Optional[str] = None


# ============================================================================
# Helper Functions for Feature Computation
# ============================================================================

async def compute_features_from_event(event_id: str, db) -> Dict[str, Any]:
    """
    Compute the exact 15-feature vector for an event from stored FIRMS and enrichment data.
    Returns a dictionary with the 15 required features.
    """
    try:
        # Fetch event from database
        event_query = """
            SELECT
                id, acquisition_time, latitude, longitude, brightness, frp, confidence,
                satellite, instrument, day_night
            FROM thermal_events
            WHERE id = :event_id
            """
        event_result = await db.execute_one(event_query, {"event_id": event_id})

        if not event_result:
            raise ValueError(f"Event {event_id} not found")

        # Fetch enrichment data
        enrichment_query = """
            SELECT
                land_cover_label,
                land_cover_probabilities_json,
                acquisition_date,
                query_date,
                coverage_state
            FROM event_spatial_enrichment
            WHERE event_id = :event_id
            ORDER BY created_at DESC
            LIMIT 1
            """
        enrichment_result = await db.execute_one(enrichment_query, {"event_id": event_id})

        # Prepare the 15 features as per feature_schema.json
        features = {}

        # FIRMS features (bright_ti4, bright_ti5, scan, track, confidence, satellite, instrument, daynight, source_satellite)
        # Note: FIRMS data provides brightness temperature, but we need to estimate bright_ti4 and bright_ti5
        # For VIIRS, we have M12 (brightness) and M13 (not directly available)
        # We'll use brightness as an approximation for both bands, or derive from available data
        brightness_k = float(event_result['brightness']) if event_result['brightness'] is not None else 290.0

        # For VIIRS, we can approximate:
        # bright_ti4: similar to brightness temperature (M12 band)
        # bright_ti5: similar to brightness temperature (M13 band) - we'll use same value as approximation
        features['bright_ti4'] = brightness_k
        features['bright_ti5'] = brightness_k  # Approximation - in reality M13 is slightly different

        # Scan and track (in degrees, need to convert to km for feature engineering)
        # The feature engineering expects scan_km and track_km (0-2 range)
        features['scan'] = float(event_result.get('scan', 0.0))  # Assuming this is already in degrees
        features['track'] = float(event_result.get('track', 0.0))  # Assuming this is already in degrees

        # Confidence (0-100)
        features['confidence'] = float(event_result['confidence']) if event_result['confidence'] is not None else 0.0

        # Satellite and instrument
        features['satellite'] = event_result['satellite']
        features['instrument'] = event_result.get('instrument', 'VIIRS')

        # Day/Night
        features['daynight'] = event_result['day_night']

        # Source satellite (combination)
        features['source_satellite'] = f"{event_result['satellite']}_{event_result.get('instrument', 'VIIRS')}"

        # Dynamic World features (dw_bare, dw_confidence, dw_difference, dw_found, dw_grass, dw_water)
        # Initialize with defaults
        features['dw_bare'] = 0.1
        features['dw_water'] = 0.1
        features['dw_grass'] = 0.1
        features['dw_confidence'] = 0.5
        features['dw_difference'] = 0.0
        features['dw_found'] = 0.0

        # If we have enrichment data, update DW features
        if enrichment_result and enrichment_result['land_cover_probabilities_json']:
            try:
                probs = json.loads(enrichment_result['land_cover_probabilities_json'])
                # Map Dynamic World classes to our feature names
                # DW classes: water, trees, grass, flooded_vegetation, crops, shrub_scrub, built, bare, snow_ice
                features['dw_water'] = float(probs.get('water', 0.1))
                features['dw_grass'] = float(probs.get('grass', 0.1))
                features['dw_bare'] = float(probs.get('bare', 0.1))

                # Compute derived features as per feature engineering
                # dw_confidence: measure of classification certainty (1 - entropy, simplified)
                # We'll use max probability as confidence approximation
                max_prob = max(probs.values()) if probs else 0.5
                features['dw_confidence'] = max_prob

                # dw_difference: difference between grass and bare (as per feature engineering)
                features['dw_difference'] = abs(features['dw_grass'] - features['dw_bare'])

                # dw_found: whether DW data was successfully retrieved
                features['dw_found'] = 1.0 if enrichment_result['coverage_state'] in ['live', 'demo_mode', 'cached'] else 0.0

            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.warning(f"Could not parse DW probabilities for event {event_id}: {e}")
                # Keep default values

        return features

    except Exception as e:
        logger.error(f"Error computing features for event {event_id}: {e}")
        raise


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/predict", response_model=PredictionResponse)
async def predict(
    request: PredictionRequest,
    db: Database = Depends(get_db)
):
    """
    Predict fire class for thermal event

    If event_id provided: fetch event from database, compute features
    If features provided: use directly

    Returns predicted class, confidence, and probabilities for all 5 classes
    """
    try:
        # Determine feature source
        if request.event_id is not None:
            # Compute features from event data
            logger.info(f"Computing features from event_id: {request.event_id}")
            features_dict = await compute_features_from_event(request.event_id, db)
        elif request.features is not None:
            # Use provided features directly
            features_dict = request.features
            logger.info("Using provided features dict")
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide either 'event_id' or 'features' dict"
            )

        # Load the classifier (which includes preprocessing pipeline and model)
        from ml.models.inference import FireSourceClassifier
        # Use the pre-resolved absolute model directory
        classifier = FireSourceClassifier(model_dir=_STAGE2D_MODEL_DIR)

        # Run prediction (the classifier handles preprocessing internally)
        prediction_dict = classifier.predict(features_dict)

        # Create base ML prediction dictionary
        ml_prediction = {
            "category": prediction_dict["predicted_class"],
            "confidence": prediction_dict["confidence"],
            "probabilities": prediction_dict["class_probabilities"],
            "model_type": prediction_dict.get("model_type")
        }

        # Apply SIH classification post-processing
        # Note: We don't have persistence info here in the ml_predict endpoint,
        # so we pass None for persistence_info. The SIH classifier will handle this.
        sih_result = map_to_sih_category(ml_prediction, None)

        return PredictionResponse(
            predicted_class=sih_result["sih_category"],
            confidence=sih_result["sih_confidence"],
            class_probabilities=prediction_dict["class_probabilities"],  # Keep original 3-class probabilities
            model_type=prediction_dict.get("model_type")
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))