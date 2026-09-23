from __future__ import annotations

import cv2
import numpy as np

from app.engine import OpenCVDemoEngine


def encode(image: np.ndarray) -> bytes:
    ok, buffer = cv2.imencode(".jpg", image)
    assert ok
    return buffer.tobytes()


def test_invalid_image():
    result = OpenCVDemoEngine().analyze(b"not-an-image")
    assert result.image_status == "INVALID_IMAGE"


def test_blank_image_has_no_face():
    image = np.full((480, 640, 3), 240, dtype=np.uint8)
    result = OpenCVDemoEngine().analyze(encode(image))
    assert result.image_status == "NO_FACE"
    assert result.face_count == 0

