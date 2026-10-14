from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

from demo_common import save_json
from prepare_kdef_demo import (
    LABEL_TO_CODE,
    checksum,
    discover_kaggle_images,
    eligible_kaggle_groups,
    ordered_kaggle_candidates,
    render_on_canvas,
)


def prepare(
    source_root: Path,
    output_root: Path,
    *,
    group_count: int,
    seed: int,
    groups_file: Path | None,
) -> None:
    images, ignored = discover_kaggle_images(source_root)
    eligible = eligible_kaggle_groups(images)
    if len(eligible) < group_count:
        raise SystemExit(
            f"Chỉ có {len(eligible)} mã nhóm đủ bảy nhãn, cần {group_count}"
        )
    if output_root.exists():
        raise SystemExit(f"Không ghi đè dữ liệu cũ: {output_root}")

    if groups_file is None:
        selected = sorted(random.Random(seed).sample(eligible, group_count))
        selection_method = "fixed-seed random sample"
    else:
        group_payload = json.loads(groups_file.read_text(encoding="utf-8"))
        selected = sorted(str(value) for value in group_payload["selected_groups"])
        if len(selected) != group_count or len(set(selected)) != group_count:
            raise SystemExit(
                f"Tệp nhóm phải chứa đúng {group_count} mã duy nhất"
            )
        missing = sorted(set(selected) - set(eligible))
        if missing:
            raise SystemExit(f"Mã nhóm không hợp lệ: {missing}")
        selection_method = str(group_payload.get("method", "explicit group list"))
    calibration_root = output_root / "calibration"
    calibration_root.mkdir(parents=True)
    rows: list[dict[str, str | int]] = []
    for group_id in selected:
        for expression_label in LABEL_TO_CODE:
            candidates = ordered_kaggle_candidates(images[(group_id, expression_label)])
            source = candidates[0]
            output = calibration_root / group_id / f"{expression_label.lower()}.jpg"
            transform = render_on_canvas(
                source,
                output,
                canvas_size=(1280, 720),
                target_height=535,
                offset=(450, 88),
            )
            rows.append(
                {
                    "group_id": group_id,
                    "expression_label": expression_label,
                    "source_filename": source.name,
                    "source_sha256": checksum(source),
                    "output": str(output.relative_to(output_root)),
                    "output_sha256": checksum(output),
                    **transform,
                }
            )

    manifest_path = output_root / "calibration_manifest.csv"
    with manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    experiment_run_id = f"KDEF-{group_count}-GROUP-CALIBRATION-20261014"
    save_json(
        output_root / "kdef_demo_manifest.json",
        {
            "dataset": "Karolinska Directed Emotional Faces (KDEF)",
            "distribution": "Processed KDEF mirror on Kaggle",
            "distribution_url": "https://www.kaggle.com/datasets/chenrich/kdef-database",
            "source_layout": "kaggle_label_folders",
            "source_image_count": sum(len(paths) for paths in images.values()),
            "eligible_source_group_count": len(eligible),
            "selected_source_group_count": len(selected),
            "selected_subjects": selected,
            "calibration_images_per_group": len(LABEL_TO_CODE),
            "calibration_image_count": len(rows),
            "selection_seed": seed,
            "selection_method": selection_method,
            "groups_file": str(groups_file) if groups_file is not None else None,
            "experiment_run_id": experiment_run_id,
            "ignored_files": ignored,
            "identity_scope": (
                "Source group identifiers are used as calibration labels because the "
                "processed mirror does not preserve original KDEF subject identifiers."
            ),
        },
    )
    print(
        f"Đã tạo tập hiệu chỉnh tại {output_root}: "
        f"{len(selected)} mã nhóm, {len(rows)} ảnh"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tạo tập hiệu chỉnh ArcFace từ bản KDEF đã xử lý trên Kaggle."
    )
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--group-count", type=int, default=70)
    parser.add_argument("--seed", type=int, default=20261008)
    parser.add_argument("--groups-file", type=Path)
    args = parser.parse_args()
    prepare(
        args.source_root.expanduser().resolve(),
        args.output_root.expanduser().resolve(),
        group_count=args.group_count,
        seed=args.seed,
        groups_file=(
            args.groups_file.expanduser().resolve()
            if args.groups_file is not None
            else None
        ),
    )


if __name__ == "__main__":
    main()
