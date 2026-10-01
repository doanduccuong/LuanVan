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
    assert result.faces == []


def test_multiple_faces_are_processed_independently():
    class DetectorStub:
        def detectMultiScale(self, *_args, **_kwargs):
            return np.asarray([[8, 8, 48, 48], [72, 8, 48, 48]], dtype=np.int32)

    rng = np.random.default_rng(20261001)
    image = rng.integers(0, 256, size=(72, 136, 3), dtype=np.uint8)
    engine = OpenCVDemoEngine()
    engine.detector = DetectorStub()

    result = engine.analyze(encode(image))

    assert result.image_status == "VALID"
    assert result.face_count == 2
    assert [face.face_index for face in result.faces] == [0, 1]
    assert all(face.image_status == "VALID" for face in result.faces)
    assert all(face.embedding for face in result.faces)
