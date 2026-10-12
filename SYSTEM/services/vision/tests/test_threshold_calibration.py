from __future__ import annotations

import pytest

from app.threshold_calibration import build_roc_curve, roc_auc, select_roc_threshold


def test_build_roc_curve_from_distance_thresholds():
    points = build_roc_curve([0.20, 0.40], [0.50, 0.70])

    assert [(point.false_positive_rate, point.true_positive_rate) for point in points] == [
        (0.0, 0.0),
        (0.0, 0.5),
        (0.0, 1.0),
        (0.5, 1.0),
        (1.0, 1.0),
    ]


def test_select_roc_threshold_maximizes_tpr_at_target_fpr():
    points = build_roc_curve([0.20, 0.40], [0.50, 0.70])

    selected = select_roc_threshold(points, target_false_positive_rate=0.0)

    assert selected.threshold == pytest.approx(0.40)
    assert selected.true_positive_rate == pytest.approx(1.0)
    assert selected.false_positive_rate == pytest.approx(0.0)


def test_roc_auc_uses_all_threshold_points():
    points = build_roc_curve([0.20, 0.40], [0.50, 0.70])

    assert roc_auc(points) == pytest.approx(1.0)


def test_roc_curve_requires_both_pair_types():
    with pytest.raises(ValueError, match="Cần cả"):
        build_roc_curve([0.20], [])
