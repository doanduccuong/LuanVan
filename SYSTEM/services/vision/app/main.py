from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile

from .engine import Analysis, get_engine
from .settings import get_settings


app = FastAPI(title="Touchpoint Vision Service", version="0.1.0")


@app.get("/health/live")
def health_live():
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready():
    engine = get_engine()
    return {"status": "ready", "backend": engine.__class__.__name__}


@app.post("/internal/v1/analyze-face")
async def analyze_face(image: UploadFile = File(...)):
    data = await image.read()
    settings = get_settings()
    if not data or len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=422, detail="Ảnh rỗng hoặc vượt dung lượng cho phép")
    try:
        result: Analysis = get_engine().analyze(data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Không thể xử lý ảnh: {type(exc).__name__}") from exc
    return {
        "image_status": result.image_status,
        "face_count": result.face_count,
        "box": result.box,
        "detection_score": result.detection_score,
        "expression_status": result.expression_status,
        "expression": (
            {
                "label": result.expression_label,
                "confidence": result.expression_confidence,
                "scores": result.expression_scores,
            }
            if result.expression_label
            else None
        ),
        "embedding": result.embedding,
        "models": result.models or {},
    }

