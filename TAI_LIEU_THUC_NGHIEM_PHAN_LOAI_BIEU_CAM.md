# Tài liệu thực nghiệm so sánh phương pháp phân loại biểu cảm

## 1. Mục đích và phạm vi

Thực nghiệm này so sánh LBP--SVM với mô hình CNN Emotion được tích hợp qua DeepFace, gồm trạng thái trước và sau khi tinh chỉnh trên FER-2013.

Thực nghiệm cần trả lời ba câu hỏi:

1. LBP--SVM và CNN Emotion khác nhau thế nào về khả năng phân loại bảy biểu cảm trên cùng tập kiểm tra?
2. Tinh chỉnh CNN Emotion trên FER-2013 có cải thiện mức độ đồng đều giữa các lớp hay không?
3. Chất lượng tăng thêm, nếu có, phải đánh đổi bao nhiêu độ trễ và dung lượng mô hình?

Đầu vào là ảnh khuôn mặt đã được cắt sẵn. Phép đo không bao gồm phát hiện khuôn mặt, tạo véc-tơ ArcFace, đối sánh danh tính, truyền dữ liệu hoặc ghi cơ sở dữ liệu. Vì vậy, độ trễ trong tài liệu này không phải độ trễ đầu cuối của hệ thống.

## 2. Đối tượng được so sánh

| Mã trong chương trình | Phương pháp | Cách tạo mô hình |
|---|---|---|
| `lbp_svm` | Histogram LBP theo vùng + SVM | Huấn luyện trên `Training`; chọn cấu hình SVM bằng `PublicTest` |
| `deepface_emotion` | CNN Emotion bảy đầu ra được nạp qua DeepFace | Dùng trực tiếp trọng số có sẵn, không tinh chỉnh trong benchmark |
| `deepface_emotion_finetuned` | Cùng CNN Emotion sau tinh chỉnh | Khởi tạo từ trọng số trên, tinh chỉnh bằng `Training`, chọn checkpoint bằng `PublicTest` |

DeepFace là thư viện dùng để nạp và thực thi mô hình. Đối tượng được đo là **mô hình CNN Emotion**, không phải toàn bộ thư viện DeepFace.

Phép so sánh gồm hai bước:

- **Bước A:** LBP--SVM so với CNN Emotion trước tinh chỉnh.
- **Bước B:** LBP--SVM so với CNN Emotion sau tinh chỉnh; đồng thời đối chiếu CNN trước và sau tinh chỉnh để xác định tác động của việc tinh chỉnh.

## 3. Tập dữ liệu thực nghiệm

Sử dụng **FER-2013** tại:

```text
COMPARE_FACIAL_EXPRESSION/data/fer2013.csv
```

Tệp phải có ba cột `emotion`, `pixels`, `Usage`. Dữ liệu gồm ảnh khuôn mặt xám `48 x 48` pixel với bảy lớp: Angry, Disgust, Fear, Happy, Sad, Surprise và Neutral.

Giữ nguyên cách chia công bố:

| Phần dữ liệu | Số ảnh | Mục đích |
|---|---:|---|
| `Training` | 28.709 | Huấn luyện LBP--SVM và tinh chỉnh CNN |
| `PublicTest` | 3.589 | Chọn kernel/siêu tham số SVM, epoch và checkpoint CNN; không dùng để báo cáo kết quả cuối |
| `PrivateTest` | 3.589 | Đánh giá cuối sau khi đã khóa cấu hình |
| **Tổng** | **35.887** |  |

### Lý do chọn FER-2013

- Dữ liệu có đúng bảy lớp mà thành phần Emotion của hệ thống xuất ra.
- Ảnh đã cắt sẵn và có kích thước đầu vào `48 x 48`, cho phép cô lập chất lượng của bộ phân loại khỏi sai số phát hiện khuôn mặt.
- Cách chia `Training`/`PublicTest`/`PrivateTest` hỗ trợ tách huấn luyện, chọn cấu hình và đánh giá cuối, hạn chế rò rỉ dữ liệu.
- Đây là bộ dữ liệu chuẩn, giúp kết quả có thể đối chiếu và chạy lại.

### Phạm vi diễn giải dữ liệu

FER-2013 là ảnh độ phân giải thấp đã cắt sẵn, không đại diện đầy đủ cho ảnh camera cửa hàng. Kết quả chỉ chứng minh khả năng phân loại bảy nhãn trên FER-2013, không chứng minh mức độ hài lòng hay trạng thái tâm lý của khách hàng.

Bản kê khai hiện tại phát hiện ảnh trùng hoàn toàn giữa các phần chia công bố. Lần chạy chính giữ nguyên cách chia để có thể đối chiếu, nhưng phải ghi số ảnh trùng và nên có thêm một lượt đánh giá độ nhạy loại các ảnh `PrivateTest` trùng với dữ liệu huấn luyện.

## 4. Tham số phải khóa trước khi chạy cuối

### 4.1. LBP--SVM

- LBP: `points=8`, `radius=1`, lưới không gian `6 x 6`.
- Ứng viên SVM: linear với `C=1.0`; RBF với `C=10.0`, `gamma=scale`.
- Chọn ứng viên bằng Macro-F1 trên `PublicTest`, sau đó không thay đổi khi chạy `PrivateTest`.

### 4.2. CNN Emotion trước tinh chỉnh

- Trọng số: `~/.deepface/weights/facial_expression_model_weights.h5`.
- Batch dùng cho dự đoán chất lượng: `128`.

### 4.3. CNN Emotion sau tinh chỉnh

- Seed: `20261007`.
- Batch size: `128`; tối đa `20` epoch; Adam với learning rate `1e-5`.
- Dùng class weights; patience `4`; `min_delta=0.001`.
- Tăng cường dữ liệu: lật ngang, xoay `0.04`, tịnh tiến `0.05`, thay đổi tương phản `0.10`.
- Chọn checkpoint theo Macro-F1 trên `PublicTest`.
- `PrivateTest` không được dùng để cập nhật trọng số, chọn epoch hoặc điều chỉnh siêu tham số.

## 5. Giao thức chạy

- Mọi phương pháp dùng cùng tệp FER-2013 và giữ nguyên trường `Usage`.
- LBP--SVM được huấn luyện bằng `Training`; CNN có sẵn chỉ suy luận; CNN tinh chỉnh chỉ dùng `Training` để cập nhật trọng số.
- `PublicTest` chỉ dùng để chọn cấu hình hoặc checkpoint.
- Chỉ chạy `PrivateTest` sau khi cấu hình đã khóa và `run.final_evaluation=true`.
- Trước khi đo độ trễ, mỗi phương pháp warm-up `20` ảnh.
- Độ trễ được đo với từng ảnh riêng lẻ (`batch=1` trong vòng timing), chạy `3` lượt trên toàn bộ `PrivateTest`.
- Các phương pháp phải chạy trên cùng máy và cùng môi trường phần mềm.
- Lưu cấu hình, SHA-256 của dữ liệu và mô hình, môi trường, dự đoán từng ảnh, đủ bảy điểm đầu ra và chỉ số tổng hợp.
- Không dùng smoke test hoặc tập con làm kết quả báo cáo chính thức.

## 6. Chỉ số chất lượng cần đo

Với mỗi lớp, xem lớp đang xét là dương tính và sáu lớp còn lại là âm tính để tính Precision, Recall và F1. Macro-F1 là trung bình F1 của bảy lớp; Balanced Accuracy là trung bình Recall của bảy lớp.

| Chỉ số | Ý nghĩa | Lý do chọn | Chiều tốt hơn |
|---|---|---|---|
| **Accuracy** | Tỷ lệ tổng số ảnh được dự đoán đúng | Cho biết tỷ lệ đúng chung, dễ hiểu và phù hợp để mô tả hiệu quả tổng thể | Cao hơn |
| **Precision từng lớp** | Trong các ảnh được gán vào một lớp, tỷ lệ thực sự thuộc lớp đó | Chỉ ra mô hình có hay gán nhầm các biểu cảm khác vào lớp đang xét hay không | Cao hơn |
| **Recall từng lớp** | Trong các ảnh thật của một lớp, tỷ lệ được nhận ra đúng | Cho biết lớp nào thường bị bỏ sót | Cao hơn |
| **F1 từng lớp** | Cân bằng giữa Precision và Recall của từng lớp | Tránh đánh giá một lớp chỉ theo một loại sai sót | Cao hơn |
| **Macro-F1** | Trung bình cộng F1 của bảy lớp, mỗi lớp có trọng số như nhau | FER-2013 mất cân bằng mạnh; chỉ số này không để lớp nhiều ảnh lấn át lớp ít ảnh và được chọn làm tiêu chí chính | Cao hơn |
| **Balanced Accuracy** | Trung bình Recall của bảy lớp | Đo khả năng bao phủ đồng đều giữa các lớp, bổ sung cho Accuracy | Cao hơn |
| **Confusion Matrix tuyệt đối** | Số lượng mẫu theo cặp nhãn thật--nhãn dự đoán | Cho biết số sai cụ thể và quy mô hỗ trợ của từng lớp | Đọc theo từng ô |
| **Normalized Confusion Matrix** | Tỷ lệ dự đoán trong từng hàng nhãn thật; mỗi hàng có tổng bằng 1 | Cho biết các cặp biểu cảm dễ nhầm mà không bị quy mô lớp chi phối | Đường chéo cao hơn |
| **Tỷ lệ xử lý lỗi** | Tỷ lệ ảnh không tạo được dự đoán hợp lệ | Một mô hình có điểm cao nhưng thường lỗi vẫn không phù hợp để tích hợp | Thấp hơn |

**Macro-F1 là chỉ số lựa chọn chính** vì phân bố lớp không cân bằng, ví dụ lớp Disgust ít ảnh hơn nhiều so với Happy. Accuracy vẫn phải báo cáo vì nó trả lời câu hỏi khác: tổng cộng mô hình dự đoán đúng bao nhiêu ảnh. Accuracy cao hơn không đồng nghĩa mọi lớp đều tốt hơn.

## 7. Chỉ số hiệu năng cần đo

| Chỉ số | Ý nghĩa | Lý do chọn | Chiều tốt hơn |
|---|---|---|---|
| **P50 (ms/ảnh)** | Độ trễ điển hình | Cho biết thời gian xử lý thường gặp | Thấp hơn |
| **P95 (ms/ảnh)** | 95% lượt chạy không vượt quá giá trị này | Phản ánh nhóm lượt chậm và được dùng làm tie-breaker | Thấp hơn |
| **P99 (ms/ảnh)** | 99% lượt chạy không vượt quá giá trị này | Phát hiện đuôi trễ dài và các lần xử lý rất chậm | Thấp hơn |
| **Thông lượng (ảnh/giây)** | Số ảnh xử lý trung bình mỗi giây | Cho biết khả năng xử lý liên tục | Cao hơn |
| **Kích thước mô hình (byte/MiB)** | Dung lượng tệp mô hình hoặc checkpoint | Phản ánh chi phí lưu trữ và triển khai; dùng làm tie-breaker thứ hai | Thấp hơn |

Các giá trị trên chỉ đo bộ phân loại, không bao gồm RetinaFace, ArcFace, truyền dữ liệu, ghi cơ sở dữ liệu hoặc giao diện hệ thống.

## 8. Quy tắc lựa chọn

1. Chọn phương pháp có Macro-F1 cao nhất.
2. Nếu một phương pháp cách Macro-F1 cao nhất **ít hơn `0.01`**, xem các phương pháp đó là gần tương đương về tiêu chí chính.
3. Trong nhóm gần tương đương, ưu tiên P95 thấp hơn.
4. Nếu P95 vẫn không phân biệt rõ, ưu tiên mô hình nhỏ hơn.
5. Dù chọn phương pháp nào, vẫn phải trình bày Accuracy, Balanced Accuracy, kết quả từng lớp và ma trận nhầm lẫn.

## 9. Cách chạy

### 9.1. Kiểm tra dữ liệu và chọn cấu hình

```bash
cd "/Users/sotatek/Desktop/Do An/COMPARE_FACIAL_EXPRESSION"

uv venv --python "$HOME/.pyenv/versions/3.11.7/bin/python" .venv
uv sync --python .venv/bin/python --extra deepface

.venv/bin/python -m pytest
.venv/bin/python -m expression_benchmark.validate_dataset \
  --config configs/benchmark.yaml

run_id="fer2013-selection-002"
.venv/bin/python -m expression_benchmark.run_benchmark \
  --config configs/benchmark.yaml \
  --run-id "$run_id"
```

Lần chạy chọn cấu hình chỉ dùng `Training` và `PublicTest`; `run.final_evaluation` phải là `false`.

### 9.2. Đánh giá LBP--SVM và CNN trước tinh chỉnh

```bash
run_id="fer2013-lbp-vs-deepface-002"
.venv/bin/python -m expression_benchmark.run_benchmark \
  --config configs/benchmark-final.yaml \
  --run-id "$run_id" \
  --methods lbp_svm deepface_emotion

.venv/bin/python -m expression_benchmark.build_report \
  "results/$run_id"
```

### 9.3. Tinh chỉnh CNN Emotion

```bash
cd "/Users/sotatek/Desktop/Do An/TRAIN_DEEPFACE_EMOTION"

uv venv --python "$HOME/.pyenv/versions/3.11.7/bin/python" .venv
uv sync --python .venv/bin/python

.venv/bin/python -m pytest
.venv/bin/python -m emotion_finetuning.validate_dataset \
  --config configs/train.yaml

run_id="fer2013-emotion-finetune-002"
.venv/bin/python -m emotion_finetuning.train \
  --config configs/train.yaml \
  --run-id "$run_id"
```

Sau khi chạy, kiểm tra `training_manifest.json` có `private_test_used=false`, đúng SHA-256 của dữ liệu, checkpoint và đúng thứ tự bảy nhãn. Nếu đổi run ID, cập nhật đồng thời `weights_path` và `training_manifest_path` trong cấu hình benchmark cuối.

### 9.4. Đánh giá LBP--SVM và CNN sau tinh chỉnh

```bash
cd "/Users/sotatek/Desktop/Do An/COMPARE_FACIAL_EXPRESSION"

run_id="fer2013-lbp-vs-finetuned-emotion-002"
.venv/bin/python -m expression_benchmark.run_benchmark \
  --config configs/benchmark-finetuned-final.yaml \
  --run-id "$run_id" \
  --methods lbp_svm deepface_emotion_finetuned

.venv/bin/python -m expression_benchmark.build_report \
  "results/$run_id"
```

Các run ID trong ví dụ phải được đổi thành giá trị duy nhất cho lần chạy mới vì chương trình không ghi đè kết quả cũ.

## 10. Mẫu bảng kết quả

| Phương pháp | Accuracy | Macro-F1 | Balanced Accuracy | P50 (ms) | P95 (ms) | P99 (ms) | Ảnh/giây | Kích thước (MiB) | Tỷ lệ lỗi |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| LBP--SVM |  |  |  |  |  |  |  |  |  |
| CNN Emotion trước tinh chỉnh |  |  |  |  |  |  |  |  |  |
| CNN Emotion sau tinh chỉnh |  |  |  |  |  |  |  |  |  |

| Lớp | Số ảnh | F1 LBP--SVM | F1 CNN trước tinh chỉnh | F1 CNN sau tinh chỉnh |
|---|---:|---:|---:|---:|
| Angry |  |  |  |  |
| Disgust |  |  |  |  |
| Fear |  |  |  |  |
| Happy |  |  |  |  |
| Sad |  |  |  |  |
| Surprise |  |  |  |  |
| Neutral |  |  |  |  |

## 11. Checklist trước khi đưa kết quả vào báo cáo

- [ ] Dữ liệu đủ 28.709 ảnh `Training`, 3.589 ảnh `PublicTest` và 3.589 ảnh `PrivateTest`.
- [ ] Bản kê khai dữ liệu có SHA-256, phân bố lớp và số ảnh trùng giữa các phần chia.
- [ ] Không dùng `PrivateTest` để chọn SVM, epoch, checkpoint hoặc siêu tham số.
- [ ] Không dùng smoke test, tập con hoặc run đang dở làm kết quả chính thức.
- [ ] Ba cấu hình cuối được đánh giá trên cùng `PrivateTest` và cùng máy.
- [ ] Có đủ dự đoán từng ảnh, bảy điểm đầu ra, metric, timing, cấu hình và môi trường.
- [ ] Báo cáo Macro-F1, Accuracy, Balanced Accuracy và F1 từng lớp.
- [ ] Có cả Confusion Matrix tuyệt đối và chuẩn hóa.
- [ ] Bảng tốc độ ghi rõ chỉ đo bộ phân loại với `batch=1` trong vòng timing.
- [ ] Kết luận chỉ áp dụng cho FER-2013; không suy diễn nhãn biểu cảm thành mức độ hài lòng.

## 12. Tệp cấu hình và bằng chứng

- Cấu hình lựa chọn: `COMPARE_FACIAL_EXPRESSION/configs/benchmark.yaml`.
- Cấu hình đánh giá trước tinh chỉnh: `COMPARE_FACIAL_EXPRESSION/configs/benchmark-final.yaml`.
- Cấu hình đánh giá sau tinh chỉnh: `COMPARE_FACIAL_EXPRESSION/configs/benchmark-finetuned-final.yaml`.
- Đặc tả: `COMPARE_FACIAL_EXPRESSION/TECH_SPEC.md`.
- Cấu hình tinh chỉnh: `TRAIN_DEEPFACE_EMOTION/configs/train.yaml`.
- Kết quả benchmark: các thư mục run trong `COMPARE_FACIAL_EXPRESSION/results/`.
- Kết quả huấn luyện: các thư mục run trong `TRAIN_DEEPFACE_EMOTION/artifacts/`.
