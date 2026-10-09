from __future__ import annotations

import time
from typing import Callable

import numpy as np

from .adapters.base import PredictionBatch


def measure_latency(
    predict: Callable[[np.ndarray], PredictionBatch],
    images: np.ndarray,
    *,
    warmup_samples: int,
    repeats: int,
) -> dict[str, float | int]:
    if len(images) == 0:
        raise ValueError("Không có ảnh để đo độ trễ.")
    for index in range(min(warmup_samples, len(images))):
        predict(images[index : index + 1])
    measurements: list[float] = []
    for _ in range(repeats):
        for index in range(len(images)):
            start = time.perf_counter_ns()
            predict(images[index : index + 1])
            measurements.append((time.perf_counter_ns() - start) / 1_000_000.0)
    values = np.asarray(measurements, dtype=np.float64)
    total_seconds = float(values.sum() / 1000.0)
    return {
        "samples": int(values.size),
        "repeats": int(repeats),
        "latency_p50_ms": float(np.percentile(values, 50)),
        "latency_p95_ms": float(np.percentile(values, 95)),
        "latency_p99_ms": float(np.percentile(values, 99)),
        "throughput_images_per_second": float(values.size / total_seconds),
    }
