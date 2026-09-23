from __future__ import annotations

from typing import Any

import cv2
import numpy as np
import torch
from facenet_pytorch import MTCNN

from ..types import Detection
from .base import FaceDetector


class MTCNNDetector(FaceDetector):
    name = "mtcnn"

    def __init__(self, config: dict[str, Any], device: str = "cpu") -> None:
        self.config = config
        self.device = torch.device(device)
        self.model: MTCNN | None = None

    def load(self) -> None:
        self.model = MTCNN(
            min_face_size=int(self.config["min_face_size"]),
            thresholds=tuple(float(value) for value in self.config["thresholds"]),
            factor=float(self.config["factor"]),
            keep_all=True,
            post_process=False,
            device=self.device,
        )
        self.model.eval()

    def detect(self, image_bgr: np.ndarray) -> list[Detection]:
        if self.model is None:
            raise RuntimeError("MTCNN detector is not loaded")
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        boxes, probabilities = self.model.detect(image_rgb, landmarks=False)
        if boxes is None or probabilities is None:
            return []
        detections = [
            Detection(float(box[0]), float(box[1]), float(box[2]), float(box[3]), float(score))
            for box, score in zip(boxes, probabilities, strict=True)
            if score is not None and np.isfinite(score)
        ]
        return sorted(detections, key=lambda item: item.score, reverse=True)

