#!/usr/bin/env python3
"""
Detailed debug of Dynamic World query to see why it's returning None
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

def debug_dw_detailed():
    print("=== Detailed Debug of Dynamic World Query ===")

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

        # Test parameters - use the same as in our successful test
        event_lat, event_lon = 18.5204, 73.8567  # Pune, India
        # Use a date a few days ago to ensure we have data
        acquisition_date = (datetime.utcnow() - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
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
        print(f"  Point geometry created")

        # Buffer for analysis
        buffer_m = buffer_km * 1000
        buffered_point = point.buffer(buffer_m)
        print(f"  Buffered point created (radius: {buffer_m} meters)")

        # Query Dynamic World
        dw = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        print(f"  Dynamic World collection loaded")

        # Filter by date (within 30 days of acquisition)
        start_date = (acq_dt - timedelta(days=15)).strftime("%Y-%m-%d")
        end_date = (acq_dt + timedelta(days=15)).strftime("%Y-%m-%d")
        print(f"  Date range: {start_date} to {end_date}")

        print(f"  Applying date filter...")
        dw_date_filtered = dw.filterDate(start_date, end_date)
        print(f"  Date filtered collection created")

        print(f"  Applying bounds filter...")
        dw_filtered = dw_date_filtered.filterBounds(buffered_point)
        print(f"  Bounds filtered collection created")

        # Check size of filtered collection
        print(f"  Checking collection size...")
        size = dw_filtered.size().getInfo()
        print(f"  Filtered collection size: {size}")

        if size > 0:
            print(f"  Getting first image from collection...")
            first_image = dw_filtered.first()
            print(f"  First image: {first_image}")

            if first_image is not None:
                print(f"  First image is NOT None")
                # Try to get some info about it
                try:
                    image_info = first_image.getInfo()
                    print(f"  Image info type: {type(image_info)}")
                    if image_info:
                        print(f"  Image has {len(image_info.get('bands', []))} bands")
                except Exception as e:
                    print(f"  Error getting image info: {e}")
            else:
                print(f"  FIRST IMAGE IS NONE!")
                print(f"  This means the collection has size > 0 but .first() returned None")

                # Let's try to get the image in a different way
                print(f"  Trying to get image using .limit(1)...")
                limited = dw_filtered.limit(1)
                limited_size = limited.size().getInfo()
                print(f"  Limited collection size: {limited_size}")

                if limited_size > 0:
                    first_from_limited = limited.first()
                    print(f"  First from limited: {first_from_limited}")
                else:
                    print(f"  Limited collection also has size 0?")
        else:
            print(f"  No images found in the date range and bounds")

            # Let's debug the filters step by step
            print(f"\n  Debugging filters...")

            # Check the raw collection size
            raw_size = dw.size().getInfo()
            print(f"  Raw DW collection size: {raw_size}")

            # Check date filtered size
            date_filtered_size = dw.filterDate(start_date, end_date).size().getInfo()
            print(f"  Date filtered size: {date_filtered_size}")

            # Check bounds filtered size (no date filter)
            bounds_filtered_size = dw.filterBounds(buffered_point).size().getInfo()
            print(f"  Bounds filtered size (no date): {bounds_filtered_size}")

            # Let's try a much broader date range
            print(f"\n  Trying much broader date range (2 years)...")
            broad_start = (acq_dt - timedelta(days=365*2)).strftime("%Y-%m-%d")
            broad_end = (acq_dt + timedelta(days=365*2)).strftime("%Y-%m-%d")
            print(f"  Broad date range: {broad_start} to {broad_end}")

            broad_filtered = dw.filterDate(broad_start, broad_end).filterBounds(buffered_point)
            broad_size = broad_filtered.size().getInfo()
            print(f"  Broad filtered collection size: {broad_size}")

            if broad_size > 0:
                print(f"  Found {broad_size} images with broad date range!")
                broad_first = broad_filtered.first()
                print(f"  First image from broad query: {broad_first}")

                if broad_first is not None:
                    print(f"  SUCCESS: Broad query returned an image")
                    # Try to get the date of this image
                    try:
                        date_ms = ee.Number(broad_first.get('system:time_start')).getInfo()
                        date_str = datetime.utcfromtimestamp(date_ms / 1000).strftime('%Y-%m-%d')
                        print(f"  Image date: {date_str}")
                    except Exception as e:
                        print(f"  Error getting image date: {e}")
                else:
                    print(f"  But .first() still returned None for broad query!")
            else:
                print(f"  Still no images found with broad date range")

                # Let's check if we can get ANY image from the collection at all
                print(f"\n  Checking if we can get ANY image from the DW collection...")
                any_image = dw.first()
                print(f"  Any image from DW collection: {any_image}")

                if any_image is not None:
                    print(f"  Got an image from the raw collection!")
                    try:
                        date_ms = ee.Number(any_image.get('system:time_start')).getInfo()
                        date_str = datetime.utcfromtimestamp(date_ms / 1000).strftime('%Y-%m-%d')
                        print(f"  Image date: {date_str}")
                    except Exception as e:
                        print(f"  Error getting image date: {e}")
                else:
                    print(f"  Cannot get ANY image from the DW collection - this is strange!")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_dw_detailed()