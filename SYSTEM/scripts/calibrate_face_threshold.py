from __future__ import annotations

import itertools
import json
import math
import statistics
from datetime import datetime, timezone

import httpx

from demo_common import ARTIFACT_ROOT, DATASET_ROOT, VISION_URL, save_json


def cosine_distance(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return 1 - dot / (norm_a * norm_b)


def analyze(path):
    with path.open("rb") as handle:
        response = httpx.post(f"{VISION_URL}/internal/v1/analyze-face", files={"image": (path.name, handle, "image/jpeg")}, timeout=120)
    response.raise_for_status()
    data = response.json()
    faces = data.get("faces", [])
    if data["image_status"] != "VALID" or len(faces) != 1 or not faces[0].get("embedding"):
        raise RuntimeError(f"Không tạo được embedding cho {path}: {data['image_status']}")
    return faces[0]["embedding"], data["models"]["embedding"]


def main() -> None:
    root = DATASET_ROOT / "calibration"
    manifest_path = DATASET_ROOT / "kdef_demo_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    embeddings: dict[str, list[list[float]]] = {}
    model_version = None
    for subject_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        embeddings[subject_dir.name] = []
        for image in sorted(subject_dir.glob("*.jpg")):
            embedding, model_version = analyze(image)
            embeddings[subject_dir.name].append(embedding)
    positives, negatives = [], []
    for subject, vectors in embeddings.items():
        positives.extend(cosine_distance(a, b) for a, b in itertools.combinations(vectors, 2))
        for other, other_vectors in embeddings.items():
            if other <= subject:
                continue
            negatives.extend(cosine_distance(a, b) for a in vectors for b in other_vectors)
    candidates = sorted(set(positives + negatives))
    best = None
    for threshold in candidates:
        true_positive_rate = sum(value <= threshold for value in positives) / len(positives)
        true_negative_rate = sum(value > threshold for value in negatives) / len(negatives)
        # Sai ghép khách nguy hiểm hơn bỏ sót trong luồng CRM. Ưu tiên tuyệt đối
        # ngưỡng không tạo false match trên tập calibration dành riêng, sau đó
        # tối đa hóa TPR và chọn ngưỡng lớn hơn nếu các chỉ số bằng nhau.
        candidate = (
            true_negative_rate == 1.0,
            true_positive_rate,
            true_negative_rate,
            threshold,
        )
        if best is None or candidate > best:
            best = candidate
    assert best is not None
    artifact = {
        "version": f"kdef-kaggle-operational-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "threshold": best[3],
        "selection_rule": (
            "require zero false matches on reserved calibration pairs; "
            "then maximize true-positive rate and choose the largest tied threshold"
        ),
        "true_positive_rate": best[1],
        "true_negative_rate": best[2],
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
            "operational threshold calibrated on reserved KDEF-Kaggle images; "
            "calibration files are excluded from replay and this is not a population-level accuracy claim"
        ),
    }
    save_json(ARTIFACT_ROOT / "face-threshold.json", artifact)
    print(f"Đã tạo ngưỡng đối sánh cho thực nghiệm vận hành: {artifact['threshold']:.6f}")


if __name__ == "__main__":
    main()
