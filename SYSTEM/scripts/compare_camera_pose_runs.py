"""Compare saved direct-vision predictions for two camera-pose datasets."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from demo_common import ARTIFACT_ROOT, save_json


def main(baseline_run: str, candidate_run: str) -> None:
    baseline_root = ARTIFACT_ROOT / "experiment-runs" / baseline_run
    candidate_root = ARTIFACT_ROOT / "experiment-runs" / candidate_run
    baseline_summary = json.loads((baseline_root / "checkpoint-comparison.json").read_text())
    candidate_summary = json.loads((candidate_root / "image-variant-comparison.json").read_text())
    baseline_rows = json.loads((baseline_root / "checkpoint-comparison-predictions.json").read_text())
    candidate_rows = json.loads((candidate_root / "image-variant-predictions.json").read_text())

    baseline_by_path = {row["image_path"]: row for row in baseline_rows}
    candidate_by_path = {row["image_path"]: row for row in candidate_rows}
    if set(baseline_by_path) != set(candidate_by_path) or len(candidate_by_path) != 100:
        raise ValueError("Hai lần chạy phải có cùng 100 vị trí sự kiện")

    outcomes: Counter[str] = Counter()
    changed_labels = 0
    for image_path in sorted(candidate_by_path):
        baseline = baseline_by_path[image_path]
        candidate = candidate_by_path[image_path]
        if baseline["expected_label"] != candidate["expected_label"]:
            raise ValueError(f"Nhãn đối chiếu không khớp tại {image_path}")
        expected = candidate["expected_label"]
        old_label = baseline["finetuned_weights"]["label"]
        new_label = candidate["native"]["label"]
        outcomes[
            f"baseline_correct={old_label == expected},candidate_correct={new_label == expected}"
        ] += 1
        changed_labels += int(old_label != new_label)

    old_metrics = baseline_summary["finetuned_weights"]
    new_metrics = candidate_summary["native"]
    result = {
        "scope": (
            "Direct vision predictions before identity matching; identical event positions, "
            "expected labels, timestamps and fine-tuned Emotion weights; source pose changed"
        ),
        "baseline_run_id": baseline_run,
        "candidate_run_id": candidate_run,
        "baseline": old_metrics,
        "candidate": new_metrics,
        "delta": {
            "correct_count": new_metrics["correct_count"] - old_metrics["correct_count"],
            "accuracy": new_metrics["end_to_end_accuracy"] - old_metrics["end_to_end_accuracy"],
            "macro_f1": new_metrics["macro_f1"] - old_metrics["macro_f1"],
        },
        "paired_outcomes": dict(outcomes),
        "changed_predicted_labels": changed_labels,
    }
    save_json(candidate_root / "camera-pose-comparison.json", result)
    print(json.dumps(result["delta"], ensure_ascii=False))
    print(json.dumps(result["paired_outcomes"], ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-run", required=True)
    parser.add_argument("--candidate-run", required=True)
    args = parser.parse_args()
    main(args.baseline_run, args.candidate_run)
