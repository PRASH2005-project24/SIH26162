"""
Demo data generator for Stage 1A testing
Loads mock FIRMS events when API credentials are unavailable
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict
from uuid import uuid4
import random

from backend.database import Database
from backend.config import Config

logger = logging.getLogger(__name__)


async def load_demo_thermal_events(db: Database, config: Config):
    """
    Load demo thermal events into the database.
    Used when FIRMS_MAP_KEY is unavailable or in demo mode.
    """
    logger.info("📦 Loading demo thermal events...")

    run_id = str(uuid4())

    try:
        # Generate mock events
        events = generate_mock_events(count=50, config=config)
        logger.info(f"✓ Generated {len(events)} mock FIRMS events")

        # Ingest events
        ingested = 0
        for event in events:
            try:
                await _insert_demo_event(db, event, run_id)
                ingested += 1
            except Exception as e:
                logger.warning(f"Failed to ingest demo event: {e}")
                continue

        # Log run
        await _log_demo_run(db, run_id, ingested)
        logger.info(f"✓ Demo data ingestion complete: {ingested} events loaded")

    except Exception as e:
        logger.error(f"❌ Demo data loading failed: {e}", exc_info=True)
        raise


def generate_mock_events(count: int = 50, config: Config = None) -> List[Dict]:
    """Generate realistic mock thermal events"""
    if not config:
        from backend.config import Config
        config = Config()

    # India-wide region coordinates
    min_lat, min_lon, max_lat, max_lon = config.india_bbox_tuple

    events = []
    base_time = datetime.utcnow() - timedelta(days=7)

    # Industrial hotspots across India (mock locations)
    hotspots = [
        {"name": "Pimpri Industrial Area, Pune", "lat": 18.6298, "lon": 73.8007},
        {"name": "Vadodara Industrial Zone, Gujarat", "lat": 22.3072, "lon": 73.1812},
        {"name": "Gurgaon Industrial Area, Haryana", "lat": 28.4595, "lon": 77.0266},
        {"name": "Coimbatore Industrial Zone, Tamil Nadu", "lat": 11.0168, "lon": 76.9558},
        {"name": "Howrah Industrial Belt, West Bengal", "lat": 22.5964, "lon": 88.2631},
    ]

    for i in range(count):
        # Mix hotspot events with random scatter
        if i % 4 == 0 and hotspots:
            hotspot = random.choice(hotspots)
            lat = hotspot["lat"] + random.uniform(-0.01, 0.01)
            lon = hotspot["lon"] + random.uniform(-0.01, 0.01)
            event_name = hotspot["name"]
        else:
            lat = random.uniform(min_lat, max_lat)
            lon = random.uniform(min_lon, max_lon)
            event_name = f"Random event {i}"

        # Acquisition time: spread over past week
        acq_time = base_time + timedelta(hours=random.randint(0, 168))

        brightness = random.uniform(280, 380)  # Kelvin
        frp = random.uniform(5, 150)  # Megawatts
        confidence = random.choice([30, 60, 80])

        event = {
            "id": str(uuid4()),
            "acquisition_time": acq_time,  # Pass datetime object, not ISO string
            "satellite": random.choice(["NOAA-20", "Suomi NPP"]),
            "instrument": "VIIRS",
            "brightness": brightness,
            "brightness_rad": random.uniform(3, 20),
            "frp": frp,
            "confidence": confidence,
            "scan": random.uniform(0.4, 1.0),
            "track": random.uniform(0.4, 1.0),
            "day_night": random.choice(["D", "N"]),
            "latitude": lat,
            "longitude": lon,
            "pipeline_version": "1.0.0-demo",
        }

        events.append(event)

    return events


async def _insert_demo_event(db: Database, event: Dict, run_id: str):
    """Insert a single demo event"""
    query = """
        INSERT INTO thermal_events (
            id, acquisition_time, satellite, instrument,
            brightness, brightness_rad, frp, confidence,
            scan, track, day_night,
            latitude, longitude,
            pipeline_version, ingestion_run_id,
            status
        ) VALUES (
            :id, :acquisition_time, :satellite, :instrument,
            :brightness, :brightness_rad, :frp, :confidence,
            :scan, :track, :day_night,
            :latitude, :longitude,
            :pipeline_version, :ingestion_run_id,
            'active'
        )
        ON CONFLICT DO NOTHING
    """

    await db.execute_update(query, {
        "id": event["id"],
        "acquisition_time": event["acquisition_time"],
        "satellite": event["satellite"],
        "instrument": event["instrument"],
        "brightness": event["brightness"],
        "brightness_rad": event["brightness_rad"],
        "frp": event["frp"],
        "confidence": event["confidence"],
        "scan": event["scan"],
        "track": event["track"],
        "day_night": event["day_night"],
        "latitude": event["latitude"],
        "longitude": event["longitude"],
        "pipeline_version": event["pipeline_version"],
        "ingestion_run_id": run_id,
    })


async def _log_demo_run(db: Database, run_id: str, count: int):
    """Log demo data ingestion run"""
    query = """
        INSERT INTO ingestion_runs (
            id, source, run_timestamp, bbox,
            record_count, deduplicated_count, success
        ) VALUES (
            :id, 'demo', :run_timestamp, :bbox,
            :record_count, :record_count, true
        )
    """

    await db.execute_update(query, {
        "id": run_id,
        "run_timestamp": datetime.utcnow(),  # Pass datetime object, not ISO string
        "bbox": "demo",
        "record_count": count,
    })
