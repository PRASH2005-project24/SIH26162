import asyncio
from backend.database import Database
from backend.config import Config
from backend.ml.classifier_engine import ClassifierEngine
import logging

logging.basicConfig(level=logging.INFO)

async def main():
    db = Database(Config())
    await db.connect()
    
    engine = ClassifierEngine(db, Config())
    
    print("Finding unclassified events...")
    query = """
        SELECT t.id 
        FROM thermal_events t
        LEFT JOIN event_classifications c ON t.id = c.event_id
        WHERE c.event_id IS NULL
    """
    unclassified = await db.execute(query)
    
    if not unclassified:
        print("All events are already classified!")
        await db.disconnect()
        return
        
    event_ids = [row["id"] for row in unclassified]
    print(f"Found {len(event_ids)} unclassified events. Starting batch classification...")
    
    # Process in chunks of 50
    chunk_size = 50
    successful = 0
    failed = 0
    
    for i in range(0, len(event_ids), chunk_size):
        chunk = event_ids[i:i+chunk_size]
        print(f"Processing batch {i//chunk_size + 1}/{(len(event_ids) + chunk_size - 1)//chunk_size}...")
        result = await engine.classify_batch(chunk)
        successful += result.get("successful", 0)
        failed += result.get("failed", 0)
        
    print(f"\nBackfill complete! Successful: {successful}, Failed: {failed}")
    await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
