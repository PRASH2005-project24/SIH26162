import pandas as pd
import numpy as np
from datetime import datetime

# Read the CSV file
print("Reading CSV...")
df = pd.read_csv(r"C:\ProjectX\SIH26162\docs\FireGuard_MASTER.csv")
print(f"Shape: {df.shape}")

# Basic info
print("\n=== BASIC INFO ===")
print(f"Number of rows: {len(df)}")
print(f"Number of columns: {len(df.columns)}")
print(f"Columns: {list(df.columns)}")

# Data types
print("\n=== DATA TYPES ===")
print(df.dtypes)

# Missing values
print("\n=== MISSING VALUES (count and percentage) ===")
missing = df.isnull().sum()
missing_pct = (missing / len(df)) * 100
missing_df = pd.DataFrame({'missing_count': missing, 'missing_percentage': missing_pct})
print(missing_df[missing_df['missing_count'] > 0].sort_values('missing_percentage', ascending=False))

# Unique values for categorical columns (object and maybe integer with few unique)
print("\n=== UNIQUE VALUE COUNTS (for columns with < 50 unique values) ===")
for col in df.columns:
    if df[col].dtype == 'object' or (df[col].dtype == 'int64' and df[col].nunique() < 50):
        uniq = df[col].nunique()
        if uniq < 50:
            print(f"{col}: {uniq} unique values")
            # Show top 5 values
            top_vals = df[col].value_counts().head(5)
            print(f"  Top 5: {top_vals.to_dict()}")

# Date range for acq_datetime
if 'acq_datetime' in df.columns:
    print("\n=== DATE RANGE (acq_datetime) ===")
    df['acq_datetime'] = pd.to_datetime(df['acq_datetime'], errors='coerce')
    min_date = df['acq_datetime'].min()
    max_date = df['acq_datetime'].max()
    print(f"Min: {min_date}")
    print(f"Max: {max_date}")
    print(f"Range: {max_date - min_date}")

# Geographic extent
if 'latitude' in df.columns and 'longitude' in df.columns:
    print("\n=== GEOGRAPHIC EXTENT ===")
    print(f"Latitude: min={df['latitude'].min()}, max={df['latitude'].max()}")
    print(f"Longitude: min={df['longitude'].min()}, max={df['longitude'].max()}")

# Duplicate fire_id
if 'fire_id' in df.columns:
    print("\n=== DUPLICATE fire_id ===")
    duplicate_fire_id = df['fire_id'].duplicated().sum()
    print(f"Duplicate fire_id count: {duplicate_fire_id}")
    if duplicate_fire_id > 0:
        print("Example duplicate fire_ids:")
        print(df[df['fire_id'].duplicated(keep=False)]['fire_id'].head())

# Duplicate coordinate/time combinations (latitude, longitude, acq_datetime)
print("\n=== DUPLICATE COORDINATE/TIME COMBINATIONS ===")
coord_time_dup = df.duplicated(subset=['latitude', 'longitude', 'acq_datetime'], keep=False).sum()
print(f"Rows with duplicate (lat, lon, acq_datetime): {coord_time_dup}")

# Duplicate rows (all columns)
print("\n=== DUPLICATE ROWS ===")
full_duplicate = df.duplicated().sum()
print(f"Fully duplicate rows: {full_duplicate}")

# FIRMS source/satellite distribution
if 'source_satellite' in df.columns:
    print("\n=== FIRMS source_satellite DISTRIBUTION ===")
    print(df['source_satellite'].value_counts())

if 'satellite' in df.columns:
    print("\n=== FIRMS satellite DISTRIBUTION ===")
    print(df['satellite'].value_counts())

# OSM facility-category distribution
if 'nearest_facility_category' in df.columns:
    print("\n=== NEAREST FACILITY CATEGORY DISTRIBUTION ===")
    # Fill NaN with 'None' for counting
    cat_series = df['nearest_facility_category'].fillna('None')
    print(cat_series.value_counts().head(20))

# Dynamic World label distribution
if 'dw_label' in df.columns:
    print("\n=== DYNAMIC WORLD dw_label DISTRIBUTION ===")
    print(df['dw_label'].value_counts())

# snpp_anomaly_flag distribution
if 'snpp_anomaly_flag' in df.columns:
    print("\n=== SNPP ANOMALY FLAG DISTRIBUTION ===")
    print(df['snpp_anomaly_flag'].value_counts(dropna=False))

# Confidence distribution
if 'confidence' in df.columns:
    print("\n=== CONFIDENCE DISTRIBUTION ===")
    print(df['confidence'].value_counts())

# FRP statistics
if 'frp' in df.columns:
    print("\n=== FRP STATISTICS ===")
    print(df['frp'].describe())

print("\n=== DONE ===")