# Tổng hợp cập nhật luận văn

Tài liệu này tổng hợp các thay đổi gần đây đối với Chương 2 và Chương 3 của luận văn.

## 1. Điều chỉnh cách dẫn khung hành trình khách hàng

**Tệp:** `Chuong/3_Phuong_an_de_xuat.tex`  
**Vị trí:** Mục 3.1.1 — Bài toán cần giải quyết

- Loại bỏ câu diễn giải trực tiếp rằng khung của Halvorsrud, Kvale và Følstad yêu cầu giữ lại vị trí và thứ tự của từng tương tác.
- Thay bằng dẫn chiếu tới cơ sở phân tích hành trình khách hàng đã trình bày tại Mục 2.4.
- Làm rõ đóng góp của luận văn là liên kết các kết quả nhận dạng biểu cảm theo khách hàng và lượt ghé thăm, sau đó sắp xếp chúng theo thời gian.
- Tránh tạo cảm giác luận văn áp dụng nguyên vẹn khung lý thuyết của Halvorsrud, Kvale và Følstad như một mô hình kỹ thuật.

## 2. Mở rộng cách biểu diễn biểu cảm tại điểm chạm

**Tệp:** `Chuong/2_Nen_tang_ly_thuyet_va_cong_nghe.tex`  
**Vị trí:** Mục 2.4.1 và 2.4.2

- Không còn giả định mỗi điểm chạm chỉ có một nhãn biểu cảm duy nhất.
- Mỗi điểm chạm có thể tạo ra nhiều quan sát tại các thời điểm khác nhau.
- Hành trình được tổ chức theo hai cấp:
  1. Các quan sát bên trong từng điểm chạm.
  2. Chuỗi điểm chạm của toàn bộ lượt ghé thăm.
- Bổ sung hai mức phân tích:
  - Biến thiên biểu cảm bên trong cùng một khu vực.
  - Sự thay đổi biểu cảm giữa các điểm chạm trong hành trình.
- Làm rõ rằng phân tích theo các phân vùng vật lý nhỏ hơn cần có mã phân vùng riêng. Trong cấu hình hiện tại, điểm chạm vẫn là đơn vị không gian nhỏ nhất.

## 3. Thiết kế lại Hình 2.9

**Tệp:** `Chuong/2_Nen_tang_ly_thuyet_va_cong_nghe.tex`  
**Nhãn LaTeX:** `fig:touchpoint_sequence`

- Thay sơ đồ chỉ có một biểu cảm tại mỗi điểm chạm bằng sơ đồ có nhiều quan sát theo thời gian.
- Mỗi điểm chạm được biểu diễn dưới dạng một thẻ riêng gồm:
  - Tên điểm chạm.
  - Trục thời gian nội bộ.
  - Các mốc quan sát.
  - Nhãn biểu cảm tại từng mốc.
- Bốn thẻ được nối theo thứ tự: Tiếp đón, Tư vấn, Trải nghiệm và Thanh toán.
- Sử dụng tông xám để phù hợp với tài liệu học thuật và vẫn rõ khi in đen trắng.
- Đổi chú thích hình thành:

> Các quan sát biểu cảm trong từng điểm chạm của một hành trình

## 4. Điều chỉnh đầu vào và đầu ra của phương pháp

**Tệp:** `Chuong/3_Phuong_an_de_xuat.tex`  
**Vị trí:** Mục 3.1.2 — Đầu vào và đầu ra

- Làm rõ camera có thể tạo nhiều ảnh tại cùng một điểm chạm ở các thời điểm khác nhau.
- Thời điểm ghi nhận được dùng để sắp xếp:
  - Nhiều quan sát trong cùng một khu vực.
  - Các quan sát trong toàn bộ lượt ghé thăm.
- Chuyển đầu ra của phương pháp từ hai mức thành ba mức:
  1. **Mức quan sát:** bản ghi gồm điểm chạm, thời gian, nhãn biểu cảm, độ tin cậy và kết quả nhận dạng khách hàng.
  2. **Mức điểm chạm:** tập hợp các quan sát của cùng khách hàng tại một khu vực.
  3. **Mức hành trình:** chuỗi các bản ghi thuộc cùng khách hàng và lượt ghé thăm, được sắp xếp theo thời gian.

## 5. Bổ sung phân tích chi tiết tại từng điểm chạm

**Tệp:** `Chuong/3_Phuong_an_de_xuat.tex`  
**Vị trí:** Mục 3.4.1 — Phân bố biểu cảm tại từng điểm chạm

- Không rút gọn ngay một điểm chạm thành một nhãn biểu cảm duy nhất.
- Giữ các bản ghi tại cùng điểm chạm theo thứ tự thời gian để xem biểu cảm được duy trì hay thay đổi.
- Cho phép nhóm dữ liệu theo các khoảng thời gian thống nhất để theo dõi biến thiên phân bố biểu cảm tại cùng khu vực.
- Ghi rõ phân tích theo phân vùng vật lý là hướng mở rộng và cần bổ sung mã phân vùng vào mỗi quan sát.

## 6. Tổ chức lại luồng xử lý thành ba cụm

**Tệp:** `Chuong/3_Phuong_an_de_xuat.tex`  
**Vị trí:** Mục 3.1.3 — Luồng xử lý tổng thể

Luồng tổng thể được tổ chức lại thành ba cụm độc lập:

```text
Cụm dữ liệu đầu vào → Cụm xử lý → Cụm dữ liệu đầu ra
```

### Cụm dữ liệu đầu vào

- Ảnh tại điểm chạm.
- Mã điểm chạm.
- Thời điểm ghi nhận.
- Mẫu khuôn mặt tham chiếu.
- Trạng thái lượt ghé thăm.

### Cụm xử lý

1. Phát hiện và chuẩn hóa khuôn mặt.
2. Phân loại biểu cảm.
3. Nhận dạng khách hàng.
4. Tạo và liên kết bản ghi.
5. Phân tích đa điểm chạm.

### Cụm dữ liệu đầu ra

- Nhãn biểu cảm và độ tin cậy.
- Kết quả nhận dạng khách hàng.
- Bản ghi tại điểm chạm.
- Chuỗi quan sát theo thời gian.
- Kết quả phân tích hành trình.

## 7. Thiết kế lại Bảng 3.1

**Tệp:** `Chuong/3_Phuong_an_de_xuat.tex`  
**Nhãn LaTeX:** `tab:method_stages`

- Đổi tên bảng thành **Thành phần và vai trò của ba cụm trong phương pháp**.
- Thay cấu trúc liệt kê đầu vào và đầu ra của từng công đoạn bằng ba dòng tương ứng với ba cụm.
- Các cột mới gồm:
  - Cụm.
  - Thành phần.
  - Vai trò.
- Giảm sự trùng lặp giữa Bảng 3.1 và sơ đồ luồng xử lý tổng thể.

## 8. Nhận diện nhiều khách hàng trong cùng một ảnh

**Tệp:** `Chuong/3_Phuong_an_de_xuat.tex`  
**Vị trí:** Mục 3.1.1, 3.2.1, 3.2.2 và 3.2.3

- Thay giả định chỉ chọn một khuôn mặt trong ảnh bằng quy trình phát hiện tất cả vùng khuôn mặt hợp lệ.
- Mỗi vùng khuôn mặt được căn chỉnh, phân loại biểu cảm và đối sánh danh tính độc lập.
- Kết quả biểu cảm chỉ được gắn với danh tính suy ra từ chính vùng khuôn mặt tương ứng.
- Khuôn mặt không đạt ngưỡng đối sánh được giữ ở trạng thái không xác định.
- Một ảnh có thể tạo nhiều bản ghi quan sát, tương ứng với nhiều khách hàng hoặc khuôn mặt được phát hiện.
- Bổ sung vị trí khuôn mặt vào thông tin bản ghi để phân biệt các kết quả được tạo từ cùng một ảnh.

### Lưu trải nghiệm của khách hàng không xác định

> Ghi chú đề xuất, chưa áp dụng vào nội dung LaTeX hoặc mã nguồn hiện tại.

- Mọi quan sát khuôn mặt và biểu cảm hợp lệ đều được lưu, kể cả khi khách hàng chưa đăng ký hoặc không đối sánh được danh tính.
- Khách hàng chưa có hồ sơ CRM được cấp định danh ẩn danh khi đặc trưng khuôn mặt đủ chất lượng.
- Định danh ẩn danh được dùng để nhận biết khách quay lại, tạo các lượt ghé thăm và truy xuất lịch sử điểm chạm, thời gian, biểu cảm.
- Nếu chất lượng đặc trưng hoặc điểm đối sánh chưa đủ, bản ghi được giữ ở trạng thái chưa liên kết nhưng vẫn tham gia thống kê tổng hợp.
- Định danh ẩn danh không tự động được chuyển thành hồ sơ CRM; thao tác liên kết cần quy trình xác nhận và sự đồng ý phù hợp.
- Dữ liệu khuôn mặt ẩn danh vẫn cần giới hạn quyền truy cập và thời hạn lưu giữ vì có khả năng liên kết một người qua thời gian.
- Lưu ý triển khai: mô hình dữ liệu và API hiện tại chưa có thực thể định danh ẩn danh riêng; phần mã nguồn cần được mở rộng để thực hiện đúng phương pháp này.

## 9. Trạng thái kiểm tra

- Mã LaTeX/TikZ đã được kiểm tra về sự cân bằng của các môi trường chính.
- Chưa thể biên dịch lại `LuanVan.pdf` vì MiKTeX trên máy yêu cầu hoàn tất thiết lập ban đầu.
- Sau khi MiKTeX được thiết lập, cần biên dịch lại toàn bộ luận văn và kiểm tra:
  - Kích thước và khả năng đọc của Hình 2.9.
  - Bố cục sơ đồ ba cụm tại Mục 3.1.3.
  - Độ rộng và ngắt dòng của Bảng 3.1.
  - Các tham chiếu chéo, danh mục hình và danh mục bảng.
