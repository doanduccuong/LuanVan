from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pickle
import urllib.request
from pathlib import Path

import cv2
import numpy as np

from demo_common import DATASET_ROOT, SYSTEM_ROOT
from prepare_demo_dataset import write_static_crm_data


FAIRFACE_URL = "https://huggingface.co/datasets/nateraw/fairface/resolve/main/val.pt"
FAIRFACE_HOME = "https://github.com/MilaNLProc/fairface"


class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module: str, name: str):
        raise pickle.UnpicklingError(f"Không cho phép đối tượng pickle: {module}.{name}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str, target: Path) -> None:
    if target.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "touchpoint-crm-thesis-demo/1.0"})
    temporary = target.with_suffix(target.suffix + ".part")
    with urllib.request.urlopen(request, timeout=120) as response, temporary.open("wb") as output:
        while chunk := response.read(1024 * 1024):
            output.write(chunk)
    temporary.replace(target)


def load_examples(path: Path) -> list[dict]:
    with path.open("rb") as handle:
        examples = RestrictedUnpickler(handle).load()
    if not isinstance(examples, list) or not all(isinstance(item, dict) for item in examples):
        raise ValueError("Tệp FairFace không có cấu trúc danh sách bản ghi mong đợi")
    return examples


def prepare(count: int) -> None:
    if count != 100:
        raise ValueError("Bộ demo được khóa ở đúng 100 khách hàng")
    cache = SYSTEM_ROOT / "data" / "raw" / "fairface" / "val.pt"
    download(FAIRFACE_URL, cache)
    examples = load_examples(cache)
    if len(examples) < count:
        raise ValueError(f"Nguồn chỉ có {len(examples)} ảnh, không đủ {count} ảnh")

    destination = DATASET_ROOT / "customer_images"
    destination.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []
    for index, example in enumerate(examples[:count], 1):
        raw = example.get("img_bytes")
        if not isinstance(raw, bytes):
            raise ValueError(f"Bản ghi {index} không có dữ liệu ảnh hợp lệ")
        image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Không giải mã được ảnh FairFace thứ {index}")
        image = cv2.resize(image, (256, 256), interpolation=cv2.INTER_AREA)
        output = destination / f"CUS-DEMO-{index:03d}.jpg"
        if not cv2.imwrite(str(output), image, [cv2.IMWRITE_JPEG_QUALITY, 90]):
            raise ValueError(f"Không ghi được ảnh {output}")
        manifest.append(
            {
                "customer_code": f"CUS-DEMO-{index:03d}",
                "source_index": index - 1,
                "source_id": example.get("_id", index - 1),
                "age_class": example.get("age"),
                "gender_class": example.get("gender"),
                "race_class": example.get("race"),
                "output": str(output.relative_to(DATASET_ROOT)),
                "output_sha256": sha256(output),
            }
        )

    with (DATASET_ROOT / "customer_image_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(manifest[0]))
        writer.writeheader()
        writer.writerows(manifest)
    source = {
        "dataset": "FairFace validation subset",
        "homepage": FAIRFACE_HOME,
        "download_url": FAIRFACE_URL,
        "license": "CC BY 4.0",
        "selected_images": count,
        "selection": "first 100 validation records",
        "source_sha256": sha256(cache),
        "purpose": "offline non-production CRM simulation",
    }
    (DATASET_ROOT / "portrait_sources.json").write_text(json.dumps(source, ensure_ascii=False, indent=2), encoding="utf-8")
    write_static_crm_data()
    print(f"Đã chuẩn bị đúng {count} ảnh khách hàng tại {destination}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=100)
    args = parser.parse_args()
    prepare(args.count)
