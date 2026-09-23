from __future__ import annotations

from pathlib import Path
from typing import Any

import cv2
import numpy as np

from ..types import Detection
from .base import FaceDetector


class HaarDetector(FaceDetector):
    name = "haar"

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.classifier: cv2.CascadeClassifier | None = None

    def load(self) -> None:
        cascade_value = self.config["cascade"]
        cascade_path = Path(cascade_value)
        if not cascade_path.is_absolute():
            cascade_path = Path(cv2.data.haarcascades) / cascade_value
        self.classifier = cv2.CascadeClassifier(str(cascade_path))
        if self.classifier.empty():
            raise RuntimeError(f"Cannot load Haar cascade: {cascade_path}")

    def detect(self, image_bgr: np.ndarray) -> list[Detection]:
        if self.classifier is None:
            raise RuntimeError("Haar detector is not loaded")
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        min_size = tuple(self.config["min_size"])
        max_size_value = self.config.get("max_size")
        max_size = tuple(max_size_value) if max_size_value else (0, 0)
        rectangles, _reject_levels, level_weights = self.classifier.detectMultiScale3(
            gray,
            scaleFactor=float(self.config["scale_factor"]),
            minNeighbors=int(self.config["min_neighbors"]),
            minSize=min_size,
            maxSize=max_size,
            outputRejectLevels=True,
        )
        weights = np.asarray(level_weights, dtype=np.float64).reshape(-1)
        detections: list[Detection] = []
        for index, (x, y, width, height) in enumerate(rectangles):
            score = float(weights[index]) if index < len(weights) else 0.0
            detections.append(
                Detection(float(x), float(y), float(x + width), float(y + height), score)
            )
        return sorted(detections, key=lambda item: item.score, reverse=True)

