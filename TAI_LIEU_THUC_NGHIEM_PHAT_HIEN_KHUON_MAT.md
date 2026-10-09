# Tài liệu thực nghiệm so sánh phương pháp phát hiện khuôn mặt

## 1. Mục đích và phạm vi

Thực nghiệm này so sánh ba phương pháp **phát hiện khuôn mặt**: Haar Cascade, MTCNN và RetinaFace--MobileNet0.25. Đầu vào là ảnh gốc; đầu ra là danh sách khung bao khuôn mặt và điểm tin cậy.

Mục tiêu là trả lời hai câu hỏi:

1. Phương pháp nào phát hiện và định vị khuôn mặt tốt hơn khi điều kiện quan sát chuyển từ dễ sang khó?
2. Phương pháp nào có chi phí suy luận phù hợp hơn với luồng xử lý ảnh của hệ thống trên CPU?

Đây là phép đo **phát hiện**, không phải nhận dạng danh tính. Kết quả không cho biết hai khuôn mặt có thuộc cùng một người hay không, cũng không đo độ chính xác phân loại biểu cảm hoặc độ trễ đầu cuối của hệ thống.

## 2. Đối tượng được so sánh

| Mã trong chương trình | Phương pháp | Cấu hình được khóa |
|---|---|---|
| `haar` | Haar Cascade của OpenCV | `scale_factor=1.1`, `min_neighbors=5`, kích thước mặt tối thiểu `20 x 20` |
| `mtcnn` | MTCNN của `facenet-pytorch` | `min_face_size=20`, ngưỡng ba tầng `[0.6, 0.7, 0.7]`, `factor=0.709` |
| `retinaface_mobilenet025` | RetinaFace với backbone MobileNet0.25 | ngưỡng thu dự đoán `0.02`, ngưỡng vận hành `0.6`, `top_k=5000`, NMS `0.4`, `keep_top_k=750` |

Chỉ so sánh đúng ba cấu hình trên. Việc thêm backbone khác hoặc thay đổi ngưỡng tạo thành một thực nghiệm khác và phải có run ID mới.

## 3. Tập dữ liệu thực nghiệm

Sử dụng **toàn bộ tập xác thực WIDER FACE (WIDER FACE validation)** gồm **3.226 ảnh**, kèm:

- ảnh trong `WIDER_val/images`;
- tệp khung bao chuẩn `wider_face_val_bbx_gt.txt`;
- các tệp đánh giá chính thức `wider_face_val.mat`, `wider_easy_val.mat`, `wider_medium_val.mat` và `wider_hard_val.mat`.

Cấu trúc dữ liệu trong dự án:

```text
COMPARE_FACE_DETECTION/data/wider_face/
├── WIDER_val/
│   └── images/
├── wider_face_split/
│   └── wider_face_val_bbx_gt.txt
└── ground_truth/
    ├── wider_face_val.mat
    ├── wider_easy_val.mat
    ├── wider_medium_val.mat
    └── wider_hard_val.mat
```

### Lý do chọn WIDER FACE validation

- Bài toán cần đo là phát hiện khuôn mặt, nên dữ liệu phải có khung bao chuẩn thay vì chỉ có nhãn danh tính hoặc biểu cảm.
- Dữ liệu có ảnh nhiều người, khuôn mặt nhỏ, che khuất, khác tư thế và điều kiện chiếu sáng; các tình huống này gần với ảnh thu nhận trong cửa hàng hơn ảnh chân dung một người.
- Ba nhóm Easy, Medium và Hard cho phép quan sát mức suy giảm của mô hình khi điều kiện khó hơn.
- Nhãn của tập validation được công khai, nên có thể tính chỉ số cục bộ và chạy lại. Không dùng WIDER FACE test vì nhãn chuẩn của tập này không được công khai.

## 4. Giao thức chạy

- Thiết bị chính: CPU.
- Số luồng PyTorch: `1`; số luồng OpenCV: `1`.
- Mỗi mô hình nhận cùng ảnh gốc, cùng danh sách ảnh và cùng thứ tự ảnh; không resize chung trước khi đưa vào mô hình.
- Warm-up `20` ảnh cho từng mô hình và không ghi các lượt này vào kết quả.
- Chạy `3` lượt trên toàn bộ 3.226 ảnh; thứ tự mô hình được xoay vòng giữa các lượt.
- Độ trễ bao gồm tiền xử lý, suy luận, hậu xử lý/NMS và chuyển kết quả về định dạng chung; không gồm đọc ảnh, đọc nhãn, ghi tệp hoặc tính chỉ số.
- Dùng IoU tối thiểu `0.5` để ghép khung dự đoán với khung chuẩn.
- Một khung dự đoán chỉ được ghép với một khung chuẩn; dự đoán trùng sau lần ghép đầu được tính là false positive.
- AP được tạo từ `1.000` ngưỡng trên đường Precision--Recall.
- Không đặt kết quả CPU và GPU/MPS trong cùng bảng chính.

## 5. Chỉ số chất lượng cần đo

Với khung dự đoán \(B_p\) và khung chuẩn \(B_g\):

\[
IoU(B_p,B_g)=\frac{|B_p\cap B_g|}{|B_p\cup B_g|}.
\]

Tại ngưỡng vận hành:

\[
Precision=\frac{TP}{TP+FP},\quad
Recall=\frac{TP}{TP+FN},\quad
F1=\frac{2\times Precision\times Recall}{Precision+Recall}.
\]

| Chỉ số | Ý nghĩa | Lý do chọn | Chiều tốt hơn |
|---|---|---|---|
| **AP Easy** | Diện tích dưới đường Precision--Recall trên nhóm khuôn mặt dễ | Xác nhận chất lượng trong điều kiện thuận lợi và tạo mốc so sánh cơ bản | Cao hơn |
| **AP Medium** | AP trên nhóm độ khó trung bình | Cho biết mô hình duy trì chất lượng thế nào khi kích thước, tư thế hoặc che khuất phức tạp hơn | Cao hơn |
| **AP Hard** | AP trên nhóm khó | Quan trọng với khuôn mặt nhỏ, che khuất hoặc cảnh đông người; tránh chọn mô hình chỉ tốt với mặt lớn và rõ | Cao hơn |
| **Precision** | Trong các khung được dự đoán là khuôn mặt, tỷ lệ khung đúng | Đo mức phát hiện nhầm nền hoặc vật thể khác thành khuôn mặt | Cao hơn |
| **Recall** | Trong toàn bộ khuôn mặt chuẩn, tỷ lệ được phát hiện | Khuôn mặt bị bỏ sót sẽ không đi tiếp tới phân loại biểu cảm và nhận dạng | Cao hơn |
| **F1** | Trung bình điều hòa của Precision và Recall | Mô tả sự cân bằng giữa phát hiện nhầm và bỏ sót tại ngưỡng vận hành | Cao hơn |
| **False positives/ảnh** | Số khung phát hiện nhầm trung bình trên mỗi ảnh | Hai mô hình có Precision gần nhau vẫn có thể tạo số lượng quan sát giả khác nhau | Thấp hơn |
| **Tỷ lệ ảnh không phát hiện** | Tỷ lệ ảnh có khuôn mặt chuẩn nhưng mô hình không trả về khung nào | Phản ánh trực tiếp tỷ lệ ảnh không tạo được đầu vào cho bước sau | Thấp hơn |

**AP Easy, Medium và Hard là nhóm chỉ số chất lượng chính.** AP tổng hợp hành vi trên toàn dải ngưỡng, phù hợp khi điểm tin cậy của ba mô hình không được hiệu chỉnh trên cùng một thang xác suất.

Precision, Recall và F1 chỉ mô tả hành vi tại các ngưỡng vận hành đã khóa:

- Haar Cascade: không lọc thêm ngoài cấu hình cascade;
- MTCNN: dùng đầu ra sau ngưỡng O-Net `0.7`;
- RetinaFace: giữ dự đoán có confidence từ `0.6`.

## 6. Chỉ số hiệu năng cần đo

| Chỉ số | Ý nghĩa | Lý do chọn | Chiều tốt hơn |
|---|---|---|---|
| **Thời gian nạp mô hình (ms)** | Thời gian khởi tạo và nạp trọng số | Hữu ích khi dịch vụ phải khởi động hoặc tải lại mô hình | Thấp hơn |
| **Độ trễ P50/trung vị (ms/ảnh)** | Một nửa số lượt xử lý không vượt quá giá trị này | Ít bị chi phối bởi một số lượt bất thường, mô tả độ trễ điển hình | Thấp hơn |
| **Độ trễ P95 (ms/ảnh)** | 95% số lượt xử lý không vượt quá giá trị này | Phản ánh nhóm lượt chậm và độ ổn định khi vận hành | Thấp hơn |
| **FPS** | Số ảnh xử lý trung bình mỗi giây, tính từ tổng thời gian detector | Cho biết thông lượng khi xử lý chuỗi ảnh | Cao hơn |
| **Peak RSS (byte/MiB)** | Bộ nhớ thường trú cực đại trong lúc chạy | Kiểm tra khả năng triển khai trên máy có tài nguyên giới hạn | Thấp hơn |

Không cộng AP và FPS thành một “điểm tổng hợp” nếu chưa có cơ sở xác định trọng số. Khi chọn mô hình, trước hết loại phương án bị phương án khác trội hơn đồng thời về chất lượng và độ trễ. Nếu vẫn có đánh đổi, báo cáo riêng mức thay đổi AP, P95 và FPS.

## 7. Cách chạy

```bash
cd "/Users/sotatek/Desktop/Do An/COMPARE_FACE_DETECTION"

uv venv --python "$HOME/.pyenv/versions/3.11.7/bin/python" .venv
uv sync --python .venv/bin/python

.venv/bin/python -m pytest
.venv/bin/python -m face_benchmark.validate_dataset

run_id="wider-val-cpu-20261007-002"
.venv/bin/python -m face_benchmark.run_benchmark \
  --config configs/benchmark.yaml \
  --run-id "$run_id"

.venv/bin/python -m face_benchmark.build_report \
  "results/$run_id"
```

Run ID trong ví dụ phải được đổi thành giá trị duy nhất cho lần chạy mới. Không dùng một lần chạy có tùy chọn `--limit` làm kết quả chính thức.

Đầu ra cần kiểm tra gồm:

- `comparison.csv` và `comparison.md`;
- `metrics.json`;
- `environment.json` và `dataset_manifest.json`;
- dự đoán của từng mô hình;
- các tệp timing của từng lượt chạy.

## 8. Mẫu bảng kết quả

| Mô hình | AP Easy | AP Medium | AP Hard | Precision | Recall | F1 | FP/ảnh | Tỷ lệ ảnh không phát hiện |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Haar Cascade |  |  |  |  |  |  |  |  |
| MTCNN |  |  |  |  |  |  |  |  |
| RetinaFace--MobileNet0.25 |  |  |  |  |  |  |  |  |

| Mô hình | Load (ms) | P50 (ms) | P95 (ms) | FPS | Peak RSS (MiB) |
|---|---:|---:|---:|---:|---:|
| Haar Cascade |  |  |  |  |  |
| MTCNN |  |  |  |  |  |
| RetinaFace--MobileNet0.25 |  |  |  |  |  |

## 9. Checklist trước khi đưa kết quả vào báo cáo

- [ ] Dữ liệu đủ 3.226 ảnh, đúng cấu trúc và có bản kê khai SHA-256.
- [ ] Cả ba mô hình chạy trên cùng danh sách ảnh, cùng máy và cùng chế độ CPU.
- [ ] Cấu hình và ngưỡng đã được khóa trước khi đọc kết quả.
- [ ] Warm-up không xuất hiện trong dữ liệu timing chính.
- [ ] Mỗi ảnh có đủ ba bản ghi thời gian tương ứng ba lượt chạy.
- [ ] Có đủ dự đoán, timing, metric, cấu hình và thông tin môi trường.
- [ ] Báo cáo AP riêng cho Easy, Medium và Hard, không chỉ một giá trị chung.
- [ ] Nhận xét nêu cả chất lượng và chi phí, không gọi mô hình “tốt nhất” chỉ dựa vào một cột.
- [ ] Kết luận chỉ áp dụng cho WIDER FACE validation và môi trường đã đo.

## 10. Tệp cấu hình và bằng chứng

- Cấu hình: `COMPARE_FACE_DETECTION/configs/benchmark.yaml`.
- Đặc tả: `COMPARE_FACE_DETECTION/TECH_SPEC.md`.
- Hướng dẫn chạy: `COMPARE_FACE_DETECTION/README.md`.
- Kết quả: các thư mục run trong `COMPARE_FACE_DETECTION/results/`.
