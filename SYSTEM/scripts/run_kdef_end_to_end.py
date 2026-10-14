from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path


SYSTEM_ROOT = Path(__file__).resolve().parents[1]
VISION_ROOT = SYSTEM_ROOT / "services" / "vision"
API_ROOT = SYSTEM_ROOT / "apps" / "api"
WEB_ROOT = SYSTEM_ROOT / "apps" / "web"
ARTIFACT_ROOT = SYSTEM_ROOT / "artifacts"


def run(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> None:
    print(f"\n>>> {' '.join(command)}", flush=True)
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    subprocess.run(command, cwd=cwd, env=merged_env, check=True)


def backup_database(run_root: Path) -> None:
    backup_path = run_root / "backup" / "before-rerun.dump"
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"\n>>> Sao lưu cơ sở dữ liệu vào {backup_path}", flush=True)
    with backup_path.open("wb") as output:
        subprocess.run(
            [
                "docker",
                "compose",
                "exec",
                "-T",
                "postgres",
                "pg_dump",
                "-U",
                "touchpoint",
                "-d",
                "touchpoint",
                "-Fc",
            ],
            cwd=SYSTEM_ROOT,
            stdout=output,
            check=True,
        )


def preserve_inputs(dataset_root: Path, run_root: Path) -> None:
    input_root = run_root / "input"
    input_root.mkdir(parents=True, exist_ok=True)
    for name in ("kdef_demo_manifest.json", "events.csv", "image_manifest.csv"):
        source = dataset_root / name
        if source.exists():
            shutil.copy2(source, input_root / name)
    shutil.copy2(ARTIFACT_ROOT / "face-threshold.json", run_root / "face-threshold.json")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Chạy một mạch thực nghiệm KDEF từ khởi động hệ thống đến bằng chứng cuối."
    )
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--emotion-weights", type=Path, required=True)
    parser.add_argument("--capture-all", action="store_true")
    parser.add_argument("--resume-evidence", action="store_true", help="Tiếp tục xuất bằng chứng của lần chạy đã hoàn thành xử lý ảnh và kiểm tra dữ liệu.")
    parser.add_argument(
        "--update-report",
        action="store_true",
        help="Sao chép biểu đồ và ảnh chụp của lần chạy vào luận văn.",
    )
    parser.add_argument(
        "--evaluation-mode",
        action="store_true",
        help="Cho phép sai số định danh để đo tỷ lệ thay vì coi đó là lỗi hạ tầng.",
    )
    args = parser.parse_args()

    dataset_root = args.dataset_root.expanduser().resolve()
    emotion_weights = args.emotion_weights.expanduser().resolve()
    if not emotion_weights.is_file():
        raise SystemExit(f"Không tìm thấy trọng số biểu cảm: {emotion_weights}")
    weight_digest = hashlib.sha256(emotion_weights.read_bytes()).hexdigest()
    manifest_path = dataset_root / "kdef_demo_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("experiment_run_id") != args.run_id:
        raise SystemExit("Run ID trong manifest không khớp tham số --run-id")
    if manifest.get("camera_image_protocol") != (
        "byte-identical-source-no-resize-no-canvas-no-brightness-change"
    ):
        raise SystemExit("Bộ dữ liệu không dùng giao thức ảnh frontal-native nguyên bản")

    threshold = json.loads(
        (ARTIFACT_ROOT / "face-threshold.json").read_text(encoding="utf-8")
    )
    if threshold.get("target_false_positive_rate") != 0.1:
        raise SystemExit("Ngưỡng hiện tại không được hiệu chỉnh với FPR mục tiêu 10%")

    run_root = ARTIFACT_ROOT / "experiment-runs" / args.run_id
    run_root.mkdir(parents=True, exist_ok=True)
    dataset_env = {"DEMO_DATASET_ROOT": str(dataset_root)}
    if args.resume_evidence:
        for relative_path in ("kdef_metrics.json", "sequence-analysis/run.json", "journey-scoring/run.json", "face-threshold.json", "input/kdef_demo_manifest.json"):
            if not (run_root / relative_path).is_file():
                raise SystemExit(f"Chưa có kết quả để tiếp tục: {relative_path}")
        if json.loads((run_root / "input/kdef_demo_manifest.json").read_text()) != manifest:
            raise SystemExit("Dữ liệu đầu vào không khớp bản đã lưu của lần chạy")
        threshold = json.loads((run_root / "face-threshold.json").read_text())
        collect_evidence(args, run_root, manifest, threshold, weight_digest)
        return
    preserve_inputs(dataset_root, run_root)

    compose_env = {
        "EMOTION_WEIGHTS_HOST_PATH": str(emotion_weights),
        "EMOTION_WEIGHTS_SHA256": weight_digest,
        "DEMO_DATASET_ROOT": str(dataset_root),
    }
    run(
        ["docker", "compose", "up", "-d", "--build", "--wait", "--force-recreate"],
        cwd=SYSTEM_ROOT,
        env=compose_env,
    )
    backup_database(run_root)
    run(
        [
            "uv",
            "run",
            "python",
            "../../scripts/reset_demo_data.py",
            "--confirm",
            "RESET-DEMO",
        ],
        cwd=API_ROOT,
        env={
            "DATABASE_URL": (
                "postgresql+psycopg://touchpoint:touchpoint@127.0.0.1:5432/touchpoint"
            )
        },
    )
    run(["uv", "run", "python", "../../scripts/seed_demo_crm.py"], cwd=VISION_ROOT, env=dataset_env)
    run(["uv", "run", "python", "../../scripts/configure_journey_scoring.py"], cwd=VISION_ROOT, env=dataset_env)
    run(["uv", "run", "python", "../../scripts/enroll_demo_faces.py"], cwd=VISION_ROOT, env=dataset_env)
    run(
        [
            "uv",
            "run",
            "python",
            "../../scripts/replay_demo_journeys.py",
            "--scenario",
            "all",
            "--speed",
            "0",
            "--minimum-pass-rate",
            "0",
        ],
        cwd=VISION_ROOT,
        env=dataset_env,
    )
    run(
        [
            "uv",
            "run",
            "python",
            "../../scripts/run_journey_scoring.py",
            "--source-type", "CAMERA", "--source-run-id", args.run_id,
        ], cwd=VISION_ROOT, env=dataset_env,
    )
    run(
        [
            "uv",
            "run",
            "python",
            "../../scripts/run_sequence_analysis.py",
            "--source-type",
            "CAMERA",
            "--source-run-id",
            args.run_id,
        ],
        cwd=VISION_ROOT,
        env=dataset_env,
    )
    verification_command = ["uv", "run", "python", "../../scripts/verify_demo_results.py"]
    if args.evaluation_mode:
        verification_command.append("--evaluation-mode")
    run(verification_command, cwd=VISION_ROOT, env=dataset_env)
    run(["uv", "run", "python", "../../scripts/audit_camera_dataset.py"], cwd=VISION_ROOT, env=dataset_env)
    run(["uv", "run", "python", "../../scripts/audit_live_run.py"], cwd=VISION_ROOT, env=dataset_env)
    collect_evidence(args, run_root, manifest, threshold, weight_digest)


def collect_evidence(args, run_root: Path, manifest: dict, threshold: dict, weight_digest: str) -> None:
    metrics = json.loads((run_root / "kdef_metrics.json").read_text(encoding="utf-8"))
    sequence = json.loads(
        (run_root / "sequence-analysis" / "run.json").read_text(encoding="utf-8")
    )["result"]
    evidence_env = {
        "SOURCE_RUN_ID": args.run_id,
        "SOURCE_TYPE": "CAMERA",
        "EXPECTED_OBSERVATIONS": str(
            metrics["identity"]["correct_match_count"]
            + metrics["identity"]["false_match_count"]
        ),
        "EXPECTED_CUSTOMERS": str(manifest["customer_count"]),
        "EXPECTED_USED_VISITS": str(sequence["used_visit_count"]),
        "EXPECTED_K": str(sequence["selected_k"]),
        "UPDATE_REPORT": "true" if args.update_report else "false",
        "UPDATE_CHAPTER4": "true" if args.capture_all else "false",
    }
    run(["uv", "run", "python", "../../scripts/render_kdef_metrics.py"], cwd=VISION_ROOT, env=evidence_env)
    run(["node", "scripts/capture_kdef_live_demo.mjs"], cwd=SYSTEM_ROOT, env=evidence_env)
    run(["node", "scripts/capture_sequence_analysis.mjs"], cwd=SYSTEM_ROOT, env=evidence_env)
    run(["node", "scripts/capture_journey_scoring.mjs"], cwd=SYSTEM_ROOT, env=evidence_env)
    run(["uv", "run", "python", "../../scripts/render_journey_scores.py"], cwd=VISION_ROOT, env=evidence_env)
    run(["node", "scripts/capture_system_status.mjs"], cwd=SYSTEM_ROOT, env=evidence_env)
    if args.capture_all:
        run(["node", "scripts/capture_chapter4.mjs"], cwd=SYSTEM_ROOT, env=evidence_env)
        run(["node", "../../scripts/capture_chapter5.mjs"], cwd=WEB_ROOT, env=evidence_env)

    summary = {
        "run_id": args.run_id,
        "threshold": threshold["threshold"],
        "target_false_positive_rate": threshold["target_false_positive_rate"],
        "emotion_weights_sha256": weight_digest,
        "capture_event_count": metrics["capture_event_count"],
        "correct_match_count": metrics["identity"]["correct_match_count"],
        "expression_accuracy": metrics["expression"]["accuracy"],
        "expression_macro_f1": metrics["expression"]["macro_f1_present_classes"],
        "complete_journeys": metrics["journeys"]["complete"],
        "selected_k": sequence["selected_k"],
        "average_silhouette_width": sequence["average_silhouette_width"],
        "scoring_summary": json.loads((run_root / "journey-scoring/run.json").read_text())["result"]["scoring_summary"],
        "scoring_config": json.loads((run_root / "journey-scoring/run.json").read_text())["result"]["scoring_config"],
    }
    (run_root / "end_to_end_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("\n=== HOÀN TẤT THỰC NGHIỆM ĐẦU CUỐI ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
