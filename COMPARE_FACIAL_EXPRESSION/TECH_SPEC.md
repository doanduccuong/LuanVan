# Đặc tả thực nghiệm phân loại biểu cảm

## Câu hỏi cần trả lời

1. LBP-SVM và mô hình CNN Emotion của DeepFace khác nhau thế nào về Macro-F1 trên cùng tập kiểm tra?
2. Mô hình đang được tích hợp trong hệ thống đạt chất lượng từng lớp như thế nào trên FER-2013?
3. Chất lượng tăng thêm, nếu có, phải đổi bằng bao nhiêu độ trễ và dung lượng mô hình?

## Biến thực nghiệm

| Mã | Biểu diễn đặc trưng | Bộ phân loại | Khởi tạo |
|---|---|---|---|
| `lbp_svm` | Histogram LBP theo vùng | SVM | Không áp dụng |
| `deepface_emotion` | Đặc trưng CNN | Softmax 7 đầu ra | Trọng số huấn luyện sẵn do DeepFace cung cấp |
| `deepface_emotion_finetuned` | Đặc trưng CNN | Softmax 7 đầu ra | Checkpoint do `TRAIN_DEEPFACE_EMOTION` tinh chỉnh bằng Training và chọn bằng PublicTest |

DeepFace là thư viện tích hợp. Đối tượng được đo là mô hình Emotion mà thư viện cung
cấp, không phải toàn bộ thư viện. LBP-SVM được huấn luyện trên `Training`; mô hình
DeepFace Emotion được giữ nguyên trọng số và chỉ suy luận. Vì vậy, đây là so sánh giữa
một baseline truyền thống và thành phần học sâu đang triển khai, không phải phép so
sánh hai chiến lược huấn luyện có cùng nguồn dữ liệu.

Để thực hiện phép so sánh gần hơn về dữ liệu huấn luyện, phương pháp
`deepface_emotion_finetuned` chỉ nạp checkpoint từ dự án huấn luyện độc lập. Dự án
benchmark không có quyền tạo checkpoint. Trước khi đánh giá, chương trình bắt buộc
đối chiếu SHA-256 của checkpoint, SHA-256 của FER-2013, thứ tự bảy nhãn, tập dùng
để lựa chọn checkpoint và cờ xác nhận không sử dụng `PrivateTest`.

## Quy tắc chống rò rỉ dữ liệu

- Không thay đổi trường `Usage` của FER-2013.
- Không che giấu ảnh trùng giữa các tập: lượt chính giữ phân chia công bố và ghi số lượng ảnh trùng; lượt đánh giá độ nhạy sẽ loại ảnh kiểm tra đã xuất hiện ở tập huấn luyện.
- Không tính trọng số lớp bằng `PublicTest` hoặc `PrivateTest`.
- Không chọn tham số, số epoch hoặc checkpoint bằng `PrivateTest`.
- Không cho phép chạy `PrivateTest` nếu cấu hình chưa đặt `final_evaluation=true`.
- Kết quả từng ảnh được lưu để mọi chỉ số có thể tính lại.

## Đầu ra bắt buộc

Mỗi lần chạy lưu:

- bản sao cấu hình;
- SHA-256 của dữ liệu và mô hình;
- môi trường phần mềm, phần cứng;
- lịch sử huấn luyện;
- dự đoán từng ảnh và đủ bảy điểm đầu ra;
- Accuracy, Balanced Accuracy, Macro-F1 và chỉ số từng lớp;
- ma trận nhầm lẫn tuyệt đối và chuẩn hóa;
- độ trễ P50, P95, P99 và thông lượng;
- cờ phân biệt smoke test với thực nghiệm chính thức.

## Điều kiện chưa đáp ứng

Kho mã chưa kèm FER-2013. Vì vậy, chỉ có thể hoàn tất kiểm thử đơn vị và smoke test trước khi dữ liệu chính thức được cung cấp. Không được suy diễn kết quả smoke test thành chất lượng của phương pháp.
