import pandas as pd
import numpy as np

print("Loading master CSV...")
df = pd.read_csv(r"C:\ProjectX\SIH26162\docs\FireGuard_MASTER.csv")

print(f"Loaded {len(df)} rows")

# Convert acq_datetime to datetime
df['acq_datetime'] = pd.to_datetime(df['acq_datetime'])

# Compute persistence columns: group by latitude, longitude
print("Computing persistence columns...")
grouped = df.groupby(['latitude', 'longitude'])['acq_datetime']

# persistence_date_count: number of unique dates (date part) at each location
persistence_date_count = grouped.apply(lambda x: x.dt.date.nunique()).reset_index(name='persistence_date_count')

# time_span_days: (max_date - min_date).days at each location
time_span_days = grouped.apply(lambda x: (x.max() - x.min()).days).reset_index(name='time_span_days')

# Merge back to original dataframe
df = df.merge(persistence_date_count, on=['latitude', 'longitude'], how='left')
df = df.merge(time_span_days, on=['latitude', 'longitude'], how='left')

# Now compute labels

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
confidence[target_class == 'industrial'] = industrial_confidence[target_class == 'industrial']
# For agricultural rows
confidence[target_class == 'agricultural'] = agricultural_confidence[target_class == 'agricultural']
# For wildfire rows
confidence[target_class == 'wildfire'] = wildfire_confidence[target_class == 'wildfire']
# For unknown rows: set confidence to 0.0
confidence[target_class == 'unknown'] = 0.0

# For conflict rows: compute average of the confidences of the matching classes
# We'll do this by iterating over conflict rows only if there are any
conflict_indices = df[target_class == 'conflict'].index
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

# Now, we have the target_class series. Let's assign it to df.
df['target_class'] = target_class

# Now, add the required columns:
df['label_source'] = "weak_rule_based"
df['is_ground_truth'] = False

# Create label_conflict column: True if target_class is 'conflict'
df['label_conflict'] = (df['target_class'] == 'conflict')

# Now, we need to reorder columns to keep the original ones and add the new ones at the end.
# List the new columns we want to add:
new_columns = ['target_class', 'label_confidence', 'label_confidence_level', 'label_evidence',
               'label_conflict', 'is_persistent', 'persistence_date_count', 'time_span_days',
               'label_source', 'is_ground_truth']

# Get the original column order (without the new columns and temporary columns)
# We'll drop temporary columns first
df = df.drop(columns=['month', 'matching_classes'], errors='ignore')

# Now get original columns (excluding the new ones we want to add)
original_cols = [col for col in df.columns if col not in new_columns]

# Create a new dataframe with the original columns first, then the new columns
df_out = df[original_cols + new_columns]

# Write to CSV
output_path = r"C:\ProjectX\SIH26162\docs\FireGuard_WEAKLABELS.csv"
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
    'missing_counts': missing_cols.to_dict()
}

# Print validation summary for report
print("\n=== Validation Summary (for report) ===")
print(f"Input rows: {validation_summary['input_rows']}")
print(f"Output rows: {validation_summary['output_rows']}")
print("\\nClass counts:")
for cls, cnt in validation_summary['class_counts'].items():
    print(f"  {cls}: {cnt} ({cnt/validation_summary['output_rows']*100:.2f}%)")
print("\\nConfidence level counts:")
for level, cnt in validation_summary['conf_level_counts'].items():
    print(f"  {level}: {cnt} ({cnt/validation_summary['output_rows']*100:.2f}%)")
print(f"Conflict count: {validation_summary['conflict_count']} ({validation_summary['conflict_count']/validation_summary['output_rows']*100:.2f}%)")
print(f"Persistent count: {validation_summary['persistent_count']} ({validation_summary['persistent_count']/validation_summary['output_rows']*100:.2f}%)")
print("\\nMissing values in generated columns:")
for col, cnt in validation_summary['missing_counts'].items():
    if cnt > 0:
        print(f"  {col}: {cnt}")