import logging
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from backend.database import Database
from backend.config import Config
from backend.api.ml_predict import compute_features_from_event
from ml.models.inference import FireSourceClassifier
from backend.ml.sih_classifier import map_to_sih_category
from backend.api.events import PersistenceResponse
import os

logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_STAGE2D_MODEL_DIR = os.path.join(_PROJECT_ROOT, "docs", "stage2d", "models")

class ClassifierEngine:
    """
    Engine to compute features, run ML classification, compute persistence,
    map to SIH category, and persist the results to PostgreSQL.
    """

    def __init__(self, db: Database, config: Config):
        self.db = db
        self.config = config
        
        try:
            self.classifier = FireSourceClassifier(model_dir=_STAGE2D_MODEL_DIR)
        except Exception as e:
            logger.error(f"Failed to load FireSourceClassifier: {e}")
            self.classifier = None

    async def classify_batch(self, event_ids: List[str]) -> Dict[str, int]:
        """Classify a batch of events and persist the results."""
        results = {"successful": 0, "failed": 0}
        
        for event_id in event_ids:
            try:
                success = await self._classify_and_persist(event_id)
                if success:
                    results["successful"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.error(f"Error classifying event {event_id}: {e}", exc_info=True)
                results["failed"] += 1
                
        return results

    async def _classify_and_persist(self, event_id: str) -> bool:
        """Classify a single event and store result."""
        
        ml_prediction = None
        inference_error = None
        
        if self.classifier:
            try:
                # 1. Compute features
                features_dict = await compute_features_from_event(event_id, self.db)
                
                # 2. Run prediction
                prediction_dict = self.classifier.predict(features_dict)
                
                ml_prediction = {
                    "category": prediction_dict["predicted_class"],
                    "confidence": prediction_dict["confidence"],
                    "probabilities": prediction_dict["class_probabilities"],
                    "model_type": prediction_dict.get("model_type", "Random Forest")
                }
            except Exception as e:
                inference_error = f"ML inference failed: {str(e)}"
                logger.warning(f"Event {event_id}: {inference_error}")
        else:
            inference_error = "Classifier model not loaded"

        # 3. Get persistence info
        persistence_info = await self._get_persistence_info(event_id)

        # 4. Map to SIH Category
        sih_result = {
            "sih_category": "Unknown / Other",
            "sih_confidence": 0.0
        }
        
        if ml_prediction:
            sih_result = map_to_sih_category(ml_prediction, persistence_info)
        elif persistence_info and persistence_info.is_persistent:
            sih_result["sih_category"] = "Persistent Thermal Source"

        # 5. Persist to database
        return await self._persist_classification(
            event_id=event_id,
            ml_prediction=ml_prediction,
            persistence_info=persistence_info,
            sih_category=sih_result["sih_category"],
            inference_error=inference_error
        )

    async def _get_persistence_info(self, event_id: str) -> Optional[PersistenceResponse]:
        """Get persistence information from historical events."""
        event_query = """
            SELECT latitude, longitude, acquisition_time
            FROM thermal_events
            WHERE id = :event_id
        """
        event_result = await self.db.execute_one(event_query, {"event_id": event_id})
        
        if not event_result:
            return None

        # 1km radius, only past observations
        persistence_query = """
            SELECT
                acquisition_time::date as event_date
            FROM thermal_events
            WHERE
                id != :event_id
                AND acquisition_time <= :event_time
                AND ST_DWithin(
                    ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)::geography,
                    ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)::geography,
                    1000
                )
            ORDER BY acquisition_time::date
        """
        
        acq_time = event_result["acquisition_time"]
        if isinstance(acq_time, str):
            from datetime import datetime
            try:
                # Handle cases where 'Z' is appended or milliseconds are included
                acq_time = datetime.fromisoformat(acq_time.replace('Z', '+00:00'))
            except ValueError:
                pass

        historical_events = await self.db.execute(persistence_query, {
            "event_id": event_id,
            "event_time": acq_time,
            "latitude": float(event_result["latitude"]),
            "longitude": float(event_result["longitude"])
        })
        
        if not historical_events:
            return PersistenceResponse(
                is_persistent=False,
                date_count=0,
                duration_days=0,
                persistence_date_count=0,
                persistence_duration_days=0
            )

        unique_dates = {row["event_date"] for row in historical_events}
        date_count = len(unique_dates)
        
        dates_list = sorted(list(unique_dates))
        duration_days = (dates_list[-1] - dates_list[0]).days + 1
        
        is_persistent = date_count >= 5 and duration_days >= 30
        
        return PersistenceResponse(
            is_persistent=is_persistent,
            date_count=date_count,
            duration_days=duration_days,
            persistence_date_count=date_count if is_persistent else 0,
            persistence_duration_days=duration_days if is_persistent else 0
        )

    async def _persist_classification(
        self,
        event_id: str,
        ml_prediction: Optional[Dict],
        persistence_info: Optional[PersistenceResponse],
        sih_category: str,
        inference_error: Optional[str]
    ) -> bool:
        """Upsert classification results into event_classifications table."""
        
        status = "failed" if inference_error else "success"
        
        query = """
            INSERT INTO event_classifications (
                event_id,
                ml_predicted_class,
                ml_confidence,
                ml_probabilities_json,
                is_persistent,
                persistence_date_count,
                persistence_duration_days,
                final_sih_category,
                classification_status,
                inference_error,
                pipeline_version
            ) VALUES (
                :event_id,
                :ml_predicted_class,
                :ml_confidence,
                :ml_probabilities_json,
                :is_persistent,
                :persistence_date_count,
                :persistence_duration_days,
                :final_sih_category,
                :status,
                :inference_error,
                :pipeline_version
            )
            ON CONFLICT (event_id) DO UPDATE SET
                ml_predicted_class = EXCLUDED.ml_predicted_class,
                ml_confidence = EXCLUDED.ml_confidence,
                ml_probabilities_json = EXCLUDED.ml_probabilities_json,
                is_persistent = EXCLUDED.is_persistent,
                persistence_date_count = EXCLUDED.persistence_date_count,
                persistence_duration_days = EXCLUDED.persistence_duration_days,
                final_sih_category = EXCLUDED.final_sih_category,
                classification_status = EXCLUDED.classification_status,
                inference_error = EXCLUDED.inference_error,
                pipeline_version = EXCLUDED.pipeline_version,
                classification_timestamp = CURRENT_TIMESTAMP
        """
        
        params = {
            "event_id": event_id,
            "ml_predicted_class": ml_prediction["category"] if ml_prediction else None,
            "ml_confidence": ml_prediction["confidence"] if ml_prediction else None,
            "ml_probabilities_json": json.dumps(ml_prediction["probabilities"]) if ml_prediction else None,
            "is_persistent": persistence_info.is_persistent if persistence_info else False,
            "persistence_date_count": persistence_info.date_count if persistence_info else 0,
            "persistence_duration_days": persistence_info.duration_days if persistence_info else 0,
            "final_sih_category": sih_category,
            "status": status,
            "inference_error": inference_error,
            "pipeline_version": "1.0.0"
        }
        
        try:
            await self.db.execute_update(query, params)
            return True
        except Exception as e:
            logger.error(f"Database error persisting classification for {event_id}: {e}")
            return False
