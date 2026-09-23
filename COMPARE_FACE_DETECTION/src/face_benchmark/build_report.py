from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .config import load_config, resolve_path
from .dataset import parse_wider_annotations
from .io import load_predictions, predictions_for_wider_eval
from .metrics import operating_point_metrics, wider_face_ap


LABELS = {
    "haar": "Haar Cascade – OpenCV frontal default",
    "mtcnn": "MTCNN – facenet-pytorch",
    "retinaface_mobilenet025": "RetinaFace – MobileNet0.25",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    project_root = Path(__file__).resolve().parents[2]
    config = load_config(run_dir / "config.snapshot.yaml")
    run_metadata = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    dataset_root = resolve_path(project_root, config["paths"]["dataset_root"])
    annotation_path = resolve_path(project_root, config["paths"]["annotation_txt"])
    ground_truth_dir = resolve_path(project_root, config["paths"]["ground_truth_dir"])
    records = parse_wider_annotations(annotation_path, dataset_root / "WIDER_val" / "images")
    if run_metadata.get("limit") is not None:
        raise RuntimeError("Official report cannot be built from a limited smoke-test run")

    rows: list[dict[str, object]] = []
    metrics_output: dict[str, object] = {}
    for detector_name in run_metadata["detectors"]:
        prediction_path = run_dir / "predictions" / f"{detector_name}.jsonl"
        predictions = load_predictions(prediction_path, repeat=0)
        wider_predictions = predictions_for_wider_eval(predictions)
        ap = wider_face_ap(
            wider_predictions,
            ground_truth_dir,
            iou_threshold=float(config["evaluation"]["iou_threshold"]),
            threshold_count=int(config["evaluation"]["pr_thresholds"]),
        )
        threshold = config["detectors"][detector_name].get("operating_threshold")
        operating = operating_point_metrics(
            records,
            predictions,
            score_threshold=threshold,
            iou_threshold=float(config["evaluation"]["iou_threshold"]),
        )
        timing = pd.read_csv(run_dir / "timing" / f"{detector_name}.csv")
        total_seconds = float(timing["latency_ms"].sum()) / 1000.0
        fps = len(timing) / total_seconds if total_seconds else 0.0
        row = {
            "model": LABELS[detector_name],
            "ap_easy": ap["easy"],
            "ap_medium": ap["medium"],
            "ap_hard": ap["hard"],
            "precision": operating.precision,
            "recall": operating.recall,
            "f1": operating.f1,
            "median_ms": float(np.median(timing["latency_ms"])),
            "p95_ms": float(np.percentile(timing["latency_ms"], 95)),
            "fps": fps,
            "no_detection_rate": operating.no_detection_rate,
            "false_positives_per_image": operating.false_positives_per_image,
            "load_ms": float(run_metadata["models"][detector_name]["load_ms"]),
            "peak_rss_bytes": int(timing["rss_bytes"].max()),
        }
        rows.append(row)
        metrics_output[detector_name] = row

    frame = pd.DataFrame(rows)
    frame.to_csv(run_dir / "comparison.csv", index=False)
    display = frame[
        [
            "model",
            "ap_easy",
            "ap_medium",
            "ap_hard",
            "precision",
            "recall",
            "f1",
            "median_ms",
            "p95_ms",
            "fps",
            "no_detection_rate",
        ]
    ].copy()
    for column in ["ap_easy", "ap_medium", "ap_hard", "precision", "recall", "f1", "no_detection_rate"]:
        display[column] = display[column].map(lambda value: f"{value:.4f}")
    for column in ["median_ms", "p95_ms", "fps"]:
        display[column] = display[column].map(lambda value: f"{value:.2f}")
    headers = [
        "Mô hình",
        "AP Easy",
        "AP Medium",
        "AP Hard",
        "Precision",
        "Recall",
        "F1",
        "Median ms",
        "P95 ms",
        "FPS",
        "Ảnh không phát hiện",
    ]
    display.columns = headers
    (run_dir / "comparison.md").write_text(display.to_markdown(index=False) + "\n", encoding="utf-8")
    (run_dir / "metrics.json").write_text(
        json.dumps(metrics_output, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(run_dir / "comparison.md")


if __name__ == "__main__":
    main()

