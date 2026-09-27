"""
ML Prediction API Endpoint - Stage 2
POST /api/v1/ml/predict
Enhanced to accept event_id and auto-compute features from stored data
"""

import logging
from typing import Optional, Dict, Any
import json
import os

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


# Resolve model directory to an absolute path once,
# anchored to the project root.
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)
_STAGE2D_MODEL_DIR = os.path.join(
    _PROJECT_ROOT, "docs", "stage2d", "models", "source_neutral_classifier"
)


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

async def compute_features_from_event(
    event_id: str,
    db
) -> Dict[str, Any]:
    """
    Compute the exact 15-feature vector for an event from stored FIRMS
    and enrichment data.

    Returns a dictionary containing the 15 required model features.
    """

    try:
        # --------------------------------------------------------------------
        # Fetch event from database
        # --------------------------------------------------------------------
        event_query = """
            SELECT
                id,
                acquisition_time,
                latitude,
                longitude,
                brightness,
                bright_ti5,
                frp,
                confidence,
                confidence_class,
                model_satellite,
                source_satellite,
                satellite,
                instrument,
                day_night,
                scan,
                track
            FROM thermal_events
            WHERE id = :event_id
        """

        event_result = await db.execute_one(
            event_query,
            {"event_id": event_id}
        )

        if not event_result:
            raise ValueError(f"Event {event_id} not found")

        # --------------------------------------------------------------------
        # Fetch latest enrichment data
        # --------------------------------------------------------------------
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

        enrichment_result = await db.execute_one(
            enrichment_query,
            {"event_id": event_id}
        )

        # --------------------------------------------------------------------
        # Prepare the 15 features
        # --------------------------------------------------------------------
        features: Dict[str, Any] = {}

        # --------------------------------------------------------------------
        # FIRMS features
        #
        # Schema:
        # bright_ti4
        # bright_ti5
        # scan
        # track
        # confidence
        # satellite
        # instrument
        # daynight
        # source_satellite
        # --------------------------------------------------------------------

        brightness_k = (
            float(event_result["brightness"])
            if event_result["brightness"] is not None
            else 290.0
        )

        # Current Stage 2D implementation uses brightness
        # as the approximation for both bands.
        features["bright_ti4"] = brightness_k
        features["bright_ti5"] = (
            float(event_result["bright_ti5"])
            if event_result.get("bright_ti5") is not None
            else float("nan")
        )

        # Use the actual FIRMS values stored in thermal_events.
        features["scan"] = (
            float(event_result["scan"])
            if event_result["scan"] is not None
            else 0.0
        )

        features["track"] = (
            float(event_result["track"])
            if event_result["track"] is not None
            else 0.0
        )

        confidence_class = event_result.get("confidence_class")
        if confidence_class not in {"l", "n", "h"}:
            numeric_confidence = event_result.get("confidence")
            if numeric_confidence is None:
                confidence_class = None
            else:
                numeric_confidence = float(numeric_confidence)
                confidence_class = "h" if numeric_confidence >= 80 else "l" if numeric_confidence <= 30 else "n"
        features["confidence"] = confidence_class

        features["satellite"] = event_result.get("model_satellite") or event_result["satellite"]

        features["instrument"] = (
            event_result["instrument"]
            if event_result["instrument"] is not None
            else "VIIRS"
        )

        features["daynight"] = event_result["day_night"]

        # Source satellite is the same combination used by
        # the existing Stage 2D feature construction.
        features["source_satellite"] = event_result.get("source_satellite") or str(features["satellite"])

        # --------------------------------------------------------------------
        # Dynamic World features
        # --------------------------------------------------------------------

        # Defaults used when usable DW probability data is unavailable.
        features["dw_bare"] = float("nan")
        features["dw_water"] = float("nan")
        features["dw_grass"] = float("nan")
        features["dw_confidence"] = float("nan")
        features["dw_difference"] = float("nan")
        features["dw_found"] = 0.0

        if enrichment_result:
            coverage_state = enrichment_result.get("coverage_state")

            # coverage_state is stored in the form:
            #
            #     osm:live,dw:cached
            #
            #     osm:live,dw:live
            #
            #     osm:source_unavailable,dw:no_valid_pixel
            #
            # Extract the Dynamic World state specifically.
            dw_state = None

            if coverage_state:
                for state_part in str(coverage_state).split(","):
                    state_part = state_part.strip()

                    if state_part.startswith("dw:"):
                        dw_state = state_part.split(":", 1)[1].strip()
                        break

            # A DW result is considered found when its provider state
            # indicates that usable data was retrieved/cached.
            # ---------------------------------------------------------------
            # Parse Dynamic World probabilities
            # ---------------------------------------------------------------
            probabilities_json = (
                enrichment_result.get(
                    "land_cover_probabilities_json"
                )
            )

            if probabilities_json:
                try:
                    probs = json.loads(probabilities_json)

                    if not isinstance(probs, dict):
                        raise TypeError(
                            "Dynamic World probabilities are not a dictionary"
                        )

                    if dw_state not in {"live", "cached"} or not all(
                        key in probs for key in ("water", "grass", "bare")
                    ):
                        probs = {}

                    if probs:
                        features["dw_found"] = 1.0

                    # Dynamic World classes:
                    # water, trees, grass, flooded_vegetation,
                    # crops, shrub_scrub, built, bare, snow_ice

                    features["dw_water"] = float(probs["water"])

                    features["dw_grass"] = float(
                        probs["grass"]
                    )

                    features["dw_bare"] = float(
                        probs["bare"]
                    )

                    # Maximum class probability as the current
                    # confidence approximation.
                    max_prob = (
                        max(probs.values())
                        if probs
                        else 0.5
                    )

                    features["dw_confidence"] = float(max_prob)

                    # Difference between grass and bare probabilities.
                    features["dw_difference"] = abs(
                        features["dw_grass"]
                        - features["dw_bare"]
                    )

                except (
                    json.JSONDecodeError,
                    KeyError,
                    TypeError,
                    ValueError
                ) as e:
                    logger.warning(
                        f"Could not parse DW probabilities "
                        f"for event {event_id}: {e}"
                    )

        # --------------------------------------------------------------------
        # Final feature validation
        # --------------------------------------------------------------------

        expected_features = [
            "bright_ti4",
            "bright_ti5",
            "scan",
            "track",
            "confidence",
            "satellite",
            "instrument",
            "daynight",
            "source_satellite",
            "dw_bare",
            "dw_confidence",
            "dw_difference",
            "dw_found",
            "dw_grass",
            "dw_water",
        ]

        missing_features = [
            name for name in expected_features
            if name not in features
        ]

        if missing_features:
            raise ValueError(
                f"Missing model features for event {event_id}: "
                f"{missing_features}"
            )

        logger.info(
            f"Computed 15 ML features for event {event_id}: "
            f"scan={features['scan']}, "
            f"track={features['track']}, "
            f"dw_found={features['dw_found']}"
        )

        return features

    except Exception as e:
        logger.error(
            f"Error computing features for event {event_id}: {e}"
        )
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
    Predict fire class for a thermal event.

    If event_id is provided:
        Fetch event from database and compute features.

    If features is provided:
        Use the supplied feature dictionary directly.

    Returns the SIH post-processed category together with
    the original 3-class ML probabilities.
    """

    try:
        # --------------------------------------------------------------------
        # Determine feature source
        # --------------------------------------------------------------------

        if request.event_id is not None:

            logger.info(
                f"Computing features from event_id: "
                f"{request.event_id}"
            )

            features_dict = await compute_features_from_event(
                request.event_id,
                db
            )

        elif request.features is not None:

            features_dict = request.features
            logger.info("Using provided features dict")

        else:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Must provide either 'event_id' "
                    "or 'features' dict"
                )
            )

        # --------------------------------------------------------------------
        # Load classifier
        # --------------------------------------------------------------------

        from ml.models.inference import FireSourceClassifier

        classifier = FireSourceClassifier(
            model_dir=_STAGE2D_MODEL_DIR
        )

        # --------------------------------------------------------------------
        # Run prediction
        # --------------------------------------------------------------------

        prediction_dict = classifier.predict(
            features_dict
        )

        # --------------------------------------------------------------------
        # Create base ML prediction dictionary
        # --------------------------------------------------------------------

        ml_prediction = {
            "category": prediction_dict["predicted_class"],
            "confidence": prediction_dict["confidence"],
            "probabilities": prediction_dict["class_probabilities"],
            "model_type": prediction_dict.get("model_type"),
        }

        # --------------------------------------------------------------------
        # SIH post-processing
        #
        # This endpoint does not calculate persistence information.
        # The full classifier engine performs persistence analysis.
        # --------------------------------------------------------------------

        sih_result = map_to_sih_category(
            ml_prediction,
            None
        )

        return PredictionResponse(
            predicted_class=sih_result["sih_category"],
            confidence=sih_result["sih_confidence"],
            class_probabilities=prediction_dict[
                "class_probabilities"
            ],
            model_type=prediction_dict.get("model_type"),
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(
            f"Prediction error: {e}",
            exc_info=True
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )