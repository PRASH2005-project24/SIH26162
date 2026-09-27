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

    from backend.gis.boundary import is_point_in_india

    # Industrial, forest, and agricultural anchor zones across India
    indian_anchors = [
        {"name": "Pimpri Industrial Area, Pune", "lat": 18.6298, "lon": 73.8007},
        {"name": "Vadodara Industrial Zone, Gujarat", "lat": 22.3072, "lon": 73.1812},
        {"name": "Gurgaon Industrial Area, Haryana", "lat": 28.4595, "lon": 77.0266},
        {"name": "Coimbatore Industrial Zone, Tamil Nadu", "lat": 11.0168, "lon": 76.9558},
        {"name": "Howrah Industrial Belt, West Bengal", "lat": 22.5964, "lon": 88.2631},
        {"name": "Ludhiana Agricultural Belt, Punjab", "lat": 30.9010, "lon": 75.8573},
        {"name": "Karnal Farm Zone, Haryana", "lat": 29.6857, "lon": 76.9905},
        {"name": "Singrauli Thermal Belt, MP", "lat": 24.1997, "lon": 82.6645},
        {"name": "Jharia Coal Belt, Jharkhand", "lat": 23.7418, "lon": 86.4137},
        {"name": "Visakhapatnam Industrial Corridor, AP", "lat": 17.6868, "lon": 83.2185},
        {"name": "Bandipur Forest Fringe, Karnataka", "lat": 11.6664, "lon": 76.6293},
        {"name": "Simlipal Forest Reserve, Odisha", "lat": 21.8540, "lon": 86.3400},
        {"name": "Kanpur Industrial Hub, UP", "lat": 26.4499, "lon": 80.3319},
        {"name": "Nashik MIDC, Maharashtra", "lat": 19.9975, "lon": 73.7898},
    ]

    for i in range(count):
        anchor = random.choice(indian_anchors)
        # Scatter within reasonable radius of real Indian hubs and verify boundary
        lat = anchor["lat"] + random.uniform(-0.4, 0.4)
        lon = anchor["lon"] + random.uniform(-0.4, 0.4)
        while not is_point_in_india(lat, lon):
            lat = anchor["lat"] + random.uniform(-0.1, 0.1)
            lon = anchor["lon"] + random.uniform(-0.1, 0.1)

        event_name = f"{anchor['name']} region {i}"

        # Half events are Live (within last 1–12 hours), half are spread over past week
        if i % 2 == 0:
            acq_time = datetime.utcnow() - timedelta(hours=random.uniform(0.8, 11.5))
        else:
            acq_time = base_time + timedelta(hours=random.randint(0, 168))

        brightness = random.uniform(280, 380)  # Kelvin
        frp = random.uniform(5, 150)  # Megawatts
        confidence = random.choice([70, 80, 85, 90, 95])

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
            latitude, longitude, point,
            pipeline_version, ingestion_run_id,
            status
        ) VALUES (
            :id, :acquisition_time, :satellite, :instrument,
            :brightness, :brightness_rad, :frp, :confidence,
            :scan, :track, :day_night,
            :latitude, :longitude,
            ST_GeomFromText(:point, 4326),
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
        "point": f"POINT({event['longitude']} {event['latitude']})",
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
