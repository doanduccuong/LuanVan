from __future__ import annotations

import hashlib
import json
from pathlib import Path

import cv2

from .types import ImageRecord


def parse_wider_annotations(annotation_path: Path, images_root: Path) -> list[ImageRecord]:
    lines = annotation_path.read_text(encoding="utf-8").splitlines()
    records: list[ImageRecord] = []
    index = 0
    while index < len(lines):
        image_id = lines[index].strip()
        index += 1
        if not image_id:
            continue
        if index >= len(lines):
            raise ValueError(f"Missing face count after {image_id}")
        face_count = int(lines[index].strip())
        index += 1
        boxes: list[tuple[float, float, float, float]] = []
        for _ in range(face_count):
            if index >= len(lines):
                raise ValueError(f"Missing bounding box data for {image_id}")
            parts = lines[index].split()
            index += 1
            if len(parts) < 4:
                raise ValueError(f"Invalid bounding box for {image_id}: {parts}")
            x, y, width, height = map(float, parts[:4])
            boxes.append((x, y, width, height))
        image_path = images_root / image_id
        records.append(
            ImageRecord(
                image_id=image_id,
                path=str(image_path),
                width=None,
                height=None,
                boxes_xywh=tuple(boxes),
            )
        )
    return records


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def validate_dataset(
    records: list[ImageRecord],
    annotation_path: Path,
    artifact_paths: list[Path] | None = None,
) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    duplicate_ids: list[str] = []
    seen: set[str] = set()
    face_count = 0
    for record in records:
        if record.image_id in seen:
            duplicate_ids.append(record.image_id)
        seen.add(record.image_id)
        image_path = Path(record.path)
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None:
            errors.append(f"Unreadable image: {image_path}")
            continue
        height, width = image.shape[:2]
        for box in record.boxes_xywh:
            x, y, box_width, box_height = box
            face_count += 1
            if box_width <= 0 or box_height <= 0:
                warnings.append(f"Ignored non-positive box in {record.image_id}: {box}")
                continue
            if x >= width or y >= height or x + box_width <= 0 or y + box_height <= 0:
                warnings.append(f"Box intersects no image pixels in {record.image_id}: {box}")
    if duplicate_ids:
        errors.extend(f"Duplicate image id: {item}" for item in duplicate_ids)
    artifacts = {
        str(path): {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
        for path in artifact_paths or []
        if path.exists()
    }
    return {
        "annotation_path": str(annotation_path),
        "annotation_sha256": sha256_file(annotation_path),
        "image_count": len(records),
        "face_count": face_count,
        "artifacts": artifacts,
        "warnings": warnings,
        "errors": errors,
        "valid": not errors,
    }


def write_manifest(manifest: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
