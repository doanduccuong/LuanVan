from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import tarfile
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import cv2
import numpy as np

from demo_common import DATASET_ROOT, SYSTEM_ROOT, save_json, write_csv


REGISTERED_SUBJECTS = [f"subject{index:02d}" for index in range(9, 14)]
CALIBRATION_SUBJECTS = [f"subject{index:02d}" for index in range(1, 9)]
UNKNOWN_SUBJECTS = ["subject14", "subject15"]
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


def safe_extract(archive: Path, destination: Path) -> Path:
    if archive.is_dir():
        return archive
    if not tarfile.is_tarfile(archive):
        raise ValueError("DEMO_SOURCE phải là thư mục đã giải nén hoặc tệp tar của Yale")
    with tarfile.open(archive) as bundle:
        base = destination.resolve()
        for member in bundle.getmembers():
            target = (destination / member.name).resolve()
            if base not in target.parents and target != base:
                raise ValueError("Tệp nén chứa đường dẫn không an toàn")
        bundle.extractall(destination)
    return destination


def index_images(root: Path) -> dict[tuple[str, str], Path]:
    index: dict[tuple[str, str], Path] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.lower()
        if not name.startswith("subject") or "." not in name:
            continue
        parts = name.split(".")
        subject, condition = parts[0], parts[1]
        index[(subject, condition)] = path
    return index


def choose(index: dict[tuple[str, str], Path], subject: str, preferred: list[str]) -> tuple[Path, str]:
    for condition in preferred:
        if (subject, condition) in index:
            return index[(subject, condition)], condition
    matches = sorted((condition, path) for (item_subject, condition), path in index.items() if item_subject == subject)
    if not matches:
        raise ValueError(f"Không tìm thấy ảnh cho {subject}")
    condition, path = matches[0]
    return path, condition


def render_scene(source: Path, output: Path, offset: tuple[int, int], face_height: int = 300, brightness: int = 0) -> dict:
    image = cv2.imread(str(source), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Không đọc được ảnh {source}")
    height, width = image.shape[:2]
    scale = face_height / height
    resized = cv2.resize(image, (max(1, int(width * scale)), face_height), interpolation=cv2.INTER_CUBIC)
    if brightness:
        resized = cv2.convertScaleAbs(resized, alpha=1.0, beta=brightness)
    canvas = np.full((480, 640, 3), 224, dtype=np.uint8)
    x, y = offset
    x2, y2 = min(640, x + resized.shape[1]), min(480, y + resized.shape[0])
    canvas[y:y2, x:x2] = resized[: y2 - y, : x2 - x]
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), canvas, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return {"offset_x": x, "offset_y": y, "face_height": face_height, "brightness": brightness}


def prepare(source: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="touchpoint-demo-") as temporary:
        source_root = safe_extract(source, Path(temporary))
        images = index_images(source_root)
        if len({subject for subject, _ in images}) < 15:
            raise ValueError("Nguồn không có đủ 15 mã người của Yale Face Database")

        for relative in ("enrollment", "observations", "calibration"):
            target = DATASET_ROOT / relative
            if target.exists():
                shutil.rmtree(target)
            target.mkdir(parents=True)

        manifest: list[dict] = []
        for subject in CALIBRATION_SUBJECTS:
            subject_files = sorted((condition, path) for (item_subject, condition), path in images.items() if item_subject == subject)
            for position, (condition, path) in enumerate(subject_files):
                output = DATASET_ROOT / "calibration" / subject / f"{condition}.jpg"
                transform = render_scene(path, output, (170 + position % 3 * 4, 80), 320)
                manifest.append({"output": str(output.relative_to(DATASET_ROOT)), "subject_id": subject, "condition": condition, "source_sha256": checksum(path), "output_sha256": checksum(output), **transform})

        enrollment_conditions = ["normal", "noglasses"]
        observation_conditions = ["happy", "sad", "surprised", "glasses", "leftlight", "rightlight", "sleepy", "wink"]
        for subject in REGISTERED_SUBJECTS:
            for condition in enrollment_conditions:
                source_path, used_condition = choose(images, subject, [condition, "centerlight", "normal"])
                output = DATASET_ROOT / "enrollment" / subject / f"{condition}.jpg"
                transform = render_scene(source_path, output, (175, 78), 320)
                manifest.append({"output": str(output.relative_to(DATASET_ROOT)), "subject_id": subject, "condition": used_condition, "source_sha256": checksum(source_path), "output_sha256": checksum(output), **transform})
            for position, condition in enumerate(observation_conditions):
                source_path, used_condition = choose(images, subject, [condition, "normal"])
                output = DATASET_ROOT / "observations" / subject / f"{position + 1:02d}-{condition}.jpg"
                transform = render_scene(source_path, output, (145 + position % 3 * 20, 70 + position % 2 * 8), 300 - position % 2 * 15, (position % 3 - 1) * 8)
                manifest.append({"output": str(output.relative_to(DATASET_ROOT)), "subject_id": subject, "condition": used_condition, "source_sha256": checksum(source_path), "output_sha256": checksum(output), **transform})

        for subject in UNKNOWN_SUBJECTS:
            source_path, condition = choose(images, subject, ["happy", "normal"])
            output = DATASET_ROOT / "observations" / "unknown" / f"{subject}.jpg"
            transform = render_scene(source_path, output, (170, 80), 310)
            manifest.append({"output": str(output.relative_to(DATASET_ROOT)), "subject_id": subject, "condition": condition, "source_sha256": checksum(source_path), "output_sha256": checksum(output), **transform})

        error_dir = DATASET_ROOT / "observations" / "errors"
        error_dir.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(error_dir / "no-face.jpg"), np.full((480, 640, 3), 224, dtype=np.uint8))
        (error_dir / "invalid.jpg").write_bytes(b"not-an-image")
        left = cv2.imread(str(DATASET_ROOT / "observations" / "unknown" / "subject14.jpg"))
        right = cv2.imread(str(DATASET_ROOT / "observations" / "unknown" / "subject15.jpg"))
        multi = np.full((480, 1280, 3), 224, dtype=np.uint8)
        multi[:, :640] = left
        multi[:, 640:] = right
        cv2.imwrite(str(error_dir / "multiple-faces.jpg"), multi)

        write_static_crm_data()
        write_events()
        with (DATASET_ROOT / "image_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
            fields = ["output", "subject_id", "condition", "source_sha256", "output_sha256", "offset_x", "offset_y", "face_height", "brightness"]
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(manifest)
        source_payload = {
            "dataset": "Yale Face Database",
            "url": "http://cvc.cs.yale.edu/cvc/projects/yalefaces/yalefaces.html",
            "license_scope": "publicly available for non-commercial use",
            "source": str(source),
            "source_sha256": checksum(source) if source.is_file() else None,
        }
        save_json(DATASET_ROOT / "sources.json", source_payload)
        print(f"Đã tạo bộ dữ liệu demo tại {DATASET_ROOT}")


def write_static_crm_data() -> None:
    customers = [
        {
            "customer_code": f"CUS-DEMO-{index:03d}",
            "full_name": f"Khách hàng mô phỏng {index:03d}",
            "phone": f"0900{index:06d}",
            "email": f"customer{index:03d}@example.com",
            "subject_id": f"fairface-{index:04d}",
            "profile_image_url": f"/demo/customers/CUS-DEMO-{index:03d}.jpg",
        }
        for index in range(1, 101)
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
        {"external_code": "ORD-DEMO-OLD-001", "customer_code": "CUS-DEMO-001", "ordered_at": "2026-09-01T09:00:00+07:00", "status": "COMPLETED"},
        {"external_code": "ORD-DEMO-OLD-002", "customer_code": "CUS-DEMO-002", "ordered_at": "2026-09-05T10:30:00+07:00", "status": "COMPLETED"},
        {"external_code": "ORD-DEMO-CANCELLED", "customer_code": "CUS-DEMO-003", "ordered_at": "2026-09-07T14:00:00+07:00", "status": "CANCELLED"},
    ]
    write_csv("orders.csv", orders, list(orders[0]))
    items = [
        {"external_code": "ORD-DEMO-OLD-001", "sku": "BEV-001", "quantity": "2", "unit_price": "10000"},
        {"external_code": "ORD-DEMO-OLD-001", "sku": "SNK-001", "quantity": "1", "unit_price": "25000"},
        {"external_code": "ORD-DEMO-OLD-002", "sku": "CAR-001", "quantity": "2", "unit_price": "15000"},
        {"external_code": "ORD-DEMO-CANCELLED", "sku": "CAR-002", "quantity": "1", "unit_price": "38000"},
    ]
    write_csv("order_items.csv", items, list(items[0]))


def write_events() -> None:
    base = datetime(2026, 9, 22, 9, 0, tzinfo=timezone(timedelta(hours=7)))
    events: list[dict] = []

    def add(scenario: str, event: str, customer: str, visit: str, touchpoint: str, minutes: int, path: str, image_status: str = "VALID", identity_status: str = "MATCHED", subject: str = "", condition: str = ""):
        events.append({"scenario_id": scenario, "event_id": event, "expected_customer_code": customer, "expected_visit_key": visit, "touchpoint_code": touchpoint, "observed_at": (base + timedelta(minutes=minutes)).isoformat(), "image_path": path, "expected_image_status": image_status, "expected_identity_status": identity_status, "source_subject_id": subject, "source_condition": condition})

    for idx, (touchpoint, condition) in enumerate(zip([item[0] for item in TOUCHPOINTS], ["happy", "sad", "surprised", "glasses"], strict=True)):
        add("DEMO-01", f"demo01-{idx + 1}", "CUS-DEMO-001", "VISIT-DEMO-01", touchpoint, idx * 5, f"observations/subject09/{idx + 1:02d}-{condition}.jpg", subject="subject09", condition=condition)
    for idx, (touchpoint, file_no, condition) in enumerate([("TP-ENTRANCE", 1, "happy"), ("TP-DISPLAY", 2, "sad"), ("TP-CHECKOUT", 4, "glasses")]):
        add("DEMO-02", f"demo02-{idx + 1}", "CUS-DEMO-002", "VISIT-DEMO-02", touchpoint, 60 + idx * 5, f"observations/subject10/{file_no:02d}-{condition}.jpg", subject="subject10", condition=condition)
    add("DEMO-03", "demo03-1", "CUS-DEMO-001", "VISIT-DEMO-03", "TP-ENTRANCE", 180, "observations/subject09/05-leftlight.jpg", subject="subject09", condition="leftlight")
    add("DEMO-03", "demo03-2", "CUS-DEMO-001", "VISIT-DEMO-03", "TP-CHECKOUT", 185, "observations/subject09/06-rightlight.jpg", subject="subject09", condition="rightlight")
    add("DEMO-04", "demo04-1", "", "", "TP-DISPLAY", 240, "observations/unknown/subject14.jpg", identity_status="NO_MATCH", subject="subject14", condition="happy")
    add("DEMO-05", "demo05-no-face", "", "", "TP-ENTRANCE", 250, "observations/errors/no-face.jpg", image_status="NO_FACE", identity_status="NOT_RUN")
    add("DEMO-05", "demo05-many", "", "", "TP-ENTRANCE", 251, "observations/errors/multiple-faces.jpg", image_status="MULTIPLE_FACES", identity_status="NOT_RUN")
    add("DEMO-05", "demo05-invalid", "", "", "TP-ENTRANCE", 252, "observations/errors/invalid.jpg", image_status="INVALID_IMAGE", identity_status="NOT_RUN")
    write_csv("events.csv", events, list(events[0]))
    expected = {
        "customers": {"CUS-DEMO-001": {"minimum_visits": 2}, "CUS-DEMO-002": {"minimum_visits": 1}},
        "scenarios": {"DEMO-01": {"touchpoints": [item[0] for item in TOUCHPOINTS]}, "DEMO-02": {"touchpoints": ["TP-ENTRANCE", "TP-DISPLAY", "TP-CHECKOUT"]}},
    }
    save_json(DATASET_ROOT / "expected" / "expected_visits.json", expected)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    args = parser.parse_args()
    if not args.source.exists():
        raise SystemExit(f"Không tìm thấy nguồn: {args.source}")
    prepare(args.source.resolve())
