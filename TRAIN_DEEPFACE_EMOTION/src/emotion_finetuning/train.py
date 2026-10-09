from __future__ import annotations

import argparse
import platform
import shutil
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np

from .config import load_config, resolve_path, validate_training_config
from .constants import LABELS
from .dataset import balanced_class_weights, load_training_bundle
from .io import sha256_file, write_json, write_jsonl
from .metrics import classification_metrics
from .model import EmotionFineTuner


def _prediction_rows(
    sample_ids: tuple[str, ...],
    true_labels: np.ndarray,
    scores: np.ndarray,
) -> list[dict[str, Any]]:
    predicted = np.argmax(scores, axis=1).astype(np.int64)
    return [
        {
            "sample_id": sample_id,
            "true_label_id": int(true_label),
            "true_label": LABELS[int(true_label)],
            "predicted_label_id": int(predicted_label),
            "predicted_label": LABELS[int(predicted_label)],
            "scores": [float(value) for value in row_scores],
        }
        for sample_id, true_label, predicted_label, row_scores in zip(
            sample_ids,
            true_labels,
            predicted,
            scores,
            strict=True,
        )
    ]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tinh chỉnh DeepFace Emotion bằng FER-2013 Training/PublicTest."
    )
    parser.add_argument("--config", type=Path, default=Path("configs/train.yaml"))
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    project_root = args.config.resolve().parent.parent
    config = load_config(args.config)
    validate_training_config(config)
    paths = config["paths"]
    dataset_path = resolve_path(project_root, str(paths["fer2013_csv"]))
    initial_weights = resolve_path(project_root, str(paths["initial_weights"]))
    artifacts_root = resolve_path(project_root, str(paths["artifacts_root"]))
    run_dir = artifacts_root / args.run_id
    if run_dir.exists():
        raise FileExistsError(f"Run ID đã tồn tại, không ghi đè: {run_dir}")
    run_dir.mkdir(parents=True)
    shutil.copy2(args.config, run_dir / "resolved_config.yaml")

    dataset_config = config["dataset"]
    bundle = load_training_bundle(
        dataset_path,
        expected_counts={
            key: int(value)
            for key, value in dataset_config["expected_counts"].items()
        },
        strict_counts=bool(dataset_config["strict_counts"]),
        fail_on_cross_split_duplicates=bool(
            dataset_config["fail_on_cross_split_duplicates"]
        ),
    )
    write_json(run_dir / "dataset_manifest.json", bundle.manifest)

    training_config = config["training"]
    seed = int(config["run"]["seed"])
    class_weights = (
        balanced_class_weights(bundle.training.labels)
        if bool(training_config.get("use_class_weights", True))
        else None
    )
    checkpoint = run_dir / "models" / "deepface_emotion_finetuned.weights.h5"
    tuner = EmotionFineTuner(
        initial_weights=initial_weights,
        batch_size=int(training_config["batch_size"]),
    )
    fit_summary = tuner.fit(
        training_images=bundle.training.images,
        training_labels=bundle.training.labels,
        validation_images=bundle.validation.images,
        validation_labels=bundle.validation.labels,
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

    validation_scores = tuner.predict_scores(bundle.validation.images)
    validation_labels = np.argmax(validation_scores, axis=1).astype(np.int64)
    validation_metrics = classification_metrics(
        bundle.validation.labels,
        validation_labels,
    )
    write_json(run_dir / "validation_metrics.json", validation_metrics)
    write_jsonl(
        run_dir / "validation_predictions.jsonl",
        _prediction_rows(
            bundle.validation.sample_ids,
            bundle.validation.labels,
            validation_scores,
        ),
    )

    manifest = {
        "run_id": args.run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_sha256": bundle.manifest["dataset_sha256"],
        "dataset_counts": bundle.manifest["counts"],
        "labels": list(LABELS),
        "training_split": "Training",
        "selection_split": "PublicTest",
        "private_test_used": False,
        "seed": seed,
        "training_samples": len(bundle.training),
        "validation_samples": len(bundle.validation),
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
    print(f"Đã hoàn tất tinh chỉnh: {run_dir}")


if __name__ == "__main__":
    main()
