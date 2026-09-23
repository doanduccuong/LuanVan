# Kịch bản demo hệ thống không sử dụng camera

## 1. Mục đích và phạm vi

Kịch bản dùng để chứng minh các phần mềm sau đã hoạt động:

1. Quản lý đúng 100 khách hàng có ảnh đại diện.
2. Quản lý danh mục sản phẩm và lịch sử mua hàng.
3. Tạo các lượt ghé thăm qua nhiều điểm chạm khi chưa có camera.
4. Theo dõi hành trình của từng khách hàng.
5. Xem phân bố và sự thay đổi của nhãn biểu cảm.
6. Theo dõi nhãn trong cùng khu vực, cùng ngày và cùng khoảng thời gian.
7. Tách dữ liệu hợp lệ khỏi dữ liệu lỗi.

Kịch bản không dùng để đánh giá độ chính xác của mô hình FER hoặc nhận dạng khách hàng. Nhãn biểu cảm được tạo giả lập và mọi quan sát đều được đánh dấu `source_type=SIMULATOR`.

## 2. Dữ liệu chuẩn bị

### 2.1. Khách hàng và ảnh đại diện

- Số khách hàng: đúng 100.
- Mã: `CUS-DEMO-001` đến `CUS-DEMO-100`.
- Tên, số điện thoại và thư điện tử: dữ liệu giả.
- Ảnh đại diện: 100 ảnh đầu tiên được chọn từ tập kiểm tra FairFace.
- Tệp ảnh: `SYSTEM/fixtures/demo_dataset/customer_images/`.
- Tệp kê khai: `customer_image_manifest.csv` và `portrait_sources.json`.

Ảnh FairFace chỉ hiển thị trong hồ sơ CRM. Ảnh không được dùng làm nhãn đúng cho FER và không chứng minh khả năng nhận dạng một người qua nhiều camera.

Nguồn:

- [FairFace paper, WACV 2021](https://openaccess.thecvf.com/content/WACV2021/html/Karkkainen_FairFace_Face_Attribute_Dataset_for_Balanced_Race_Gender_and_Age_WACV_2021_paper.html)
- [Kho mã FairFace](https://github.com/joojs/fairface)

### 2.2. Điểm chạm

| Thứ tự | Mã | Tên |
|---:|---|---|
| 1 | `TP-ENTRANCE` | Cửa vào |
| 2 | `TP-DISPLAY` | Khu trưng bày sản phẩm |
| 3 | `TP-CONSULT` | Khu tư vấn |
| 4 | `TP-CHECKOUT` | Quầy thanh toán |

Hệ thống chỉ có một cửa hàng và không sinh dữ liệu chi nhánh.

### 2.3. Sản phẩm và đơn hàng

- 6 nhóm sản phẩm.
- 24 sản phẩm.
- 3 đơn hàng được tạo khi nạp dữ liệu ban đầu.
- Dịch vụ mô phỏng tạo thêm đơn hàng cho một phần lượt ghé thăm.
- Dòng đơn giữ mã, tên và giá sản phẩm tại thời điểm mua.

## 3. Dịch vụ mô phỏng

Dịch vụ chạy tại <http://127.0.0.1:8002>. Khi nhận yêu cầu tạo dữ liệu, dịch vụ thực hiện:

1. Đăng nhập vào máy chủ nghiệp vụ.
2. Kiểm tra có đúng 100 khách hàng.
3. Đọc danh sách điểm chạm và sản phẩm.
4. Tạo ít nhất một lượt ghé thăm cho mỗi khách hàng.
5. Tạo thêm lượt thứ hai cho mỗi khách hàng thứ tư.
6. Chọn từ hai đến bốn điểm chạm cho mỗi lượt.
7. Tạo nhãn biểu cảm và độ tin cậy bằng hạt giống cố định.
8. Tạo 12 trường hợp lỗi có kiểm soát.
9. Gửi sự kiện theo lô qua máy chủ nghiệp vụ.
10. Tạo đơn hàng và liên kết với khách hàng, lượt ghé thăm phù hợp.

Tham số `customer_count` bị khóa ở 100. Dịch vụ không ghi trực tiếp vào PostgreSQL.

## 4. Cách chạy lại

Từ thư mục `SYSTEM`:

```bash
docker compose up -d --build
make demo-portraits
make demo-seed
make demo-simulate
```

Tài khoản:

```text
manager@example.com
demo1234
```

Nếu cơ sở dữ liệu đã có lần mô phỏng trước, không chạy lặp lại khi chưa kiểm tra dữ liệu. Lần chạy lặp sẽ tạo thêm lượt ghé thăm và đơn hàng.

## 5. Kịch bản trình diễn trên giao diện

### Bước 1. Kiểm tra tổng quan

Mở <http://127.0.0.1:8080/dashboard>.

Kết quả cần thấy:

- 100 khách hàng.
- 24 sản phẩm.
- 125 lượt ghé thăm sau lần chạy chính.
- Thẻ phân bố nhãn theo điểm chạm.

### Bước 2. Theo dõi cùng thời gian và cùng khu vực

Tại trang tổng quan, chọn thẻ **Biến thiên theo thời gian và khu vực**.

1. Chọn một điểm chạm.
2. Chọn ngày.
3. Chọn khoảng 5, 15, 30 hoặc 60 phút.

Kết quả cần thấy là số quan sát của bảy nhãn tại đúng khu vực và ngày đã chọn, được sắp xếp theo các mốc thời gian.

### Bước 3. Kiểm tra khách hàng và lịch sử mua hàng

Mở trang **Khách hàng**, tìm `CUS-DEMO-001` và mở hồ sơ.

Kết quả cần thấy:

- Ảnh đại diện.
- Thông tin CRM giả lập.
- Ba đơn hàng trong lần dữ liệu hiện tại.
- Chi tiết sản phẩm trong từng đơn.

### Bước 4. Kiểm tra sản phẩm và đơn hàng

- Trang **Sản phẩm** hiển thị 24 sản phẩm thuộc 6 nhóm.
- Trang **Mua hàng** hiển thị 93 đơn sau lần chạy chính.
- Mở chi tiết một đơn để xem sản phẩm, số lượng, đơn giá và thành tiền.

### Bước 5. Kiểm tra hành trình

Mở trang **Theo dõi hành trình** và chọn một lượt ghé thăm.

Kết quả cần thấy:

- Danh sách 100 khách hàng có hành trình.
- Tổng 125 lượt ghé thăm.
- Sơ đồ các điểm chạm theo thứ tự thời gian.
- Nhãn biểu cảm và độ tin cậy tại từng điểm.
- Dấu hiệu cho biết dữ liệu do mô phỏng tạo.

### Bước 6. Kiểm tra báo cáo

Mở trang **Phân tích biểu cảm** và lần lượt xem:

- Phân bố tại điểm chạm.
- Thay đổi giữa các điểm chạm.
- Chất lượng dữ liệu.

Kết quả chất lượng dữ liệu của lần chạy chính:

- 385 quan sát hợp lệ.
- 8 quan sát không có khuôn mặt.
- 4 ảnh không hợp lệ.
- Tổng 397 quan sát.

## 6. Kết quả lần chạy chính

| Dữ liệu | Số lượng |
|---|---:|
| Khách hàng | 100 |
| Nhóm sản phẩm | 6 |
| Sản phẩm | 24 |
| Điểm chạm | 4 |
| Lượt ghé thăm | 125 |
| Quan sát | 397 |
| Đơn hàng | 93 |
| Dòng sản phẩm trong đơn | 232 |

- Mã lần chạy: `SIM-20260923083712-be107c`.
- Hạt giống: `20260923`.
- Đơn hàng mới do mô phỏng tạo: 90.

## 7. Giới hạn phải nêu khi trình bày

- Chưa có camera vật lý.
- Nhãn biểu cảm trong demo là nhãn giả lập.
- Cấu hình mô hình thật chưa được kiểm chứng đầy đủ trong Docker.
- Không dùng biểu đồ để kết luận trạng thái tâm lý hoặc mức hài lòng.
- Không dùng 100 ảnh đại diện để tuyên bố độ chính xác nhận dạng khách hàng.
- Không có dữ liệu nhiều chi nhánh.
