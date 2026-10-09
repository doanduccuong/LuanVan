from __future__ import annotations

from collections import defaultdict
from typing import Any

import numpy as np


def aggregate_runs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row["method"])].append(row)
    output: list[dict[str, Any]] = []
    for method, method_rows in sorted(grouped.items()):
        metric_values = np.asarray([row["macro_f1"] for row in method_rows], dtype=np.float64)
        accuracy_values = np.asarray([row["accuracy"] for row in method_rows], dtype=np.float64)
        balanced_values = np.asarray(
            [row["balanced_accuracy"] for row in method_rows], dtype=np.float64
        )
        latency_values = np.asarray(
            [row["latency_p95_ms"] for row in method_rows], dtype=np.float64
        )
        size_values = np.asarray([row["model_size_bytes"] for row in method_rows], dtype=np.float64)
        output.append(
            {
                "method": method,
                "runs": len(method_rows),
                "macro_f1_mean": float(metric_values.mean()),
                "macro_f1_std": float(metric_values.std(ddof=0)),
                "accuracy_mean": float(accuracy_values.mean()),
                "accuracy_std": float(accuracy_values.std(ddof=0)),
                "balanced_accuracy_mean": float(balanced_values.mean()),
                "balanced_accuracy_std": float(balanced_values.std(ddof=0)),
                "latency_p95_ms_mean": float(latency_values.mean()),
                "model_size_bytes_mean": float(size_values.mean()),
            }
        )
    return output


def select_method(
    aggregate_rows: list[dict[str, Any]],
    *,
    tie_margin: float,
) -> dict[str, Any]:
    if not aggregate_rows:
        raise ValueError("Không có kết quả để lựa chọn phương pháp.")
    best_macro_f1 = max(float(row["macro_f1_mean"]) for row in aggregate_rows)
    eligible = [
        row
        for row in aggregate_rows
        if best_macro_f1 - float(row["macro_f1_mean"]) < tie_margin
    ]
    selected = min(
        eligible,
        key=lambda row: (
            float(row["latency_p95_ms_mean"]),
            float(row["model_size_bytes_mean"]),
            str(row["method"]),
        ),
    )
    return {
        "selected_method": selected["method"],
        "best_macro_f1": best_macro_f1,
        "tie_margin": tie_margin,
        "eligible_methods": [row["method"] for row in eligible],
        "decision_rule": (
            "Giữ các phương pháp cách Macro-F1 cao nhất ít hơn tie_margin; "
            "nếu có nhiều phương pháp thì chọn P95 thấp hơn, sau đó mô hình nhỏ hơn."
        ),
        "selected_metrics": selected,
    }
