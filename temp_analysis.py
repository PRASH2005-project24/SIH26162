import pandas as pd
import numpy as np
from datetime import datetime
import os

# Verify the dataset
csv_path = r"C:\ProjectX\SIH26162\docs\FireGuard_MASTER.csv"
print("Verifying dataset...")
print(f"File exists: {os.path.exists(csv_path)}")
print(f"File size: {os.path.getsize(csv_path) / (1024*1024):.2f} MB")

# First, let's get the column names and basic info without loading the entire file
# We'll read the first few rows to get the columns and data types
df_sample = pd.read_csv(csv_path, nrows=5)
print("\nColumns:", list(df_sample.columns))
print("\nData types from sample:")
print(df_sample.dtypes)

# Now we'll do a full pass in chunks to compute statistics
chunksize = 50000
total_rows = 0

# We'll accumulate statistics for various fields
# For categorical fields, we'll collect value counts
# For numerical fields, we'll collect min, max, sum, sum of squares for mean and std

# Initialize accumulators
# We'll do this for a set of key features first

# Define feature groups
firms_thermal = ['frp', 'bright_ti4', 'bright_ti5', 'scan', 'track']
# confidence is categorical but we'll treat it as such
spatial_context = ['latitude', 'longitude', 'nearest_facility_distance_km', 'nearest_osm_id',
                   'facility_within_1km', 'facility_within_5km', 'facility_within_10km']
dynamic_world = ['dw_bare', 'dw_built', 'dw_confidence', 'dw_crops', 'dw_difference',
                 'dw_flooded_vegetation', 'dw_grass', 'dw_label', 'dw_shrub_and_scrub',
                 'dw_snow_and_ice', 'dw_trees', 'dw_water']
temporal = ['acq_date', 'acq_datetime']  # we'll parse these
categorical = ['satellite', 'instrument', 'confidence', 'version', 'daynight',
               'nearest_facility_category', 'nearest_facility_name', 'source_satellite',
               'source_file', 'shapeName', 'shapeISO', 'shapeID', 'shapeGroup', 'shapeType']

# We'll also need to compute persistence later, which requires grouping by space and time.
# For now, we'll focus on distributions and bivariate relationships.

# Let's create dictionaries to hold our statistics
# For numerical columns: we'll store sum, sum of squares, min, max, count of non-null
# For categorical: we'll store a dictionary of counts

num_cols = firms_thermal + spatial_context + dynamic_world
cat_cols = categorical

# Initialize accumulators for numerical
num_stats = {col: {'sum': 0.0, 'sum_sq': 0.0, 'min': float('inf'), 'max': float('-inf'), 'count': 0}
             for col in num_cols}

# For categorical, we'll use a dict of dicts
cat_counts = {col: {} for col in cat_cols}

# We'll also collect some specific distributions we need for rule discovery
# For example, we want to know for each facility category, the distribution of distance, FRP, etc.
# We'll do this in a second pass or by collecting joint counts? That might be too heavy.
# Instead, we'll do a pass that collects:
#   - For each row, we note the facility category and then update stats for that category?
#   But that would require storing per-category stats, which might be okay if categories are few.

# Let's first get the unique facility categories from a small sample to know what we're dealing with.
print("\nGetting unique facility categories from a sample...")
df_cat_sample = pd.read_csv(csv_path, usecols=['nearest_facility_category'])
unique_cats = df_cat_sample['nearest_facility_category'].dropna().unique()
print(f"Unique facility categories (non-null): {unique_cats}")
print(f"Number of unique facility categories: {len(unique_cats)}")

# We'll also get unique dw_label values (which are numeric but we treat as categorical for land cover)
dw_label_sample = pd.read_csv(csv_path, usecols=['dw_label'])
unique_dw_label = dw_label_sample['dw_label'].dropna().unique()
print(f"Unique dw_label values: {unique_dw_label}")

# Now, we'll do a pass over the data to compute:
#   - Overall statistics for numerical columns
#   - Counts for categorical columns
#   - For facility category, we'll also compute conditional stats (e.g., median distance per category)
#     but we'll do that in a second pass to avoid too much complexity in one pass.

# We'll do two passes:
#   Pass 1: Overall numerical and categorical counts
#   Pass 2: For each facility category, compute stats of associated numerical features

# However, to save time, we'll do one pass that collects:
#   - For numerical: overall stats
#   - For categorical: counts
#   - For facility category: we'll also collect the sum, count, etc. of associated numerical features per category?
#     That would require a dictionary of dictionaries, which might be heavy but the number of categories is small.

# Let's try to do it in one pass for the facility category and a few key numerical features.

# We'll focus on: distance, FRP, dw_built, dw_crops, dw_trees for each facility category.

# We'll create a dict for each facility category that we encounter, storing:
#   count, sum_distance, sum_frp, sum_dw_built, sum_dw_crops, sum_dw_trees
#   and also min, max if needed.

# But note: we also need to compute medians and percentiles, which we cannot do exactly in one pass without storing all values.
# We'll approximate median by using the midpoint of min and max? Not good.
# Alternatively, we can store all values for a sample? Or we can use iterative methods? Too complex.

# Given the constraints, we'll compute approximate statistics (mean, std) and then for percentiles we'll do a separate pass
# or we'll use the chunked data to approximate percentiles by storing a sample? We'll do a reservoir sample for each category?
# That might be too heavy.

# Let's change strategy: we'll do a pass that collects the overall distribution of key features and then
# we'll do a second pass that focuses on facility category by filtering the data for each category?
# But that would require reading the entire file multiple times.

# Considering the file is 328 MB, reading it a few times is acceptable.

# We'll do:
#   Pass 1: Basic verification and overall distributions (categorical counts, numerical moments)
#   Pass 2: For each facility category, we'll extract the rows for that category and compute statistics.
#           We'll do this by reading the file in chunks and selecting rows where the category matches.

# But note: there are about 8 facility categories (from the earlier audit). So 8 passes over the data is 8 * 328 MB = ~2.6 GB, which is acceptable.

# Let's proceed.

# First, let's do Pass 1: overall statistics.

print("\n=== PASS 1: Overall statistics ===")

# We'll reset the accumulators
num_stats = {col: {'sum': 0.0, 'sum_sq': 0.0, 'min': float('inf'), 'max': float('-inf'), 'count': 0}
             for col in num_cols}
cat_counts = {col: {} for col in cat_cols}

# We'll also count missing values
missing_counts = {col: 0 for col in num_cols + cat_cols}

# We'll also compute the date range for acq_datetime
date_min = pd.Timestamp.max
date_max = pd.Timestamp.min

# We'll also count rows
total_rows = 0

# We'll also compute the distribution of confidence values (which are strings)
# and daynight

# Let's iterate over chunks
chunk_iter = pd.read_csv(csv_path, chunksize=chunksize)
for i, chunk in enumerate(chunk_iter):
    total_rows += len(chunk)
    if i % 10 == 0:
        print(f"  Processed {total_rows} rows...")

    # Process numerical columns
    for col in num_cols:
        if col in chunk.columns:
            col_data = chunk[col].dropna()
            if len(col_data) > 0:
                num_stats[col]['sum'] += col_data.sum()
                num_stats[col]['sum_sq'] += (col_data ** 2).sum()
                num_stats[col]['min'] = min(num_stats[col]['min'], col_data.min())
                num_stats[col]['max'] = max(num_stats[col]['max'], col_data.max())
                num_stats[col]['count'] += len(col_data)
            missing_counts[col] += len(chunk) - len(col_data)

    # Process categorical columns
    for col in cat_cols:
        if col in chunk.columns:
            col_data = chunk[col].dropna()
            for val in col_data:
                cat_counts[col][val] = cat_counts[col].get(val, 0) + 1
            missing_counts[col] += len(chunk) - len(col_data)

    # Process acq_datetime for date range
    if 'acq_datetime' in chunk.columns:
        # Convert to datetime, coercing errors
        dt_series = pd.to_datetime(chunk['acq_datetime'], errors='coerce')
        valid_dts = dt_series.dropna()
        if len(valid_dts) > 0:
            date_min = min(date_min, valid_dts.min())
            date_max = max(date_max, valid_dts.max())

print(f"\nTotal rows processed: {total_rows}")

# Compute mean and std for numerical columns
print("\n=== Numerical Feature Statistics ===")
for col in num_cols:
    if num_stats[col]['count'] > 0:
        mean = num_stats[col]['sum'] / num_stats[col]['count']
        # variance = E[X^2] - E[X]^2
        variance = (num_stats[col]['sum_sq'] / num_stats[col]['count']) - (mean ** 2)
        std = np.sqrt(variance) if variance >= 0 else 0.0
        print(f"{col}: count={num_stats[col]['count']}, missing={missing_counts[col]}, "
              f"mean={mean:.4f}, std={std:.4f}, min={num_stats[col]['min']:.4f}, max={num_stats[col]['max']:.4f}")
    else:
        print(f"{col}: all missing")

print("\n=== Categorical Feature Statistics (top 5) ===")
for col in cat_cols:
    if cat_counts[col]:
        # Sort by count descending
        sorted_items = sorted(cat_counts[col].items(), key=lambda x: x[1], reverse=True)
        print(f"{col}: missing={missing_counts[col]}, unique values={len(cat_counts[col])}")
        print(f"  Top 5: {sorted_items[:5]}")
    else:
        print(f"{col}: all missing")

print(f"\nDate range for acq_datetime: {date_min} to {date_max}")

# Now, Pass 2: For each facility category, compute statistics of associated features
print("\n=== PASS 2: Facility Category Analysis ===")

# We'll focus on the facility categories we saw in the earlier audit (from the unique_cats list)
# But we'll get the unique categories from the entire dataset in this pass? We'll just use the ones we saw.
# However, we should get the unique categories from the entire dataset to be safe.
# We'll do a quick pass to get all unique facility categories (non-null) and then iterate over them.

# Let's get the unique facility categories from the entire dataset (but we can do it in the same pass as above?
# We already have cat_counts for 'nearest_facility_category', so we can use that.

facility_cats = [cat for cat in cat_counts['nearest_facility_category'].keys() if pd.notnull(cat)]
print(f"Facility categories to analyze: {facility_cats}")

# For each facility category, we want to compute:
#   - Number of rows (events) associated with that category
#   - For each of: distance, FRP, dw_built, dw_crops, dw_trees: mean, std, min, max, percentiles (we'll do approximate percentiles by storing a sample?
#     Instead, we'll compute the exact percentiles by collecting all values for that category? That might be too heavy if there are many rows per category.
#     We'll do: for each category, we'll collect the values in a list and then compute percentiles? But the list could be large.
#     We'll do a compromise: we'll compute the mean and std and then approximate the median by assuming symmetry? Not good.
#     Alternatively, we can use an online algorithm for percentiles? There are libraries but we don't have them.
#     We'll do: we'll store the values for each category in a list only if the category has less than, say, 10000 rows?
#     Otherwise, we'll skip the percentiles and just report mean and std.

# Given the time, we'll compute mean, std, min, max and leave percentiles for later if needed.

# We'll create a dictionary to hold the stats for each facility category
facility_stats = {}

# We'll iterate over the data again, but this time we'll accumulate per facility category
# We'll reset the accumulators for each category? Actually, we'll do one pass and update the stats for the category of each row.

# Let's initialize for each category: we'll have a dict for the numerical features we care about.
features_of_interest = ['nearest_facility_distance_km', 'frp', 'dw_built', 'dw_crops', 'dw_trees']

# We'll create a nested dict: facility_stats[category][feature] = {'sum':0, 'sum_sq':0, 'min':inf, 'max':-inf, 'count':0}
facility_stats = {cat: {feat: {'sum': 0.0, 'sum_sq': 0.0, 'min': float('inf'), 'max': float('-inf'), 'count': 0}
                        for feat in features_of_interest}
                  for cat in facility_cats}

# We'll also count the number of rows per category
cat_row_counts = {cat: 0 for cat in facility_cats}

# We'll also count missing values per feature per category? We'll just count the non-null.

# Now, iterate over the data in chunks
chunk_iter = pd.read_csv(csv_path, chunksize=chunksize)
for i, chunk in enumerate(chunk_iter):
    if i % 10 == 0:
        print(f"  Processed {total_rows} rows for facility stats...")

    # For each row, we need to know its facility category (if not null) and then update the stats for that category
    # We'll iterate over the rows? That would be slow. Instead, we'll group by facility category in the chunk?
    # We'll do: for each facility category present in the chunk, we'll extract the subset and update the stats.

    # First, let's get the facility category column
    if 'nearest_facility_category' not in chunk.columns:
        continue

    # We'll drop rows where facility category is null for this analysis
    chunk_facility = chunk.dropna(subset=['nearest_facility_category'])

    # Group by facility category
    grouped = chunk_facility.groupby('nearest_facility_category')

    for cat, group in grouped:
        if cat not in facility_cats:
            # We might encounter a category not in our list (if we missed some in the cat_counts)
            # We'll skip it for now, or we could add it to our list? Let's skip to keep it simple.
            continue

        cat_row_counts[cat] += len(group)

        for feat in features_of_interest:
            if feat in group.columns:
                feat_data = group[feat].dropna()
                if len(feat_data) > 0:
                    stats = facility_stats[cat][feat]
                    stats['sum'] += feat_data.sum()
                    stats['sum_sq'] += (feat_data ** 2).sum()
                    stats['min'] = min(stats['min'], feat_data.min())
                    stats['max'] = max(stats['max'], feat_data.max())
                    stats['count'] += len(feat_data)

print("\n=== Facility Category Statistics ===")
for cat in facility_cats:
    print(f"\nCategory: {cat} (row count: {cat_row_counts[cat]})")
    for feat in features_of_interest:
        stats = facility_stats[cat][feat]
        if stats['count'] > 0:
            mean = stats['sum'] / stats['count']
            variance = (stats['sum_sq'] / stats['count']) - (mean ** 2)
            std = np.sqrt(variance) if variance >= 0 else 0.0
            print(f"  {feat}: count={stats['count']}, mean={mean:.4f}, std={std:.4f}, min={stats['min']:.4f}, max={stats['max']:.4f}")
        else:
            print(f"  {feat}: no data")

# Now, let's also look at the Dynamic World label distribution and its relationship with facility category
# We'll do a similar analysis for dw_label (which is numeric but we treat as land cover class)
# We'll compute the distribution of dw_label values (as integers) and then for each facility category, the mean dw_label, etc.

print("\n=== Dynamic World Label Analysis ===")
# We'll compute overall dw_label distribution and then per facility category

# We'll reuse the chunk iteration but we'll do it in a new pass for clarity?
# We'll do it in the same pass as above? We already have the overall dw_label distribution from Pass 1?
# Actually, we didn't compute dw_label in Pass 1 because it's in dynamic_world and we did compute numerical stats for it.
# So we have the overall mean, etc. for dw_label from Pass 1.

# Let's get the overall dw_label stats from Pass 1
if 'dw_label' in num_stats:
    stats = num_stats['dw_label']
    if stats['count'] > 0:
        mean = stats['sum'] / stats['count']
        variance = (stats['sum_sq'] / stats['count']) - (mean ** 2)
        std = np.sqrt(variance) if variance >= 0 else 0.0
        print(f"Overall dw_label: count={stats['count']}, missing={missing_counts['dw_label']}, "
              f"mean={mean:.4f}, std={std:.4f}, min={stats['min']:.4f}, max={stats['max']:.4f}")

# Now, let's compute the mean dw_label per facility category
# We'll do a similar accumulation as above but for dw_label

# Initialize for dw_label per facility category
dw_label_stats = {cat: {'sum': 0.0, 'count': 0} for cat in facility_cats}

# Iterate over chunks again
chunk_iter = pd.read_csv(csv_path, chunksize=chunksize)
for i, chunk in enumerate(chunk_iter):
    if i % 10 == 0:
        print(f"  Processed {total_rows} rows for dw_label stats...")

    if 'nearest_facility_category' not in chunk.columns or 'dw_label' not in chunk.columns:
        continue

    chunk_facility = chunk.dropna(subset=['nearest_facility_category', 'dw_label'])
    grouped = chunk_facility.groupby('nearest_facility_category')

    for cat, group in grouped:
        if cat not in facility_cats:
            continue
        dw_label_data = group['dw_label'].dropna()
        if len(dw_label_data) > 0:
            dw_label_stats[cat]['sum'] += dw_label_data.sum()
            dw_label_stats[cat]['count'] += len(dw_label_data)

print("\n=== Mean dw_label per Facility Category ===")
for cat in facility_cats:
    if dw_label_stats[cat]['count'] > 0:
        mean_dw_label = dw_label_stats[cat]['sum'] / dw_label_stats[cat]['count']
        print(f"{cat}: count={dw_label_stats[cat]['count']}, mean dw_label={mean_dw_label:.4f}")
    else:
        print(f"{cat}: no dw_label data")

# Now, let's look at the distribution of dw_label values (the actual integer-like values) overall
# We already have the numerical stats, but we want to see the distribution of the integer values.
# We'll do a pass to collect the counts of each dw_label value (treating it as categorical)

print("\n=== dw_label value distribution (treating as categorical) ===")
dw_label_counts = {}
chunk_iter = pd.read_csv(csv_path, chunksize=chunksize)
for i, chunk in enumerate(chunk_iter):
    if i % 10 == 0:
        print(f"  Processed {total_rows} rows for dw_label distribution...")
    if 'dw_label' in chunk.columns:
        dw_label_data = chunk['dw_label'].dropna()
        # Since dw_label is stored as float but represents integer classes, we'll round to nearest integer?
        # Actually, from the sample we saw, it's like 0.0, 1.0, etc. So we can convert to int by rounding.
        # But note: there might be fractional values? We'll treat the float as is and then bin?
        # We'll just use the float value and count occurrences of each exact float?
        # But due to floating point, we might get many unique values. Instead, we'll round to 2 decimal places.
        dw_label_rounded = dw_label_data.round(2)
        for val in dw_label_rounded:
            dw_label_counts[val] = dw_label_counts.get(val, 0) + 1

# Sort the dw_label counts by value
sorted_dw_label = sorted(dw_label_counts.items(), key=lambda x: x[0])
print(f"dw_label distribution (rounded to 2 decimals):")
for val, count in sorted_dw_label:
    print(f"  {val}: {count} ({count/total_rows*100:.2f}%)")

# Now, let's do some bivariate analysis for rule discovery:
# For example, we want to see the relationship between dw_crops and dw_built, etc.

# We'll compute the correlation matrix for a set of features? But we'll do it in a pass that collects the necessary moments.
# However, we already have the sum and sum of squares for each feature, but we need the sum of products for pairs.
# We'll do a pass to compute the covariance matrix for a subset of features.

# Let's define a set of features for which we want to compute correlations:
corr_features = ['frp', 'dw_built', 'dw_crops', 'dw_trees', 'nearest_facility_distance_km']
# We'll also include latitude and longitude? Maybe not.

# We'll compute the mean and covariance matrix.

# We'll initialize:
n_features = len(corr_features)
sums = {feat: 0.0 for feat in corr_features}
sums_sq = {feat: 0.0 for feat in corr_features}
sums_prod = {(f1, f2): 0.0 for f1 in corr_features for f2 in corr_features if f1 <= f2}
counts = {feat: 0 for feat in corr_features}

# Iterate over chunks
chunk_iter = pd.read_csv(csv_path, chunksize=chunksize)
for i, chunk in enumerate(chunk_iter):
    if i % 10 == 0:
        print(f"  Processed {total_rows} rows for correlation matrix...")

    # Extract the subset of features
    subset = chunk[corr_features].dropna()
    if len(subset) == 0:
        continue

    # Update sums and sums of squares
    for feat in corr_features:
        feat_data = subset[feat]
        sums[feat] += feat_data.sum()
        sums_sq[feat] += (feat_data ** 2).sum()
        counts[feat] += len(feat_data)

    # Update sums of products
    for idx, f1 in enumerate(corr_features):
        for f2 in corr_features[idx:]:  # to avoid duplicate pairs
            prod_data = subset[f1] * subset[f2]
            sums_prod[(f1, f2)] += prod_data.sum()

# Now compute means, variances, and covariances
means = {feat: sums[feat] / counts[feat] for feat in corr_features if counts[feat] > 0}
variances = {}
for feat in corr_features:
    if counts[feat] > 0:
        mean = means[feat]
        variances[feat] = (sums_sq[feat] / counts[feat]) - (mean ** 2)
    else:
        variances[feat] = 0.0

# Covariance matrix
cov = {}
for (f1, f2) in sums_prod:
    if counts[f1] > 0 and counts[f2] > 0:
        mean1 = means[f1]
        mean2 = means[f2]
        cov[(f1, f2)] = (sums_prod[(f1, f2)] / counts[f1]) - (mean1 * mean2)  # Note: we used counts[f1] but should be the same for both?
        # Actually, we stored the sum of products for the pairs that are present in the subset (which has no missing values for either).
        # So the count for the pair is the number of rows where both f1 and f2 are present, which is the same as counts[f1] and counts[f2] in the subset?
        # But we have been updating counts for each feature independently, which counts rows where the feature is present (even if the other is missing?).
        # In our subset, we dropped rows where any of the features is missing, so the count for each feature in the subset is the same.
        # However, we updated counts[feat] for every row in the subset, so counts[feat] is the number of rows in the subset for that feature.
        # And since we used the same subset for all features, the counts[feat] should be the same for all features?
        # Not exactly: if a row has a missing value for one feature but not the other, it would be dropped from the subset, so the subset only has rows with all features present.
        # Therefore, in the subset, the count for each feature is the same (the number of rows in the subset).
        # We'll use n = counts[corr_features[0]] (if it's >0) as the number of rows in the subset.
        n = counts[corr_features[0]] if counts[corr_features[0]] > 0 else 1
        cov[(f1, f2)] = (sums_prod[(f1, f2)] / n) - (means[f1] * means[f2])
    else:
        cov[(f1, f2)] = 0.0

# Now compute correlation matrix
print("\n=== Correlation Matrix ===")
print("Features:", corr_features)
# Print header
header = " " * 12
for feat in corr_features:
    header += f"{feat:>12}"
print(header)
for f1 in corr_features:
    row = f"{f1:>12}"
    for f2 in corr_features:
        if f1 <= f2:
            c = cov.get((f1, f2), 0.0)
        else:
            c = cov.get((f2, f1), 0.0)
        # Avoid division by zero
        if variances[f1] > 0 and variances[f2] > 0:
            corr = c / np.sqrt(variances[f1] * variances[f2])
        else:
            corr = 0.0
        row += f"{corr:>12.3f}"
    print(row)

# Now, let's do some analysis for rule discovery by looking at the distribution of features for different classes of events.
# For example, we want to see the distribution of FRP for events near industrial facilities vs. not.

# We'll do a pass to compute the mean FRP for events with facility_within_1km=1 and facility_within_1km=0, etc.

print("\n=== Bivariate Analysis for Rule Discovery ===")

# We'll compute:
#   - Mean FRP by facility_within_1km
#   - Mean dw_crops by facility_within_1km
#   - etc.

# We'll initialize accumulators for these group statistics.

# Let's define some grouping variables:
grouping_vars = ['facility_within_1km', 'facility_within_5km', 'facility_within_10km']
# We'll also consider the facility category? We'll do that separately.

# For each grouping variable, we want to compute the mean of certain target features.
target_features = ['frp', 'dw_built', 'dw_crops', 'dw_trees', 'nearest_facility_distance_km']

# We'll create a dict: group_stats[grouping_var][group_value][target_feature] = {'sum':0, 'count':0}
group_stats = {}
for gv in grouping_vars:
    group_stats[gv] = {}
    # The grouping variables are binary (0/1) but we'll treat them as categorical
    group_stats[gv][0] = {feat: {'sum': 0.0, 'count': 0} for feat in target_features}
    group_stats[gv][1] = {feat: {'sum': 0.0, 'count': 0} for feat in target_features}

# Iterate over chunks
chunk_iter = pd.read_csv(csv_path, chunksize=chunksize)
for i, chunk in enumerate(chunk_iter):
    if i % 10 == 0:
        print(f"  Processed {total_rows} rows for group stats...")

    for gv in grouping_vars:
        if gv not in chunk.columns:
            continue
        # Ensure the grouping variable is integer (0 or 1)
        # We'll drop rows where the grouping variable is missing
        chunk_gv = chunk.dropna(subset=[gv])
        # Convert to int (should already be 0 or 1)
        chunk_gv[gv] = chunk_gv[gv].astype(int)

        for group_val in [0, 1]:
            group_chunk = chunk_gv[chunk_gv[gv] == group_val]
            for feat in target_features:
                if feat in group_chunk.columns:
                    feat_data = group_chunk[feat].dropna()
                    if len(feat_data) > 0:
                        stats = group_stats[gv][group_val][feat]
                        stats['sum'] += feat_data.sum()
                        stats['count'] += len(feat_data)

# Now compute and print the means
print("\n=== Group Means ===")
for gv in grouping_vars:
    print(f"\nGrouping by {gv}:")
    for group_val in [0, 1]:
        print(f"  {gv} = {group_val}:")
        for feat in target_features:
            stats = group_stats[gv][group_val][feat]
            if stats['count'] > 0:
                mean = stats['sum'] / stats['count']
                print(f"    {feat}: mean={mean:.4f} (count={stats['count']})")
            else:
                print(f"    {feat}: no data")

# Now, let's look at the distribution of nearest_facility_distance_km for each facility category
# We already have that in facility_stats, but we'll also compute the proportion of events within certain distance thresholds.

print("\n=== Distance Threshold Analysis per Facility Category ===")
# We'll compute, for each facility category, the proportion of events within 0.1km, 0.25km, 0.5km, 1km, 2km.
# We'll do this by accumulating counts per category and per threshold.

thresholds = [0.1, 0.25, 0.5, 1.0, 2.0]
# Initialize: dist_thresh_stats[cat][thresh] = {'count_within':0, 'total_count':0}
dist_thresh_stats = {cat: {thresh: {'count_within': 0, 'total_count': 0} for thresh in thresholds}
                     for cat in facility_cats}

# Iterate over chunks
chunk_iter = pd.read_csv(csv_path, chunksize=chunksize)
for i, chunk in enumerate(chunk_iter):
    if i % 10 == 0:
        print(f"  Processed {total_rows} rows for distance thresholds...")

    if 'nearest_facility_category' not in chunk.columns or 'nearest_facility_distance_km' not in chunk.columns:
        continue

    chunk_facility = chunk.dropna(subset=['nearest_facility_category', 'nearest_facility_distance_km'])
    # We'll iterate over rows? We'll do vectorized operations per chunk.
    for cat in facility_cats:
        mask_cat = chunk_facility['nearest_facility_category'] == cat
        if mask_cat.any():
            subset = chunk_facility[mask_cat]
            total = len(subset)
            dist_thresh_stats[cat]['total_count'] += total  # but note: we are doing per chunk, so we'll accumulate
            for thresh in thresholds:
                within = (subset['nearest_facility_distance_km'] <= thresh).sum()
                dist_thresh_stats[cat][thresh]['count_within'] += within

# Now compute proportions
print("\n=== Proportion of events within distance thresholds per facility category ===")
for cat in facility_cats:
    print(f"\nCategory: {cat}")
    total = dist_thresh_stats[cat]['total_count']
    if total > 0:
        for thresh in thresholds:
            within = dist_thresh_stats[cat][thresh]['count_within']
            proportion = within / total if total > 0 else 0
            print(f"  Within {thresh} km: {within}/{total} = {proportion:.2%}")
    else:
        print(f"  No data")

# Now, let's look at the temporal distribution: month of acquisition
# We'll extract the month from acq_datetime and see if there are seasonal patterns.

print("\n=== Temporal Analysis (month) ===")
# We'll compute the count of events per month
month_counts = {m: 0 for m in range(1, 13)}
# We'll also compute per month the mean FRP, etc. if needed.

chunk_iter = pd.read_csv(csv_path, chunksize=chunksize)
for i, chunk in enumerate(chunk_iter):
    if i % 10 == 0:
        print(f"  Processed {total_rows} rows for monthly stats...")

    if 'acq_datetime' not in chunk.columns:
        continue

    # Convert to datetime
    chunk['acq_datetime'] = pd.to_datetime(chunk['acq_datetime'], errors='coerce')
    # Drop NaT
    chunk_dt = chunk.dropna(subset=['acq_datetime'])
    if len(chunk_dt) == 0:
        continue

    # Extract month
    months = chunk_dt['acq_datetime'].dt.month
    for m in months:
        month_counts[m] = month_counts.get(m, 0) + 1

print("\n=== Events per month ===")
for m in range(1, 13):
    count = month_counts.get(m, 0)
    print(f"Month {m}: {count} events ({count/total_rows*100:.2f}%)")

# Now, let's do some analysis for the persistent thermal source: we want to see how many detections per location.
# We'll do a spatial binning (e.g., 0.01 degree) and count the number of unique dates per bin.
# This is more complex and might be memory intensive if we store all the points.
# We'll do a pass that builds a dictionary mapping (lat_bin, lon_bin) to a set of dates?
# But storing sets of dates for each bin could be heavy.
# Instead, we'll do: we'll compute the number of detections per bin and the number of unique dates per bin by using two passes?
#   First pass: count detections per bin.
#   Second pass: for each bin that has more than one detection, we'll collect the dates and compute unique count.
# But we don't want to store all the points.

# We'll do an approximate method: we'll use a hash map that maps (lat_bin, lon_bin) to a list of dates, but we'll only store the list if the bin has a small number of detections?
# Alternatively, we can use probabilistic data structures like HyperLogLog for unique count, but we don't have that.

# Given the time, we'll do a simpler approach: we'll compute the number of detections per bin and then assume that if the count is high, it's likely persistent.
# We'll also compute the time span (max date - min date) per bin by storing the min and max datetime per bin.

# We'll initialize:
#   bin_counts: dict of (lat_bin, lon_bin) -> count
#   bin_min_dt: dict of (lat_bin, lon_bin) -> min datetime
#   bin_max_dt: dict of (lat_bin, lon_bin) -> max datetime

# We'll use a bin size of 0.01 degrees (about 1km at the equator).

print("\n=== Persistence Analysis (spatial binning) ===")
bin_size = 0.01
# We'll use dictionaries
bin_counts = {}
bin_min_dt = {}
bin_max_dt = {}

# We'll also count the total number of bins and the number of bins with multiple detections.

chunk_iter = pd.read_csv(csv_path, chunksize=chunksize)
for i, chunk in enumerate(chunk_iter):
    if i % 10 == 0:
        print(f"  Processed {total_rows} rows for persistence binning...")

    if 'latitude' not in chunk.columns or 'longitude' not in chunk.columns or 'acq_datetime' not in chunk.columns:
        continue

    # Drop rows with missing lat, lon, or datetime
    chunk_clean = chunk.dropna(subset=['latitude', 'longitude', 'acq_datetime'])
    if len(chunk_clean) == 0:
        continue

    # Convert datetime
    chunk_clean['acq_datetime'] = pd.to_datetime(chunk_clean['acq_datetime'], errors='coerce')
    chunk_clean = chunk_clean.dropna(subset=['acq_datetime'])
    if len(chunk_clean) == 0:
        continue

    # Compute bin indices
    lat_bin = (chunk_clean['latitude'] // bin_size).astype(int)
    lon_bin = (chunk_clean['longitude'] // bin_size).astype(int)

    # We'll create a tuple (lat_bin, lon_bin) for each row
    # We'll iterate over the rows? We'll do it in a loop over the chunk rows (which is acceptable because chunksize is 50k)
    for idx in range(len(chunk_clean)):
        lat = chunk_clean.iloc[idx]['latitude']
        lon = chunk_clean.iloc[idx]['longitude']
        dt = chunk_clean.iloc[idx]['acq_datetime']

        lat_bin_idx = int(lat // bin_size)
        lon_bin_idx = int(lon // bin_size)
        key = (lat_bin_idx, lon_bin_idx)

        # Update count
        bin_counts[key] = bin_counts.get(key, 0) + 1

        # Update min and max datetime
        if key in bin_min_dt:
            if dt < bin_min_dt[key]:
                bin_min_dt[key] = dt
            if dt > bin_max_dt[key]:
                bin_max_dt[key] = dt
        else:
            bin_min_dt[key] = dt
            bin_max_dt[key] = dt

# Now compute statistics
print(f"\nNumber of unique spatial bins (size {bin_size}°): {len(bin_counts)}")
if bin_counts:
    counts_list = list(bin_counts.values())
    print(f"Detections per bin: min={min(counts_list)}, max={max(counts_list)}, mean={np.mean(counts_list):.2f}, median={np.median(counts_list):.2f}")

    # Number of bins with more than one detection
    bins_multiple = sum(1 for c in counts_list if c > 1)
    print(f"Bins with >1 detection: {bins_multiple} ({bins_multiple/len(bin_counts)*100:.2f}%)")

    # Bins with >2 detections
    bins_gt2 = sum(1 for c in counts_list if c > 2)
    print(f"Bins with >2 detections: {bins_gt2} ({bins_gt2/len(bin_counts)*100:.2f}%)")

    # Compute time span for each bin
    time_spans = []
    for key in bin_counts:
        if key in bin_min_dt and key in bin_max_dt:
            span = bin_max_dt[key] - bin_min_dt[key]
            time_spans.append(span.total_seconds() / (3600*24))  # convert to days

    if time_spans:
        print(f"\nTime span per bin (days): min={min(time_spans):.2f}, max={max(time_spans):.2f}, mean={np.mean(time_spans):.2f}, median={np.median(time_spans):.2f}")

        # Bins with time span > 30 days
        bins_span_gt30 = sum(1 for s in time_spans if s > 30)
        print(f"Bins with time span >30 days: {bins_span_gt30} ({bins_span_gt30/len(time_spans)*100:.2f}%)")

        # Bins with time span > 365 days (roughly a year)
        bins_span_gt365 = sum(1 for s in time_spans if s > 365)
        print(f"Bins with time span >365 days: {bins_span_gt365} ({bins_span_gt365/len(time_spans)*100:.2f}%)")

# Now, let's also look at the persistence in terms of facility category: are persistent bins more likely to be near industrial facilities?
# We'll compute, for each bin that has multiple detections, the predominant facility category?
# We'll do a separate pass for that? Given time, we'll skip.

# Now, we have collected a lot of statistics. We'll use them to inform our rule discovery.

# Let's write a summary of our findings to a file that we can then use to create the report.
# But we are required to create the report directly.

# We'll now create the report Markdown file.

print("\n=== Creating the report ===")