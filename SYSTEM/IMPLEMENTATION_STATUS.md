# Trạng thái triển khai hệ thống

Tài liệu này ghi nhận trạng thái đã kiểm tra ngày 01/10/2026. Hệ thống phục vụ một cửa hàng và không có chức năng quản lý chi nhánh.

## 1. Thành phần đã chạy

- PostgreSQL 16 và pgvector 0.8.3.
- Máy chủ nghiệp vụ FastAPI.
- Dịch vụ xử lý ảnh ở cấu hình `deepface_retinaface`, sử dụng RetinaFace--MobileNet0.25, mô hình Emotion qua DeepFace và ArcFace.
- Dịch vụ tạo dữ liệu mô phỏng.
- Giao diện React/TypeScript qua Nginx.
- Di trú cơ sở dữ liệu bằng Alembic.
- Cơ sở dữ liệu dự án đã nâng cấp đến `e7b4a91d2c60`; bản này nằm sau và bao gồm `c8f31b7b2a19`.

Các địa chỉ đang sử dụng:

- Giao diện: <http://127.0.0.1:8080>
- API nghiệp vụ: <http://127.0.0.1:8000/docs>
- Dịch vụ xử lý ảnh: <http://127.0.0.1:8001/docs>
- Dịch vụ mô phỏng: <http://127.0.0.1:8002/docs>

## 2. Chức năng đã triển khai

### CRM

- Đăng nhập bằng cookie JWT.
- Quản lý khách hàng và trạng thái đồng ý sử dụng dữ liệu khuôn mặt.
- Quản lý nhóm sản phẩm, sản phẩm, đơn hàng và lịch sử mua hàng.
- Giữ mã, tên và đơn giá sản phẩm tại thời điểm tạo đơn hàng.
- Quản lý bốn khu vực được xác định trước trong một cửa hàng.
- Xem hồ sơ khách hàng cùng ảnh đại diện và lịch sử mua hàng.

### Khuôn mặt và quá trình mua sắm

- Giao diện đăng ký mẫu khuôn mặt và tìm khách hàng bằng ảnh.
- Hợp đồng API cho phát hiện khuôn mặt, FER và véc-tơ nhận dạng.
- Lưu riêng sự kiện thu nhận và từng quan sát khuôn mặt trong một khung hình.
- Xử lý độc lập nhiều khuôn mặt; một khung hình có thể tạo nhiều quan sát.
- Lưu trạng thái ảnh không hợp lệ hoặc không có khuôn mặt ở cấp sự kiện thu nhận.
- Tạo, cập nhật và kết thúc lần mua sắm.
- Sắp xếp các quan sát trong cùng lần mua sắm theo thời gian.
- Phát hiện khu vực bị thiếu và bản ghi xung đột thời gian.
- Giữ lịch sử khi xác nhận khách hàng hoặc xử lý lại một quan sát.
- Cho phép người quản lý xác nhận khách hàng đối với bản ghi chưa xác định.
- Đánh dấu riêng dữ liệu nguồn camera và nguồn mô phỏng.

### Báo cáo

- Phân bố bảy nhãn biểu cảm tại từng khu vực.
- Thay đổi nhãn giữa các khu vực liên tiếp trong cùng lần mua sắm.
- Chất lượng dữ liệu đầu vào.
- Biến thiên nhãn trong cùng khu vực, cùng ngày và các khoảng 5, 15, 30 hoặc 60 phút.
- Chuỗi quan sát của từng khách hàng.
- Lọc báo cáo theo khu vực, thời gian và trạng thái xác định khách hàng.
- Chọn bản ghi đầu tiên, cuối cùng hoặc có mức tin cậy cao nhất làm đại diện khi phân tích thay đổi.

## 3. Dữ liệu thử nghiệm hiện có

- 100 khách hàng và 100 mẫu ArcFace.
- Một nguồn ảnh FairFace với 110 bản ghi được chia rời thành 100 khách hàng, 8 danh tính hiệu chỉnh và 2 người chưa đăng ký.
- 115 sự kiện ảnh khách đã đăng ký, 2 sự kiện người chưa đăng ký và 3 ca biên; tổng 120/120 sự kiện đạt điều kiện mong đợi.
- 6 nhóm sản phẩm và 24 sản phẩm.
- 4 khu vực được xác định trước.
- 225 lần mua sắm, gồm 100 lần hình thành từ luồng ảnh và 125 lần từ tải nghiệp vụ.
- 529 sự kiện thu nhận và 633 quan sát; trong đó luồng xử lý ảnh tạo 120 sự kiện và 236 quan sát, còn tải nghiệp vụ tạo 409 sự kiện và 397 quan sát.
- 93 đơn hàng và 232 dòng sản phẩm trong đơn.

Tải nghiệp vụ dùng hạt giống `20260923` và tạo 90 đơn hàng mới. Ba đơn hàng còn lại thuộc dữ liệu khởi tạo.

Trong 633 quan sát, 236 quan sát đi qua dịch vụ xử lý ảnh và 397 quan sát thuộc tải nghiệp vụ được xây dựng theo quy tắc cố định. Phần tải nghiệp vụ dùng để kiểm tra phép lọc, tổng hợp và giao diện; nó không được dùng để chứng minh độ chính xác FER.

## 4. Kết quả kiểm tra

- 9/9 kiểm thử máy chủ nghiệp vụ đạt, gồm kiểm thử một khung hình tạo nhiều quan sát và chống gửi trùng.
- 3/3 kiểm thử dịch vụ xử lý ảnh đạt, gồm kiểm thử xử lý độc lập nhiều khuôn mặt.
- Giao diện React/TypeScript biên dịch thành công ở chế độ phát hành.
- Phát lại dữ liệu ảnh đạt 120/120 sự kiện; kiểm tra hậu điều kiện đạt 105/105.
- Toàn bộ hệ thống chạy bằng Docker Compose.
- Ảnh giao diện chức năng được dùng trong Chương 4; ảnh của lần kiểm nghiệm và trạng thái triển khai được dùng trong Chương 5.
- PDF luận văn đã build và kiểm tra trực quan sau khi cập nhật Chương 4 và Chương 5.

## 5. Phần chưa được coi là hoàn thành

- Chưa kết nối camera vật lý.
- Chưa có thuật toán theo dõi một người chưa xác định qua các khung hình liên tiếp; nguồn thu nhận phải kiểm soát tần suất lấy mẫu.
- Chưa đánh giá độ chính xác FER.
- Ngưỡng cosine 0,269958 chỉ được hiệu chỉnh cho điều kiện biến đổi có kiểm soát; chưa đại diện cho camera thật.
- FairFace không phải tập định danh theo người; kết quả 115/115 không phải độ chính xác nhận dạng ngoài thực tế.
- Chưa có kiểm thử trình duyệt tự động trong bộ kiểm thử chính thức; chương trình chụp ảnh chỉ phục vụ kiểm tra và tạo minh chứng.
- Gói JavaScript còn lớn và cần được chia nhỏ ở giai đoạn tối ưu.

Các nội dung chưa kiểm chứng không được dùng làm kết quả thực nghiệm hoặc kết luận trong luận văn.
