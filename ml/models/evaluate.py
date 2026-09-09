"""
Model Evaluation - Stage 2 ML Pipeline
"""

import logging
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)
import json
from datetime import datetime
from typing import Dict, Any
import os

logger = logging.getLogger(__name__)


class ModelEvaluator:
    """Evaluate model performance"""

    def __init__(self, class_names: list):
        self.class_names = class_names
        self.metrics = {}

    def evaluate(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        y_pred_proba: np.ndarray = None,
        set_name: str = "test"
    ) -> Dict[str, Any]:
        """
        Evaluate model predictions
        Returns metrics dictionary
        """
        logger.info(f"Evaluating on {set_name} set...")

        metrics = {
            "set": set_name,
            "timestamp": datetime.utcnow().isoformat(),
            "n_samples": len(y_true),
        }

        # Overall metrics
        metrics["accuracy"] = accuracy_score(y_true, y_pred)
        metrics["macro_f1"] = f1_score(y_true, y_pred, average="macro", zero_division=0)
        metrics["weighted_f1"] = f1_score(y_true, y_pred, average="weighted", zero_division=0)

        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        metrics["confusion_matrix"] = cm.tolist()

        # Per-class metrics
        per_class = {}
        for i, class_name in enumerate(self.class_names):
            mask = (y_true == i)
            if mask.sum() == 0:
                per_class[class_name] = {
                    "precision": None,
                    "recall": None,
                    "f1": None,
                    "support": 0
                }
            else:
                per_class[class_name] = {
                    "precision": precision_score(y_true, y_pred, labels=[i], average=None, zero_division=0)[0] if len(np.unique(y_pred)) > 1 else 0,
                    "recall": recall_score(y_true, y_pred, labels=[i], average=None, zero_division=0)[0] if len(np.unique(y_pred)) > 1 else 0,
                    "f1": f1_score(y_true, y_pred, labels=[i], average=None, zero_division=0)[0] if len(np.unique(y_pred)) > 1 else 0,
                    "support": int(mask.sum())
                }

        metrics["per_class"] = per_class

        # Print report
        logger.info(f"\n{'='*60}")
        logger.info(f"{set_name.upper()} SET EVALUATION")
        logger.info(f"{'='*60}")
        logger.info(f"Accuracy: {metrics['accuracy']:.4f}")
        logger.info(f"Macro F1: {metrics['macro_f1']:.4f}")
        logger.info(f"Weighted F1: {metrics['weighted_f1']:.4f}")
        logger.info(f"\nPer-Class Metrics:")
        logger.info(f"{'Class':<30} {'Precision':<12} {'Recall':<12} {'F1':<12} {'Support':<10}")
        logger.info(f"{'-'*76}")

        for class_name in self.class_names:
            m = per_class[class_name]
            if m["support"] > 0:
                logger.info(
                    f"{class_name:<30} {m['precision']:<12.4f} "
                    f"{m['recall']:<12.4f} {m['f1']:<12.4f} {m['support']:<10}"
                )
            else:
                logger.info(f"{class_name:<30} {'N/A':<12} {'N/A':<12} {'N/A':<12} {m['support']:<10}")

        logger.info(f"{'='*60}\n")

        self.metrics = metrics
        return metrics

    def save_metrics(self, filepath: str):
        """Save metrics to JSON"""
        with open(filepath, "w") as f:
            json.dump(self.metrics, f, indent=2)
        logger.info(f"Metrics saved to {filepath}")
