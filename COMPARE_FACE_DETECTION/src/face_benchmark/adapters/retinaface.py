from __future__ import annotations

import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch

from ..types import Detection
from .base import FaceDetector


class RetinaFaceMobileNetDetector(FaceDetector):
    name = "retinaface_mobilenet025"

    def __init__(
        self,
        config: dict[str, Any],
        vendor_path: Path,
        weights_path: Path,
        device: str = "cpu",
    ) -> None:
        self.config = config
        self.vendor_path = vendor_path.resolve()
        self.weights_path = weights_path.resolve()
        self.device = torch.device(device)
        self.model: torch.nn.Module | None = None
        self.cfg: dict[str, Any] | None = None
        self.PriorBox: Any = None
        self.decode: Any = None
        self.py_cpu_nms: Any = None

    def load(self) -> None:
        if not self.vendor_path.exists():
            raise FileNotFoundError(f"Missing RetinaFace vendor repository: {self.vendor_path}")
        if not self.weights_path.exists():
            raise FileNotFoundError(f"Missing RetinaFace weights: {self.weights_path}")
        vendor_string = str(self.vendor_path)
        if vendor_string not in sys.path:
            sys.path.insert(0, vendor_string)

        from data import cfg_mnet
        from layers.functions.prior_box import PriorBox
        from models.retinaface import RetinaFace
        from utils.box_utils import decode
        from utils.nms.py_cpu_nms import py_cpu_nms

        self.cfg = deepcopy(cfg_mnet)
        self.cfg["pretrain"] = False
        self.PriorBox = PriorBox
        self.decode = decode
        self.py_cpu_nms = py_cpu_nms
        model = RetinaFace(cfg=self.cfg, phase="test")
        checkpoint = torch.load(self.weights_path, map_location=self.device)
        if "state_dict" in checkpoint:
            checkpoint = checkpoint["state_dict"]
        checkpoint = {key.removeprefix("module."): value for key, value in checkpoint.items()}
        model.load_state_dict(checkpoint, strict=True)
        model.eval()
        self.model = model.to(self.device)

    def detect(self, image_bgr: np.ndarray) -> list[Detection]:
        if self.model is None or self.cfg is None:
            raise RuntimeError("RetinaFace detector is not loaded")
        image = image_bgr.astype(np.float32, copy=True)
        image -= (104, 117, 123)
        tensor = torch.from_numpy(image.transpose(2, 0, 1)).unsqueeze(0).to(self.device)
        height, width = image_bgr.shape[:2]
        scale = torch.tensor([width, height, width, height], dtype=torch.float32, device=self.device)
        with torch.inference_mode():
            locations, confidences, _landmarks = self.model(tensor)
            priors = self.PriorBox(self.cfg, image_size=(height, width)).forward().to(self.device)
            boxes = self.decode(locations.squeeze(0), priors, self.config["variance"])
            boxes = boxes * scale
            scores = confidences.squeeze(0)[:, 1]

        boxes_np = boxes.detach().cpu().numpy()
        scores_np = scores.detach().cpu().numpy()
        keep = np.where(scores_np > float(self.config["confidence_threshold"]))[0]
        boxes_np = boxes_np[keep]
        scores_np = scores_np[keep]
        order = scores_np.argsort()[::-1][: int(self.config["top_k"])]
        boxes_np = boxes_np[order]
        scores_np = scores_np[order]
        proposals = np.hstack((boxes_np, scores_np[:, None])).astype(np.float32, copy=False)
        keep_nms = self.py_cpu_nms(proposals, float(self.config["nms_threshold"]))
        keep_nms = keep_nms[: int(self.config["keep_top_k"])]
        proposals = proposals[keep_nms]
        return [
            Detection(float(row[0]), float(row[1]), float(row[2]), float(row[3]), float(row[4]))
            for row in proposals
        ]
