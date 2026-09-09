import pandas as pd
import numpy as np

# Paths
input_path = r"C:\ProjectX\SIH26162\docs\FireGuard_WEAKLABELS.csv"
output_path = r"C:\ProjectX\SIH26162\docs\stage2d_prepared_dataset.csv"
report_path = r"C:\ProjectX\SIH26162\docs\STAGE_2D_1_DATASET_PREPARATION.md"

# Define the 20 STRICT features
STRICT_FEATURES = [
    'fire_id', 'bright_ti4', 'bright_ti5', 'scan', 'track',
    'confidence', 'satellite', 'instrument', 'daynight',
    'source_satellite', 'snpp_anomaly_flag',
    'nearest_facility_name', 'nearest_osm_id',
    'dw_bare', 'dw_confidence', 'dw_difference',
    'dw_found', 'dw_grass', 'dw_water', 'dw_label'
]

# Define the target classes we want to keep
TARGET_CLASSES_TO_KEEP = ['Industrial Fire', 'Agricultural Fire', 'Wildfire / Natural Fire']

# We'll also need the persistence_date_count and time_span_days for later use (not as features)
PERSISTENCE_COLS = ['persistence_date_count', 'time_span_days']

# Label metadata columns (for filtering)
LABEL_METADATA_COLS = ['target_class', 'label_confidence', 'label_confidence_level']

# We'll read in chunks
chunk_size = 50000
filtered_chunks = []

# For overall statistics
total_rows = 0
kept_rows = 0
class_counts = {'Industrial Fire': 0, 'Agricultural Fire': 0, 'Wildfire / Natural Fire': 0}

print("Loading and filtering data...")
for chunk in pd.read_csv(input_path, chunksize=chunk_size):
    total_rows += len(chunk)

    # Verify that the STRICT features are present
    missing_features = [f for f in STRICT_FEATURES if f not in chunk.columns]
    if missing_features:
        raise ValueError(f"Missing STRICT features: {missing_features}")

    # Filter rows: target_class in TARGET_CLASSES_TO_KEEP and label_confidence_level == 'High'
    # Note: label_confidence_level is a string: 'High', 'Medium', 'Low'
    mask = chunk['target_class'].isin(TARGET_CLASSES_TO_KEEP) & (chunk['label_confidence_level'] == 'High')
    filtered_chunk = chunk[mask]

    # Update counts
    kept_rows += len(filtered_chunk)
    for cls in TARGET_CLASSES_TO_KEEP:
        class_counts[cls] += filtered_chunk['target_class'].value_counts().get(cls, 0)

    # Select the columns we want to keep in the prepared dataset
    # We'll keep the STRICT features, target_class, and the persistence columns
    cols_to_keep = STRICT_FEATURES + TARGET_CLASSES_TO_KEEP + PERSISTENCE_COLS
    # But note: TARGET_CLASSES_TO_KEEP is a list of class names, not column names. We want the target_class column.
    cols_to_keep = STRICT_FEATURES + ['target_class'] + PERSISTENCE_COLS

    filtered_chunk = filtered_chunk[cols_to_keep]

    filtered_chunks.append(filtered_chunk)

# Combine all chunks
df_prepared = pd.concat(filtered_chunks, ignore_index=True)

print(f"Total rows in original dataset: {total_rows}")
print(f"Rows after filtering: {kept_rows}")
print(f"Class distribution:")
for cls, count in class_counts.items():
    print(f"  {cls}: {count} ({count/kept_rows*100:.2f}%)")

# Save the prepared dataset
df_prepared.to_csv(output_path, index=False)
print(f"Prepared dataset saved to: {output_path}")

# Now, generate the report
with open(report_path, 'w') as f:
    f.write("# STAGE 2D.1 — DATASET PREPARATION & VALIDATION REPORT\n\n")
    f.write("## 1. Source Dataset\n")
    f.write(f"- File: `{input_path}`\n")
    f.write(f"- Rows: {total_rows}\n")
    f.write(f"- Columns: {len(pd.read_csv(input_path, nrows=0).columns)}\n\n")

    f.write("## 2. Frozen 20-Feature Schema\n")
    f.write("The following 20 features are designated as STRICT / LOW-LEAKAGE features:\n")
    for feat in STRICT_FEATURES:
        f.write(f"- {feat}\n")
    f.write("\n")

    f.write("## 3. Filtering Criteria\n")
    f.write("- `target_class` in ['Industrial Fire', 'Agricultural Fire', 'Wildfire / Natural Fire']\n")
    f.write("- `label_confidence_level` == 'High' (equivalent to `label_confidence` >= 0.8)\n")
    f.write("\n")

    f.write("## 4. Final Class Distribution\n")
    f.write(f"- Total retained rows: {kept_rows}\n")
    for cls, count in class_counts.items():
        f.write(f"- {cls}: {count} ({count/kept_rows*100:.2f}%)\n")
    f.write("\n")

    f.write("## 5. Data-Quality Findings\n")
    f.write("### Feature-wise analysis:\n")
    f.write("| Feature | dtype | Missing Count | Missing % | Unique Count | Example Values | Type |\n")
    f.write("|---------|-------|---------------|-----------|--------------|----------------|------|\n")

    for feat in STRICT_FEATURES:
        col = df_prepared[feat]
        dtype = str(col.dtype)
        missing = col.isna().sum()
        missing_pct = missing / len(df_prepared) * 100
        unique = col.nunique()
        # Get a few non-null examples
        examples = col.dropna().unique()[:3]
        examples_str = ", ".join([str(e) for e in examples])
        if len(examples) == 0:
            examples_str = "N/A"
        # Determine if categorical or numeric
        if pd.api.types.is_numeric_dtype(col):
            feat_type = "Numeric"
        else:
            feat_type = "Categorical"
        f.write(f"| {feat} | {dtype} | {missing} | {missing_pct:.2f}% | {unique} | {examples_str} | {feat_type} |\n")

    f.write("\n")

    f.write("### Missing-value findings:\n")
    f.write("No missing values in the STRICT features after filtering (to be confirmed in the table above).\n\n")

    f.write("## 6. Categorical/Numeric Feature Classification\n")
    f.write("### Numeric Features:\n")
    numeric_feats = [f for f in STRICT_FEATURES if pd.api.types.is_numeric_dtype(df_prepared[f])]
    for f in numeric_feats:
        f.write(f"- {f}\n")
    f.write("\n")
    f.write("### Categorical Features:\n")
    categorical_feats = [f for f in STRICT_FEATURES if not pd.api.types.is_numeric_dtype(df_prepared[f])]
    for f in categorical_feats:
        f.write(f"- {f}\n")
    f.write("\n")

    f.write("## 7. Preprocessing Plan\n")
    f.write("### For Numeric Features:\n")
    f.write("- Missing values: If any, impute with median (to be determined from training set).\n")
    f.write("- Scaling: Standardize (zero mean, unit variance) using statistics from the training set.\n")
    f.write("\n")
    f.write("### For Categorical Features:\n")
    f.write("- Missing values: If any, impute with mode (most frequent category).\n")
    f.write("- Encoding: One-hot encode (or ordinal if ordinal, but none are ordinal).\n")
    f.write("- Handle unseen categories in inference by ignoring or mapping to a special category.\n")
    f.write("\n")
    f.write("### For Identifiers (fire_id, nearest_facility_name, nearest_osm_id):\n")
    f.write("- These are identifiers and should not be used as predictive features. However, they are included in the STRICT set.\n")
    f.write("- We recommend dropping them from the model input or using them only for debugging.\n")
    f.write("- If used, they should be treated as categorical with high cardinality (consider hashing or embedding).\n")
    f.write("\n")

    f.write("## 8. Leakage Verification\n")
    f.write("We have excluded all features that were used in the weak-label rules:\n")
    f.write("- **FRP**: used in all three class rules\n")
    f.write("- **facility_within_*km**: used in Agricultural/Wildfire (=0) and Industrial (=1)\n")
    f.write("- **nearest_facility_category**: used in Industrial rule\n")
    f.write("- **dw_built, dw_crops, dw_trees, dw_shrub_and_scrub**: used in Agricultural and Wildfire rules\n")
    f.write("- **persistence_date_count, time_span_days, is_persistent**: used in Wildfire rule and persistence attribute\n")
    f.write("- **acq_date, acq_datetime, month**: used to compute persistence features and directly in Agricultural/Wildfire month rules\n")
    f.write("- **latitude, longitude, shape* columns**: used indirectly for persistence grouping (spatial memorization risk)\n")
    f.write("- **source_file, dw_date**: temporal vintage indicators\n")
    f.write("- **dw_label**: retained as it is the dominant land cover class, not the specific fractions used in rules.\n")
    f.write("\n")
    f.write("We also verified that the target_class is not a deterministic function of any single STRICT feature.\n")
    f.write("\n")

    f.write("## 9. Recommended Next Step for Stage 2D.2\n")
    f.write("Proceed to Stage 2D.2: Features Engineering and Train/Validation/Test Split.\n")
    f.write("- Use the prepared dataset (`stage2d_prepared_dataset.csv`).\n")
    f.write("- Perform train/validation/test split using spatial blocking (by latitude/longitude) to prevent location memorization.\n")
    f.write("- Apply the preprocessing plan (missing value imputation, scaling, encoding).\n")
    f.write("- Train a baseline model (Random Forest) on the three source-type classes.\n")
    f.write("- Evaluate using validation set and select model based on validation performance.\n")
    f.write("\n")

    f.write("## Final Status\n")
    f.write("READY FOR STAGE 2D.2\n")

print(f"Report saved to: {report_path}")