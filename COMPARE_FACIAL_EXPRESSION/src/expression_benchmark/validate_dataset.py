from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config, resolve_path
from .dataset import load_fer2013
from .io import write_json


def main() -> None:
    parser = argparse.ArgumentParser(description="Kiểm tra cấu trúc và phân chia FER-2013.")
    parser.add_argument("--config", type=Path, default=Path("configs/benchmark.yaml"))
    parser.add_argument("--output", type=Path, default=Path("dataset_manifest.json"))
    args = parser.parse_args()

    project_root = args.config.resolve().parent.parent
    config = load_config(args.config)
    dataset_config = config["dataset"]
    csv_path = resolve_path(project_root, config["paths"]["fer2013_csv"])
    bundle = load_fer2013(
        csv_path,
        strict_counts=bool(dataset_config["strict_counts"]),
        expected_counts={key: int(value) for key, value in dataset_config["expected_counts"].items()},
        fail_on_cross_split_duplicates=bool(dataset_config["fail_on_cross_split_duplicates"]),
        training_fraction=float(dataset_config.get("training_fraction", 1.0)),
        sampling_seed=int(dataset_config.get("sampling_seed", 0)),
    )
    output = args.output if args.output.is_absolute() else project_root / args.output
    write_json(output, bundle.manifest)
    print(f"FER-2013 hợp lệ. Bản kê khai: {output}")


if __name__ == "__main__":
    main()
