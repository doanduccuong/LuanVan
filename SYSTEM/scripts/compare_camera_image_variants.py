"""Compare native and rendered frames through the same running vision service."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import httpx

from demo_common import ARTIFACT_ROOT, VISION_URL, save_json


LABELS = ("Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral")


def events(root: Path) -> list[dict[str, str]]:
    with (root / "events.csv").open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def metrics(rows: list[dict], variant: str) -> dict:
    pairs = [(row["expected_label"], row[variant]["label"]) for row in rows]
    confusion = {
        label: {predicted: sum(a == label and b == predicted for a, b in pairs)
                for predicted in (*LABELS, "Missing")}
        for label in LABELS
    }
    classes = {}
    for label in LABELS:
        tp = sum(a == b == label for a, b in pairs)
        fp = sum(a != label and b == label for a, b in pairs)
        fn = sum(a == label and b != label for a, b in pairs)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        classes[label] = {"correct": tp, "support": tp + fn,
                          "precision": precision, "recall": recall,
                          "f1": 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0}
    available = sum(b != "Missing" for _, b in pairs)
    correct = sum(a == b for a, b in pairs)
    return {"input_count": len(pairs), "available_predictions": available,
            "correct_count": correct, "end_to_end_accuracy": correct / len(pairs),
            "accuracy_on_available": correct / available if available else 0.0,
            "macro_f1": sum(v["f1"] for v in classes.values()) / len(LABELS),
            "per_class": classes, "confusion_matrix": confusion}


def main(baseline: Path, native: Path) -> None:
    baseline_events, native_events = events(baseline), events(native)
    baseline_by_image = {row["image_path"]: row for row in baseline_events}
    run_id = json.loads((native / "kdef_demo_manifest.json").read_text())["experiment_run_id"]
    output = ARTIFACT_ROOT / "experiment-runs" / run_id
    cache = {}
    rows = []
    with httpx.Client(timeout=120) as client:
        for index, native_event in enumerate(native_events, 1):
            baseline_event = baseline_by_image[native_event["image_path"]]
            for key in ("source_filename", "expected_expression_label", "observed_at", "touchpoint_code"):
                assert baseline_event[key] == native_event[key]
            row = {"image_path": native_event["image_path"],
                   "expected_label": native_event["expected_expression_label"],
                   "event_id": native_event["event_id"]}
            for variant, root in (("rendered", baseline), ("native", native)):
                path = root / native_event["image_path"]
                data = path.read_bytes()
                digest = hashlib.sha256(data).hexdigest()
                if digest not in cache:
                    response = client.post(f"{VISION_URL}/internal/v1/analyze-face",
                                           files={"image": (path.name, data, "image/jpeg")})
                    response.raise_for_status()
                    cache[digest] = response.json()
                payload = cache[digest]
                faces = payload.get("faces", [])
                face = faces[0] if len(faces) == 1 else {}
                expression = face.get("expression") or {}
                row[variant] = {"label": expression.get("label", "Missing"),
                                "confidence": expression.get("confidence"),
                                "scores": expression.get("scores"),
                                "image_status": payload["image_status"],
                                "face_count": payload["face_count"],
                                "box": face.get("box"), "models": payload["models"],
                                "input_sha256": digest}
            assert row["rendered"]["models"] == row["native"]["models"]
            rows.append(row)
            if index % 20 == 0:
                print(f"Compared {index}/100 frame pairs", flush=True)
    summary = {"scope": "Direct vision predictions before customer matching; same 100 source selections",
               "rendered": metrics(rows, "rendered"), "native": metrics(rows, "native"),
               "paired_outcomes": dict(Counter(
                   f"rendered_correct={row['rendered']['label'] == row['expected_label']},"
                   f"native_correct={row['native']['label'] == row['expected_label']}"
                   for row in rows)),
               "changed_labels": sum(row["native"]["label"] != row["rendered"]["label"] for row in rows)}
    save_json(output / "image-variant-comparison.json", summary)
    save_json(output / "image-variant-predictions.json", rows)
    print(json.dumps({name: {k: v for k, v in summary[name].items() if k not in ("per_class", "confusion_matrix")}
                      for name in ("rendered", "native")}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    args = parser.parse_args()
    main(args.baseline.resolve(), args.native.resolve())
