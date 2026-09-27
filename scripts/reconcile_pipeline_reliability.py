import asyncio

from backend.config import Config
from backend.database import Database
from backend.firms_collector import FIRMSCollector
from backend.gis.enrichment_engine import GISEnrichmentEngine


async def main():
    config = Config()
    db = Database(config)
    await db.connect()

    try:
        collector = FIRMSCollector(db, config)
        run_reconcile = await collector.reconcile_orphaned_ingestion_runs(since_hours=72)
        print("ORPHANED INGESTION RUN RECONCILIATION")
        print(run_reconcile)

        enrichment_engine = GISEnrichmentEngine(db, config)
        enrichment_reconcile = await enrichment_engine.reconcile_missing_enrichment(since_hours=72, limit=500)
        print("\nMISSING/PARTIAL ENRICHMENT RECONCILIATION")
        print(enrichment_reconcile)
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
