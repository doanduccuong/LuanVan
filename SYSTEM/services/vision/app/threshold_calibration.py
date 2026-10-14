from __future__ import annotations

import math
from dataclasses import dataclass

from sklearn.metrics import auc, roc_curve


@dataclass(frozen=True)
class RocPoint:
    threshold: float
    true_positive_rate: float
    false_positive_rate: float


def cosine_distance(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        raise ValueError("Hai véc-tơ phải có cùng số chiều và không được rỗng")
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        raise ValueError("Véc-tơ không được bằng không")
    return 1 - dot / (norm_a * norm_b)


def build_roc_curve(
    positive_distances: list[float],
    negative_distances: list[float],
) -> list[RocPoint]:
    """Build ROC points with scikit-learn for distances where smaller means a match."""
    if not positive_distances or not negative_distances:
        raise ValueError("Cần cả khoảng cách cặp cùng người và khác người")
    distances = positive_distances + negative_distances
    if not all(math.isfinite(value) for value in distances):
        raise ValueError("Khoảng cách phải là số hữu hạn")

    labels = [1] * len(positive_distances) + [0] * len(negative_distances)
    scores = [-value for value in distances]
    false_positive_rates, true_positive_rates, score_thresholds = roc_curve(
        labels,
        scores,
        pos_label=1,
        drop_intermediate=False,
    )
    below_minimum = math.nextafter(min(distances), -math.inf)
    return [
        RocPoint(
            threshold=(
                below_minimum
                if math.isinf(score_threshold)
                else -float(score_threshold)
            ),
            true_positive_rate=float(true_positive_rate),
            false_positive_rate=float(false_positive_rate),
        )
        for false_positive_rate, true_positive_rate, score_threshold in zip(
            false_positive_rates,
            true_positive_rates,
            score_thresholds,
            strict=True,
        )
    ]


def select_roc_threshold(
    roc_points: list[RocPoint],
    target_false_positive_rate: float,
) -> RocPoint:
    """Maximize TPR subject to the target FPR; use the largest tied threshold."""
    if not 0.0 <= target_false_positive_rate <= 1.0:
        raise ValueError("FPR mục tiêu phải nằm trong đoạn [0, 1]")
    eligible = [
        point
        for point in roc_points
        if point.false_positive_rate <= target_false_positive_rate
    ]
    if not eligible:
        raise ValueError("Không có điểm ROC đáp ứng FPR mục tiêu")
    return max(eligible, key=lambda point: (point.true_positive_rate, point.threshold))


def roc_auc(roc_points: list[RocPoint]) -> float:
    """Compute ROC AUC with scikit-learn from points ordered by threshold."""
    if not roc_points:
        raise ValueError("Đường ROC không được rỗng")
    return float(
        auc(
            [point.false_positive_rate for point in roc_points],
            [point.true_positive_rate for point in roc_points],
        )
    )
