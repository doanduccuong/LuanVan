from __future__ import annotations

import platform
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from typing import Any

import numpy
import sklearn


def _command_output(command: list[str]) -> str | None:
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def collect_environment() -> dict[str, Any]:
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_brand": _command_output(["sysctl", "-n", "machdep.cpu.brand_string"]),
        "memory_bytes": _command_output(["sysctl", "-n", "hw.memsize"]),
        "numpy": numpy.__version__,
        "scikit_learn": sklearn.__version__,
        "deepface": _package_version("deepface"),
        "tensorflow": _package_version("tensorflow"),
        "tf_keras": _package_version("tf-keras"),
        "opencv_python": _package_version("opencv-python"),
    }
