#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# Load .env file explicitly
load_dotenv('C:/ProjectX/SIH26162/.env')

print("Environment variables:")
print(f"EARTH_ENGINE_PROJECT_ID: '{os.getenv('EARTH_ENGINE_PROJECT_ID')}'")
print(f"DEMO_MODE: {os.getenv('DEMO_MODE')}")

# Now test importing the config
import sys
sys.path.insert(0, 'C:/ProjectX/SIH26162/backend')
from backend.config import Config

config = Config()
print(f"\nConfig EARTH_ENGINE_PROJECT_ID: '{config.EARTH_ENGINE_PROJECT_ID}'")
print(f"Config DEMO_MODE: {config.DEMO_MODE}")