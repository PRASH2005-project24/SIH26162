import asyncio
import os
import sys
import logging
import hashlib
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import Database
from backend.config import Config
from backend.firms_collector import FIRMSCollector
from backend.gis.enrichment_engine import GISEnrichmentEngine
from backend.ml.classifier_engine import ClassifierEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ReliabilityTest")

async def test_firms_failures(db, config):
    logger.info("--- 1. FIRMS FAILURE TESTS ---")
    collector = FIRMSCollector(db, config)
    
    # A. FIRMS HTTP 500
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.status = 500
        async def mock_text(): return "Internal Server Error"
        mock_resp.text = mock_text
        mock_get.return_value.__aenter__.return_value = mock_resp
        
        res = await collector.poll_once()
        assert res["success"] is False
        assert "500" in res["error"]
        
        run = await db.execute_one("SELECT success FROM ingestion_runs WHERE id = :id", {"id": res["run_id"]})
        assert run["success"] is False
    logger.info("✓ Handled FIRMS HTTP 500")

    # B. FIRMS Timeout
    with patch('aiohttp.ClientSession.get', side_effect=asyncio.TimeoutError()):
        res = await collector.poll_once()
        assert res["success"] is False
    logger.info("✓ Handled FIRMS Timeout")

    # C. Malformed FIRMS CSV
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.status = 200
        async def mock_text(): return "not,a,real,csv\nbad,data"
        mock_resp.text = mock_text
        mock_get.return_value.__aenter__.return_value = mock_resp
        
        res = await collector.poll_once()
        assert res["success"] is True
        assert res["error_count"] > 0 or res["skipped_out_of_bounds"] > 0
    logger.info("✓ Handled Malformed FIRMS CSV")

async def test_osm_failures(db, config):
    logger.info("--- 2. OSM FAILURE TESTS ---")
    enrich_engine = GISEnrichmentEngine(db, config)
    
    # We create a dummy thermal event
    test_event_id = "test-osm-fail-event"
    await db.execute_update("DELETE FROM thermal_events WHERE id = :id", {"id": test_event_id})
    await db.execute_update("""
        INSERT INTO thermal_events (id, acquisition_time, satellite, latitude, longitude, brightness, confidence, frp)
        VALUES (:id, :now, 'TEST', 22.0, 80.0, 320.0, 85, 15.0)
    """, {"id": test_event_id, "now": datetime.utcnow()})
    
    # Simulate Overpass Exception
    with patch('backend.gis.osm_provider.OSMProvider._execute_overpass_query') as mock_overpass:
        mock_overpass.side_effect = Exception("Overpass Gateway Timeout")
        res = await enrich_engine.enrich_batch([test_event_id])
        assert res["successful"] == 1, "Enrichment should fallback gracefully and succeed"
        
        enrich_data = await db.execute_one("SELECT * FROM event_spatial_enrichment WHERE event_id = :id", {"id": test_event_id})
        assert enrich_data["inside_industrial_zone"] is False, "Should fallback to False"
        assert enrich_data["nearby_water"] is False, "Should fallback to False"
        assert enrich_data["nearest_feature_distance_m"] is None, "Should fallback to None"
    logger.info("✓ Handled OSM Timeout/Exception")
    await db.execute_update("DELETE FROM thermal_events WHERE id = :id", {"id": test_event_id})

async def test_dw_failures(db, config):
    logger.info("--- 3. DYNAMIC WORLD FAILURE TESTS ---")
    enrich_engine = GISEnrichmentEngine(db, config)
    test_event_id = "test-dw-fail-event"
    await db.execute_update("DELETE FROM thermal_events WHERE id = :id", {"id": test_event_id})
    await db.execute_update("""
        INSERT INTO thermal_events (id, acquisition_time, satellite, latitude, longitude, brightness, confidence, frp)
        VALUES (:id, :now, 'TEST', 22.0, 80.0, 320.0, 85, 15.0)
    """, {"id": test_event_id, "now": datetime.utcnow()})
    
    with patch('backend.gis.dynamic_world_provider.DynamicWorldProvider._query_dynamic_world') as mock_dw:
        mock_dw.side_effect = Exception("Earth Engine Auth Failed")
        res = await enrich_engine.enrich_batch([test_event_id])
        assert res["successful"] == 1
        enrich_data = await db.execute_one("SELECT land_cover_label FROM event_spatial_enrichment WHERE event_id = :id", {"id": test_event_id})
        assert enrich_data["land_cover_label"] is None, "Should fallback to None"
    logger.info("✓ Handled Dynamic World Auth Failure")
    await db.execute_update("DELETE FROM thermal_events WHERE id = :id", {"id": test_event_id})

async def test_ml_failures(db, config):
    logger.info("--- 4. ML FAILURE TESTS ---")
    classifier_engine = ClassifierEngine(db, config)
    test_event_id = "test-ml-fail-event"
    await db.execute_update("DELETE FROM thermal_events WHERE id = :id", {"id": test_event_id})
    await db.execute_update("""
        INSERT INTO thermal_events (id, acquisition_time, satellite, latitude, longitude, brightness, confidence, frp)
        VALUES (:id, :now, 'TEST', 22.0, 80.0, 320.0, 85, 15.0)
    """, {"id": test_event_id, "now": datetime.utcnow()})
    
    # Simulate Prediction exception
    with patch('ml.models.inference.FireSourceClassifier.predict') as mock_predict:
        mock_predict.side_effect = Exception("Corrupt Feature Vector")
        res = await classifier_engine.classify_batch([test_event_id])
        assert res["successful"] == 1, "Should succeed in recording the failure"
        
        db_res = await db.execute_one("SELECT classification_status, inference_error FROM event_classifications WHERE event_id = :id", {"id": test_event_id})
        assert db_res["classification_status"] == "failed"
        assert "Corrupt Feature Vector" in db_res["inference_error"]
    logger.info("✓ Handled ML Inference Failure")
    await db.execute_update("DELETE FROM thermal_events WHERE id = :id", {"id": test_event_id})

async def test_idempotency_attack(db, config):
    logger.info("--- 5. IDEMPOTENCY ATTACK ---")
    collector = FIRMSCollector(db, config)
    
    test_csv = "latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_t31,frp,daynight\n"
    test_csv += "22.0000,80.0000,320.0,1.0,1.0,2026-09-08,1200,TEST-SAT,VIIRS,85,1.0,300.0,15.0,D\n"
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.status = 200
        async def mock_text(): return test_csv
        mock_resp.text = mock_text
        mock_get.return_value.__aenter__.return_value = mock_resp
        
        # Process 5 times
        for _ in range(5):
            res = await collector.poll_once()
            assert res["success"] is True
            
        # Verify counts in db
        events = await db.execute("SELECT id FROM thermal_events WHERE satellite = 'TEST-SAT'")
        assert len(events) == 1, f"Expected 1 event, got {len(events)}"
        event_id = events[0]["id"]
        
        enrich = await db.execute("SELECT * FROM event_spatial_enrichment WHERE event_id = :id", {"id": event_id})
        assert len(enrich) <= 1
        
        classes = await db.execute("SELECT * FROM event_classifications WHERE event_id = :id", {"id": event_id})
        assert len(classes) <= 1

    logger.info("✓ Idempotency Attack Defeated")
    await db.execute_update("DELETE FROM event_classifications WHERE event_id IN (SELECT id FROM thermal_events WHERE satellite = 'TEST-SAT')")
    await db.execute_update("DELETE FROM event_spatial_enrichment WHERE event_id IN (SELECT id FROM thermal_events WHERE satellite = 'TEST-SAT')")
    await db.execute_update("DELETE FROM thermal_source_events WHERE event_id IN (SELECT id FROM thermal_events WHERE satellite = 'TEST-SAT')")
    await db.execute_update("DELETE FROM thermal_events WHERE satellite = 'TEST-SAT'")

async def test_temporal_leakage(db, config):
    logger.info("--- 6. ADVERSARIAL TEMPORAL LEAKAGE TEST ---")
    classifier_engine = ClassifierEngine(db, config)
    
    event_id_past = "test-leak-past"
    event_id_target = "test-leak-target"
    event_id_future = "test-leak-future"
    
    for eid in [event_id_past, event_id_target, event_id_future]:
        await db.execute_update("DELETE FROM thermal_events WHERE id = :id", {"id": eid})
        
    t_target = datetime.utcnow()
    t_past = t_target - timedelta(days=5)
    t_future = t_target + timedelta(days=5)
    
    lat, lon = 20.0, 75.0
    
    # 1. Insert past observation
    await db.execute_update("""
        INSERT INTO thermal_events (id, acquisition_time, satellite, latitude, longitude, brightness, confidence, frp)
        VALUES (:id, :acq, 'TEST', :lat, :lon, 320.0, 85, 15.0)
    """, {"id": event_id_past, "acq": t_past, "lat": lat, "lon": lon})
    
    # 2. Insert target event and calculate
    await db.execute_update("""
        INSERT INTO thermal_events (id, acquisition_time, satellite, latitude, longitude, brightness, confidence, frp)
        VALUES (:id, :acq, 'TEST', :lat, :lon, 320.0, 85, 15.0)
    """, {"id": event_id_target, "acq": t_target, "lat": lat, "lon": lon})
    
    await classifier_engine.classify_batch([event_id_target])
    res_before = await db.execute_one("SELECT persistence_duration_days, persistence_date_count, is_persistent FROM event_classifications WHERE event_id = :id", {"id": event_id_target})
    
    # 3. Insert future observation
    await db.execute_update("""
        INSERT INTO thermal_events (id, acquisition_time, satellite, latitude, longitude, brightness, confidence, frp)
        VALUES (:id, :acq, 'TEST', :lat, :lon, 320.0, 85, 15.0)
    """, {"id": event_id_future, "acq": t_future, "lat": lat, "lon": lon})
    
    # 4. Recalculate target event
    await classifier_engine.classify_batch([event_id_target])
    res_after = await db.execute_one("SELECT persistence_duration_days, persistence_date_count, is_persistent FROM event_classifications WHERE event_id = :id", {"id": event_id_target})
    
    assert res_before["persistence_duration_days"] == res_after["persistence_duration_days"], "Future event changed past duration"
    assert res_before["persistence_date_count"] == res_after["persistence_date_count"], "Future event changed past date count"
    
    logger.info("✓ Temporal Leakage Defeated")
    for eid in [event_id_past, event_id_target, event_id_future]:
        await db.execute_update("DELETE FROM thermal_events WHERE id = :id", {"id": eid})

async def run_all_tests():
    config = Config()
    config.FIRMS_MAP_KEY = "dummy_key"
    db = Database(config)
    await db.connect()
    try:
        await test_firms_failures(db, config)
        await test_osm_failures(db, config)
        await test_dw_failures(db, config)
        await test_ml_failures(db, config)
        await test_idempotency_attack(db, config)
        await test_temporal_leakage(db, config)
        logger.info("ALL RELIABILITY TESTS PASSED GREEN")
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(run_all_tests())
