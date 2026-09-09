import pandas as pd
import numpy as np
import os
import json
import time
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import warnings
warnings.filterwarnings('ignore')

# Paths
STAGE2D_DIR = r'C:\ProjectX\SIH26162\docs\stage2d'
TRAIN_PATH = os.path.join(STAGE2D_DIR, 'train.csv')
VALIDATION_PATH = os.path.join(STAGE2D_DIR, 'validation.csv')
FEATURE_SCHEMA_PATH = os.path.join(STAGE2D_DIR, 'feature_schema.json')
MODEL_DIR = os.path.join(STAGE2D_DIR, 'models')
os.makedirs(MODEL_DIR, exist_ok=True)

# Load feature schema
with open(FEATURE_SCHEMA_PATH, 'r') as f:
    feature_schema = json.load(f)

model_input_features = feature_schema['model_input_features']
numeric_features = feature_schema['numeric_features']
categorical_features = feature_schema['categorical_features']
target_class = feature_schema['target_class']
target_classes = feature_schema['target_classes']

print(f"Using {len(model_input_features)} model input features:")
print(f"  {model_input_features}")
print(f"Numeric features: {len(numeric_features)}")
print(f"Categorical features: {len(categorical_features)}")

# Verify no leakage features are present
leakage_features = ['dw_label', 'snpp_anomaly_flag']
for leak in leakage_features:
    if leak in model_input_features:
        print(f"!!! LEAKAGE DETECTED: {leak} is in model_input_features !!!")
    else:
        print(f"[OK] {leak} correctly excluded from model_input_features")

# Load training and validation data
print("\n=== Loading Training and Validation Data ===")
train_df = pd.read_csv(TRAIN_PATH)
val_df = pd.read_csv(VALIDATION_PATH)
print(f"Training rows: {len(train_df)}")
print(f"Validation rows: {len(val_df)}")

# Prepare features and target
X_train_raw = train_df[model_input_features]
y_train_raw = train_df[target_class]
X_val_raw = val_df[model_input_features]
y_val_raw = val_df[target_class]

# Encode target classes (fit on training data only)
label_encoder = LabelEncoder()
y_train = label_encoder.fit_transform(y_train_raw)
y_val = label_encoder.transform(y_val_raw)
print(f"Classes: {label_encoder.classes_}")
print(f"Class mapping: {dict(zip(label_encoder.classes_, range(len(label_encoder.classes_))))}")

# Compute class weights from training set only
class_counts = np.bincount(y_train)
total_samples = len(y_train)
class_weights = total_samples / (len(class_counts) * class_counts)
class_weights_dict = {i: class_weights[i] for i in range(len(class_counts))}
print(f"Class weights: {class_weights_dict}")

# Load preprocessing pipeline fitted on training data
print("\n=== Loading Preprocessing Pipeline (fitted on training data) ===")
preprocessor = joblib.load(os.path.join(MODEL_DIR, 'preprocessing_pipeline.joblib'))
print("Preprocessing pipeline loaded.")

# Transform training and validation data
X_train_processed = preprocessor.transform(X_train_raw)
X_val_processed = preprocessor.transform(X_val_raw)
print(f"Processed train shape: {X_train_processed.shape}")
print(f"Processed validation shape: {X_val_processed.shape}")

# Print some statistics about the processed data
print(f"\nProcessed train data stats:")
print(f"  Mean: {np.mean(X_train_processed):.6f}")
print(f"  Std:  {np.std(X_train_processed):.6f}")
print(f"  Min:  {np.min(X_train_processed):.6f}")
print(f"  Max:  {np.max(X_train_processed):.6f}")

# Check if any columns are constant (which would be problematic)
col_stds = np.std(X_train_processed, axis=0)
constant_cols = np.where(col_stds < 1e-10)[0]
if len(constant_cols) > 0:
    print(f"  WARNING: {len(constant_cols)} constant columns detected!")
    # Print which columns are constant
    for i, col_idx in enumerate(constant_cols[:5]):  # Show first 5
        if col_idx < len(numeric_features):
            col_name = numeric_features[col_idx]
            print(f"    Constant column {i}: {col_name} (numeric)")
        else:
            cat_idx = col_idx - len(numeric_features)
            # For categorical features, we need to get the actual column names after one-hot encoding
            # This is approximate since we don't have the exact mapping
            print(f"    Constant column {i}: categorical feature index {cat_idx}")
else:
    print(f"  All columns have variance > 0")

# Compute sample weights for training
sample_weights = np.array([class_weights_dict[c] for c in y_train])

# Train Random Forest
print("\n=== Training Baseline Model ===")
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    n_jobs=-1
)
model.fit(X_train_processed, y_train, sample_weight=sample_weights)
print("Model trained.")

# Validate
print("\n=== Validation Set Evaluation ===")
y_val_pred = model.predict(X_val_processed)
accuracy = accuracy_score(y_val, y_val_pred)
precision, recall, f1, support = precision_recall_fscore_support(y_val, y_val_pred, average=None)
macro_precision = np.mean(precision)
macro_recall = np.mean(recall)
macro_f1 = np.mean(f1)
weighted_f1 = np.average(f1, weights=support)

print(f"Validation Accuracy: {accuracy:.4f}")
print(f"Validation Macro Precision: {macro_precision:.4f}")
print(f"Validation Macro Recall: {macro_recall:.4f}")
print(f"Validation Macro F1: {macro_f1:.4f}")
print(f"Validation Weighted F1: {weighted_f1:.4f}")
for i, class_name in enumerate(label_encoder.classes_):
    print(f"  {class_name}: P={precision[i]:.4f}, R={recall[i]:.4f}, F1={f1[i]:.4f}, Support={support[i]}")

# Confusion matrix
cm = confusion_matrix(y_val, y_val_pred)
print(f"Confusion Matrix:\n{cm}")

# Save the results for comparison
results = {
    'validation_accuracy': accuracy,
    'validation_macro_f1': macro_f1,
    'validation_per_class': {
        label_encoder.classes_[i]: {
            'precision': float(precision[i]),
            'recall': float(recall[i]),
            'f1': float(f1[i]),
            'support': int(support[i])
        } for i in range(len(label_encoder.classes_))
    }
}

# Save to file for reference
import json
with open(os.path.join(MODEL_DIR, 'verify_baseline_results.json'), 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nSaved verification results to {os.path.join(MODEL_DIR, 'verify_baseline_results.json')}")

print("\n=== EXPECTED CORRECTED VALIDATION REFERENCE ===")
print("Accuracy: 0.8423")
print("Macro F1: 0.8107")
print(f"Difference in accuracy: {accuracy - 0.8423:.4f}")
print(f"Difference in macro F1: {macro_f1 - 0.8107:.4f}")

# Determine if we are close
if abs(accuracy - 0.8423) < 0.01 and abs(macro_f1 - 0.8107) < 0.01:
    print("[PASS] Baseline reproduction matches expected corrected validation.")
else:
    print("[FAIL] Baseline reproduction does NOT match expected corrected validation.")
    print("   This may indicate use of incorrect pipeline (e.g., pre-correction features).")