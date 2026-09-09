"""
Main Stage 2 ML Pipeline Execution
Load CSV → Train → Evaluate → Save
"""

import sys
import os
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.config import MLConfig
from ml.data.load import DataLoader, load_demo_data
from ml.features.engineering import FeatureEngineer
from ml.models.train import ModelTrainer
from ml.models.evaluate import ModelEvaluator


def main():
    """Execute full training pipeline"""
    logger.info("="*80)
    logger.info("STAGE 2 ML PIPELINE - TRAINING")
    logger.info("="*80)

    # ========================================================================
    # STEP 1: Load CSV data
    # ========================================================================
    logger.info("\n[STEP 1] Loading CSV data...")
    csv_path = "SIH26162_stage2_demo_training_data.csv"

    loader = DataLoader()
    df = loader.load_csv(csv_path)

    # Validate data
    stats = loader.validate_data()
    logger.info(f"Data statistics: {stats}")

    # Prepare features and target
    X, y, feature_cols = loader.prepare_features_and_target()
    logger.info(f"Features shape: {X.shape}, Target shape: {y.shape}")

    # ========================================================================
    # STEP 2: Split data (temporal-aware)
    # ========================================================================
    logger.info("\n[STEP 2] Splitting data (temporal-aware)...")
    (X_train, y_train), (X_val, y_val), (X_test, y_test) = loader.temporal_train_val_test_split(
        X, y, train_ratio=0.6, val_ratio=0.2, seed=MLConfig.RANDOM_SEED
    )

    logger.info(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")
    logger.info(f"Train class dist: {y_train.value_counts().to_dict()}")

    # ========================================================================
    # STEP 3: Feature engineering
    # ========================================================================
    logger.info("\n[STEP 3] Feature engineering...")
    feature_engineer = FeatureEngineer()
    feature_engineer.fit(X_train)

    X_train_eng = feature_engineer.transform(X_train)
    X_val_eng = feature_engineer.transform(X_val)
    X_test_eng = feature_engineer.transform(X_test)

    logger.info(f"Engineered features: {X_train_eng.shape[1]}")

    # ========================================================================
    # STEP 4: Train models
    # ========================================================================
    logger.info("\n[STEP 4] Training models...")
    trainer = ModelTrainer(model_dir=MLConfig.MODEL_DIR)

    training_metadata = trainer.train(
        X_train_eng, y_train,
        X_val_eng, y_val,
        feature_cols,
        class_names=MLConfig.FIRE_CLASSES
    )

    logger.info(f"Training metadata: {training_metadata}")

    # ========================================================================
    # STEP 5: Evaluate on test set
    # ========================================================================
    logger.info("\n[STEP 5] Evaluating on test set...")
    evaluator = ModelEvaluator(MLConfig.FIRE_CLASSES)

    y_test_encoded = trainer.label_encoder.transform(y_test)
    y_test_pred = trainer.selected_model.predict(X_test_eng)
    y_test_pred_proba = trainer.selected_model.predict_proba(X_test_eng)

    test_metrics = evaluator.evaluate(y_test_encoded, y_test_pred, set_name="TEST")

    # ========================================================================
    # STEP 6: Save model
    # ========================================================================
    logger.info("\n[STEP 6] Saving model...")
    save_info = trainer.save_model(
        feature_names=feature_engineer.feature_names,
        class_names=MLConfig.FIRE_CLASSES
    )

    logger.info(f"Model saved to: {save_info['model_path']}")

    # Save feature schema
    feature_schema_path = os.path.join(MLConfig.MODEL_DIR, "feature_schema.json")
    feature_engineer.save_schema(feature_schema_path)

    # Save metrics
    metrics_path = os.path.join(MLConfig.MODEL_DIR, "metrics.json")
    evaluator.save_metrics(metrics_path)

    # ========================================================================
    # STEP 7: Test inference
    # ========================================================================
    logger.info("\n[STEP 7] Testing inference...")
    from ml.models.inference import FireSourceClassifier

    classifier = FireSourceClassifier(MLConfig.MODEL_DIR)

    # Test with first test sample
    test_sample = X_test.iloc[0].to_dict()
    prediction = classifier.predict(test_sample)

    logger.info(f"Test prediction: {prediction}")
    logger.info(f"True label: {y_test.iloc[0]}")

    logger.info("\n" + "="*80)
    logger.info("TRAINING PIPELINE COMPLETE")
    logger.info("="*80)

    return {
        "train_samples": len(X_train),
        "val_samples": len(X_val),
        "test_samples": len(X_test),
        "test_accuracy": float(test_metrics["accuracy"]),
        "test_macro_f1": float(test_metrics["macro_f1"]),
        "model_path": save_info["model_path"],
    }


if __name__ == "__main__":
    result = main()
    print("\nFinal Result:")
    print(result)
