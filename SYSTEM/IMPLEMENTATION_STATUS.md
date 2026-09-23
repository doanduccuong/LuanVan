# Trạng thái triển khai hệ thống

Tài liệu này ghi nhận đúng trạng thái đã chạy ngày 23/09/2026. Hệ thống phục vụ một cửa hàng và không có chức năng quản lý chi nhánh.

## 1. Thành phần đã chạy

- PostgreSQL 16 và pgvector 0.8.3.
- Máy chủ nghiệp vụ FastAPI.
- Dịch vụ xử lý ảnh ở cấu hình nhẹ `opencv_demo`.
- Dịch vụ tạo dữ liệu mô phỏng.
- Giao diện React/TypeScript qua Nginx.
- Di trú cơ sở dữ liệu bằng Alembic.

Các địa chỉ đang sử dụng:

- Giao diện: <http://127.0.0.1:8080>
- API nghiệp vụ: <http://127.0.0.1:8000/docs>
- Dịch vụ mô phỏng: <http://127.0.0.1:8002/docs>

## 2. Chức năng đã triển khai

### CRM

- Đăng nhập bằng cookie JWT.
- Quản lý khách hàng và trạng thái đồng ý sử dụng dữ liệu khuôn mặt.
- Quản lý nhóm sản phẩm, sản phẩm, đơn hàng và lịch sử mua hàng.
- Giữ mã, tên và đơn giá sản phẩm tại thời điểm tạo đơn hàng.
- Quản lý bốn điểm chạm trong một cửa hàng.
- Xem hồ sơ khách hàng cùng ảnh đại diện và lịch sử mua hàng.

### Khuôn mặt và hành trình

- Giao diện đăng ký mẫu khuôn mặt và tìm khách hàng bằng ảnh.
- Hợp đồng API cho phát hiện khuôn mặt, FER và véc-tơ nhận dạng.
- Lưu trạng thái ảnh không hợp lệ, không có khuôn mặt và kết quả xử lý hợp lệ.
- Tạo, cập nhật và kết thúc lượt ghé thăm.
- Sắp xếp các quan sát trong cùng lượt theo thời gian.
- Đánh dấu riêng dữ liệu nguồn camera và nguồn mô phỏng.

### Báo cáo

- Phân bố bảy nhãn biểu cảm tại từng điểm chạm.
- Thay đổi nhãn giữa các điểm chạm liên tiếp trong cùng lượt ghé thăm.
- Chất lượng dữ liệu đầu vào.
- Biến thiên nhãn trong cùng điểm chạm, cùng ngày và các khoảng 5, 15, 30 hoặc 60 phút.
- Sơ đồ hành trình của từng khách hàng.

## 3. Dữ liệu demo hiện có

- 100 khách hàng mô phỏng, không nhiều hơn.
- 100 ảnh đại diện từ tập kiểm tra FairFace, kèm tệp kê khai nguồn và mã kiểm tra.
- 6 nhóm sản phẩm và 24 sản phẩm.
- 4 điểm chạm.
- 125 lượt ghé thăm của đủ 100 khách hàng.
- 397 quan sát, gồm 385 bản ghi hợp lệ và 12 bản ghi lỗi có kiểm soát.
- 93 đơn hàng và 232 dòng sản phẩm trong đơn.

Lần mô phỏng chính có mã `SIM-20260923083712-be107c`, dùng hạt giống `20260923` và tạo 90 đơn hàng mới. Ba đơn hàng còn lại thuộc dữ liệu khởi tạo.

Nhãn biểu cảm của lần chạy này do dịch vụ mô phỏng tạo. Chúng chứng minh luồng dữ liệu và giao diện hoạt động, không chứng minh độ chính xác FER.

## 4. Kết quả kiểm tra

- 6/6 kiểm thử máy chủ nghiệp vụ đạt.
- 2/2 kiểm thử dịch vụ xử lý ảnh cấu hình nhẹ đạt.
- Giao diện React/TypeScript biên dịch thành công ở chế độ phát hành.
- Toàn bộ hệ thống chạy bằng Docker Compose.
- 13 ảnh giao diện và tài liệu API đã được chụp từ hệ thống đang chạy để dùng trong Chương 4.
- PDF luận văn đã build thành công sau khi cập nhật Chương 4.

## 5. Phần chưa được coi là hoàn thành

- Chưa kết nối camera vật lý.
- Chưa chạy và kiểm chứng đầy đủ cấu hình `deepface_retinaface` trong Docker.
- Chưa hiệu chỉnh ngưỡng nhận dạng khách hàng trên dữ liệu phù hợp.
- Chưa đánh giá độ chính xác FER.
- 100 ảnh FairFace chỉ dùng làm ảnh đại diện CRM, không phải dữ liệu đánh giá nhận dạng hay FER.
- Chưa có kiểm thử trình duyệt tự động trong bộ kiểm thử chính thức; chương trình chụp ảnh chỉ phục vụ kiểm tra và tạo minh chứng.
- Gói JavaScript còn lớn và cần được chia nhỏ ở giai đoạn tối ưu.

Các nội dung chưa kiểm chứng không được dùng làm kết quả thực nghiệm hoặc kết luận trong luận văn.
