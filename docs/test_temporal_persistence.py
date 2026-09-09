"""
Test script to verify temporal persistence calculation approach
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("Testing temporal persistence calculation...")

# Load a small sample for testing
df = pd.read_csv(r"C:\ProjectX\SIH26162\docs\FireGuard_MASTER.csv", nrows=1000)
print(f"Loaded {len(df)} rows for testing")

# Convert acq_datetime to datetime
df['acq_datetime'] = pd.to_datetime(df['acq_datetime'])

# Sort by acquisition time to ensure temporal ordering
df = df.sort_values('acq_datetime').reset_index(drop=True)

print("Testing temporally correct persistence features with sample data...")

# Initialize persistence columns
persistence_date_count = np.zeros(len(df), dtype=int)
time_span_days = np.zeros(len(df), dtype=int)

# For each event, compute persistence features using only historical data
for i, row in df.iterrows():
    if i % 100 == 0:
        print(f"  Processing event {i}/{len(df)}")

    current_time = row['acq_datetime']
    current_lat = row['latitude']
    current_lon = row['longitude']

    # Filter to historical observations at the same location (exact lat/lon match)
    historical_mask = (
        (df['latitude'] == current_lat) &
        (df['longitude'] == current_lon) &
        (df['acq_datetime'] <= current_time)
    )

    historical_df = df[historical_mask]

    if len(historical_df) > 0:
        # persistence_date_count: number of unique dates (date part) at each location
        persistence_date_count[i] = historical_df['acq_datetime'].dt.date.nunique()

        # time_span_days: (max_date - min_date).days at each location
        if len(historical_df) > 1:
            time_span_days[i] = (historical_df['acq_datetime'].max() - historical_df['acq_datetime'].min()).days
        else:
            time_span_days[i] = 0
    else:
        # No historical data - all zero
        persistence_date_count[i] = 0
        time_span_days[i] = 0

# Add persistence columns to dataframe
df['persistence_date_count'] = persistence_date_count
df['time_span_days'] = time_span_days

print("Results:")
print(f"  persistence_date_count - mean: {df['persistence_date_count'].mean():.2f}, max: {df['persistence_date_count'].max()}")
print(f"  time_span_days - mean: {df['time_span_days'].mean():.2f}, max: {df['time_span_days'].max()}")

# Verify temporal correctness: for a few random rows, check that no future data influenced the calculation
print("\nVerifying temporal correctness...")
import random
for _ in range(5):
    idx = random.randint(0, len(df)-1)
    row = df.iloc[idx]
    current_time = row['acq_datetime']
    current_lat = row['latitude']
    current_lon = row['longitude']

    # Get all data for this location
    location_df = df[(df['latitude'] == current_lat) & (df['longitude'] == current_lon)]

    # Get historical data (what should have been used)
    historical_df = location_df[location_df['acq_datetime'] <= current_time]

    # Get future data (what should NOT have been used)
    future_df = location_df[location_df['acq_datetime'] > current_time]

    # Calculate what the persistence features SHOULD be (historical only)
    if len(historical_df) > 0:
        expected_persistence_date_count = historical_df['acq_datetime'].dt.date.nunique()
        expected_time_span_days = (historical_df['acq_datetime'].max() - historical_df['acq_datetime'].min()).days if len(historical_df) > 1 else 0
    else:
        expected_persistence_date_count = 0
        expected_time_span_days = 0

    actual_persistence_date_count = row['persistence_date_count']
    actual_time_span_days = row['time_span_days']

    # Check if they match
    if expected_persistence_date_count != actual_persistence_date_count or expected_time_span_days != actual_time_span_days:
        print(f"  ERROR: Row {idx} has temporal leakage!")
        print(f"    Event time: {current_time}")
        print(f"    Expected persistence_date_count: {expected_persistence_date_count}, got: {actual_persistence_date_count}")
        print(f"    Expected time_span_days: {expected_time_span_days}, got: {actual_time_span_days}")
        print(f"    Historical rows: {len(historical_df)}, Future rows: {len(future_df)}")
        if len(future_df) > 0:
            print(f"    Future dates present: {future_df['acq_datetime'].dt.date.unique()}")
    else:
        print(f"  Row {idx}: OK - no temporal leakage detected")

print("\nTest complete.")