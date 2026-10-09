from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.svm import SVC

from .base import ClassifierAdapter, PredictionBatch


_OFFSETS = (
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, 1),
    (1, 1),
    (1, 0),
    (1, -1),
    (0, -1),
)


def _uniform_lbp(image: np.ndarray) -> np.ndarray:
    if image.ndim != 2:
        raise ValueError("LBP yêu cầu một ảnh xám hai chiều.")
    center = image[1:-1, 1:-1]
    bits = []
    for dy, dx in _OFFSETS:
        neighbor = image[1 + dy : image.shape[0] - 1 + dy, 1 + dx : image.shape[1] - 1 + dx]
        bits.append(neighbor >= center)
    bit_stack = np.stack(bits, axis=-1).astype(np.uint8)
    transitions = np.sum(bit_stack != np.roll(bit_stack, -1, axis=-1), axis=-1)
    ones = np.sum(bit_stack, axis=-1)
    return np.where(transitions <= 2, ones, 9).astype(np.uint8)


def extract_spatial_lbp(images: np.ndarray, grid_rows: int = 6, grid_cols: int = 6) -> np.ndarray:
    if images.ndim != 3:
        raise ValueError("Đầu vào LBP phải có dạng N x H x W.")
    output = np.empty((images.shape[0], grid_rows * grid_cols * 10), dtype=np.float32)
    for image_index, image in enumerate(images):
        codes = _uniform_lbp(image)
        row_parts = np.array_split(np.arange(codes.shape[0]), grid_rows)
        col_parts = np.array_split(np.arange(codes.shape[1]), grid_cols)
        features: list[np.ndarray] = []
        for rows in row_parts:
            for cols in col_parts:
                block = codes[np.ix_(rows, cols)]
                histogram = np.bincount(block.ravel(), minlength=10).astype(np.float32)
                histogram /= max(float(histogram.sum()), 1.0)
                features.append(histogram)
        output[image_index] = np.concatenate(features)
    return output


class LBPSVMAdapter(ClassifierAdapter):
    method_name = "lbp_svm"

    def __init__(
        self,
        *,
        grid_rows: int = 6,
        grid_cols: int = 6,
        kernel: str = "linear",
        c: float = 1.0,
        gamma: str | float = "scale",
        class_weight: dict[int, float] | None = None,
        seed: int = 0,
    ) -> None:
        self.grid_rows = grid_rows
        self.grid_cols = grid_cols
        self.model = SVC(
            kernel=kernel,
            C=c,
            gamma=gamma,
            class_weight=class_weight,
            decision_function_shape="ovr",
            probability=False,
            random_state=seed,
        )

    def fit(self, images: np.ndarray, labels: np.ndarray, **kwargs: object) -> dict[str, object]:
        features = extract_spatial_lbp(images, self.grid_rows, self.grid_cols)
        self.model.fit(features, labels)
        return {"training_samples": int(labels.size), "feature_size": int(features.shape[1])}

    def predict(self, images: np.ndarray) -> PredictionBatch:
        features = extract_spatial_lbp(images, self.grid_rows, self.grid_cols)
        scores = np.asarray(self.model.decision_function(features), dtype=np.float64)
        if scores.ndim == 1:
            raise ValueError("SVM chưa được huấn luyện đủ bảy lớp.")
        labels = np.asarray(self.model.classes_[np.argmax(scores, axis=1)], dtype=np.int64)
        result = PredictionBatch(labels=labels, scores=scores)
        result.validate(len(images))
        return result

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {"grid_rows": self.grid_rows, "grid_cols": self.grid_cols, "model": self.model},
            path,
        )
