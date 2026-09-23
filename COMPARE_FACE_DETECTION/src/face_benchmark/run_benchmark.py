from __future__ import annotations

import argparse
import gc
import json
import random
import shutil
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import psutil
import torch
from tqdm import tqdm

from .adapters import HaarDetector, MTCNNDetector, RetinaFaceMobileNetDetector
from .config import load_config, resolve_path
from .dataset import parse_wider_annotations, validate_dataset, write_manifest
from .environment import write_environment
from .io import append_jsonl, write_wider_text
from .types import PredictionRecord


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _build_detector(name: str, config: dict[str, Any], project_root: Path):
    detector_config = config["detectors"][name]
    device = config["run"]["device"]
    if name == "haar":
        return HaarDetector(detector_config)
    if name == "mtcnn":
        return MTCNNDetector(detector_config, device=device)
    if name == "retinaface_mobilenet025":
        return RetinaFaceMobileNetDetector(
            detector_config,
            vendor_path=resolve_path(project_root, config["paths"]["retinaface_vendor"]),
            weights_path=resolve_path(project_root, config["paths"]["retinaface_weights"]),
            device=device,
        )
    raise ValueError(f"Unknown detector: {name}")


def _clip_detections(detections, width: int, height: int):
    from .types import Detection

    output = []
    for item in detections:
        x1 = min(max(item.x1, 0.0), float(width))
        y1 = min(max(item.y1, 0.0), float(height))
        x2 = min(max(item.x2, 0.0), float(width))
        y2 = min(max(item.y2, 0.0), float(height))
        if x2 > x1 and y2 > y1:
            output.append(Detection(x1, y1, x2, y2, item.score))
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("configs/benchmark.yaml"))
    parser.add_argument(
        "--detectors",
        nargs="+",
        default=["haar", "mtcnn", "retinaface_mobilenet025"],
    )
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    project_root = _project_root()
    config_path = args.config if args.config.is_absolute() else project_root / args.config
    config = load_config(config_path)
    torch.set_num_threads(int(config["run"]["torch_threads"]))
    torch.set_num_interop_threads(1)
    cv2.setNumThreads(int(config["run"]["opencv_threads"]))
    random.seed(int(config["run"]["seed"]))
    np.random.seed(int(config["run"]["seed"]))

    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    results_root = resolve_path(project_root, config["paths"]["results_root"]) / run_id
    results_root.mkdir(parents=True, exist_ok=False)
    shutil.copy2(config_path, results_root / "config.snapshot.yaml")
    write_environment(results_root / "environment.json")

    dataset_root = resolve_path(project_root, config["paths"]["dataset_root"])
    annotation_path = resolve_path(project_root, config["paths"]["annotation_txt"])
    images_root = dataset_root / "WIDER_val" / "images"
    records = parse_wider_annotations(annotation_path, images_root)
    if args.limit is not None:
        records = records[: args.limit]
    if args.limit is None:
        ground_truth_dir = resolve_path(project_root, config["paths"]["ground_truth_dir"])
        artifact_paths = [
            project_root / "data" / "WIDER_val.zip",
            project_root / "data" / "wider_face_split.zip",
            ground_truth_dir / "wider_face_val.mat",
            ground_truth_dir / "wider_easy_val.mat",
            ground_truth_dir / "wider_medium_val.mat",
            ground_truth_dir / "wider_hard_val.mat",
            resolve_path(project_root, config["paths"]["retinaface_weights"]),
        ]
        manifest = validate_dataset(records, annotation_path, artifact_paths=artifact_paths)
        write_manifest(manifest, results_root / "dataset_manifest.json")
        if not manifest["valid"]:
            raise RuntimeError("Dataset validation failed; see dataset_manifest.json")
    run_metadata: dict[str, Any] = {
        "run_id": run_id,
        "image_count": len(records),
        "limit": args.limit,
        "detectors": args.detectors,
        "models": {},
    }
    warmup_count = min(int(config["run"]["warmup_images"]), len(records))
    repeats = int(config["run"]["repeats"])

    detectors: dict[str, Any] = {}
    timing_rows: dict[str, list[str]] = {}
    for detector_name in args.detectors:
        detector = _build_detector(detector_name, config, project_root)
        load_started = time.perf_counter_ns()
        detector.load()
        load_ms = (time.perf_counter_ns() - load_started) / 1_000_000
        for record in records[:warmup_count]:
            image = cv2.imread(record.path, cv2.IMREAD_COLOR)
            if image is None:
                raise RuntimeError(f"Cannot read warm-up image: {record.path}")
            detector.detect(image)
        detectors[detector_name] = detector
        timing_rows[detector_name] = [
            "repeat,image_id,latency_ms,width,height,detection_count,rss_bytes"
        ]
        run_metadata["models"][detector_name] = {"load_ms": load_ms}

    process = psutil.Process()
    detector_names = list(args.detectors)
    for repeat in range(repeats):
        rotation = repeat % len(detector_names)
        repeat_order = detector_names[rotation:] + detector_names[:rotation]
        for detector_name in repeat_order:
            detector = detectors[detector_name]
            prediction_path = results_root / "predictions" / f"{detector_name}.jsonl"
            wider_output = results_root / "wider_txt" / detector_name
            gc.collect()
            for record in tqdm(records, desc=f"{detector_name} repeat {repeat + 1}/{repeats}"):
                image = cv2.imread(record.path, cv2.IMREAD_COLOR)
                if image is None:
                    raise RuntimeError(f"Cannot read image: {record.path}")
                height, width = image.shape[:2]
                started = time.perf_counter_ns()
                detections = detector.detect(image)
                latency_ms = (time.perf_counter_ns() - started) / 1_000_000
                detections = _clip_detections(detections, width, height)
                prediction_record = PredictionRecord(
                    image_id=record.image_id,
                    detections=tuple(detections),
                    latency_ms=latency_ms,
                    repeat=repeat,
                )
                append_jsonl(prediction_path, prediction_record)
                if repeat == 0:
                    write_wider_text(wider_output, record.image_id, detections)
                timing_rows[detector_name].append(
                    f"{repeat},{record.image_id},{latency_ms:.8f},{width},{height},"
                    f"{len(detections)},{process.memory_info().rss}"
                )

    for detector_name in detector_names:
        timing_path = results_root / "timing" / f"{detector_name}.csv"
        timing_path.parent.mkdir(parents=True, exist_ok=True)
        timing_path.write_text("\n".join(timing_rows[detector_name]) + "\n", encoding="utf-8")
    detectors.clear()
    gc.collect()

    (results_root / "run.json").write_text(
        json.dumps(run_metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(results_root)


if __name__ == "__main__":
    main()
