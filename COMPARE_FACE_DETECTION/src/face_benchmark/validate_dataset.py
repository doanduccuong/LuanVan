from __future__ import annotations

import argparse
import json
from pathlib import Path

from .config import load_config, resolve_path
from .dataset import parse_wider_annotations, validate_dataset, write_manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("configs/benchmark.yaml"))
    parser.add_argument("--output", type=Path, default=Path("dataset_manifest.json"))
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parents[2]
    config_path = args.config if args.config.is_absolute() else project_root / args.config
    config = load_config(config_path)
    dataset_root = resolve_path(project_root, config["paths"]["dataset_root"])
    annotation_path = resolve_path(project_root, config["paths"]["annotation_txt"])
    records = parse_wider_annotations(annotation_path, dataset_root / "WIDER_val" / "images")
    ground_truth_dir = resolve_path(project_root, config["paths"]["ground_truth_dir"])
    artifact_paths = [
        project_root / "data" / "WIDER_val.zip",
        project_root / "data" / "wider_face_split.zip",
        ground_truth_dir / "wider_face_val.mat",
        ground_truth_dir / "wider_easy_val.mat",
        ground_truth_dir / "wider_medium_val.mat",
        ground_truth_dir / "wider_hard_val.mat",
        resolve_path(project_root, config["paths"]["retinaface_weights"]),
    ]
    manifest = validate_dataset(records, annotation_path, artifact_paths=artifact_paths)
    output_path = args.output if args.output.is_absolute() else project_root / args.output
    write_manifest(manifest, output_path)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    if not manifest["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
