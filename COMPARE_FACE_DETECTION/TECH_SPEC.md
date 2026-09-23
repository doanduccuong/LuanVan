# Tech Spec – Benchmark các phương pháp phát hiện khuôn mặt

## 1. Trạng thái tài liệu

- **Phiên bản:** 0.2
- **Trạng thái:** Sẵn sàng để rà soát trước khi coding
- **Phạm vi:** Chỉ benchmark bước phát hiện khuôn mặt
- **Không thuộc phạm vi:** Phân loại biểu cảm, DeepFace wrapper, nhận dạng danh tính và phân tích hành trình đa điểm chạm

Mã benchmark chỉ được viết sau khi tài liệu này được chấp thuận. Nếu thay đổi mô hình, trọng số, dữ liệu, metric hoặc giao thức đo sau khi coding, phải tăng phiên bản tech spec và chạy lại các kết quả bị ảnh hưởng.

---

## 2. Mục tiêu

Xây dựng một benchmark có thể tái lập để so sánh ba phương pháp phát hiện khuôn mặt trên cùng dữ liệu và phần cứng:

1. Haar Cascade.
2. MTCNN.
3. RetinaFace.

Benchmark phải trả lời riêng hai câu hỏi:

- Chất lượng phát hiện của từng mô hình trên WIDER FACE validation như thế nào?
- Chi phí suy luận của từng mô hình trên máy triển khai thử nghiệm như thế nào?

Tech spec không giả định trước mô hình nào chính xác hơn, nhanh hơn hoặc phù hợp hơn. Kết luận chỉ được viết sau khi bảng kết quả cuối cùng được sinh từ dữ liệu thô.

---

## 3. Đối tượng được benchmark

### 3.1. Haar Cascade

- **Mô hình:** `haarcascade_frontalface_default.xml`.
- **Nguồn:** OpenCV 4.x.
- **Implementation:** `cv2.CascadeClassifier`.
- **Lý do đưa vào benchmark:** là mô hình công khai có cấu hình xác định, tái lập được và đại diện cho phương pháp Haar Cascade/Viola–Jones.
- **Tham số phải khóa trong file cấu hình:** `scaleFactor`, `minNeighbors`, `minSize`, `maxSize`.

Nguồn: [OpenCV Haar Cascades](https://github.com/opencv/opencv/tree/4.x/data/haarcascades).

### 3.2. MTCNN

- **Mô hình:** MTCNN tiền huấn luyện gồm P-Net, R-Net và O-Net.
- **Implementation:** `facenet-pytorch`.
- **Repository tham chiếu:** commit `787da06156087cd6b616fe6608213722bddc30cd`.
- **Package dự kiến:** `facenet-pytorch==2.6.0`.
- **Lý do đưa vào benchmark:** implementation công khai đồng thời mã, trọng số và giao diện suy luận của cả ba tầng, cho phép tái lập bằng một package cố định.
- **Tham số phải khóa:** `min_face_size=20`, `thresholds=[0.6, 0.7, 0.7]`, `factor=0.709`, `keep_all=True`, `post_process=False`.

Nguồn: [`facenet-pytorch`](https://github.com/timesler/facenet-pytorch).

### 3.3. RetinaFace

- **Mô hình:** RetinaFace-MobileNet0.25.
- **Trọng số:** `mobilenet0.25_Final.pth` tiền huấn luyện trên WIDER FACE training.
- **SHA-256 trọng số:** `2979b33ffafda5d74b6948cd7a5b9a7a62f62b949cef24e95fd15d2883a65220`.
- **Implementation:** `biubug6/Pytorch_Retinaface`.
- **Repository khóa tại commit:** `b984b4b775b2c4dced95c1eadd195a5c7d32a60b`.
- **Lý do đưa vào benchmark:** repository cung cấp mã suy luận, trọng số và luồng đánh giá WIDER FACE cho đúng biến thể, nhờ đó có thể chạy lại thí nghiệm với cấu hình cố định.
- **Tham số phải khóa:** `confidence_threshold=0.02`, `top_k=5000`, `nms_threshold=0.4`, `keep_top_k=750`.

Nguồn: [`Pytorch_Retinaface`](https://github.com/biubug6/Pytorch_Retinaface).

Chỉ benchmark một biến thể RetinaFace. Không thêm ResNet50 vào cùng bảng chính.

---

## 4. Dữ liệu đánh giá

### 4.1. Tập dữ liệu

- **Tên:** WIDER FACE validation.
- **Thành phần:** ảnh validation, file bounding-box ground truth và các file phân nhóm Easy, Medium, Hard của bộ đánh giá chính thức.
- **Đơn vị đánh giá:** bounding box khuôn mặt.
- **Không sử dụng:** WIDER FACE test do ground truth không được công khai để tính metric cục bộ.

Nguồn: [WIDER FACE: A Face Detection Benchmark](https://openaccess.thecvf.com/content_cvpr_2016/html/Yang_WIDER_FACE_A_CVPR_2016_paper.html) và [trang dữ liệu chính thức](https://mmlab.ie.cuhk.edu.hk/projects/WIDERFace/).

### 4.2. Cấu trúc dữ liệu dự kiến

```text
data/
└── wider_face/
    ├── WIDER_val/
    │   └── images/
    └── wider_face_split/
        ├── wider_face_val_bbx_gt.txt
        ├── wider_easy_val.mat
        ├── wider_medium_val.mat
        └── wider_hard_val.mat
```

### 4.3. Kiểm tra dữ liệu trước benchmark

Chương trình `validate_dataset.py` phải kiểm tra:

- Số lượng ảnh đọc được khớp annotation.
- Không có đường dẫn ảnh trùng hoặc thiếu.
- Bounding box có chiều rộng và chiều cao hợp lệ. Các box suy biến có sẵn trong annotation chính thức được ghi thành cảnh báo và loại khỏi metric vận hành tự tính; không chỉnh sửa file nguồn.
- Tọa độ sau khi chuyển đổi không nằm ngoài ảnh.
- Danh sách Easy, Medium và Hard tham chiếu đúng ảnh và chỉ số khuôn mặt.
- SHA-256 của các gói dữ liệu và annotation được ghi vào `dataset_manifest.json`.

Không loại ảnh lỗi âm thầm. Mọi ảnh bị bỏ phải được ghi đường dẫn và lý do vào log; nếu ảnh không đọc được hoặc cấu trúc annotation bị hỏng thì dừng lần chạy chính thức. Bounding box suy biến trong annotation chính thức được lưu trong danh sách cảnh báo và không làm dừng benchmark.

---

## 5. Môi trường thực nghiệm

### 5.1. Phần cứng chính

- **Máy:** Apple M4 Pro, kiến trúc arm64.
- **RAM:** 25.769.803.776 byte, tương đương 24 GiB.
- **Hệ điều hành tại thời điểm lập spec:** macOS 26.5, build 25F71.
- **Thiết bị benchmark chính:** CPU.

CPU được chọn làm chế độ chính vì cả ba implementation đều chạy được trên CPU. Không trộn kết quả CPU và MPS/GPU trong cùng bảng.

Nếu thực hiện thêm benchmark MPS thì phải trình bày thành bảng phụ riêng; Haar Cascade vẫn được ghi là CPU và không dùng bảng phụ đó để kết luận về so sánh thuần phần cứng.

### 5.2. Môi trường phần mềm khóa cho coding

- Python `3.11.7` qua `pyenv`.
- Môi trường ảo đặt tại `.venv`.
- `numpy==1.26.4`.
- `opencv-python==4.10.0.84`.
- `torch==2.2.2`.
- `torchvision==0.17.2`.
- `facenet-pytorch==2.6.0`.
- `Pillow==10.2.0`.
- `scipy==1.12.0`.
- `pandas==2.2.3`.
- `matplotlib==3.9.2`.
- `pytest==8.3.3`.

Sau khi cài đặt thành công phải sinh file lock và `environment.json`. Nếu một phiên bản không cài được trên máy thử nghiệm, phải sửa tech spec trước khi thay phiên bản, không tự động dùng bản mới hơn.

### 5.3. Thiết lập tài nguyên

- Chạy một tiến trình benchmark tại một thời điểm.
- `torch.set_num_threads(1)`.
- `torch.set_num_interop_threads(1)`.
- `cv2.setNumThreads(1)`.
- Không chạy đồng thời ứng dụng tải CPU lớn.
- Ghi nhiệt độ hoặc trạng thái thermal nếu hệ điều hành cung cấp được API ổn định; nếu không, ghi rõ là không thu thập được.

---

## 6. Chuẩn hóa đầu vào và đầu ra

### 6.1. Đầu vào

- Mỗi phương pháp nhận cùng một ảnh gốc và cùng độ phân giải.
- Không resize chung ảnh trước detector.
- Việc chuyển RGB/BGR, chuẩn hóa và image pyramid thuộc adapter của từng mô hình và được tính vào detector latency.
- Thời gian đọc file và giải mã ảnh không tính vào detector latency chính.

### 6.2. Đầu ra chuẩn hóa

Mọi adapter phải trả về danh sách prediction theo schema:

```json
{
  "image_id": "event/image_name",
  "detections": [
    {
      "x1": 0.0,
      "y1": 0.0,
      "x2": 0.0,
      "y2": 0.0,
      "score": 0.0
    }
  ],
  "latency_ms": 0.0
}
```

Quy ước:

- Bounding box dùng định dạng `xyxy`, số thực, gốc tọa độ ở góc trên trái.
- Bounding box được clip vào kích thước ảnh trước khi đánh giá.
- Prediction có diện tích không dương bị loại và được đếm trong log.
- Không áp dụng thêm NMS chung sau adapter; NMS là một phần của từng implementation và phải dùng đúng cấu hình đã khóa.

### 6.3. Điểm tin cậy

- Haar Cascade sử dụng `levelWeights` từ `detectMultiScale3(..., outputRejectLevels=True)` làm score xếp hạng.
- MTCNN sử dụng xác suất trả về bởi `MTCNN.detect()`.
- RetinaFace sử dụng confidence của nhánh phân loại khuôn mặt.

Score của ba mô hình không được hiểu là đã hiệu chỉnh trên cùng thang xác suất. Score chỉ dùng để xếp hạng prediction bên trong từng mô hình khi tạo đường Precision–Recall và tính AP.

---

## 7. Chỉ số đánh giá chất lượng

### 7.1. Metric chính

- AP trên nhóm Easy.
- AP trên nhóm Medium.
- AP trên nhóm Hard.

Việc ghép prediction với ground truth sử dụng IoU tối thiểu `0.5` và mỗi ground-truth box chỉ được ghép với một prediction. Cách xử lý ignore/difficulty phải bám theo annotation và giao thức WIDER FACE.

### 7.2. Metric phụ

- Precision tại ngưỡng vận hành đã khóa.
- Recall tại ngưỡng vận hành đã khóa.
- F1 tại ngưỡng vận hành đã khóa.
- Tỷ lệ ảnh không phát hiện được khuôn mặt nào.
- Số false positive trung bình trên mỗi ảnh.

Ngưỡng vận hành:

- Haar Cascade: không lọc thêm ngoài cấu hình cascade đã khóa.
- MTCNN: giữ prediction sau ngưỡng O-Net `0.7` của cấu hình MTCNN.
- RetinaFace: giữ prediction có confidence từ `0.6` cho metric tại điểm vận hành; ngưỡng `0.02` chỉ dùng để tạo đường Precision–Recall/AP.

AP là metric chất lượng chính vì không phụ thuộc vào một điểm ngưỡng đầu ra duy nhất. Các metric tại ngưỡng vận hành chỉ dùng để mô tả cấu hình dự kiến triển khai và không được dùng riêng để khẳng định mô hình tốt hơn.

---

## 8. Chỉ số hiệu năng

### 8.1. Phạm vi đo

Detector latency gồm:

1. Chuyển ảnh đã giải mã sang định dạng model yêu cầu.
2. Tiền xử lý của detector.
3. Forward/inference.
4. Hậu xử lý và NMS.
5. Chuyển kết quả về schema chuẩn.

Không gồm:

- Đọc ảnh từ ổ đĩa.
- Parse annotation.
- Ghi JSON/CSV.
- Tính metric.

### 8.2. Giao thức đo

- Load mô hình một lần trước khi đo.
- Warm-up `20` ảnh; không ghi các lần này vào kết quả.
- Chạy `3` lượt toàn bộ WIDER FACE validation cho từng mô hình.
- Thứ tự ảnh cố định theo đường dẫn đã sort.
- Thứ tự mô hình được xoay vòng giữa các lượt để hạn chế ảnh hưởng thứ tự chạy.
- Dùng `time.perf_counter_ns()`.
- Thu gom rác trước mỗi lượt đầy đủ; không gọi garbage collection trong từng ảnh.
- Không tính lần load model vào latency từng ảnh; model load time được ghi thành metric riêng.

### 8.3. Kết quả hiệu năng

- Model load time.
- Latency trung vị theo ảnh.
- Latency P95 theo ảnh.
- FPS suy ra từ tổng thời gian detector của toàn bộ ảnh.
- Peak RSS của tiến trình nếu thu thập ổn định được trên macOS.

Không lấy trung bình FPS của từng ảnh. FPS được tính bằng tổng số ảnh chia tổng detector time.

---

## 9. Thiết kế mã nguồn

```text
COMPARE_FACE_DETECTION/
├── TECH_SPEC.md
├── README.md
├── pyproject.toml
├── uv.lock
├── configs/
│   └── benchmark.yaml
├── src/
│   └── face_benchmark/
│       ├── adapters/
│       │   ├── haar.py
│       │   ├── mtcnn.py
│       │   └── retinaface.py
│       ├── dataset.py
│       ├── metrics.py
│       ├── validate_dataset.py
│       ├── run_benchmark.py
│       └── build_report.py
├── tests/
├── data/
├── vendor/
├── weights/
└── results/
    └── <run_id>/
```

Mỗi detector phải triển khai cùng interface:

```python
class FaceDetector(Protocol):
    name: str

    def load(self) -> None: ...
    def warmup(self, images: list[np.ndarray]) -> None: ...
    def detect(self, image: np.ndarray) -> list[Detection]: ...
```

---

## 10. File kết quả bắt buộc

Mỗi lần chạy chính thức tạo một thư mục bất biến `results/<run_id>/` gồm:

```text
results/<run_id>/
├── config.snapshot.yaml
├── environment.json
├── dataset_manifest.json
├── predictions/
│   ├── haar.jsonl
│   ├── mtcnn.jsonl
│   └── retinaface_mobilenet025.jsonl
├── timing/
│   ├── haar.csv
│   ├── mtcnn.csv
│   └── retinaface_mobilenet025.csv
├── metrics.json
├── comparison.csv
├── comparison.md
└── run.log
```

`comparison.md` và `comparison.csv` phải được sinh bởi `build_report.py`; không sửa thủ công.

---

## 11. Bảng kết quả cuối cùng

Bảng chính được sinh theo cấu trúc:

| Mô hình | AP Easy | AP Medium | AP Hard | Precision | Recall | F1 | Median ms | P95 ms | FPS | Ảnh không phát hiện |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Haar Cascade – OpenCV frontal default |  |  |  |  |  |  |  |  |  |  |
| MTCNN – facenet-pytorch |  |  |  |  |  |  |  |  |  |  |
| RetinaFace – MobileNet0.25 |  |  |  |  |  |  |  |  |  |  |

Mọi ô số để trống trong tech spec. Chỉ chương trình benchmark được phép điền số liệu.

Không thêm cột “xếp hạng tổng” hoặc tự tính điểm có trọng số. Kết quả phải được phân tích theo hai trục riêng: chất lượng phát hiện và chi phí suy luận.

---

## 12. Kiểm thử bắt buộc trước lần chạy chính thức

### 12.1. Dataset

- Parse đúng ảnh không có mặt và ảnh có nhiều mặt.
- Chuyển `xywh` ground truth sang `xyxy` đúng.
- Phát hiện annotation thiếu hoặc box không hợp lệ.

### 12.2. Metric

- IoU của hai box trùng nhau bằng `1`.
- IoU của hai box không giao nhau bằng `0`.
- Một prediction không được ghép với nhiều ground-truth box.
- Prediction trùng lặp được tính false positive sau lần ghép đầu.
- AP trên fixture nhỏ có kết quả tính tay đã biết.

### 12.3. Adapter

- Mỗi adapter trả đúng schema.
- Không detector nào thay đổi kích thước ảnh đầu vào dùng bởi detector khác.
- Bounding box được clip đúng biên ảnh.
- Ảnh không có detection trả danh sách rỗng thay vì lỗi.

### 12.4. Timing

- Không tính thời gian đọc file.
- Warm-up không xuất hiện trong CSV chính.
- Mỗi ảnh có đủ ba bản ghi latency tương ứng ba lượt chạy.

---

## 13. Quy tắc phân tích và lựa chọn sau benchmark

- Không gọi một mô hình là “tốt nhất” chỉ vì có AP cao nhất hoặc FPS cao nhất.
- Xác định mô hình nào bị mô hình khác trội hơn đồng thời về chất lượng và latency.
- Nếu có đánh đổi, trình bày rõ AP thay đổi bao nhiêu và latency/FPS thay đổi bao nhiêu.
- Không tạo điểm tổng hợp giữa AP và FPS khi chưa có cơ sở xác định trọng số.
- Chỉ đề xuất mô hình cho hệ thống sau khi đối chiếu kết quả với yêu cầu vận hành thực tế.
- Mọi nhận xét phải truy ngược được tới `comparison.csv`, `metrics.json` hoặc file timing gốc.

---

## 14. Điều kiện hoàn thành benchmark detector

Benchmark detector được xem là hoàn thành khi:

1. Tech spec đã được duyệt và không còn thay đổi chưa ghi phiên bản.
2. Toàn bộ test bắt buộc vượt qua.
3. Cả ba mô hình chạy trên cùng danh sách ảnh và cùng máy.
4. Có đủ prediction, timing, environment và dataset manifest.
5. Bảng `comparison.md` được sinh tự động.
6. Chạy lặp lại không làm thay đổi metric chất lượng; chênh lệch latency nằm trong giới hạn được báo cáo.
7. Có thể chạy lại bằng một lệnh được ghi trong README.

Chỉ sau khi đáp ứng bảy điều kiện này mới viết phần bảng so sánh, phân tích và lựa chọn detector trong luận văn.

---

## 15. Tài liệu tham chiếu

1. Viola, P. và Jones, M. (2001), *Rapid Object Detection using a Boosted Cascade of Simple Features*. [CVPR](https://doi.org/10.1109/CVPR.2001.990517).
2. Zhang, K. và cộng sự (2016), *Joint Face Detection and Alignment Using Multitask Cascaded Convolutional Networks*. [IEEE Signal Processing Letters](https://doi.org/10.1109/LSP.2016.2603342).
3. Deng, J. và cộng sự (2020), *RetinaFace: Single-Shot Multi-Level Face Localisation in the Wild*. [CVPR](https://openaccess.thecvf.com/content_CVPR_2020/html/Deng_RetinaFace_Single-Shot_Multi-Level_Face_Localisation_in_the_Wild_CVPR_2020_paper.html).
4. Yang, S. và cộng sự (2016), *WIDER FACE: A Face Detection Benchmark*. [CVPR](https://openaccess.thecvf.com/content_cvpr_2016/html/Yang_WIDER_FACE_A_CVPR_2016_paper.html).
