from __future__ import annotations

import cv2
import numpy as np

from app.engine import (
    FACE_ALIGNMENT_TEMPLATE,
    DeepFaceRetinaFaceEngine,
    OpenCVDemoEngine,
    align_face,
    estimate_face_alignment,
)


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


def test_face_alignment_maps_rotated_landmarks_to_arcface_template():
    angle = np.deg2rad(18.0)
    scale = 1.15
    template_to_source = np.asarray(
        [
            [scale * np.cos(angle), -scale * np.sin(angle), 24.0],
            [scale * np.sin(angle), scale * np.cos(angle), 11.0],
        ],
        dtype=np.float32,
    )
    source = FACE_ALIGNMENT_TEMPLATE @ template_to_source[:, :2].T + template_to_source[:, 2]

    alignment = estimate_face_alignment(source)
    mapped = source @ alignment[:, :2].T + alignment[:, 2]

    np.testing.assert_allclose(mapped, FACE_ALIGNMENT_TEMPLATE, atol=0.1)


def test_face_alignment_returns_arcface_sized_image():
    image = np.full((160, 160, 3), 127, dtype=np.uint8)

    aligned = align_face(image, FACE_ALIGNMENT_TEMPLATE)

    assert aligned.shape == (112, 112, 3)


def test_deepface_branches_receive_the_same_aligned_face():
    class DeepFaceStub:
        inputs: list[np.ndarray] = []

        @classmethod
        def analyze(cls, *, img_path, **_kwargs):
            cls.inputs.append(img_path.copy())
            return {
                "emotion": {
                    label.lower(): (100.0 if label == "Happy" else 0.0)
                    for label in ("Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral")
                },
                "dominant_emotion": "happy",
            }

        @classmethod
        def represent(cls, *, img_path, **_kwargs):
            cls.inputs.append(img_path.copy())
            return [{"embedding": [1.0, 0.0, 0.0]}]

    engine = object.__new__(DeepFaceRetinaFaceEngine)
    engine.DeepFace = DeepFaceStub
    image = np.full((160, 160, 3), 180, dtype=np.uint8)
    detection = {
        "box": [20.0, 20.0, 140.0, 150.0],
        "score": 0.99,
        "landmarks": FACE_ALIGNMENT_TEMPLATE.tolist(),
    }

    result = engine._analyze_detection(image, detection, 0)

    assert result.image_status == "VALID"
    assert result.expression_status == "VALID"
    assert result.identity_status == "VALID"
    assert len(DeepFaceStub.inputs) == 2
    assert DeepFaceStub.inputs[0].shape == (112, 112, 3)
    np.testing.assert_array_equal(DeepFaceStub.inputs[0], DeepFaceStub.inputs[1])
