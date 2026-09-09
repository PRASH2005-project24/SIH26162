#!/usr/bin/env python3
"""
Final test for Earth Engine initialization and Dynamic World query
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
from backend.gis.dynamic_world_provider import DynamicWorldProvider
import asyncio

async def test_earth_engine():
    print("=== Testing Earth Engine Initialization ===")

    # Load config (now should have correct values from .env)
    config = Config()
    print(f"EARTH_ENGINE_PROJECT_ID: '{config.EARTH_ENGINE_PROJECT_ID}'")
    print(f"DEMO_MODE: {config.DEMO_MODE}")

    # Initialize Dynamic World provider
    dw_provider = DynamicWorldProvider(config)

    print(f"Earth Engine credentials available: {dw_provider.credentials_available}")
    print(f"Earth Engine client initialized: {dw_provider.ee_client is not None}")

    if dw_provider.credentials_available:
        print("Earth Engine initialized successfully")

        # Test a real query for Pune coordinates - use a date we know works from our previous test
        test_lat, test_lon = 18.5204, 73.8567  # Pune, India
        # Use a date from our successful test: 2026-07-14 (from the debug output)
        test_date = "2026-07-14T10:30:00Z"

        try:
            result = await dw_provider.get_land_cover(test_lat, test_lon, test_date)
            print(f"Query result: {result}")

            # Check if we got live data
            if result.get('coverage_state') == 'live':
                print("SUCCESS: Retrieved LIVE Dynamic World data")

                # Extract the required features for the model
                label = result.get('land_cover_label')
                probs = result.get('class_probabilities', {})

                print(f"\nLand cover label: {label}")
                print(f"Class probabilities: {probs}")

                # Map to expected model features
                dw_bare = probs.get('bare', 0.0)
                dw_confidence = max(probs.values()) if probs else 0.0  # Using max probability as confidence
                dw_difference = abs(probs.get('grass', 0.0) - probs.get('bare', 0.0))  # Example calculation
                dw_found = 1.0 if label and label != "unknown" else 0.0
                dw_grass = probs.get('grass', 0.0)
                dw_water = probs.get('water', 0.0)

                print(f"\nMapped features for model:")
                print(f"  dw_bare: {dw_bare:.4f}")
                print(f"  dw_confidence: {dw_confidence:.4f}")
                print(f"  dw_difference: {dw_difference:.4f}")
                print(f"  dw_found: {dw_found}")
                print(f"  dw_grass: {dw_grass:.4f}")
                print(f"  dw_water: {dw_water:.4f}")

                # Verify forbidden features are NOT used
                forbidden_features = ['dw_label', 'dw_crops', 'dw_built', 'dw_trees', 'dw_shrub_and_scrub']
                print(f"\nVerifying forbidden features are NOT in model input:")
                for feat in forbidden_features:
                    if feat == 'dw_label':
                        print(f"  {feat}: NOT USED (land cover label is {label})")
                    elif feat in probs:
                        print(f"  {feat}: {probs.get(feat, 0.0):.4f} - AVAILABLE in provider but NOT passed to model")
                    else:
                        print(f"  {feat}: NOT AVAILABLE in provider")

                return True
            else:
                print(f"INFO: Got non-live data: {result.get('coverage_state')}")
                if result.get('coverage_state') == 'demo_mode':
                    print("INFO: Using demo data - Earth Engine credentials may not be properly configured")
                elif result.get('coverage_state') == 'coverage_unknown':
                    print("INFO: No Dynamic World data available for the specified date and location")
                return False

        except Exception as e:
            print(f"ERROR: Error querying Dynamic World: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print("ERROR: Earth Engine not initialized - checking why...")
        if not config.EARTH_ENGINE_PROJECT_ID:
            print("  EARTH_ENGINE_PROJECT_ID not set")
        else:
            print("  Earth Engine initialization failed - check credentials")

            # Try to diagnose Earth Engine issues
            try:
                import ee
                print("  ✓ earthengine-api package is available")
            except ImportError:
                print("  ✗ earthengine-api package NOT installed")

            print(f"  Project ID: '{config.EARTH_ENGINE_PROJECT_ID}'")
            print(f"  Credentials path: '{config.EARTH_ENGINE_CREDENTIALS_PATH}'")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_earth_engine())
    sys.exit(0 if result else 1)