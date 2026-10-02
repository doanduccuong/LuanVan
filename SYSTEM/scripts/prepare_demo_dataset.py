from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pickle
import shutil
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import cv2
import numpy as np

from demo_common import DATASET_ROOT, SYSTEM_ROOT, save_json, write_csv


FAIRFACE_URL = "https://huggingface.co/datasets/nateraw/fairface/resolve/main/val.pt"
FAIRFACE_HOME = "https://github.com/joojs/fairface"
CUSTOMER_COUNT = 100
CALIBRATION_COUNT = 8
UNKNOWN_COUNT = 2
# Bản ghi 92 bị loại sau bước sàng lọc vì véc-tơ của ảnh quan sát không gần
# véc-tơ đăng ký của chính nó dưới biến đổi camera đã định nghĩa. Bản ghi 110
# được dùng thay thế; các tập hiệu chỉnh và người chưa đăng ký vẫn tách rời.
CUSTOMER_SOURCE_INDICES = [index for index in range(100) if index != 92] + [110]
CALIBRATION_SOURCE_INDICES = list(range(100, 108))
UNKNOWN_SOURCE_INDICES = list(range(108, 110))
TOUCHPOINTS = [
    ("TP-ENTRANCE", "Cửa vào", 1),
    ("TP-DISPLAY", "Khu trưng bày sản phẩm", 2),
    ("TP-CONSULT", "Khu tư vấn", 3),
    ("TP-CHECKOUT", "Quầy thanh toán", 4),
]


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class RestrictedUnpickler(pickle.Unpickler):
    def find_class(self, module: str, name: str):
        raise pickle.UnpicklingError(f"Không cho phép đối tượng pickle: {module}.{name}")


def download(url: str, target: Path) -> None:
    if target.exists():
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "touchpoint-crm-experiment/1.0"})
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


def decode_example(example: dict, source_index: int) -> np.ndarray:
    raw = example.get("img_bytes")
    if not isinstance(raw, bytes):
        raise ValueError(f"Bản ghi FairFace {source_index} không có dữ liệu ảnh hợp lệ")
    image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Không giải mã được ảnh FairFace {source_index}")
    return image


def render_scene(image: np.ndarray, output: Path, offset: tuple[int, int], face_height: int = 300, brightness: int = 0) -> dict:
    canvas = np.full((480, 640, 3), 224, dtype=np.uint8)
    place_on_canvas(canvas, image, offset, face_height, brightness)
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), canvas, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return {"offset_x": offset[0], "offset_y": offset[1], "face_height": face_height, "brightness": brightness}


def place_on_canvas(
    canvas: np.ndarray,
    image: np.ndarray,
    offset: tuple[int, int],
    face_height: int,
    brightness: int = 0,
) -> None:
    height, width = image.shape[:2]
    scale = face_height / height
    resized = cv2.resize(image, (max(1, int(width * scale)), face_height), interpolation=cv2.INTER_CUBIC)
    if brightness:
        resized = cv2.convertScaleAbs(resized, alpha=1.0, beta=brightness)
    x, y = offset
    canvas_height, canvas_width = canvas.shape[:2]
    x2, y2 = min(canvas_width, x + resized.shape[1]), min(canvas_height, y + resized.shape[0])
    canvas[y:y2, x:x2] = resized[: y2 - y, : x2 - x]


def render_observation_scene(
    primary: np.ndarray,
    distractor: np.ndarray,
    output: Path,
    variant: int,
) -> dict:
    layouts = (
        (((155, 180), 330, -8), ((795, 195), 320, 4)),
        (((790, 170), 330, 6), ((150, 205), 320, -5)),
        (((165, 210), 330, 14), ((800, 160), 320, -6)),
        (((785, 200), 330, -3), ((145, 150), 320, 8)),
    )
    primary_layout, distractor_layout = layouts[variant % len(layouts)]
    canvas = np.full((720, 1280, 3), 224, dtype=np.uint8)
    place_on_canvas(canvas, primary, primary_layout[0], primary_layout[1], primary_layout[2])
    place_on_canvas(canvas, distractor, distractor_layout[0], distractor_layout[1], distractor_layout[2])
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), canvas, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return {
        "offset_x": primary_layout[0][0],
        "offset_y": primary_layout[0][1],
        "face_height": primary_layout[1],
        "brightness": primary_layout[2],
    }


def prepare(source: Path | None = None) -> None:
    source = source or SYSTEM_ROOT / "data" / "raw" / "fairface" / "val.pt"
    download(FAIRFACE_URL, source)
    examples = load_examples(source)
    selected_indices = CUSTOMER_SOURCE_INDICES + CALIBRATION_SOURCE_INDICES + UNKNOWN_SOURCE_INDICES
    required = max(selected_indices) + 1
    if len(examples) < required:
        raise ValueError(f"FairFace chỉ có {len(examples)} bản ghi, cần chỉ số đến {required - 1}")

    for relative in ("customer_images", "enrollment", "observations", "calibration"):
        target = DATASET_ROOT / relative
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)

    unknown_sources = [
        (source_index, decode_example(examples[source_index], source_index))
        for source_index in UNKNOWN_SOURCE_INDICES
    ]

    manifest: list[dict] = []
    customer_images: list[dict] = []
    for index, source_index in enumerate(CUSTOMER_SOURCE_INDICES, 1):
        example = examples[source_index]
        subject_id = f"fairface-{source_index:04d}"
        customer_code = f"CUS-EXP-{index:03d}"
        image = decode_example(example, source_index)
        profile_output = DATASET_ROOT / "customer_images" / f"{customer_code}.jpg"
        profile = cv2.resize(image, (256, 256), interpolation=cv2.INTER_AREA)
        cv2.imwrite(str(profile_output), profile, [cv2.IMWRITE_JPEG_QUALITY, 92])
        customer_images.append({"customer_code": customer_code, "subject_id": subject_id, "source_index": source_index, "source_id": example.get("_id", source_index), "output": str(profile_output.relative_to(DATASET_ROOT)), "output_sha256": checksum(profile_output)})

        enrollment_output = DATASET_ROOT / "enrollment" / subject_id / "enrollment.jpg"
        transform = render_scene(image, enrollment_output, (160, 70), 330, 0)
        manifest.append({"output": str(enrollment_output.relative_to(DATASET_ROOT)), "role": "enrollment", "subject_id": subject_id, "source_index": source_index, "source_id": example.get("_id", source_index), "secondary_source_index": "", "output_sha256": checksum(enrollment_output), **transform})

        variants = 4 if index <= 5 else 1
        for variant in range(variants):
            observation_output = DATASET_ROOT / "observations" / subject_id / f"{variant + 1:02d}.jpg"
            distractor_source_index, distractor = unknown_sources[(index + variant) % len(unknown_sources)]
            transform = render_observation_scene(image, distractor, observation_output, variant)
            manifest.append({"output": str(observation_output.relative_to(DATASET_ROOT)), "role": "observation", "subject_id": subject_id, "source_index": source_index, "source_id": example.get("_id", source_index), "secondary_source_index": distractor_source_index, "output_sha256": checksum(observation_output), **transform})

    for source_index in CALIBRATION_SOURCE_INDICES:
        example = examples[source_index]
        subject_id = f"fairface-{source_index:04d}"
        image = decode_example(example, source_index)
        for variant, (position, height, brightness) in enumerate((((150, 72), 320, 0), ((130, 64), 300, -10), ((180, 82), 285, 12)), 1):
            output = DATASET_ROOT / "calibration" / subject_id / f"{variant:02d}.jpg"
            transform = render_scene(image, output, position, height, brightness)
            manifest.append({"output": str(output.relative_to(DATASET_ROOT)), "role": "calibration", "subject_id": subject_id, "source_index": source_index, "source_id": example.get("_id", source_index), "output_sha256": checksum(output), **transform})

    unknown_images: list[Path] = []
    for offset, source_index in enumerate(UNKNOWN_SOURCE_INDICES):
        example = examples[source_index]
        subject_id = f"fairface-{source_index:04d}"
        image = unknown_sources[offset][1]
        other = unknown_sources[(offset + 1) % len(unknown_sources)][1]
        output = DATASET_ROOT / "observations" / "unknown" / f"{subject_id}.jpg"
        transform = render_observation_scene(image, other, output, offset)
        manifest.append({"output": str(output.relative_to(DATASET_ROOT)), "role": "unknown", "subject_id": subject_id, "source_index": source_index, "source_id": example.get("_id", source_index), "secondary_source_index": UNKNOWN_SOURCE_INDICES[(offset + 1) % len(UNKNOWN_SOURCE_INDICES)], "output_sha256": checksum(output), **transform})
        unknown_images.append(output)

    error_dir = DATASET_ROOT / "observations" / "errors"
    error_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(error_dir / "no-face.jpg"), np.full((480, 640, 3), 224, dtype=np.uint8))
    (error_dir / "invalid.jpg").write_bytes(b"not-an-image")
    render_observation_scene(
        unknown_sources[0][1],
        unknown_sources[1][1],
        error_dir / "multiple-faces.jpg",
        2,
    )

    write_static_crm_data()
    write_events()
    with (DATASET_ROOT / "image_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(manifest[0]))
        writer.writeheader()
        writer.writerows(manifest)
    with (DATASET_ROOT / "customer_image_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(customer_images[0]))
        writer.writeheader()
        writer.writerows(customer_images)
    save_json(DATASET_ROOT / "sources.json", {"dataset": "FairFace validation subset", "homepage": FAIRFACE_HOME, "download_url": FAIRFACE_URL, "license": "CC BY 4.0", "source": str(source), "source_sha256": checksum(source), "selected_records": len(selected_indices), "partition": {"customers": CUSTOMER_SOURCE_INDICES, "calibration": CALIBRATION_SOURCE_INDICES, "unknown": UNKNOWN_SOURCE_INDICES}, "screening_note": "source index 92 was replaced by 110 after the controlled observation transform failed self-identity consistency screening"})
    portrait_source = DATASET_ROOT / "portrait_sources.json"
    if portrait_source.exists():
        portrait_source.unlink()
    print(f"Đã tạo dữ liệu thực nghiệm cho {CUSTOMER_COUNT} khách hàng từ FairFace tại {DATASET_ROOT}")


def write_static_crm_data() -> None:
    customers = [
        {
            "customer_code": f"CUS-EXP-{index:03d}",
            "full_name": f"Khách hàng thực nghiệm {index:03d}",
            "phone": f"0900{index:06d}",
            "email": f"customer{index:03d}@example.com",
            "subject_id": f"fairface-{CUSTOMER_SOURCE_INDICES[index - 1]:04d}",
            "profile_image_url": f"/demo/customers/CUS-EXP-{index:03d}.jpg",
        }
        for index in range(1, CUSTOMER_COUNT + 1)
    ]
    write_csv("customers.csv", customers, list(customers[0]))
    categories = [
        {"category_code": "BEVERAGE", "name": "Đồ uống"},
        {"category_code": "SNACK", "name": "Đồ ăn nhẹ"},
        {"category_code": "CARE", "name": "Chăm sóc cá nhân"},
        {"category_code": "HOUSEHOLD", "name": "Đồ dùng gia đình"},
        {"category_code": "DAIRY", "name": "Sữa và sản phẩm lạnh"},
        {"category_code": "STATIONERY", "name": "Văn phòng phẩm"},
    ]
    write_csv("product_categories.csv", categories, list(categories[0]))
    products = [
        {"sku": "BEV-001", "name": "Nước khoáng", "category_code": "BEVERAGE", "current_price": "12000"},
        {"sku": "BEV-002", "name": "Trà đóng chai", "category_code": "BEVERAGE", "current_price": "18000"},
        {"sku": "SNK-001", "name": "Bánh quy", "category_code": "SNACK", "current_price": "25000"},
        {"sku": "SNK-002", "name": "Hạt dinh dưỡng", "category_code": "SNACK", "current_price": "45000"},
        {"sku": "CAR-001", "name": "Khăn giấy", "category_code": "CARE", "current_price": "15000"},
        {"sku": "CAR-002", "name": "Nước rửa tay", "category_code": "CARE", "current_price": "38000"},
        {"sku": "BEV-003", "name": "Nước cam", "category_code": "BEVERAGE", "current_price": "22000"},
        {"sku": "BEV-004", "name": "Cà phê lon", "category_code": "BEVERAGE", "current_price": "21000"},
        {"sku": "SNK-003", "name": "Khoai tây lát", "category_code": "SNACK", "current_price": "28000"},
        {"sku": "SNK-004", "name": "Kẹo bạc hà", "category_code": "SNACK", "current_price": "16000"},
        {"sku": "CAR-003", "name": "Dầu gội gói", "category_code": "CARE", "current_price": "9000"},
        {"sku": "CAR-004", "name": "Kem đánh răng", "category_code": "CARE", "current_price": "42000"},
        {"sku": "HOU-001", "name": "Nước rửa chén", "category_code": "HOUSEHOLD", "current_price": "36000"},
        {"sku": "HOU-002", "name": "Túi đựng rác", "category_code": "HOUSEHOLD", "current_price": "24000"},
        {"sku": "HOU-003", "name": "Miếng rửa bát", "category_code": "HOUSEHOLD", "current_price": "12000"},
        {"sku": "HOU-004", "name": "Nước lau sàn", "category_code": "HOUSEHOLD", "current_price": "52000"},
        {"sku": "DAI-001", "name": "Sữa tươi", "category_code": "DAIRY", "current_price": "34000"},
        {"sku": "DAI-002", "name": "Sữa chua", "category_code": "DAIRY", "current_price": "26000"},
        {"sku": "DAI-003", "name": "Bơ lạt", "category_code": "DAIRY", "current_price": "59000"},
        {"sku": "DAI-004", "name": "Phô mai lát", "category_code": "DAIRY", "current_price": "48000"},
        {"sku": "STA-001", "name": "Bút bi", "category_code": "STATIONERY", "current_price": "7000"},
        {"sku": "STA-002", "name": "Sổ tay", "category_code": "STATIONERY", "current_price": "32000"},
        {"sku": "STA-003", "name": "Băng keo", "category_code": "STATIONERY", "current_price": "11000"},
        {"sku": "STA-004", "name": "Bút đánh dấu", "category_code": "STATIONERY", "current_price": "15000"},
    ]
    write_csv("products.csv", products, list(products[0]))
    touchpoints = [{"touchpoint_code": code, "name": name, "sequence_order": order} for code, name, order in TOUCHPOINTS]
    write_csv("touchpoints.csv", touchpoints, list(touchpoints[0]))
    orders = [
        {"external_code": "ORD-EXP-OLD-001", "customer_code": "CUS-EXP-001", "ordered_at": "2026-09-01T09:00:00+07:00", "status": "COMPLETED"},
        {"external_code": "ORD-EXP-OLD-002", "customer_code": "CUS-EXP-002", "ordered_at": "2026-09-05T10:30:00+07:00", "status": "COMPLETED"},
        {"external_code": "ORD-EXP-CANCELLED", "customer_code": "CUS-EXP-003", "ordered_at": "2026-09-07T14:00:00+07:00", "status": "CANCELLED"},
    ]
    write_csv("orders.csv", orders, list(orders[0]))
    items = [
        {"external_code": "ORD-EXP-OLD-001", "sku": "BEV-001", "quantity": "2", "unit_price": "10000"},
        {"external_code": "ORD-EXP-OLD-001", "sku": "SNK-001", "quantity": "1", "unit_price": "25000"},
        {"external_code": "ORD-EXP-OLD-002", "sku": "CAR-001", "quantity": "2", "unit_price": "15000"},
        {"external_code": "ORD-EXP-CANCELLED", "sku": "CAR-002", "quantity": "1", "unit_price": "38000"},
    ]
    write_csv("order_items.csv", items, list(items[0]))


def write_events() -> None:
    base = datetime(2026, 9, 22, 9, 0, tzinfo=timezone(timedelta(hours=7)))
    events: list[dict] = []

    def add(scenario: str, event: str, customer: str, visit: str, touchpoint: str, minutes: int, path: str, image_status: str = "VALID", identity_status: str = "MATCHED", expected_face_count: int = 1, subject: str = "", condition: str = ""):
        events.append({"scenario_id": scenario, "event_id": event, "expected_customer_code": customer, "expected_visit_key": visit, "touchpoint_code": touchpoint, "observed_at": (base + timedelta(minutes=minutes)).isoformat(), "image_path": path, "expected_image_status": image_status, "expected_identity_status": identity_status, "expected_face_count": expected_face_count, "source_subject_id": subject, "source_condition": condition})

    for customer_index in range(1, CUSTOMER_COUNT + 1):
        subject = f"fairface-{CUSTOMER_SOURCE_INDICES[customer_index - 1]:04d}"
        customer_code = f"CUS-EXP-{customer_index:03d}"
        scenario = f"EXP-IDENTITY-{customer_index:03d}"
        event_count = 4 if customer_index <= 5 else 1
        for event_position in range(1, event_count + 1):
            touchpoint = TOUCHPOINTS[event_position - 1][0] if event_count == 4 else TOUCHPOINTS[(customer_index - 1) % len(TOUCHPOINTS)][0]
            add(
                scenario,
                f"exp-identity-{customer_index:03d}-{event_position}",
                customer_code,
                f"VISIT-{scenario}",
                touchpoint,
                (customer_index - 1) * 40 + (event_position - 1) * 5,
                f"observations/{subject}/{event_position:02d}.jpg",
                expected_face_count=2,
                subject=subject,
                condition=f"composite-layout-{event_position}",
            )
    add("EXP-UNKNOWN", "exp-unknown-1", "", "", "TP-DISPLAY", 4050, "observations/unknown/fairface-0108.jpg", identity_status="NO_MATCH", expected_face_count=2, subject="fairface-0108", condition="composite-layout-1")
    add("EXP-UNKNOWN", "exp-unknown-2", "", "", "TP-CONSULT", 4055, "observations/unknown/fairface-0109.jpg", identity_status="NO_MATCH", expected_face_count=2, subject="fairface-0109", condition="composite-layout-2")
    add("EXP-ERROR", "exp-no-face", "", "", "TP-ENTRANCE", 4060, "observations/errors/no-face.jpg", image_status="NO_FACE", identity_status="NOT_RUN", expected_face_count=0)
    add("EXP-ERROR", "exp-many-faces", "", "", "TP-ENTRANCE", 4061, "observations/errors/multiple-faces.jpg", image_status="VALID", identity_status="NO_MATCH", expected_face_count=2)
    add("EXP-ERROR", "exp-invalid-image", "", "", "TP-ENTRANCE", 4062, "observations/errors/invalid.jpg", image_status="INVALID_IMAGE", identity_status="NOT_RUN", expected_face_count=0)
    write_csv("events.csv", events, list(events[0]))
    expected = {
        "customers": {f"CUS-EXP-{index:03d}": {"minimum_visits": 1} for index in range(1, CUSTOMER_COUNT + 1)},
        "scenarios": {f"EXP-IDENTITY-{index:03d}": {"touchpoints": [item[0] for item in TOUCHPOINTS]} for index in range(1, 6)},
    }
    save_json(DATASET_ROOT / "expected" / "expected_visits.json", expected)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path)
    args = parser.parse_args()
    if args.source and not args.source.exists():
        raise SystemExit(f"Không tìm thấy nguồn: {args.source}")
    prepare(args.source.resolve() if args.source else None)
