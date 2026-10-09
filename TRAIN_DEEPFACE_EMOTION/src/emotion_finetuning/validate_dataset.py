from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config, resolve_path
from .dataset import load_training_bundle
from .io import write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Kiểm tra FER-2013 cho bước tinh chỉnh.")
    parser.add_argument("--config", type=Path, default=Path("configs/train.yaml"))
    args = parser.parse_args()
    project_root = args.config.resolve().parent.parent
    config = load_config(args.config)
    dataset_config = config["dataset"]
    bundle = load_training_bundle(
        resolve_path(project_root, str(config["paths"]["fer2013_csv"])),
        expected_counts={
            key: int(value)
            for key, value in dataset_config["expected_counts"].items()
        },
        strict_counts=bool(dataset_config["strict_counts"]),
        fail_on_cross_split_duplicates=bool(
            dataset_config["fail_on_cross_split_duplicates"]
        ),
    )
    output = project_root / "dataset_manifest.json"
    write_json(output, bundle.manifest)
    print(f"FER-2013 hợp lệ. Bản kê khai: {output}")


if __name__ == "__main__":
    main()
