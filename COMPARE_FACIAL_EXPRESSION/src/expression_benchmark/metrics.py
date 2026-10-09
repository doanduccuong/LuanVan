from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    confusion_matrix,
    precision_recall_fscore_support,
)

from .constants import LABELS


def classification_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, Any]:
    if y_true.shape != y_pred.shape:
        raise ValueError("y_true và y_pred phải có cùng kích thước.")
    if y_true.size == 0:
        raise ValueError("Không thể tính chỉ số trên tập rỗng.")
    label_ids = np.arange(len(LABELS))
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=label_ids,
        zero_division=0,
    )
    matrix = confusion_matrix(y_true, y_pred, labels=label_ids)
    row_sums = matrix.sum(axis=1, keepdims=True)
    normalized = np.divide(
        matrix,
        row_sums,
        out=np.zeros_like(matrix, dtype=np.float64),
        where=row_sums != 0,
    )
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(np.mean(f1)),
        "per_class": [
            {
                "label_id": int(index),
                "label": LABELS[index],
                "precision": float(precision[index]),
                "recall": float(recall[index]),
                "f1": float(f1[index]),
                "support": int(support[index]),
            }
            for index in label_ids
        ],
        "confusion_matrix": matrix.tolist(),
        "confusion_matrix_normalized": normalized.tolist(),
        "sample_count": int(y_true.size),
        "processing_failure_rate": 0.0,
    }
