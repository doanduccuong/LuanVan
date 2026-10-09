from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .constants import (
    ALL_SPLITS,
    LABELS,
    PIXEL_COUNT,
    PRIVATE_SPLIT,
    TRAINING_SPLIT,
    VALIDATION_SPLIT,
)
from .io import sha256_file


@dataclass(frozen=True)
class SplitData:
    images: np.ndarray
    labels: np.ndarray
    sample_ids: tuple[str, ...]

    def __len__(self) -> int:
        return int(self.labels.size)


@dataclass(frozen=True)
class TrainingBundle:
    training: SplitData
    validation: SplitData
    manifest: dict[str, Any]


def _parse_pixels(raw: str, row_number: int) -> np.ndarray:
    pixels = np.fromstring(raw, dtype=np.int16, sep=" ")
    if pixels.size != PIXEL_COUNT:
        raise ValueError(
            f"Dòng {row_number}: cần {PIXEL_COUNT} điểm ảnh, nhận {pixels.size}."
        )
    if np.any((pixels < 0) | (pixels > 255)):
        raise ValueError(f"Dòng {row_number}: điểm ảnh phải nằm trong khoảng 0..255.")
    return pixels.astype(np.uint8).reshape(48, 48)


def load_training_bundle(
    path: Path,
    *,
    expected_counts: dict[str, int],
    strict_counts: bool,
    fail_on_cross_split_duplicates: bool,
) -> TrainingBundle:
    """Load Training/PublicTest and count PrivateTest without exposing it to training."""
    stored_splits = (TRAINING_SPLIT, VALIDATION_SPLIT)
    images: dict[str, list[np.ndarray]] = {split: [] for split in stored_splits}
    labels: dict[str, list[int]] = {split: [] for split in stored_splits}
    sample_ids: dict[str, list[str]] = {split: [] for split in stored_splits}
    counts = {split: 0 for split in ALL_SPLITS}
    class_counts = {
        split: {label: 0 for label in LABELS} for split in ALL_SPLITS
    }
    digests: dict[str, set[str]] = {split: set() for split in ALL_SPLITS}

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("Tệp FER-2013 không có dòng tiêu đề.")
        canonical = {name.strip().lower(): name for name in reader.fieldnames}
        required = {"emotion", "pixels", "usage"}
        if not required.issubset(canonical):
            raise ValueError(f"Thiếu cột: {sorted(required - set(canonical))}")

        for row_number, row in enumerate(reader, start=2):
            split = row[canonical["usage"]].strip()
            if split not in ALL_SPLITS:
                raise ValueError(f"Dòng {row_number}: Usage không hợp lệ: {split!r}.")
            try:
                label = int(row[canonical["emotion"]])
            except ValueError as exc:
                raise ValueError(f"Dòng {row_number}: nhãn không phải số nguyên.") from exc
            if not 0 <= label < len(LABELS):
                raise ValueError(f"Dòng {row_number}: nhãn ngoài khoảng 0..6.")

            image = _parse_pixels(row[canonical["pixels"]], row_number)
            counts[split] += 1
            class_counts[split][LABELS[label]] += 1
            digests[split].add(hashlib.sha256(image.tobytes()).hexdigest())
            if split != PRIVATE_SPLIT:
                images[split].append(image)
                labels[split].append(label)
                sample_ids[split].append(f"{split}:{row_number - 2:05d}")

    if strict_counts and counts != expected_counts:
        raise ValueError(f"Số mẫu không khớp: nhận {counts}, cần {expected_counts}.")

    overlaps: dict[str, int] = {}
    for index, left in enumerate(ALL_SPLITS):
        for right in ALL_SPLITS[index + 1 :]:
            overlaps[f"{left}__{right}"] = len(digests[left] & digests[right])
    if fail_on_cross_split_duplicates and any(overlaps.values()):
        raise ValueError(f"Phát hiện ảnh trùng hoàn toàn giữa các tập: {overlaps}.")

    def create_split(name: str) -> SplitData:
        return SplitData(
            images=np.stack(images[name]),
            labels=np.asarray(labels[name], dtype=np.int64),
            sample_ids=tuple(sample_ids[name]),
        )

    return TrainingBundle(
        training=create_split(TRAINING_SPLIT),
        validation=create_split(VALIDATION_SPLIT),
        manifest={
            "source_path": str(path.resolve()),
            "dataset_sha256": sha256_file(path),
            "counts": counts,
            "class_counts": class_counts,
            "cross_split_exact_duplicates": overlaps,
            "loaded_splits": [TRAINING_SPLIT, VALIDATION_SPLIT],
            "private_test_used": False,
            "labels": list(LABELS),
        },
    )


def balanced_class_weights(labels: np.ndarray) -> dict[int, float]:
    counts = np.bincount(labels, minlength=len(LABELS)).astype(np.float64)
    if np.any(counts == 0):
        raise ValueError(f"Training thiếu lớp: {np.flatnonzero(counts == 0).tolist()}.")
    weights = labels.size / (len(LABELS) * counts)
    return {index: float(value) for index, value in enumerate(weights)}
