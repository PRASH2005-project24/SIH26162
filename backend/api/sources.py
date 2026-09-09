"""
Data source health and ingestion run endpoints
"""

import logging
from datetime import datetime
from typing import Dict, Any, List

from fastapi import APIRouter, Depends, Query, HTTPException

from backend.database import Database

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/sources", tags=["sources"])


# ============================================================================
# Dependencies
# ============================================================================

async def get_db() -> Database:
    """Dependency injection for database"""
    from backend.main import db
    return db


# ============================================================================
# Endpoints
# ============================================================================

@router.get("/health")
async def get_sources_health(db: Database = Depends(get_db)) -> Dict[str, Any]:
    """
    Get health status of all configured data sources.
    """
    try:
        query = """
            SELECT
                source_name, source_type, status, last_check,
                last_success, coverage_bbox, data_version, error_log
            FROM source_health
            ORDER BY source_name
        """

        sources = await db.execute(query)

        # Initialize missing sources (first time)
        if not sources:
            await _initialize_source_health(db)
            sources = await db.execute(query)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "sources": sources,
            "summary": {
                "healthy": len([s for s in sources if s["status"] == "healthy"]),
                "degraded": len([s for s in sources if s["status"] == "degraded"]),
                "unavailable": len([s for s in sources if s["status"] == "unavailable"]),
                "unknown": len([s for s in sources if s["status"] == "unknown"]),
            }
        }

    except Exception as e:
        logger.error(f"Error getting source health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/{source_name}")
async def get_source_health(
    source_name: str,
    db: Database = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get health status of a specific data source.
    """
    try:
        query = """
            SELECT
                source_name, source_type, status, last_check,
                last_success, coverage_bbox, data_version,
                success_count, failure_count, error_log, notes
            FROM source_health
            WHERE source_name = :name
        """

        source = await db.execute_one(query, {"name": source_name})

        if not source:
            raise HTTPException(status_code=404, detail=f"Source '{source_name}' not found")

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "source": source
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting source health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs")
async def get_ingestion_runs(
    db: Database = Depends(get_db),
    source: str = Query("FIRMS"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """
    Get ingestion run history.
    """
    try:
        # Get total count
        count_query = """
            SELECT COUNT(*) as count
            FROM ingestion_runs
            WHERE source = :source
        """
        count_result = await db.execute_one(count_query, {"source": source})
        total = count_result["count"] if count_result else 0

        # Get paginated runs
        runs_query = """
            SELECT
                id, source, run_timestamp, bbox,
                record_count, deduplicated_count, duplicate_count, error_count,
                success, error_message, duration_seconds,
                next_scheduled_run, started_at, completed_at
            FROM ingestion_runs
            WHERE source = :source
            ORDER BY run_timestamp DESC
            LIMIT :limit OFFSET :offset
        """

        runs = await db.execute(
            runs_query,
            {"source": source, "limit": limit, "offset": offset}
        )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "source": source,
            "runs": runs,
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + limit) < total
        }

    except Exception as e:
        logger.error(f"Error getting ingestion runs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}")
async def get_ingestion_run(
    run_id: str,
    db: Database = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get details of a specific ingestion run.
    """
    try:
        query = """
            SELECT
                id, source, run_timestamp, bbox,
                record_count, deduplicated_count, duplicate_count, error_count,
                success, error_message, duration_seconds,
                next_scheduled_run, started_at, completed_at, created_at
            FROM ingestion_runs
            WHERE id = :id
        """

        run = await db.execute_one(query, {"id": run_id})

        if not run:
            raise HTTPException(status_code=404, detail="Ingestion run not found")

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "run": run
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ingestion run: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}/events")
async def get_run_events(
    run_id: str,
    db: Database = Depends(get_db),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """
    Get all thermal events from a specific ingestion run.
    """
    try:
        # Verify run exists
        run_query = "SELECT id, source, record_count FROM ingestion_runs WHERE id = :id"
        run = await db.execute_one(run_query, {"id": run_id})

        if not run:
            raise HTTPException(status_code=404, detail="Ingestion run not found")

        # Get events
        events_query = """
            SELECT
                id, acquisition_time, latitude, longitude,
                brightness, frp, confidence, satellite,
                day_night, status, processed_at
            FROM thermal_events
            WHERE ingestion_run_id = :run_id
            ORDER BY acquisition_time DESC
            LIMIT :limit OFFSET :offset
        """

        events = await db.execute(
            events_query,
            {"run_id": run_id, "limit": limit, "offset": offset}
        )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "run_id": run_id,
            "source": run["source"],
            "events": events,
            "count": len(events),
            "run_total": run["record_count"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting run events: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Helper functions
# ============================================================================

async def _initialize_source_health(db: Database):
    """Initialize source_health table with known sources"""
    sources = [
        ("FIRMS", "API"),
        ("OSM-Overpass", "API"),
        ("Bhuvan-NDVI", "API"),  # Placeholder
        ("IILB-NCoG", "API"),  # Placeholder
    ]

    for source_name, source_type in sources:
        query = """
            INSERT INTO source_health (source_name, source_type, status, notes)
            VALUES (:name, :type, 'unknown', 'Initialized')
            ON CONFLICT (source_name) DO NOTHING
        """
        await db.execute(query, {"name": source_name, "type": source_type})

    logger.info(f"✓ Initialized {len(sources)} sources in source_health table")
