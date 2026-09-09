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
# Note: We will handle conflicts later
target_class[industrial_mask] = 'industrial'
target_class[agricultural_mask] = 'agricultural'
target_class[wildfire_mask] = 'wildfire'

# Check for conflicts: where more than one mask is True
conflict_mask = industrial_mask & agricultural_mask | industrial_mask & wildfire_mask | agricultural_mask & wildfire_mask
# Also check for three-way conflict
conflict_mask = conflict_mask | (industrial_mask & agricultural_mask & wildfire_mask)

# For rows with conflict, we need to set label_conflict=True and choose a class based on priority?
# The instruction says: "If multiple source-class rules match, do NOT silently choose one.
# Record: label_conflict=True and preserve the competing evidence in a suitable column.
# Use a documented priority only if necessary for a single target_class."

# We'll set target_class to 'conflict' for now, and then we can decide on a priority if needed.
# But the instruction says to use a documented priority only if necessary for a single target_class.
# We'll create a separate column for the conflicting evidence.

# Let's create a column that lists the matching classes
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

# We'll update target_class for conflicts to 'conflict'
target_class[conflict_mask] = 'conflict'

# Now create the label_confidence and label_confidence_level and label_evidence
# We'll define a heuristic confidence:

# For each row, confidence based on:
#   - How strongly the conditions are met (e.g., how far above thresholds)
#   - Agreement between different evidence (if multiple conditions point to same class)

# We'll compute a simple score for each class and then set confidence to the max score for the assigned class.

# Initialize confidence columns
df['label_confidence'] = 0.0
df['label_confidence_level'] = 'low'
df['label_evidence'] = ''

# We'll compute evidence for each class

# Industrial evidence:
#   - facility_within_1km (binary, but we know it's 1)
#   - nearest_facility_category (we can give weight if it's one of the three)
#   - frp: we can normalize by how much above 2.0? But note: frp can be very high.
#   - persistence_date_count: we can use as supporting evidence (but not required)

# We'll compute a score for each class and then normalize to 0-1.

# Let's define:

# Industrial score:
#   facility_within_1km: 1 if true else 0
#   facility_category: 1 if in {fuel,power_plant,manufacturing} else 0
#   frp: we can use a sigmoid-like function: 1 - exp(-(frp-2.0)/scale) but we don't know scale.
#        Instead, we can use min(frp/10.0, 1.0) but note frp can be >10.
#        We'll use: min(frp/20.0, 1.0)  [assuming 20 is a high frp]
#   persistence_date_count: we can use min(persistence_date_count/2.0, 1.0)  [since we know max is 2]

# We'll combine with weights.

# However, to keep it simple and interpretable, we'll use a set of binary evidence and then compute confidence as the fraction of evidence present.

# For Industrial, we have 4 pieces of evidence:
#   1. facility_within_1km == 1
#   2. nearest_facility_category in {fuel,power_plant,manufacturing}
#   3. frp > 2.0
#   4. persistence_date_count >= 1 (as supporting evidence, not required)

# We'll compute:
#   industrial_evidence_count = sum of these 4 binary conditions
#   industrial_confidence = industrial_evidence_count / 4.0

# Similarly for Agricultural and Wildfire.

# Let's define the evidence for each class:

# Industrial evidence:
ind_ev1 = (df['facility_within_1km'] == 1).astype(int)
ind_ev2 = (df['nearest_facility_category'].isin(['fuel', 'power_plant', 'manufacturing'])).astype(int)
ind_ev3 = (df['frp'] > 2.0).astype(int)
ind_ev4 = (df['persistence_date_count'] >= 1).astype(int)  # supporting evidence
industrial_evidence_count = ind_ev1 + ind_ev2 + ind_ev3 + ind_ev4
industrial_confidence = industrial_evidence_count / 4.0

# Agricultural evidence:
#   1. dw_crops >= 0.60
#   2. dw_built <= 0.10
#   3. dw_trees <= 0.10
#   4. dw_shrub_and_scrub <= 0.10
#   5. facility_within_1km == 0
#   6. month in {3,4,5,10,11,12}
#   7. frp < 20
agri_ev1 = (df['dw_crops'] >= 0.60).astype(int)
agri_ev2 = (df['dw_built'] <= 0.10).astype(int)
agri_ev3 = (df['dw_trees'] <= 0.10).astype(int)
agri_ev4 = (df['dw_shrub_and_scrub'] <= 0.10).astype(int)
agri_ev5 = (df['facility_within_1km'] == 0).astype(int)
agri_ev6 = (df['month'].isin([3,4,5,10,11,12])).astype(int)
agri_ev7 = (df['frp'] < 20).astype(int)
agricultural_evidence_count = agri_ev1 + agri_ev2 + agri_ev3 + agri_ev4 + agri_ev5 + agri_ev6 + agri_ev7
agricultural_confidence = agricultural_evidence_count / 7.0

# Wildfire evidence:
#   1. dw_trees >= 0.50
#   2. dw_built <= 0.10
#   3. dw_crops <= 0.10
#   4. facility_within_1km == 0
#   5. persistence_date_count == 1
#   6. month in {2,3,4,5}
wild_ev1 = (df['dw_trees'] >= 0.50).astype(int)
wild_ev2 = (df['dw_built'] <= 0.10).astype(int)
wild_ev3 = (df['dw_crops'] <= 0.10).astype(int)
wild_ev4 = (df['facility_within_1km'] == 0).astype(int)
wild_ev5 = (df['persistence_date_count'] == 1).astype(int)
wild_ev6 = (df['month'].isin([2,3,4,5])).astype(int)
wildfire_evidence_count = wild_ev1 + wild_ev2 + wild_ev3 + wild_ev4 + wild_ev5 + wild_ev6
wildfire_confidence = wildfire_evidence_count / 6.0

# Now, for each row, we set:
#   label_confidence = confidence of the assigned class (if assigned to industrial, agricultural, wildfire)
#   For conflict, we can set confidence as the average of the confidences of the conflicting classes? Or max?
#   For unknown, we set confidence to 0.0? Or we can compute a confidence for unknown as 1 - max(class_confidences)?
#   The instruction says confidence must reflect rule strength and evidence agreement.

# We'll do:
#   If target_class is industrial, agricultural, or wildfire: confidence = corresponding class confidence
#   If target_class is conflict: confidence = average of the confidences of the matching classes
#   If target_class is unknown: confidence = 1.0 - max(industrial_confidence, agricultural_confidence, wildfire_confidence)  [but note: this might not be accurate]

# However, note that the unknown class is defined as not matching any rule, so we can set confidence low.

# Let's set for unknown: confidence = 0.0 (or we can compute as 1.0 - max(class_confidences) but then it might be high if no class matches but one is close).

# We'll set unknown confidence to 0.0 for simplicity.

# We'll also create label_confidence_level based on confidence thresholds:
#   high: confidence >= 0.8
#   medium: confidence >= 0.5 and < 0.8
#   low: confidence < 0.5

# Now, compute confidence for each row based on target_class

# Initialize confidence series
confidence = pd.Series(0.0, index=df.index)

# For industrial rows
confidence[target_class == 'industrial'] = industrial_confidence[target_class == 'industrial']
# For agricultural rows
confidence[target_class == 'agricultural'] = agricultural_confidence[target_class == 'agricultural']
# For wildfire rows
confidence[target_class == 'wildfire'] = wildfire_confidence[target_class == 'wildfire']
# For conflict rows: we'll compute the average of the confidences of the matching classes
# We'll do this by iterating over conflict rows? Or we can vectorize.

# Let's create a temporary dataframe for the confidences of each class
temp_df = pd.DataFrame({
    'industrial_conf': industrial_confidence,
    'agricultural_conf': agricultural_confidence,
    'wildfire_conf': wildfire_confidence
}, index=df.index)

# For conflict rows, we want the average of the confidences of the classes that are True in the masks.
# We'll do:
def get_conflict_confidence(row):
    classes = row['matching_classes']
    if not classes:
        return 0.0
    # Get the confidences for these classes
    vals = []
    if 'industrial' in classes:
        vals.append(row['industrial_conf'])
    if 'agricultural' in classes:
        vals.append(row['agricultural_conf'])
    if 'wildfire' in classes:
        vals.append(row['wildfire_conf'])
    return np.mean(vals) if vals else 0.0

# Apply to conflict rows
confidence[target_class == 'conflict'] = df[target_class == 'conflict'].apply(get_conflict_confidence, axis=1)
# For unknown rows, set confidence to 0.0
confidence[target_class == 'unknown'] = 0.0

# Now assign to df
df['label_confidence'] = confidence

# Label confidence level
df['label_confidence_level'] = pd.cut(df['label_confidence'],
                                      bins=[-0.1, 0.5, 0.8, 1.1],
                                      labels=['low', 'medium', 'high'],
                                      include_lowest=True)

# Label evidence: we can create a string that lists the evidence that was met for the assigned class.
# We'll create a function to generate evidence string for a row based on the assigned class.

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

# Now, we have the target_class column (which we called target_class, but we need to rename to target_class? Actually we have a column named target_class from the series we created)
# We created a series `target_class` and then assigned to df? Actually we did not assign it to df yet.

# We have the series `target_class` that we computed. Let's assign it to df.
df['target_class'] = target_class

# Now, add the required columns:
df['label_source'] = "weak_rule_based"
df['is_ground_truth'] = False

# We already have:
#   target_class
#   label_confidence
#   label_confidence_level
#   label_evidence
#   label_conflict (we haven't created this yet, we have conflict_mask and matching_classes)
#   is_persistent
#   persistence_date_count
#   time_span_days

# Create label_conflict column: True if target_class is 'conflict'
df['label_conflict'] = (df['target_class'] == 'conflict')

# Now, we need to reorder columns to keep the original ones and add the new ones at the end? Or as specified.
# The instruction says: "Retain useful original fields, but add these new fields:"
# We'll keep the original columns and then add the new ones at the end.

# Let's list the new columns we want to add:
new_columns = ['target_class', 'label_confidence', 'label_confidence_level', 'label_evidence',
               'label_conflict', 'is_persistent', 'persistence_date_count', 'time_span_days',
               'label_source', 'is_ground_truth']

# Check if any of these already exist (they shouldn't)
# We'll create a new dataframe with the original columns in their original order, then the new columns.

# Get the original column order (without the new columns)
original_cols = [col for col in df.columns if col not in new_columns]

# Now create a new dataframe with the original columns first, then the new columns
df_out = df[original_cols + new_columns]

# However, note that we added a column 'month' during processing. This is not in the original CSV.
# We should not include 'month' in the output? The instruction says to retain useful original fields.
# We added 'month' for our computation, but it is not an original field.
# We should drop it from the output.

# Also, we added 'matching_classes' for internal use, we should drop it.

# Let's drop the temporary columns: 'month', 'matching_classes'
df_out = df_out.drop(columns=['month', 'matching_classes'], errors='ignore')

# Now, write to CSV
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

# We'll write this to a file or just print and then we can use it in the report.
# For now, we'll print and then the user can copy.

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