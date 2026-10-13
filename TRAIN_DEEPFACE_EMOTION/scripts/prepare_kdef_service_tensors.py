from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
from deepface import DeepFace
from deepface.modules import detection, preprocessing

from app.engine import RetinaFaceMobileNetDetector, align_face


LABELS = ("Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral")
FILENAME_PATTERN = re.compile(r"^(?P<group>\d+)_(?P<image>\d+)\.(?:jpg|jpeg)$", re.I)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def discover(root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    label_lookup = {label.lower(): label for label in LABELS}
    for path in sorted(root.rglob("*.jpg")):
        label = label_lookup.get(path.parent.name.lower())
        match = FILENAME_PATTERN.fullmatch(path.name)
        if label is None or match is None:
            continue
        rows.append(
            {
                "path": path,
                "relative_path": str(path.relative_to(root)),
                "group": f"KG{int(match.group('group')):03d}",
                "label": label,
                "label_id": LABELS.index(label),
                "sha256": sha256_file(path),
            }
        )
    if not rows:
        raise ValueError(f"Không tìm thấy ảnh KDEF trong {root}")
    return rows


def service_tensor(
    image: np.ndarray,
    detector: RetinaFaceMobileNetDetector,
    emotion_client: object,
) -> np.ndarray:
    detections = detector.detect(image)
    if len(detections) != 1:
        raise ValueError(f"Cần đúng một khuôn mặt, nhận {len(detections)}")
    aligned = align_face(image, detections[0]["landmarks"])
    face = detection.extract_faces(
        aligned,
        detector_backend="skip",
        enforce_detection=False,
        align=False,
        normalize_face=True,
    )[0]["face"]
    bgr = face[:, :, ::-1]
    padded = preprocessing.resize_image(img=bgr, target_size=(224, 224))[0]
    tensor = emotion_client._preprocess_image(padded).astype(np.float32)
    if tensor.shape != (48, 48):
        raise ValueError(f"Tensor Emotion có kích thước không hợp lệ: {tensor.shape}")
    if float(tensor.min()) < 0.0 or float(tensor.max()) > 1.0:
        raise ValueError("Tensor Emotion phải nằm trong khoảng 0..1")
    return tensor


def main(
    source: Path,
    experiment_manifest: Path,
    output: Path,
    manifest_output: Path,
    seed: int,
    validation_ratio: float,
) -> None:
    if output.exists() or manifest_output.exists():
        raise FileExistsError("Không ghi đè bộ tensor KDEF đã tồn tại")
    experiment = json.loads(experiment_manifest.read_text(encoding="utf-8"))
    evaluation_groups = set(experiment["selected_subjects"])
    rows = discover(source)

    digests: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        digests[str(row["sha256"])].append(row)
    duplicate_digests = {digest for digest, items in digests.items() if len(items) > 1}
    usable = [row for row in rows if row["sha256"] not in duplicate_digests]

    candidate_groups = sorted({str(row["group"]) for row in usable} - evaluation_groups)
    if len(candidate_groups) < 2:
        raise ValueError("Không đủ nhóm KDEF để tách huấn luyện và xác thực")
    validation_count = max(1, round(len(candidate_groups) * validation_ratio))
    validation_groups = set(random.Random(seed).sample(candidate_groups, validation_count))
    training_groups = set(candidate_groups) - validation_groups

    detector = RetinaFaceMobileNetDetector()
    emotion_client = DeepFace.build_model(model_name="Emotion", task="facial_attribute")
    split_images: dict[str, list[np.ndarray]] = {"training": [], "validation": []}
    split_labels: dict[str, list[int]] = {"training": [], "validation": []}
    split_groups: dict[str, list[str]] = {"training": [], "validation": []}
    split_paths: dict[str, list[str]] = {"training": [], "validation": []}
    failures: list[dict[str, str]] = []

    selected_rows = [row for row in usable if row["group"] not in evaluation_groups]
    for index, row in enumerate(selected_rows, 1):
        path = Path(row["path"])
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            failures.append({"path": str(row["relative_path"]), "reason": "decode_failed"})
            continue
        try:
            tensor = service_tensor(image, detector, emotion_client)
        except (ValueError, KeyError, TypeError, cv2.error) as exc:
            failures.append({"path": str(row["relative_path"]), "reason": str(exc)})
            continue
        split = "validation" if row["group"] in validation_groups else "training"
        split_images[split].append(tensor)
        split_labels[split].append(int(row["label_id"]))
        split_groups[split].append(str(row["group"]))
        split_paths[split].append(str(row["relative_path"]))
        if index % 200 == 0:
            print(f"Đã chuẩn bị {index}/{len(selected_rows)} ảnh KDEF", flush=True)

    for split in ("training", "validation"):
        present = set(split_labels[split])
        if present != set(range(len(LABELS))):
            raise ValueError(f"Tập {split} không đủ bảy lớp: {sorted(present)}")

    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output,
        training_images=np.stack(split_images["training"]).astype(np.float32),
        training_labels=np.asarray(split_labels["training"], dtype=np.int64),
        training_groups=np.asarray(split_groups["training"]),
        training_paths=np.asarray(split_paths["training"]),
        validation_images=np.stack(split_images["validation"]).astype(np.float32),
        validation_labels=np.asarray(split_labels["validation"], dtype=np.int64),
        validation_groups=np.asarray(split_groups["validation"]),
        validation_paths=np.asarray(split_paths["validation"]),
    )
    payload = {
        "source": str(source.resolve()),
        "source_image_count": len(rows),
        "source_sha256_by_file": {
            str(row["relative_path"]): str(row["sha256"]) for row in rows
        },
        "tensor_archive": str(output.resolve()),
        "tensor_archive_sha256": sha256_file(output),
        "labels": list(LABELS),
        "seed": seed,
        "validation_ratio": validation_ratio,
        "training_groups": sorted(training_groups),
        "validation_groups": sorted(validation_groups),
        "evaluation_groups": sorted(evaluation_groups),
        "evaluation_groups_used_for_training": False,
        "training_count": len(split_labels["training"]),
        "validation_count": len(split_labels["validation"]),
        "training_class_counts": dict(
            Counter(LABELS[value] for value in split_labels["training"])
        ),
        "validation_class_counts": dict(
            Counter(LABELS[value] for value in split_labels["validation"])
        ),
        "excluded_duplicate_digest_count": len(duplicate_digests),
        "excluded_duplicate_file_count": sum(len(digests[value]) for value in duplicate_digests),
        "preprocessing_failures": failures,
        "preprocessing": "RetinaFace-MobileNet -> ArcFace landmark alignment 112x112 -> DeepFace Emotion 48x48, range 0..1",
    }
    manifest_output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Hoàn tất: training={payload['training_count']}, "
        f"validation={payload['validation_count']}, failures={len(failures)}",
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--experiment-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261013)
    parser.add_argument("--validation-ratio", type=float, default=0.2)
    args = parser.parse_args()
    if not 0.05 <= args.validation_ratio <= 0.5:
        raise SystemExit("validation-ratio phải nằm trong [0.05, 0.5]")
    main(
        args.source.resolve(),
        args.experiment_manifest.resolve(),
        args.output.resolve(),
        args.manifest_output.resolve(),
        args.seed,
        args.validation_ratio,
    )
