import pandas as pd
import numpy as np
import sys
import os
from collections import defaultdict, Counter

csv_path = os.path.join(os.path.dirname(__file__), 'docs', 'FireGuard_MASTER.csv')
print(f"Analyzing {csv_path} for label feasibility...")
print("="*60)

# We'll process in chunks for memory efficiency
chunk_size = 50000  # Adjust based on memory

# We'll initialize accumulators as None, and set them on the first chunk
header = None
missing_counts = None
numeric_stats = None  # dict of dicts
categorical_unique = None
categorical_counter = None
# For persistence
persistence_data = {}  # key: (lat_rounded, lon_rounded)
# For date range
date_min = None
date_max = None
# For duplicate fire_id
seen_fire_ids = set()
duplicate_fire_id_count = 0
# For duplicate spatiotemporal (lat, lon, time to minute)
seen_spatiotemporal = set()
duplicate_spatiotemporal_count = 0
# Row count
row_count = 0

# Columns of interest for label feasibility
categorical_cols_to_track = ['nearest_facility_category', 'dw_label', 'daynight', 'snpp_anomaly_flag', 'satellite', 'instrument']

try:
    chunk_iter = pd.read_csv(csv_path, chunksize=chunk_size, encoding='utf-8-sig')
    for i, chunk in enumerate(chunk_iter):
        if header is None:
            header = chunk.columns.tolist()
            num_columns = len(header)
            print(f"Rows: {row_count} (will update after processing)")
            print(f"Columns: {num_columns}")
            print()
            print("Column list:")
            for i, col in enumerate(header):
                print(f"  {i:2d}: {col}")
            print()
            # Initialize accumulators
            missing_counts = {col: 0 for col in header}
            numeric_stats = {col: {'min': float('inf'), 'max': float('-inf'), 'sum': 0.0, 'count': 0} for col in header}
            categorical_unique = {col: set() for col in categorical_cols_to_track if col in header}
            categorical_counter = {col: defaultdict(int) for col in categorical_cols_to_track if col in header}

        row_count += len(chunk)
        # Update missing counts
        for col in header:
            missing_counts[col] += chunk[col].isnull().sum()

        # For numeric columns, update min, max, sum, count
        for col in header:
            if pd.api.types.is_numeric_dtype(chunk[col]):
                col_min = chunk[col].min()
                col_max = chunk[col].max()
                if col_min < numeric_stats[col]['min']:
                    numeric_stats[col]['min'] = col_min
                if col_max > numeric_stats[col]['max']:
                    numeric_stats[col]['max'] = col_max
                non_null = chunk[col].dropna()
                numeric_stats[col]['sum'] += non_null.sum()
                numeric_stats[col]['count'] += len(non_null)

        # For specific categorical columns, update unique values and counters
        for col in categorical_cols_to_track:
            if col in chunk.columns:
                # Get non-null values
                vals = chunk[col].dropna()
                for v in vals:
                    s = str(v)
                    categorical_unique[col].add(s)
                    categorical_counter[col][s] += 1
                    # Limit the unique set to avoid memory issues (if it gets too large, we stop adding new ones but keep counting)
                    if len(categorical_unique[col]) > 1000:
                        # We'll still count frequencies but not add to the unique set
                        pass

        # For persistence: round lat/lon to 3 decimal places (approx 100m)
        if 'latitude' in chunk.columns and 'longitude' in chunk.columns:
            # Round to 3 decimal places
            chunk['lat_rounded'] = chunk['latitude'].round(3)
            chunk['lon_rounded'] = chunk['longitude'].round(3)

            # Parse acq_datetime if available
            if 'acq_datetime' in chunk.columns:
                try:
                    chunk['acq_datetime_parsed'] = pd.to_datetime(chunk['acq_datetime'], errors='coerce')
                    # Round to nearest minute for deduplication
                    chunk['acq_datetime_rounded'] = chunk['acq_datetime_parsed'].dt.floor('min')
                except Exception:
                    chunk['acq_datetime_parsed'] = pd.NaT
                    chunk['acq_datetime_rounded'] = pd.NaT
            else:
                chunk['acq_datetime_parsed'] = pd.NaT
                chunk['acq_datetime_rounded'] = pd.NaT

            # Update persistence data and check for duplicates
            for idx, row in chunk.iterrows():
                lat_r = row['lat_rounded']
                lon_r = row['lon_rounded']
                # Skip if lat/lon is NaN
                if pd.isna(lat_r) or pd.isna(lon_r):
                    continue
                location_key = (lat_r, lon_r)

                # Update persistence data for this location
                if location_key not in persistence_data:
                    persistence_data[location_key] = {
                        'count': 0,
                        'min_time': None,
                        'max_time': None,
                        'frp_sum': 0.0,
                        'frp_count': 0
                    }

                pers = persistence_data[location_key]
                pers['count'] += 1

                # Update time range
                if not pd.isna(row['acq_datetime_parsed']):
                    dt = row['acq_datetime_parsed']
                    if pers['min_time'] is None or dt < pers['min_time']:
                        pers['min_time'] = dt
                    if pers['max_time'] is None or dt > pers['max_time']:
                        pers['max_time'] = dt

                # Update FRP stats
                if not pd.isna(row['frp']):
                    pers['frp_sum'] += row['frp']
                    pers['frp_count'] += 1

                # Check for duplicate spatiotemporal point (same location and same rounded time)
                if not pd.isna(row['acq_datetime_rounded']):
                    time_key = row['acq_datetime_rounded']
                    st_key = (lat_r, lon_r, time_key)
                    if st_key in seen_spatiotemporal:
                        duplicate_spatiotemporal_count += 1
                    else:
                        seen_spatiotemporal.add(st_key)

        # For duplicate fire_id
        if 'fire_id' in chunk.columns:
            for fid in chunk['fire_id'].dropna():
                if fid in seen_fire_ids:
                    duplicate_fire_id_count += 1
                else:
                    seen_fire_ids.add(fid)

        # For date range (using acq_datetime_parsed)
        if 'acq_datetime_parsed' in chunk.columns:
            chunk_min = chunk['acq_datetime_parsed'].min()
            chunk_max = chunk['acq_datetime_parsed'].max()
            if pd.notna(chunk_min):
                if date_min is None or chunk_min < date_min:
                    date_min = chunk_min
            if pd.notna(chunk_max):
                if date_max is None or chunk_max > date_max:
                    date_max = chunk_max

        # Progress
        if (i+1) % 10 == 0:
            print(f"Processed { (i+1)*chunk_size } rows...")

except UnicodeDecodeError:
    print("UTF-8-SIG failed, trying latin1...")
    # Fallback to latin1
    chunk_iter = pd.read_csv(csv_path, chunksize=chunk_size, encoding='latin1')
    for i, chunk in enumerate(chunk_iter):
        if header is None:
            header = chunk.columns.tolist()
            num_columns = len(header)
            print(f"Rows: {row_count} (will update after processing)")
            print(f"Columns: {num_columns}")
            print()
            print("Column list:")
            for i, col in enumerate(header):
                print(f"  {i:2d}: {col}")
            print()
            # Initialize accumulators
            missing_counts = {col: 0 for col in header}
            numeric_stats = {col: {'min': float('inf'), 'max': float('-inf'), 'sum': 0.0, 'count': 0} for col in header}
            categorical_unique = {col: set() for col in categorical_cols_to_track if col in header}
            categorical_counter = {col: defaultdict(int) for col in categorical_cols_to_track if col in header}

        row_count += len(chunk)
        # Update missing counts
        for col in header:
            missing_counts[col] += chunk[col].isnull().sum()

        # For numeric columns, update min, max, sum, count
        for col in header:
            if pd.api.types.is_numeric_dtype(chunk[col]):
                col_min = chunk[col].min()
                col_max = chunk[col].max()
                if col_min < numeric_stats[col]['min']:
                    numeric_stats[col]['min'] = col_min
                if col_max > numeric_stats[col]['max']:
                    numeric_stats[col]['max'] = col_max
                non_null = chunk[col].dropna()
                numeric_stats[col]['sum'] += non_null.sum()
                numeric_stats[col]['count'] += len(non_null)

        # For specific categorical columns, update unique values and counters
        for col in categorical_cols_to_track:
            if col in chunk.columns:
                # Get non-null values
                vals = chunk[col].dropna()
                for v in vals:
                    s = str(v)
                    categorical_unique[col].add(s)
                    categorical_counter[col][s] += 1
                    # Limit the unique set to avoid memory issues (if it gets too large, we stop adding new ones but keep counting)
                    if len(categorical_unique[col]) > 1000:
                        # We'll still count frequencies but not add to the unique set
                        pass

        # For persistence: round lat/lon to 3 decimal places (approx 100m)
        if 'latitude' in chunk.columns and 'longitude' in chunk.columns:
            # Round to 3 decimal places
            chunk['lat_rounded'] = chunk['latitude'].round(3)
            chunk['lon_rounded'] = chunk['longitude'].round(3)

            # Parse acq_datetime if available
            if 'acq_datetime' in chunk.columns:
                try:
                    chunk['acq_datetime_parsed'] = pd.to_datetime(chunk['acq_datetime'], errors='coerce')
                    # Round to nearest minute for deduplication
                    chunk['acq_datetime_rounded'] = chunk['acq_datetime_parsed'].dt.floor('min')
                except Exception:
                    chunk['acq_datetime_parsed'] = pd.NaT
                    chunk['acq_datetime_rounded'] = pd.NaT
            else:
                chunk['acq_datetime_parsed'] = pd.NaT
                chunk['acq_datetime_rounded'] = pd.NaT

            # Update persistence data and check for duplicates
            for idx, row in chunk.iterrows():
                lat_r = row['lat_rounded']
                lon_r = row['lon_rounded']
                # Skip if lat/lon is NaN
                if pd.isna(lat_r) or pd.isna(lon_r):
                    continue
                location_key = (lat_r, lon_r)

                # Update persistence data for this location
                if location_key not in persistence_data:
                    persistence_data[location_key] = {
                        'count': 0,
                        'min_time': None,
                        'max_time': None,
                        'frp_sum': 0.0,
                        'frp_count': 0
                    }

                pers = persistence_data[location_key]
                pers['count'] += 1

                # Update time range
                if not pd.isna(row['acq_datetime_parsed']):
                    dt = row['acq_datetime_parsed']
                    if pers['min_time'] is None or dt < pers['min_time']:
                        pers['min_time'] = dt
                    if pers['max_time'] is None or dt > pers['max_time']:
                        pers['max_time'] = dt

                # Update FRP stats
                if not pd.isna(row['frp']):
                    pers['frp_sum'] += row['frp']
                    pers['frp_count'] += 1

                # Check for duplicate spatiotemporal point (same location and same rounded time)
                if not pd.isna(row['acq_datetime_rounded']):
                    time_key = row['acq_datetime_rounded']
                    st_key = (lat_r, lon_r, time_key)
                    if st_key in seen_spatiotemporal:
                        duplicate_spatiotemporal_count += 1
                    else:
                        seen_spatiotemporal.add(st_key)

        # For duplicate fire_id
        if 'fire_id' in chunk.columns:
            for fid in chunk['fire_id'].dropna():
                if fid in seen_fire_ids:
                    duplicate_fire_id_count += 1
                else:
                    seen_fire_ids.add(fid)

        # For date range (using acq_datetime_parsed)
        if 'acq_datetime_parsed' in chunk.columns:
            chunk_min = chunk['acq_datetime_parsed'].min()
            chunk_max = chunk['acq_datetime_parsed'].max()
            if pd.notna(chunk_min):
                if date_min is None or chunk_min < date_min:
                    date_min = chunk_min
            if pd.notna(chunk_max):
                if date_max is None or chunk_max > date_max:
                    date_max = chunk_max

        # Progress
        if (i+1) % 10 == 0:
            print(f"Processed { (i+1)*chunk_size } rows...")

print("="*60)
print("LABEL FEASIBILITY ANALYSIS RESULTS")
print("="*60)

print(f"Total rows processed: {row_count}")
print(f"Total columns: {num_columns}")
print()

print("Missing values (count and percentage):")
missing_data = []
for col in header:
    missing_data.append({
        'column': col,
        'missing_count': missing_counts[col],
        'missing_percent': (missing_counts[col] / row_count) * 100 if row_count > 0 else 0
    })
missing_df = pd.DataFrame(missing_data)
print(missing_df.sort_values('missing_count', ascending=False).to_string(index=False))
print()

print("Numeric columns statistics:")
for col in header:
    if numeric_stats[col]['count'] > 0:
        mean = numeric_stats[col]['sum'] / numeric_stats[col]['count']
        print(f"  {col}: min={numeric_stats[col]['min']:.4f}, max={numeric_stats[col]['max']:.4f}, mean={mean:.4f}, count={numeric_stats[col]['count']}")
    else:
        print(f"  {col}: all NaN")
print()

print("Date range (acq_datetime):")
if date_min is not None and date_max is not None:
    print(f"  Min: {date_min}")
    print(f"  Max: {date_max}")
else:
    print("  Could not determine date range.")
print()

print("Geographic extent (based on non-NaN latitude/longitude):")
# We need to compute lat/lon bounds from the numeric stats we collected
lat_min = numeric_stats['latitude']['min'] if 'latitude' in numeric_stats and numeric_stats['latitude']['count'] > 0 else float('inf')
lat_max = numeric_stats['latitude']['max'] if 'latitude' in numeric_stats and numeric_stats['latitude']['count'] > 0 else float('-inf')
lon_min = numeric_stats['longitude']['min'] if 'longitude' in numeric_stats and numeric_stats['longitude']['count'] > 0 else float('inf')
lon_max = numeric_stats['longitude']['max'] if 'longitude' in numeric_stats and numeric_stats['longitude']['count'] > 0 else float('-inf')
if lat_min != float('inf'):
    print(f"  Latitude: {lat_min:.4f} to {lat_max:.4f}")
    print(f"  Longitude: {lon_min:.4f} to {lon_max:.4f}")
else:
    print("  Could not determine geographic extent.")
print()

print("Duplicate fire_id count:")
print(f"  Duplicate fire_id (based on chunk processing): {duplicate_fire_id_count}")
print(f"  Unique fire_id seen: {len(seen_fire_ids)}")
print()

print("Duplicate spatiotemporal (lat,lon,time to minute) count:")
print(f"  Duplicate spatiotemporal points: {duplicate_spatiotemporal_count}")
print(f"  Unique spatiotemporal points seen: {len(seen_spatiotemporal)}")
print()

print("Unique values for specific categorical columns (showing top 5 and counts):")
for col in categorical_cols_to_track:
    if col in header:
        unique_count = len(categorical_unique[col])
        print(f"  {col}: {unique_count} unique values")
        if unique_count > 0:
            # Get top 5 most frequent values
            counter = categorical_counter[col]
            top5 = counter.most_common(5)
            print(f"    Top 5: {top5}")
        print()

print("Persistence analysis (grouped by lat/lon rounded to 3 decimal places ~100m):")
print(f"  Number of unique locations: {len(persistence_data)}")
if len(persistence_data) > 0:
    # Compute some stats on persistence
    location_counts = [data['count'] for data in persistence_data.values()]
    frp_means = []
    for key, data in persistence_data.items():
        if data['frp_count'] > 0:
            frp_means.append(data['frp_sum'] / data['frp_count'])

    print(f"  Observations per location: min={min(location_counts)}, max={max(location_counts)}, mean={np.mean(location_counts):.2f}")
    if frp_means:
        print(f"  Mean FRP per location: min={min(frp_means):.2f}, max={max(frp_means):.2f}, mean={np.mean(frp_means):.2f}")

    # Count locations with multiple observations
    multi_obs_locations = sum(1 for count in location_counts if count > 1)
    print(f"  Locations with >1 observation: {multi_obs_locations} ({multi_obs_locations/len(persistence_data)*100:.1f}%)")

    # Count locations with observations across multiple days
    multi_day_locations = 0
    for key, data in persistence_data.items():
        if data['min_time'] is not None and data['max_time'] is not None:
            delta = data['max_time'] - data['min_time']
            if delta.days > 0:
                multi_day_locations += 1
    print(f"  Locations with observations across multiple days: {multi_day_locations} ({multi_day_locations/len(persistence_data)*100:.1f}%)")

    # Show top 5 locations by observation count
    sorted_locations = sorted(persistence_data.items(), key=lambda x: x[1]['count'], reverse=True)
    print(f"  Top 5 locations by observation count:")
    for j, (loc, data) in enumerate(sorted_locations[:5]):
        print(f"    {j+1}. Lat={loc[0]}, Lon={loc[1]}: count={data['count']}, "
              f"time_range={data['min_time']} to {data['max_time']}, "
              f"mean_FRP={data['frp_sum']/data['frp_count'] if data['frp_count']>0 else 0:.2f}")
print()

print("Note: For exact duplicate rows and exact unique counts for all columns, a full load or external tool is required.")
print("This chunked approach provides approximate statistics for feasibility analysis.")

# Write summary to file
output_path = os.path.join(os.path.dirname(__file__), 'docs', 'label_feasibility_raw.txt')
with open(output_path, 'w') as f:
    f.write(f"Rows: {row_count}\n")
    f.write(f"Columns: {num_columns}\n")
    f.write(f"Columns list: {', '.join(header)}\n")
    f.write("\nMissing values:\n")
    f.write(missing_df.to_string(index=False))
    f.write("\n\nNumeric columns statistics:\n")
    for col in header:
        if numeric_stats[col]['count'] > 0:
            mean = numeric_stats[col]['sum'] / numeric_stats[col]['count']
            f.write(f"  {col}: min={numeric_stats[col]['min']:.4f}, max={numeric_stats[col]['max']:.4f}, mean={mean:.4f}, count={numeric_stats[col]['count']}\n")
        else:
            f.write(f"  {col}: all NaN\n")
    f.write(f"\nDate range (acq_datetime): {date_min} to {date_max}\n")
    f.write(f"\nGeographic extent:\n")
    f.write(f"  Latitude: {lat_min:.4f} to {lat_max:.4f}\n")
    f.write(f"  Longitude: {lon_min:.4f} to {lon_max:.4f}\n")
    f.write(f"\nDuplicate fire_id: {duplicate_fire_id_count}\n")
    f.write(f"Unique fire_id seen: {len(seen_fire_ids)}\n")
    f.write(f"\nDuplicate spatiotemporal (lat,lon,time to minute): {duplicate_spatiotemporal_count}\n")
    f.write(f"Unique spatiotemporal points seen: {len(seen_spatiotemporal)}\n")
    f.write("\nUnique values for specific categorical columns:\n")
    for col in categorical_cols_to_track:
        if col in header:
            vals = list(categorical_unique[col])
            f.write(f"  {col}: {len(vals)} unique values\n")
            if len(vals) > 0:
                f.write(f"    Top 5: {sorted(categorical_counter[col].items(), key=lambda x: x[1], reverse=True)[:5]}\n")
    f.write("\nPersistence analysis:\n")
    f.write(f"  Number of unique locations: {len(persistence_data)}\n")
    if len(persistence_data) > 0:
        location_counts = [data['count'] for data in persistence_data.values()]
        f.write(f"  Observations per location: min={min(location_counts)}, max={max(location_counts)}, mean={np.mean(location_counts):.2f}\n")
        multi_obs_locations = sum(1 for count in location_counts if count > 1)
        f.write(f"  Locations with >1 observation: {multi_obs_locations} ({multi_obs_locations/len(persistence_data)*100:.1f}%)\n")
        multi_day_locations = 0
        for key, data in persistence_data.items():
            if data['min_time'] is not None and data['max_time'] is not None:
                delta = data['max_time'] - data['min_time']
                if delta.days > 0:
                    multi_day_locations += 1
        f.write(f"  Locations with observations across multiple days: {multi_day_locations} ({multi_day_locations/len(persistence_data)*100:.1f}%)\n")
print(f"Raw summary written to {output_path}")