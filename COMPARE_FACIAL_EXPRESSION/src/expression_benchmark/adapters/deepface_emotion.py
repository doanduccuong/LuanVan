from __future__ import annotations

from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np

from ..constants import LABELS
from .base import PredictionBatch


class DeepFaceEmotionAdapter:
    """Run the pretrained Emotion model distributed through DeepFace."""

    method_name = "deepface_emotion"

    def __init__(
        self,
        *,
        batch_size: int = 128,
        weights_path: Path | None = None,
        model: Any | None = None,
    ) -> None:
        if batch_size < 1:
            raise ValueError("batch_size phải lớn hơn 0.")
        self.batch_size = batch_size
        self._package_version = "test-double"
        if model is None:
            try:
                from deepface import DeepFace
                from deepface.models.demography.DemographyUtils import EMOTION_LABELS
            except ImportError as exc:
                raise RuntimeError(
                    "Thiếu DeepFace. Chạy `uv sync --extra deepface` trước benchmark."
                ) from exc
            deepface_labels = tuple(str(label).title() for label in EMOTION_LABELS)
            if deepface_labels != LABELS:
                raise RuntimeError(
                    f"Thứ tự nhãn DeepFace không khớp FER-2013: {deepface_labels}."
                )
            model = DeepFace.build_model(
                model_name="Emotion",
                task="facial_attribute",
            )
            self._package_version = version("deepface")
        self.model = model
        if weights_path is not None:
            resolved_weights = weights_path.expanduser().resolve()
            if not resolved_weights.exists():
                raise FileNotFoundError(
                    f"Không tìm thấy trọng số Emotion: {resolved_weights}"
                )
            if not hasattr(self.model, "model"):
                raise TypeError("Emotion client không cung cấp mô hình Keras để nạp trọng số.")
            self.model.model.load_weights(str(resolved_weights))

    @property
    def package_version(self) -> str:
        return self._package_version

    def predict(self, images: np.ndarray) -> PredictionBatch:
        if images.ndim != 3:
            raise ValueError("Đầu vào DeepFace Emotion phải có dạng N x H x W.")
        if len(images) == 0:
            raise ValueError("Không có ảnh để phân loại.")

        score_batches: list[np.ndarray] = []
        for start in range(0, len(images), self.batch_size):
            grayscale = images[start : start + self.batch_size]
            # DeepFace Emotion nhận ảnh BGR rồi tự chuyển về ảnh xám 48 x 48.
            # Lặp lại kênh không làm thay đổi cường độ ảnh FER-2013.
            bgr = np.repeat(grayscale[..., None], 3, axis=-1)
            scores = np.asarray(self.model.predict(bgr), dtype=np.float64)
            if scores.ndim == 1:
                scores = scores[None, :]
            score_batches.append(scores)

        all_scores = np.concatenate(score_batches, axis=0)
        result = PredictionBatch(
            labels=np.argmax(all_scores, axis=1).astype(np.int64),
            scores=all_scores,
        )
        result.validate(len(images))
        return result
