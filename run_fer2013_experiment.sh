#!/usr/bin/env bash
set -euo pipefail

workspace_root="$(cd "$(dirname "$0")" && pwd)"
training_root="$workspace_root/TRAIN_DEEPFACE_EMOTION"
benchmark_root="$workspace_root/COMPARE_FACIAL_EXPRESSION"
training_run_id="fer2013-emotion-finetune-final"
benchmark_run_id="fer2013-expression-comparison-final"

if [[ -e "$training_root/artifacts/$training_run_id" ]]; then
  echo "Đã tồn tại kết quả huấn luyện: $training_root/artifacts/$training_run_id" >&2
  exit 1
fi

if [[ -e "$benchmark_root/results/$benchmark_run_id" ]]; then
  echo "Đã tồn tại kết quả đánh giá: $benchmark_root/results/$benchmark_run_id" >&2
  exit 1
fi

cd "$training_root"
.venv/bin/python -m emotion_finetuning.validate_dataset --config configs/train.yaml
.venv/bin/python -u -m emotion_finetuning.train \
  --config configs/train.yaml \
  --run-id "$training_run_id"

cd "$benchmark_root"
.venv/bin/python -m expression_benchmark.validate_dataset \
  --config configs/benchmark-all-final.yaml
.venv/bin/python -u -m expression_benchmark.run_benchmark \
  --config configs/benchmark-all-final.yaml \
  --run-id "$benchmark_run_id" \
  --methods lbp_svm deepface_emotion deepface_emotion_finetuned
.venv/bin/python -m expression_benchmark.build_report \
  "results/$benchmark_run_id"

echo "Hoàn tất. Kết quả tổng hợp:"
echo "$benchmark_root/results/$benchmark_run_id/tables/comparison.md"
