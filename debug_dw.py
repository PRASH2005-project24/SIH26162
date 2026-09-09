#!/usr/bin/env python3
"""
Debug Dynamic World query
"""

import sys
import os
from datetime import datetime, timedelta

# Load .env file FIRST before importing any modules that might read env vars
from dotenv import load_dotenv
env_path = 'C:/ProjectX/SIH26162/.env'
print(f"Loading .env from: {env_path}")
load_dotenv(env_path, override=True)  # override=True ensures we get the .env values

# Now we can import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.config import Config
import ee

def debug_dw_query():
    print("=== Debugging Dynamic World Query ===")

    # Load config
    config = Config()
    print(f"EARTH_ENGINE_PROJECT_ID: '{config.EARTH_ENGINE_PROJECT_ID}'")

    try:
        # Initialize Earth Engine
        print("Initializing Earth Engine...")
        ee.Initialize(
            opt_url="https://earthengine-highvolume.googleapis.com",
            project=config.EARTH_ENGINE_PROJECT_ID
        )
        print("SUCCESS: Earth Engine initialized!")

        # Test parameters
        event_lat, event_lon = 18.5204, 73.8567  # Pune, India
        acquisition_date = "2026-09-06T10:30:00Z"
        buffer_km = 0.5

        print(f"\nQuery parameters:")
        print(f"  Location: ({event_lat}, {event_lon})")
        print(f"  Acquisition date: {acquisition_date}")
        print(f"  Buffer: {buffer_km} km")

        # Parse acquisition date
        acq_dt = datetime.fromisoformat(acquisition_date.replace('Z', '+00:00'))
        print(f"  Parsed acquisition date: {acq_dt}")

        # Create point geometry
        point = ee.Geometry.Point([event_lon, event_lat])
        print(f"  Point geometry: {point.getInfo()}")

        # Buffer for analysis
        buffer_m = buffer_km * 1000
        buffered_point = point.buffer(buffer_m)
        print(f"  Buffered point: {buffered_point.getInfo()}")

        # Query Dynamic World
        dw = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        print(f"  Dynamic World collection: {dw}")

        # Filter by date (within 30 days of acquisition)
        start_date = (acq_dt - timedelta(days=15)).strftime("%Y-%m-%d")
        end_date = (acq_dt + timedelta(days=15)).strftime("%Y-%m-%d")
        print(f"  Date range: {start_date} to {end_date}")

        dw_filtered = (
            dw
            .filterDate(start_date, end_date)
            .filterBounds(buffered_point)
        )
        print(f"  Filtered collection: {dw_filtered}")

        # Check size of filtered collection
        size = dw_filtered.size().getInfo()
        print(f"  Filtered collection size: {size}")

        if size > 0:
            # Get the first image
            first_image = dw_filtered.first()
            print(f"  First image: {first_image}")

            if first_image:
                # Get image info
                image_info = first_image.getInfo()
                print(f"  First image info keys: {list(image_info.keys()) if image_info else 'None'}")

                # Try to get the bands
                bands = first_image.bandNames().getInfo()
                print(f"  Available bands: {bands}")

                # Try reduceRegion
                print("  Attempting reduceRegion...")
                sample = first_image.reduceRegion(
                    reducer=ee.Reducer.first(),
                    geometry=point,
                    scale=10,
                    bestEffort=True
                )
                results = sample.getInfo()
                print(f"  ReduceRegion results: {results}")
            else:
                print("  First image is None!")
        else:
            print("  No images found in the filtered collection")

            # Let's try a broader date range to see if we can get ANY data
            print("\nTrying broader date range (last 6 months)...")
            broad_start = (acq_dt - timedelta(days=180)).strftime("%Y-%m-%d")
            broad_end = (acq_dt + timedelta(days=180)).strftime("%Y-%m-%d")
            print(f"  Broad date range: {broad_start} to {broad_end}")

            dw_broad = (
                dw
                .filterDate(broad_start, broad_end)
                .filterBounds(buffered_point)
            )
            broad_size = dw_broad.size().getInfo()
            print(f"  Broad filtered collection size: {broad_size}")

            if broad_size > 0:
                broad_first = dw_broad.first()
                print(f"  First image from broad query: {broad_first}")
                if broad_first:
                    broad_info = broad_first.getInfo()
                    print(f"  Broad image info keys: {list(broad_info.keys()) if broad_info else 'None'}")
                else:
                    print("  Broad first image is None!")
            else:
                print("  Still no images found with broad date range")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_dw_query()