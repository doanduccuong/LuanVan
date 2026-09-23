from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .types import Detection, PredictionRecord


def append_jsonl(path: Path, record: PredictionRecord) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")


def load_predictions(path: Path, repeat: int = 0) -> dict[str, list[Detection]]:
    predictions: dict[str, list[Detection]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            payload = json.loads(line)
            if int(payload["repeat"]) != repeat:
                continue
            predictions[payload["image_id"]] = [Detection(**item) for item in payload["detections"]]
    return predictions


def predictions_for_wider_eval(
    predictions: dict[str, list[Detection]],
) -> dict[str, dict[str, np.ndarray]]:
    output: dict[str, dict[str, np.ndarray]] = {}
    for image_id, detections in predictions.items():
        event, filename = image_id.split("/", maxsplit=1)
        stem = Path(filename).stem
        rows = [
            [item.x1, item.y1, item.x2 - item.x1, item.y2 - item.y1, item.score]
            for item in sorted(detections, key=lambda value: value.score, reverse=True)
        ]
        output.setdefault(event, {})[stem] = np.asarray(rows, dtype=np.float64).reshape(-1, 5)
    return output


def write_wider_text(output_root: Path, image_id: str, detections: list[Detection]) -> None:
    event, filename = image_id.split("/", maxsplit=1)
    output_path = output_root / event / f"{Path(filename).stem}.txt"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [filename, str(len(detections))]
    lines.extend(
        f"{item.x1:.3f} {item.y1:.3f} {item.x2 - item.x1:.3f} "
        f"{item.y2 - item.y1:.3f} {item.score:.8f}"
        for item in detections
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

