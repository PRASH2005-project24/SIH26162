#!/usr/bin/env python3
"""
Test Dynamic World reduceRegion to get a successful query
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

def test_dw_reduce():
    print("=== Testing Dynamic World reduceRegion ===")

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

        # Test parameters - use a date that likely has data
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
        print(f"  Point geometry: {point.getInfo()}")

        # Buffer for analysis
        buffer_m = buffer_km * 1000
        buffered_point = point.buffer(buffer_m)
        print(f"  Buffered point radius: {buffer_m} meters")

        # Query Dynamic World
        dw = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
        print(f"  Dynamic World collection loaded")

        # Filter by date (within 15 days of acquisition to match original logic)
        start_date = (acq_dt - timedelta(days=15)).strftime("%Y-%m-%d")
        end_date = (acq_dt + timedelta(days=15)).strftime("%Y-%m-%d")
        print(f"  Date range: {start_date} to {end_date}")

        dw_filtered = (
            dw
            .filterDate(start_date, end_date)
            .filterBounds(buffered_point)
        )
        # Check size of filtered collection
        size = dw_filtered.size().getInfo()
        print(f"  Filtered collection size: {size}")

        if size > 0:
            # Get the first image
            first_image = dw_filtered.first()
            print(f"  First image retrieved")

            # Get image info to see bands
            image_info = first_image.getInfo()
            bands = [b['id'] for b in image_info['bands']]
            print(f"  Available bands: {bands}")

            # Try reduceRegion for the classification band (label) and probability bands
            # We'll try to get the 'label' band and the probability bands
            # According to Dynamic World documentation, there is a 'label' band and then probability bands
            # Let's try to reduceRegion to get the first value of each band
            sample = first_image.reduceRegion(
                reducer=ee.Reducer.first(),
                geometry=point,
                scale=10,
                bestEffort=True
            )
            results = sample.getInfo()
            print(f"  ReduceRegion results: {results}")

            # Now, let's try to parse the results as we did in the provider
            # The Dynamic World dataset has bands: 'label', 'probability_band_0', ... 'probability_band_8'
            # where the probability bands correspond to the classes in order:
            # 0: water, 1: trees, 2: grass, 3: flooded_vegetation, 4: crops, 5: shrub_scrub, 6: built, 7: bare, 8: snow_ice
            if results:
                # Extract the label (classification)
                label_idx = results.get('label')
                if label_idx is not None:
                    if isinstance(label_idx, list):
                        label_idx = int(label_idx[0])
                    else:
                        label_idx = int(label_idx)
                    print(f"  Classification index: {label_idx}")
                    # Map to class name
                    LAND_COVER_CLASSES = {
                        0: "water",
                        1: "trees",
                        2: "grass",
                        3: "flooded_vegetation",
                        4: "crops",
                        5: "shrub_scrub",
                        6: "built",
                        7: "bare",
                        8: "snow_ice",
                    }
                    label = LAND_COVER_CLASSES.get(label_idx, "unknown")
                    print(f"  Classification label: {label}")

                # Extract probabilities
                probs = {}
                for class_idx in range(9):
                    class_name = LAND_COVER_CLASSES[class_idx]
                    prob_key = f'probability_band_{class_idx}'
                    prob_val = results.get(prob_key)
                    if prob_val is not None:
                        if isinstance(prob_val, list):
                            prob_val = float(prob_val[0])
                        else:
                            prob_val = float(prob_val)
                        probs[class_name] = round(prob_val, 4)
                    else:
                        probs[class_name] = 0.0
                print(f"  Class probabilities: {probs}")

                # Normalize probabilities (they should already sum to ~1.0)
                total = sum(probs.values())
                if total > 0:
                    probs = {k: round(v / total, 4) for k, v in probs.items()}
                    print(f"  Normalized probabilities: {probs}")

                # Now, let's map to the features expected by the model
                dw_bare = probs.get('bare', 0.0)
                dw_confidence = max(probs.values()) if probs else 0.0  # Using max probability as confidence
                dw_difference = abs(probs.get('grass', 0.0) - probs.get('bare', 0.0))
                dw_found = 1.0 if label != "unknown" else 0.0
                dw_grass = probs.get('grass', 0.0)
                dw_water = probs.get('water', 0.0)

                print(f"\nMapped features for model:")
                print(f"  dw_bare: {dw_bare:.4f}")
                print(f"  dw_confidence: {dw_confidence:.4f}")
                print(f"  dw_difference: {dw_difference:.4f}")
                print(f"  dw_found: {dw_found}")
                print(f"  dw_grass: {dw_grass:.4f}")
                print(f"  dw_water: {dw_water:.4f}")

                # Check if we got a live-like result (coverage_state would be 'live' in the provider)
                print(f"\nSUCCESS: Retrieved Dynamic World data for {acquisition_date}")
                return True
            else:
                print("  ReduceRegion returned no results")
        else:
            print("  No images found in the date range. Trying to get the most recent image...")

            # Let's try to get the most recent image available for the point
            dw_recent = (
                dw
                .filterBounds(buffered_point)
                .sort('system:time_start', False)  # Most recent first
            )
            recent_size = dw_recent.size().getInfo()
            print(f"  Recent collection size: {recent_size}")

            if recent_size > 0:
                recent_first = dw_recent.first()
                print(f"  Most recent image retrieved")
                # Get its date
                date_ms = ee.Number(recent_first.get('system:time_start')).getInfo()
                date_str = datetime.utcfromtimestamp(date_ms / 1000).strftime('%Y-%m-%d')
                print(f"  Image date: {date_str}")

                # Try reduceRegion on this image
                sample = recent_first.reduceRegion(
                    reducer=ee.Reducer.first(),
                    geometry=point,
                    scale=10,
                    bestEffort=True
                )
                results = sample.getInfo()
                print(f"  ReduceRegion results: {results}")

                if results:
                    # Same parsing as above
                    label_idx = results.get('label')
                    if label_idx is not None:
                        if isinstance(label_idx, list):
                            label_idx = int(label_idx[0])
                        else:
                            label_idx = int(label_idx)
                        LAND_COVER_CLASSES = {
                            0: "water", 1: "trees", 2: "grass", 3: "flooded_vegetation",
                            4: "crops", 5: "shrub_scrub", 6: "built", 7: "bare", 8: "snow_ice"
                        }
                        label = LAND_COVER_CLASSES.get(label_idx, "unknown")
                        print(f"  Classification label: {label}")

                    probs = {}
                    for class_idx in range(9):
                        class_name = LAND_COVER_CLASSES[class_idx]
                        prob_key = f'probability_band_{class_idx}'
                        prob_val = results.get(prob_key)
                        if prob_val is not None:
                            if isinstance(prob_val, list):
                                prob_val = float(prob_val[0])
                            else:
                                prob_val = float(prob_val)
                            probs[class_name] = round(prob_val, 4)
                        else:
                            probs[class_name] = 0.0
                    print(f"  Class probabilities: {probs}")

                    # Normalize
                    total = sum(probs.values())
                    if total > 0:
                        probs = {k: round(v / total, 4) for k, v in probs.items()}
                        print(f"  Normalized probabilities: {probs}")

                    # Map to model features
                    dw_bare = probs.get('bare', 0.0)
                    dw_confidence = max(probs.values()) if probs else 0.0
                    dw_difference = abs(probs.get('grass', 0.0) - probs.get('bare', 0.0))
                    dw_found = 1.0 if label != "unknown" else 0.0
                    dw_grass = probs.get('grass', 0.0)
                    dw_water = probs.get('water', 0.0)

                    print(f"\nMapped features for model:")
                    print(f"  dw_bare: {dw_bare:.4f}")
                    print(f"  dw_confidence: {dw_confidence:.4f}")
                    print(f"  dw_difference: {dw_difference:.4f}")
                    print(f"  dw_found: {dw_found}")
                    print(f"  dw_grass: {dw_grass:.4f}")
                    print(f"  dw_water: {dw_water:.4f}")

                    print(f"\nSUCCESS: Retrieved Dynamic World data from most recent image ({date_str})")
                    return True
                else:
                    print("  ReduceRegion on most recent image returned no results")
            else:
                print("  No images found at all for the point")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = test_dw_reduce()
    sys.exit(0 if result else 1)