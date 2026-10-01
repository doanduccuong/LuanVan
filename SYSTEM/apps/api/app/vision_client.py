from __future__ import annotations

from dataclasses import dataclass

import httpx

from .config import get_settings


@dataclass
class VisionFaceResult:
    face_index: int
    image_status: str
    box: list[float]
    expression_status: str
    identity_status: str
    expression_label: str | None
    expression_confidence: float | None
    expression_scores: dict[str, float] | None
    embedding: list[float] | None
    detection_score: float | None


@dataclass
class VisionResult:
    image_status: str
    face_count: int
    faces: list[VisionFaceResult]
    models: dict[str, str]

    def single_face(self) -> VisionFaceResult | None:
        return self.faces[0] if len(self.faces) == 1 else None


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
        faces = [
            VisionFaceResult(
                face_index=int(face["face_index"]),
                image_status=face.get("image_status", "VALID"),
                box=[float(value) for value in face.get("box", [])],
                expression_status=face.get("expression_status", "NOT_RUN"),
                identity_status=face.get("identity_status", "NOT_RUN"),
                expression_label=(face.get("expression") or {}).get("label"),
                expression_confidence=(face.get("expression") or {}).get("confidence"),
                expression_scores=(face.get("expression") or {}).get("scores"),
                embedding=face.get("embedding"),
                detection_score=face.get("detection_score"),
            )
            for face in data.get("faces", [])
        ]
        return VisionResult(
            image_status=data["image_status"],
            face_count=int(data.get("face_count", len(faces))),
            faces=faces,
            models=data.get("models", {}),
        )


def get_vision_client() -> VisionClient:
    return VisionClient()
