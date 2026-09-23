from __future__ import annotations

import itertools
import math
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
    if data["image_status"] != "VALID" or not data.get("embedding"):
        raise RuntimeError(f"Không tạo được embedding cho {path}: {data['image_status']}")
    return data["embedding"], data["models"]["embedding"]


def main() -> None:
    root = DATASET_ROOT / "calibration"
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
        score = (true_positive_rate + true_negative_rate) / 2
        candidate = (score, -threshold, threshold, true_positive_rate, true_negative_rate)
        if best is None or candidate > best:
            best = candidate
    assert best is not None
    artifact = {
        "version": f"demo-calibration-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "threshold": best[2],
        "selection_rule": "maximum balanced accuracy; ties choose the smaller threshold",
        "true_positive_rate": best[3],
        "true_negative_rate": best[4],
        "positive_pairs": len(positives),
        "negative_pairs": len(negatives),
        "subjects": sorted(embeddings),
        "embedding_model": model_version,
        "scope": "demo only; not a thesis evaluation result",
    }
    save_json(ARTIFACT_ROOT / "face-threshold.json", artifact)
    print(f"Đã tạo ngưỡng demo: {artifact['threshold']:.6f}")


if __name__ == "__main__":
    main()

