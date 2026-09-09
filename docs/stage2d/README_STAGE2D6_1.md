# Stage 2D.6.1 — Temporal Leakage Remediation & Full Rebuild

This directory contains the outputs and artifacts from Stage 2D.6.1, which focused on remediating temporal leakage in the weak label generation pipeline and rebuilding the entire ML workflow from corrected weak labels through final model evaluation.

## Files Overview

### Data Files
- `train.csv` - Training set (121,608 rows) after spatial split and filtering
- `validation.csv` - Validation set (28,848 rows) after spatial split and filtering  
- `test.csv` - Test set (26,137 rows) after spatial split and filtering (held-out, untouched until final evaluation)
- `stage2d_prepared_dataset_fixed.csv` - Intermediate prepared dataset before splitting (176,593 rows)

### Model Artifacts (in models/ directory)
- `final_model.joblib` - Trained Random Forest classifier
- `preprocessing_pipeline.joblib` - Fitted preprocessing pipeline (fitted on training data only)
- `label_encoder.joblib` - Mapping from class names to integers
- `feature_schema.json` - Definition of the 15-feature input set
- `model_metadata.json` - Comprehensive metadata including performance metrics

### Documentation
- `FINAL_SUMMARY.txt` - Concise summary of the remediation effort and final performance
- `STAGE_2D_6_1_TEMPORAL_LEAKAGE_REMEDIATION.md` - Detailed report covering root cause, code changes, temporal test results, before/after label statistics, and complete verification
- `feature_schema.json` - Current feature schema reflecting the corrected pipeline

### Scripts Used in Remediation
- `generate_weak_labels_final_fixed.py` - Fixed weak label generation with temporal correctness
- `prepare_stage2d_dataset_from_fixed_labels.py` - Dataset preparation from fixed weak labels
- `create_spatial_split_final.py` - Spatial blocking split (0.2°) to prevent location memorization
- `update_feature_schema.py` - Updated feature schema with new split statistics
- `train_final_model.py` - Final model training and evaluation script
- `verify_baseline.py` - Baseline reproduction verification script

## Key Accomplishments

1. **Fixed Temporal Leakage**: Persistence features in weak label generation now computed using only historical data ≤ event time
2. **Rebuilt Pipeline**: Complete reconstruction from corrected weak labels through final model evaluation
3. **Validated Performance**: Final model achieves Test Accuracy of 0.9338 and Test Macro F1 of 0.9154 on untouched test set
4. **Eliminated Leakage Sources**: Comprehensive audit confirmed elimination of target, temporal, spatial, preprocessing, and feature contract leakage
5. **Maintained SIH Five-Category Architecture**: Industrial Fire, Agricultural Fire, Wildfire/Natural Fire, Persistent Thermal Source (post-processing), Unknown/Other

## Final Performance Metrics

**Test Set Evaluation (Untouched):**
- Accuracy: 0.9338
- Macro Precision: 0.9326
- Macro Recall: 0.9008
- Macro F1: 0.9154
- Weighted F1: 0.9333

**Per-Class F1 Scores:**
- Agricultural Fire: 0.9308
- Industrial Fire: 0.8685
- Wildfire/Natural Fire: 0.9468

## Reproducibility

To reproduce these results:
1. Run `generate_weak_labels_final_fixed.py` to create FireGuard_WEAKLABELS_FIXED.csv
2. Run `prepare_stage2d_dataset_from_fixed_labels.py` to create stage2d_prepared_dataset_fixed.csv
3. Run `create_spatial_split_final.py` to create train/validation/test splits
4. Run `train_final_model.py` to train and evaluate the final model
5. Run `verify_baseline.py` to verify baseline reproduction

All scripts are located in the docs/ directory.