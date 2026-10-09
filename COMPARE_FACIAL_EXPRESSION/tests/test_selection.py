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
            "model_size_bytes": 100,
        },
        {
            "method": "cnn",
            "macro_f1": 0.8,
            "accuracy": 0.9,
            "balanced_accuracy": 0.8,
            "latency_p95_ms": 12.0,
            "model_size_bytes": 100,
        },
    ]
    result = aggregate_runs(rows)[0]
    assert result["macro_f1_mean"] == pytest.approx(0.7)
    assert result["macro_f1_std"] == pytest.approx(0.1)


def test_selection_uses_latency_only_within_margin() -> None:
    rows = [
        {
            "method": "accurate",
            "macro_f1_mean": 0.75,
            "latency_p95_ms_mean": 20.0,
            "model_size_bytes_mean": 200.0,
        },
        {
            "method": "fast",
            "macro_f1_mean": 0.745,
            "latency_p95_ms_mean": 5.0,
            "model_size_bytes_mean": 100.0,
        },
    ]
    assert select_method(rows, tie_margin=0.01)["selected_method"] == "fast"
    assert select_method(rows, tie_margin=0.001)["selected_method"] == "accurate"
