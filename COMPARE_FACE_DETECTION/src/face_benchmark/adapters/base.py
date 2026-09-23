from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from ..types import Detection


class FaceDetector(ABC):
    name: str

    @abstractmethod
    def load(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def detect(self, image_bgr: np.ndarray) -> list[Detection]:
        raise NotImplementedError

