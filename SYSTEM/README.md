# Touchpoint CRM

Mã nguồn triển khai hệ thống CRM kết hợp nhận dạng biểu cảm khuôn mặt tại nhiều điểm chạm. Phiên bản này phục vụ một cửa hàng, không có mô-đun quản lý chi nhánh.

## Thành phần

- `apps/api`: FastAPI, SQLAlchemy, PostgreSQL/SQLite.
- `services/vision`: phát hiện khuôn mặt, FER và véc-tơ nhận dạng.
- `services/simulator`: tạo hành trình và đơn hàng trình diễn khi không có camera.
- `apps/web`: React, TypeScript và Ant Design.
- `scripts`: chuẩn bị 100 ảnh đại diện, nạp dữ liệu CRM và chụp ảnh minh chứng.

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

## Hai chế độ xử lý ảnh

- `opencv_demo`: nhẹ, dùng để kiểm tra API và giao diện. Nhãn biểu cảm và véc-tơ của chế độ này không được dùng trong báo cáo hay đánh giá.
- `deepface_retinaface`: dùng RetinaFace-MobileNet0.25, mô hình Emotion của DeepFace và ArcFace. Chế độ này yêu cầu đầy đủ trọng số và nhóm phụ thuộc mô hình.

Docker mặc định không cài nhóm phụ thuộc mô hình nặng. Khi kiểm thử backend thật, đặt `INSTALL_MODEL_DEPS=true` và `VISION_BACKEND=deepface_retinaface` trong `.env` rồi dựng lại dịch vụ `vision`.

## Kiểm thử

```bash
make test
```

Xem [trạng thái triển khai](IMPLEMENTATION_STATUS.md) để biết phần đã chạy được và phần còn cần dữ liệu hoặc môi trường thật để kiểm chứng.

## Demo không có camera

Xem `../SYSTEM_DEVELOPMENT/DEMO_SCENARIO.md`. Kịch bản hiện tại tạo đúng 100 khách hàng, 24 sản phẩm, lịch sử mua hàng và hành trình tại bốn điểm chạm. Ảnh đại diện được lấy từ tập kiểm tra FairFace và có tệp kê khai nguồn đi kèm.

Sau khi hệ thống Docker hoạt động, chuẩn bị ảnh, nạp dữ liệu và chạy mô phỏng bằng các lệnh:

```bash
make demo-portraits
make demo-seed
make demo-simulate
```

Lệnh mô phỏng tạo nhãn biểu cảm giả lập và đánh dấu nguồn là `SIMULATOR`. Dữ liệu này chỉ dùng để kiểm tra lưu trữ, hành trình và giao diện; không dùng để đánh giá độ chính xác FER.
