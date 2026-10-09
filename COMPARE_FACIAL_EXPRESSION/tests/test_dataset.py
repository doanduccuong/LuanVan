from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import pytest

from expression_benchmark.dataset import class_weights, load_fer2013


def _write_csv(path: Path, rows: list[tuple[int, str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["emotion", "pixels", "Usage"])
        writer.writerows(rows)


def _pixels(value: int) -> str:
    return " ".join([str(value)] * 2304)


def test_loads_three_published_splits(tmp_path: Path) -> None:
    path = tmp_path / "fer.csv"
    _write_csv(
        path,
        [
            (0, _pixels(1), "Training"),
            (1, _pixels(2), "PublicTest"),
            (2, _pixels(3), "PrivateTest"),
        ],
    )
    bundle = load_fer2013(path, strict_counts=False)
    assert bundle.manifest["counts"] == {"Training": 1, "PublicTest": 1, "PrivateTest": 1}
    assert bundle.splits["Training"].images.shape == (1, 48, 48)


def test_rejects_wrong_pixel_count(tmp_path: Path) -> None:
    path = tmp_path / "fer.csv"
    _write_csv(path, [(0, "1 2 3", "Training")])
    with pytest.raises(ValueError, match="2304"):
        load_fer2013(path, strict_counts=False)


def test_rejects_cross_split_duplicate(tmp_path: Path) -> None:
    path = tmp_path / "fer.csv"
    _write_csv(
        path,
        [(0, _pixels(7), "Training"), (0, _pixels(7), "PublicTest")],
    )
    with pytest.raises(ValueError, match="trùng"):
        load_fer2013(path, strict_counts=False)


def test_class_weights_are_computed_from_supplied_labels() -> None:
    labels = np.repeat(np.arange(7), np.arange(1, 8))
    weights = class_weights(labels)
    assert weights.shape == (7,)
    assert weights[0] > weights[-1]


def test_stratified_training_subset_is_deterministic(tmp_path: Path) -> None:
    path = tmp_path / "fer.csv"
    rows: list[tuple[int, str, str]] = []
    pixel_value = 1
    for label in range(7):
        for _ in range(4):
            rows.append((label, _pixels(pixel_value), "Training"))
            pixel_value += 1
    rows.extend(
        [
            (0, _pixels(100), "PublicTest"),
            (0, _pixels(101), "PrivateTest"),
        ]
    )
    _write_csv(path, rows)

    first = load_fer2013(
        path,
        strict_counts=False,
        fail_on_cross_split_duplicates=False,
        training_fraction=0.25,
        sampling_seed=123,
    )
    second = load_fer2013(
        path,
        strict_counts=False,
        fail_on_cross_split_duplicates=False,
        training_fraction=0.25,
        sampling_seed=123,
    )

    assert first.manifest["source_counts"]["Training"] == 28
    assert first.manifest["counts"] == {"Training": 7, "PublicTest": 1, "PrivateTest": 1}
    assert first.manifest["class_counts"]["Training"] == {
        label: 1 for label in first.manifest["labels"]
    }
    assert first.manifest["training_subset"]["sample_ids"] == second.manifest[
        "training_subset"
    ]["sample_ids"]
    assert first.splits["PublicTest"].sample_ids == ("PublicTest:00028",)
    assert first.splits["PrivateTest"].sample_ids == ("PrivateTest:00029",)


def test_rejects_invalid_training_fraction(tmp_path: Path) -> None:
    path = tmp_path / "fer.csv"
    _write_csv(path, [(0, _pixels(1), "Training")])
    with pytest.raises(ValueError, match="training_fraction"):
        load_fer2013(path, strict_counts=False, training_fraction=0.0)
