# Trạng thái triển khai hệ thống

Tài liệu này ghi nhận đúng phạm vi mã nguồn đã triển khai và các phần còn cần dữ liệu hoặc môi trường chạy để kiểm chứng. Hệ thống hiện phục vụ một cửa hàng, không có chức năng quản lý chi nhánh.

## 1. Phần đã triển khai

### Máy chủ nghiệp vụ

- Xác thực bằng cookie JWT với tài khoản quản lý được cấu hình sẵn.
- Quản lý khách hàng và trạng thái đồng ý sử dụng dữ liệu khuôn mặt.
- Đăng ký, tìm kiếm, xem và xóa mẫu khuôn mặt.
- Quản lý nhóm sản phẩm, sản phẩm, đơn hàng và lịch sử mua hàng.
- Lưu ảnh chụp thông tin sản phẩm trong từng dòng đơn hàng để lịch sử không thay đổi khi giá hoặc tên sản phẩm được cập nhật.
- Quản lý các điểm chạm trong một cửa hàng.
- Tiếp nhận bản ghi quan sát, liên kết khách hàng với lượt ghé thăm và sắp xếp các bản ghi theo thời gian.
- Báo cáo phân bố biểu cảm, thay đổi biểu cảm giữa các điểm chạm và chất lượng dữ liệu.
- Ghi nhật ký các thao tác có ảnh hưởng đến dữ liệu cá nhân.

### Dịch vụ xử lý ảnh

- Hợp đồng API phát hiện khuôn mặt, nhận dạng biểu cảm và tạo véc-tơ đặc trưng khuôn mặt.
- Chế độ `opencv_demo` để kiểm tra luồng API và giao diện mà không cần tải mô hình lớn.
- Mã tích hợp RetinaFace-MobileNet0.25, DeepFace Emotion và ArcFace cho chế độ `deepface_retinaface`.
- Trả về trạng thái rõ ràng khi ảnh không hợp lệ, không có khuôn mặt hoặc có nhiều khuôn mặt.
- Không tự đặt ngưỡng nhận dạng khi chưa có kết quả hiệu chỉnh.

### Giao diện CRM

- Đăng nhập và trang tổng quan.
- Quản lý khách hàng và xem lịch sử mua hàng.
- Quản lý đồng ý, đăng ký khuôn mặt và tìm khách hàng bằng ảnh.
- Quản lý nhóm sản phẩm, sản phẩm và đơn hàng.
- Quản lý điểm chạm.
- Xem danh sách lượt ghé thăm và diễn biến biểu cảm theo điểm chạm.
- Xem các biểu đồ báo cáo.
- Không có trang quản lý tài khoản và không có chức năng quản lý chi nhánh.

### Bộ dữ liệu và kịch bản demo

- Chương trình chuẩn bị ảnh từ bộ dữ liệu Yale do người dùng cung cấp.
- Chương trình tạo dữ liệu CRM mô phỏng cho một cửa hàng.
- Chương trình hiệu chỉnh ngưỡng nhận dạng khuôn mặt.
- Chương trình đăng ký ảnh khuôn mặt, phát lại hành trình và đối chiếu kết quả demo.
- Dữ liệu demo được đánh dấu riêng để có thể xóa mà không ảnh hưởng đến dữ liệu khác.

### Môi trường chạy và kiểm thử

- Docker Compose cho PostgreSQL có pgvector, dịch vụ di trú dữ liệu, API, dịch vụ xử lý ảnh và giao diện web.
- Di trú cơ sở dữ liệu ban đầu bằng Alembic.
- Kiểm thử API, quy tắc nghiệp vụ và các lỗi đầu vào của dịch vụ xử lý ảnh.
- Kiểm tra biên dịch giao diện ở chế độ phát hành.

## 2. Kết quả kiểm tra hiện có

- 5 kiểm thử của API và quy tắc nghiệp vụ đã đạt.
- 2 kiểm thử của dịch vụ xử lý ảnh đã đạt.
- Giao diện React/TypeScript đã biên dịch thành công.
- Di trú cơ sở dữ liệu đã chạy thành công trên cơ sở dữ liệu SQLite mới.
- Luồng đăng nhập, tạo khách hàng, tạo điểm chạm và gửi ảnh quan sát đã chạy qua API cục bộ.
- Cấu hình Docker Compose hợp lệ về mặt cú pháp.

## 3. Phần chưa được coi là hoàn thành

- Chưa chạy và kiểm chứng chế độ `deepface_retinaface` với đầy đủ trọng số và thư viện mô hình.
- Chưa tạo bộ dữ liệu demo thực tế vì kho mã không chứa ảnh Yale và nguồn tải chính thức chưa truy cập được từ môi trường hiện tại.
- Chưa hiệu chỉnh được ngưỡng nhận dạng khuôn mặt, vì vậy chế độ nhận dạng thật phải giữ trạng thái vô hiệu hóa cho đến khi có dữ liệu hiệu chỉnh.
- Chưa phát lại toàn bộ kịch bản demo bằng mô hình thật và chưa sinh tệp kết quả cuối cùng.
- Chưa chạy toàn bộ hệ thống bằng Docker Compose do Docker daemon chưa hoạt động trong lần kiểm tra này.
- Chưa có kiểm thử tự động từ trình duyệt và chưa đo thời gian đáp ứng của hệ thống với dữ liệu thật.
- Gói JavaScript của giao diện còn lớn; việc chia nhỏ gói tải là phần tối ưu sau khi luồng chức năng ổn định.

Các nội dung chưa kiểm chứng ở mục này không được dùng làm kết quả thực nghiệm hoặc kết luận trong luận văn.
