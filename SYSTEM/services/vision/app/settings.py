from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    vision_backend: str = "opencv_demo"
    max_upload_bytes: int = 8 * 1024 * 1024
    detector_confidence_threshold: float = 0.8
    retinaface_vendor_path: Path = Path("/models/Pytorch_Retinaface")
    retinaface_weights_path: Path = Path("/models/mobilenet0.25_Final.pth")
    device: str = "cpu"


@lru_cache
def get_settings() -> Settings:
    return Settings()

