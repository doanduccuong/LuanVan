from __future__ import annotations

import json
from pathlib import Path

import pytest

from expression_benchmark.build_report import build_comparison


def test_report_refuses_smoke_results(tmp_path: Path) -> None:
    (tmp_path / "run_manifest.json").write_text(
        json.dumps({"smoke_test": True, "final_evaluation": True}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="smoke"):
        build_comparison(tmp_path)


def test_report_contains_all_agreed_metrics(tmp_path: Path) -> None:
    (tmp_path / "run_manifest.json").write_text(
        json.dumps({"smoke_test": False, "final_evaluation": True}),
        encoding="utf-8",
    )
    training = tmp_path / "training"
    training.mkdir()
    (training / "lbp_svm.json").write_text(
        json.dumps(
            {
                "method": "lbp_svm",
                "model_size_bytes": 2 * 1024 * 1024,
                "private_test": {
                    "sample_count": 3589,
                    "accuracy": 0.5,
                    "macro_f1": 0.4,
                    "balanced_accuracy": 0.45,
                },
                "latency": {
                    "latency_p50_ms": 2.0,
                    "latency_p95_ms": 3.0,
                    "throughput_images_per_second": 400.0,
                },
            }
        ),
        encoding="utf-8",
    )

    row = build_comparison(tmp_path)[0]

    assert row == {
        "method": "lbp_svm",
        "sample_count": 3589,
        "macro_f1": 0.4,
        "accuracy": 0.5,
        "balanced_accuracy": 0.45,
        "latency_p50_ms": 2.0,
        "latency_p95_ms": 3.0,
        "throughput_images_per_second": 400.0,
        "model_size_mib": 2.0,
    }
