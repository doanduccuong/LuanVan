from __future__ import annotations

import numpy as np

from expression_benchmark.metrics import classification_metrics


def test_perfect_predictions_have_unit_scores() -> None:
    labels = np.arange(7)
    metrics = classification_metrics(labels, labels.copy())
    assert metrics["accuracy"] == 1.0
    assert metrics["balanced_accuracy"] == 1.0
    assert metrics["macro_f1"] == 1.0
    assert metrics["confusion_matrix"] == np.eye(7, dtype=int).tolist()


def test_macro_f1_gives_each_class_equal_weight() -> None:
    true = np.array([0, 0, 0, 0, 1, 2, 3, 4, 5, 6])
    predicted = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    metrics = classification_metrics(true, predicted)
    assert metrics["accuracy"] == 0.4
    assert metrics["macro_f1"] < metrics["accuracy"]
