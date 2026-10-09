from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    if not isinstance(config, dict):
        raise ValueError(f"Cấu hình không hợp lệ: {path}")
    return config


def resolve_path(project_root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (project_root / path).resolve()


def validate_training_config(config: dict[str, Any]) -> None:
    training = config["training"]
    if int(training["batch_size"]) < 1:
        raise ValueError("batch_size phải lớn hơn 0.")
    if int(training["epochs"]) < 1:
        raise ValueError("epochs phải lớn hơn 0.")
    if float(training["learning_rate"]) <= 0:
        raise ValueError("learning_rate phải lớn hơn 0.")
    if int(training["patience"]) < 1:
        raise ValueError("patience phải lớn hơn 0.")
    if float(training["min_delta"]) < 0:
        raise ValueError("min_delta không được âm.")
    augmentation = training.get("augmentation", {})
    for key in ("rotation_factor", "translation_factor", "contrast_factor"):
        value = float(augmentation.get(key, 0.0))
        if not 0.0 <= value <= 0.5:
            raise ValueError(f"{key} phải nằm trong khoảng 0..0,5.")
