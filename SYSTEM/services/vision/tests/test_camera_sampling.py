import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from prepare_kdef_demo import (
    partition_kaggle_sources,
    sample_camera_images,
    sample_touchpoint_time_offsets,
)


def pools():
    return {label: [Path(f"{label}-{i}.jpg") for i in range(3)]
            for label in ("Angry", "Disgust", "Fear", "Happy", "Neutral", "Sad", "Surprise")}


def test_camera_sampling_reproducible_and_seed_sensitive():
    first = sample_camera_images(pools(), random.Random(20261013), 100)
    assert first == sample_camera_images(pools(), random.Random(20261013), 100)
    assert first != sample_camera_images(pools(), random.Random(20261014), 100)
    assert len(first) == 100
    assert {label for label, _ in first} == set(pools())
    assert all(path in pools()[label] for label, path in first)


def test_camera_sampling_rejects_missing_label_pool():
    source = pools()
    source["Fear"] = []
    with pytest.raises(ValueError):
        sample_camera_images(source, random.Random(1), 100)


def test_frontal_camera_partition_is_disjoint_and_keeps_first_candidate():
    source = pools()
    enrollment, calibration, camera = partition_kaggle_sources(
        source,
        "frontal-camera",
    )

    assert enrollment == source["Neutral"][1]
    assert calibration["Neutral"] == source["Neutral"][2]
    assert all(camera[label] == [source[label][0]] for label in source)
    reserved = {enrollment, *calibration.values()}
    assert not reserved & {path for paths in camera.values() for path in paths}


def test_touchpoint_time_offsets_are_reproducible_bounded_and_variable():
    first_rng = random.Random(20261013)
    second_rng = random.Random(20261013)
    first = [sample_touchpoint_time_offsets(first_rng, 4) for _ in range(25)]
    assert first == [sample_touchpoint_time_offsets(second_rng, 4) for _ in range(25)]
    gaps = [later - earlier for offsets in first for earlier, later in zip(offsets, offsets[1:])]
    assert all(5 <= gap <= 15 for gap in gaps)
    assert len(set(gaps)) > 1
