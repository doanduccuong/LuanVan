from __future__ import annotations

import hashlib
import math
import sys
from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache

import cv2
import numpy as np

from .settings import get_settings


LABELS = ("ANGRY", "DISGUST", "FEAR", "HAPPY", "SAD", "SURPRISE", "NEUTRAL")


@dataclass
class Analysis:
    image_status: str
    face_count: int
    box: list[float] | None = None
    detection_score: float | None = None
    expression_status: str = "NOT_RUN"
    expression_label: str | None = None
    expression_confidence: float | None = None
    expression_scores: dict[str, float] | None = None
    embedding: list[float] | None = None
    models: dict[str, str] | None = None


class VisionEngine(ABC):
    @abstractmethod
    def analyze(self, image_bytes: bytes) -> Analysis:
        raise NotImplementedError


def decode_image(image_bytes: bytes) -> np.ndarray:
    array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None or image.size == 0:
        raise ValueError("INVALID_IMAGE")
    return image


def normalize_embedding(values: np.ndarray) -> list[float]:
    vector = values.astype(np.float32).reshape(-1)
    norm = float(np.linalg.norm(vector))
    if not math.isfinite(norm) or norm == 0:
        raise ValueError("INVALID_EMBEDDING")
    return (vector / norm).tolist()


class OpenCVDemoEngine(VisionEngine):
    """Lightweight pipeline for API development, never for thesis metrics."""

    def __init__(self) -> None:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.detector = cv2.CascadeClassifier(cascade_path)

    def analyze(self, image_bytes: bytes) -> Analysis:
        try:
            image = decode_image(image_bytes)
        except ValueError:
            return Analysis(image_status="INVALID_IMAGE", face_count=0, models=self._models())
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        boxes = self.detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(32, 32))
        if len(boxes) == 0:
            return Analysis(image_status="NO_FACE", face_count=0, models=self._models())
        if len(boxes) > 1:
            return Analysis(image_status="MULTIPLE_FACES", face_count=len(boxes), models=self._models())
        x, y, width, height = [int(v) for v in boxes[0]]
        crop = gray[y : y + height, x : x + width]
        if crop.size == 0:
            return Analysis(image_status="INVALID_FACE_CROP", face_count=1, models=self._models())
        # This deterministic output keeps API tests runnable. It is explicitly marked DEMO.
        resized = cv2.resize(crop, (32, 16), interpolation=cv2.INTER_AREA)
        embedding = normalize_embedding(resized.astype(np.float32) - float(resized.mean()))
        digest = hashlib.sha256(crop.tobytes()).digest()
        raw = np.array([digest[index] + 1 for index in range(7)], dtype=np.float64)
        scores_array = raw / raw.sum()
        best = int(scores_array.argmax())
        scores = {label: float(scores_array[index]) for index, label in enumerate(LABELS)}
        return Analysis(
            image_status="VALID",
            face_count=1,
            box=[float(x), float(y), float(x + width), float(y + height)],
            detection_score=1.0,
            expression_status="VALID",
            expression_label=LABELS[best],
            expression_confidence=float(scores_array[best]),
            expression_scores=scores,
            embedding=embedding,
            models=self._models(),
        )

    @staticmethod
    def _models() -> dict[str, str]:
        return {
            "detector": "opencv-haar:demo-only",
            "emotion": "deterministic-demo-output:not-for-evaluation",
            "embedding": "normalized-pixels:demo-only",
        }


class RetinaFaceMobileNetDetector:
    def __init__(self) -> None:
        settings = get_settings()
        vendor_path = settings.retinaface_vendor_path.resolve()
        if not vendor_path.exists() or not settings.retinaface_weights_path.exists():
            raise RuntimeError("Thiếu mã hoặc trọng số RetinaFace-MobileNet0.25")
        if str(vendor_path) not in sys.path:
            sys.path.insert(0, str(vendor_path))
        import torch
        from data import cfg_mnet
        from layers.functions.prior_box import PriorBox
        from models.retinaface import RetinaFace
        from utils.box_utils import decode, decode_landm
        from utils.nms.py_cpu_nms import py_cpu_nms

        self.torch = torch
        self.PriorBox = PriorBox
        self.decode = decode
        self.decode_landm = decode_landm
        self.py_cpu_nms = py_cpu_nms
        self.device = torch.device(settings.device)
        self.cfg = deepcopy(cfg_mnet)
        self.cfg["pretrain"] = False
        model = RetinaFace(cfg=self.cfg, phase="test")
        checkpoint = torch.load(settings.retinaface_weights_path, map_location=self.device)
        if "state_dict" in checkpoint:
            checkpoint = checkpoint["state_dict"]
        checkpoint = {key.removeprefix("module."): value for key, value in checkpoint.items()}
        model.load_state_dict(checkpoint, strict=True)
        self.model = model.eval().to(self.device)

    def detect(self, image_bgr: np.ndarray) -> list[dict]:
        torch = self.torch
        settings = get_settings()
        image = image_bgr.astype(np.float32, copy=True)
        image -= (104, 117, 123)
        tensor = torch.from_numpy(image.transpose(2, 0, 1)).unsqueeze(0).to(self.device)
        height, width = image_bgr.shape[:2]
        scale = torch.tensor([width, height, width, height], dtype=torch.float32, device=self.device)
        landmark_scale = torch.tensor([width, height] * 5, dtype=torch.float32, device=self.device)
        with torch.inference_mode():
            locations, confidences, landmarks = self.model(tensor)
            priors = self.PriorBox(self.cfg, image_size=(height, width)).forward().to(self.device)
            boxes = self.decode(locations.squeeze(0), priors, self.cfg["variance"]) * scale
            landmarks = self.decode_landm(landmarks.squeeze(0), priors, self.cfg["variance"]) * landmark_scale
            scores = confidences.squeeze(0)[:, 1]
        boxes_np = boxes.cpu().numpy()
        scores_np = scores.cpu().numpy()
        landmarks_np = landmarks.cpu().numpy()
        keep = np.where(scores_np >= settings.detector_confidence_threshold)[0]
        boxes_np, scores_np, landmarks_np = boxes_np[keep], scores_np[keep], landmarks_np[keep]
        order = scores_np.argsort()[::-1][:5000]
        proposals = np.hstack((boxes_np[order], scores_np[order, None])).astype(np.float32, copy=False)
        landmarks_np = landmarks_np[order]
        keep_nms = self.py_cpu_nms(proposals, 0.4)[:750]
        return [
            {
                "box": proposals[index, :4].tolist(),
                "score": float(proposals[index, 4]),
                "landmarks": landmarks_np[index].reshape(5, 2).tolist(),
            }
            for index in keep_nms
        ]


class DeepFaceRetinaFaceEngine(VisionEngine):
    def __init__(self) -> None:
        try:
            from deepface import DeepFace
        except ImportError as exc:
            raise RuntimeError("Chưa cài nhóm phụ thuộc models của dịch vụ vision") from exc
        self.DeepFace = DeepFace
        self.detector = RetinaFaceMobileNetDetector()

    def analyze(self, image_bytes: bytes) -> Analysis:
        try:
            image = decode_image(image_bytes)
        except ValueError:
            return Analysis(image_status="INVALID_IMAGE", face_count=0, models=self._models())
        detections = self.detector.detect(image)
        if not detections:
            return Analysis(image_status="NO_FACE", face_count=0, models=self._models())
        if len(detections) > 1:
            return Analysis(image_status="MULTIPLE_FACES", face_count=len(detections), models=self._models())
        detection = detections[0]
        height, width = image.shape[:2]
        x1, y1, x2, y2 = detection["box"]
        x1, y1 = max(0, int(x1)), max(0, int(y1))
        x2, y2 = min(width, int(x2)), min(height, int(y2))
        crop = image[y1:y2, x1:x2]
        if crop.size == 0:
            return Analysis(image_status="INVALID_FACE_CROP", face_count=1, models=self._models())
        emotion_result = self.DeepFace.analyze(
            img_path=crop,
            actions=["emotion"],
            detector_backend="skip",
            enforce_detection=False,
            align=False,
            silent=True,
        )
        if isinstance(emotion_result, list):
            emotion_result = emotion_result[0]
        raw_scores = emotion_result["emotion"]
        scores = {key.upper(): float(value) / 100.0 for key, value in raw_scores.items()}
        label = str(emotion_result["dominant_emotion"]).upper()
        representations = self.DeepFace.represent(
            img_path=crop,
            model_name="ArcFace",
            detector_backend="skip",
            enforce_detection=False,
            align=False,
            normalization="ArcFace",
        )
        representation = representations[0]["embedding"]
        return Analysis(
            image_status="VALID",
            face_count=1,
            box=[float(x1), float(y1), float(x2), float(y2)],
            detection_score=detection["score"],
            expression_status="VALID",
            expression_label=label,
            expression_confidence=scores[label],
            expression_scores=scores,
            embedding=normalize_embedding(np.asarray(representation, dtype=np.float32)),
            models=self._models(),
        )

    @staticmethod
    def _models() -> dict[str, str]:
        return {
            "detector": "retinaface-mobilenet0.25:configured-checksum",
            "emotion": "deepface-emotion:configured-checksum",
            "embedding": "deepface-arcface:configured-checksum",
        }


@lru_cache
def get_engine() -> VisionEngine:
    backend = get_settings().vision_backend
    if backend == "opencv_demo":
        return OpenCVDemoEngine()
    if backend == "deepface_retinaface":
        return DeepFaceRetinaFaceEngine()
    raise RuntimeError(f"VISION_BACKEND không được hỗ trợ: {backend}")

