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
    path = Path(value)
    return path if path.is_absolute() else project_root / path


def ensure_private_test_allowed(config: dict[str, Any]) -> None:
    run = config.get("run", {})
    if not bool(run.get("final_evaluation", False)):
        raise PermissionError(
            "PrivateTest chỉ được dùng khi run.final_evaluation=true sau khi cấu hình đã khóa."
        )
