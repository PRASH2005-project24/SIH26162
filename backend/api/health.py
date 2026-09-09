"""
Health check and status endpoints
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends
from sqlalchemy import text

from backend.database import Database

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["health"])


async def get_db() -> Database:
    """Dependency injection for database (will be wired up in main)"""
    from backend.main import db
    return db


@router.get("/health")
async def health_check(db: Database = Depends(get_db)) -> Dict[str, Any]:
    """
    Basic health check endpoint.
    Verifies PostgreSQL connection and PostGIS availability.
    Returns 200 OK if healthy, 503 if PostGIS unavailable.
    """
    db_health = await db.health_check()
    postgis_available = False
    postgis_version = None

    try:
        # Check PostGIS availability
        postgis_result = await db.execute("SELECT PostGIS_version();")
        if postgis_result:
            postgis_version = postgis_result[0].get('postgis_version')
            postgis_available = True
    except Exception as e:
        logger.warning(f"PostGIS check failed: {e}")

    # Determine overall health
    overall_status = "healthy"
    if db_health["status"] != "healthy":
        overall_status = "degraded"
    elif not postgis_available:
        overall_status = "degraded"
        db_health["warning"] = "PostgreSQL connected but PostGIS extension not available. Run: CREATE EXTENSION IF NOT EXISTS postgis;"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "backend": "ok",
        "database": db_health,
        "postgis": {
            "available": postgis_available,
            "version": postgis_version
        },
        "version": "1.0.0-stage1a"
    }


@router.get("/health/live")
async def liveness_check() -> Dict[str, str]:
    """
    Kubernetes-style liveness probe.
    Returns 200 OK if process is running.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_check(db: Database = Depends(get_db)) -> Dict[str, str]:
    """
    Kubernetes-style readiness probe.
    Returns 200 OK only if backend is ready to serve traffic.
    """
    try:
        db_health = await db.health_check()
        if db_health["status"] == "healthy":
            return {"status": "ready"}
        else:
            return {"status": "not_ready", "reason": "database_unhealthy"}
    except Exception as e:
        return {"status": "not_ready", "reason": str(e)}


@router.get("/status")
async def backend_status(db: Database = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed backend status including ingestion metrics.
    """
    try:
        # Get latest ingestion run
        latest_run_query = """
            SELECT
                id, source, run_timestamp, record_count,
                deduplicated_count, duplicate_count, error_count,
                success, duration_seconds
            FROM ingestion_runs
            ORDER BY run_timestamp DESC
            LIMIT 1
        """
        latest_run = await db.execute_one(latest_run_query)

        # Get event count
        event_count_query = """
            SELECT COUNT(*) as total,
                   COUNT(*) FILTER (WHERE status = 'active') as active,
                   COUNT(*) FILTER (WHERE status = 'duplicate') as duplicates
            FROM thermal_events
        """
        event_counts = await db.execute_one(event_count_query)

        # Get source health
        source_health_query = """
            SELECT source_name, status, last_check, last_success
            FROM source_health
            ORDER BY source_name
        """
        sources = await db.execute(source_health_query)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "backend": {
                "environment": "development",  # TODO: get from config
                "version": "1.0.0-stage1a"
            },
            "database": await db.health_check(),
            "ingestion": {
                "latest_run": latest_run,
                "event_counts": event_counts
            },
            "sources": sources
        }

    except Exception as e:
        logger.error(f"Error generating status: {e}", exc_info=True)
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(e)
        }
