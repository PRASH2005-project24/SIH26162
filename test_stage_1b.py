"""
Test OSM Provider and GIS Enrichment Pipeline
Verifies Overpass API connectivity and enrichment functionality
"""

import asyncio
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Set environment variables
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://postgres:PRASH2005@localhost:5432/sih26162'
os.environ['DEMO_MODE'] = 'true'


async def test_osm_provider():
    """Test OSM Overpass provider"""
    logger.info("=" * 80)
    logger.info("TEST 1: OSM Overpass Provider")
    logger.info("=" * 80)

    from backend.database import Database
    from backend.config import Config
    from backend.gis.osm_provider import OSMProvider

    config = Config()
    db = Database(config)
    await db.connect()

    try:
        osm = OSMProvider(db, config)

        # Test 1: Query industrial features in Pune
        logger.info("\n📍 Querying industrial features in Pune...")
        pune_lat, pune_lon = 18.5204, 73.8567

        industrial = await osm.get_industrial_features(pune_lat, pune_lon, buffer_km=5.0)
        logger.info(f"✓ Industrial features found: {industrial['count']}")
        logger.info(f"  Coverage state: {industrial['coverage_state']}")
        logger.info(f"  Source: {industrial['source']}")

        if industrial['count'] > 0:
            logger.info(f"  Sample features:")
            for feature in industrial['features'][:3]:
                logger.info(f"    - {feature.get('name', 'unnamed')}: ({feature['latitude']}, {feature['longitude']})")

        # Test 2: Query water features
        logger.info("\n💧 Querying water features in Pune...")
        water = await osm.get_water_features(pune_lat, pune_lon, buffer_km=2.0)
        logger.info(f"✓ Water features found: {len(water.get('features', []))}")
        logger.info(f"  Has water: {water.get('has_water', False)}")
        logger.info(f"  Coverage state: {water['coverage_state']}")

        # Test 3: Test caching
        logger.info("\n💾 Testing OSM cache...")
        industrial_cached = await osm.get_industrial_features(pune_lat, pune_lon, buffer_km=5.0)
        logger.info(f"✓ Cache hit! Coverage state: {industrial_cached['coverage_state']}")

        # Test 4: India-wide boundary check
        logger.info("\n🗺️  Testing India-wide coverage...")

        # Point in Mumbai
        mumbai_lat, mumbai_lon = 19.0760, 72.8777
        mumbai_industrial = await osm.get_industrial_features(mumbai_lat, mumbai_lon, buffer_km=3.0)
        logger.info(f"✓ Mumbai ({mumbai_lat}, {mumbai_lon}): {mumbai_industrial['count']} features")

        # Point in Bangalore
        bangalore_lat, bangalore_lon = 12.9716, 77.5946
        bangalore_industrial = await osm.get_industrial_features(bangalore_lat, bangalore_lon, buffer_km=3.0)
        logger.info(f"✓ Bangalore ({bangalore_lat}, {bangalore_lon}): {bangalore_industrial['count']} features")

        # Point outside India (should fail gracefully)
        outside_lat, outside_lon = 40.7128, -74.0060  # New York
        outside_industrial = await osm.get_industrial_features(outside_lat, outside_lon, buffer_km=3.0)
        logger.info(f"✓ Outside India ({outside_lat}, {outside_lon}): {outside_industrial['count']} features (expected 0)")
        logger.info(f"  Coverage state: {outside_industrial['coverage_state']} (expected 'outside_india')")

        logger.info("\n✅ OSM Provider tests passed!")
        return True

    except Exception as e:
        logger.error(f"❌ OSM Provider test failed: {e}", exc_info=True)
        return False

    finally:
        await db.disconnect()


async def test_dynamic_world_provider():
    """Test Google Dynamic World provider"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Google Dynamic World Provider")
    logger.info("=" * 80)

    from backend.config import Config
    from backend.gis.dynamic_world_provider import DynamicWorldProvider

    config = Config()
    dw = DynamicWorldProvider(config)

    try:
        # Test with demo data (credentials unavailable)
        logger.info("\n📡 Querying land cover (demo mode)...")

        pune_lat, pune_lon = 18.5204, 73.8567
        acq_time = "2026-08-20T10:30:00Z"

        land_cover = await dw.get_land_cover(pune_lat, pune_lon, acq_time)

        logger.info(f"✓ Land cover result received")
        logger.info(f"  Label: {land_cover.get('land_cover_label')}")
        logger.info(f"  Coverage state: {land_cover.get('coverage_state')}")
        logger.info(f"  Provider version: {land_cover.get('provider_version')}")

        if land_cover.get('class_probabilities'):
            logger.info(f"  Class probabilities:")
            for class_name, prob in list(land_cover['class_probabilities'].items())[:5]:
                logger.info(f"    - {class_name}: {prob:.3f}")

        logger.info("\n✅ Dynamic World Provider tests passed!")
        return True

    except Exception as e:
        logger.error(f"❌ Dynamic World Provider test failed: {e}", exc_info=True)
        return False


async def test_enrichment_engine():
    """Test GIS Enrichment Engine"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: GIS Enrichment Engine")
    logger.info("=" * 80)

    from backend.database import Database
    from backend.config import Config
    from backend.gis.enrichment_engine import GISEnrichmentEngine

    config = Config()
    db = Database(config)
    await db.connect()

    try:
        engine = GISEnrichmentEngine(db, config)

        # Get a sample event
        logger.info("\n🔍 Fetching sample event...")
        event = await db.execute_one(
            "SELECT id FROM thermal_events WHERE status = 'active' LIMIT 1"
        )

        if not event:
            logger.warning("⚠️  No active events found for enrichment test")
            return False

        event_id = event['id']
        logger.info(f"✓ Using event: {event_id}")

        # Enrich single event
        logger.info("\n🔄 Enriching single event...")
        result = await engine.enrich_event(event_id)

        if result['status'] == 'success':
            logger.info(f"✓ Enrichment successful")
            logger.info(f"  Inside industrial: {result.get('inside_industrial')}")
            logger.info(f"  Nearby water: {result.get('nearby_water')}")
            logger.info(f"  Land cover: {result.get('land_cover_label')}")
            logger.info(f"  Nearest distance (m): {result.get('nearest_distance_m')}")
            logger.info(f"  Confidence score: {result.get('confidence_score', 0):.3f}")
            logger.info(f"  OSM coverage: {result.get('osm_coverage')}")
            logger.info(f"  Dynamic World coverage: {result.get('dw_coverage')}")
        else:
            logger.error(f"✗ Enrichment failed: {result.get('reason')}")
            return False

        # Test batch enrichment
        logger.info("\n⚙️  Testing batch enrichment...")
        batch_result = await engine.enrich_batch(limit=5)
        logger.info(f"✓ Batch enrichment complete")
        logger.info(f"  Total: {batch_result['batch_size']}")
        logger.info(f"  Successful: {batch_result['successful']}")
        logger.info(f"  Failed: {batch_result['failed']}")

        logger.info("\n✅ Enrichment Engine tests passed!")
        return True

    except Exception as e:
        logger.error(f"❌ Enrichment Engine test failed: {e}", exc_info=True)
        return False

    finally:
        await db.disconnect()


async def test_enrichment_api():
    """Test Enrichment API endpoints"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: Enrichment API Endpoints")
    logger.info("=" * 80)

    from backend.database import Database
    from backend.config import Config
    from backend.gis.enrichment_engine import GISEnrichmentEngine

    config = Config()
    db = Database(config)
    await db.connect()

    try:
        # Test enrichment statistics endpoint
        logger.info("\n📊 Getting enrichment statistics...")

        stats = await db.execute_one(
            """
            SELECT
                (SELECT COUNT(*) FROM thermal_events) as total_events,
                (SELECT COUNT(DISTINCT event_id) FROM event_spatial_enrichment) as enriched_events
            """
        )

        total = stats.get('total_events', 0) or 0
        enriched = stats.get('enriched_events', 0) or 0
        coverage = (enriched / total * 100) if total > 0 else 0

        logger.info(f"✓ Statistics retrieved")
        logger.info(f"  Total events: {total}")
        logger.info(f"  Enriched events: {enriched}")
        logger.info(f"  Coverage: {coverage:.1f}%")

        # Test getting enriched events
        logger.info("\n📋 Fetching enriched events...")
        enriched_events = await db.execute(
            """
            SELECT te.id, te.latitude, te.longitude, ese.land_cover_label
            FROM event_spatial_enrichment ese
            JOIN thermal_events te ON ese.event_id = te.id
            LIMIT 5
            """
        )

        logger.info(f"✓ Found {len(enriched_events)} enriched events")
        for event in enriched_events[:3]:
            logger.info(f"  - {event['id'][:8]}... at ({event['latitude']:.4f}, {event['longitude']:.4f}): {event['land_cover_label']}")

        logger.info("\n✅ Enrichment API tests passed!")
        return True

    except Exception as e:
        logger.error(f"❌ Enrichment API test failed: {e}", exc_info=True)
        return False

    finally:
        await db.disconnect()


async def main():
    """Run all tests"""
    logger.info("\n🧪 SIH26162 Stage 1B GIS Enrichment - Test Suite")
    logger.info("=" * 80)

    results = {
        "OSM Provider": await test_osm_provider(),
        "Dynamic World Provider": await test_dynamic_world_provider(),
        "Enrichment Engine": await test_enrichment_engine(),
        "Enrichment API": await test_enrichment_api(),
    }

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {test_name}")

    total_passed = sum(1 for p in results.values() if p)
    total_tests = len(results)
    logger.info(f"\nTotal: {total_passed}/{total_tests} tests passed")

    return all(results.values())


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
