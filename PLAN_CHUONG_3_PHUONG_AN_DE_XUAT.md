# Kế hoạch Chương 3 – Phương pháp đề xuất

## 1. Phương pháp được đề xuất

Chương 3 tập trung vào một nội dung duy nhất:

> Liên kết kết quả nhận dạng biểu cảm tại nhiều điểm chạm với đúng khách hàng và đúng lượt ghé thăm, từ đó hình thành chuỗi biểu cảm theo thời gian và tạo dữ liệu phân tích đa điểm chạm.

Luận văn không đề xuất một kiến trúc học sâu mới. Bộ phát hiện khuôn mặt, bộ phân loại biểu cảm và mô hình nhận dạng khách hàng là các thành phần được sử dụng để tạo đầu vào cho phương pháp. Nội dung đóng góp nằm ở cách phối hợp các kết quả rời rạc thành một hành trình có thứ tự.

## 2. Ranh giới với các chương khác

- **Chương 2:** cơ sở lý thuyết về phát hiện khuôn mặt, FER, nhận dạng khuôn mặt, hành trình khách hàng và điểm chạm.
- **Chương 3:** đầu vào, đầu ra, quy tắc liên kết quan sát và cách phân tích hành trình.
- **Chương 4:** mô hình cụ thể, kiến trúc phần mềm, cơ sở dữ liệu, API, mã trạng thái, chức năng CRM và giao diện.
- **Chương 5:** dữ liệu thử nghiệm, cấu hình đo, chỉ số đánh giá và kết quả thực nghiệm.

Chương 3 không trình bày CRUD của CRM, hợp đồng JSON, cấu trúc bảng dữ liệu, công nghệ backend/frontend hoặc ảnh giao diện.

## 3. Cấu trúc Chương 3

### 3.1. Tổng quan phương pháp đề xuất

#### 3.1.1. Bài toán cần giải quyết

- Mỗi camera tạo các quan sát độc lập.
- Một kết quả FER đơn lẻ chưa tạo thành hành trình.
- Cần xác định khách hàng, phân biệt từng lượt đến cửa hàng và giữ thứ tự các điểm chạm.
- Nêu rõ phương pháp không tạo mô hình học sâu mới.

#### 3.1.2. Đầu vào và đầu ra

- Đầu vào: ảnh, mã điểm chạm và thời gian ghi nhận.
- Đầu ra mức điểm chạm: nhãn biểu cảm, độ tin cậy và kết quả nhận dạng khách hàng.
- Đầu ra mức hành trình: chuỗi các quan sát thuộc cùng khách hàng và cùng lượt ghé thăm.

#### 3.1.3. Luồng xử lý tổng thể

Luồng trình bày:

```text
Ảnh + điểm chạm + thời gian
            ↓
Phát hiện và chuẩn hóa khuôn mặt
            ↓
  Phân loại biểu cảm ─┐
                      ├─→ Bản ghi điểm chạm
 Nhận dạng khách hàng ┘
            ↓
Xác định lượt ghé thăm
            ↓
Liên kết và sắp xếp các bản ghi
            ↓
Phân tích kết quả đa điểm chạm
```

**Hình 3.1:** Luồng xử lý của phương pháp đề xuất.

**Bảng 3.1:** Đầu vào và đầu ra của từng công đoạn.

### 3.2. Tạo bản ghi biểu cảm tại một điểm chạm

#### 3.2.1. Phát hiện và chuẩn hóa khuôn mặt

- Phát hiện vùng khuôn mặt hợp lệ.
- Căn chỉnh bằng điểm mốc nếu mô hình hỗ trợ.
- Không tự chọn một người trong ảnh nhiều khuôn mặt nếu chưa có quy tắc đã kiểm chứng.
- Chỉ mô tả vai trò của công đoạn; tên mô hình và tham số cụ thể chuyển sang Chương 4.

#### 3.2.2. Phân loại biểu cảm và nhận dạng khách hàng

- Hai nhiệm vụ sử dụng chung vùng khuôn mặt nhưng có đầu ra độc lập.
- Nhánh FER trả nhãn trong bảy lớp và độ tin cậy.
- Nhánh nhận dạng trả mã khách hàng đã đăng ký hoặc trạng thái không xác định.
- Không sử dụng độ tin cậy FER để quyết định danh tính.
- Không chuyển các lớp biểu cảm thành điểm tích cực–tiêu cực.

**Hình 3.2:** Hai nhiệm vụ được thực hiện trên cùng vùng khuôn mặt.

#### 3.2.3. Thông tin của bản ghi điểm chạm

Trình bày ở mức logic:

- Điểm chạm.
- Thời điểm.
- Nhãn biểu cảm.
- Độ tin cậy.
- Kết quả nhận dạng khách hàng.
- Phiên bản cấu hình mô hình.

Không sử dụng tên cột, kiểu dữ liệu hoặc đoạn JSON trong Chương 3.

**Bảng 3.2:** Thông tin của một bản ghi tại điểm chạm.

### 3.3. Liên kết các bản ghi thành hành trình đa điểm chạm

#### 3.3.1. Xác định khách hàng đã đăng ký

- So sánh đặc trưng ảnh truy vấn với mẫu tham chiếu.
- Chỉ chấp nhận kết quả đạt ngưỡng đã được kiểm chứng.
- Nếu chưa đủ tin cậy, trả về trạng thái không xác định.

#### 3.3.2. Xác định lượt ghé thăm

- Không nhóm toàn bộ dữ liệu chỉ theo mã khách hàng.
- Kiểm tra lượt ghé thăm đang hoạt động.
- Tạo lượt mới khi chưa có hoặc khi đã vượt ngưỡng ngắt lượt.
- Ngưỡng ngắt lượt là tham số cần xác định từ nghiệp vụ và dữ liệu thử nghiệm; không tự đặt một khoảng thời gian trong báo cáo.

#### 3.3.3. Gắn và sắp xếp bản ghi

- Gắn bản ghi vào đúng lượt ghé thăm.
- Sắp xếp theo thời gian ảnh được ghi nhận.
- Không sử dụng nhãn biểu cảm để xác định hai bản ghi có cùng khách hàng hay không.

**Hình 3.3:** Liên kết các bản ghi vào cùng một lượt ghé thăm.

#### 3.3.4. Xử lý dữ liệu thiếu và khách hàng không xác định

- Không nội suy biểu cảm tại điểm chạm bị thiếu.
- Khách hàng không xác định chỉ tham gia thống kê tại điểm chạm.
- Không tự động tạo hồ sơ hoặc hành trình cá nhân.
- Bản ghi xung đột thứ tự không tham gia phân tích thay đổi giữa hai điểm chạm.

**Bảng 3.3:** Cách xử lý các trường hợp liên kết hành trình.

### 3.4. Phân tích kết quả theo hành trình

#### 3.4.1. Phân bố biểu cảm tại từng điểm chạm

- Đếm số bản ghi hợp lệ của từng lớp.
- Tính tỷ lệ trên tổng số bản ghi hợp lệ tại cùng điểm chạm.
- Luôn trình bày đồng thời số lượng mẫu và tỷ lệ.
- Đây là thống kê mô tả, không phải phép đo mức độ hài lòng.

#### 3.4.2. Sự thay đổi giữa các điểm chạm liên tiếp

- Chỉ sử dụng lượt ghé thăm có dữ liệu hợp lệ tại cả hai điểm.
- Mỗi lượt đóng góp một cặp nhãn trước–sau.
- Tổng hợp bằng bảng chéo cho từng cặp điểm chạm.
- Không diễn giải bảng như quan hệ nhân quả hoặc mô hình chuyển trạng thái tâm lý.

#### 3.4.3. Nguyên tắc diễn giải

- Không tính điểm cảm xúc chung.
- Không tính biểu cảm trung bình.
- Không quy đổi bảy lớp thành thang tích cực–tiêu cực.
- Không ghép dữ liệu của hai khách hàng hoặc hai lượt ghé thăm khác nhau.
- Luôn báo cáo số dữ liệu hợp lệ và dữ liệu thiếu.

### 3.5. Phạm vi và giới hạn

- Sai số phát hiện khuôn mặt ảnh hưởng đến hai nhiệm vụ phía sau.
- Sai số nhận dạng khách hàng có thể làm sai hành trình.
- FER chỉ mô tả biểu hiện khuôn mặt quan sát được.
- Liên kết cá nhân chỉ áp dụng cho khách hàng đã đăng ký và đồng ý sử dụng dữ liệu khuôn mặt.
- Thiếu dữ liệu không được thay bằng nhãn giả định.

## 4. Hình, bảng và tài liệu tham khảo

### 4.1. Hình và bảng

Chương 3 dự kiến có:

- 3 hình mô tả phương pháp.
- 3 bảng mô tả đầu vào, bản ghi điểm chạm và quy tắc liên kết.

Hình phải được giải thích trong nội dung trước hoặc ngay sau khi xuất hiện. Bảng không chứa số liệu minh họa dễ bị hiểu nhầm là kết quả thực nghiệm.

### 4.2. Trích dẫn

- Mọi nội dung lấy từ nghiên cứu, tiêu chuẩn, báo cáo hoặc mã nguồn phải có trích dẫn ngay tại câu sử dụng.
- Không trích dẫn nguồn cho một kết luận mà nguồn đó không trực tiếp hỗ trợ.
- Những quy tắc do luận văn đề xuất phải được ghi rõ là quy tắc của phương pháp, không trình bày như kết luận của nghiên cứu trước.
- Không đưa số liệu định lượng, ngưỡng hoặc cấu hình nếu chưa có nguồn hoặc kết quả thực nghiệm.

## 5. Điều kiện trước khi hoàn thiện chương

1. Đặc tả kỹ thuật phải thống nhất với cơ chế nhận dạng khách hàng và lượt ghé thăm.
2. Mã xử lý phải tạo được bản ghi điểm chạm và chuỗi hành trình mẫu.
3. Phải có đầu ra kiểm tra cho phân bố biểu cảm và bảng thay đổi giữa các điểm chạm.
4. Ngưỡng đối sánh và ngưỡng ngắt lượt phải được khóa trước khi đánh giá.
5. Chỉ sau khi mã và đầu ra được kiểm tra mới bổ sung các cấu hình cuối cùng vào báo cáo.

## 6. Yêu cầu về cách viết

- Dùng câu ngắn, trình bày trực tiếp chủ thể, thao tác và kết quả.
- Ưu tiên thuật ngữ tiếng Việt; thuật ngữ tiếng Anh chỉ đặt trong ngoặc ở lần xuất hiện đầu tiên khi cần thiết.
- Không dùng các cụm từ quảng bá như “toàn diện”, “vượt trội”, “tối ưu”, “giải quyết trọn vẹn” nếu không có kết quả chứng minh.
- Không suy diễn nguyên nhân từ thay đổi biểu cảm.
- Không gọi biểu cảm quan sát được là cảm xúc thật hoặc mức độ hài lòng.
- Không kết thúc chương bằng mục “Kết luận chương”.
