# Kế hoạch cập nhật luận văn đã thống nhất

Tài liệu này ghi lại phạm vi chỉnh sửa đã được chấp nhận. Nguyên tắc chung là nội dung luận văn phải phản ánh đúng phương pháp, mã nguồn và dữ liệu đã kiểm nghiệm; không trình bày ý tưởng mở rộng như chức năng đã triển khai.

## 1. Trọng tâm chỉnh sửa

### Chương 2 — Cơ sở lý thuyết

- Trình bày một điểm chạm có thể tạo nhiều quan sát tại các thời điểm khác nhau.
- Tổ chức hành trình theo hai cấp: các quan sát trong từng điểm chạm và chuỗi điểm chạm của một lần mua sắm.
- Hình minh họa phải thể hiện nhiều quan sát trong từng khu vực, không gán cố định một biểu cảm cho mỗi điểm chạm.
- Không dùng khung lý thuyết hành trình khách hàng để suy ra các quy tắc kỹ thuật mà nguồn tài liệu không đề cập.

### Chương 3 — Phương pháp đề xuất

- Một khung hình có thể chứa nhiều khuôn mặt; số lượng khuôn mặt không phải điều kiện loại bỏ ảnh.
- Mỗi khuôn mặt được cắt và xử lý độc lập qua hai nhánh: phân loại biểu cảm và tạo đặc trưng nhận dạng.
- Một sự kiện thu nhận có thể tạo từ không đến nhiều quan sát, mỗi quan sát gắn với một khuôn mặt và khung bao tương ứng.
- Đầu ra được tổ chức thành ba mức: quan sát, điểm chạm và lần mua sắm.
- Bản ghi chưa xác định khách hàng vẫn có thể tham gia thống kê theo khu vực nếu kết quả biểu cảm hợp lệ, nhưng không được tự động ghép thành chuỗi cá nhân.
- Chương này chỉ trình bày phương pháp và quy tắc xử lý, không mô tả code, container hoặc trạng thái triển khai.

### Chương 4 — Xây dựng và phát triển hệ thống

- Trình bày cấu trúc chức năng, kiến trúc thành phần, luồng dữ liệu và giao tiếp theo đúng hệ thống đã xây dựng.
- Bốn thành phần phần mềm chính gồm giao diện CRM, máy chủ nghiệp vụ, dịch vụ xử lý ảnh và cơ sở dữ liệu. Nguồn thu nhận ảnh là tác nhân cung cấp dữ liệu, không phải một thành phần xử lý ngang hàng.
- Giao diện sử dụng React và TypeScript; Nginx phục vụ tệp tĩnh và chuyển tiếp yêu cầu đến API.
- Máy chủ FastAPI là trung tâm điều phối quy tắc nghiệp vụ. Dịch vụ xử lý ảnh không truy cập trực tiếp CRM hoặc PostgreSQL.
- Xác thực sử dụng JWT lưu trong cookie. PostgreSQL/pgvector lưu véc-tơ khuôn mặt; mã nguồn hiện thực hiện phép tính khoảng cách cosine tại máy chủ nghiệp vụ.
- Ảnh chụp giao diện được giữ để chỉ rõ nơi người dùng thực hiện các chức năng đã xây dựng. Sơ đồ chỉ bổ sung cho kiến trúc và luồng xử lý, không thay thế bằng chứng giao diện.

### Chương 5 — Đánh giá thực nghiệm

- Trình bày rõ cách xây dựng dữ liệu vì chưa có hệ thống camera và dữ liệu bán hàng thực tế.
- Nguồn ảnh khuôn mặt duy nhất là FairFace. Khung quan sát nhiều người được ghép từ hai bản ghi FairFace với thay đổi vị trí, kích thước và độ sáng.
- Thực nghiệm sử dụng 100 khách hàng, 120 sự kiện xử lý ảnh và tạo 236 quan sát từ luồng xử lý ảnh.
- Sau khi nạp thêm tải nghiệp vụ, cơ sở dữ liệu có 529 sự kiện và 633 quan sát.
- Chương 5 dùng số liệu, kiểm thử và ảnh chụp sau lần chạy để chứng minh các thành phần phần mềm phối hợp đúng trong điều kiện đã xây dựng.
- Giới hạn phải nêu rõ: chưa kết nối camera vật lý, chưa đánh giá độ chính xác FER, chưa kiểm nghiệm nhận dạng qua nhiều ngày và chưa theo dõi người chưa xác định qua nhiều khung hình.

## 2. Quy tắc diễn giải kết quả biểu cảm

- Giữ riêng bảy nhãn FER: `Angry`, `Disgust`, `Fear`, `Happy`, `Sad`, `Surprise` và `Neutral`.
- Không quy đổi các nhãn thành thang điểm tích cực--trung tính--tiêu cực.
- Không dùng `Happy` như một phép đo mức độ hài lòng.
- Không dùng sự thay đổi nhãn để kết luận một khu vực làm trải nghiệm tốt lên hoặc xấu đi.
- Báo cáo chỉ mô tả số lượng, tỷ lệ và cặp thay đổi của các nhãn được mô hình ghi nhận.
- Kết luận về mức độ hài lòng cần dữ liệu đối chiếu độc lập như khảo sát, phản hồi hoặc chỉ báo nghiệp vụ đã được kiểm chứng.

## 3. Nội dung không đưa vào phần hệ thống đã xây dựng

Các nội dung sau chưa được triển khai hoặc chưa được kiểm chứng, vì vậy không được mô tả như kết quả của đề tài:

- Đường cong điểm cảm xúc hoặc chỉ số `Positive Rate`.
- Cảnh báo thời gian thực qua WebSocket hoặc Server-Sent Events.
- Cảnh báo dựa trên chuỗi biểu cảm bị quy ước là tiêu cực.
- Kho mẫu khuôn mặt ẩn danh và theo dõi một người chưa đăng ký qua nhiều phiên.
- Vai trò Marketing/CX và các ca sử dụng chưa có trong hệ thống.
- Số liệu, tỷ lệ chuyển đổi hoặc xu hướng theo giờ không được tạo từ lần thực nghiệm hiện tại.

Những nội dung này chỉ có thể được nêu ở phần hướng phát triển, kèm điều kiện kỹ thuật, dữ liệu kiểm chứng và yêu cầu bảo vệ dữ liệu cá nhân.

## 4. Ranh giới giữa các chương

- Chương 2 trả lời: cơ sở lý thuyết nào được sử dụng?
- Chương 3 trả lời: phương pháp xử lý dữ liệu và hình thành kết quả như thế nào?
- Chương 4 trả lời: hệ thống đã được xây dựng bằng các thành phần và chức năng nào?
- Chương 5 trả lời: dữ liệu thử nghiệm được xây dựng ra sao, hệ thống được kiểm nghiệm như thế nào và kết quả chứng minh được điều gì?

## 5. Trạng thái thực hiện

- Đã cập nhật Mục 2.4 để thể hiện nhiều quan sát trong từng điểm chạm.
- Đã bổ sung ba mức đầu ra của phương pháp trong Chương 3.
- Chương 4 đã bám theo kiến trúc và chức năng hiện có; không bổ sung chức năng chưa triển khai.
- Chương 5 đã sử dụng khung quan sát nhiều người và số liệu 633 quan sát sau thực nghiệm tích hợp.
- Đã loại bỏ khỏi kế hoạch các đề xuất quy đổi biểu cảm thành tích cực--tiêu cực, cảnh báo thời gian thực và theo dõi định danh ẩn danh đa phiên.
