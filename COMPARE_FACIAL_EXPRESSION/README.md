# Facial Expression Benchmark

Dự án độc lập dùng để so sánh:

1. LBP kết hợp SVM;
2. mô hình CNN Emotion được huấn luyện sẵn và cung cấp qua DeepFace;
3. mô hình CNN Emotion đã được tinh chỉnh trên FER-2013 ở dự án riêng.

DeepFace là thư viện tích hợp mô hình, không phải tên của một kiến trúc CNN. Trong
benchmark này, `deepface_emotion` chỉ mô hình Emotion bảy lớp mà hệ thống thực tế
đang gọi qua DeepFace `0.0.101`.

Mã huấn luyện không nằm trong dự án benchmark. Thư mục
`../TRAIN_DEEPFACE_EMOTION` tạo checkpoint chỉ từ `Training` và `PublicTest`;
benchmark kiểm tra bản kê khai rồi mới cho phép đánh giá checkpoint đó trên
`PrivateTest` bằng phương pháp `deepface_emotion_finetuned`.

## Biên giới của phép đo

- Đầu vào là ảnh khuôn mặt 48 x 48 đã được cắt sẵn trong FER-2013.
- RetinaFace không chạy trong benchmark này.
- `Training` dùng để huấn luyện LBP-SVM; DeepFace Emotion dùng trọng số có sẵn.
- Với mô hình đã tinh chỉnh, benchmark chỉ nạp checkpoint bên ngoài; nó không huấn
  luyện lại và từ chối checkpoint nếu SHA-256, tập dữ liệu hoặc thứ tự nhãn không
  khớp bản kê khai.
- `PublicTest` dùng để chọn cấu hình SVM.
- `PrivateTest` chỉ được dùng khi `run.final_evaluation=true` sau khi cấu hình đã khóa.
- Macro-F1 là chỉ số lựa chọn chính.
- Đây là so sánh một phương pháp truyền thống được huấn luyện trên FER-2013 với mô
  hình học sâu đã huấn luyện sẵn; không phải so sánh hai quy trình huấn luyện đồng nhất.
- Kết quả chỉ chứng minh khả năng phân loại bảy nhãn trên FER-2013; không chứng minh mức độ hài lòng của khách hàng.
- Phân chia công bố của FER-2013 được giữ nguyên để đối chiếu với các nghiên cứu trước. Bản kê khai dữ liệu phải công bố số ảnh trùng hoàn toàn giữa các tập; một lượt đánh giá độ nhạy loại ảnh trùng sẽ được chạy riêng.

## Chuẩn bị môi trường

```bash
cd COMPARE_FACIAL_EXPRESSION
uv venv --python "$HOME/.pyenv/versions/3.11.7/bin/python" .venv
uv sync --python .venv/bin/python --extra deepface
.venv/bin/python -m pytest
```

## Dữ liệu chính thức

Đặt tệp FER-2013 tại `data/fer2013.csv`. Tệp phải có ba cột:

```text
emotion,pixels,Usage
```

Chương trình yêu cầu đúng 28.709 mẫu `Training`, 3.589 mẫu `PublicTest` và 3.589 mẫu `PrivateTest`. Dữ liệu không được đưa vào Git.

Kiểm tra dữ liệu trước khi huấn luyện:

```bash
.venv/bin/python -m expression_benchmark.validate_dataset \
  --config configs/benchmark.yaml
```

## Chạy lựa chọn cấu hình

Giữ `run.final_evaluation: false` trong `configs/benchmark.yaml`:

```bash
.venv/bin/python -m expression_benchmark.run_benchmark \
  --config configs/benchmark.yaml \
  --run-id fer2013-selection-001
```

Lần chạy này chỉ sử dụng `Training` và `PublicTest`.

## Chạy kiểm tra cuối cùng

Sau khi khóa cấu hình, sao chép cấu hình thành một tệp mới, đặt `run.final_evaluation: true` rồi chạy với `run-id` mới. Không ghi đè lần chạy cũ.

```bash
.venv/bin/python -m expression_benchmark.run_benchmark \
  --config configs/benchmark-final.yaml \
  --run-id fer2013-final-001

.venv/bin/python -m expression_benchmark.build_report \
  results/fer2013-final-001
```

## So sánh LBP-SVM với Emotion CNN đã tinh chỉnh

Trước hết hoàn tất lần chạy `fer2013-emotion-finetune-001` trong thư mục
`TRAIN_DEEPFACE_EMOTION`. Sau đó chạy benchmark cuối bằng cấu hình đã trỏ đến
checkpoint và bản kê khai của lần huấn luyện đó:

```bash
.venv/bin/python -m expression_benchmark.run_benchmark \
  --config configs/benchmark-finetuned-final.yaml \
  --run-id fer2013-lbp-vs-finetuned-emotion-001 \
  --methods lbp_svm deepface_emotion_finetuned

.venv/bin/python -m expression_benchmark.build_report \
  results/fer2013-lbp-vs-finetuned-emotion-001
```

Nếu đổi `run-id` của lần huấn luyện, phải sửa đồng thời `weights_path` và
`training_manifest_path` trong `configs/benchmark-finetuned-final.yaml`.

## Smoke test

Smoke test chỉ kiểm tra mã có chạy xuyên suốt hay không. Dữ liệu do lệnh dưới đây tạo ra không phải ảnh biểu cảm thật và kết quả không được đưa vào luận văn.

```bash
.venv/bin/python -m expression_benchmark.make_smoke_dataset \
  data/smoke_fer2013.csv

.venv/bin/python -m expression_benchmark.run_benchmark \
  --config configs/smoke.yaml \
  --run-id smoke-001 \
  --methods lbp_svm
```

Lệnh smoke mặc định chỉ chạy LBP-SVM để không phụ thuộc TensorFlow. Adapter DeepFace
được kiểm thử bằng mô hình thay thế trong unit test. `build_report` chủ động từ chối
sinh bảng luận văn nếu `smoke_test=true`.
