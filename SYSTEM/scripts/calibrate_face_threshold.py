from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import statistics
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import httpx

from app.threshold_calibration import (
    build_roc_curve,
    cosine_distance,
    roc_auc,
    select_roc_threshold,
)
from demo_common import ARTIFACT_ROOT, DATASET_ROOT, VISION_URL, save_json


def analyze(path):
    with path.open("rb") as handle:
        response = httpx.post(f"{VISION_URL}/internal/v1/analyze-face", files={"image": (path.name, handle, "image/jpeg")}, timeout=120)
    response.raise_for_status()
    data = response.json()
    faces = data.get("faces", [])
    if data["image_status"] != "VALID" or len(faces) != 1 or not faces[0].get("embedding"):
        raise RuntimeError(f"Không tạo được embedding cho {path}: {data['image_status']}")
    return faces[0]["embedding"], data["models"]["embedding"]


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Hiệu chỉnh ngưỡng đối sánh ArcFace từ thư mục calibration."
    )
    parser.add_argument("--dataset-root", type=Path, default=DATASET_ROOT)
    parser.add_argument("--artifact-root", type=Path, default=ARTIFACT_ROOT)
    parser.add_argument("--target-fpr", type=float, default=0.10)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset_root = args.dataset_root.expanduser().resolve()
    artifact_root = args.artifact_root.expanduser().resolve()
    root = dataset_root / "calibration"
    manifest_path = dataset_root / "kdef_demo_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    cache_path = dataset_root / "arcface_embeddings.json"
    cache = (
        json.loads(cache_path.read_text(encoding="utf-8"))
        if cache_path.exists()
        else {"images": {}}
    )
    cached_images = cache.setdefault("images", {})
    embeddings: dict[str, list[list[float]]] = {}
    model_version = None
    image_paths = [
        image
        for subject_dir in sorted(path for path in root.iterdir() if path.is_dir())
        for image in sorted(subject_dir.glob("*.jpg"))
    ]
    processed = 0
    for subject_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        embeddings[subject_dir.name] = []
        for image in sorted(subject_dir.glob("*.jpg")):
            relative_path = str(image.relative_to(dataset_root))
            digest = file_sha256(image)
            cached = cached_images.get(relative_path)
            if cached and cached.get("sha256") == digest:
                embedding = cached["embedding"]
                model_version = cached["model_version"]
            else:
                embedding, model_version = analyze(image)
                cached_images[relative_path] = {
                    "sha256": digest,
                    "embedding": embedding,
                    "model_version": model_version,
                }
            embeddings[subject_dir.name].append(embedding)
            processed += 1
            if processed % 10 == 0 or processed == len(image_paths):
                save_json(cache_path, cache)
                print(
                    f"Đã tạo embedding {processed}/{len(image_paths)} ảnh",
                    flush=True,
                )
    positives, negatives = [], []
    for subject, vectors in embeddings.items():
        positives.extend(cosine_distance(a, b) for a, b in itertools.combinations(vectors, 2))
        for other, other_vectors in embeddings.items():
            if other <= subject:
                continue
            negatives.extend(cosine_distance(a, b) for a in vectors for b in other_vectors)
    target_false_positive_rate = args.target_fpr
    roc_points = build_roc_curve(positives, negatives)
    selected_point = select_roc_threshold(roc_points, target_false_positive_rate)
    artifact = {
        "version": f"kdef-kaggle-operational-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "threshold": selected_point.threshold,
        "selection_method": "roc-operating-point-at-target-fpr",
        "selection_rule": (
            "maximize true-positive rate subject to false-positive rate <= target; "
            "ties choose the largest threshold"
        ),
        "target_false_positive_rate": target_false_positive_rate,
        "true_positive_rate": selected_point.true_positive_rate,
        "false_positive_rate": selected_point.false_positive_rate,
        "true_negative_rate": 1.0 - selected_point.false_positive_rate,
        "roc_auc": roc_auc(roc_points),
        "roc_points": [asdict(point) for point in roc_points],
        "positive_pairs": len(positives),
        "negative_pairs": len(negatives),
        "subjects": sorted(embeddings),
        "embedding_model": model_version,
        "source_distribution": manifest.get("distribution"),
        "source_url": manifest.get("distribution_url"),
        "experiment_run_id": manifest.get("experiment_run_id"),
        "calibration_images": sum(len(vectors) for vectors in embeddings.values()),
        "positive_distance_summary": {
            "min": min(positives),
            "median": statistics.median(positives),
            "max": max(positives),
        },
        "negative_distance_summary": {
            "min": min(negatives),
            "median": statistics.median(negatives),
            "max": max(negatives),
        },
        "scope": (
            "operational threshold calibrated on reserved KDEF images; "
            "calibration files are excluded from replay and this is not a population-level accuracy claim"
        ),
    }
    save_json(artifact_root / "face-threshold.json", artifact)
    run_root = artifact_root / "experiment-runs" / manifest["experiment_run_id"]
    save_json(run_root / "face-threshold.json", artifact)
    save_json(run_root / "calibration-distances.json", {
        "positive_distances": positives,
        "negative_distances": negatives,
        "scope": "Pairs share images and are not independent trials.",
    })
    print(f"Đã tạo ngưỡng đối sánh cho thực nghiệm vận hành: {artifact['threshold']:.6f}")


if __name__ == "__main__":
    main()
