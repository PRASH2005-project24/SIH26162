#!/usr/bin/env python3
import os
from dotenv import load_dotenv

# Load .env file explicitly
env_path = 'C:/ProjectX/SIH26162/.env'
print(f"Loading .env from: {env_path}")
print(f"File exists: {os.path.exists(env_path)}")

load_dotenv(env_path)

print("Environment variables after load_dotenv:")
print(f"EARTH_ENGINE_PROJECT_ID: '{os.getenv('EARTH_ENGINE_PROJECT_ID')}'")
print(f"DEMO_MODE: '{os.getenv('DEMO_MODE')}'")

# Check if we can read the file directly
with open(env_path, 'r') as f:
    content = f.read()
    print("\n.env file content:")
    for line in content.split('\n'):
        if 'EARTH_ENGINE' in line or 'DEMO_MODE' in line:
            print(f"  {line}")