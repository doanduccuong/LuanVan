from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass(frozen=True)
class PredictionBatch:
    labels: np.ndarray
    scores: np.ndarray

    def validate(self, sample_count: int, class_count: int = 7) -> None:
        if self.labels.shape != (sample_count,):
            raise ValueError(f"Nhãn dự đoán có kích thước sai: {self.labels.shape}.")
        if self.scores.shape != (sample_count, class_count):
            raise ValueError(f"Điểm dự đoán có kích thước sai: {self.scores.shape}.")
        if not np.all(np.isfinite(self.scores)):
            raise ValueError("Điểm dự đoán chứa NaN hoặc vô cực.")


class ClassifierAdapter(ABC):
    method_name: str

    @abstractmethod
    def fit(self, images: np.ndarray, labels: np.ndarray, **kwargs: object) -> dict[str, object]:
        raise NotImplementedError

    @abstractmethod
    def predict(self, images: np.ndarray) -> PredictionBatch:
        raise NotImplementedError

    @abstractmethod
    def save(self, path: Path) -> None:
        raise NotImplementedError
