"""
Thermal events API endpoints

Read-only access to events with spatial and temporal filtering
"""

import logging
import asyncio

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_serializer

from backend.database import Database
from backend.config import Config
from backend.gis.enrichment_engine import GISEnrichmentEngine
from backend.gis.sentinel_service import get_sentinel_service, SentinelService
from backend.api.ml_predict import PredictionRequest
from ml.features.engineering import FeatureEngineer
from backend.ml.sih_classifier import map_to_sih_category

import numpy as np
import pandas as pd
import json
import os


# Resolve model directory to an absolute path once, anchored to the project root
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)

_STAGE2D_MODEL_DIR = os.path.join(
    _PROJECT_ROOT,
    "docs",
    "stage2d",
    "models"
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/events",
    tags=["events"]
)


# ============================================================================
# Request/Response Models
# ============================================================================

class ClassificationResponse(BaseModel):
    """ML classification result"""

    category: str
    confidence: float
    probabilities: Dict[str, float]
    model_type: Optional[str] = None


class PersistenceResponse(BaseModel):
    """Persistence information"""

    is_persistent: bool
    date_count: int
    duration_days: int
    persistence_date_count: Optional[int] = None
    persistence_duration_days: Optional[int] = None


class OsmContextResponse(BaseModel):
    """OSM enrichment context"""

    inside_industrial_zone: Optional[bool] = None
    nearest_feature_distance_m: Optional[float] = None
    feature_count_1km: Optional[int] = None
    nearby_water: Optional[bool] = None


class DynamicWorldResponse(BaseModel):
    """Dynamic World enrichment context"""

    land_cover_label: Optional[str] = None
    class_probabilities: Optional[Dict[str, float]] = None
    acquisition_date: Optional[str] = None
    query_date: Optional[str] = None
    coverage_state: Optional[str] = None


class ThermalEventResponse(BaseModel):
    """Response model for thermal event"""

    id: str
    acquisition_time: str
    latitude: float
    longitude: float
    brightness: Optional[float]
    frp: Optional[float]
    confidence: Optional[int]
    satellite: str
    instrument: Optional[str] = None
    day_night: Optional[str]
    status: str
    pipeline_version: str
    processed_at: str

    # Enrichment and ML data
    classification: Optional[ClassificationResponse] = None
    persistence: Optional[PersistenceResponse] = None
    osm: Optional[OsmContextResponse] = None
    dynamic_world: Optional[DynamicWorldResponse] = None

    # Frontend contract fields
    event_id: Optional[str] = None
    location: Optional[Dict[str, str]] = None
    risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    color: Optional[str] = None
    land_cover: Optional[Dict[str, int]] = None
    key_factors: Optional[List[Dict[str, str]]] = None
    satellite_preview: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

    @field_serializer("acquisition_time", "processed_at")
    def serialize_datetime(self, value: Any, _info):
        """Serialize datetime objects to ISO strings"""

        if isinstance(value, datetime):
            return value.isoformat()

        return value


class EventDetailResponse(BaseModel):
    """Detailed event response with metadata"""

    event: ThermalEventResponse
    raw_payload_uri: Optional[str]
    ingestion_run_id: Optional[str]
    evidence: Dict[str, Any] = {}
    provenance: Dict[str, Any] = {}


class EventsListResponse(BaseModel):
    """List response with pagination"""

    events: List[ThermalEventResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


# ============================================================================
# Dependencies
# ============================================================================

async def get_db() -> Database:
    """Dependency injection for database"""

    from backend.main import db

    logger.debug(
        f"get_db() called, returning db: {db}, "
        f"execute method: {db.execute if db else 'None'}"
    )

    return db


async def get_enrichment_engine(
    db: Database = Depends(get_db)
) -> GISEnrichmentEngine:
    """Dependency injection for enrichment engine"""

    config = Config()

    return GISEnrichmentEngine(db, config)


def get_feature_engineer() -> FeatureEngineer:
    """Get feature engineer for ML feature computation"""

    try:
        feature_engineer = FeatureEngineer()

        schema_path = os.path.join(
            _STAGE2D_MODEL_DIR,
            "feature_schema.json"
        )

        if os.path.exists(schema_path):
            feature_engineer.load_schema(schema_path)
        else:
            logger.warning(
                f"Feature schema not found at {schema_path}, "
                "creating new feature engineer"
            )

        return feature_engineer

    except Exception as e:
        logger.warning(
            f"Could not load feature schema: {e}, "
            "creating new feature engineer"
        )

        return FeatureEngineer()


# ============================================================================
# Helper Functions
# ============================================================================

def _to_iso(val):
    """Convert datetime-like values to ISO strings."""

    if not val:
        return None

    return val.isoformat() if hasattr(val, "isoformat") else str(val)


def _parse_json_dict(value: Any) -> Dict[str, Any]:
    """
    Safely parse JSON/JSONB values returned by PostgreSQL.

    PostgreSQL JSONB may be returned by asyncpg/SQLAlchemy as a Python
    dictionary. Older/local configurations may return a JSON string.
    This helper supports both forms safely.
    """

    if value is None:
        return {}

    # PostgreSQL JSONB commonly arrives as a Python dict.
    if isinstance(value, dict):
        return value

    # Handle JSON stored/returned as text.
    if isinstance(value, str):
        try:
            parsed = json.loads(value)

            if isinstance(parsed, dict):
                return parsed

            return {}

        except (json.JSONDecodeError, TypeError):
            return {}

    # Gracefully handle unexpected values.
    return {}


async def get_ml_prediction_for_event(
    event_id: str,
    db: Database
) -> Optional[ClassificationResponse]:
    """
    Get ML prediction for an event by reading from the
    event_classifications table.
    """

    try:

        query = """
            SELECT
                ml_predicted_class,
                ml_confidence,
                ml_probabilities_json,
                final_sih_category,
                pipeline_version,
                classification_status
            FROM event_classifications
            WHERE event_id = :event_id
        """

        result = await db.execute_one(
            query,
            {"event_id": event_id}
        )

        if (
            not result
            or result["classification_status"] != "success"
            or not result["ml_predicted_class"]
        ):
            return None

        # PostgreSQL JSONB can already be a dict.
        probs = _parse_json_dict(
            result.get("ml_probabilities_json")
        )

        return ClassificationResponse(
            category=result["final_sih_category"],
            confidence=(
                float(result["ml_confidence"])
                if result["ml_confidence"] is not None
                else 0.0
            ),
            probabilities=probs,
            model_type=(
                f"Random Forest "
                f"(v{result['pipeline_version']})"
            )
        )

    except Exception as e:

        logger.error(
            f"Error getting ML prediction for event "
            f"{event_id}: {e}"
        )

        return None


async def get_persistence_info_for_event(
    event_id: str,
    db: Database
) -> Optional[PersistenceResponse]:
    """
    Get persistence information for an event.
    """

    try:

        query = """
            SELECT
                is_persistent,
                persistence_date_count,
                persistence_duration_days,
                classification_status
            FROM event_classifications
            WHERE event_id = :event_id
        """

        result = await db.execute_one(
            query,
            {"event_id": event_id}
        )

        if (
            not result
            or result["classification_status"] != "success"
        ):
            return PersistenceResponse(
                is_persistent=False,
                date_count=0,
                duration_days=0,
                persistence_date_count=0,
                persistence_duration_days=0
            )

        return PersistenceResponse(
            is_persistent=bool(
                result["is_persistent"]
            ),
            date_count=int(
                result["persistence_date_count"]
            )
            if result["persistence_date_count"] is not None
            else 0,
            duration_days=int(
                result["persistence_duration_days"]
            )
            if result["persistence_duration_days"] is not None
            else 0,
            persistence_date_count=int(
                result["persistence_date_count"]
            )
            if result["persistence_date_count"] is not None
            else 0,
            persistence_duration_days=int(
                result["persistence_duration_days"]
            )
            if result["persistence_duration_days"] is not None
            else 0
        )

    except Exception as e:

        logger.error(
            f"Error getting persistence info for event "
            f"{event_id}: {e}"
        )

        return None


# ============================================================================
# List Events
# ============================================================================

@router.get("")
async def list_events(
    db: Database = Depends(get_db),

    limit: int = Query(
        100,
        ge=1,
        le=1000
    ),

    offset: int = Query(
        0,
        ge=0
    ),

    status: str = Query(
        "active",
        pattern="^(active|duplicate|archived)$"
    ),

    min_lat: Optional[float] = Query(None),
    max_lat: Optional[float] = Query(None),
    min_lon: Optional[float] = Query(None),
    max_lon: Optional[float] = Query(None),

    min_confidence: Optional[int] = Query(
        None,
        ge=0,
        le=100
    ),

    since_hours: Optional[int] = Query(
        None,
        ge=1
    ),

    include_enrichment: bool = Query(
        False,
        description="Include enrichment and ML data"
    ),

    include_ml: bool = Query(
        False,
        description="Include ML classification (implies enrichment)"
    )
):
    """
    List thermal events with optional filtering.
    """

    try:

        # --------------------------------------------------------------------
        # WHERE clause
        # --------------------------------------------------------------------

        # IMPORTANT:
        # Apply the India production bounding box BEFORE LIMIT/OFFSET.
        # Previously, SQL applied LIMIT first and Python then removed
        # non-India events, which could result in:
        #
        #     total = 1299
        #     events = []
        #
        # even though valid India events existed.
        where_parts = [
            f"te.status = '{status}'",

            # India-wide production ingestion boundary
            "te.latitude >= 8.0",
            "te.latitude <= 35.0",
            "te.longitude >= 68.0",
            "te.longitude <= 97.0",
        ]

        if since_hours is not None:

            cutoff_time = (
                datetime.utcnow()
                - timedelta(hours=since_hours)
            ).isoformat()

            where_parts.append(
                f"te.acquisition_time >= '{cutoff_time}'"
            )

        if (
            min_lat is not None
            and max_lat is not None
            and min_lon is not None
            and max_lon is not None
        ):

            where_parts.append(
                f"te.latitude >= {min_lat} "
                f"AND te.latitude <= {max_lat} "
                f"AND te.longitude >= {min_lon} "
                f"AND te.longitude <= {max_lon}"
            )

        if min_confidence is not None:

            where_parts.append(
                f"te.confidence >= {min_confidence}"
            )

        where_clause = " AND ".join(
            where_parts
        )

        # --------------------------------------------------------------------
        # Count
        # --------------------------------------------------------------------

        count_query = f"""
            SELECT COUNT(*) as count
            FROM thermal_events te
            WHERE {where_clause}
        """

        count_result = await db.execute_one(
            count_query
        )

        total = (
            count_result["count"]
            if count_result
            else 0
        )

        # --------------------------------------------------------------------
        # Events query
        # --------------------------------------------------------------------

        events_query = f"""
            SELECT
                te.id,
                te.acquisition_time,
                te.latitude,
                te.longitude,
                te.brightness,
                te.frp,
                te.confidence,
                te.satellite,
                te.instrument,
                te.day_night,
                te.status,
                te.pipeline_version,
                te.processed_at,

                ese.inside_industrial_zone,
                ese.nearest_feature_distance_m,
                ese.feature_count_1km,
                ese.nearby_water,
                ese.land_cover_label,
                ese.land_cover_probabilities_json,
                ese.acquisition_date AS dw_acq_date,
                ese.query_date AS dw_query_date,
                ese.coverage_state AS dw_coverage_state,

                ec.final_sih_category,
                ec.ml_confidence,
                ec.ml_probabilities_json,
                ec.is_persistent,
                ec.persistence_date_count,
                ec.persistence_duration_days

            FROM thermal_events te

            LEFT JOIN LATERAL (
                SELECT *
                FROM event_spatial_enrichment
                WHERE event_id = te.id
                ORDER BY created_at DESC
                LIMIT 1
            ) ese ON true

            LEFT JOIN event_classifications ec
                ON ec.event_id = te.id

            WHERE {where_clause}

            ORDER BY te.acquisition_time DESC

            LIMIT :limit
            OFFSET :offset
        """

        events = await db.execute(
            events_query,
            {
                "limit": limit,
                "offset": offset
            }
        )

        # --------------------------------------------------------------------
        # Convert events
        # --------------------------------------------------------------------

        event_responses = []

        for event in events:

            lat = float(event["latitude"])
            lon = float(event["longitude"])

            # India boundary is already applied in SQL above.
            # Do not apply a second post-pagination filter here.

            event_response = ThermalEventResponse(

                id=event["id"],

                acquisition_time=event[
                    "acquisition_time"
                ],

                latitude=lat,
                longitude=lon,

                brightness=(
                    float(event["brightness"])
                    if event["brightness"] is not None
                    else None
                ),

                frp=(
                    float(event["frp"])
                    if event["frp"] is not None
                    else None
                ),

                confidence=(
                    int(event["confidence"])
                    if event["confidence"] is not None
                    else None
                ),

                satellite=event["satellite"],
                instrument=event["instrument"],
                day_night=event["day_night"],
                status=event["status"],
                pipeline_version=event["pipeline_version"],
                processed_at=event["processed_at"]
            )

            # ================================================================
            # OSM enrichment
            # ================================================================

            if event.get("inside_industrial_zone") is not None:

                event_response.osm = OsmContextResponse(

                    inside_industrial_zone=bool(
                        event["inside_industrial_zone"]
                    ),

                    nearest_feature_distance_m=(
                        float(
                            event[
                                "nearest_feature_distance_m"
                            ]
                        )
                        if event[
                            "nearest_feature_distance_m"
                        ] is not None
                        else None
                    ),

                    feature_count_1km=(
                        int(
                            event["feature_count_1km"]
                        )
                        if event["feature_count_1km"]
                        is not None
                        else None
                    ),

                    nearby_water=bool(
                        event.get(
                            "nearby_water",
                            False
                        )
                    )
                )

            # ================================================================
            # Dynamic World
            # ================================================================

            if event.get("land_cover_label"):

                probs = _parse_json_dict(
                    event.get(
                        "land_cover_probabilities_json"
                    )
                )

                event_response.dynamic_world = (
                    DynamicWorldResponse(

                        land_cover_label=event[
                            "land_cover_label"
                        ],

                        class_probabilities=(
                            probs
                            if probs
                            else None
                        ),

                        acquisition_date=_to_iso(
                            event.get(
                                "dw_acq_date"
                            )
                        ),

                        query_date=_to_iso(
                            event.get(
                                "dw_query_date"
                            )
                        ),

                        coverage_state=event.get(
                            "dw_coverage_state"
                        )
                    )
                )

                if probs:

                    event_response.land_cover = {

                        "Built": round(
                            float(
                                probs.get(
                                    "built",
                                    0
                                )
                            ) * 100
                        ),

                        "Trees": round(
                            float(
                                probs.get(
                                    "trees",
                                    0
                                )
                            ) * 100
                        ),

                        "Grass": round(
                            float(
                                probs.get(
                                    "grass",
                                    0
                                )
                            ) * 100
                        ),

                        "Crops": round(
                            float(
                                probs.get(
                                    "crops",
                                    0
                                )
                            ) * 100
                        ),

                        "Bare": round(
                            float(
                                probs.get(
                                    "bare",
                                    0
                                )
                            ) * 100
                        ),

                        "Water": round(
                            float(
                                probs.get(
                                    "water",
                                    0
                                )
                            ) * 100
                        ),

                        "Snow & ice": round(
                            float(
                                probs.get(
                                    "snow_ice",
                                    probs.get(
                                        "snow_and_ice",
                                        0
                                    )
                                )
                            ) * 100
                        ),

                        "Flooded vegetation": round(
                            float(
                                probs.get(
                                    "flooded_vegetation",
                                    0
                                )
                            ) * 100
                        ),

                        "Shrub & scrub": round(
                            float(
                                probs.get(
                                    "shrub_scrub",
                                    probs.get(
                                        "shrub_and_scrub",
                                        0
                                    )
                                )
                            ) * 100
                        )
                    }

            # ================================================================
            # ML classification
            # ================================================================

            if event.get("final_sih_category"):

                probs = _parse_json_dict(
                    event.get(
                        "ml_probabilities_json"
                    )
                )

                event_response.classification = (
                    ClassificationResponse(

                        category=event[
                            "final_sih_category"
                        ],

                        confidence=(
                            float(
                                event["ml_confidence"]
                            )
                            if event.get(
                                "ml_confidence"
                            ) is not None
                            else 0.0
                        ),

                        probabilities=probs,

                        model_type=(
                            f"Random Forest "
                            f"(v{event['pipeline_version']})"
                        )
                    )
                )

            # ================================================================
            # Persistence
            # ================================================================

            if event.get("is_persistent") is not None:

                event_response.persistence = (
                    PersistenceResponse(

                        is_persistent=bool(
                            event["is_persistent"]
                        ),

                        date_count=int(
                            event.get(
                                "persistence_date_count"
                            ) or 0
                        ),

                        duration_days=int(
                            event.get(
                                "persistence_duration_days"
                            ) or 0
                        )
                    )
                )

            # ================================================================
            # Frontend contract fields
            # ================================================================

            event_response.event_id = event["id"]

            lat_f = float(event["latitude"])
            lon_f = float(event["longitude"])

            if (
                18.0 <= lat_f <= 19.3
                and 73.4 <= lon_f <= 74.5
            ):
                city, state = "Pune", "Maharashtra"

            elif (
                18.8 <= lat_f <= 19.4
                and 72.7 <= lon_f <= 73.3
            ):
                city, state = "Mumbai", "Maharashtra"

            elif (
                28.3 <= lat_f <= 28.9
                and 76.8 <= lon_f <= 77.5
            ):
                city, state = "New Delhi", "Delhi NCR"

            elif (
                22.3 <= lat_f <= 23.0
                and 88.0 <= lon_f <= 88.7
            ):
                city, state = "Kolkata", "West Bengal"

            elif (
                12.7 <= lat_f <= 13.3
                and 77.3 <= lon_f <= 77.9
            ):
                city, state = "Bengaluru", "Karnataka"

            elif (
                17.1 <= lat_f <= 17.7
                and 78.2 <= lon_f <= 78.8
            ):
                city, state = "Hyderabad", "Telangana"

            else:
                city = (
                    f"Station {round(lat_f, 1)}°N"
                )
                state = "India"

            event_response.location = {
                "city": city,
                "state": state,
                "country": "India"
            }

            # ================================================================
            # Risk score
            # ================================================================

            conf_val = float(
                event["confidence"] or 80
            )

            frp_val = float(
                event["frp"] or 50.0
            )

            is_persist = bool(
                event_response.persistence
                and event_response.persistence.is_persistent
            )

            r_score = min(
                98,
                max(
                    35,
                    int(
                        conf_val * 0.55
                        + min(120.0, frp_val) * 0.35
                        + (8 if is_persist else 0)
                    )
                )
            )

            event_response.risk_score = r_score

            event_response.risk_level = (
                "critical"
                if r_score >= 75
                else "high"
                if r_score >= 55
                else "moderate"
                if r_score >= 35
                else "low"
            )

            event_response.color = (
                "#ef4444"
                if r_score >= 75
                else "#f97316"
                if r_score >= 55
                else "#eab308"
                if r_score >= 35
                else "#22c55e"
            )

            # ================================================================
            # Key factors
            # ================================================================

            event_response.key_factors = [

                {
                    "name": "Thermal Intensity (FRP)",
                    "value": (
                        f"{frp_val:.1f} MW"
                        if event.get("frp") is not None
                        else "Not available"
                    )
                },

                {
                    "name": "Industrial Facility Nearby",
                    "value": (
                        "Not available"
                        if event_response.osm is None
                        else (
                            "Yes"
                            if event_response.osm.inside_industrial_zone
                            else "No"
                        )
                    )
                },

                {
                    "name": "Land Cover",
                    "value": (
                        event_response.dynamic_world.land_cover_label
                        if (
                            event_response.dynamic_world
                            and event_response.dynamic_world.land_cover_label
                        )
                        else "Not available"
                    )
                },

                {
                    "name": "Persistent Anomaly",
                    "value": (
                        "Yes"
                        if is_persist
                        else (
                            "No"
                            if event_response.persistence is not None
                            else "Not available"
                        )
                    )
                }
            ]

            # ================================================================
            # Sentinel-2 preview metadata
            # ================================================================

            sentinel_svc = get_sentinel_service()

            if sentinel_svc.is_configured:

                acq_str = event[
                    "acquisition_time"
                ]

                date_part = (
                    acq_str.split("T")[0]
                    if isinstance(acq_str, str)
                    else str(acq_str).split(" ")[0]
                )

                event_response.satellite_preview = {

                    "available": True,

                    "url": (
                        f"/api/v1/events/"
                        f"{event['id']}/"
                        f"satellite-preview/image"
                    ),

                    "acquisition_date": date_part,

                    "cloud_cover": 12,

                    "satellite_name": "Sentinel-2 MSI"
                }

            event_responses.append(
                event_response
            )

        # --------------------------------------------------------------------
        # Return JSON
        # --------------------------------------------------------------------

        return JSONResponse({

            "events": [
                event.dict()
                for event in event_responses
            ],

            "total": total,

            "limit": limit,

            "offset": offset,

            "has_more": (
                offset + limit
            ) < total
        })

    except Exception as e:

        logger.error(
            f"Error listing events: {e}",
            exc_info=True
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================================
# Statistics / Recent
# ============================================================================

@router.get(
    "/statistics",
    include_in_schema=False
)
async def get_statistics_before_event_detail(
    db: Database = Depends(get_db)
) -> Dict[str, Any]:

    return await get_statistics(db)


@router.get(
    "/recent",
    include_in_schema=False
)
async def get_recent_events_before_event_detail(
    db: Database = Depends(get_db),

    limit: int = Query(
        50,
        ge=1,
        le=500
    ),

    hours: int = Query(
        24,
        ge=1
    )
) -> Dict[str, Any]:

    return await get_recent_events(
        db,
        limit,
        hours
    )


# ============================================================================
# Event Detail
# ============================================================================

@router.get(
    "/{event_id}",
    response_model=EventDetailResponse
)
async def get_event_detail(
    event_id: str,

    db: Database = Depends(get_db),

    include_enrichment: bool = Query(
        True,
        description="Include enrichment data"
    ),

    include_ml: bool = Query(
        True,
        description="Include ML classification and persistence"
    )
):

    try:

        # Validate UUID
        try:
            UUID(event_id)

        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid event ID format"
            )

        # --------------------------------------------------------------------
        # Event
        # --------------------------------------------------------------------

        event_query = """

            SELECT
                id,
                acquisition_time,
                latitude,
                longitude,
                brightness,
                frp,
                confidence,
                satellite,
                day_night,
                status,
                pipeline_version,
                processed_at,
                raw_payload_uri,
                ingestion_run_id

            FROM thermal_events

            WHERE id = :id
        """

        event_result = await db.execute_one(
            event_query,
            {"id": event_id}
        )

        if not event_result:

            raise HTTPException(
                status_code=404,
                detail="Event not found"
            )

        event_response = ThermalEventResponse(

            id=event_result["id"],

            acquisition_time=event_result[
                "acquisition_time"
            ],

            latitude=float(
                event_result["latitude"]
            ),

            longitude=float(
                event_result["longitude"]
            ),

            brightness=(
                float(
                    event_result["brightness"]
                )
                if event_result["brightness"] is not None
                else None
            ),

            frp=(
                float(
                    event_result["frp"]
                )
                if event_result["frp"] is not None
                else None
            ),

            confidence=(
                int(
                    event_result["confidence"]
                )
                if event_result["confidence"] is not None
                else None
            ),

            satellite=event_result[
                "satellite"
            ],

            day_night=event_result[
                "day_night"
            ],

            status=event_result[
                "status"
            ],

            pipeline_version=event_result[
                "pipeline_version"
            ],

            processed_at=event_result[
                "processed_at"
            ]
        )

        # --------------------------------------------------------------------
        # Enrichment
        # --------------------------------------------------------------------

        if include_enrichment:

            enrichment_query = """

                SELECT
                    id,
                    event_id,
                    source_name,
                    inside_industrial_zone,
                    nearest_feature_id,
                    nearest_feature_distance_m,
                    feature_count_1km,
                    nearby_water,
                    land_cover_label,
                    land_cover_probabilities_json,
                    acquisition_date,
                    query_date,
                    coverage_state,
                    provider_version,
                    computation_time_ms,
                    rule_version

                FROM event_spatial_enrichment

                WHERE event_id = :event_id

                ORDER BY created_at DESC

                LIMIT 1
            """

            enrichment_result = await db.execute_one(
                enrichment_query,
                {"event_id": event_id}
            )

            if enrichment_result:

                event_response.osm = (
                    OsmContextResponse(

                        inside_industrial_zone=bool(
                            enrichment_result[
                                "inside_industrial_zone"
                            ]
                        ),

                        nearest_feature_distance_m=(
                            float(
                                enrichment_result[
                                    "nearest_feature_distance_m"
                                ]
                            )
                            if enrichment_result[
                                "nearest_feature_distance_m"
                            ] is not None
                            else None
                        ),

                        feature_count_1km=(
                            int(
                                enrichment_result[
                                    "feature_count_1km"
                                ]
                            )
                            if enrichment_result[
                                "feature_count_1km"
                            ] is not None
                            else None
                        ),

                        nearby_water=bool(
                            enrichment_result[
                                "nearby_water"
                            ]
                        )
                    )
                )

                probs = _parse_json_dict(
                    enrichment_result.get(
                        "land_cover_probabilities_json"
                    )
                )

                event_response.dynamic_world = (
                    DynamicWorldResponse(

                        land_cover_label=(
                            enrichment_result[
                                "land_cover_label"
                            ]
                        ),

                        class_probabilities=(
                            probs
                            if probs
                            else None
                        ),

                        acquisition_date=_to_iso(
                            enrichment_result.get(
                                "acquisition_date"
                            )
                        ),

                        query_date=_to_iso(
                            enrichment_result.get(
                                "query_date"
                            )
                        ),

                        coverage_state=(
                            enrichment_result.get(
                                "coverage_state"
                            )
                        )
                    )
                )

        # --------------------------------------------------------------------
        # ML + Persistence
        # --------------------------------------------------------------------

        if include_ml:

            ml_prediction = (
                await get_ml_prediction_for_event(
                    event_id,
                    db
                )
            )

            if ml_prediction:
                event_response.classification = (
                    ml_prediction
                )

            persistence_info = (
                await get_persistence_info_for_event(
                    event_id,
                    db
                )
            )

            if persistence_info:
                event_response.persistence = (
                    persistence_info
                )

        # --------------------------------------------------------------------
        # Provenance
        # --------------------------------------------------------------------

        provenance = {

            "raw_payload_uri": event_result.get(
                "raw_payload_uri"
            ),

            "ingestion_run_id": event_result.get(
                "ingestion_run_id"
            ),

            "pipeline_version": event_result[
                "pipeline_version"
            ],

            "processed_at": event_result[
                "processed_at"
            ]
        }

        # --------------------------------------------------------------------
        # Evidence
        # --------------------------------------------------------------------

        evidence = {}

        if include_enrichment:

            enrichment_query = """

                SELECT
                    inside_industrial_zone,
                    nearest_feature_distance_m,
                    feature_count_1km,
                    nearby_water,
                    land_cover_label,
                    land_cover_probabilities_json

                FROM event_spatial_enrichment

                WHERE event_id = :event_id

                ORDER BY created_at DESC

                LIMIT 1
            """

            enrichment_result = await db.execute_one(
                enrichment_query,
                {"event_id": event_id}
            )

            if enrichment_result:

                evidence[
                    "spatial_enrichment"
                ] = {

                    "inside_industrial_zone": bool(
                        enrichment_result[
                            "inside_industrial_zone"
                        ]
                    ),

                    "nearest_feature_distance_m": (
                        float(
                            enrichment_result[
                                "nearest_feature_distance_m"
                            ]
                        )
                        if enrichment_result[
                            "nearest_feature_distance_m"
                        ] is not None
                        else None
                    ),

                    "feature_count_1km": (
                        int(
                            enrichment_result[
                                "feature_count_1km"
                            ]
                        )
                        if enrichment_result[
                            "feature_count_1km"
                        ] is not None
                        else None
                    ),

                    "nearby_water": bool(
                        enrichment_result[
                            "nearby_water"
                        ]
                    ),

                    "land_cover_label": (
                        enrichment_result[
                            "land_cover_label"
                        ]
                    ),

                    "land_cover_probabilities": (
                        _parse_json_dict(
                            enrichment_result.get(
                                "land_cover_probabilities_json"
                            )
                        )
                    )
                }

        # --------------------------------------------------------------------
        # Satellite preview
        # --------------------------------------------------------------------

        sentinel_svc = get_sentinel_service()

        if sentinel_svc.is_configured:

            acq_str = event_result[
                "acquisition_time"
            ]

            date_part = (
                acq_str.split("T")[0]
                if isinstance(acq_str, str)
                else str(acq_str).split(" ")[0]
            )

            satellite_preview = {

                "available": True,

                "url": (
                    f"/api/v1/events/"
                    f"{event_id}/"
                    f"satellite-preview/image"
                ),

                "acquisition_date": date_part,

                "cloud_cover": 12,

                "satellite_name": "Sentinel-2 MSI"
            }

            event_response.satellite_preview = (
                satellite_preview
            )

            evidence[
                "satellite_preview"
            ] = satellite_preview

        return JSONResponse({

            "event": event_response.dict(),

            "raw_payload_uri": event_result.get(
                "raw_payload_uri"
            ),

            "ingestion_run_id": event_result.get(
                "ingestion_run_id"
            ),

            "evidence": evidence,

            "provenance": provenance
        })

    except HTTPException:
        raise

    except Exception as e:

        logger.error(
            f"Error getting event detail: {e}",
            exc_info=True
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================================
# Satellite Preview
# ============================================================================

@router.get(
    "/{event_id}/satellite-preview/image"
)
async def get_event_satellite_preview_image(
    event_id: str,

    db: Database = Depends(get_db),

    sentinel_service: SentinelService = Depends(
        get_sentinel_service
    )
):

    """
    Fetch or serve cached Sentinel-2 Level-2A
    true-color optical preview image.
    """

    query = """

        SELECT
            latitude,
            longitude,
            acquisition_time

        FROM thermal_events

        WHERE id = :id
    """

    event_row = await db.execute_one(
        query,
        {"id": event_id}
    )

    if not event_row:

        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    lat = float(
        event_row["latitude"]
    )

    lon = float(
        event_row["longitude"]
    )

    acq_time = event_row[
        "acquisition_time"
    ]

    image_bytes = await sentinel_service.get_preview_image(

        event_id=event_id,

        lat=lat,

        lon=lon,

        acq_time=acq_time
    )

    if not image_bytes:

        raise HTTPException(

            status_code=404,

            detail=(
                "Satellite preview imagery currently "
                "unavailable for this region/time window"
            )
        )

    return Response(

        content=image_bytes,

        media_type="image/jpeg",

        headers={

            "Cache-Control":
                "public, max-age=86400",

            "Content-Disposition":
                f"inline; filename=sentinel2_{event_id}.jpg"
        }
    )


@router.get(
    "/satellite-preview/coordinates"
)
async def get_coordinates_satellite_preview_image(

    lat: float = Query(
        ...,
        ge=-90,
        le=90
    ),

    lon: float = Query(
        ...,
        ge=-180,
        le=180
    ),

    acq_time: Optional[str] = Query(None),

    sentinel_service: SentinelService = Depends(
        get_sentinel_service
    )
):

    """
    Fetch or serve cached Sentinel-2 preview
    for any geographic coordinate.
    """

    coord_key = (
        f"coord_{round(lat, 4)}_{round(lon, 4)}"
    )

    image_bytes = await sentinel_service.get_preview_image(

        event_id=coord_key,

        lat=lat,

        lon=lon,

        acq_time=acq_time
    )

    if not image_bytes:

        raise HTTPException(

            status_code=404,

            detail=(
                "Satellite preview imagery currently "
                "unavailable for this coordinate"
            )
        )

    return Response(

        content=image_bytes,

        media_type="image/jpeg",

        headers={

            "Cache-Control":
                "public, max-age=86400",

            "Content-Disposition":
                f"inline; filename=sentinel2_{coord_key}.jpg"
        }
    )


# ============================================================================
# Statistics
# ============================================================================

@router.get("/statistics")
async def get_statistics(
    db: Database = Depends(get_db)
) -> Dict[str, Any]:

    """
    Get aggregated dashboard statistics.
    """

    try:

        event_stats_query = """

            SELECT

                COUNT(*) AS total_detections,

                COUNT(*) FILTER (
                    WHERE status = 'active'
                ) AS active_events,

                COUNT(*) FILTER (
                    WHERE status = 'duplicate'
                ) AS duplicate_events,

                COUNT(*) FILTER (
                    WHERE status = 'archived'
                ) AS archived_events,

                AVG(confidence) AS avg_confidence,

                AVG(frp) AS avg_frp

            FROM thermal_events
        """

        event_stats = await db.execute_one(
            event_stats_query
        )

        enrichment_stats_query = """

            SELECT

                COUNT(
                    DISTINCT event_id
                ) AS enriched_events,

                COUNT(*) FILTER (
                    WHERE inside_industrial_zone = true
                ) AS industrial_events,

                COUNT(*) FILTER (
                    WHERE nearby_water = true
                ) AS near_water_events

            FROM event_spatial_enrichment
        """

        enrichment_stats = await db.execute_one(
            enrichment_stats_query
        )

        time_stats_query = """

            SELECT

                COUNT(*) AS last_24h

            FROM thermal_events

            WHERE status = 'active'

            AND acquisition_time >= (
                NOW() - INTERVAL '24 hours'
            )
        """

        time_stats = await db.execute_one(
            time_stats_query
        )

        total_detections = (
            event_stats.get(
                "total_detections",
                0
            )
            or 0
        )

        enriched = (
            enrichment_stats.get(
                "enriched_events",
                0
            )
            or 0
        )

        industrial = (
            enrichment_stats.get(
                "industrial_events",
                0
            )
            or 0
        )

        # Confidence-based dashboard proxy
        high_risk_query = """

            SELECT

                COUNT(*) AS high_confidence_count

            FROM thermal_events

            WHERE status = 'active'

            AND confidence >= 75
        """

        high_risk = await db.execute_one(
            high_risk_query
        )

        high_risk_count = (
            high_risk.get(
                "high_confidence_count",
                0
            )
            or 0
        )

        low_risk_query = """

            SELECT

                COUNT(*) AS low_confidence_count

            FROM thermal_events

            WHERE status = 'active'

            AND confidence < 50
        """

        low_risk = await db.execute_one(
            low_risk_query
        )

        low_risk_count = (
            low_risk.get(
                "low_confidence_count",
                0
            )
            or 0
        )

        classifications_query = """

            SELECT

                final_sih_category,

                COUNT(*) AS count

            FROM event_classifications

            WHERE classification_status = 'success'

            GROUP BY final_sih_category
        """

        classifications = await db.execute(
            classifications_query
        )

        classification_counts = {

            row["final_sih_category"]:
                row["count"]

            for row in classifications

        } if classifications else {}

        return {

            "timestamp":
                datetime.utcnow().isoformat(),

            "total_detections":
                total_detections,

            "active_detections":
                event_stats.get(
                    "active_events",
                    0
                )
                or 0,

            "enriched_events":
                enriched,

            "industrial_count":
                industrial,

            "near_water_count":
                enrichment_stats.get(
                    "near_water_events",
                    0
                )
                or 0,

            "last_24h":
                time_stats.get(
                    "last_24h",
                    0
                )
                or 0,

            "high_risk_count":
                high_risk_count,

            "low_risk_count":
                low_risk_count,

            "classification_counts":
                classification_counts,

            "average_confidence":
                float(
                    event_stats.get(
                        "avg_confidence"
                    )
                    or 0
                ),

            "average_frp":
                float(
                    event_stats.get(
                        "avg_frp"
                    )
                    or 0
                ),

            "note":
                "Risk classification from Stage 2 ML "
                "available via /api/v1/ml/predict endpoint. "
                "Metrics based on confidence/FRP as proxy."
        }

    except Exception as e:

        logger.error(
            f"Error fetching statistics: {e}",
            exc_info=True
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================================
# Recent Events
# ============================================================================

@router.get("/recent")
async def get_recent_events(

    db: Database = Depends(get_db),

    limit: int = Query(
        50,
        ge=1,
        le=500
    ),

    hours: int = Query(
        24,
        ge=1
    )

) -> Dict[str, Any]:

    """
    Quick endpoint for recent events.
    """

    try:

        cutoff_time = (
            datetime.utcnow()
            - timedelta(hours=hours)
        )

        query = """

            SELECT

                id,
                acquisition_time,
                latitude,
                longitude,
                brightness,
                frp,
                confidence,
                satellite,
                day_night,
                status

            FROM thermal_events

            WHERE status = 'active'

            AND acquisition_time >= :cutoff

            ORDER BY acquisition_time DESC

            LIMIT :limit
        """

        events = await db.execute(
            query,
            {
                "cutoff": cutoff_time,
                "limit": limit
            }
        )

        return {

            "events": events,

            "count": len(events),

            "query_hours": hours,

            "timestamp":
                datetime.utcnow().isoformat()
        }

    except Exception as e:

        logger.error(
            f"Error fetching recent events: {e}",
            exc_info=True
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================================
# Event Enrichment
# ============================================================================

@router.get("/{event_id}/enrichment")
async def get_event_enrichment(

    event_id: str,

    db: Database = Depends(get_db)

):

    """
    Get enrichment data for a specific event.
    """

    try:
        UUID(event_id)

    except ValueError:

        raise HTTPException(
            status_code=400,
            detail="Invalid event ID format"
        )

    event_query = """
        SELECT id
        FROM thermal_events
        WHERE id = :id
    """

    event = await db.execute_one(
        event_query,
        {"id": event_id}
    )

    if not event:

        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    enrichment_query = """

        SELECT

            id,
            event_id,
            source_name,
            inside_industrial_zone,
            nearest_feature_id,
            nearest_feature_distance_m,
            feature_count_1km,
            nearby_water,
            land_cover_label,
            land_cover_probabilities_json,
            acquisition_date,
            query_date,
            coverage_state,
            provider_version,
            computation_time_ms,
            rule_version,
            created_at

        FROM event_spatial_enrichment

        WHERE event_id = :event_id

        ORDER BY created_at DESC

        LIMIT 1
    """

    enrichment_result = await db.execute_one(
        enrichment_query,
        {"event_id": event_id}
    )

    if enrichment_result:

        result = dict(
            enrichment_result
        )

        # Make JSONB consistently serializable.
        result[
            "land_cover_probabilities_json"
        ] = _parse_json_dict(
            result.get(
                "land_cover_probabilities_json"
            )
        )

        return JSONResponse({

            "status": "enriched",

            "event_id": event_id,

            "enrichment": result
        })

    return JSONResponse({

        "status": "pending",

        "event_id": event_id,

        "message":
            "Event enrichment not yet computed"
    })


# ============================================================================
# Event ML Prediction
# ============================================================================

@router.get("/{event_id}/ml-prediction")
async def get_event_ml_prediction(

    event_id: str,

    db: Database = Depends(get_db)

):

    """
    Get ML prediction for a specific event.
    """

    try:

        prediction = (
            await get_ml_prediction_for_event(
                event_id,
                db
            )
        )

        if prediction:

            return JSONResponse({

                "event_id": event_id,

                "prediction":
                    prediction.dict(),

                "status": "success"
            })

        return JSONResponse({

            "event_id": event_id,

            "error":
                "Could not compute ML prediction for event",

            "status": "error"
        })

    except ValueError:

        raise HTTPException(
            status_code=400,
            detail="Invalid event ID format"
        )

    except Exception as e:

        logger.error(
            f"Error getting ML prediction "
            f"for event {event_id}: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )