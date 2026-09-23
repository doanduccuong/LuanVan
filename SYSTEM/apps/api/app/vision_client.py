from __future__ import annotations

from dataclasses import dataclass

import httpx

from .config import get_settings


@dataclass
class VisionResult:
    image_status: str
    expression_status: str
    identity_status: str
    expression_label: str | None
    expression_confidence: float | None
    expression_scores: dict[str, float] | None
    embedding: list[float] | None
    detection_score: float | None
    models: dict[str, str]


class VisionClient:
    async def analyze(self, image: bytes, filename: str, content_type: str | None) -> VisionResult:
        settings = get_settings()
        async with httpx.AsyncClient(timeout=settings.vision_request_timeout_seconds) as client:
            response = await client.post(
                f"{settings.vision_base_url}/internal/v1/analyze-face",
                files={"image": (filename, image, content_type or "application/octet-stream")},
            )
        response.raise_for_status()
        data = response.json()
        return VisionResult(
            image_status=data["image_status"],
            expression_status=data.get("expression_status", "NOT_RUN"),
            identity_status="NOT_RUN",
            expression_label=(data.get("expression") or {}).get("label"),
            expression_confidence=(data.get("expression") or {}).get("confidence"),
            expression_scores=(data.get("expression") or {}).get("scores"),
            embedding=data.get("embedding"),
            detection_score=data.get("detection_score"),
            models=data.get("models", {}),
        )


def get_vision_client() -> VisionClient:
    return VisionClient()

