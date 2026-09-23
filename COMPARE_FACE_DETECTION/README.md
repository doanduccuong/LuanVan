# Face Detection Benchmark

Benchmark Haar Cascade, MTCNN và RetinaFace-MobileNet0.25 trên WIDER FACE validation. Giao thức đầy đủ nằm tại [`TECH_SPEC.md`](TECH_SPEC.md).

## Nguyên tắc

- Không viết kết luận trước khi chạy đủ dữ liệu.
- Không sửa thủ công `comparison.csv` hoặc `comparison.md`.
- Smoke test có `--limit` không được dùng làm kết quả luận văn.
- Kết quả chính thức chỉ chạy trên CPU và ba lượt theo `configs/benchmark.yaml`.

## Quy trình chạy

```bash
uv venv --python "$HOME/.pyenv/versions/3.11.7/bin/python" .venv
uv sync --python .venv/bin/python
.venv/bin/python -m pytest
.venv/bin/python -m face_benchmark.validate_dataset
.venv/bin/python -m face_benchmark.run_benchmark
.venv/bin/python -m face_benchmark.build_report results/<run_id>
```

Các lệnh tải dữ liệu và trọng số sẽ được bổ sung sau khi xác minh URL nguồn và checksum.
