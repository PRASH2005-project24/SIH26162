"""
Final fixed version of weak label generation with temporally correct persistence features.
Processes data in chunks to avoid memory/timeout issues.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
from tqdm import tqdm

print("Loading master CSV...")
df = pd.read_csv(r"C:\ProjectX\SIH26162\docs\FireGuard_MASTER.csv")

print(f"Loaded {len(df)} rows")

# Convert acq_datetime to datetime
df['acq_datetime'] = pd.to_datetime(df['acq_datetime'])

# Sort by acquisition time to ensure temporal ordering
df = df.sort_values('acq_datetime').reset_index(drop=True)

print("Grouping by location for efficient processing...")

# Group by latitude, longitude to process each location separately
grouped = df.groupby(['latitude', 'longitude'])

# Initialize arrays for ALL persistence features mentioned in the requirements
persistence_date_count = np.zeros(len(df), dtype=int)
time_span_days = np.zeros(len(df), dtype=int)
detections_24h = np.zeros(len(df), dtype=int)
detections_3d = np.zeros(len(df), dtype=int)
detections_7d = np.zeros(len(df), dtype=int)
active_days = np.zeros(len(df), dtype=int)
persistence_duration_days = np.zeros(len(df), dtype=int)
mean_frp = np.zeros(len(df), dtype=float)
max_frp = np.zeros(len(df), dtype=float)

# Process each location group
print("Processing locations...")
processed_rows = 0
num_groups = len(grouped)

for group_idx, ((lat, lon), group) in enumerate(tqdm(grouped, desc="Processing locations")):
    group_indices = group.index.values
    group_size = len(group_indices)

    if group_size == 0:
        continue

    # Get the acquisition times and FRP values for this group, already sorted due to overall sort
    times = group['acq_datetime'].values
    frp_values = group['frp'].values

    # For each observation in the group, compute features using only historical data
    for i in range(group_size):
        idx = group_indices[i]
        current_time = times[i]

        # Historical observations are those with index <= i (since sorted by time)
        historical_times = times[:i+1]
        historical_frp = frp_values[:i+1]

        if len(historical_times) > 0:
            # persistence_date_count: number of unique dates (date part) at each location
            unique_dates = np.unique(historical_times.astype('datetime64[D]'))
            persistence_date_count[idx] = len(unique_dates)

            # time_span_days: (max_date - min_date).days at each location
            if len(historical_times) > 1:
                time_span_days[idx] = (historical_times.max() - historical_times.min()).astype('timedelta64[D]').astype(int)
            else:
                time_span_days[idx] = 0

            # detections_24h: number of detections in the last 24 hours
            time_24h_ago = current_time - timedelta(hours=24)
            detections_24h[idx] = np.sum((historical_times >= time_24h_ago) & (historical_times <= current_time))

            # detections_3d: number of detections in the last 3 days
            time_3d_ago = current_time - timedelta(days=3)
            detections_3d[idx] = np.sum((historical_times >= time_3d_ago) & (historical_times <= current_time))

            # detections_7d: number of detections in the last 7 days
            time_7d_ago = current_time - timedelta(days=7)
            detections_7d[idx] = np.sum((historical_times >= time_7d_ago) & (historical_times <= current_time))

            # active_days: number of unique dates with detections
            active_days[idx] = persistence_date_count[idx]  # Same definition for this use case

            # persistence_duration_days: (max_date - min_date).days
            persistence_duration_days[idx] = time_span_days[idx]  # Same as time_span_days

            # mean_frp: mean FRP of historical detections
            mean_frp[idx] = np.mean(historical_frp) if len(historical_frp) > 0 else 0.0

            # max_frp: maximum FRP of historical detections
            max_frp[idx] = np.max(historical_frp) if len(historical_frp) > 0 else 0.0
        else:
            # First observation at this location - all zero
            persistence_date_count[idx] = 0
            time_span_days[idx] = 0
            detections_24h[idx] = 0
            detections_3d[idx] = 0
            detections_7d[idx] = 0
            active_days[idx] = 0
            persistence_duration_days[idx] = 0
            mean_frp[idx] = 0.0
            max_frp[idx] = 0.0

    processed_rows += group_size

print(f"Processed {processed_rows} rows from {num_groups} location groups")

# Add persistence columns to dataframe
df['persistence_date_count'] = persistence_date_count
df['time_span_days'] = time_span_days
df['detections_24h'] = detections_24h
df['detections_3d'] = detections_3d
df['detections_7d'] = detections_7d
df['active_days'] = active_days
df['persistence_duration_days'] = persistence_duration_days
df['mean_frp'] = mean_frp
df['max_frp'] = max_frp

print("Computing labels with corrected persistence features...")

# Now compute labels (same as original logic)
# Industrial: facility_within_1km=1 AND nearest_facility_category in {fuel,power_plant,manufacturing} AND frp>2.0
industrial_mask = (
    (df['facility_within_1km'] == 1) &
    (df['nearest_facility_category'].isin(['fuel', 'power_plant', 'manufacturing'])) &
    (df['frp'] > 2.0)
)

# Agricultural: dw_crops>=0.60 AND dw_built<=0.10 AND dw_trees<=0.10 AND dw_shrub_and_scrub<=0.10 AND facility_within_1km=0 AND month in {3,4,5,10,11,12} AND frp<20
# Extract month from acq_datetime
df['month'] = df['acq_datetime'].dt.month
agricultural_mask = (
    (df['dw_crops'] >= 0.60) &
    (df['dw_built'] <= 0.10) &
    (df['dw_trees'] <= 0.10) &
    (df['dw_shrub_and_scrub'] <= 0.10) &
    (df['facility_within_1km'] == 0) &
    (df['month'].isin([3,4,5,10,11,12])) &
    (df['frp'] < 20)
)

# Wildfire: dw_trees>=0.50 AND dw_built<=0.10 AND dw_crops<=0.10 AND facility_within_1km=0 AND persistence_date_count=1 AND month in {2,3,4,5}
wildfire_mask = (
    (df['dw_trees'] >= 0.50) &
    (df['dw_built'] <= 0.10) &
    (df['dw_crops'] <= 0.10) &
    (df['facility_within_1km'] == 0) &
    (df['persistence_date_count'] == 1) &
    (df['month'].isin([2,3,4,5]))
)

# Persistence attribute: is_persistent = True when persistence_date_count >= 2
is_persistent = (df['persistence_date_count'] >= 2)

# Initialize target_class as 'unknown'
target_class = pd.Series('unknown', index=df.index)

# Assign classes where masks are True
target_class[industrial_mask] = 'industrial'
target_class[agricultural_mask] = 'agricultural'
target_class[wildfire_mask] = 'wildfire'

# Check for conflicts: where more than one mask is True
conflict_mask = (industrial_mask & agricultural_mask) | (industrial_mask & wildfire_mask) | (agricultural_mask & wildfire_mask) | (industrial_mask & agricultural_mask & wildfire_mask)

# For rows with conflict, we need to set label_conflict=True and preserve the competing evidence
# We'll create a column that lists the matching classes
matching_classes = []
for idx, row in df.iterrows():
    classes = []
    if industrial_mask[idx]:
        classes.append('industrial')
    if agricultural_mask[idx]:
        classes.append('agricultural')
    if wildfire_mask[idx]:
        classes.append('wildfire')
    matching_classes.append(classes)

df['matching_classes'] = matching_classes

# Now, for target_class, we will assign:
# - If exactly one class matches, use that class.
# - If more than one matches, set target_class to 'conflict' and set label_conflict=True.
# - If none matches, target_class remains 'unknown'.

# Update target_class for conflicts to 'conflict'
target_class[conflict_mask] = 'conflict'

# Now, assign the target_class series to the dataframe
df['target_class'] = target_class

# Now create the label_confidence and label_confidence_level and label_evidence
# We'll define a heuristic confidence based on evidence count

# Industrial evidence (4 conditions):
ind_ev1 = (df['facility_within_1km'] == 1).astype(int)
ind_ev2 = (df['nearest_facility_category'].isin(['fuel', 'power_plant', 'manufacturing'])).astype(int)
ind_ev3 = (df['frp'] > 2.0).astype(int)
ind_ev4 = (df['persistence_date_count'] >= 1).astype(int)  # supporting evidence
industrial_evidence_count = ind_ev1 + ind_ev2 + ind_ev3 + ind_ev4
industrial_confidence = industrial_evidence_count / 4.0

# Agricultural evidence (7 conditions):
agri_ev1 = (df['dw_crops'] >= 0.60).astype(int)
agri_ev2 = (df['dw_built'] <= 0.10).astype(int)
agri_ev3 = (df['dw_trees'] <= 0.10).astype(int)
agri_ev4 = (df['dw_shrub_and_scrub'] <= 0.10).astype(int)
agri_ev5 = (df['facility_within_1km'] == 0).astype(int)
agri_ev6 = (df['month'].isin([3,4,5,10,11,12])).astype(int)
agri_ev7 = (df['frp'] < 20).astype(int)
agricultural_evidence_count = agri_ev1 + agri_ev2 + agri_ev3 + agri_ev4 + agri_ev5 + agri_ev6 + agri_ev7
agricultural_confidence = agricultural_evidence_count / 7.0

# Wildfire evidence (6 conditions):
wild_ev1 = (df['dw_trees'] >= 0.50).astype(int)
wild_ev2 = (df['dw_built'] <= 0.10).astype(int)
wild_ev3 = (df['dw_crops'] <= 0.10).astype(int)
wild_ev4 = (df['facility_within_1km'] == 0).astype(int)
wild_ev5 = (df['persistence_date_count'] == 1).astype(int)
wild_ev6 = (df['month'].isin([2,3,4,5])).astype(int)
wildfire_evidence_count = wild_ev1 + wild_ev2 + wild_ev3 + wild_ev4 + wild_ev5 + wild_ev6
wildfire_confidence = wildfire_evidence_count / 6.0

# Initialize confidence series
confidence = pd.Series(0.0, index=df.index)

# For industrial rows
confidence[df['target_class'] == 'industrial'] = industrial_confidence[df['target_class'] == 'industrial']
# For agricultural rows
confidence[df['target_class'] == 'agricultural'] = agricultural_confidence[df['target_class'] == 'agricultural']
# For wildfire rows
confidence[df['target_class'] == 'wildfire'] = wildfire_confidence[df['target_class'] == 'wildfire']
# For unknown rows: set confidence to 0.0
confidence[df['target_class'] == 'unknown'] = 0.0

# For conflict rows: compute average of the confidences of the matching classes
# We'll do this by iterating over conflict rows only if there are any
conflict_indices = df[df['target_class'] == 'conflict'].index
if len(conflict_indices) > 0:
    conflict_confidences = []
    for idx in conflict_indices:
        row = df.loc[idx]
        classes = row['matching_classes']
        vals = []
        if 'industrial' in classes:
            vals.append(industrial_confidence[idx])
        if 'agricultural' in classes:
            vals.append(agricultural_confidence[idx])
        if 'wildfire' in classes:
            vals.append(wildfire_confidence[idx])
        conflict_confidences.append(np.mean(vals) if vals else 0.0)
    confidence[conflict_indices] = conflict_confidences

# Assign to df
df['label_confidence'] = confidence

# Label confidence level
df['label_confidence_level'] = pd.cut(df['label_confidence'],
                                      bins=[-0.1, 0.5, 0.8, 1.1],
                                      labels=['low', 'medium', 'high'],
                                      include_lowest=True)

# Label evidence: create a string that lists the evidence that was met for the assigned class.
def get_evidence_string(row):
    # For the assigned class, list which evidence conditions were met.
    if row['target_class'] == 'industrial':
        evidences = []
        if row['facility_within_1km'] == 1:
            evidences.append("facility_within_1km=1")
        if row['nearest_facility_category'] in ['fuel', 'power_plant', 'manufacturing']:
            evidences.append(f"facility_category={row['nearest_facility_category']}")
        if row['frp'] > 2.0:
            evidences.append(f"frp>{row['frp']:.2f}")
        if row['persistence_date_count'] >= 1:
            evidences.append(f"persistence_date_count>={row['persistence_date_count']}")
        return "; ".join(evidences)
    elif row['target_class'] == 'agricultural':
        evidences = []
        if row['dw_crops'] >= 0.60:
            evidences.append(f"dw_crops>={row['dw_crops']:.2f}")
        if row['dw_built'] <= 0.10:
            evidences.append(f"dw_built<={row['dw_built']:.2f}")
        if row['dw_trees'] <= 0.10:
            evidences.append(f"dw_trees<={row['dw_trees']:.2f}")
        if row['dw_shrub_and_scrub'] <= 0.10:
            evidences.append(f"dw_shrub_and_scrub<={row['dw_shrub_and_scrub']:.2f}")
        if row['facility_within_1km'] == 0:
            evidences.append("facility_within_1km=0")
        if row['month'] in [3,4,5,10,11,12]:
            evidences.append(f"month={row['month']}")
        if row['frp'] < 20:
            evidences.append(f"frp<{row['frp']:.2f}")
        return "; ".join(evidences)
    elif row['target_class'] == 'wildfire':
        evidences = []
        if row['dw_trees'] >= 0.50:
            evidences.append(f"dw_trees>={row['dw_trees']:.2f}")
        if row['dw_built'] <= 0.10:
            evidences.append(f"dw_built<={row['dw_built']:.2f}")
        if row['dw_crops'] <= 0.10:
            evidences.append(f"dw_crops<={row['dw_crops']:.2f}")
        if row['facility_within_1km'] == 0:
            evidences.append("facility_within_1km=0")
        if row['persistence_date_count'] == 1:
            evidences.append("persistence_date_count=1")
        if row['month'] in [2,3,4,5]:
            evidences.append(f"month={row['month']}")
        return "; ".join(evidences)
    elif row['target_class'] == 'conflict':
        # List the evidence for each matching class? Or just say conflict.
        return f"Conflict between: {', '.join(row['matching_classes'])}"
    else:
        return "No rule matched"

df['label_evidence'] = df.apply(get_evidence_string, axis=1)

# Now, add the required columns:
df['label_source'] = "weak_rule_based"
df['is_ground_truth'] = False

# Create label_conflict column: True if target_class is 'conflict'
df['label_conflict'] = (df['target_class'] == 'conflict')

# Now, we need to reorder columns to keep the original ones and add the new ones at the end.
# List the new columns we want to add:
new_columns = ['target_class', 'label_confidence', 'label_confidence_level', 'label_evidence',
               'label_conflict', 'is_persistent', 'persistence_date_count', 'time_span_days',
               'detections_24h', 'detections_3d', 'detections_7d', 'active_days',
               'persistence_duration_days', 'mean_frp', 'max_frp',
               'label_source', 'is_ground_truth']

# Get the original column order (without the new columns and temporary columns)
# We'll drop temporary columns first
df = df.drop(columns=['month', 'matching_classes'], errors='ignore')

# Now get original columns (excluding the new ones we want to add)
original_cols = [col for col in df.columns if col not in new_columns]

# Create a new dataframe with the original columns first, then the new columns
df_out = df[original_cols + new_columns]

# Write to CSV
output_path = r"C:\ProjectX\SIH26162\docs\FireGuard_WEAKLABELS_FIXED.csv"
print(f"Writing weak labels to {output_path}...")
df_out.to_csv(output_path, index=False)

print("Done.")

# Now, let's do some validation and print summary for the report.
print("\n=== Validation Summary ===")
print(f"Input rows: {len(df)}")
print(f"Output rows: {len(df_out)}")
assert len(df) == len(df_out), "Row count mismatch!"

# Class counts
class_counts = df_out['target_class'].value_counts()
print("\nTarget class distribution:")
for cls, count in class_counts.items():
    print(f"  {cls}: {count} ({count/len(df_out)*100:.2f}%)")

# Confidence level distribution
conf_level_counts = df_out['label_confidence_level'].value_counts()
print("\nConfidence level distribution:")
for level, count in conf_level_counts.items():
    print(f"  {level}: {count} ({count/len(df_out)*100:.2f}%)")

# Conflict count
conflict_count = df_out['label_conflict'].sum()
print(f"\nConflict count: {conflict_count} ({conflict_count/len(df_out)*100:.2f}%)")

# Persistent count
persistent_count = df_out['is_persistent'].sum()
print(f"Persistent count: {persistent_count} ({persistent_count/len(df_out)*100:.2f}%)")

# Persistence feature statistics
print("\nPersistence feature statistics (corrected):")
print(f"  persistence_date_count - mean: {df_out['persistence_date_count'].mean():.2f}, max: {df_out['persistence_date_count'].max()}")
print(f"  time_span_days - mean: {df_out['time_span_days'].mean():.2f}, max: {df_out['time_span_days'].max()}")
print(f"  detections_24h - mean: {df_out['detections_24h'].mean():.2f}, max: {df_out['detections_24h'].max()}")
print(f"  active_days - mean: {df_out['active_days'].mean():.2f}, max: {df_out['active_days'].max()}")
print(f"  persistence_duration_days - mean: {df_out['persistence_duration_days'].mean():.2f}, max: {df_out['persistence_duration_days'].max()}")
print(f"  mean_frp - mean: {df_out['mean_frp'].mean():.2f}, max: {df_out['mean_frp'].max():.2f}")
print(f"  max_frp - mean: {df_out['max_frp'].mean():.2f}, max: {df_out['max_frp'].max():.2f}")

# Check for missing values in generated columns
missing_cols = df_out[new_columns].isnull().sum()
print("\nMissing values in generated columns:")
for col in new_columns:
    if missing_cols[col] > 0:
        print(f"  {col}: {missing_cols[col]}")

# Save the validation summary to a string for the report
validation_summary = {
    'input_rows': len(df),
    'output_rows': len(df_out),
    'class_counts': class_counts.to_dict(),
    'conf_level_counts': conf_level_counts.to_dict(),
    'conflict_count': int(conflict_count),
    'persistent_count': int(persistent_count),
    'persistence_stats': {
        'persistence_date_count_mean': float(df_out['persistence_date_count'].mean()),
        'persistence_date_count_max': int(df_out['persistence_date_count'].max()),
        'time_span_days_mean': float(df_out['time_span_days'].mean()),
        'time_span_days_max': int(df_out['time_span_days'].max()),
        'detections_24h_mean': float(df_out['detections_24h'].mean()),
        'detections_24h_max': int(df_out['detections_24h'].max()),
        'active_days_mean': float(df_out['active_days'].mean()),
        'active_days_max': int(df_out['active_days'].max()),
        'persistence_duration_days_mean': float(df_out['persistence_duration_days'].mean()),
        'persistence_duration_days_max': int(df_out['persistence_duration_days'].max()),
        'mean_frp_mean': float(df_out['mean_frp'].mean()),
        'mean_frp_max': float(df_out['mean_frp'].max()),
        'max_frp_mean': float(df_out['max_frp'].mean()),
        'max_frp_max': float(df_out['max_frp'].max())
    },
    'missing_counts': missing_cols.to_dict()
}

# Print validation summary for report
print("\n=== Validation Summary (for report) ===")
print(f"Input rows: {validation_summary['input_rows']}")
print(f"Output rows: {validation_summary['output_rows']}")
print("\nClass counts:")
for cls, cnt in validation_summary['class_counts'].items():
    print(f"  {cls}: {cnt} ({cnt/validation_summary['output_rows']*100:.2f}%)")
print("\nConfidence level counts:")
for level, cnt in validation_summary['conf_level_counts'].items():
    print(f"  {level}: {cnt} ({cnt/validation_summary['output_rows']*100:.2f}%)")
print(f"Conflict count: {validation_summary['conflict_count']} ({validation_summary['conflict_count']/validation_summary['output_rows']*100:.2f}%)")
print(f"Persistent count: {validation_summary['persistent_count']} ({validation_summary['persistent_count']/validation_summary['output_rows']*100:.2f}%)")
print("\nPersistence feature statistics:")
stats = validation_summary['persistence_stats']
print(f"  persistence_date_count - mean: {stats['persistence_date_count_mean']:.2f}, max: {stats['persistence_date_count_max']}")
print(f"  time_span_days - mean: {stats['time_span_days_mean']:.2f}, max: {stats['time_span_days_max']}")
print(f"  detections_24h - mean: {stats['detections_24h_mean']:.2f}, max: {stats['detections_24h_max']}")
print(f"  active_days - mean: {stats['active_days_mean']:.2f}, max: {stats['active_days_max']}")
print(f"  persistence_duration_days - mean: {stats['persistence_duration_days_mean']:.2f}, max: {stats['persistence_duration_days_max']}")
print(f"  mean_frp - mean: {stats['mean_frp_mean']:.2f}, max: {stats['mean_frp_max']:.2f}")
print(f"  max_frp - mean: {stats['max_frp_mean']:.2f}, max: {stats['max_frp_max']:.2f}")
print("\nMissing values in generated columns:")
for col, cnt in validation_summary['missing_counts'].items():
    if cnt > 0:
        print(f"  {col}: {cnt}")

# Also save summary to JSON for later use
with open(r"C:\ProjectX\SIH26162\docs\weak_labels_fixed_summary.json", 'w') as f:
    json.dump(validation_summary, f, indent=2)

print(f"\nValidation summary saved to weak_labels_fixed_summary.json")

# Run temporal leakage test
print("\n=== Running Temporal Leakage Test ===")
print("Verifying that no future data influenced persistence features...")

# Test a sample of rows for temporal correctness
import random
test_indices = random.sample(range(len(df_out)), min(1000, len(df_out)))
leakage_found = False

for idx in test_indices:
    row = df_out.iloc[idx]
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
        expected_detections_24h = ((historical_df['acq_datetime'] >= (current_time - timedelta(hours=24))) &
                                  (historical_df['acq_datetime'] <= current_time)).sum()
        expected_active_days = historical_df['acq_datetime'].dt.date.nunique()
    else:
        expected_persistence_date_count = 0
        expected_time_span_days = 0
        expected_detections_24h = 0
        expected_active_days = 0

    actual_persistence_date_count = row['persistence_date_count']
    actual_time_span_days = row['time_span_days']
    actual_detections_24h = row['detections_24h']
    actual_active_days = row['active_days']

    # Check if they match
    if (expected_persistence_date_count != actual_persistence_date_count or
        expected_time_span_days != actual_time_span_days or
        expected_detections_24h != actual_detections_24h or
        expected_active_days != actual_active_days):
        print(f"  TEMPORAL LEAKAGE DETECTED at row {idx}!")
        print(f"    Event time: {current_time}")
        print(f"    Expected persistence_date_count: {expected_persistence_date_count}, got: {actual_persistence_date_count}")
        print(f"    Expected time_span_days: {expected_time_span_days}, got: {actual_time_span_days}")
        print(f"    Expected detections_24h: {expected_detections_24h}, got: {actual_detections_24h}")
        print(f"    Expected active_days: {expected_active_days}, got: {actual_active_days}")
        leakage_found = True
        break

if not leakage_found:
    print("  [PASS] No temporal leakage detected in sample test")
else:
    print("  [FAIL] TEMPORAL LEAKAGE CONFIRMED")