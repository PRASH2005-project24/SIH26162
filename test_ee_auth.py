#!/usr/bin/env python3
"""
Test Earth Engine authentication only
"""

import sys
import os

# Load .env file FIRST before importing any modules that might read env vars
from dotenv import load_dotenv
env_path = 'C:/ProjectX/SIH26162/.env'
print(f"Loading .env from: {env_path}")
load_dotenv(env_path, override=True)  # override=True ensures we get the .env values

# Now we can import backend modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.config import Config
import ee

def test_ee_auth():
    print("=== Testing Earth Engine Authentication ===")

    # Load config (now should have correct values from .env)
    config = Config()
    print(f"EARTH_ENGINE_PROJECT_ID: '{config.EARTH_ENGINE_PROJECT_ID}'")
    print(f"DEMO_MODE: {config.DEMO_MODE}")

    if not config.EARTH_ENGINE_PROJECT_ID:
        print("ERROR: EARTH_ENGINE_PROJECT_ID not set")
        return False

    try:
        # Try to initialize Earth Engine
        print("Initializing Earth Engine...")
        ee.Initialize(
            opt_url="https://earthengine-highvolume.googleapis.com",
            project=config.EARTH_ENGINE_PROJECT_ID
        )
        print("SUCCESS: Earth Engine initialized successfully!")

        # Test a simple operation
        print("Testing simple EE operation...")
        point = ee.Geometry.Point([73.8567, 18.5204])  # Pune
        print(f"Created point: {point.getInfo()}")

        return True

    except Exception as e:
        print(f"ERROR: Failed to initialize Earth Engine: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = test_ee_auth()
    sys.exit(0 if result else 1)