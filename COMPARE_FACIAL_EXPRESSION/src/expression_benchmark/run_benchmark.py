from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

from .adapters.deepface_emotion import DeepFaceEmotionAdapter
from .adapters.lbp_svm import LBPSVMAdapter
from .benchmark_latency import measure_latency
from .config import ensure_private_test_allowed, load_config, resolve_path
from .constants import LABELS
from .dataset import class_weights, load_fer2013
from .environment import collect_environment
from .io import sha256_file, write_json, write_jsonl
from .metrics import classification_metrics
from .records import prediction_rows


def _weight_mapping(labels: np.ndarray) -> dict[int, float]:
    values = class_weights(labels)
    return {index: float(value) for index, value in enumerate(values)}


def _save_evaluation(
    *,
    run_dir: Path,
    method: str,
    seed: int | None,
    split: Any,
    predictions: Any,
) -> dict[str, Any]:
    suffix = method if seed is None else f"{method}_seed_{seed}"
    metrics = classification_metrics(split.labels, predictions.labels)
    write_json(run_dir / "metrics" / f"{suffix}.json", metrics)
    write_jsonl(
        run_dir / "predictions" / f"{suffix}.jsonl",
        prediction_rows(
            method=method,
            seed=seed,
            sample_ids=split.sample_ids,
            true_labels=split.labels,
            predictions=predictions,
        ),
    )
    return metrics


def _run_lbp(
    config: dict[str, Any],
    bundle: Any,
    run_dir: Path,
    evaluate_private: bool,
) -> dict[str, Any]:
    training = bundle.splits["Training"]
    validation = bundle.splits["PublicTest"]
    lbp_config = config["lbp_svm"]
    if int(lbp_config["points"]) != 8 or int(lbp_config["radius"]) != 1:
        raise ValueError("Bản cài đặt LBP hiện khóa points=8 và radius=1.")
    best_adapter: LBPSVMAdapter | None = None
    best_candidate: dict[str, Any] | None = None
    best_validation_f1 = -1.0
    candidates: list[dict[str, Any]] = []
    for candidate in lbp_config["candidates"]:
        print(f"[lbp_svm] training candidate={candidate}", flush=True)
        adapter = LBPSVMAdapter(
            grid_rows=int(lbp_config["grid_rows"]),
            grid_cols=int(lbp_config["grid_cols"]),
            kernel=str(candidate["kernel"]),
            c=float(candidate["C"]),
            gamma=candidate.get("gamma", "scale"),
            class_weight=_weight_mapping(training.labels),
            seed=int(config["run"].get("random_seed", 20261006)),
        )
        adapter.fit(training.images, training.labels)
        validation_predictions = adapter.predict(validation.images)
        validation_metrics = classification_metrics(validation.labels, validation_predictions.labels)
        candidate_result = {"parameters": candidate, "validation": validation_metrics}
        print(
            f"[lbp_svm] candidate={candidate} "
            f"validation_macro_f1={validation_metrics['macro_f1']:.4f}",
            flush=True,
        )
        candidates.append(candidate_result)
        if validation_metrics["macro_f1"] > best_validation_f1:
            best_validation_f1 = float(validation_metrics["macro_f1"])
            best_adapter = adapter
            best_candidate = dict(candidate)
    if best_adapter is None or best_candidate is None:
        raise RuntimeError("Không có cấu hình LBP-SVM hợp lệ.")

    model_path = run_dir / "models" / "lbp_svm.joblib"
    best_adapter.save(model_path)
    result: dict[str, Any] = {
        "method": "lbp_svm",
        "selection_split": "PublicTest",
        "selected_parameters": best_candidate,
        "best_validation_macro_f1": best_validation_f1,
        "candidates": candidates,
        "model_path": str(model_path),
        "model_sha256": sha256_file(model_path),
        "model_size_bytes": model_path.stat().st_size,
    }
    if evaluate_private:
        test = bundle.splits["PrivateTest"]
        predictions = best_adapter.predict(test.images)
        result["private_test"] = _save_evaluation(
            run_dir=run_dir,
            method="lbp_svm",
            seed=None,
            split=test,
            predictions=predictions,
        )
        latency_config = config["latency"]
        result["latency"] = measure_latency(
            best_adapter.predict,
            test.images,
            warmup_samples=int(latency_config["warmup_samples"]),
            repeats=int(latency_config["repeats"]),
        )
    write_json(run_dir / "training" / "lbp_svm.json", result)
    return result


def _run_deepface_emotion(
    config: dict[str, Any],
    bundle: Any,
    run_dir: Path,
    evaluate_private: bool,
) -> dict[str, Any]:
    deepface_config = config["deepface_emotion"]
    adapter = DeepFaceEmotionAdapter(batch_size=int(deepface_config["batch_size"]))
    weights_path = Path(str(deepface_config["weights_path"])).expanduser()
    if not weights_path.is_absolute():
        weights_path = run_dir.parent.parent / weights_path
    if not weights_path.exists():
        raise FileNotFoundError(f"Không tìm thấy trọng số DeepFace Emotion: {weights_path}")

    split_name = "PrivateTest" if evaluate_private else "PublicTest"
    split = bundle.splits[split_name]
    predictions = adapter.predict(split.images)
    metrics = _save_evaluation(
        run_dir=run_dir,
        method="deepface_emotion",
        seed=None,
        split=split,
        predictions=predictions,
    )
    result: dict[str, Any] = {
        "method": "deepface_emotion",
        "seed": None,
        "pretrained": True,
        "training_samples": 0,
        "evaluation_split": split_name,
        "deepface_version": adapter.package_version,
        "model_path": str(weights_path),
        "model_sha256": sha256_file(weights_path),
        "model_size_bytes": weights_path.stat().st_size,
    }
    result["private_test" if evaluate_private else "validation"] = metrics
    latency_config = config["latency"]
    result["latency"] = measure_latency(
        adapter.predict,
        split.images,
        warmup_samples=int(latency_config["warmup_samples"]),
        repeats=int(latency_config["repeats"]),
    )
    write_json(run_dir / "training" / "deepface_emotion.json", result)
    return result


def _run_deepface_emotion_finetuned(
    config: dict[str, Any],
    bundle: Any,
    run_dir: Path,
    evaluate_private: bool,
) -> dict[str, Any]:
    finetune_config = config["deepface_emotion_finetuned"]
    weights_path = Path(str(finetune_config["weights_path"])).expanduser()
    if not weights_path.is_absolute():
        weights_path = run_dir.parent.parent / weights_path
    weights_path = weights_path.resolve()
    if not weights_path.exists():
        raise FileNotFoundError(f"Không tìm thấy trọng số Emotion đã tinh chỉnh: {weights_path}")

    manifest_path = Path(str(finetune_config["training_manifest_path"])).expanduser()
    if not manifest_path.is_absolute():
        manifest_path = run_dir.parent.parent / manifest_path
    manifest_path = manifest_path.resolve()
    if not manifest_path.exists():
        raise FileNotFoundError(f"Không tìm thấy bản kê khai huấn luyện: {manifest_path}")
    training_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    actual_weights_hash = sha256_file(weights_path)
    if training_manifest.get("model_sha256") != actual_weights_hash:
        raise ValueError("SHA-256 của checkpoint không khớp bản kê khai huấn luyện.")
    if training_manifest.get("dataset_sha256") != bundle.manifest["source_sha256"]:
        raise ValueError("Checkpoint không được huấn luyện từ đúng tệp FER-2013 đang đánh giá.")
    if tuple(training_manifest.get("labels", [])) != LABELS:
        raise ValueError("Thứ tự nhãn của checkpoint không khớp benchmark.")
    if training_manifest.get("selection_split") != "PublicTest":
        raise ValueError("Checkpoint phải được lựa chọn bằng PublicTest.")
    if training_manifest.get("private_test_used") is not False:
        raise ValueError("Bản kê khai phải xác nhận PrivateTest không được dùng khi huấn luyện.")

    adapter = DeepFaceEmotionAdapter(
        batch_size=int(finetune_config["batch_size"]),
        weights_path=weights_path,
    )
    seed = int(training_manifest["seed"])
    split_name = "PrivateTest" if evaluate_private else "PublicTest"
    split = bundle.splits[split_name]
    predictions = adapter.predict(split.images)
    metrics = _save_evaluation(
        run_dir=run_dir,
        method="deepface_emotion_finetuned",
        seed=seed,
        split=split,
        predictions=predictions,
    )
    result: dict[str, Any] = {
        "method": "deepface_emotion_finetuned",
        "seed": seed,
        "pretrained": True,
        "fine_tuned": True,
        "evaluation_split": split_name,
        "deepface_version": adapter.package_version,
        "model_path": str(weights_path),
        "model_sha256": actual_weights_hash,
        "model_size_bytes": weights_path.stat().st_size,
        "training_manifest_path": str(manifest_path),
        "training_manifest": training_manifest,
    }
    result["private_test" if evaluate_private else "validation"] = metrics
    latency_config = config["latency"]
    result["latency"] = measure_latency(
        adapter.predict,
        split.images,
        warmup_samples=int(latency_config["warmup_samples"]),
        repeats=int(latency_config["repeats"]),
    )
    write_json(run_dir / "training" / "deepface_emotion_finetuned.json", result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Chạy benchmark phân loại biểu cảm FER-2013.")
    parser.add_argument("--config", type=Path, default=Path("configs/benchmark.yaml"))
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--methods",
        nargs="+",
        choices=("lbp_svm", "deepface_emotion", "deepface_emotion_finetuned"),
        default=("lbp_svm", "deepface_emotion"),
    )
    parser.add_argument("--limit-per-split", type=int)
    args = parser.parse_args()

    project_root = args.config.resolve().parent.parent
    config = load_config(args.config)
    smoke_test = bool(config["run"].get("smoke_test", False))
    if args.limit_per_split is not None and not smoke_test:
        raise ValueError("--limit-per-split chỉ được phép khi run.smoke_test=true.")
    evaluate_private = bool(config["run"].get("final_evaluation", False))
    if evaluate_private:
        ensure_private_test_allowed(config)

    result_root = resolve_path(project_root, config["paths"]["results_root"])
    run_dir = result_root / args.run_id
    if run_dir.exists():
        raise FileExistsError(f"Run ID đã tồn tại, không ghi đè: {run_dir}")
    run_dir.mkdir(parents=True)
    shutil.copy2(args.config, run_dir / "resolved_config.yaml")
    write_json(run_dir / "environment.json", collect_environment())

    dataset_config = config["dataset"]
    limits = None
    if args.limit_per_split is not None:
        limits = {split: args.limit_per_split for split in ("Training", "PublicTest", "PrivateTest")}
    csv_path = resolve_path(project_root, config["paths"]["fer2013_csv"])
    bundle = load_fer2013(
        csv_path,
        strict_counts=bool(dataset_config["strict_counts"]) and limits is None,
        expected_counts={key: int(value) for key, value in dataset_config["expected_counts"].items()},
        fail_on_cross_split_duplicates=bool(dataset_config["fail_on_cross_split_duplicates"]),
        training_fraction=float(dataset_config.get("training_fraction", 1.0)),
        sampling_seed=int(dataset_config.get("sampling_seed", 0)),
        limits=limits,
    )
    bundle.manifest["smoke_test"] = smoke_test
    write_json(run_dir / "dataset_manifest.json", bundle.manifest)

    outputs: dict[str, Any] = {}
    if "lbp_svm" in args.methods:
        outputs["lbp_svm"] = _run_lbp(config, bundle, run_dir, evaluate_private)
    if "deepface_emotion" in args.methods:
        outputs["deepface_emotion"] = _run_deepface_emotion(
            config, bundle, run_dir, evaluate_private
        )
    if "deepface_emotion_finetuned" in args.methods:
        outputs["deepface_emotion_finetuned"] = _run_deepface_emotion_finetuned(
            config,
            bundle,
            run_dir,
            evaluate_private,
        )
    write_json(
        run_dir / "run_manifest.json",
        {
            "run_id": args.run_id,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "smoke_test": smoke_test,
            "final_evaluation": evaluate_private,
            "methods": list(args.methods),
            "labels": list(LABELS),
            "dataset_sha256": bundle.manifest["source_sha256"],
            "outputs": outputs,
        },
    )
    print(f"Đã hoàn tất lần chạy: {run_dir}")


if __name__ == "__main__":
    main()
