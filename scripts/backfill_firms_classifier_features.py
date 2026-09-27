"""Recover training-compatible classifier fields from retained FIRMS CSV payloads."""

import asyncio
import csv
import io
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import Config
from backend.database import Database


def normalize_satellite(value: object) -> Tuple[str, str]:
    satellite = str(value or "").strip().upper()
    aliases = {
        "N20": ("N20", "NOAA20"),
        "NOAA-20": ("N20", "NOAA20"),
        "NOAA20": ("N20", "NOAA20"),
        "N21": ("N21", "NOAA21"),
        "NOAA-21": ("N21", "NOAA21"),
        "NOAA21": ("N21", "NOAA21"),
        "N": ("SNPP", "SNPP"),
        "SNPP": ("SNPP", "SNPP"),
        "SUOMI NPP": ("SNPP", "SNPP"),
        "SUOMI-NPP": ("SNPP", "SNPP"),
        "VIIRS_SNPP": ("SNPP", "SNPP"),
    }
    return aliases.get(satellite, (satellite, satellite))


def normalize_confidence(value: object) -> Optional[str]:
    confidence = str(value or "").strip().lower()
    if confidence in {"l", "n", "h"}:
        return confidence
    if confidence.isdigit():
        numeric = int(confidence)
        return "h" if numeric >= 80 else "l" if numeric <= 30 else "n"
    return None


def payload_key(record: Dict[str, str]) -> Optional[Tuple[float, float, str, str]]:
    try:
        acquisition_minute = f"{record['acq_date']} {str(record['acq_time']).strip().zfill(4)}"
        satellite, _ = normalize_satellite(record.get("satellite"))
        return (
            round(float(record["latitude"]), 4),
            round(float(record["longitude"]), 4),
            acquisition_minute,
            satellite,
        )
    except (KeyError, TypeError, ValueError):
        return None


async def main() -> None:
    db = Database(Config())
    await db.connect()
    try:
        payloads = await db.execute(
            "SELECT payload_json FROM raw_payloads WHERE source='FIRMS' ORDER BY created_at"
        )
        events = await db.execute("""
            SELECT id::text AS id,
                   ROUND(latitude::numeric, 4) AS latitude,
                   ROUND(longitude::numeric, 4) AS longitude,
                   to_char(acquisition_time, 'YYYY-MM-DD HH24MI') AS acquisition_minute,
                   satellite, confidence
            FROM thermal_events
            WHERE status = 'active'
        """)

        source_by_event: Dict[Tuple[float, float, str, str], Dict[str, Optional[float]]] = {}
        for payload in payloads:
            for record in csv.DictReader(io.StringIO(payload["payload_json"])):
                key = payload_key(record)
                if key is None:
                    continue
                bright_ti5 = record.get("bright_ti5")
                try:
                    second_band = float(bright_ti5) if bright_ti5 not in (None, "") else None
                except ValueError:
                    second_band = None
                source_by_event[key] = {
                    "bright_ti5": second_band,
                    "confidence_class": normalize_confidence(record.get("confidence")),
                }

        recovered = 0
        updated = 0
        for event in events:
            satellite = str(event["satellite"] or "")
            model_satellite, source_satellite = normalize_satellite(satellite)
            key = (
                round(float(event["latitude"]), 4),
                round(float(event["longitude"]), 4),
                event["acquisition_minute"],
                model_satellite,
            )
            recovered_features = source_by_event.get(key)
            if recovered_features:
                recovered += recovered_features["bright_ti5"] is not None
            confidence_class = (
                recovered_features.get("confidence_class") if recovered_features else None
            ) or normalize_confidence(event.get("confidence"))

            updated += await db.execute_update("""
                UPDATE thermal_events
                SET bright_ti5 = COALESCE(:bright_ti5, bright_ti5),
                    confidence_class = COALESCE(:confidence_class, confidence_class),
                    model_satellite = COALESCE(NULLIF(:model_satellite, ''), model_satellite),
                    source_satellite = COALESCE(NULLIF(:source_satellite, ''), source_satellite)
                WHERE id = :event_id
            """, {
                "event_id": event["id"],
                "bright_ti5": recovered_features.get("bright_ti5") if recovered_features else None,
                "confidence_class": confidence_class,
                "model_satellite": model_satellite,
                "source_satellite": source_satellite,
            })

        totals = await db.execute_one("""
            SELECT COUNT(*) AS active_events,
                   COUNT(bright_ti5) AS with_bright_ti5,
                   COUNT(confidence_class) AS with_confidence_class,
                   COUNT(model_satellite) AS with_model_satellite
            FROM thermal_events WHERE status='active'
        """)
        print({
            "active_events_processed": len(events),
            "bright_ti5_recovered_from_raw_payload": recovered,
            "rows_updated": updated,
            "feature_coverage_after_backfill": totals,
        })
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())