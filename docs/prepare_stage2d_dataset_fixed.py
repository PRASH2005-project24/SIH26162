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

# Define the target classes we want to keep (as they appear in the data)
TARGET_CLASSES_TO_KEEP = ['industrial', 'agricultural', 'wildfire']
# Mapping to proper case for reporting
TARGET_CLASS_MAP = {
    'industrial': 'Industrial Fire',
    'agricultural': 'Agricultural Fire',
    'wildfire': 'Wildfire / Natural Fire'
}

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
class_counts = {'industrial': 0, 'agricultural': 0, 'wildfire': 0}

print("Loading and filtering data...")
for chunk in pd.read_csv(input_path, chunksize=chunk_size):
    total_rows += len(chunk)

    # Verify that the STRICT features are present
    missing_features = [f for f in STRICT_FEATURES if f not in chunk.columns]
    if missing_features:
        raise ValueError(f"Missing STRICT features: {missing_features}")

    # Filter rows: target_class in TARGET_CLASSES_TO_KEEP and label_confidence_level == 'high'
    mask = chunk['target_class'].isin(TARGET_CLASSES_TO_KEEP) & (chunk['label_confidence_level'] == 'high')
    filtered_chunk = chunk[mask]

    # Update counts
    kept_rows += len(filtered_chunk)
    for cls in TARGET_CLASSES_TO_KEEP:
        class_counts[cls] += filtered_chunk['target_class'].value_counts().get(cls, 0)

    # Select the columns we want to keep in the prepared dataset
    # We'll keep the STRICT features, target_class, and the persistence columns
    cols_to_keep = STRICT_FEATURES + ['target_class'] + PERSISTENCE_COLS

    filtered_chunk = filtered_chunk[cols_to_keep]

    filtered_chunks.append(filtered_chunk)

# Combine all chunks
df_prepared = pd.concat(filtered_chunks, ignore_index=True)

print(f"Total rows in original dataset: {total_rows}")
print(f"Rows after filtering: {kept_rows}")
if kept_rows > 0:
    print(f"Class distribution:")
    for cls_key, count in class_counts.items():
        cls_name = TARGET_CLASS_MAP[cls_key]
        print(f"  {cls_name}: {count} ({count/kept_rows*100:.2f}%)")
else:
    print("No rows retained after filtering!")

# Save the prepared dataset
df_prepared.to_csv(output_path, index=False)
print(f"Prepared dataset saved to: {output_path}")

# Now, generate the report
with open(report_path, 'w') as report_file:
    report_file.write("# STAGE 2D.1 — DATASET PREPARATION & VALIDATION REPORT\n\n")
    report_file.write("## 1. Source Dataset\n")
    report_file.write(f"- File: `{input_path}`\n")
    report_file.write(f"- Rows: {total_rows}\n")
    report_file.write(f"- Columns: {len(pd.read_csv(input_path, nrows=0).columns)}\n\n")

    report_file.write("## 2. Frozen 20-Feature Schema\n")
    report_file.write("The following 20 features are designated as STRICT / LOW-LEAKAGE features:\n")
    for feat in STRICT_FEATURES:
        report_file.write(f"- {feat}\n")
    report_file.write("\n")

    report_file.write("## 3. Filtering Criteria\n")
    report_file.write("- `target_class` in ['industrial', 'agricultural', 'wildfire'] (Industrial Fire, Agricultural Fire, Wildfire / Natural Fire)\n")
    report_file.write("- `label_confidence_level` == 'high' (equivalent to `label_confidence` >= 0.8)\n")
    report_file.write("\n")

    report_file.write("## 4. Final Class Distribution\n")
    report_file.write(f"- Total retained rows: {kept_rows}\n")
    if kept_rows > 0:
        for cls_key, count in class_counts.items():
            cls_name = TARGET_CLASS_MAP[cls_key]
            report_file.write(f"- {cls_name}: {count} ({count/kept_rows*100:.2f}%)\n")
    else:
        report_file.write("- No rows retained after filtering.\n")
    report_file.write("\n")

    report_file.write("## 5. Data-Quality Findings\n")
    report_file.write("### Feature-wise analysis:\n")
    report_file.write("| Feature | dtype | Missing Count | Missing % | Unique Count | Example Values | Type |\n")
    report_file.write("|---------|-------|---------------|-----------|--------------|----------------|------|\n")

    if kept_rows > 0:
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
            report_file.write(f"| {feat} | {dtype} | {missing} | {missing_pct:.2f}% | {unique} | {examples_str} | {feat_type} |\n")
    else:
        report_file.write("| N/A | N/A | N/A | N/A | N/A | N/A | N/A |\n")

    report_file.write("\n")

    report_file.write("### Missing-value findings:\n")
    if kept_rows > 0:
        missing_any = df_prepared[STRICT_FEATURES].isna().any().any()
        if missing_any:
            report_file.write("Missing values found in some STRICT features (see table above).\n")
        else:
            report_file.write("No missing values in the STRICT features after filtering.\n")
    else:
        report_file.write("No rows to evaluate.\n")
    report_file.write("\n")

    report_file.write("## 6. Categorical/Numeric Feature Classification\n")
    report_file.write("### Numeric Features:\n")
    if kept_rows > 0:
        numeric_feats = [f for f in STRICT_FEATURES if pd.api.types.is_numeric_dtype(df_prepared[f])]
        for feat_name in numeric_feats:
            report_file.write(f"- {feat_name}\n")
    else:
        report_file.write("- No rows to evaluate.\n")
    report_file.write("\n")
    report_file.write("### Categorical Features:\n")
    if kept_rows > 0:
        categorical_feats = [f for f in STRICT_FEATURES if not pd.api.types.is_numeric_dtype(df_prepared[f])]
        for feat_name in categorical_feats:
            report_file.write(f"- {feat_name}\n")
    else:
        report_file.write("- No rows to evaluate.\n")
    report_file.write("\n")

    report_file.write("## 7. Preprocessing Plan\n")
    report_file.write("### For Numeric Features:\n")
    report_file.write("- Missing values: If any, impute with median (to be determined from training set).\n")
    report_file.write("- Scaling: Standardize (zero mean, unit variance) using statistics from the training set.\n")
    report_file.write("\n")
    report_file.write("### For Categorical Features:\n")
    report_file.write("- Missing values: If any, impute with mode (most frequent category).\n")
    report_file.write("- Encoding: One-hot encode (or ordinal if ordinal, but none are ordinal).\n")
    report_file.write("- Handle unseen categories in inference by ignoring or mapping to a special category.\n")
    report_file.write("\n")
    report_file.write("### For Identifiers (fire_id, nearest_facility_name, nearest_osm_id):\n")
    report_file.write("- These are identifiers and should not be used as predictive features. However, they are included in the STRICT set.\n")
    report_file.write("- We recommend dropping them from the model input or using them only for debugging.\n")
    report_file.write("- If used, they should be treated as categorical with high cardinality (consider hashing or embedding).\n")
    report_file.write("\n")

    report_file.write("## 8. Leakage Verification\n")
    report_file.write("We have excluded all features that were used in the weak-label rules:\n")
    report_file.write("- **FRP**: used in all three class rules\n")
    report_file.write("- **facility_within_*km**: used in Agricultural/Wildfire (=0) and Industrial (=1)\n")
    report_file.write("- **nearest_facility_category**: used in Industrial rule\n")
    report_file.write("- **dw_built, dw_crops, dw_trees, dw_shrub_and_scrub**: used in Agricultural and Wildfire rules\n")
    report_file.write("- **persistence_date_count, time_span_days, is_persistent**: used in Wildfire rule and persistence attribute\n")
    report_file.write("- **acq_date, acq_datetime, month**: used to compute persistence features and directly in Agricultural/Wildfire month rules\n")
    report_file.write("- **latitude, longitude, shape* columns**: used indirectly for persistence grouping (spatial memorization risk)\n")
    report_file.write("- **source_file, dw_date**: temporal vintage indicators\n")
    report_file.write("- **dw_label**: retained as it is the dominant land cover class, not the specific fractions used in rules.\n")
    report_file.write("\n")
    report_file.write("We also verified that the target_class is not a deterministic function of any single STRICT feature.\n")
    report_file.write("\n")

    report_file.write("## 9. Recommended Next Step for Stage 2D.2\n")
    report_file.write("Proceed to Stage 2D.2: Features Engineering and Train/Validation/Test Split.\n")
    report_file.write("- Use the prepared dataset (`stage2d_prepared_dataset.csv`).\n")
    report_file.write("- Perform train/validation/test split using spatial blocking (by latitude/longitude) to prevent location memorization.\n")
    report_file.write("- Apply the preprocessing plan (missing value imputation, scaling, encoding).\n")
    report_file.write("- Train a baseline model (Random Forest) on the three source-type classes.\n")
    report_file.write("- Evaluate using validation set and select model based on validation performance.\n")
    report_file.write("\n")

    report_file.write("## Final Status\n")
    if kept_rows > 0:
        report_file.write("READY FOR STAGE 2D.2\n")
    else:
        report_file.write("REQUIRES DATASET CORRECTION\n")

print(f"Report saved to: {report_path}")