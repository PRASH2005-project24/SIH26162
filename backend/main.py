"""
SIH26162 Backend - Main FastAPI Application
Stage 1A: FIRMS Ingestion with live FIRMS data
"""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from backend.database import Database, init_db
from backend.config import Config
from backend.firms_collector import FIRMSCollector
from backend.demo_data import load_demo_thermal_events
from backend.api import health, events, sources, enrichment
from backend.api.ml_predict import router as ml_predict_router

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global state
db: Database = None
firms_collector: FIRMSCollector = None
config: Config = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: startup and shutdown"""
    global db, firms_collector, config

    try:
        logger.info("🚀 Starting SIH26162 Backend...")

        # Load configuration
        config = Config()
        logger.info(f"Config: env={config.BACKEND_ENV}, demo_mode={config.DEMO_MODE}")

        # Initialize database connection
        db = Database(config)
        await db.connect()
        logger.info("✓ Database connected")

        # Initialize schema (migrations)
        await init_db(db)
        logger.info("✓ Database schema initialized")

        # Initialize FIRMS collector
        firms_collector = FIRMSCollector(db, config)
        logger.info("✓ FIRMS collector initialized")

        import asyncio
        if not config.DEMO_MODE:
            asyncio.create_task(firms_collector.start_polling_loop())
            logger.info("✓ FIRMS background polling started")

        # Log demo mode status
        if config.DEMO_MODE:
            logger.warning("⚠️  DEMO MODE ENABLED: Using mock FIRMS data. Set DEMO_MODE=false to use real API.")

        yield

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}", exc_info=True)
        raise

    finally:
        logger.info("🛑 Shutting down...")
        if db:
            await db.disconnect()
        logger.info("✓ Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="SIH26162 Thermal Event Intelligence Platform",
    version="1.0.0-stage1a",
    description="Stage 1A: FIRMS Ingestion with Geospatial Fusion",
    lifespan=lifespan
)

# Configure CORS
cors_origins = [origin.strip() for origin in Config().CORS_ORIGINS.split(",") if origin.strip() and origin.strip() != "*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# API Routes
# ============================================================================

# Health and status endpoints
app.include_router(health.router)

# Events endpoints (read)
app.include_router(events.router)

# Source health endpoints
app.include_router(sources.router)

# GIS Enrichment endpoints
app.include_router(enrichment.router)

# ML Prediction endpoints (Stage 2)
app.include_router(ml_predict_router)


# ============================================================================
# Manual ingestion endpoints (admin-only for now)
# ============================================================================

@app.post("/api/v1/admin/ingest-demo-data")
async def ingest_demo_data(background_tasks: BackgroundTasks):
    """
    Admin endpoint: Load demo FIRMS data into database.
    Only available in development/demo mode.
    """
    if not config.DEMO_MODE:
        raise HTTPException(status_code=403, detail="Only available in DEMO_MODE")

    try:
        background_tasks.add_task(load_demo_thermal_events, db, config)
        return {
            "status": "queued",
            "message": "Demo data ingestion started in background"
        }
    except Exception as e:
        logger.error(f"Demo data ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/admin/poll-firms-now")
async def poll_firms_now(background_tasks: BackgroundTasks):
    """
    Admin endpoint: Trigger FIRMS poll immediately (not on schedule).
    """
    if not firms_collector:
        raise HTTPException(status_code=500, detail="FIRMS collector not initialized")

    try:
        background_tasks.add_task(firms_collector.poll_once)
        return {
            "status": "queued",
            "message": "FIRMS poll started in background"
        }
    except Exception as e:
        logger.error(f"FIRMS poll failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/admin/start-polling")
async def start_polling_schedule(background_tasks: BackgroundTasks):
    """
    Admin endpoint: Start the background FIRMS polling loop.
    """
    if not firms_collector:
        raise HTTPException(status_code=500, detail="FIRMS collector not initialized")

    try:
        background_tasks.add_task(firms_collector.start_polling_loop)
        return {
            "status": "queued",
            "message": "FIRMS polling loop started in background"
        }
    except Exception as e:
        logger.error(f"Polling loop failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Error handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
