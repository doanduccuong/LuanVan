"""Create a paired camera dataset using untouched source files for observations."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path

from PIL import Image


def checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def save_rows(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main(baseline: Path, source: Path, output: Path, run_id: str) -> None:
    if output.exists():
        raise ValueError(f"Output already exists: {output}")
    manifest = json.loads((baseline / "kdef_demo_manifest.json").read_text())
    old_run = manifest["experiment_run_id"]
    fields, images = load_rows(baseline / "image_manifest.csv")
    replacements = []
    for row in images:
        if row["role"] != "observation":
            continue
        matches = list(source.rglob(row["source_filename"]))
        matches = [path for path in matches if checksum(path) == row["source_sha256"]]
        if len(matches) != 1:
            raise ValueError(f"Cannot uniquely resolve source: {row['source_filename']}")
        replacements.append((row, matches[0]))
    if len(replacements) != 100:
        raise ValueError("Expected exactly 100 observation images")
    shutil.copytree(baseline, output)
    sizes: Counter[str] = Counter()
    for row, source_image in replacements:
        target = output / row["output"]
        shutil.copy2(source_image, target)
        width, height = Image.open(target).size
        sizes[f"{width}x{height}"] += 1
        row.update({
            "output_sha256": checksum(target), "canvas_width": str(width),
            "canvas_height": str(height), "offset_x": "0", "offset_y": "0",
            "target_height": str(height), "brightness": "0",
        })
        assert row["output_sha256"] == row["source_sha256"]
    save_rows(output / "image_manifest.csv", fields, images)
    event_fields, events = load_rows(output / "events.csv")
    for event in events:
        for key in ("experiment_run_id", "event_id", "expected_visit_key"):
            event[key] = event[key].replace(old_run, run_id)
    save_rows(output / "events.csv", event_fields, events)
    expected_path = output / "expected/expected_visits.json"
    expected_path.write_text(expected_path.read_text().replace(old_run, run_id), encoding="utf-8")
    manifest.update({
        "experiment_run_id": run_id,
        "baseline_run_id": old_run,
        "camera_layouts": None,
        "camera_image_protocol": "byte-identical-source-no-resize-no-canvas-no-brightness-change",
        "observation_image_dimensions": dict(sizes),
        "unchanged_inputs": ["source selection", "labels", "timestamps", "enrollment", "calibration"],
    })
    (output / "kdef_demo_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Prepared {len(events)} native-size observations; dimensions={dict(sizes)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    main(args.baseline.resolve(), args.source.resolve(), args.output.resolve(), args.run_id)
