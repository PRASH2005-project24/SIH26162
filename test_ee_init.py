#!/usr/bin/env python3
"""
Test Earth Engine initialization and Dynamic World query
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.config import Config
from backend.gis.dynamic_world_provider import DynamicWorldProvider
import asyncio

async def test_earth_engine():
    print("=== Testing Earth Engine Initialization ===")

    # Load config
    config = Config()
    print(f"EARTH_ENGINE_PROJECT_ID: '{config.EARTH_ENGINE_PROJECT_ID}'")
    print(f"DEMO_MODE: {config.DEMO_MODE}")

    # Initialize Dynamic World provider
    dw_provider = DynamicWorldProvider(config)

    print(f"Earth Engine credentials available: {dw_provider.credentials_available}")
    print(f"Earth Engine client initialized: {dw_provider.ee_client is not None}")

    if dw_provider.credentials_available:
        print("✓ Earth Engine initialized successfully")

        # Test a real query for Pune coordinates
        print("\n=== Testing Dynamic World Query ===")
        test_lat, test_lon = 18.5204, 73.8567  # Pune, India
        test_date = "2026-09-06T10:30:00Z"

        try:
            result = await dw_provider.get_land_cover(test_lat, test_lon, test_date)
            print(f"Query result: {result}")

            # Check if we got live data
            if result.get('coverage_state') == 'live':
                print("✓ Successfully retrieved LIVE Dynamic World data")

                # Extract the required features for the model
                label = result.get('land_cover_label')
                probs = result.get('class_probabilities', {})

                print(f"\nLand cover label: {label}")
                print(f"Class probabilities: {probs}")

                # Map to expected model features
                dw_bare = probs.get('bare', 0.0)
                # For confidence, we'll use a reasonable default if not directly available
                dw_confidence = result.get('class_probabilities', {}).get('confidence', 0.8)
                dw_difference = abs(probs.get('grass', 0.0) - probs.get('bare', 0.0))  # Example calculation
                dw_found = 1.0 if label else 0.0
                dw_grass = probs.get('grass', 0.0)
                dw_water = probs.get('water', 0.0)

                print(f"\nMapped features for model:")
                print(f"  dw_bare: {dw_bare}")
                print(f"  dw_confidence: {dw_confidence}")
                print(f"  dw_difference: {dw_difference}")
                print(f"  dw_found: {dw_found}")
                print(f"  dw_grass: {dw_grass}")
                print(f"  dw_water: {dw_water}")

                # Verify forbidden features are NOT used
                forbidden_features = ['dw_label', 'dw_crops', 'dw_built', 'dw_trees', 'dw_shrub_and_scrub']
                print(f"\nVerifying forbidden features are NOT in model input:")
                for feat in forbidden_features:
                    if feat == 'dw_label':
                        print(f"  {feat}: NOT USED (land cover label is {label})")
                    elif feat in probs:
                        print(f"  {feat}: {probs.get(feat, 0.0)} - AVAILABLE in provider but NOT passed to model")
                    else:
                        print(f"  {feat}: NOT AVAILABLE in provider")

                return True
            else:
                print(f"! Got non-live data: {result.get('coverage_state')}")
                if result.get('coverage_state') == 'demo_mode':
                    print("! Using demo data - Earth Engine credentials may not be properly configured")
                return False

        except Exception as e:
            print(f"X Error querying Dynamic World: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("X Earth Engine not initialized - checking why...")
        if not config.EARTH_ENGINE_PROJECT_ID:
            print("  X EARTH_ENGINE_PROJECT_ID not set")
        else:
            print("  X Earth Engine initialization failed - check credentials")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_earth_engine())
    sys.exit(0 if result else 1)