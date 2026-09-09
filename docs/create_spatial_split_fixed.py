import pandas as pd
import numpy as np
import os

# Paths
weak_labels_path = r"C:\ProjectX\SIH26162\docs\FireGuard_WEAKLABELS_FIXED.csv"
prepared_dataset_path = r"C:\ProjectX\SIH26162\docs\stage2d\stage2d_prepared_dataset_fixed.csv"
stage2d_dir = r"C:\ProjectX\SIH26162\docs\stage2d"
train_path = os.path.join(stage2d_dir, "train.csv")
validation_path = os.path.join(stage2d_dir, "validation.csv")
test_path = os.path.join(stage2d_dir, "test.csv")

# Load the prepared dataset (to get the row order and indices)
print(f"Loading prepared dataset from {prepared_dataset_path}")
df_prepared = pd.read_csv(prepared_dataset_path)
print(f"Loaded {len(df_prepared)} rows from prepared dataset")

# Load the weak labels to get latitude/longitude for spatial grouping
print(f"Loading weak labels from {weak_labels_path}")
df_weak = pd.read_csv(weak_labels_path)
print(f"Loaded {len(df_weak)} rows from weak labels")

# Verify they have the same number of rows and same fire_id order
assert len(df_prepared) == len(df_weak), "Row count mismatch between datasets"
assert (df_prepared['fire_id'].values == df_weak['fire_id'].values).all(), "fire_id order mismatch"

# Create spatial blocks of 0.2 degrees using latitude/longitude from weak labels
print("Creating spatial blocks (0.2°)...")
df_weak['lat_block'] = (df_weak['latitude'] // 0.2) * 0.2
df_weak['lon_block'] = (df_weak['longitude'] // 0.2) * 0.2
# Combine into a block identifier
df_weak['block_id'] = df_weak['lat_block'].astype(str) + "_" + df_weak['lon_block'].astype(str)

# Get unique blocks
unique_blocks = df_weak['block_id'].unique()
print(f"Number of unique 0.2° blocks: {len(unique_blocks)}")

# Shuffle the blocks for random assignment
np.random.seed(42)  # for reproducibility
shuffled_blocks = np.random.permutation(unique_blocks)

# Split: 70% train, 15% validation, 15% test
n_blocks = len(shuffled_blocks)
n_train = int(0.7 * n_blocks)
n_val = int(0.15 * n_blocks)
# The rest goes to test

train_blocks = shuffled_blocks[:n_train]
val_blocks = shuffled_blocks[n_train:n_train + n_val]
test_blocks = shuffled_blocks[n_train + n_val:]

print(f"Train blocks: {len(train_blocks)}")
print(f"Validation blocks: {len(val_blocks)}")
print(f"Test blocks: {len(test_blocks)}")

# Assign each row to a set based on its block
df_weak['set'] = np.where(df_weak['block_id'].isin(train_blocks), 'train',
                          np.where(df_weak['block_id'].isin(val_blocks), 'validation', 'test'))

# Now split the prepared dataset using the same indices
train_indices = df_weak[df_weak['set'] == 'train'].index
val_indices = df_weak[df_weak['set'] == 'validation'].index
test_indices = df_weak[df_weak['set'] == 'test'].index

train_df = df_prepared.loc[train_indices].copy()
val_df = df_prepared.loc[val_indices].copy()
test_df = df_prepared.loc[test_indices].copy()

print(f"\nSplit sizes:")
print(f"  Train: {len(train_df)} rows")
print(f"  Validation: {len(val_df)} rows")
print(f"  Test: {len(test_df)} rows")

# Save to CSV
train_df.to_csv(train_path, index=False)
val_df.to_csv(validation_path, index=False)
test_df.to_csv(test_path, index=False)

print(f"\nSaved:")
print(f"  Train: {train_path}")
print(f"  Validation: {validation_path}")
print(f"  Test: {test_path}")

# Also, let's check the class distribution in each set
print("\nClass distribution in each set:")
for set_name, set_df in [('train', train_df), ('validation', val_df), ('test', test_df)]:
    if len(set_df) > 0:
        dist = set_df['target_class'].value_counts()
        print(f"  {set_name}:")
        for cls, count in dist.items():
            print(f"    {cls}: {count} ({count/len(set_df)*100:.2f}%)")
    else:
        print(f"  {set_name}: 0 rows")

print("\nSpatial split complete.")