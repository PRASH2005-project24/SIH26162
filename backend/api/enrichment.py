"""
GIS Enrichment API endpoints
Provides endpoints for enriching thermal events with spatial context
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.database import Database
from backend.gis.enrichment_engine import GISEnrichmentEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/enrichment", tags=["enrichment"])


# ============================================================================
# Request/Response Models
# ============================================================================

class EnrichmentRequest(BaseModel):
    """Request to enrich a single event"""
    event_id: str


class EnrichmentBatchRequest(BaseModel):
    """Request to enrich multiple events"""
    event_ids: Optional[List[str]] = None
    limit: int = 100


class EnrichmentResult(BaseModel):
    """Result of enriching a single event"""
    status: str
    event_id: Optional[str] = None
    enrichment_id: Optional[str] = None
    inside_industrial: Optional[bool] = None
    nearby_water: Optional[bool] = None
    land_cover_label: Optional[str] = None
    nearest_distance_m: Optional[float] = None
    confidence_score: Optional[float] = None
    osm_coverage: Optional[str] = None
    dw_coverage: Optional[str] = None
    reason: Optional[str] = None


# ============================================================================
# Dependencies
# ============================================================================

async def get_db() -> Database:
    """Dependency injection for database"""
    from backend.main import db
    return db


async def get_enrichment_engine(db: Database = Depends(get_db)) -> GISEnrichmentEngine:
    """Dependency injection for enrichment engine"""
    from backend.config import Config
    config = Config()
    return GISEnrichmentEngine(db, config)


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/enrich-event")
async def enrich_single_event(
    request: EnrichmentRequest,
    engine: GISEnrichmentEngine = Depends(get_enrichment_engine)
):
    """
    Enrich a single thermal event with GIS data.

    Queries:
    - OSM/Overpass for industrial zones and water features
    - Google Dynamic World for land cover classification

    Returns enrichment result with confidence scores.
    """
    try:
        result = await engine.enrich_event(request.event_id)
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Error enriching event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enrich-batch")
async def enrich_batch_events(
    request: EnrichmentBatchRequest,
    engine: GISEnrichmentEngine = Depends(get_enrichment_engine),
    background_tasks: BackgroundTasks = None
):
    """
    Enrich multiple thermal events in batch mode.

    Can either:
    1. Provide specific event_ids to enrich
    2. Leave event_ids empty to auto-enrich unenriched events

    Returns status and individual results.
    """
    try:
        result = await engine.enrich_batch(request.event_ids, request.limit)
        return JSONResponse(result)
    except Exception as e:
        logger.error(f"Error in batch enrichment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enrich-batch-background")
async def enrich_batch_background(
    request: EnrichmentBatchRequest,
    engine: GISEnrichmentEngine = Depends(get_enrichment_engine),
    background_tasks: BackgroundTasks = None
):
    """
    Queue batch enrichment as background task.
    Returns immediately with task status.
    """
    try:
        if background_tasks:
            background_tasks.add_task(engine.enrich_batch, request.event_ids, request.limit)

        return JSONResponse({
            "status": "queued",
            "message": f"Batch enrichment queued for {request.limit} events",
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        logger.error(f"Error queuing batch enrichment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enrichment-status/{event_id}")
async def get_enrichment_status(
    event_id: str,
    db: Database = Depends(get_db)
):
    """
    Get enrichment status for a specific event.
    Returns enrichment data if available, or status if pending.
    """
    try:
        result = await db.execute_one(
            """
            SELECT
                id, event_id, source_name,
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
            """,
            {"event_id": event_id}
        )

        if result:
            return JSONResponse({
                "status": "enriched",
                "event_id": event_id,
                "enrichment": result
            })
        else:
            return JSONResponse({
                "status": "pending",
                "event_id": event_id,
                "message": "Event enrichment not yet computed"
            })

    except Exception as e:
        logger.error(f"Error getting enrichment status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enrichment-stats")
async def get_enrichment_statistics(
    db: Database = Depends(get_db)
):
    """
    Get overall enrichment statistics.
    Returns counts of enriched/unenriched events and coverage info.
    """
    try:
        # Get event counts
        event_stats = await db.execute_one(
            """
            SELECT
                COUNT(*) as total_events,
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_events
            FROM thermal_events
            """
        )

        # Get enrichment counts
        enrichment_stats = await db.execute_one(
            """
            SELECT
                COUNT(DISTINCT event_id) as enriched_events,
                COUNT(*) as total_enrichments,
                AVG(CAST(nearest_feature_distance_m AS FLOAT)) as avg_nearest_distance,
                SUM(CASE WHEN inside_industrial_zone = true THEN 1 ELSE 0 END) as events_in_industrial,
                SUM(CASE WHEN nearby_water = true THEN 1 ELSE 0 END) as events_near_water
            FROM event_spatial_enrichment
            """
        )

        # Get coverage stats
        coverage_stats = await db.execute(
            """
            SELECT
                coverage_state,
                COUNT(*) as count
            FROM event_spatial_enrichment
            GROUP BY coverage_state
            """
        )

        total_events = event_stats.get("total_events", 0) or 0
        enriched_events = enrichment_stats.get("enriched_events", 0) or 0
        enrichment_coverage = (enriched_events / total_events * 100) if total_events > 0 else 0

        return JSONResponse({
            "timestamp": datetime.utcnow().isoformat(),
            "event_statistics": {
                "total_events": total_events,
                "active_events": event_stats.get("active_events", 0) or 0,
                "enriched_events": enriched_events,
                "pending_enrichment": total_events - enriched_events,
                "enrichment_coverage_percent": round(enrichment_coverage, 2)
            },
            "enrichment_statistics": {
                "total_enrichments": enrichment_stats.get("total_enrichments", 0) or 0,
                "avg_nearest_distance_m": enrichment_stats.get("avg_nearest_distance") or 0,
                "events_in_industrial_zone": enrichment_stats.get("events_in_industrial", 0) or 0,
                "events_near_water": enrichment_stats.get("events_near_water", 0) or 0
            },
            "coverage_breakdown": [
                {
                    "state": stat["coverage_state"],
                    "count": stat["count"]
                }
                for stat in coverage_stats
            ]
        })

    except Exception as e:
        logger.error(f"Error getting enrichment statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enriched-events")
async def get_enriched_events(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    inside_industrial: Optional[bool] = Query(None),
    near_water: Optional[bool] = Query(None),
    land_cover: Optional[str] = Query(None),
    db: Database = Depends(get_db)
):
    """
    Get enriched events with optional filtering.

    Query parameters:
    - limit: number of results (default 50, max 500)
    - offset: pagination offset
    - inside_industrial: filter by industrial zone proximity
    - near_water: filter by water proximity
    - land_cover: filter by land cover type
    """
    try:
        # Build WHERE clause using parameterized queries
        where_parts = []
        params = {"limit": limit, "offset": offset}

        if inside_industrial is not None:
            where_parts.append("ese.inside_industrial_zone = :inside_industrial")
            params["inside_industrial"] = inside_industrial

        if near_water is not None:
            where_parts.append("ese.nearby_water = :near_water")
            params["near_water"] = near_water

        if land_cover is not None:
            where_parts.append("ese.land_cover_label = :land_cover")
            params["land_cover"] = land_cover

        where_clause = " AND ".join(where_parts)
        if where_clause:
            where_clause = "WHERE " + where_clause
        else:
            where_clause = ""

        # Get total count
        count_query = f"""
            SELECT COUNT(*) as count
            FROM event_spatial_enrichment ese
            JOIN thermal_events te ON ese.event_id = te.id
            {where_clause}
        """
        count_result = await db.execute_one(count_query, params)
        total = count_result.get("count", 0) if count_result else 0

        # Get paginated results
        events_query = f"""
            SELECT
                te.id, te.latitude, te.longitude, te.brightness, te.frp,
                te.confidence, te.acquisition_time,
                ese.inside_industrial_zone,
                ese.nearest_feature_distance_m,
                ese.feature_count_1km,
                ese.nearby_water,
                ese.land_cover_label,
                ese.query_date
            FROM event_spatial_enrichment ese
            JOIN thermal_events te ON ese.event_id = te.id
            {where_clause}
            ORDER BY te.acquisition_time DESC
            LIMIT :limit OFFSET :offset
        """

        events = await db.execute(events_query, params)

        return JSONResponse({
            "events": events,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total
        })

    except Exception as e:
        logger.error(f"Error fetching enriched events: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
