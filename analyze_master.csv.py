import pandas as pd
import numpy as np
import sys
import os

csv_path = os.path.join(os.path.dirname(__file__), 'docs', 'FireGuard_MASTER.csv')
print(f"Analyzing {csv_path}...")
print("="*60)

# We'll load the CSV in chunks to avoid memory issues, but for simplicity and given the size (313MB) we can try to load it.
# However, to be safe, we'll use chunking for iterative stats and only load a sample for some operations.

# First, let's get the number of rows and columns by reading the header and then counting lines.
import csv
with open(csv_path, 'r') as f:
    reader = csv.reader(f)
    header = next(reader)
    num_columns = len(header)
    # Count rows by iterating
    row_count = sum(1 for row in reader)  # This excludes header

print(f"Rows: {row_count}")
print(f"Columns: {num_columns}")
print()

print("Column list:")
for i, col in enumerate(header):
    print(f"  {i:2d}: {col}")
print()

# Now we'll load the data in chunks to compute statistics.
chunk_size = 100000  # 100k rows per chunk

# Initialize accumulators
missing_counts = {col: 0 for col in header}
# For numeric columns, we'll compute min, max, sum, count for mean
numeric_cols = {}
# For categorical columns, we'll collect unique values (limited to top 20 to avoid memory explosion)
categorical_cols = {col: set() for col in header}
# We'll also track unique values for a few specific columns of interest
specific_columns = ['fire_id', 'latitude', 'longitude', 'satellite', 'instrument', 'nearest_facility_category', 'dw_label', 'daynight', 'snpp_anomaly_flag']
specific_values = {col: set() for col in specific_columns if col in header}
# For date range, we'll parse acq_datetime if available
date_min = None
date_max = None
# For duplicate fire_id, we'll keep a set of seen fire_id and count duplicates
seen_fire_ids = set()
duplicate_fire_id_count = 0
# For duplicate rows, we'll hash a tuple of selected columns? Too heavy. We'll skip exact duplicate rows for now and note we can't compute without loading all.
# Instead, we'll note that we cannot compute exact duplicates without loading all data into memory or using external tools.

# We'll also compute bounds for latitude and longitude
lat_min = float('inf')
lat_max = float('-inf')
lon_min = float('inf')
lon_max = float('-inf')

# Process in chunks
chunk_iter = pd.read_csv(csv_path, chunksize=chunk_size)
for i, chunk in enumerate(chunk_iter):
    # Update missing counts
    for col in header:
        missing_counts[col] += chunk[col].isnull().sum()
    # For numeric columns, update min, max, sum, count
    for col in header:
        if pd.api.types.is_numeric_dtype(chunk[col]):
            if col not in numeric_cols:
                numeric_cols[col] = {'min': float('inf'), 'max': float('-inf'), 'sum': 0.0, 'count': 0}
            # Update min and max
            col_min = chunk[col].min()
            col_max = chunk[col].max()
            if col_min < numeric_cols[col]['min']:
                numeric_cols[col]['min'] = col_min
            if col_max > numeric_cols[col]['max']:
                numeric_cols[col]['max'] = col_max
            # Update sum and count (ignoring NaN)
            non_null = chunk[col].dropna()
            numeric_cols[col]['sum'] += non_null.sum()
            numeric_cols[col]['count'] += len(non_null)
    # For categorical columns, update unique values (limited)
    for col in header:
        if not pd.api.types.is_numeric_dtype(chunk[col]):
            # Get unique values in this chunk, but limit to avoid memory issues
            vals = chunk[col].dropna().unique()
            for v in vals:
                # Convert to string for uniformity in set
                s = str(v)
                categorical_cols[col].add(s)
                # If the set gets too large, we stop adding (but we still want to know it's large)
                if len(categorical_cols[col]) > 1000:
                    # We'll just note that it's large and break? Actually, we want to keep counting unique but limit memory.
                    # We'll change strategy: we'll only keep track of unique counts by using a HyperLogLog approximation? Too complex.
                    # For simplicity, we'll break and note that we cannot compute exact unique counts for large columns.
                    # We'll change the approach: we'll only compute unique counts for a few specific columns.
                    pass
    # For specific columns, we'll keep track of unique values (without limit for now, but we'll break if too large)
    for col in specific_columns:
        if col in header:
            vals = chunk[col].dropna().unique()
            for v in vals:
                s = str(v)
                specific_values[col].add(s)
                if len(specific_values[col]) > 1000:
                    # Too many, we'll note and break? We'll just keep going but risk memory.
                    pass
    # For date range, if acq_datetime exists
    if 'acq_datetime' in chunk.columns:
        # Convert to datetime, errors='coerce' will turn invalid to NaT
        try:
            chunk['acq_datetime_parsed'] = pd.to_datetime(chunk['acq_datetime'], errors='coerce')
            # Update min and max
            chunk_min = chunk['acq_datetime_parsed'].min()
            chunk_max = chunk['acq_datetime_parsed'].max()
            if pd.notna(chunk_min):
                if date_min is None or chunk_min < date_min:
                    date_min = chunk_min
            if pd.notna(chunk_max):
                if date_max is None or chunk_max > date_max:
                    date_max = chunk_max
        except Exception:
            pass
    # For latitude and longitude bounds
    if 'latitude' in chunk.columns:
        lat_min = min(lat_min, chunk['latitude'].min())
        lat_max = max(lat_max, chunk['latitude'].max())
    if 'longitude' in chunk.columns:
        lon_min = min(lon_min, chunk['longitude'].min())
        lon_max = max(lon_max, chunk['longitude'].max())
    # For duplicate fire_id
    if 'fire_id' in chunk.columns:
        for fid in chunk['fire_id'].dropna():
            if fid in seen_fire_ids:
                duplicate_fire_id_count += 1
            else:
                seen_fire_ids.add(fid)
    # Progress
    if (i+1) % 10 == 0:
        print(f"Processed { (i+1)*chunk_size } rows...")

print("="*60)
print("FINAL STATISTICS")
print("="*60)
print(f"Total rows processed: { (i+1)*chunk_size }")  # This is approximate because last chunk may be partial
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
for col in numeric_cols:
    if numeric_cols[col]['count'] > 0:
        mean = numeric_cols[col]['sum'] / numeric_cols[col]['count']
        print(f"  {col}: min={numeric_cols[col]['min']:.4f}, max={numeric_cols[col]['max']:.4f}, mean={mean:.4f}, count={numeric_cols[col]['count']}")
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
print("Geographic extent:")
print(f"  Latitude: {lat_min:.4f} to {lat_max:.4f}")
print(f"  Longitude: {lon_min:.4f} to {lon_max:.4f}")
print()
print("Duplicate fire_id count:")
print(f"  Duplicate fire_id (based on chunk processing): {duplicate_fire_id_count}")
print(f"  Unique fire_id seen: {len(seen_fire_ids)}")
print()
print("Unique values for specific columns (showing up to 20):")
for col in specific_columns:
    if col in header:
        vals = list(specific_values[col])
        print(f"  {col}: {len(vals)} unique values")
        if len(vals) > 0:
            print(f"    First 20: {vals[:20]}")
print()
print("Note: For exact duplicate rows and exact unique counts for all columns, a full load or external tool is required.")
print("This chunked approach provides approximate statistics.")

# Write summary to file
output_path = os.path.join(os.path.dirname(__file__), 'docs', 'master_dataset_summary.txt')
with open(output_path, 'w') as f:
    f.write(f"Rows: {row_count}\n")
    f.write(f"Columns: {num_columns}\n")
    f.write(f"Columns list: {', '.join(header)}\n")
    f.write("\nMissing values:\n")
    f.write(missing_df.to_string(index=False))
    f.write("\n\nNumeric columns statistics:\n")
    for col in numeric_cols:
        if numeric_cols[col]['count'] > 0:
            mean = numeric_cols[col]['sum'] / numeric_cols[col]['count']
            f.write(f"  {col}: min={numeric_cols[col]['min']:.4f}, max={numeric_cols[col]['max']:.4f}, mean={mean:.4f}, count={numeric_cols[col]['count']}\n")
        else:
            f.write(f"  {col}: all NaN\n")
    f.write(f"\nDate range (acq_datetime): {date_min} to {date_max}\n")
    f.write(f"\nGeographic extent:\n")
    f.write(f"  Latitude: {lat_min:.4f} to {lat_max:.4f}\n")
    f.write(f"  Longitude: {lon_min:.4f} to {lon_max:.4f}\n")
    f.write(f"\nDuplicate fire_id: {duplicate_fire_id_count}\n")
    f.write(f"Unique fire_id seen: {len(seen_fire_ids)}\n")
    f.write("\nUnique values for specific columns:\n")
    for col in specific_columns:
        if col in header:
            vals = list(specific_values[col])
            f.write(f"  {col}: {len(vals)} unique values\n")
            if len(vals) > 0:
                f.write(f"    First 20: {vals[:20]}\n")
print(f"Summary written to {output_path}")