from __future__ import annotations

import csv
import json
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import httpx


SYSTEM_ROOT = Path(__file__).resolve().parents[1]
DATASET_ROOT = SYSTEM_ROOT / "fixtures" / "demo_dataset"
ARTIFACT_ROOT = SYSTEM_ROOT / "artifacts"
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")
VISION_URL = os.getenv("VISION_URL", "http://localhost:8001")


def read_csv(name: str) -> list[dict[str, str]]:
    with (DATASET_ROOT / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(name: str, rows: list[dict], fieldnames: list[str]) -> None:
    DATASET_ROOT.mkdir(parents=True, exist_ok=True)
    with (DATASET_ROOT / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


@contextmanager
def login_client() -> Iterator[httpx.Client]:
    with httpx.Client(base_url=API_URL, timeout=60.0) as client:
        response = client.post(
            "/auth/login",
            json={
                "email": os.getenv("DEMO_USER_EMAIL", "manager@example.com"),
                "password": os.getenv("DEMO_USER_PASSWORD", "demo1234"),
            },
        )
        response.raise_for_status()
        yield client


def save_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
