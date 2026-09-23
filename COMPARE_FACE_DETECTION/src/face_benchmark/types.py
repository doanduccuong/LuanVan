from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class Detection:
    x1: float
    y1: float
    x2: float
    y2: float
    score: float

    def to_dict(self) -> dict[str, float]:
        return asdict(self)


@dataclass(frozen=True)
class ImageRecord:
    image_id: str
    path: str
    width: int | None
    height: int | None
    boxes_xywh: tuple[tuple[float, float, float, float], ...]


@dataclass(frozen=True)
class PredictionRecord:
    image_id: str
    detections: tuple[Detection, ...]
    latency_ms: float
    repeat: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "image_id": self.image_id,
            "detections": [d.to_dict() for d in self.detections],
            "latency_ms": self.latency_ms,
            "repeat": self.repeat,
        }

