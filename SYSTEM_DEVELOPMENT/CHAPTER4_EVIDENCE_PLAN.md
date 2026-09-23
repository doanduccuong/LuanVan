# Hình và kết quả minh chứng cho Chương 4

## Nguyên tắc

- Chương 4 chỉ mô tả chức năng đã có mã nguồn và đầu ra kiểm tra được.
- Mỗi nhóm nội dung phải có sơ đồ, bảng kết quả hoặc ảnh chụp từ hệ thống đang chạy.
- Ảnh giao diện phải có dữ liệu, không dùng màn hình trống.
- Nhãn do dịch vụ mô phỏng tạo phải được nói rõ, không dùng làm bằng chứng độ chính xác FER.
- Mỗi hình trong LaTeX có chú thích, nhãn tham chiếu và được giải thích trong nội dung.

## Cấu trúc minh chứng đang sử dụng

| Mục Chương 4 | Minh chứng |
|---|---|
| 4.1 Tổng quan hệ thống | Bảng thành phần, sơ đồ kiến trúc và sơ đồ luồng dữ liệu |
| 4.2.1 Ca sử dụng tổng quan | Sơ đồ tác nhân và các ca sử dụng chính |
| 4.2.2 Phân rã chức năng | Sơ đồ bốn nhóm chức năng |
| 4.2.3 Đặc tả chức năng | Bảng UC01–UC05 với điều kiện, dữ liệu vào và kết quả |
| 4.2.4 API và xử lý ảnh | Ảnh tài liệu OpenAPI và sơ đồ xử lý ảnh |
| 4.2.5 Dữ liệu mô phỏng | Ảnh 100 khách hàng, ảnh API mô phỏng và bảng số liệu PostgreSQL |
| 4.3.1 Tổng quan | Ảnh tổng quan và ảnh biến thiên theo ngày, khu vực |
| 4.3.2 Khách hàng | Ảnh hồ sơ cùng lịch sử mua hàng |
| 4.3.3 Sản phẩm, đơn hàng | Hai ảnh danh sách có dữ liệu |
| 4.3.4 Điểm chạm, hành trình | Ảnh bốn điểm chạm và sơ đồ lượt ghé thăm |
| 4.3.5 Phân tích | Ảnh phân bố, thay đổi nhãn và chất lượng dữ liệu |
| 4.4 Kiểm tra | Bảng kết quả kiểm thử và số liệu lần mô phỏng |

## Ảnh đã tạo

Tất cả ảnh nằm tại `BAO CAO/Hinhve/Chuong4/` và được tạo bằng `SYSTEM/scripts/capture_chapter4.mjs`.

| Tệp | Nội dung |
|---|---|
| `4_01_tong_quan.png` | Tổng số khách hàng, sản phẩm, lượt ghé thăm và phân bố nhãn |
| `4_02_danh_sach_khach_hang.png` | Danh sách 100 khách hàng có ảnh đại diện |
| `4_03_ho_so_lich_su_mua_hang.png` | Hồ sơ và ba đơn hàng của khách hàng demo 001 |
| `4_04_danh_muc_san_pham.png` | Danh mục 24 sản phẩm |
| `4_05_lich_su_mua_hang.png` | Danh sách đơn hàng |
| `4_06_diem_cham.png` | Bốn điểm chạm của một cửa hàng |
| `4_07_theo_doi_hanh_trinh.png` | Danh sách lượt và sơ đồ hành trình đang chọn |
| `4_08_phan_bo_bieu_cam.png` | Phân bố bảy nhãn theo điểm chạm |
| `4_09_thay_doi_bieu_cam.png` | Luồng nhãn giữa các điểm chạm liên tiếp |
| `4_10_chat_luong_du_lieu.png` | 385 bản ghi hợp lệ và 12 bản ghi lỗi |
| `4_11_tai_lieu_api.png` | Tài liệu API nghiệp vụ |
| `4_12_dich_vu_mo_phong.png` | Tài liệu API của dịch vụ mô phỏng |
| `4_13_bien_thien_theo_thoi_gian_khu_vuc.png` | Biến thiên nhãn trong cùng ngày và cùng khu vực |

## Kết quả kiểm tra đi kèm

- 6/6 kiểm thử API đạt.
- 2/2 kiểm thử dịch vụ ảnh cấu hình nhẹ đạt.
- Giao diện biên dịch thành công.
- Docker Compose chạy đủ PostgreSQL, API, vision, simulator và web.
- PostgreSQL có 100 khách hàng, 24 sản phẩm, 125 lượt ghé thăm, 397 quan sát và 93 đơn hàng.
- PDF được render và kiểm tra trực quan toàn bộ các trang Chương 4.

## Nội dung chưa được phép dùng làm minh chứng

- Độ chính xác FER từ nhãn mô phỏng.
- Độ chính xác nhận dạng khách hàng từ ảnh đại diện FairFace.
- Kết quả cấu hình `deepface_retinaface` khi chưa chạy kiểm chứng đầy đủ.
- Kết luận hài lòng hoặc không hài lòng chỉ từ nhãn biểu cảm.
