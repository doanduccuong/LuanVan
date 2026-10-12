from __future__ import annotations

import math
from dataclasses import dataclass


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
    """Build ROC points for a distance score where smaller means a match."""
    if not positive_distances or not negative_distances:
        raise ValueError("Cần cả khoảng cách cặp cùng người và khác người")
    distances = positive_distances + negative_distances
    if not all(math.isfinite(value) for value in distances):
        raise ValueError("Khoảng cách phải là số hữu hạn")

    observed_thresholds = sorted(set(distances))
    thresholds = [math.nextafter(observed_thresholds[0], -math.inf), *observed_thresholds]
    return [
        RocPoint(
            threshold=threshold,
            true_positive_rate=sum(value <= threshold for value in positive_distances)
            / len(positive_distances),
            false_positive_rate=sum(value <= threshold for value in negative_distances)
            / len(negative_distances),
        )
        for threshold in thresholds
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
    """Compute the trapezoidal area under an ROC curve ordered by threshold."""
    if not roc_points:
        raise ValueError("Đường ROC không được rỗng")
    area = 0.0
    for left, right in zip(roc_points, roc_points[1:], strict=False):
        width = right.false_positive_rate - left.false_positive_rate
        area += width * (left.true_positive_rate + right.true_positive_rate) / 2.0
    return area
