from __future__ import annotations

import numpy as np
import pytest

from emotion_finetuning.model import prepare_images


def test_prepare_images_adds_grayscale_channel() -> None:
    images = np.zeros((3, 48, 48), dtype=np.uint8)
    prepared = prepare_images(images)
    assert prepared.shape == (3, 48, 48, 1)
    assert prepared.dtype == np.float32


def test_prepare_images_rejects_wrong_shape() -> None:
    with pytest.raises(ValueError, match="N x 48 x 48"):
        prepare_images(np.zeros((3, 32, 32), dtype=np.uint8))
