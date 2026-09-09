#!/usr/bin/env python3
"""
Test Dynamic World across multiple locations in India
"""

import sys
import os
from datetime import datetime, timedelta

# Load .env file FIRST before importing any modules that might read env vars
from dotenv import load_dotenv
env_path = 'C:/ProjectX/SIH26162/.env'
print(f"Loading .env from: {env_path}")
load_dotenv(env_path, override=True)

# Now we can import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.config import Config
from backend.gis.dynamic_world_provider import DynamicWorldProvider
import asyncio

async def test_multiple_locations():
    print("=== Testing Dynamic World Across Multiple Indian Locations ===")

    # Load config
    config = Config()
    print(f"EARTH_ENGINE_PROJECT_ID: '{config.EARTH_ENGINE_PROJECT_ID}'")
    print(f"INDIA_BBOX: {config.INDIA_BBOX}")

    # Initialize Dynamic World provider
    dw_provider = DynamicWorldProvider(config)

    if not dw_provider.credentials_available:
        print("ERROR: Earth Engine not initialized")
        return False

    print("Earth Engine initialized successfully\n")

    # Test locations across India (using the INDIA_BBOX)
    test_locations = [
        {"name": "Kashmir (North)", "lat": 34.0, "lon": 74.5},
        {"name": "Delhi (North Central)", "lat": 28.6, "lon": 77.2},
        {"name": "Rajasthan (West)", "lat": 26.9, "lon": 75.8},
        {"name": "Gujarat (West)", "lat": 22.3, "lon": 71.0},
        {"name": "Mumbai (West Coast)", "lat": 19.0, "lon": 72.8},
        {"name": "Pune (Central)", "lat": 18.5, "lon": 73.8},
        {"name": "Hyderabad (South Central)", "lat": 17.4, "lon": 78.5},
        {"name": "Karnataka (South)", "lat": 15.3, "lon": 75.7},
        {"name": "Tamil Nadu (South)", "lat": 13.0, "lon": 80.2},
        {"name": "Kerala (South West)", "lat": 10.0, "lon": 76.3},
        {"name": "West Bengal (East)", "lat": 22.5, "lon": 88.4},
        {"name": "Assam (North East)", "lat": 26.2, "lon": 91.5},
    ]

    # Use a date that we know works from previous testing
    test_date = "2026-07-14T10:30:00Z"
    results = []

    for location in test_locations:
        print(f"Testing {location['name']} ({location['lat']}, {location['lon']}):")

        try:
            result = await dw_provider.get_land_cover(
                location['lat'],
                location['lon'],
                test_date
            )

            if result.get('coverage_state') == 'live':
                label = result.get('land_cover_label')
                probs = result.get('class_probabilities', {})

                # Extract model features
                dw_bare = probs.get('bare', 0.0)
                dw_confidence = max(probs.values()) if probs else 0.0
                dw_grass = probs.get('grass', 0.0)
                dw_water = probs.get('water', 0.0)

                print(f"  + LIVE - Land cover: {label}")
                print(f"    dw_bare: {dw_bare:.3f}, dw_confidence: {dw_confidence:.3f}")
                print(f"    dw_grass: {dw_grass:.3f}, dw_water: {dw_water:.3f}")

                results.append({
                    "location": location['name'],
                    "coords": f"{location['lat']}, {location['lon']}",
                    "status": "LIVE",
                    "label": label,
                    "dw_bare": dw_bare,
                    "dw_confidence": dw_confidence,
                    "dw_grass": dw_grass,
                    "dw_water": dw_water
                })
            else:
                print(f"  - {result.get('coverage_state').upper()} - {result.get('error', 'No error details')}")
                results.append({
                    "location": location['name'],
                    "coords": f"{location['lat']}, {location['lon']}",
                    "status": result.get('coverage_state', 'UNKNOWN').upper(),
                    "error": result.get('error', 'No error details')
                })

        except Exception as e:
            print(f"  - ERROR: {e}")
            results.append({
                "location": location['name'],
                "coords": f"{location['lat']}, {location['lon']}",
                "status": "ERROR",
                "error": str(e)
            })

        print()

    # Summary
    print("=== SUMMARY ===")
    live_count = sum(1 for r in results if r.get('status') == 'LIVE')
    total_count = len(results)

    print(f"Live results: {live_count}/{total_count}")

    if live_count > 0:
        print("\nLive locations:")
        for r in results:
            if r.get('status') == 'LIVE':
                print(f"  {r['location']} ({r['coords']}): {r['label']}")

        print(f"\nSUCCESS: Dynamic World working across {live_count} locations in India")
        return True
    else:
        print("\nFAILURE: No live Dynamic World data retrieved for any location")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_multiple_locations())
    sys.exit(0 if result else 1)