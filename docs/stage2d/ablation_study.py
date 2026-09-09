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

# Load data and feature schema
print("=== Loading Data and Feature Schema ===")
train_df = pd.read_csv(TRAIN_PATH)
val_df = pd.read_csv(VALIDATION_PATH)
with open(FEATURE_SCHEMA_PATH, 'r') as f:
    feature_schema = json.load(f)

model_input_features = feature_schema['model_input_features']
numeric_features = feature_schema['numeric_features']
categorical_features = feature_schema['categorical_features']
print(f"Using {len(model_input_features)} model input features.")
print(f"Numeric features: {len(numeric_features)}")
print(f"Categorical features: {len(categorical_features)}")

# Separate features and target
X_train_raw = train_df[model_input_features]
y_train_raw = train_df['target_class']
X_val_raw = val_df[model_input_features]
y_val_raw = val_df['target_class']

# Encode target classes
label_encoder = LabelEncoder()
y_train = label_encoder.fit_transform(y_train_raw)
y_val = label_encoder.transform(y_val_raw)
class_names = label_encoder.classes_
print(f"Classes: {class_names}")

# Compute class weights from training set (same for all experiments)
class_counts = np.bincount(y_train)
total_samples = len(y_train)
class_weights = total_samples / (len(class_counts) * class_counts)
class_weights_dict = {i: class_weights[i] for i in range(len(class_counts))}
print(f"Class weights: {class_weights_dict}")

# Function to create preprocessing pipeline (fitted on data)
def create_preprocessing_pipeline(X_fit):
    # Numeric pipeline: median impute + standardize
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    # Categorical pipeline: most frequent impute + one-hot encode
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])
    # Combine
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])
    return preprocessor

# We need to import OneHotEncoder
from sklearn.preprocessing import OneHotEncoder

# Function to train and evaluate given features to exclude
def train_and_evaluate(exclude_features=None, experiment_name="Experiment"):
    if exclude_features is None:
        exclude_features = []
    print(f"\n=== {experiment_name} ===")
    if len(exclude_features) > 0:
        print(f"Excluding features: {exclude_features}")
        # Remove excluded features from raw data
        features_to_use = [f for f in model_input_features if f not in exclude_features]
    else:
        features_to_use = model_input_features.copy()
    print(f"Number of features after exclusion: {len(features_to_use)}")

    # Subset raw data
    X_train_use = X_train_raw[features_to_use]
    X_val_use = X_val_raw[features_to_use]

    # Identify numeric and categorical features among the remaining
    numeric_use = [f for f in numeric_features if f in features_to_use]
    categorical_use = [f for f in categorical_features if f in features_to_use]

    # Create preprocessing pipeline for this feature set
    # Numeric pipeline: median impute + standardize
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    # Categorical pipeline: most frequent impute + one-hot encode
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])
    # Combine
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_use),
            ('cat', categorical_transformer, categorical_use)
        ])

    # Fit preprocessing on training data only
    print("Fitting preprocessing pipeline on training data...")
    preprocessor.fit(X_train_use)

    # Transform training and validation data
    X_train_processed = preprocessor.transform(X_train_use)
    X_val_processed = preprocessor.transform(X_val_use)
    print(f"Processed train shape: {X_train_processed.shape}")
    print(f"Processed validation shape: {X_val_processed.shape}")

    # Compute sample weights for training
    sample_weights = np.array([class_weights_dict[c] for c in y_train])

    # Train Random Forest
    print("Training Random Forest...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train_processed, y_train, sample_weight=sample_weights)

    # Validate
    y_val_pred = model.predict(X_val_processed)
    accuracy = accuracy_score(y_val, y_val_pred)
    precision, recall, f1, support = precision_recall_fscore_support(y_val, y_val_pred, average=None)
    macro_precision = np.mean(precision)
    macro_recall = np.mean(recall)
    macro_f1 = np.mean(f1)
    weighted_f1 = np.average(f1, weights=support)

    # Per-class metrics
    per_class = {}
    for i, class_name in enumerate(class_names):
        per_class[class_name] = {
            'precision': precision[i],
            'recall': recall[i],
            'f1': f1[i],
            'support': support[i]
        }

    print(f"Validation Accuracy: {accuracy:.4f}")
    print(f"Validation Macro F1: {macro_f1:.4f}")
    print(f"Validation Weighted F1: {weighted_f1:.4f}")
    for class_name in class_names:
        m = per_class[class_name]
        print(f"  {class_name}: P={m['precision']:.4f}, R={m['recall']:.4f}, F1={m['f1']:.4f}")

    return {
        'model': model,
        'preprocessor': preprocessor,
        'accuracy': accuracy,
        'macro_precision': macro_precision,
        'macro_recall': macro_recall,
        'macro_f1': macro_f1,
        'weighted_f1': weighted_f1,
        'per_class': per_class,
        'confusion_matrix': confusion_matrix(y_val, y_val_pred),
        'features_used': features_to_use,
        'processed_train_shape': X_train_processed.shape,
        'processed_val_shape': X_val_processed.shape
    }

# Baseline (no exclusion)
print("\n" + "="*60)
print("BASELINE (All Features)")
print("="*60)
baseline = train_and_evaluate(exclude_features=[], experiment_name="Baseline")

# Feature importances from baseline (on processed features)
# We can get feature names after one-hot encoding
# Let's get the feature names from the preprocessor
def get_feature_names_after_preprocessing(preprocessor, input_features):
    # This works for ColumnTransformer with named transformers
    try:
        # Get output feature names
        feature_names = preprocessor.get_feature_names_out(input_features)
        return feature_names
    except AttributeError:
        # Fallback for older sklearn
        feature_names = []
        for name, trans, cols in preprocessor.transformers_:
            if trans == 'drop' or (hasattr(trans, '__len__') and len(cols) == 0):
                continue
            if trans == 'passthrough':
                feature_names.extend(cols)
            elif hasattr(trans, 'get_feature_names_out'):
                # For Pipeline, we need to get the final step's feature names
                if isinstance(trans, Pipeline):
                    # Get the last step
                    last_step = trans[-1]
                    if hasattr(last_step, 'get_feature_names_out'):
                        feature_names.extend(last_step.get_feature_names_out(cols))
                    else:
                        # If no get_feature_names_out, just use input names
                        feature_names.extend(cols)
                else:
                    feature_names.extend(cols)
            else:
                feature_names.extend(cols)
        return feature_names

try:
    feature_names_out = get_feature_names_after_preprocessing(baseline['preprocessor'], baseline['features_used'])
    importances = baseline['model'].feature_importances_
    feat_imp = pd.DataFrame({'feature': feature_names_out, 'importance': importances})
    feat_imp = feat_imp.sort_values('importance', ascending=False)
    print("\nTop 10 features by importance (after preprocessing):")
    print(feat_imp.head(10))
    # Also aggregate by original feature? We'll skip for brevity.
except Exception as e:
    print(f"Could not compute feature importances: {e}")

# Ablation A: FIRMS thermal/sensor
firms_features = ['bright_ti4', 'bright_ti5', 'scan', 'track']
result_A = train_and_evaluate(exclude_features=firms_features, experiment_name="Ablation A: Remove FIRMS thermal/sensor")

# Ablation B: Dynamic World
dw_features = ['dw_bare', 'dw_confidence', 'dw_difference', 'dw_found', 'dw_grass', 'dw_water', 'dw_label']
result_B = train_and_evaluate(exclude_features=dw_features, experiment_name="Ablation B: Remove Dynamic World")

# Ablation C: Acquisition/sensor metadata
metadata_features = ['confidence', 'satellite', 'instrument', 'daynight', 'source_satellite', 'snpp_anomaly_flag']
result_C = train_and_evaluate(exclude_features=metadata_features, experiment_name="Ablation C: Remove Acquisition/sensor metadata")

# Individual suspicious-feature ablation: dw_label
result_dwlabel = train_and_evaluate(exclude_features=['dw_label'], experiment_name="Individual Ablation: Remove dw_label")

# Also verify that traceability fields are not in model inputs (already done in baseline)
print("\n=== Checking that traceability fields are not in model inputs ===")
traceability_fields = ['fire_id', 'nearest_facility_name', 'nearest_osm_id']
unexpected = [f for f in model_input_features if f in traceability_fields]
if len(unexpected) == 0:
    print("PASS: No traceability fields in model input features.")
else:
    print(f"FAIL: Traceability fields in model input: {unexpected}")

# Summary table
print("\n" + "="*60)
print("SUMMARY OF RESULTS")
print("="*60)
print(f"{'Experiment':<40} {'Accuracy':<10} {'Macro F1':<10}")
print("-"*60)
print(f"{'Baseline (all 17 features)':<40} {baseline['accuracy']:<10.4f} {baseline['macro_f1']:<10.4f}")
print(f"{'A) No FIRMS thermal/sensor':<40} {result_A['accuracy']:<10.4f} {result_A['macro_f1']:<10.4f}")
print(f"{'B) No Dynamic World':<40} {result_B['accuracy']:<10.4f} {result_B['macro_f1']:<10.4f}")
print(f"{'C) No Acquisition/sensor metadata':<40} {result_C['accuracy']:<10.4f} {result_C['macro_f1']:<10.4f}")
print(f"{'Individual: no dw_label':<40} {result_dwlabel['accuracy']:<10.4f} {result_dwlabel['macro_f1']:<10.4f}")

# Class-wise metrics for baseline and major ablations (we already printed per-class in each experiment)
# Let's also compute train vs validation gap for baseline and one ablation
print("\n=== TRAIN vs VALIDATION PERFORMANCE (Baseline) ===")
y_train_pred = baseline['model'].predict(baseline['preprocessor'].transform(X_train_raw[baseline['features_used']]))
train_accuracy = accuracy_score(y_train, y_train_pred)
print(f"Training Accuracy: {train_accuracy:.4f}")
print(f"Validation Accuracy: {baseline['accuracy']:.4f}")
print(f"Gap (train - val): {train_accuracy - baseline['accuracy']:.4f}")

print("\n=== TRAIN vs VALIDATION PERFORMANCE (Ablation B: No DW) ===")
X_train_use_B = X_train_raw[result_B['features_used']]
X_train_processed_B = result_B['preprocessor'].transform(X_train_use_B)
y_train_pred_B = result_B['model'].predict(X_train_processed_B)
train_accuracy_B = accuracy_score(y_train, y_train_pred_B)
print(f"Training Accuracy: {train_accuracy_B:.4f}")
print(f"Validation Accuracy: {result_B['accuracy']:.4f}")
print(f"Gap (train - val): {train_accuracy_B - result_B['accuracy']:.4f}")

# Helper function to convert numpy types to native Python types for JSON serialization
def convert_to_native(obj):
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, dict):
        return {key: convert_to_native(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_native(item) for item in obj]
    else:
        return obj

# Save results to a file for reporting
results_summary = {
    'baseline': {
        'accuracy': baseline['accuracy'],
        'macro_f1': baseline['macro_f1'],
        'weighted_f1': baseline['weighted_f1'],
        'per_class': convert_to_native(baseline['per_class'])
    },
    'ablation_A': {
        'accuracy': result_A['accuracy'],
        'macro_f1': result_A['macro_f1'],
        'weighted_f1': result_A['weighted_f1'],
        'per_class': convert_to_native(result_A['per_class'])
    },
    'ablation_B': {
        'accuracy': result_B['accuracy'],
        'macro_f1': result_B['macro_f1'],
        'weighted_f1': result_B['weighted_f1'],
        'per_class': convert_to_native(result_B['per_class'])
    },
    'ablation_C': {
        'accuracy': result_C['accuracy'],
        'macro_f1': result_C['macro_f1'],
        'weighted_f1': result_C['weighted_f1'],
        'per_class': convert_to_native(result_C['per_class'])
    },
    'ablation_dwlabel': {
        'accuracy': result_dwlabel['accuracy'],
        'macro_f1': result_dwlabel['macro_f1'],
        'weighted_f1': result_dwlabel['weighted_f1'],
        'per_class': convert_to_native(result_dwlabel['per_class'])
    }
}

import json
with open(os.path.join(MODEL_DIR, 'ablation_results.json'), 'w') as f:
    json.dump(results_summary, f, indent=2)
print(f"\nSaved ablation results to {os.path.join(MODEL_DIR, 'ablation_results.json')}")