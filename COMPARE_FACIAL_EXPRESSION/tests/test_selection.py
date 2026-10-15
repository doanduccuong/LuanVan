from __future__ import annotations

import pytest

from expression_benchmark.select_model import aggregate_runs, select_method


def test_aggregate_runs_reports_mean_and_std() -> None:
    rows = [
        {
            "method": "cnn",
            "macro_f1": 0.6,
            "accuracy": 0.7,
            "balanced_accuracy": 0.6,
            "latency_p95_ms": 10.0,
            "throughput_images_per_second": 100.0,
            "model_size_mib": 10.0,
        },
        {
            "method": "cnn",
            "macro_f1": 0.8,
            "accuracy": 0.9,
            "balanced_accuracy": 0.8,
            "latency_p95_ms": 12.0,
            "throughput_images_per_second": 90.0,
            "model_size_mib": 10.0,
        },
    ]
    result = aggregate_runs(rows)[0]
    assert result["macro_f1_mean"] == pytest.approx(0.7)
    assert result["macro_f1_std"] == pytest.approx(0.1)


def test_selection_uses_macro_f1_as_primary_metric() -> None:
    rows = [
        {
            "method": "accurate",
            "macro_f1_mean": 0.75,
            "latency_p95_ms_mean": 20.0,
            "model_size_mib_mean": 200.0,
        },
        {
            "method": "fast",
            "macro_f1_mean": 0.745,
            "latency_p95_ms_mean": 5.0,
            "model_size_mib_mean": 100.0,
        },
    ]
    assert select_method(rows)["selected_method"] == "accurate"
