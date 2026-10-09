from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import cv2
import numpy as np

from demo_common import DATASET_ROOT, save_json, write_csv
from prepare_demo_dataset import write_static_crm_data


FILENAME_PATTERN = re.compile(
    r"^(?P<session>[AB])(?P<gender>[FM])(?P<identity>\d{2})"
    r"(?P<expression>AF|AN|DI|HA|NE|SA|SU)(?P<angle>FL|HL|HR|FR|S)\.JPG$",
    re.IGNORECASE,
)
KAGGLE_FILENAME_PATTERN = re.compile(r"^(?P<group_id>\d+)_(?P<image_id>\d+)\.(?:JPG|JPEG)$", re.IGNORECASE)
EXPRESSION_LABELS = {
    "AF": "Fear",
    "AN": "Angry",
    "DI": "Disgust",
    "HA": "Happy",
    "NE": "Neutral",
    "SA": "Sad",
    "SU": "Surprise",
}
LABEL_TO_CODE = {value: key for key, value in EXPRESSION_LABELS.items()}
KAGGLE_FOLDER_LABELS = {label.lower(): label for label in EXPRESSION_LABELS.values()}
TOUCHPOINTS = [
    ("TP-ENTRANCE", "Cửa vào", 1),
    ("TP-DISPLAY", "Khu trưng bày sản phẩm", 2),
    ("TP-CONSULT", "Khu tư vấn", 3),
    ("TP-CHECKOUT", "Quầy thanh toán", 4),
]
ARCHETYPES = {
    "archetype_01": ("Neutral", "Neutral", "Neutral", "Neutral"),
    "archetype_02": ("Happy", "Happy", "Happy", "Happy"),
    "archetype_03": ("Neutral", "Surprise", "Happy", "Happy"),
    "archetype_04": ("Neutral", "Sad", "Angry", "Angry"),
    # Cùng tỷ lệ nhãn với archetype_03 nhưng khác thứ tự để so sánh với
    # baseline tỷ lệ trạng thái vốn không giữ thông tin trình tự.
    "archetype_05": ("Happy", "Neutral", "Surprise", "Happy"),
}
CAMERA_PRIORITY = (
    ("B", "S"),
    ("B", "HL"),
    ("B", "HR"),
    ("A", "HL"),
    ("A", "HR"),
    ("B", "FL"),
    ("B", "FR"),
    ("A", "FL"),
    ("A", "FR"),
    ("A", "S"),
)


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_kdef_filename(path: Path) -> dict[str, str]:
    match = FILENAME_PATTERN.fullmatch(path.name.upper())
    if not match:
        raise ValueError(f"Tên tệp KDEF không hợp lệ: {path.name}")
    values = {key: value.upper() for key, value in match.groupdict().items()}
    values["subject_id"] = f"{values['gender']}{values['identity']}"
    values["expression_label"] = EXPRESSION_LABELS[values["expression"]]
    return values


def discover_images(root: Path) -> tuple[dict[tuple[str, str, str, str], Path], list[str]]:
    parsed: dict[tuple[str, str, str, str], Path] = {}
    ignored: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".jpg", ".jpeg"}:
            continue
        try:
            metadata = parse_kdef_filename(path)
        except ValueError:
            ignored.append(str(path.relative_to(root)))
            continue
        key = (
            metadata["subject_id"],
            metadata["session"],
            metadata["expression"],
            metadata["angle"],
        )
        if key in parsed:
            raise ValueError(f"Tệp KDEF bị trùng khóa {key}: {parsed[key]} và {path}")
        parsed[key] = path
    return parsed, ignored


def discover_kaggle_images(
    root: Path,
) -> tuple[dict[tuple[str, str], list[Path]], list[str]]:
    """Đọc bản KDEF đã xử lý theo cấu trúc ``<label>/<group>_<image>.jpg``.

    ``group`` là mã nhóm nguồn do bộ Kaggle cung cấp, không được diễn giải là
    mã chủ thể KDEF gốc hoặc phiên A/B vì mirror đã bỏ các trường đó.
    """

    parsed: dict[tuple[str, str], list[Path]] = defaultdict(list)
    ignored: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".jpg", ".jpeg"}:
            continue
        label = KAGGLE_FOLDER_LABELS.get(path.parent.name.lower())
        match = KAGGLE_FILENAME_PATTERN.fullmatch(path.name)
        if label is None or match is None:
            ignored.append(str(path.relative_to(root)))
            continue
        group_id = f"KG{int(match.group('group_id')):03d}"
        parsed[(group_id, label)].append(path)
    for paths in parsed.values():
        paths.sort(key=lambda item: tuple(int(value) for value in re.findall(r"\d+", item.stem)))
    return parsed, ignored


def eligible_subjects(images: dict[tuple[str, str, str, str], Path]) -> list[str]:
    subjects = sorted({key[0] for key in images})
    required = {
        (session, expression, angle)
        for session in ("A", "B")
        for expression in EXPRESSION_LABELS
        for angle in ("FL", "HL", "S", "HR", "FR")
    }
    eligible = []
    for subject in subjects:
        actual = {(session, expression, angle) for who, session, expression, angle in images if who == subject}
        if required.issubset(actual):
            eligible.append(subject)
    return eligible


def eligible_kaggle_groups(images: dict[tuple[str, str], list[Path]]) -> list[str]:
    groups = sorted({key[0] for key in images})
    required_labels = set(EXPRESSION_LABELS.values())
    return [
        group_id
        for group_id in groups
        if required_labels.issubset({label for who, label in images if who == group_id})
    ]


def read_image(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None or image.size == 0:
        raise ValueError(f"Không đọc được ảnh KDEF: {path}")
    return image


def frontal_score(path: Path) -> tuple[int, float, float]:
    """Ưu tiên ảnh nhìn thẳng bằng bộ dò Haar; tên tệp là khóa phụ ổn định."""

    image = read_image(path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(
        str(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml")
    )
    boxes = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
    if len(boxes) == 0:
        return (0, 0.0, 0.0)
    height, width = gray.shape[:2]
    best = max(boxes, key=lambda box: int(box[2]) * int(box[3]))
    x, y, face_width, face_height = (int(value) for value in best)
    area_ratio = (face_width * face_height) / float(width * height)
    center_x = x + face_width / 2
    center_y = y + face_height / 2
    center_error = abs(center_x - width / 2) / width + abs(center_y - height / 2) / height
    return (1, area_ratio, -center_error)


def ordered_kaggle_candidates(paths: list[Path]) -> list[Path]:
    return sorted(paths, key=lambda path: (frontal_score(path), path.name), reverse=True)


def render_on_canvas(
    source: Path,
    output: Path,
    *,
    canvas_size: tuple[int, int],
    target_height: int,
    offset: tuple[int, int],
    brightness: int = 0,
) -> dict:
    image = read_image(source)
    source_height, source_width = image.shape[:2]
    scale = target_height / source_height
    resized = cv2.resize(
        image,
        (max(1, round(source_width * scale)), target_height),
        interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC,
    )
    if brightness:
        resized = cv2.convertScaleAbs(resized, alpha=1.0, beta=brightness)
    canvas_width, canvas_height = canvas_size
    canvas = np.full((canvas_height, canvas_width, 3), 228, dtype=np.uint8)
    x, y = offset
    x2 = min(canvas_width, x + resized.shape[1])
    y2 = min(canvas_height, y + resized.shape[0])
    if x < 0 or y < 0 or x2 <= x or y2 <= y:
        raise ValueError(f"Vị trí ảnh vượt canvas: {source.name}")
    canvas[y:y2, x:x2] = resized[: y2 - y, : x2 - x]
    output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output), canvas, [cv2.IMWRITE_JPEG_QUALITY, 94]):
        raise RuntimeError(f"Không ghi được ảnh: {output}")
    return {
        "canvas_width": canvas_width,
        "canvas_height": canvas_height,
        "offset_x": x,
        "offset_y": y,
        "target_height": target_height,
        "brightness": brightness,
    }


def write_profile(source: Path, output: Path) -> None:
    image = read_image(source)
    height, width = image.shape[:2]
    side = min(height, width)
    x = (width - side) // 2
    y = max(0, (height - side) // 2 - side // 12)
    y = min(y, height - side)
    crop = image[y : y + side, x : x + side]
    profile = cv2.resize(crop, (256, 256), interpolation=cv2.INTER_AREA)
    output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output), profile, [cv2.IMWRITE_JPEG_QUALITY, 94]):
        raise RuntimeError(f"Không ghi được ảnh đại diện: {output}")


def camera_candidates(
    images: dict[tuple[str, str, str, str], Path],
    subject_id: str,
    expression_code: str,
) -> list[Path]:
    result = []
    for session, angle in CAMERA_PRIORITY:
        path = images[(subject_id, session, expression_code, angle)]
        if expression_code == "NE" and session == "A" and angle == "S":
            continue
        result.append(path)
    return result


def prepare(kdef_root: Path, *, customer_count: int, seed: int, experiment_run_id: str) -> None:
    if not kdef_root.exists() or not kdef_root.is_dir():
        raise SystemExit(f"Không tìm thấy thư mục KDEF: {kdef_root}")
    images, ignored = discover_images(kdef_root)
    kaggle_images: dict[tuple[str, str], list[Path]] = {}
    source_layout = "official_filename_layout"
    if images:
        eligible = eligible_subjects(images)
    else:
        kaggle_images, ignored = discover_kaggle_images(kdef_root)
        eligible = eligible_kaggle_groups(kaggle_images)
        source_layout = "kaggle_label_folders"
    if len(eligible) < customer_count:
        raise SystemExit(
            f"Nguồn KDEF chỉ có {len(eligible)} nhóm đủ bảy nhãn, cần {customer_count}"
        )
    selected = sorted(random.Random(seed).sample(eligible, customer_count))

    if DATASET_ROOT.exists():
        shutil.rmtree(DATASET_ROOT)
    for relative in ("customer_images", "enrollment", "calibration", "observations", "expected"):
        (DATASET_ROOT / relative).mkdir(parents=True, exist_ok=True)

    # Tái sử dụng danh mục sản phẩm/điểm chạm hiện có, sau đó thay phần khách hàng
    # và đơn hàng bằng manifest KDEF của lần chạy này.
    write_static_crm_data()
    customers: list[dict] = []
    image_manifest: list[dict] = []
    events: list[dict] = []
    base = datetime(2026, 10, 8, 9, 0, tzinfo=timezone(timedelta(hours=7)))
    layouts = (
        ((455, 86), 540, -6),
        ((420, 92), 525, 4),
        ((475, 78), 550, 8),
        ((438, 96), 520, -3),
    )

    for customer_index, subject_id in enumerate(selected, 1):
        customer_code = f"CUS-KDEF-{customer_index:03d}"
        if source_layout == "official_filename_layout":
            enrollment_source = images[(subject_id, "A", "NE", "S")]
            enrollment_session = "A"
            enrollment_angle = "S"
            calibration_sources = {
                label: images[(subject_id, "B", code, "S")]
                for label, code in LABEL_TO_CODE.items()
            }
        else:
            ordered_sources = {
                label: ordered_kaggle_candidates(kaggle_images[(subject_id, label)])
                for label in LABEL_TO_CODE
            }
            neutral_candidates = ordered_sources["Neutral"]
            enrollment_source = neutral_candidates[0]
            enrollment_session = "not_available"
            enrollment_angle = "frontal_selected_by_detector"
            calibration_sources = {
                label: (paths[1] if label == "Neutral" else paths[0])
                for label, paths in ordered_sources.items()
            }
        profile_output = DATASET_ROOT / "customer_images" / f"{customer_code}.jpg"
        write_profile(enrollment_source, profile_output)
        customers.append(
            {
                "customer_code": customer_code,
                "full_name": f"Khách hàng KDEF {subject_id}",
                "phone": f"0910{customer_index:06d}",
                "email": f"kdef.{subject_id.lower()}@example.com",
                "subject_id": subject_id,
                "profile_image_url": f"/demo/customers/{customer_code}.jpg",
            }
        )
        enrollment_output = DATASET_ROOT / "enrollment" / subject_id / "enrollment.jpg"
        transform = render_on_canvas(
            enrollment_source,
            enrollment_output,
            canvas_size=(640, 480),
            target_height=430,
            offset=(161, 25),
        )
        image_manifest.append(
            {
                "role": "enrollment",
                "subject_id": subject_id,
                "customer_code": customer_code,
                "source_filename": enrollment_source.name,
                "source_sha256": checksum(enrollment_source),
                "output": str(enrollment_output.relative_to(DATASET_ROOT)),
                "output_sha256": checksum(enrollment_output),
                "expression_label": "Neutral",
                "session": enrollment_session,
                "angle": enrollment_angle,
                **transform,
            }
        )

        for label, calibration_source in calibration_sources.items():
            calibration_output = DATASET_ROOT / "calibration" / subject_id / f"{label.lower()}.jpg"
            calibration_transform = render_on_canvas(
                calibration_source,
                calibration_output,
                canvas_size=(1280, 720),
                target_height=535,
                offset=(450, 88),
            )
            image_manifest.append(
                {
                    "role": "calibration",
                    "subject_id": subject_id,
                    "customer_code": customer_code,
                    "source_filename": calibration_source.name,
                    "source_sha256": checksum(calibration_source),
                    "output": str(calibration_output.relative_to(DATASET_ROOT)),
                    "output_sha256": checksum(calibration_output),
                    "expression_label": label,
                    "session": "B" if source_layout == "official_filename_layout" else "not_available",
                    "angle": "S" if source_layout == "official_filename_layout" else "calibration_reserved",
                    **calibration_transform,
                }
            )

        if source_layout == "official_filename_layout":
            pools = {
                label: [
                    path
                    for path in camera_candidates(images, subject_id, code)
                    if path != calibration_sources[label]
                ]
                for label, code in LABEL_TO_CODE.items()
            }
        else:
            pools = {
                label: [
                    path
                    for path in ordered_sources[label]
                    if path not in {enrollment_source, calibration_sources[label]}
                ]
                for label in LABEL_TO_CODE
            }
        consumed = Counter()
        for visit_index, (archetype_id, sequence) in enumerate(ARCHETYPES.items(), 1):
            scenario_id = f"KDEF-{subject_id}-{archetype_id}"
            visit_key = f"VISIT-{experiment_run_id}-{subject_id}-{visit_index:02d}"
            for event_index, ((touchpoint_code, _name, _order), label) in enumerate(
                zip(TOUCHPOINTS, sequence, strict=True),
                1,
            ):
                pool_index = consumed[label]
                if not pools[label]:
                    raise RuntimeError(f"Không có ảnh {label} cho {subject_id}")
                source = pools[label][pool_index % len(pools[label])]
                consumed[label] += 1
                if source_layout == "official_filename_layout":
                    source_meta = parse_kdef_filename(source)
                    source_session = source_meta["session"]
                    source_angle = source_meta["angle"]
                else:
                    source_session = "not_available"
                    source_angle = f"candidate_{pool_index % len(pools[label]) + 1}"
                event_id = f"{experiment_run_id}-{subject_id}-V{visit_index:02d}-E{event_index:02d}"
                output = DATASET_ROOT / "observations" / subject_id / f"V{visit_index:02d}-E{event_index:02d}.jpg"
                offset, target_height, brightness = layouts[event_index - 1]
                transform = render_on_canvas(
                    source,
                    output,
                    canvas_size=(1280, 720),
                    target_height=target_height,
                    offset=offset,
                    brightness=brightness,
                )
                observed_at = base + timedelta(
                    days=visit_index - 1,
                    minutes=(customer_index - 1) * 20 + (event_index - 1) * 5,
                )
                events.append(
                    {
                        "experiment_run_id": experiment_run_id,
                        "scenario_id": scenario_id,
                        "archetype_id": archetype_id,
                        "event_id": event_id,
                        "expected_customer_code": customer_code,
                        "expected_visit_key": visit_key,
                        "touchpoint_code": touchpoint_code,
                        "observed_at": observed_at.isoformat(),
                        "image_path": str(output.relative_to(DATASET_ROOT)),
                        "source_subject_id": subject_id,
                        "source_filename": source.name,
                        "expected_expression_label": label,
                        "expected_image_status": "VALID",
                        "expected_identity_status": "MATCHED",
                        "expected_face_count": 1,
                    }
                )
                image_manifest.append(
                    {
                        "role": "observation",
                        "subject_id": subject_id,
                        "customer_code": customer_code,
                        "source_filename": source.name,
                        "source_sha256": checksum(source),
                        "output": str(output.relative_to(DATASET_ROOT)),
                        "output_sha256": checksum(output),
                        "expression_label": label,
                        "session": source_session,
                        "angle": source_angle,
                        **transform,
                    }
                )

    write_csv("customers.csv", customers, list(customers[0]))
    write_csv("orders.csv", [], ["external_code", "customer_code", "ordered_at", "status"])
    write_csv("order_items.csv", [], ["external_code", "sku", "quantity", "unit_price"])
    write_csv("events.csv", events, list(events[0]))
    with (DATASET_ROOT / "image_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(image_manifest[0]))
        writer.writeheader()
        writer.writerows(image_manifest)

    expected = {
        "experiment_run_id": experiment_run_id,
        "customer_count": customer_count,
        "visits_per_customer": len(ARCHETYPES),
        "events_per_visit": len(TOUCHPOINTS),
        "expected_visit_count": customer_count * len(ARCHETYPES),
        "expected_event_count": customer_count * len(ARCHETYPES) * len(TOUCHPOINTS),
        "customers": {row["customer_code"]: {"subject_id": row["subject_id"], "expected_visits": len(ARCHETYPES)} for row in customers},
        "scenarios": {
            row["scenario_id"]: {
                "archetype_id": row["archetype_id"],
                "customer_code": row["expected_customer_code"],
                "touchpoints": [item[0] for item in TOUCHPOINTS],
            }
            for row in events[:: len(TOUCHPOINTS)]
        },
    }
    save_json(DATASET_ROOT / "expected" / "expected_visits.json", expected)
    save_json(
        DATASET_ROOT / "kdef_demo_manifest.json",
        {
            "dataset": "Karolinska Directed Emotional Faces (KDEF)",
            "distribution": "Processed KDEF mirror on Kaggle",
            "distribution_url": "https://www.kaggle.com/datasets/chenrich/kdef-database",
            "homepage": "https://kdef.se/home/aboutKDEF",
            "usage_terms": "https://kdef.se/faq/using-and-publishing-kdef-and-akdef",
            "source_layout": source_layout,
            "source_image_count": (
                len(images) if source_layout == "official_filename_layout"
                else sum(len(paths) for paths in kaggle_images.values())
            ),
            "eligible_source_group_count": len(eligible),
            "seed": seed,
            "experiment_run_id": experiment_run_id,
            "selected_subjects": selected,
            "customer_count": customer_count,
            "ignored_non_kdef_files": ignored,
            "raw_images_embedded": False,
        },
    )
    print(
        f"Đã tạo demo KDEF tại {DATASET_ROOT}: "
        f"{customer_count} khách, {expected['expected_visit_count']} visit, {len(events)} sự kiện"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--kdef-root", type=Path, required=True)
    parser.add_argument("--customer-count", type=int, default=25)
    parser.add_argument("--seed", type=int, default=20261008)
    parser.add_argument("--experiment-run-id", default="KDEF-DEMO-20261008")
    args = parser.parse_args()
    if not 4 <= args.customer_count <= 70:
        raise SystemExit("customer-count phải nằm trong [4, 70]")
    if not args.experiment_run_id or len(args.experiment_run_id) > 64:
        raise SystemExit("experiment-run-id phải có 1-64 ký tự")
    prepare(
        args.kdef_root.expanduser().resolve(),
        customer_count=args.customer_count,
        seed=args.seed,
        experiment_run_id=args.experiment_run_id,
    )
