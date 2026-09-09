"""
Test script to verify the fixed weak label generation on a small subset
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

print("Testing fixed weak label generation on subset...")

# Load a small sample for testing
df = pd.read_csv(r"C:\ProjectX\SIH26162\docs\FireGuard_MASTER.csv", nrows=5000)
print(f"Loaded {len(df)} rows for testing")

# Convert acq_datetime to datetime
df['acq_datetime'] = pd.to_datetime(df['acq_datetime'])

# Sort by acquisition time to ensure temporal ordering
df = df.sort_values('acq_datetime').reset_index(drop=True)

print("Computing temporally correct persistence features...")

# Group by latitude, longitude to process each location separately
grouped = df.groupby(['latitude', 'longitude'])

# Initialize arrays for persistence features
persistence_date_count = np.zeros(len(df), dtype=int)
time_span_days = np.zeros(len(df), dtype=int)

# Process each location group
processed_rows = 0
for (lat, lon), group in grouped:
    group_indices = group.index.values
    group_size = len(group_indices)

    if group_size == 0:
        continue

    # Get the acquisition times for this group, already sorted due to overall sort
    times = group['acq_datetime'].values

    # For each observation in the group, compute features using only historical data
    for i in range(group_size):
        idx = group_indices[i]
        current_time = times[i]

        # Historical observations are those with index <= i (since sorted by time)
        historical_times = times[:i+1]

        if len(historical_times) > 0:
            # persistence_date_count: number of unique dates (date part)
            unique_dates = np.unique(historical_times.astype('datetime64[D]'))
            persistence_date_count[idx] = len(unique_dates)

            # time_span_days: (max_date - min_date).days
            if len(historical_times) > 1:
                time_span_days[idx] = (historical_times.max() - historical_times.min()).astype('timedelta64[D]').astype(int)
            else:
                time_span_days[idx] = 0
        else:
            # First observation at this location - all zero
            persistence_date_count[idx] = 0
            time_span_days[idx] = 0

    processed_rows += group_size

print(f"Processed {processed_rows} rows")

# Add persistence columns to dataframe
df['persistence_date_count'] = persistence_date_count
df['time_span_days'] = time_span_days

print("Results:")
print(f"  persistence_date_count - mean: {df['persistence_date_count'].mean():.2f}, max: {df['persistence_date_count'].max()}")
print(f"  time_span_days - mean: {df['time_span_days'].mean():.2f}, max: {df['time_span_days'].max()}")

# Verify temporal correctness: check that no future data influenced the calculation
print("\nVerifying temporal correctness...")
import random
leakage_found = False
for _ in range(min(100, len(df))):
    idx = random.randint(0, len(df)-1)
    row = df.iloc[idx]
    current_time = row['acq_datetime']
    current_lat = row['latitude']
    current_lon = row['longitude']

    # Get all data for this location
    location_df = df[(df['latitude'] == current_lat) & (df['longitude'] == current_lon)]

    # Get historical data (what should have been used)
    historical_df = location_df[location_df['acq_datetime'] <= current_time]

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
        print(f"  TEMPORAL LEAKAGE DETECTED at row {idx}!")
        print(f"    Event time: {current_time}")
        print(f"    Expected persistence_date_count: {expected_persistence_date_count}, got: {actual_persistence_date_count}")
        print(f"    Expected time_span_days: {expected_time_span_days}, got: {actual_time_span_days}")
        leakage_found = True
        break

if not leakage_found:
    print("  [PASS] No temporal leakage detected in subset test")
else:
    print("  [FAIL] TEMPORAL LEAKAGE CONFIRMED")

# Save the test output
output_path = r"C:\ProjectX\SIH26162\docs\FireGuard_WEAKLABELS_TEST_FIXED.csv"
print(f"\nSaving test weak labels to {output_path}...")

# Add the target class computation (simplified for test)
df['target_class'] = 'unknown'  # Simplified for test

# Save with minimal columns for testing
test_output = df[['fire_id', 'acq_datetime', 'latitude', 'longitude', 'persistence_date_count', 'time_span_days', 'target_class']]
test_output.to_csv(output_path, index=False)

print("Test complete.")