# CRM kết hợp nhận dạng biểu cảm

Mã nguồn triển khai hệ thống CRM kết hợp nhận dạng biểu cảm khuôn mặt tại nhiều khu vực được xác định trước. Phiên bản này phục vụ một cửa hàng, không có mô-đun quản lý chi nhánh.

## Thành phần

- `apps/api`: FastAPI, SQLAlchemy, PostgreSQL/SQLite.
- `services/vision`: phát hiện khuôn mặt, FER và véc-tơ nhận dạng.
- `services/simulator`: tạo quá trình mua sắm và đơn hàng minh họa khi không có camera.
- `apps/web`: React, TypeScript và Ant Design.
- `scripts`: chuẩn bị dữ liệu KDEF, đăng ký mẫu, phát lại sự kiện ảnh theo điểm chạm, chạy thực nghiệm chuỗi có đối chứng, kiểm tra hậu điều kiện và chụp ảnh minh chứng.

## Chạy phát triển không dùng Docker

```bash
make install
make run-vision
make run-api
cd apps/web && npm run dev
```

API mặc định dùng SQLite tại `apps/api/touchpoint_crm.db`. Giao diện mở tại <http://localhost:5173>.

Tài khoản phát triển:

```text
manager@example.com
demo1234
```

## Chạy bằng Docker Compose

Sao chép `.env.example` thành `.env`, thay khóa JWT và chọn backend xử lý ảnh, sau đó:

```bash
docker compose up --build
```

Giao diện mở tại <http://localhost:8080>.

## Cấu hình xử lý ảnh

- `opencv_demo`: nhẹ, dùng để kiểm tra API và giao diện. Nhãn biểu cảm và véc-tơ của chế độ này không được dùng trong báo cáo hay đánh giá.
- `deepface_retinaface`: dùng RetinaFace-MobileNet0.25, mô hình Emotion của DeepFace và ArcFace. Chế độ này yêu cầu đầy đủ trọng số và nhóm phụ thuộc mô hình.

Dịch vụ xử lý toàn bộ khuôn mặt phát hiện được trong một ảnh. Máy chủ lưu một sự kiện thu nhận cho khung hình và một quan sát riêng cho từng khuôn mặt; ảnh nhiều người không bị loại bỏ.

Docker mặc định cài nhóm phụ thuộc mô hình và sử dụng `deepface_retinaface`. Trọng số RetinaFace và bộ nhớ đệm mô hình DeepFace được gắn vào container ở chế độ chỉ đọc.

## Kiểm thử

```bash
make test
```

Xem [trạng thái triển khai](IMPLEMENTATION_STATUS.md) để biết phần đã chạy được và phần còn cần dữ liệu hoặc môi trường thật để kiểm chứng.

## Phân tích chuỗi trạng thái

Máy chủ tạo một chuỗi nhãn dự đoán cho mỗi lần mua sắm, tính ma trận khoảng cách Optimal Matching bằng Sequenzo, phân cụm PAM và chọn số cụm bằng Average Silhouette Width sau khi loại các phương án có cụm quá nhỏ. Kết quả lưu cả medoid, kích thước cụm, silhouette của từng chuỗi và liên kết về lần mua sắm gốc.

Chạy thực nghiệm có đối chứng gồm 25 khách hàng, 125 lần mua sắm và 500 quan sát:

```bash
make demo-sequence-experiment \
  SIMULATION_RUN_ID=SIM-CONTROLLED-20261008 \
  SEED=20261008
make demo-sequence-evidence \
  SOURCE_RUN_ID=SIM-CONTROLLED-20261008 \
  SOURCE_TYPE=SIMULATOR \
  EXPECTED_USED_VISITS=125 \
  EXPECTED_K=5
```

Lớp này dùng nhãn được tạo theo năm mẫu biết trước để kiểm tra thuật toán và giao diện. Nó không đi qua dịch vụ xử lý ảnh và không được dùng để kết luận chất lượng RetinaFace, ArcFace, DeepFace hoặc mức độ hài lòng của khách hàng.

## Demo đầu cuối bằng KDEF

Nguồn tệp dùng cho demo là bản KDEF đã xử lý trên Kaggle: [chenrich/kdef-database](https://www.kaggle.com/datasets/chenrich/kdef-database). Bản phân phối gồm 2.938 ảnh trong bảy thư mục nhãn và 140 mã nhóm nguồn dạng số; nó không giữ mã phiên/góc và tên tệp của KDEF gốc. Ảnh không được lưu trong kho mã. Người chạy tải dữ liệu, giải nén và truyền thư mục chứa bảy thư mục nhãn qua `KDEF_ROOT`. Kịch bản chọn cùng mã nhóm ở nhiều biểu cảm, ưu tiên một ảnh Neutral nhìn thẳng làm ảnh đăng ký và phát các ảnh khác tại bốn điểm chạm. Biểu cảm và ảnh nguồn có thể lặp.

Lần demo cuối đã dùng năm mã nhóm nguồn, năm lượt cho mỗi hồ sơ và bốn điểm chạm cho mỗi lượt, tương ứng 5 hồ sơ, 25 lần mua sắm và 100 khung Camera. Đây là cấu hình trình diễn luồng, không phải giới hạn của hệ thống.

Để chạy lại từ đầu, chuẩn bị dữ liệu trước, khởi động stack, sau đó chạy đúng thứ tự:

```bash
make demo-prepare \
  KDEF_ROOT=/Users/sotatek/Downloads/archive \
  CUSTOMER_COUNT=5 \
  EXPERIMENT_RUN_ID=KDEF-KAGGLE-20261008-LIVE
docker compose up --build -d
make demo-reset
make demo-seed
make demo-enroll
make demo-calibrate
make demo-replay SPEED=0 MINIMUM_PASS_RATE=0.90
make demo-analyze EXPERIMENT_RUN_ID=KDEF-KAGGLE-20261008-LIVE
make demo-verify
SOURCE_RUN_ID=KDEF-KAGGLE-20261008-LIVE \
  node scripts/capture_kdef_live_demo.mjs
SOURCE_RUN_ID=KDEF-KAGGLE-20261008-LIVE \
  SOURCE_TYPE=CAMERA EXPECTED_USED_VISITS=22 EXPECTED_K=5 \
  node scripts/capture_sequence_analysis.mjs
SOURCE_RUN_ID=KDEF-KAGGLE-20261008-LIVE \
  node scripts/capture_system_status.mjs
```

`MINIMUM_PASS_RATE` chỉ quyết định mã thoát của lệnh replay; mọi khung không đạt vẫn được giữ nguyên trong `replay_results.jsonl` và thống kê. Lần chạy đã khóa đạt 96/100 khung nên dùng ngưỡng 0,90 để quy trình tiếp tục sang bước phân tích mà không che bốn ca `NO_MATCH`.

Chuỗi đưa vào phân cụm luôn lấy từ `Observation.expression_label` do dịch vụ ảnh trả về. Nhãn thư mục Kaggle chỉ dùng để chọn ảnh và đối chiếu sau chạy, không được thay cho dự đoán của hệ thống. Không được mô tả bản Kaggle 2.938 ảnh là bộ KDEF gốc đầy đủ 4.900 ảnh.

## Artefact và ảnh minh chứng

Mỗi lần chạy ghi kết quả dưới `artifacts/experiment-runs/<RUN_ID>/`. Ảnh được chụp bằng trình duyệt sau khi script xác nhận đúng run, nguồn dữ liệu, số observation, số chuỗi và số cụm. `capture_system_status.mjs` còn ghi lại trạng thái Compose cùng phản hồi HTTP dưới dạng JSON và ảnh. Danh mục bằng chứng hoàn chỉnh nằm tại [HANDOVER_EVIDENCE.md](HANDOVER_EVIDENCE.md).
