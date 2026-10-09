from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .constants import EXPECTED_COUNTS, LABELS, PIXEL_COUNT, SPLITS
from .io import sha256_file


@dataclass(frozen=True)
class SplitData:
    images: np.ndarray
    labels: np.ndarray
    sample_ids: tuple[str, ...]

    def __len__(self) -> int:
        return int(self.labels.shape[0])


@dataclass(frozen=True)
class FERBundle:
    splits: dict[str, SplitData]
    manifest: dict[str, Any]


def _parse_pixels(raw: str, row_number: int) -> np.ndarray:
    pixels = np.fromstring(raw, dtype=np.int16, sep=" ")
    if pixels.size != PIXEL_COUNT:
        raise ValueError(
            f"Dòng {row_number}: cần {PIXEL_COUNT} điểm ảnh, nhận được {pixels.size}."
        )
    if np.any((pixels < 0) | (pixels > 255)):
        raise ValueError(f"Dòng {row_number}: điểm ảnh phải nằm trong khoảng 0..255.")
    return pixels.astype(np.uint8).reshape(48, 48)


def load_fer2013(
    path: Path,
    *,
    strict_counts: bool = True,
    expected_counts: dict[str, int] | None = None,
    fail_on_cross_split_duplicates: bool = True,
    training_fraction: float = 1.0,
    sampling_seed: int = 0,
    limits: dict[str, int] | None = None,
) -> FERBundle:
    """Load FER-2013 without changing the published Usage split."""
    if not 0.0 < training_fraction <= 1.0:
        raise ValueError("training_fraction phải nằm trong khoảng (0, 1].")
    if limits is not None and training_fraction < 1.0:
        raise ValueError("Không kết hợp limits với training_fraction < 1.0.")

    expected = expected_counts or EXPECTED_COUNTS
    images: dict[str, list[np.ndarray]] = {split: [] for split in SPLITS}
    labels: dict[str, list[int]] = {split: [] for split in SPLITS}
    sample_ids: dict[str, list[str]] = {split: [] for split in SPLITS}
    image_digests: dict[str, list[str]] = {split: [] for split in SPLITS}
    class_counts: dict[str, dict[str, int]] = {
        split: {label: 0 for label in LABELS} for split in SPLITS
    }

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("Tệp FER-2013 không có dòng tiêu đề.")
        canonical = {name.strip().lower(): name for name in reader.fieldnames}
        required = {"emotion", "pixels", "usage"}
        if not required.issubset(canonical):
            raise ValueError(f"Thiếu cột FER-2013: {sorted(required - set(canonical))}")

        for row_number, row in enumerate(reader, start=2):
            split = row[canonical["usage"]].strip()
            if split not in SPLITS:
                raise ValueError(f"Dòng {row_number}: Usage không hợp lệ: {split!r}.")
            limit = None if limits is None else limits.get(split)
            if limit is not None and len(images[split]) >= limit:
                continue
            try:
                label = int(row[canonical["emotion"]])
            except ValueError as error:
                raise ValueError(f"Dòng {row_number}: nhãn không phải số nguyên.") from error
            if not 0 <= label < len(LABELS):
                raise ValueError(f"Dòng {row_number}: nhãn ngoài khoảng 0..6: {label}.")
            image = _parse_pixels(row[canonical["pixels"]], row_number)
            digest = hashlib.sha256(image.tobytes()).hexdigest()
            images[split].append(image)
            labels[split].append(label)
            sample_ids[split].append(f"{split}:{row_number - 2:05d}")
            image_digests[split].append(digest)
            class_counts[split][LABELS[label]] += 1

    source_counts = {split: len(images[split]) for split in SPLITS}
    if strict_counts and source_counts != expected:
        raise ValueError(
            f"Số mẫu không khớp FER-2013 gốc: nhận {source_counts}, cần {expected}."
        )

    source_hashes = {split: set(image_digests[split]) for split in SPLITS}
    source_overlaps: dict[str, int] = {}
    for index, left in enumerate(SPLITS):
        for right in SPLITS[index + 1 :]:
            source_overlaps[f"{left}__{right}"] = len(source_hashes[left] & source_hashes[right])

    training_subset: dict[str, Any] = {
        "enabled": training_fraction < 1.0,
        "fraction": training_fraction,
        "seed": sampling_seed,
        "source_count": source_counts["Training"],
    }
    if training_fraction < 1.0:
        training_labels = np.asarray(labels["Training"], dtype=np.int64)
        selected_indices = _stratified_indices(training_labels, training_fraction, sampling_seed)
        images["Training"] = [images["Training"][index] for index in selected_indices]
        labels["Training"] = [labels["Training"][index] for index in selected_indices]
        sample_ids["Training"] = [sample_ids["Training"][index] for index in selected_indices]
        image_digests["Training"] = [image_digests["Training"][index] for index in selected_indices]

    counts = {split: len(images[split]) for split in SPLITS}
    class_counts = {
        split: {
            label_name: int(np.count_nonzero(np.asarray(labels[split]) == label_id))
            for label_id, label_name in enumerate(LABELS)
        }
        for split in SPLITS
    }
    selected_ids_text = "\n".join(sample_ids["Training"]).encode("utf-8")
    training_subset.update(
        {
            "selected_count": counts["Training"],
            "class_counts": class_counts["Training"],
            "sample_ids_sha256": hashlib.sha256(selected_ids_text).hexdigest(),
            "sample_ids": sample_ids["Training"],
        }
    )

    image_hashes = {split: set(image_digests[split]) for split in SPLITS}
    overlaps: dict[str, int] = {}
    for index, left in enumerate(SPLITS):
        for right in SPLITS[index + 1 :]:
            overlaps[f"{left}__{right}"] = len(image_hashes[left] & image_hashes[right])
    if fail_on_cross_split_duplicates and any(overlaps.values()):
        raise ValueError(f"Phát hiện ảnh trùng hoàn toàn giữa các tập: {overlaps}.")

    split_data = {
        split: SplitData(
            images=np.stack(images[split]) if images[split] else np.empty((0, 48, 48), np.uint8),
            labels=np.asarray(labels[split], dtype=np.int64),
            sample_ids=tuple(sample_ids[split]),
        )
        for split in SPLITS
    }
    manifest: dict[str, Any] = {
        "source_path": str(path),
        "source_sha256": sha256_file(path),
        "source_counts": source_counts,
        "counts": counts,
        "class_counts": class_counts,
        "source_cross_split_exact_duplicates": source_overlaps,
        "cross_split_exact_duplicates": overlaps,
        "training_subset": training_subset,
        "labels": list(LABELS),
        "strict_counts": strict_counts,
        "limited_load": limits is not None,
    }
    return FERBundle(splits=split_data, manifest=manifest)


def _stratified_indices(labels: np.ndarray, fraction: float, seed: int) -> np.ndarray:
    """Select an exact-size, deterministic subset while preserving class proportions."""
    class_ids, class_sizes = np.unique(labels, return_counts=True)
    target_size = int(round(labels.size * fraction))
    if target_size < class_ids.size:
        raise ValueError("Tập con quá nhỏ để giữ ít nhất một mẫu cho mỗi lớp.")

    raw_sizes = class_sizes.astype(np.float64) * fraction
    selected_sizes = np.floor(raw_sizes).astype(np.int64)
    selected_sizes = np.maximum(selected_sizes, 1)

    difference = target_size - int(selected_sizes.sum())
    remainders = raw_sizes - np.floor(raw_sizes)
    if difference > 0:
        order = np.argsort(-remainders, kind="stable")
        for position in range(difference):
            selected_sizes[order[position % order.size]] += 1
    elif difference < 0:
        order = np.argsort(remainders, kind="stable")
        for class_position in order:
            while difference < 0 and selected_sizes[class_position] > 1:
                selected_sizes[class_position] -= 1
                difference += 1
            if difference == 0:
                break
    if int(selected_sizes.sum()) != target_size:
        raise ValueError("Không thể phân bổ kích thước tập con theo lớp.")

    generator = np.random.default_rng(seed)
    selected: list[np.ndarray] = []
    for class_id, class_size in zip(class_ids, selected_sizes, strict=True):
        class_indices = np.flatnonzero(labels == class_id)
        selected.append(generator.choice(class_indices, size=int(class_size), replace=False))
    return np.sort(np.concatenate(selected))


def class_weights(labels: np.ndarray, class_count: int = 7) -> np.ndarray:
    counts = np.bincount(labels, minlength=class_count).astype(np.float64)
    if np.any(counts == 0):
        missing = np.flatnonzero(counts == 0).tolist()
        raise ValueError(f"Tập huấn luyện thiếu lớp: {missing}.")
    return labels.size / (class_count * counts)
