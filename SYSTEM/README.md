# CRM kết hợp nhận dạng biểu cảm

Mã nguồn triển khai hệ thống CRM kết hợp nhận dạng biểu cảm khuôn mặt tại nhiều khu vực được xác định trước. Phiên bản này phục vụ một cửa hàng, không có mô-đun quản lý chi nhánh.

## Thành phần

- `apps/api`: FastAPI, SQLAlchemy, PostgreSQL/SQLite.
- `services/vision`: phát hiện khuôn mặt, FER và véc-tơ nhận dạng.
- `services/simulator`: tạo quá trình mua sắm và đơn hàng minh họa khi không có camera.
- `apps/web`: React, TypeScript và Ant Design.
- `scripts`: tạo dữ liệu thử nghiệm FairFace, đăng ký mẫu, phát lại sự kiện ảnh, kiểm tra hậu điều kiện và chụp ảnh minh chứng.

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

## Thực nghiệm không có camera vật lý

Dữ liệu ảnh chỉ lấy từ một tập con FairFace. Một trăm bản ghi được dùng cho khách hàng, tám bản ghi tách rời dùng hiệu chỉnh ngưỡng và hai bản ghi tách rời dùng kiểm tra người chưa đăng ký. Từ cùng ảnh nguồn, quy trình tạo ảnh hồ sơ, khung đăng ký và khung quan sát $640\times480$ với các biến đổi vị trí, kích thước và độ sáng có kiểm soát.

Sau khi hệ thống Docker hoạt động, chuẩn bị ảnh, nạp dữ liệu và chạy mô phỏng bằng các lệnh:

```bash
make demo-prepare
make demo-seed
make demo-calibrate
make demo-enroll
make demo-replay
make demo-simulate
make demo-verify
```

Pha phát lại ảnh gửi 120 sự kiện qua RetinaFace, DeepFace và ArcFace. Tải nghiệp vụ tạo nhãn tất định và đánh dấu nguồn là `SIMULATOR`; phần này chỉ kiểm tra lưu trữ, lần mua sắm, đơn hàng và báo cáo, không dùng để đánh giá độ chính xác FER hay nhận dạng danh tính.
