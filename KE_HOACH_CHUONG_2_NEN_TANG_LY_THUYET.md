# Kế hoạch Chương 2 – Nền tảng lý thuyết

## 1. Mục tiêu và phạm vi

Chương 2 cung cấp cơ sở khoa học để giải thích bài toán nhận dạng biểu cảm khuôn mặt và phân tích hành trình đa điểm chạm. Chương này chỉ trình bày khái niệm, nguyên lý và giới hạn của các phương pháp.

Không đưa vào Chương 2:

- Mô hình cụ thể được lựa chọn cho hệ thống.
- Phiên bản thư viện, trọng số, ngưỡng hoặc cấu hình chạy.
- Tập dữ liệu và giao thức thực nghiệm.
- Kết quả đo, bảng xếp hạng hoặc kết luận phương pháp tốt nhất.
- Kiến trúc máy chủ, cơ sở dữ liệu và giao diện.

Các nội dung trên lần lượt thuộc Chương 3, Chương 4 và Chương 5.

---

## 2. Cấu trúc Chương 2

### 2.1. Cơ sở lý thuyết về nhận dạng biểu cảm khuôn mặt

#### 2.1.1. Cảm xúc, biểu cảm khuôn mặt và bài toán FER

Trình bày:

- Phân biệt cảm xúc bên trong và biểu cảm khuôn mặt quan sát được.
- Định nghĩa bài toán nhận dạng biểu cảm khuôn mặt (Facial Expression Recognition – FER).
- Đầu vào, đầu ra và giới hạn diễn giải của FER.
- Sáu nhóm biểu cảm cơ bản thường được sử dụng trong nghiên cứu của Ekman và lớp trung tính thường được bổ sung trong các bộ dữ liệu FER.
- Bài toán phân loại bảy lớp gồm Angry, Disgust, Fear, Happy, Sad, Surprise và Neutral.

Không diễn giải nhãn biểu cảm thành trạng thái tâm lý, mức độ hài lòng hoặc ý định mua hàng.

#### 2.1.2. Biểu hiện của cảm xúc trên khuôn mặt

Trình bày ngắn gọn:

- Vai trò của các vùng lông mày, mắt, mũi và miệng trong biểu hiện khuôn mặt.
- Hệ thống mã hóa hành động khuôn mặt (Facial Action Coding System – FACS).
- Đơn vị hành động mô tả chuyển động cơ mặt; nhiều đơn vị có thể cùng tạo thành một mẫu biểu cảm.
- FACS chỉ là cơ sở giải thích; hệ thống không trực tiếp phát hiện đơn vị hành động.

#### 2.1.3. Quy trình nhận dạng biểu cảm khuôn mặt tổng quát

```text
Ảnh khuôn mặt
    → Phát hiện khuôn mặt
    → Căn chỉnh và chuẩn hóa
    → Trích xuất đặc trưng
    → Phân loại biểu cảm
    → Nhãn và độ tin cậy
```

Mỗi công đoạn chỉ được giải thích ở mức nguyên lý. Không nêu thư viện hoặc cấu hình triển khai.

**Hình dự kiến:** Hình 2.1. Quy trình nhận dạng biểu cảm khuôn mặt tổng quát.

### 2.2. Các phương pháp phát hiện khuôn mặt

Mở đầu bằng định nghĩa: phát hiện khuôn mặt xác định vị trí khuôn mặt trong ảnh và trả về khung bao cùng độ tin cậy. Nêu các thách thức về kích thước, tư thế, che khuất và chiếu sáng.

Chỉ trình bày ba phương pháp đại diện.

#### 2.2.1. Haar Cascade

- Đặc trưng Haar.
- Ảnh tích phân.
- AdaBoost để lựa chọn đặc trưng.
- Bộ phân loại phân tầng để loại sớm vùng không phải khuôn mặt.
- Điểm mạnh và giới hạn theo nguyên lý.

Không nêu tên tệp mô hình OpenCV hoặc gọi đây là “mốc đối chứng”.

#### 2.2.2. MTCNN

- Ba mạng P-Net, R-Net và O-Net.
- Quá trình tạo ứng viên, tinh chỉnh khung bao và xác định điểm mốc.
- Cơ chế học đồng thời phân loại khuôn mặt và hồi quy vị trí.
- Điểm mạnh và giới hạn của cấu trúc nhiều giai đoạn.

Không nêu gói phần mềm, phiên bản hoặc ngưỡng của từng tầng.

#### 2.2.3. RetinaFace

- Cơ chế phát hiện một giai đoạn.
- Học đồng thời phân loại khuôn mặt, hồi quy khung bao và xác định điểm mốc.
- Khai thác đặc trưng nhiều mức tỷ lệ.
- Điểm mạnh và giới hạn theo nguyên lý.

Không nêu biến thể MobileNet0.25, nguồn trọng số hoặc kết quả đo.

#### 2.2.4. Tổng hợp đặc điểm lý thuyết

| Phương pháp | Nguyên lý chính | Đầu ra | Đặc điểm cần lưu ý |
|---|---|---|---|
| Haar Cascade | Đặc trưng Haar, ảnh tích phân, AdaBoost, phân tầng | Khung bao | Phụ thuộc đặc trưng thiết kế thủ công |
| MTCNN | Mạng tích chập ba giai đoạn, học nhiều nhiệm vụ | Khung bao, điểm mốc | Xử lý tuần tự qua nhiều mạng |
| RetinaFace | Mạng một giai đoạn, đặc trưng nhiều tỷ lệ, học nhiều nhiệm vụ | Khung bao, điểm mốc | Dự đoán trên nhiều mức đặc trưng |

Bảng không chứa độ chính xác, tốc độ hoặc kết luận lựa chọn. Các số liệu này thuộc Chương 5 và phải do mã thực nghiệm tạo ra.

**Hình và bảng dự kiến:**

- Hình 2.2. Luồng xử lý của Haar Cascade.
- Hình 2.3. Kiến trúc ba giai đoạn của MTCNN.
- Hình 2.4. Khái quát cơ chế phát hiện của RetinaFace.
- Bảng 2.1. Tổng hợp đặc điểm lý thuyết của ba phương pháp.

### 2.3. Các phương pháp phân loại biểu cảm khuôn mặt

#### 2.3.1. Phương pháp dựa trên đặc trưng thiết kế thủ công

- Mẫu nhị phân cục bộ hoặc lược đồ hướng độ dốc.
- Phân loại bằng máy véc-tơ hỗ trợ.
- Điểm mạnh về mức độ đơn giản và giới hạn trước thay đổi tư thế, ánh sáng.

#### 2.3.2. Phương pháp dựa trên mạng nơ-ron tích chập

- Phép tích chập để học đặc trưng không gian.
- Hàm kích hoạt, phép giảm kích thước và lớp phân loại.
- Hàm Softmax tạo phân bố xác suất các lớp.
- Nhãn dự đoán là lớp có xác suất lớn nhất.

Không trình bày chi tiết từng kiến trúc nếu mô hình đó không được sử dụng trong phương pháp hoặc thực nghiệm.

#### 2.3.3. Học chuyển giao

- Sử dụng trọng số đã học từ tập dữ liệu trước đó.
- Dùng mạng làm bộ trích xuất đặc trưng hoặc tinh chỉnh một phần/toàn bộ mạng.
- Lợi ích khi dữ liệu biểu cảm hạn chế.
- Nguy cơ sai khác miền dữ liệu giữa tập huấn luyện và môi trường thực tế.

DeepFace chỉ là thư viện tích hợp mô hình. Không trình bày DeepFace như một phương pháp phân loại biểu cảm.

**Hình và bảng dự kiến:**

- Hình 2.5. Cấu trúc khái quát của mạng nơ-ron tích chập dùng cho phân loại biểu cảm.
- Bảng 2.2. Tổng hợp các nhóm phương pháp phân loại biểu cảm.

### 2.4. Cơ sở lý thuyết về phân tích hành trình cảm xúc đa điểm chạm

#### 2.4.1. Hành trình khách hàng và điểm chạm

- Hành trình là chuỗi tương tác diễn ra theo thời gian.
- Điểm chạm là một lần tương tác trong hành trình.
- Trải nghiệm mang tính động nên cần xem xét nhiều điểm chạm thay vì một vị trí riêng lẻ.

Nguồn chính dự kiến: Lemon và Verhoef (2016).

#### 2.4.2. Quan sát biểu cảm tại một điểm chạm

Một kết quả FER hợp lệ được xem là một quan sát gồm điểm chạm, thời gian, nhãn biểu cảm và độ tin cậy.

Véc-tơ xác suất bảy lớp là đầu ra kỹ thuật của mô hình, có thể dùng để kiểm tra mức chắc chắn và phân tích lỗi. Phần phân tích hành trình chính chỉ cần nhãn và độ tin cậy; không dùng véc-tơ này để tự tạo “điểm cảm xúc chung”.

Mỗi ảnh hợp lệ tạo tối đa một quan sát.

#### 2.4.3. Biểu diễn hành trình dưới dạng chuỗi

- Các quan sát có cùng mã hành trình được sắp xếp theo thời gian.
- Thống kê phân bố biểu cảm tại từng điểm chạm.
- Thống kê sự chuyển đổi biểu cảm giữa hai điểm chạm liên tiếp.
- Ghi nhận điểm chạm thiếu hoặc quan sát không hợp lệ.

Ma trận chuyển tiếp chỉ được tính khi có mã hành trình đáng tin cậy. Mỗi ô cho biết số lượng hoặc tỷ lệ hành trình chuyển từ một nhãn ở điểm chạm trước sang một nhãn ở điểm chạm sau. Ma trận chỉ mô tả sự thay đổi quan sát được, không chứng minh quan hệ nhân quả.

Nguồn chính dự kiến: Halvorsrud, Kvale và Følstad (2016) cùng các nghiên cứu phân tích chuỗi điểm chạm đã được kiểm tra toàn văn.

#### 2.4.4. Phạm vi diễn giải

Không:

- Gán trọng số tùy ý cho bảy lớp biểu cảm.
- Tạo điểm cảm xúc chung bằng phép cộng hoặc trung bình các nhãn.
- Áp dụng quy tắc đỉnh–cuối cho xác suất FER khi chưa được kiểm chứng.
- Suy diễn trực tiếp mức độ hài lòng hoặc ý định mua hàng.
- Khẳng định liên kết cùng một khách hàng qua nhiều camera nếu không có mã phiên đáng tin cậy.

**Hình và bảng dự kiến:**

- Hình 2.6. Minh họa chuỗi quan sát theo hành trình đa điểm chạm.
- Bảng 2.3. Các đại lượng mô tả hành trình và điều kiện diễn giải.

Chương 2 không có mục “Kết luận chương”.

---

## 3. Phân bổ dung lượng

| Mục | Dung lượng dự kiến |
|---|---:|
| 2.1. Cơ sở nhận dạng biểu cảm khuôn mặt | 1,5–2 trang |
| 2.2. Các phương pháp phát hiện khuôn mặt | 2–2,5 trang |
| 2.3. Các phương pháp phân loại biểu cảm | 2–2,5 trang |
| 2.4. Phân tích hành trình đa điểm chạm | 1,5–2 trang |
| **Tổng** | **Khoảng 7–9 trang** |

---

## 4. Quy tắc nguồn và trích dẫn

Mọi định nghĩa, nguyên lý, công thức, nhận định kế thừa, hình và bảng tham khảo phải có trích dẫn ngay tại nội dung liên quan.

Ưu tiên:

1. Bài báo gốc đề xuất phương pháp.
2. Bài báo khoa học có phản biện.
3. Tài liệu chính thức của bộ dữ liệu hoặc công nghệ.
4. Mã nguồn chính thức khi cần xác nhận chi tiết triển khai.

Mỗi tài liệu phải có tác giả hoặc tổ chức, tiêu đề, năm và DOI hoặc địa chỉ truy cập ổn định. Không dùng trang kết quả tìm kiếm hoặc nguồn chưa được mở và kiểm tra.

Phân biệt rõ:

- Kiến thức kế thừa: có trích dẫn.
- Cách vận dụng: được mô tả tại Chương 3.
- Kết quả thực nghiệm: do chương trình tạo ra và trình bày tại Chương 5.

---

## 5. Quy tắc thuật ngữ và cách viết

- Dùng thống nhất từ “luận văn”; không dùng “đồ án” hoặc “đề tài” để chỉ công trình.
- Dùng “phát hiện khuôn mặt”; không dùng “nhận diện khuôn mặt” vì hệ thống không xác định danh tính.
- Ưu tiên tiếng Việt. Thuật ngữ nước ngoài chỉ xuất hiện lần đầu trong ngoặc hoặc khi là tên riêng.
- Giải thích từ viết tắt ở lần đầu và thêm vào danh mục nếu được dùng nhiều lần.
- Không dùng “tốt nhất”, “nhanh” hoặc “chính xác” nếu chưa có số liệu hỗ trợ.
- Không trộn phần lý thuyết với lựa chọn triển khai hoặc nhận xét thực nghiệm.

Các từ viết tắt dự kiến cần rà soát: FER, FACS, AU, CNN, MTCNN, LBP, HOG và SVM. Chỉ giữ từ thực sự xuất hiện trong bản cuối.

---

## 6. Điều kiện bắt đầu và hoàn thành

Trước khi viết lại Chương 2:

1. Đặc tả phương pháp đề xuất ở Chương 3 đã được duyệt.
2. Mã của phương pháp đề xuất đã chạy và có đầu ra kiểm chứng.
3. Mô hình phân loại biểu cảm sử dụng trong hệ thống đã được xác định rõ tên, nguồn trọng số và cách tiền xử lý.
4. Danh sách phương pháp thực sự cần trình bày trong phần lý thuyết đã được khóa.

Chương 2 hoàn thành khi:

- Chỉ chứa cơ sở lý thuyết, không lẫn thiết lập hoặc kết quả đo.
- Ba phương pháp phát hiện khuôn mặt được trình bày cân đối.
- Các nhóm phương pháp phân loại biểu cảm được gọi đúng bản chất.
- Phần đa điểm chạm không chứa công thức tổng hợp tùy ý.
- Mọi nhận định kế thừa có nguồn rõ ràng.
- Mục lục, danh mục hình, danh mục bảng, danh mục từ viết tắt và tài liệu tham khảo được sinh đúng sau khi biên dịch.
