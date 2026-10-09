from __future__ import annotations

from typing import Any

import numpy as np

from .adapters.base import PredictionBatch
from .constants import LABELS


def prediction_rows(
    *,
    method: str,
    seed: int | None,
    sample_ids: tuple[str, ...],
    true_labels: np.ndarray,
    predictions: PredictionBatch,
) -> list[dict[str, Any]]:
    predictions.validate(len(sample_ids))
    return [
        {
            "method": method,
            "seed": seed,
            "sample_id": sample_id,
            "true_label_id": int(true_label),
            "true_label": LABELS[int(true_label)],
            "predicted_label_id": int(predicted_label),
            "predicted_label": LABELS[int(predicted_label)],
            "scores": [float(value) for value in scores],
            "status": "OK",
        }
        for sample_id, true_label, predicted_label, scores in zip(
            sample_ids,
            true_labels,
            predictions.labels,
            predictions.scores,
        )
    ]
