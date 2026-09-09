import asyncio
import os
import json
import logging
from datetime import datetime, timedelta
from backend.database import Database
from backend.config import Config
from backend.firms_collector import FIRMSCollector
from backend.ml.classifier_engine import ClassifierEngine
from backend.gis.enrichment_engine import GISEnrichmentEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_pipeline():
    config = Config()
    db = Database(config)
    await db.connect()
    
    logger.info("Running Stage 3.5.4 Validations...")
    
    # Create test event
    test_run_id = "test-run-1234"
    test_event_id = "test-event-5678"
    
    # 1. Clean up old test data
    await db.execute_update("DELETE FROM event_classifications WHERE event_id = :id", {"id": test_event_id})
    await db.execute_update("DELETE FROM event_spatial_enrichment WHERE event_id = :id", {"id": test_event_id})
    await db.execute_update("DELETE FROM thermal_events WHERE id = :id", {"id": test_event_id})
    await db.execute_update("DELETE FROM ingestion_runs WHERE id = :id", {"id": test_run_id})
    
    # 2. Insert Ingestion Run
    await db.execute_update(
        "INSERT INTO ingestion_runs (id, source, run_timestamp, success) VALUES (:id, 'TEST', :now, false) ON CONFLICT DO NOTHING",
        {"id": test_run_id, "now": datetime.utcnow()}
    )
    
    # 3. Insert Thermal Event
    # Use coordinates in India (e.g. 22.0, 80.0)
    lat, lon = 22.0, 80.0
    acq_time = datetime.utcnow() - timedelta(days=1)
    
    await db.execute_update("""
        INSERT INTO thermal_events (
            id, acquisition_time, satellite, instrument,
            brightness, brightness_rad, frp, confidence,
            latitude, longitude,
            ingestion_run_id, pipeline_version
        ) VALUES (
            :id, :acq_time, 'TEST-SAT', 'TEST-INST',
            320.0, 10.0, 15.0, 85,
            :lat, :lon,
            :run_id, '1.0.0'
        )
    """, {
        "id": test_event_id, "acq_time": acq_time,
        "lat": lat, "lon": lon, "run_id": test_run_id
    })
    
    logger.info("✓ Inserted test thermal event")
    
    # 4. Trigger Automatic Pipeline manually to simulate firms_collector
    enrich_engine = GISEnrichmentEngine(db, config)
    classifier_engine = ClassifierEngine(db, config)
    
    # Enrichment
    enrich_res = await enrich_engine.enrich_batch([test_event_id])
    assert enrich_res["successful"] == 1, "Enrichment failed"
    logger.info("✓ Enrichment successful")
    
    # Classification
    class_res = await classifier_engine.classify_batch([test_event_id])
    assert class_res["successful"] == 1, "Classification failed"
    logger.info("✓ Classification successful")
    
    # 5. Check Persistence and Database
    res = await db.execute_one(
        "SELECT final_sih_category, is_persistent FROM event_classifications WHERE event_id = :id",
        {"id": test_event_id}
    )
    assert res is not None, "Classification not stored"
    logger.info(f"✓ Event Classified as: {res['final_sih_category']}")
    
    # 6. Idempotency Check
    class_res2 = await classifier_engine.classify_batch([test_event_id])
    assert class_res2["successful"] == 1, "Idempotency failed"
    
    res2 = await db.execute(
        "SELECT final_sih_category FROM event_classifications WHERE event_id = :id",
        {"id": test_event_id}
    )
    assert len(res2) == 1, "Idempotency created duplicates"
    logger.info("✓ Idempotency verified")
    
    # 7. Temporal Leakage Check
    future_event_id = "test-future-9999"
    await db.execute_update("DELETE FROM thermal_events WHERE id = :id", {"id": future_event_id})
    await db.execute_update("""
        INSERT INTO thermal_events (
            id, acquisition_time, satellite, instrument,
            brightness, brightness_rad, frp, confidence,
            latitude, longitude,
            ingestion_run_id, pipeline_version
        ) VALUES (
            :id, :acq_time, 'TEST-SAT', 'TEST-INST',
            320.0, 10.0, 15.0, 85,
            :lat, :lon,
            :run_id, '1.0.0'
        )
    """, {
        "id": future_event_id, 
        "acq_time": datetime.utcnow() + timedelta(days=5),
        "lat": lat, "lon": lon, "run_id": test_run_id
    })
    
    # Re-run persistence for the old event
    class_res3 = await classifier_engine.classify_batch([test_event_id])
    res3 = await db.execute_one(
        "SELECT is_persistent FROM event_classifications WHERE event_id = :id",
        {"id": test_event_id}
    )
    assert res3['is_persistent'] == res['is_persistent'], "Temporal leakage detected: future event affected past event classification"
    logger.info("✓ Temporal Safety verified")
    
    # 8. Provider Failure Isolation Test
    # Simulate failed enrichment -> ML should skip, or assign Unknown/Other?
    test_fail_id = "test-fail-1111"
    await db.execute_update("DELETE FROM event_classifications WHERE event_id = :id", {"id": test_fail_id})
    await db.execute_update("DELETE FROM event_spatial_enrichment WHERE event_id = :id", {"id": test_fail_id})
    await db.execute_update("DELETE FROM thermal_events WHERE id = :id", {"id": test_fail_id})
    
    await db.execute_update("""
        INSERT INTO thermal_events (
            id, acquisition_time, satellite, instrument,
            brightness, brightness_rad, frp, confidence,
            latitude, longitude,
            ingestion_run_id, pipeline_version
        ) VALUES (
            :id, :acq_time, 'TEST-SAT', 'TEST-INST',
            320.0, 10.0, 15.0, 85,
            :lat, :lon,
            :run_id, '1.0.0'
        )
    """, {
        "id": test_fail_id, 
        "acq_time": datetime.utcnow(),
        "lat": lat, "lon": lon, "run_id": test_run_id
    })
    
    # Do NOT enrich, try to classify
    fail_class_res = await classifier_engine.classify_batch([test_fail_id])
    assert fail_class_res["successful"] == 1, "Classifier should handle missing enrichment gracefully"
    
    fail_res = await db.execute_one(
        "SELECT final_sih_category, classification_status FROM event_classifications WHERE event_id = :id",
        {"id": test_fail_id}
    )
    print("Provider Failure Isolation Result:", fail_res)
    assert fail_res['classification_status'] in ['success', 'failed'], "Classification status should be handled"
    assert fail_res['final_sih_category'] is not None, "Should map to a category gracefully"
    logger.info("✓ Provider Failure Isolation verified")
    
    # Cleanup
    await db.execute_update("DELETE FROM event_classifications WHERE event_id IN (:id1, :id2)", {"id1": test_event_id, "id2": test_fail_id})
    await db.execute_update("DELETE FROM event_spatial_enrichment WHERE event_id = :id", {"id": test_event_id})
    await db.execute_update("DELETE FROM thermal_events WHERE id IN (:id1, :id2, :id3)", {"id1": test_event_id, "id2": test_fail_id, "id3": future_event_id})
    await db.execute_update("DELETE FROM ingestion_runs WHERE id = :id", {"id": test_run_id})
    
    await db.disconnect()
    logger.info("All pipeline tests PASSED!")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
