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

Lần mới nhất `KDEF-RANDOM-TIME-20261013-LIVE` dùng năm nhóm nguồn, năm lượt mỗi hồ sơ và bốn điểm chạm mỗi lượt: 5 hồ sơ, 25 lần mua sắm dự kiến và 100 khung Camera. Nhãn rồi ảnh được lấy ngẫu nhiên có hoàn lại; khoảng cách giữa hai điểm chạm được lấy ngẫu nhiên từ 5 đến 15 phút. Không gán trước chuỗi hoặc số cụm.

Để tái lập từ đầu, xem [quy trình, số liệu và bằng chứng mới](artifacts/experiment-runs/KDEF-RANDOM-TIME-20261013-LIVE/README.md). Luôn sao lưu trước khi reset demo và chọn thư mục dữ liệu mới để không ghi đè bằng chứng. Chụp lại giao diện của lần chạy hiện tại:

```bash
SOURCE_RUN_ID=KDEF-RANDOM-TIME-20261013-LIVE \
  EXPECTED_USED_VISITS=23 EXPECTED_K=3 EXPECTED_OBSERVATIONS=97 \
  node scripts/capture_kdef_live_demo.mjs
SOURCE_RUN_ID=KDEF-RANDOM-TIME-20261013-LIVE \
  SOURCE_TYPE=CAMERA EXPECTED_USED_VISITS=23 EXPECTED_K=3 \
  node scripts/capture_sequence_analysis.mjs
SOURCE_RUN_ID=KDEF-RANDOM-TIME-20261013-LIVE \
  node scripts/capture_system_status.mjs
SOURCE_RUN_ID=KDEF-RANDOM-TIME-20261013-LIVE node scripts/capture_chapter4.mjs
```

`MINIMUM_PASS_RATE` chỉ quyết định mã thoát của replay; mọi khung không đạt vẫn giữ trong `replay_results.jsonl`. Lần mới dùng 0 để thu thập kết quả không áp tỷ lệ thành công kỳ vọng: 97/100 khung ghép đúng, 3 không khớp, 0 ghép chéo; 23/25 chuỗi đủ điều kiện, K=3, ASW=0,345181. Tham số này không thay ngưỡng ArcFace hoặc quy tắc ROC Chương 3.

Chuỗi đưa vào phân cụm luôn lấy từ `Observation.expression_label` do dịch vụ ảnh trả về. Nhãn thư mục Kaggle chỉ dùng để chọn ảnh và đối chiếu sau chạy, không được thay cho dự đoán của hệ thống. Không được mô tả bản Kaggle 2.938 ảnh là bộ KDEF gốc đầy đủ 4.900 ảnh.

## Artefact và ảnh minh chứng

Mỗi lần chạy ghi kết quả dưới `artifacts/experiment-runs/<RUN_ID>/`. Ảnh được chụp bằng trình duyệt sau khi script xác nhận đúng run, nguồn dữ liệu, số observation, số chuỗi và số cụm. `capture_system_status.mjs` còn ghi lại trạng thái Compose cùng phản hồi HTTP dưới dạng JSON và ảnh. Danh mục bằng chứng hoàn chỉnh nằm tại [HANDOVER_EVIDENCE.md](HANDOVER_EVIDENCE.md).
