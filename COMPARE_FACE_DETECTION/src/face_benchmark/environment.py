from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path

import cv2
import numpy
import torch


def _command_output(command: list[str]) -> str | None:
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def collect_environment() -> dict[str, object]:
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "macos": _command_output(["sw_vers"]),
        "cpu_brand": _command_output(["sysctl", "-n", "machdep.cpu.brand_string"]),
        "memory_bytes": _command_output(["sysctl", "-n", "hw.memsize"]),
        "numpy": numpy.__version__,
        "opencv": cv2.__version__,
        "torch": torch.__version__,
        "torch_mps_available": bool(torch.backends.mps.is_available()),
    }


def write_environment(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(collect_environment(), indent=2), encoding="utf-8")

