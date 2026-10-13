"""Compare the current checkpoint with saved predictions on identical native images."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import httpx

from compare_camera_image_variants import events, metrics
from demo_common import ARTIFACT_ROOT, VISION_URL, save_json


def main(native: Path, baseline_run: str, model_digest: str) -> None:
    manifest = json.loads((native / "kdef_demo_manifest.json").read_text())
    run_root = ARTIFACT_ROOT / "experiment-runs" / manifest["experiment_run_id"]
    baseline_root = ARTIFACT_ROOT / "experiment-runs" / baseline_run
    baseline_rows = json.loads((baseline_root / "image-variant-predictions.json").read_text())
    baseline_by_image = {row["image_path"]: row for row in baseline_rows}
    rows, cache = [], {}
    expected_version = f"deepface-emotion-finetuned:{model_digest[:12]}"
    with httpx.Client(timeout=120) as client:
        for index, event in enumerate(events(native), 1):
            baseline = baseline_by_image[event["image_path"]]
            assert baseline["expected_label"] == event["expected_expression_label"]
            path = native / event["image_path"]
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            assert digest == baseline["native"]["input_sha256"]
            if digest not in cache:
                response = client.post(f"{VISION_URL}/internal/v1/analyze-face",
                                       files={"image": (path.name, data, "image/jpeg")})
                response.raise_for_status()
                cache[digest] = response.json()
            payload = cache[digest]
            assert payload["models"]["emotion"] == expected_version
            faces = payload.get("faces", [])
            face = faces[0] if len(faces) == 1 else {}
            expression = face.get("expression") or {}
            rows.append({"image_path": event["image_path"],
                         "expected_label": event["expected_expression_label"],
                         "event_id": event["event_id"],
                         "original_weights": baseline["native"],
                         "finetuned_weights": {"label": expression.get("label", "Missing"),
                                               "confidence": expression.get("confidence"),
                                               "scores": expression.get("scores"),
                                               "face_count": payload["face_count"],
                                               "models": payload["models"],
                                               "input_sha256": digest}})
            if index % 20 == 0:
                print(f"Verified {index}/100 same-image checkpoint comparisons", flush=True)
    summary = {"scope": "Direct vision predictions before customer matching; byte-identical native images",
               "baseline_run_id": baseline_run,
               "original_weights": metrics(rows, "original_weights"),
               "finetuned_weights": metrics(rows, "finetuned_weights"),
               "paired_outcomes": dict(Counter(
                   f"original_correct={row['original_weights']['label'] == row['expected_label']},"
                   f"finetuned_correct={row['finetuned_weights']['label'] == row['expected_label']}"
                   for row in rows)),
               "changed_labels": sum(row["original_weights"]["label"] != row["finetuned_weights"]["label"]
                                     for row in rows),
               "finetuned_model_sha256": model_digest}
    save_json(run_root / "checkpoint-comparison.json", summary)
    save_json(run_root / "checkpoint-comparison-predictions.json", rows)
    print(json.dumps({name: {k: v for k, v in summary[name].items() if k not in ("per_class", "confusion_matrix")}
                      for name in ("original_weights", "finetuned_weights")}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--baseline-run", required=True)
    parser.add_argument("--model-sha256", required=True)
    args = parser.parse_args()
    main(args.native.resolve(), args.baseline_run, args.model_sha256)
