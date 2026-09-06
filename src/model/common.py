"""
Shared evaluation helpers for Track A and Track B modeling.
"""

import numpy as np
import pandas as pd
from sklearn.metrics import (
    roc_auc_score, average_precision_score, precision_score, recall_score,
    f1_score, confusion_matrix, balanced_accuracy_score,
)

RANDOM_STATE = 42


def evaluate_at_threshold(y_true, y_prob, threshold=0.5):
    y_pred = (y_prob >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else np.nan
    specificity = tn / (tn + fp) if (tn + fp) > 0 else np.nan
    return {
        "threshold": threshold,
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "sensitivity": sensitivity,
        "specificity": specificity,
        "balanced_accuracy": balanced_accuracy_score(y_true, y_pred),
        "tn": tn, "fp": fp, "fn": fn, "tp": tp,
    }


def evaluate_model(name, y_true, y_prob, threshold=0.5):
    base = evaluate_at_threshold(y_true, y_prob, threshold)
    base["model"] = name
    base["roc_auc"] = roc_auc_score(y_true, y_prob)
    base["pr_auc"] = average_precision_score(y_true, y_prob)
    return base


def threshold_sweep(y_true, y_prob, thresholds=None):
    if thresholds is None:
        thresholds = np.round(np.arange(0.1, 0.95, 0.05), 2)
    rows = [evaluate_at_threshold(y_true, y_prob, t) for t in thresholds]
    return pd.DataFrame(rows)


def comparison_table(results):
    cols = ["model", "roc_auc", "pr_auc", "precision", "recall", "f1",
            "sensitivity", "specificity", "balanced_accuracy"]
    df = pd.DataFrame(results)[cols]
    return df.round(4)
