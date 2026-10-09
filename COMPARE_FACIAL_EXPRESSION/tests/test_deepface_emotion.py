from __future__ import annotations

import numpy as np
from pathlib import Path

from expression_benchmark.adapters.deepface_emotion import DeepFaceEmotionAdapter


class FakeEmotionModel:
    def __init__(self) -> None:
        self.batch_shapes: list[tuple[int, ...]] = []

    def predict(self, images: np.ndarray) -> np.ndarray:
        self.batch_shapes.append(images.shape)
        scores = np.zeros((len(images), 7), dtype=np.float64)
        labels = images[:, 0, 0, 0].astype(int) % 7
        scores[np.arange(len(images)), labels] = 1.0
        return scores


class FakeKerasModel:
    def __init__(self) -> None:
        self.loaded_path: str | None = None

    def load_weights(self, path: str) -> None:
        self.loaded_path = path


class FakeEmotionClient(FakeEmotionModel):
    def __init__(self) -> None:
        super().__init__()
        self.model = FakeKerasModel()


def test_deepface_adapter_batches_grayscale_images_as_three_channels() -> None:
    model = FakeEmotionModel()
    adapter = DeepFaceEmotionAdapter(batch_size=2, model=model)
    images = np.stack([np.full((48, 48), value, np.uint8) for value in (0, 1, 2)])

    predictions = adapter.predict(images)

    assert predictions.labels.tolist() == [0, 1, 2]
    assert predictions.scores.shape == (3, 7)
    assert model.batch_shapes == [(2, 48, 48, 3), (1, 48, 48, 3)]


def test_deepface_adapter_can_load_an_external_checkpoint(tmp_path: Path) -> None:
    checkpoint = tmp_path / "emotion.weights.h5"
    checkpoint.write_bytes(b"test checkpoint")
    client = FakeEmotionClient()

    DeepFaceEmotionAdapter(
        batch_size=2,
        weights_path=checkpoint,
        model=client,
    )

    assert client.model.loaded_path == str(checkpoint.resolve())
