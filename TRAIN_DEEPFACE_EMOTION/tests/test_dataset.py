from __future__ import annotations

import csv
from pathlib import Path

from emotion_finetuning.dataset import load_training_bundle


def _pixels(value: int) -> str:
    return " ".join([str(value)] * (48 * 48))


def test_private_test_is_counted_but_not_exposed_to_trainer(tmp_path: Path) -> None:
    path = tmp_path / "fer2013.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["emotion", "pixels", "Usage"])
        writer.writeheader()
        writer.writerow({"emotion": 0, "pixels": _pixels(1), "Usage": "Training"})
        writer.writerow({"emotion": 1, "pixels": _pixels(2), "Usage": "PublicTest"})
        writer.writerow({"emotion": 2, "pixels": _pixels(3), "Usage": "PrivateTest"})

    bundle = load_training_bundle(
        path,
        expected_counts={"Training": 1, "PublicTest": 1, "PrivateTest": 1},
        strict_counts=True,
        fail_on_cross_split_duplicates=True,
    )

    assert len(bundle.training) == 1
    assert len(bundle.validation) == 1
    assert bundle.manifest["private_test_used"] is False
    assert bundle.manifest["loaded_splits"] == ["Training", "PublicTest"]
