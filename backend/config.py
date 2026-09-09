"""
Configuration management for SIH26162 Backend
Loads from environment variables with sensible defaults
"""

import os
from typing import Tuple
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


# Resolve both environment files explicitly so startup does not depend on the
# directory from which uvicorn or a test runner is launched.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=True)
load_dotenv(Path(__file__).with_name(".env"), override=False)


@dataclass
class Config:
    """Central configuration object"""

    # ========================================================================
    # Database: Native PostgreSQL + PostGIS (local development)
    # Read DATABASE_URL from environment variable only
    # Format: postgresql+asyncpg://user:password@host:port/database
    # ========================================================================
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/sih26162"
    )

    # Legacy settings (kept for documentation, override with DATABASE_URL)
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "sih26162")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")  # Do NOT use default

    DB_POOL_MIN: int = int(os.getenv("DB_POOL_MIN", "2"))
    DB_POOL_MAX: int = int(os.getenv("DB_POOL_MAX", "10"))


    def __post_init__(self):
        """Validate configuration after initialization"""
        # Check if DATABASE_URL is properly configured (not using default)
        if "postgres@localhost:5432/sih26162" in self.DATABASE_URL and "postgres:postgres@" in self.DATABASE_URL:
            import warnings
            warnings.warn(
                "⚠️  Using default PostgreSQL credentials (postgres:postgres).\n"
                "Set DATABASE_URL environment variable with your local credentials:\n"
                "Example: postgresql+asyncpg://postgres:MY_PASSWORD@localhost:5432/sih26162"
            )

        if not self.FIRMS_MAP_KEY and not self.DEMO_MODE:
            raise ValueError(
                "FIRMS_MAP_KEY is required when DEMO_MODE=false. "
                "Add a valid NASA FIRMS map key to backend/.env before starting."
            )


    # ========================================================================
    # Backend
    # ========================================================================
    BACKEND_HOST: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    BACKEND_ENV: str = os.getenv("BACKEND_ENV", "development")

    # ========================================================================
    # FIRMS API
    # ========================================================================
    FIRMS_MAP_KEY: str = os.getenv("FIRMS_MAP_KEY", "")
    FIRMS_BBOX: str = os.getenv("FIRMS_BBOX", "8.0,68.0,35.0,97.0")
    FIRMS_POLLING_INTERVAL_MINUTES: int = int(
        os.getenv("FIRMS_POLLING_INTERVAL_MINUTES", "30")
    )

    @property
    def firms_bbox_tuple(self) -> Tuple[float, float, float, float]:
        """Parse FIRMS_BBOX string to (min_lat, min_lon, max_lat, max_lon)"""
        parts = self.FIRMS_BBOX.split(",")
        return (
            float(parts[0]),  # min_lat
            float(parts[1]),  # min_lon
            float(parts[2]),  # max_lat
            float(parts[3]),  # max_lon
        )

    # ========================================================================
    # Demo Mode
    # ========================================================================
    DEMO_MODE: bool = os.getenv("DEMO_MODE", "false").lower() in ("true", "1", "yes")

    # ========================================================================
    # Storage
    # ========================================================================
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "local")
    STORAGE_LOCAL_PATH: str = os.getenv("STORAGE_LOCAL_PATH", "./data/storage")
    STORAGE_RETENTION_DAYS: int = int(os.getenv("STORAGE_RETENTION_DAYS", "730"))

    # ========================================================================
    # Logging
    # ========================================================================
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # ========================================================================
    # Geospatial
    # ========================================================================
    PILOT_BBOX: str = os.getenv("PILOT_BBOX", "8.0,68.0,35.0,97.0")
    PILOT_NAME: str = os.getenv("PILOT_NAME", "india")
    INDIA_BBOX: str = os.getenv("INDIA_BBOX", "8.0,68.0,35.0,97.0")

    @property
    def pilot_bbox_tuple(self) -> Tuple[float, float, float, float]:
        """Parse pilot bounding box"""
        parts = self.PILOT_BBOX.split(",")
        return (
            float(parts[0]),  # min_lat
            float(parts[1]),  # min_lon
            float(parts[2]),  # max_lat
            float(parts[3]),  # max_lon
        )

    @property
    def india_bbox_tuple(self) -> Tuple[float, float, float, float]:
        """Parse India-wide bounding box"""
        parts = self.INDIA_BBOX.split(",")
        return (
            float(parts[0]),  # min_lat
            float(parts[1]),  # min_lon
            float(parts[2]),  # max_lat
            float(parts[3]),  # max_lon
        )

    OSM_CACHE_TTL_SECONDS: int = int(os.getenv("OSM_CACHE_TTL_SECONDS", "604800"))

    # ========================================================================
    # Google Earth Engine (Stage 1B - Dynamic World)
    # ========================================================================
    EARTH_ENGINE_PROJECT_ID: str = os.getenv("EARTH_ENGINE_PROJECT_ID", "")
    EARTH_ENGINE_CREDENTIALS_PATH: str = os.getenv("EARTH_ENGINE_CREDENTIALS_PATH", "")

    # ========================================================================
    # Feature buffers (metres)
    # ========================================================================
    EVENT_BUFFER_1KM: int = int(os.getenv("EVENT_BUFFER_1KM", "1000"))
    EVENT_BUFFER_5KM: int = int(os.getenv("EVENT_BUFFER_5KM", "5000"))

    # ========================================================================
    # CORS
    # ========================================================================
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://localhost:8000,*"
    )

