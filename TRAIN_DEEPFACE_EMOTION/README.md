# Fine-tune DeepFace Emotion trên FER-2013

Thư mục này chỉ thực hiện huấn luyện/tinh chỉnh. Nó đọc `Training`, dùng
`PublicTest` để chọn checkpoint theo Macro-F1 và không cung cấp `PrivateTest` cho
mã huấn luyện. Checkpoint sinh ra được chuyển sang dự án
`COMPARE_FACIAL_EXPRESSION` để đánh giá cuối và so sánh với LBP + SVM.

## Dữ liệu vào

Cấu hình mặc định đọc tệp:

```text
../COMPARE_FACIAL_EXPRESSION/data/fer2013.csv
```

Tệp gốc không bị thay đổi hoặc sao chép. Bản kê khai lưu SHA-256, số ảnh mỗi tập,
phân bố lớp và số ảnh trùng hoàn toàn giữa các phần chia.

## Chuẩn bị môi trường

```bash
cd "/Users/sotatek/Desktop/Do An/TRAIN_DEEPFACE_EMOTION"

uv venv --python "$HOME/.pyenv/versions/3.11.7/bin/python" .venv
uv sync --python .venv/bin/python
```

## Kiểm tra trước khi chạy

```bash
.venv/bin/python -m pytest

.venv/bin/python -m emotion_finetuning.validate_dataset \
  --config configs/train.yaml
```

## Chạy tinh chỉnh

```bash
mkdir -p logs
run_id="fer2013-emotion-finetune-001"

nohup caffeinate -i .venv/bin/python -u \
  -m emotion_finetuning.train \
  --config configs/train.yaml \
  --run-id "$run_id" \
  > "logs/$run_id.log" 2>&1 &

echo $! > "logs/$run_id.pid"
tail -f "logs/$run_id.log"
```

Checkpoint tốt nhất được chọn theo Macro-F1 trên `PublicTest`. Epoch 0 là trọng
số Emotion ban đầu; nếu mọi epoch tinh chỉnh đều kém hơn ít nhất `min_delta`, hệ
thống giữ lại checkpoint ban đầu thay vì bắt buộc nhận một mô hình kém hơn.

Đầu ra chính:

```text
artifacts/fer2013-emotion-finetune-001/
├── models/deepface_emotion_finetuned.weights.h5
├── training_manifest.json
├── validation_metrics.json
├── validation_predictions.jsonl
├── dataset_manifest.json
└── resolved_config.yaml
```

`training_manifest.json` xác nhận `private_test_used=false` và chứa hàm băm của
checkpoint. Benchmark từ chối mô hình nếu checkpoint, tập FER-2013, thứ tự nhãn
hoặc giao thức lựa chọn không khớp bản kê khai.
