from __future__ import annotations

import argparse
import json
import platform
import shutil
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np

from .config import load_config, resolve_path, validate_training_config
from .constants import LABELS
from .dataset import balanced_class_weights
from .io import sha256_file, write_json, write_jsonl
from .metrics import classification_metrics
from .model import EmotionFineTuner


def prediction_rows(
    paths: np.ndarray,
    groups: np.ndarray,
    true_labels: np.ndarray,
    scores: np.ndarray,
) -> list[dict[str, Any]]:
    predicted = np.argmax(scores, axis=1).astype(np.int64)
    return [
        {
            "path": str(path),
            "group": str(group),
            "true_label_id": int(true_label),
            "true_label": LABELS[int(true_label)],
            "predicted_label_id": int(predicted_label),
            "predicted_label": LABELS[int(predicted_label)],
            "scores": [float(value) for value in row_scores],
        }
        for path, group, true_label, predicted_label, row_scores in zip(
            paths, groups, true_labels, predicted, scores, strict=True
        )
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tinh chỉnh DeepFace Emotion trên KDEF với nhóm đánh giá được giữ riêng."
    )
    parser.add_argument("--config", type=Path, default=Path("configs/train_kdef.yaml"))
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    project_root = args.config.resolve().parent.parent
    config = load_config(args.config)
    validate_training_config(config)
    paths = config["paths"]
    dataset_path = resolve_path(project_root, str(paths["dataset_npz"]))
    dataset_manifest_path = resolve_path(project_root, str(paths["dataset_manifest"]))
    initial_weights = resolve_path(project_root, str(paths["initial_weights"]))
    artifacts_root = resolve_path(project_root, str(paths["artifacts_root"]))
    run_dir = artifacts_root / args.run_id
    if run_dir.exists():
        raise FileExistsError(f"Run ID đã tồn tại, không ghi đè: {run_dir}")
    run_dir.mkdir(parents=True)
    shutil.copy2(args.config, run_dir / "resolved_config.yaml")

    source_manifest = json.loads(dataset_manifest_path.read_text(encoding="utf-8"))
    if source_manifest["evaluation_groups_used_for_training"] is not False:
        raise ValueError("Các nhóm đánh giá không được xuất hiện trong dữ liệu huấn luyện")
    if sha256_file(dataset_path) != source_manifest["tensor_archive_sha256"]:
        raise ValueError("Hàm băm bộ tensor KDEF không khớp bản kê khai")
    bundle = np.load(dataset_path, allow_pickle=False)
    training_images = bundle["training_images"]
    training_labels = bundle["training_labels"]
    validation_images = bundle["validation_images"]
    validation_labels = bundle["validation_labels"]
    if training_images.shape[1:] != (48, 48) or validation_images.shape[1:] != (48, 48):
        raise ValueError("Ảnh KDEF phải có kích thước 48x48")
    if float(training_images.min()) < 0 or float(training_images.max()) > 1:
        raise ValueError("Ảnh huấn luyện KDEF phải nằm trong khoảng 0..1")

    training_config = config["training"]
    seed = int(config["run"]["seed"])
    class_weights = (
        balanced_class_weights(training_labels)
        if bool(training_config.get("use_class_weights", True))
        else None
    )
    checkpoint = run_dir / "models" / "deepface_emotion_kdef.weights.h5"
    tuner = EmotionFineTuner(
        initial_weights=initial_weights,
        batch_size=int(training_config["batch_size"]),
    )
    fit_summary = tuner.fit(
        training_images=training_images,
        training_labels=training_labels,
        validation_images=validation_images,
        validation_labels=validation_labels,
        checkpoint_path=checkpoint,
        class_weight=class_weights,
        seed=seed,
        epochs=int(training_config["epochs"]),
        learning_rate=float(training_config["learning_rate"]),
        patience=int(training_config["patience"]),
        min_delta=float(training_config["min_delta"]),
        deterministic_ops=bool(training_config.get("deterministic_ops", True)),
        augmentation=dict(training_config.get("augmentation", {})),
    )

    validation_scores = tuner.predict_scores(validation_images)
    validation_predictions = np.argmax(validation_scores, axis=1).astype(np.int64)
    validation_metrics = classification_metrics(validation_labels, validation_predictions)
    write_json(run_dir / "validation_metrics.json", validation_metrics)
    write_jsonl(
        run_dir / "validation_predictions.jsonl",
        prediction_rows(
            bundle["validation_paths"],
            bundle["validation_groups"],
            validation_labels,
            validation_scores,
        ),
    )
    shutil.copy2(dataset_manifest_path, run_dir / "dataset_manifest.json")
    manifest = {
        "run_id": args.run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_path": str(dataset_path),
        "dataset_sha256": sha256_file(dataset_path),
        "labels": list(LABELS),
        "training_groups": source_manifest["training_groups"],
        "validation_groups": source_manifest["validation_groups"],
        "evaluation_groups": source_manifest["evaluation_groups"],
        "evaluation_groups_used_for_training": False,
        "training_samples": int(training_labels.size),
        "validation_samples": int(validation_labels.size),
        "initial_model_path": str(initial_weights),
        "initial_model_sha256": sha256_file(initial_weights),
        "model_path": str(checkpoint),
        "model_sha256": sha256_file(checkpoint),
        "model_size_bytes": checkpoint.stat().st_size,
        "class_weights": class_weights,
        "hyperparameters": training_config,
        "fit": fit_summary,
        "validation": validation_metrics,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "deepface": tuner.deepface_version,
            "tensorflow": version("tensorflow"),
            "numpy": version("numpy"),
        },
    }
    write_json(run_dir / "training_manifest.json", manifest)
    print(f"Đã hoàn tất tinh chỉnh KDEF: {run_dir}")


if __name__ == "__main__":
    main()
