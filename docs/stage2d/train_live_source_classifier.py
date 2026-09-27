"""Train a source-neutral classifier for events with usable Dynamic World data."""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler


STAGE_DIR = Path(__file__).resolve().parent
MODEL_DIR = STAGE_DIR / "models" / "source_neutral_classifier"
FEATURE_SCHEMA_PATH = STAGE_DIR / "models" / "feature_schema.json"


def main() -> None:
    with FEATURE_SCHEMA_PATH.open(encoding="utf-8") as schema_file:
        source_schema = json.load(schema_file)

    features = [
        feature
        for feature in source_schema["model_input_features"]
        if feature not in {"satellite", "source_satellite"}
    ]
    numeric_features = [
        feature for feature in source_schema["numeric_features"] if feature in features
    ]
    categorical_features = [
        feature for feature in source_schema["categorical_features"] if feature in features
    ]

    train = pd.read_csv(STAGE_DIR / "train.csv")
    validation = pd.read_csv(STAGE_DIR / "validation.csv")
    test = pd.read_csv(STAGE_DIR / "test.csv")

    train_observed = train.loc[train["dw_found"] == 1].copy()
    validation_observed = validation.loc[validation["dw_found"] == 1].copy()
    test_observed = test.loc[test["dw_found"] == 1].copy()
    if train_observed.empty or validation_observed.empty or test_observed.empty:
        raise ValueError("Each split must contain labeled Dynamic World observations")

    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    preprocessing = ColumnTransformer([
        ("numeric", numeric_pipeline, numeric_features),
        ("categorical", categorical_pipeline, categorical_features),
    ])

    preprocessing.fit(train_observed[features])
    label_encoder = LabelEncoder()
    train_labels = label_encoder.fit_transform(train_observed["target_class"])
    training_counts = np.bincount(train_labels)
    class_weights = len(train_labels) / (len(training_counts) * training_counts)

    train_validation = pd.concat(
        [train_observed, validation_observed], ignore_index=True
    )
    train_validation_labels = label_encoder.transform(train_validation["target_class"])
    sample_weights = np.asarray([class_weights[label] for label in train_validation_labels])

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(
        preprocessing.transform(train_validation[features]),
        train_validation_labels,
        sample_weight=sample_weights,
    )

    test_labels = label_encoder.transform(test_observed["target_class"])
    test_predictions = model.predict(preprocessing.transform(test_observed[features]))
    precision, recall, f1, support = precision_recall_fscore_support(
        test_labels,
        test_predictions,
        labels=np.arange(len(label_encoder.classes_)),
        zero_division=0,
    )
    per_class = {
        label: {
            "precision": float(precision[index]),
            "recall": float(recall[index]),
            "f1": float(f1[index]),
            "support": int(support[index]),
        }
        for index, label in enumerate(label_encoder.classes_)
    }

    metadata = {
        "model_type": "RandomForestClassifier",
        "model_version": "source-neutral-dw-v1",
        "model_params": {
            "n_estimators": 100,
            "max_depth": 10,
            "random_state": 42,
            "n_jobs": -1,
        },
        "training_rows_with_dw": int(len(train_observed)),
        "validation_rows_with_dw": int(len(validation_observed)),
        "test_rows_with_dw": int(len(test_observed)),
        "excluded_no_dw_training_rows": int(len(train) - len(train_observed)),
        "excluded_source_features": ["satellite", "source_satellite"],
        "classes": label_encoder.classes_.tolist(),
        "test_accuracy_with_dw": float(accuracy_score(test_labels, test_predictions)),
        "test_macro_f1_with_dw": float(f1_score(test_labels, test_predictions, average="macro")),
        "test_per_class_with_dw": per_class,
    }
    feature_schema = {
        **source_schema,
        "model_input_features": features,
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "excluded_source_features": ["satellite", "source_satellite"],
        "requires_usable_dynamic_world": True,
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_DIR / "final_model.joblib")
    joblib.dump(label_encoder, MODEL_DIR / "label_encoder.joblib")
    joblib.dump(preprocessing, MODEL_DIR / "preprocessing_pipeline.joblib")
    with (MODEL_DIR / "model_metadata.json").open("w", encoding="utf-8") as output:
        json.dump(metadata, output, indent=2)
    with (MODEL_DIR / "feature_schema.json").open("w", encoding="utf-8") as output:
        json.dump(feature_schema, output, indent=2)

    print(json.dumps(metadata, indent=2))
    print(f"Saved source-neutral model artifacts to {MODEL_DIR}")


if __name__ == "__main__":
    main()