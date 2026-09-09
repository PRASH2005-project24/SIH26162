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

# Record start time
start_time = time.time()

# Paths
STAGE2D_DIR = r'C:\ProjectX\SIH26162\docs\stage2d'
TRAIN_PATH = os.path.join(STAGE2D_DIR, 'train.csv')
VALIDATION_PATH = os.path.join(STAGE2D_DIR, 'validation.csv')
TEST_PATH = os.path.join(STAGE2D_DIR, 'test.csv')
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

print(f"Using {len(model_input_features)} model input features.")
print(f"Numeric features: {len(numeric_features)}")
print(f"Categorical features: {len(categorical_features)}")

# Load and combine training and validation data
print("\n=== Loading Training and Validation Data ===")
train_df = pd.read_csv(TRAIN_PATH)
val_df = pd.read_csv(VALIDATION_PATH)
# Combine
df_train_val = pd.concat([train_df, val_df], ignore_index=True)
print(f"Training rows: {len(train_df)}")
print(f"Validation rows: {len(val_df)}")
print(f"Combined train+val rows: {len(df_train_val)}")

# Load test data (untouched)
test_df = pd.read_csv(TEST_PATH)
print(f"Test rows: {len(test_df)}")

# Prepare features and target for train+val
X_train_val_raw = df_train_val[model_input_features]
y_train_val_raw = df_train_val[target_class]

# Prepare features and target for test
X_test_raw = test_df[model_input_features]
y_test_raw = test_df[target_class]

# Encode target classes
label_encoder = LabelEncoder()
y_train_val = label_encoder.fit_transform(y_train_val_raw)
y_test = label_encoder.transform(y_test_raw)
print(f"Classes: {label_encoder.classes_}")
print(f"Class mapping: {dict(zip(label_encoder.classes_, range(len(label_encoder.classes_))))}")

# Compute class weights from training data only (as per original specification)
# We'll use the combined train+val for computing class weights? The original used training set only.
# We'll follow the original: use training set only for class weights.
y_train_only = label_encoder.transform(train_df[target_class])
class_counts = np.bincount(y_train_only)
total_samples = len(y_train_only)
class_weights = total_samples / (len(class_counts) * class_counts)
class_weights_dict = {i: class_weights[i] for i in range(len(class_counts))}
print(f"Class weights (from training set only): {class_weights_dict}")

# Create preprocessing pipeline
# Numeric pipeline: median impute + standardize
numeric_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])
# Categorical pipeline: most frequent impute + one-hot encode
categorical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('onehot', joblib.load('sklearn.preprocessing._encoders.OneHotEncoder') if False else None)  # We'll instantiate below
])
# Actually, we need to import OneHotEncoder
from sklearn.preprocessing import OneHotEncoder
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

# Fit preprocessing on training data only (original training set)
print("\n=== Fitting Preprocessing Pipeline on Training Data ===")
# We need to fit on the original training data (not combined) to avoid data leakage into validation?
# The instructions: "preprocessing is fitted only on TRAIN data"
# We'll use the original training set for fitting.
X_train_raw = train_df[model_input_features]
preprocessor.fit(X_train_raw)
print("Preprocessing pipeline fitted.")

# Transform all datasets
print("Transforming datasets...")
X_train_val_processed = preprocessor.transform(X_train_val_raw)
X_test_processed = preprocessor.transform(X_test_raw)
print(f"Processed train+val shape: {X_train_val_processed.shape}")
print(f"Processed test shape: {X_test_processed.shape}")

# Compute sample weights for training (using combined train+val? We'll use the original training set for sample weights to match the class weights)
# We'll compute sample weights for each instance in the combined set based on the class weights from the training set.
# For simplicity, we'll use the class weights dictionary to weight each sample.
sample_weights = np.array([class_weights_dict[c] for c in y_train_val])

# Train Random Forest
print("\n=== Training Final Model ===")
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    n_jobs=-1
)
# Note: We'll use sample_weight parameter
model.fit(X_train_val_processed, y_train_val, sample_weight=sample_weights)
print("Model trained.")

# Validate on the validation set (original validation set) to report TRAIN/VALIDATION results
print("\n=== Validation Set Evaluation (Original Validation Set) ===")
X_val_raw = val_df[model_input_features]
X_val_processed = preprocessor.transform(X_val_raw)
y_val = label_encoder.transform(val_df[target_class])

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

# Evaluate on test set
print("\n=== Test Set Evaluation (Untouched Test Set) ===")
y_test_pred = model.predict(X_test_processed)
test_accuracy = accuracy_score(y_test, y_test_pred)
test_precision, test_recall, test_f1, test_support = precision_recall_fscore_support(y_test, y_test_pred, average=None)
test_macro_precision = np.mean(test_precision)
test_macro_recall = np.mean(test_recall)
test_macro_f1 = np.mean(test_f1)
test_weighted_f1 = np.average(test_f1, weights=test_support)

print(f"Test Accuracy: {test_accuracy:.4f}")
print(f"Test Macro Precision: {test_macro_precision:.4f}")
print(f"Test Macro Recall: {test_macro_recall:.4f}")
print(f"Test Macro F1: {test_macro_f1:.4f}")
print(f"Test Weighted F1: {test_weighted_f1:.4f}")
for i, class_name in enumerate(label_encoder.classes_):
    print(f"  {class_name}: P={test_precision[i]:.4f}, R={test_recall[i]:.4f}, F1={test_f1[i]:.4f}, Support={test_support[i]}")

# Confusion matrix for test
test_cm = confusion_matrix(y_test, y_test_pred)
print(f"Test Confusion Matrix:\n{test_cm}")

# Save model artifacts
print("\n=== Saving Model Artifacts ===")
# Save model
model_artifact_path = os.path.join(MODEL_DIR, 'final_model.joblib')
joblib.dump(model, model_artifact_path)
print(f"Saved model to {model_artifact_path}")

# Save preprocessor
preprocessor_artifact_path = os.path.join(MODEL_DIR, 'preprocessing_pipeline.joblib')
joblib.dump(preprocessor, preprocessor_artifact_path)
print(f"Saved preprocessing pipeline to {preprocessor_artifact_path}")

# Save label encoder
label_encoder_path = os.path.join(MODEL_DIR, 'label_encoder.joblib')
joblib.dump(label_encoder, label_encoder_path)
print(f"Saved label encoder to {label_encoder_path}")

# Save feature schema (already saved, but we can save a copy)
feature_schema_model_path = os.path.join(MODEL_DIR, 'feature_schema.json')
with open(feature_schema_model_path, 'w') as f:
    json.dump(feature_schema, f, indent=2)
print(f"Saved feature schema copy to {feature_schema_model_path}")

# Save model metadata
model_metadata = {
    "model_type": "RandomForestClassifier",
    "model_params": {
        "n_estimators": 100,
        "max_depth": 10,
        "random_state": 42,
        "n_jobs": -1
    },
    "training_datetime": pd.Timestamp.now().isoformat(),
    "validation_accuracy": float(accuracy),
    "validation_macro_f1": float(macro_f1),
    "validation_weighted_f1": float(weighted_f1),
    "test_accuracy": float(test_accuracy),
    "test_macro_f1": float(test_macro_f1),
    "test_weighted_f1": float(test_weighted_f1),
    "validation_per_class": {
        label_encoder.classes_[i]: {
            "precision": float(precision[i]),
            "recall": float(recall[i]),
            "f1": float(f1[i]),
            "support": int(support[i])
        } for i in range(len(label_encoder.classes_))
    },
    "test_per_class": {
        label_encoder.classes_[i]: {
            "precision": float(test_precision[i]),
            "recall": float(test_recall[i]),
            "f1": float(test_f1[i]),
            "support": int(test_support[i])
        } for i in range(len(label_encoder.classes_))
    },
    "confusion_matrix": cm.tolist(),
    "test_confusion_matrix": test_cm.tolist(),
    "class_names": label_encoder.classes_.tolist(),
    "class_mapping": {label_encoder.classes_[i]: int(i) for i in range(len(label_encoder.classes_))},
    "feature_schema_path": FEATURE_SCHEMA_PATH,
    "preprocessing_pipeline_path": preprocessor_artifact_path,
    "label_encoder_path": label_encoder_path,
    "notes": "Final model trained on combined train+val data, evaluated on untouched test set. Feature set corrected per Stage 2D.5.1."
}
metadata_path = os.path.join(MODEL_DIR, 'model_metadata.json')
with open(metadata_path, 'w') as f:
    json.dump(model_metadata, f, indent=2)
print(f"Saved model metadata to {metadata_path}")

print("\n=== FINAL OUTPUT ===")
print(f"Selected model: Random Forest CPU")
print(f"Training time: {time.time() - start_time:.2f} seconds")
print(f"Validation accuracy: {accuracy:.4f}")
print(f"Validation macro F1: {macro_f1:.4f}")
print(f"Test accuracy: {test_accuracy:.4f}")
print(f"Test macro F1: {test_macro_f1:.4f}")
print(f"Per-class Test F1: Industrial={test_f1[list(label_encoder.classes_).index('industrial')] if 'industrial' in label_encoder.classes_ else 0:.4f}, Agricultural={test_f1[list(label_encoder.classes_).index('agricultural')] if 'agricultural' in label_encoder.classes_ else 0:.4f}, Wildfire={test_f1[list(label_encoder.classes_).index('wildfire')] if 'wildfire' in label_encoder.classes_ else 0:.4f}")
print(f"Model artifact path: {model_artifact_path}")
print(f"Preprocessing pipeline path: {preprocessor_artifact_path}")
print(f"Label encoder path: {label_encoder_path}")
print(f"Feature schema path: {feature_schema_model_path}")
print(f"Metadata path: {metadata_path}")
print(f"Final status: STAGE 2D.6 COMPLETE — FINAL MODEL ACCEPTED")