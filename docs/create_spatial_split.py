import pandas as pd
import numpy as np
import os

# Paths
prepared_dataset_path = r"C:\ProjectX\SIH26162\docs\stage2d\stage2d_prepared_dataset_fixed.csv"
stage2d_dir = r"C:\ProjectX\SIH26162\docs\stage2d"
train_path = os.path.join(stage2d_dir, "train.csv")
validation_path = os.path.join(stage2d_dir, "validation.csv")
test_path = os.path.join(stage2d_dir, "test.csv")

# Load the prepared dataset
print(f"Loading prepared dataset from {prepared_dataset_path}")
df = pd.read_csv(prepared_dataset_path)
print(f"Loaded {len(df)} rows")

# Create spatial blocks of 0.2 degrees
# We'll floor the latitude and longitude to the nearest 0.2 degree
df['lat_block'] = (df['latitude'] // 0.2) * 0.2
df['lon_block'] = (df['longitude'] // 0.2) * 0.2
# Combine into a block identifier
df['block_id'] = df['lat_block'].astype(str) + "_" + df['lon_block'].astype(str)

# Get unique blocks
unique_blocks = df['block_id'].unique()
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
df['set'] = np.where(df['block_id'].isin(train_blocks), 'train',
                     np.where(df['block_id'].isin(val_blocks), 'validation', 'test'))

# Split the data
train_df = df[df['set'] == 'train'].copy()
val_df = df[df['set'] == 'validation'].copy()
test_df = df[df['set'] == 'test'].copy()

# Drop the helper columns
train_df = train_df.drop(columns=['lat_block', 'lon_block', 'block_id', 'set'])
val_df = val_df.drop(columns=['lat_block', 'lon_block', 'block_id', 'set'])
test_df = test_df.drop(columns=['lat_block', 'lon_block', 'block_id', 'set'])

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