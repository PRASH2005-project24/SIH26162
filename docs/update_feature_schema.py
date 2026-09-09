import json
import pandas as pd
import numpy as np
import os

# Paths
stage2d_dir = r"C:\ProjectX\SIH26162\docs\stage2d"
feature_schema_path = os.path.join(stage2d_dir, "feature_schema.json")
train_path = os.path.join(stage2d_dir, "train.csv")
validation_path = os.path.join(stage2d_dir, "validation.csv")
test_path = os.path.join(stage2d_dir, "test.csv")

# Load the current feature schema
with open(feature_schema_path, 'r') as f:
    feature_schema = json.load(f)

# Load the split datasets
train_df = pd.read_csv(train_path)
validation_df = pd.read_csv(validation_path)
test_df = pd.read_csv(test_path)

# Update split sizes
feature_schema['split_sizes'] = {
    'train': len(train_df),
    'validation': len(validation_df),
    'test': len(test_df)
}

# Update class distribution per split
def get_class_distribution(df):
    return df['target_class'].value_counts().to_dict()

feature_schema['class_distribution_per_split'] = {
    'train': get_class_distribution(train_df),
    'validation': get_class_distribution(validation_df),
    'test': get_class_distribution(test_df)
}

# The class distribution before split should be the same as the combined dataset (train+val+test)
combined_df = pd.concat([train_df, validation_df, test_df], ignore_index=True)
feature_schema['class_distribution_before_split'] = get_class_distribution(combined_df)

# Save the updated feature schema
with open(feature_schema_path, 'w') as f:
    json.dump(feature_schema, f, indent=2)

print(f"Updated feature schema at {feature_schema_path}")
print(f"Split sizes: {feature_schema['split_sizes']}")