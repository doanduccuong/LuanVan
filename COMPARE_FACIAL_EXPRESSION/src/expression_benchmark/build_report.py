from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import yaml

from .constants import LABELS
from .io import write_json
from .select_model import aggregate_runs, select_method


def _display_name(run_name: str) -> str:
    if run_name == "lbp_svm":
        return "LBP + SVM"
    if run_name == "deepface_emotion":
        return "CNN Emotion trước tinh chỉnh"
    if run_name.startswith("deepface_emotion_finetuned"):
        return "CNN Emotion sau tinh chỉnh"
    return run_name


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_comparison(run_dir: Path) -> list[dict[str, Any]]:
    manifest = _load(run_dir / "run_manifest.json")
    if manifest.get("smoke_test"):
        raise ValueError("Không sinh bảng kết quả luận văn từ một smoke test.")
    if not manifest.get("final_evaluation"):
        raise ValueError("Lần chạy chưa đánh giá PrivateTest.")
    rows: list[dict[str, Any]] = []
    for path in sorted((run_dir / "training").glob("*.json")):
        payload = _load(path)
        if "private_test" not in payload:
            continue
        metrics = payload["private_test"]
        latency = payload.get("latency", {})
        rows.append(
            {
                "method": payload["method"],
                "seed": payload.get("seed", ""),
                "macro_f1": metrics["macro_f1"],
                "accuracy": metrics["accuracy"],
                "balanced_accuracy": metrics["balanced_accuracy"],
                "latency_p50_ms": latency.get("latency_p50_ms", ""),
                "latency_p95_ms": latency.get("latency_p95_ms", ""),
                "model_size_bytes": payload["model_size_bytes"],
            }
        )
    if not rows:
        raise ValueError("Không tìm thấy kết quả PrivateTest.")
    return rows


def _write_diagnostics(run_dir: Path) -> None:
    figures = run_dir / "figures"
    tables = run_dir / "tables"
    figures.mkdir(parents=True, exist_ok=True)
    per_class_rows: list[dict[str, Any]] = []
    for path in sorted((run_dir / "metrics").glob("*.json")):
        payload = _load(path)
        run_name = path.stem
        for row in payload["per_class"]:
            per_class_rows.append({"run": run_name, **row})
        matrix = np.asarray(payload["confusion_matrix_normalized"], dtype=np.float64)
        figure, axis = plt.subplots(figsize=(8, 7))
        image = axis.imshow(matrix, vmin=0.0, vmax=1.0, cmap="Blues")
        axis.set_xticks(range(len(LABELS)), LABELS, rotation=45, ha="right")
        axis.set_yticks(range(len(LABELS)), LABELS)
        axis.set_xlabel("Nhãn dự đoán")
        axis.set_ylabel("Nhãn thật")
        axis.set_title(f"Normalized Confusion Matrix — {_display_name(run_name)}")
        for row_index in range(matrix.shape[0]):
            for column_index in range(matrix.shape[1]):
                value = matrix[row_index, column_index]
                axis.text(
                    column_index,
                    row_index,
                    f"{value:.2f}",
                    ha="center",
                    va="center",
                    color="white" if value > 0.5 else "black",
                    fontsize=8,
                )
        figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
        figure.tight_layout()
        figure.savefig(figures / f"confusion_matrix_{run_name}.png", dpi=200)
        plt.close(figure)
    if per_class_rows:
        fieldnames = list(per_class_rows[0])
        with (tables / "per_class.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(per_class_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sinh bảng so sánh từ kết quả thô.")
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    rows = build_comparison(args.run_dir)
    config_text = (args.run_dir / "resolved_config.yaml").read_text(encoding="utf-8")
    config = yaml.safe_load(config_text)
    aggregate = aggregate_runs(rows)
    selection = select_method(
        aggregate,
        tie_margin=float(config["selection"]["tie_margin"]),
    )
    tables = args.run_dir / "tables"
    tables.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0])
    with (tables / "comparison.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    header = "| " + " | ".join(fieldnames) + " |"
    separator = "| " + " | ".join("---" for _ in fieldnames) + " |"
    lines = [header, separator]
    lines.extend("| " + " | ".join(str(row[key]) for key in fieldnames) + " |" for row in rows)
    (tables / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    aggregate_fields = list(aggregate[0])
    with (tables / "comparison_aggregate.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=aggregate_fields)
        writer.writeheader()
        writer.writerows(aggregate)
    aggregate_header = "| " + " | ".join(aggregate_fields) + " |"
    aggregate_separator = "| " + " | ".join("---" for _ in aggregate_fields) + " |"
    aggregate_lines = [aggregate_header, aggregate_separator]
    aggregate_lines.extend(
        "| " + " | ".join(str(row[key]) for key in aggregate_fields) + " |"
        for row in aggregate
    )
    (tables / "comparison_aggregate.md").write_text(
        "\n".join(aggregate_lines) + "\n", encoding="utf-8"
    )
    write_json(args.run_dir / "selection.json", selection)
    _write_diagnostics(args.run_dir)
    print(f"Đã sinh bảng tại: {tables}")


if __name__ == "__main__":
    main()
