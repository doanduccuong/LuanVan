# Kế hoạch Chương 5 – Đánh giá thực nghiệm

## 1. Nguyên tắc

Chương 5 chỉ được viết sau khi đặc tả kỹ thuật đã được duyệt, mã đã chạy và đầu ra đã được kiểm tra. Mọi con số trong bảng và biểu đồ phải được sinh từ kết quả thô của luận văn; không ghép số liệu lấy từ các bài báo khác nhau.

Mỗi nhóm thực nghiệm phải nêu:

- Câu hỏi thực nghiệm.
- Tập dữ liệu và lý do sử dụng.
- Mô hình, trọng số và cấu hình.
- Môi trường phần cứng, phần mềm.
- Chỉ số và cách tính.
- Kết quả, phân tích sai số và giới hạn.

## 2. Cấu trúc Chương 5

### 5.1. Môi trường và giao thức thực nghiệm

- Cấu hình máy tính và hệ điều hành.
- Phiên bản Python, thư viện và mã nguồn.
- Quy tắc khởi động mô hình trước khi đo.
- Số lần chạy và cách tổng hợp.
- Cách lưu kết quả thô và tái tạo bảng, biểu đồ.

**Bảng 5.1:** Cấu hình môi trường thực nghiệm.

### 5.2. So sánh các phương pháp phát hiện khuôn mặt

#### 5.2.1. Tập dữ liệu và lý do sử dụng

Trình bày phần kiểm định WIDER FACE, nhãn khung bao và ba nhóm Easy, Medium, Hard. Giải thích bằng tiếng Việt; chỉ giữ tên riêng chính thức của tập dữ liệu và các nhóm.

#### 5.2.2. Mô hình và thiết lập

Nêu đúng một mô hình đại diện cho Haar Cascade, MTCNN và RetinaFace cùng toàn bộ tham số ảnh hưởng đến kết quả.

#### 5.2.3. Chỉ số đánh giá

- Độ chính xác trung bình trên Easy, Medium, Hard.
- Độ trễ trung vị và phân vị thứ 95.
- Số ảnh xử lý trong một giây.
- Tỷ lệ ảnh không phát hiện được khuôn mặt nếu phục vụ phân tích lỗi.

#### 5.2.4. Kết quả và nhận xét

Nhận xét phải bắt đầu từ bằng chứng, chẳng hạn: “Từ kết quả thực nghiệm có thể thấy…”. Chỉ kết luận trong phạm vi tập dữ liệu và cấu hình đã đo.

**Bảng và hình:**

- Bảng 5.2. Kết quả so sánh ba phương pháp phát hiện khuôn mặt.
- Hình 5.1. So sánh độ chính xác trung bình theo mức độ khó.
- Hình 5.2. So sánh thời gian xử lý.
- Hình 5.3. Một số trường hợp phát hiện đúng, bỏ sót và phát hiện sai.

Mã và kết quả được quản lý trong `COMPARE_FACE_DETECTION/`.

### 5.3. Kiểm chứng phương pháp phân tích đa điểm chạm

#### 5.3.1. Kiểm chứng xử lý sự kiện

- Ảnh hợp lệ, không có khuôn mặt, nhiều khuôn mặt và ảnh lỗi.
- Mã hành trình thiếu.
- Điểm chạm thiếu.
- Sự kiện trùng hoặc sai thứ tự.

#### 5.3.2. Kết quả phân tích đa điểm chạm

Chỉ trình bày khi có mã hành trình đáng tin cậy:

- Phân bố nhãn tại từng điểm chạm.
- Ma trận chuyển tiếp cho từng cặp điểm chạm liên tiếp.
- Tỷ lệ thiếu dữ liệu và các trạng thái không hợp lệ.

Không tạo điểm cảm xúc chung, điểm đỉnh–cuối hoặc mức hài lòng.

**Bảng và hình:**

- Bảng 5.3. Kết quả kiểm thử các tình huống xử lý.
- Bảng 5.4. Chất lượng dữ liệu hành trình.
- Hình 5.4. Phân bố biểu cảm theo điểm chạm.
- Hình 5.5. Bản đồ nhiệt ma trận chuyển tiếp.
- Hình 5.6. Tỷ lệ dữ liệu thiếu hoặc không hợp lệ.

Mã và kết quả sẽ được quản lý trong `PROPOSED_METHOD/` sau khi đặc tả được duyệt.

### 5.4. Thảo luận kết quả và giới hạn

- Lựa chọn phương pháp dựa trên các tiêu chí đã xác định trước.
- Phân tích đánh đổi giữa chất lượng, độ trễ và tài nguyên.
- Nêu sai số lan truyền từ phát hiện khuôn mặt sang phân loại biểu cảm.
- Nêu giới hạn tập dữ liệu, môi trường kiểm thử, mã hành trình và quyền riêng tư.
- Không lặp lại toàn bộ số liệu trong bảng.

Không có mục “Kết luận chương”.

## 3. Quy tắc đối với hình và biểu đồ

- Sơ đồ mô tả phương pháp thuộc Chương 3; biểu đồ có số liệu thực nghiệm thuộc Chương 5.
- Biểu đồ phải được sinh tự động từ CSV hoặc JSON của lần chạy đã khóa.
- Không nhập số liệu hoặc chỉnh sửa cột bằng tay.
- Xuất PDF hoặc SVG để chèn LaTeX và PNG để kiểm tra nhanh.
- Dùng thống nhất màu, thứ tự lớp biểu cảm, nhãn tiếng Việt và đơn vị.
- Mỗi hình phải được dẫn và giải thích trong nội dung.
- Hình kế thừa hoặc dựng lại từ nguồn khác phải có trích dẫn trong chú thích.

## 4. Trình tự thực hiện

1. Duyệt `COMPARE_FACE_DETECTION/TECH_SPEC.md` và kiểm tra đầu ra hiện có.
2. Xác định rõ mô hình phân loại biểu cảm, nguồn trọng số và tiền xử lý; chỉ kiểm thử tích hợp, chưa so sánh nhiều mô hình.
3. Duyệt `PROPOSED_METHOD/TECH_SPEC.md`.
4. Viết mã phương pháp đề xuất và tạo đầu ra kiểm chứng.
5. Sinh toàn bộ bảng, hình và biểu đồ bằng mã.
6. Đối chiếu số liệu giữa đầu ra thô, bảng Markdown và bảng LaTeX.
7. Chỉ sau đó mới viết Chương 2, Chương 3 và Chương 5 theo kết quả đã có.

## 5. Tiêu chí hoàn thành

- Mỗi số liệu truy ngược được đến tệp kết quả thô và cấu hình chạy.
- Các phương pháp trong cùng bảng được chạy trong điều kiện so sánh hợp lệ.
- Mọi biểu đồ được tái tạo bằng một lệnh.
- Nhận xét không vượt quá phạm vi dữ liệu.
- Có cả trường hợp thành công và trường hợp thất bại.
- Mục lục, danh mục hình, danh mục bảng và tài liệu tham khảo được sinh đúng sau khi biên dịch.
