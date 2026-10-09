# Kế hoạch thực nghiệm so sánh các phương pháp phân loại biểu cảm

## 1. Trạng thái và phạm vi

- **Trạng thái:** đã duyệt phạm vi và đang triển khai mã thực nghiệm.
- **Phạm vi:** xây dựng và chạy thực nghiệm so sánh hai họ phương pháp đã trình bày tại Chương 2 qua ba cấu hình: LBP--SVM, CNN huấn luyện từ đầu và cùng CNN đó sử dụng học chuyển giao.
- **Đầu ra cuối cùng:** mã thực nghiệm có thể chạy lại, mô hình đã chọn, dữ liệu kết quả thô, bảng và biểu đồ phục vụ Chương 5.
- **Chưa thực hiện trong bước lập kế hoạch:** tải dữ liệu, huấn luyện mô hình, thay đổi dịch vụ vision hoặc ghi kết quả vào luận văn.

Mọi lựa chọn trong tài liệu này phải được khóa trước lần chạy chính thức. Nếu thay đổi dữ liệu, kiến trúc mô hình, cách chia tập hoặc chỉ số sau khi đã xem kết quả kiểm tra, thực nghiệm phải được chạy lại và ghi thành một lần chạy mới.

## 2. Câu hỏi thực nghiệm

Thực nghiệm cần trả lời ba câu hỏi:

1. Trong ba cấu hình LBP kết hợp SVM, CNN huấn luyện từ đầu và cùng CNN đó sử dụng học chuyển giao, cấu hình nào phân loại tốt nhất bảy lớp biểu cảm trên cùng một bộ dữ liệu kiểm tra?
2. Từng phương pháp thường nhầm lẫn giữa những lớp biểu cảm nào?
3. Cấu hình nào tạo được sự cân bằng phù hợp giữa chất lượng phân loại, thời gian suy luận và kích thước mô hình để tích hợp vào hệ thống?

Kết quả của thực nghiệm được dùng để lựa chọn thành phần phân loại biểu cảm. Kết quả không được dùng để kết luận khách hàng hài lòng, không hài lòng, có ý định mua hàng hoặc đang ở một trạng thái tâm lý cụ thể.

## 3. Các cấu hình được so sánh

### 3.1. Cấu hình A — LBP kết hợp SVM

- Ảnh khuôn mặt được chuyển thành ảnh xám và giữ ở kích thước 48 × 48 điểm ảnh.
- Đặc trưng LBP được tính theo từng vùng không gian; histogram của các vùng được ghép thành một véc-tơ.
- SVM thực hiện phân loại nhiều lớp theo đúng bảy nhãn biểu cảm.
- Các tham số của LBP, hệ số phạt của SVM và loại hàm nhân được chọn bằng tập xác thực, không chọn bằng tập kiểm tra.
- Nếu phương pháp này được chọn để tích hợp, điểm quyết định của SVM phải được hiệu chỉnh thành phân bố điểm của bảy lớp trên dữ liệu không dùng để kiểm tra cuối cùng.

Phương pháp này đại diện cho hướng sử dụng đặc trưng được xác định trước rồi mới huấn luyện bộ phân loại.

### 3.2. Cấu hình B — CNN huấn luyện từ đầu

- Sử dụng kiến trúc `MobileNetV3-Small` với trọng số được khởi tạo mới.
- Lớp đầu ra được thay bằng lớp phân loại bảy biểu cảm.
- Toàn bộ trọng số được học từ tập huấn luyện FER-2013.
- Kiến trúc nền phải giống Cấu hình C để phép so sánh giữa B và C chủ yếu phản ánh tác dụng của học chuyển giao.

Phương pháp này đại diện cho hướng CNN tự học đặc trưng từ dữ liệu biểu cảm mà không sử dụng trọng số đã học từ bộ dữ liệu khác.

### 3.3. Cấu hình C — CNN sử dụng học chuyển giao

- Sử dụng cùng kiến trúc `MobileNetV3-Small` như Cấu hình B.
- Khởi tạo mạng nền bằng trọng số ImageNet đã công bố trong `torchvision`.
- Thay lớp phân loại bằng lớp có bảy đầu ra.
- Thực hiện hai giai đoạn: huấn luyện lớp phân loại khi mạng nền được cố định, sau đó tinh chỉnh các lớp đã xác định trước.
- Phạm vi lớp được tinh chỉnh, tốc độ học và điều kiện dừng phải được ghi trong cấu hình.

`MobileNetV3-Small` được đề xuất vì hệ thống cần suy luận trên CPU và kiến trúc này được thiết kế cho môi trường tài nguyên hạn chế. Việc chọn kiến trúc này phải được bổ sung vào Chương 2 sau khi kế hoạch được duyệt.

## 4. Bộ dữ liệu

### 4.1. Lựa chọn dữ liệu

Sử dụng FER-2013 vì:

- Bộ dữ liệu cung cấp ảnh khuôn mặt đã được cắt và chuẩn hóa về 48 × 48 điểm ảnh.
- Hệ nhãn gồm đúng bảy lớp đang được hệ thống sử dụng: `Angry`, `Disgust`, `Fear`, `Happy`, `Sad`, `Surprise` và `Neutral`.
- Bộ dữ liệu có cách chia huấn luyện và kiểm tra được công bố, phù hợp để các phương pháp nhận cùng một đầu vào.

Nguồn phương pháp và dữ liệu: Goodfellow và cộng sự, *Challenges in Representation Learning: A report on three machine learning contests*, 2013: <https://arxiv.org/abs/1307.0414>.

### 4.2. Cách chia tập

Giữ nguyên trường `Usage` của FER-2013:

- `Training`: dùng để học trọng số và tham số mô hình.
- `PublicTest`: dùng làm tập xác thực để chọn cấu hình, điều kiện dừng và phương pháp hiệu chỉnh điểm.
- `PrivateTest`: dùng làm tập kiểm tra cuối cùng và chỉ chạy sau khi toàn bộ cấu hình đã được khóa.

Số lượng mẫu dự kiến theo bản dữ liệu gốc là 28.709 ảnh huấn luyện, 3.589 ảnh xác thực và 3.589 ảnh kiểm tra. Chương trình chuẩn bị dữ liệu phải tự kiểm tra lại các con số này từ tệp đầu vào; nếu không khớp thì dừng thay vì âm thầm bỏ mẫu.

### 4.3. Kiểm tra dữ liệu trước thực nghiệm

Chương trình kiểm tra dữ liệu phải xác nhận:

- Mỗi dòng có đúng 2.304 giá trị điểm ảnh và các giá trị nằm trong khoảng 0–255.
- Nhãn chỉ thuộc bảy giá trị hợp lệ.
- Trường `Usage` chỉ thuộc ba tập đã xác định.
- Không có dòng trùng hoàn toàn giữa ba tập.
- Không có ảnh rỗng hoặc ảnh không thể tái tạo.
- Số lượng mẫu của từng lớp và từng tập được ghi vào bản kê khai.
- SHA-256 của tệp nguồn và danh sách mẫu được lưu để bảo đảm lần chạy sau dùng đúng dữ liệu.

Dữ liệu gốc được giữ nguyên, không ghi đè và không đưa vào Git. Mọi ảnh bị loại, nếu có, phải được ghi cùng lý do; nếu lỗi ảnh hưởng đến cấu trúc bộ dữ liệu thì dừng lần chạy chính thức.

### 4.4. Mất cân bằng và chất lượng nhãn

FER-2013 có số mẫu giữa các lớp không đồng đều. Vì vậy:

- Bảng kết quả phải có số lượng mẫu từng lớp.
- Macro-F1 được dùng làm chỉ số lựa chọn chính thay vì chỉ dựa vào Accuracy.
- Cả SVM và hai CNN sử dụng trọng số lớp được tính từ tập huấn luyện; trọng số không được tính lại từ tập xác thực hoặc tập kiểm tra.
- Không tăng số lượng mẫu của tập kiểm tra và không thay nhãn thủ công sau khi xem dự đoán.

## 5. Chuẩn hóa đầu vào

### 5.1. Phần chung

- Thứ tự bảy nhãn được khóa trong một tệp cấu hình dùng chung.
- Cả ba cấu hình nhận đúng cùng danh sách ảnh ở mỗi tập.
- Benchmark phân loại sử dụng ảnh khuôn mặt đã cắt sẵn của FER-2013. RetinaFace không được chạy trong benchmark này để sai số phát hiện khuôn mặt không bị trộn với sai số phân loại biểu cảm.
- Các phép biến đổi ngẫu nhiên chỉ được áp dụng cho tập huấn luyện.

### 5.2. Tiền xử lý theo phương pháp

- **LBP--SVM:** ảnh xám 48 × 48; chuẩn hóa cường độ theo cấu hình; trích xuất LBP theo vùng.
- **Hai CNN:** lặp kênh ảnh xám thành ba kênh, thay đổi kích thước theo yêu cầu của MobileNetV3-Small và chuẩn hóa bằng đúng thống kê của cấu hình huấn luyện.
- **Tăng cường dữ liệu CNN:** lật ngang, dịch chuyển hoặc xoay nhẹ trong giới hạn đã khóa. Không sử dụng phép biến đổi làm thay đổi bản chất biểu cảm.

Việc hai họ phương pháp sử dụng biểu diễn đầu vào khác nhau là một phần của chính phương pháp, nhưng ảnh nguồn, nhãn và tập dữ liệu phải giống nhau.

## 6. Quy trình huấn luyện và lựa chọn cấu hình

### 6.1. Nguyên tắc chung

- Không dùng `PrivateTest` để chọn tham số hoặc quyết định thời điểm dừng.
- Mọi tham số được lưu trong YAML trước lần chạy kiểm tra cuối cùng.
- Trạng thái ngẫu nhiên của mỗi lần huấn luyện phải được ghi lại; không cần đưa con số này vào nội dung luận văn nhưng phải có trong tệp cấu hình để chạy lại.
- CNN được chạy ít nhất ba lần với các trạng thái khởi tạo khác nhau. Báo cáo trung bình và độ lệch chuẩn trên ba lần chạy.
- Không xóa lần chạy cho kết quả xấu. Lần chạy lỗi kỹ thuật được giữ log và chỉ chạy lại sau khi ghi rõ nguyên nhân.

### 6.2. LBP--SVM

1. Tính đặc trưng LBP cho `Training` và `PublicTest`.
2. Chọn cấu hình LBP và SVM từ một lưới tham số nhỏ được khai báo trước.
3. Chọn cấu hình có Macro-F1 cao nhất trên `PublicTest`.
4. Khóa cấu hình; chỉ sau đó mới dự đoán `PrivateTest`.
5. Nếu cần điểm xác suất để tích hợp, hiệu chỉnh điểm SVM bằng dữ liệu huấn luyện theo quy trình có chia nội bộ, không dùng `PrivateTest`.

### 6.3. CNN huấn luyện từ đầu

1. Khởi tạo toàn bộ MobileNetV3-Small bằng trọng số mới.
2. Huấn luyện bằng hàm mất mát cross-entropy có trọng số lớp.
3. Theo dõi Macro-F1 trên `PublicTest` và dừng sớm theo cấu hình đã khóa.
4. Giữ checkpoint tốt nhất theo Macro-F1 xác thực.
5. Lặp lại ba lần và đánh giá từng checkpoint trên `PrivateTest` sau khi kết thúc giai đoạn chọn cấu hình.

### 6.4. CNN học chuyển giao

1. Nạp trọng số ImageNet của MobileNetV3-Small.
2. Thay lớp đầu ra bằng lớp bảy nhãn.
3. Huấn luyện lớp đầu ra khi mạng nền được cố định.
4. Mở các lớp đã xác định trước và tinh chỉnh với tốc độ học nhỏ hơn.
5. Chọn checkpoint theo Macro-F1 của `PublicTest`.
6. Lặp lại ba lần và đánh giá trên `PrivateTest` theo cùng nguyên tắc với CNN huấn luyện từ đầu.

Nguồn kiến trúc: Howard và cộng sự, *Searching for MobileNetV3*, 2019: <https://arxiv.org/abs/1905.02244>.

## 7. Chỉ số đánh giá

### 7.1. Chất lượng phân loại

- **Macro-F1 — chỉ số chính:** tính F1 cho từng lớp rồi lấy trung bình để mỗi biểu cảm có vai trò ngang nhau.
- **Accuracy:** tỷ lệ toàn bộ ảnh được phân loại đúng.
- **Precision, Recall và F1 của từng lớp:** cho biết chất lượng riêng của từng biểu cảm.
- **Balanced Accuracy:** trung bình Recall của bảy lớp, dùng để kiểm tra ảnh hưởng của mất cân bằng.
- **Ma trận nhầm lẫn:** xuất cả số lượng tuyệt đối và tỷ lệ chuẩn hóa theo nhãn thật.
- **Tỷ lệ lỗi xử lý:** tỷ lệ ảnh không tạo được dự đoán hợp lệ.

Các chỉ số được tính từ dự đoán của từng ảnh bằng cùng một chương trình đánh giá. Không chép chỉ số do từng thư viện in ra rồi ghép thành một bảng.

### 7.2. Hiệu năng triển khai

Đo ở chế độ một ảnh mỗi lần, phù hợp với cách dịch vụ xử lý từng vùng khuôn mặt:

- Thời gian nạp mô hình.
- Độ trễ trung vị, P95 và P99 cho tiền xử lý cùng suy luận.
- Số ảnh xử lý trong một giây tính từ tổng thời gian.
- Dung lượng tệp mô hình.
- Số lượng tham số của hai CNN.
- Bộ nhớ cực đại nếu có thể thu thập ổn định.

Mô hình được nạp một lần, chạy khởi động trước khi đo và chạy ba lượt trên cùng thứ tự ảnh. Thời gian đọc CSV, tái tạo ảnh và ghi kết quả không tính vào độ trễ suy luận chính. Phần cứng, số luồng CPU, hệ điều hành và phiên bản thư viện phải được ghi trong `environment.json`.

### 7.3. Cách lựa chọn phương pháp

1. Loại cấu hình không tạo đủ bảy điểm đầu ra hoặc có lỗi xử lý trên dữ liệu hợp lệ.
2. Xếp phương pháp theo Macro-F1 trung bình trên `PrivateTest`.
3. Kiểm tra F1 từng lớp và ma trận nhầm lẫn để tránh chọn phương pháp bỏ qua lớp ít mẫu.
4. Nếu chênh lệch Macro-F1 giữa hai phương pháp nhỏ hơn 0,01, ưu tiên phương pháp có độ trễ P95 thấp hơn và kích thước mô hình nhỏ hơn.
5. Ghi rõ quyết định cuối cùng bằng số liệu; không chọn trước phương pháp thắng cuộc.

Ngưỡng chênh lệch 0,01 là tiêu chí ra quyết định của đề tài, không phải ngưỡng chuẩn của FER-2013. Nếu thay đổi tiêu chí này phải sửa kế hoạch trước khi chạy tập kiểm tra.

## 8. Phân tích sai số

Sau bảng tổng hợp, cần chọn các trường hợp sau để phân tích:

- Ảnh cả ba cấu hình đều đúng.
- Ảnh cả ba cấu hình đều sai.
- Ảnh LBP--SVM đúng nhưng hai CNN sai và trường hợp ngược lại.
- Các cặp lớp có số lượng nhầm lẫn lớn nhất.
- Ảnh có độ sáng thấp, che khuất, lệch góc hoặc độ tương phản thấp nếu có thể nhận biết từ ảnh.
- Các dự đoán có điểm cao nhưng sai nhãn.

Không xóa hoặc thay nhãn của các mẫu này. Phân tích sai số chỉ giải thích giới hạn và đề xuất hướng cải thiện.

## 9. Thiết kế mã nguồn dự kiến

Tạo một dự án độc lập để không trộn mã huấn luyện với API nghiệp vụ:

```text
COMPARE_FACIAL_EXPRESSION/
├── TECH_SPEC.md
├── README.md
├── pyproject.toml
├── uv.lock
├── configs/
│   └── benchmark.yaml
├── src/
│   └── expression_benchmark/
│       ├── adapters/
│       │   ├── base.py
│       │   ├── lbp_svm.py
│       │   ├── cnn_scratch.py
│       │   └── cnn_transfer.py
│       ├── dataset.py
│       ├── validate_dataset.py
│       ├── train.py
│       ├── evaluate.py
│       ├── metrics.py
│       ├── benchmark_latency.py
│       ├── select_model.py
│       └── build_report.py
├── tests/
├── data/
├── weights/
└── results/
    └── <run-id>/
```

Ba adapter phải trả về cùng một cấu trúc:

```text
sample_id
true_label
predicted_label
scores[7]
preprocess_latency_ms
inference_latency_ms
status
```

Không đưa các đường dẫn tuyệt đối của máy cá nhân vào mã. Đường dẫn dữ liệu, thư mục kết quả và cấu hình thiết bị được truyền qua YAML hoặc tham số dòng lệnh.

## 10. Kiểm thử mã thực nghiệm

### 10.1. Kiểm thử đơn vị

- Đọc và tái tạo đúng ảnh 48 × 48 từ CSV.
- Ánh xạ đúng thứ tự bảy nhãn.
- Phát hiện dòng thiếu điểm ảnh, nhãn sai và tập dữ liệu không hợp lệ.
- Đặc trưng LBP có kích thước cố định.
- Ba adapter trả đúng bảy điểm và một nhãn hợp lệ.
- Hàm tính Accuracy, Macro-F1 và ma trận nhầm lẫn đúng trên một bộ dữ liệu nhỏ có đáp án tính trước.
- Chương trình không cho phép dùng `PrivateTest` trong giai đoạn chọn tham số.

### 10.2. Chạy thử kỹ thuật

- Chạy trên một phần nhỏ của `Training` và `PublicTest` để kiểm tra đường ống.
- Kết quả chạy thử phải mang cờ `smoke_test=true`.
- Kết quả chạy thử không được đưa vào luận văn và không được dùng để chọn phương pháp.

### 10.3. Kiểm tra tái lập

- Chạy lại một cấu hình đã khóa phải tạo cùng danh sách mẫu và cùng tệp kê khai dữ liệu.
- Mỗi đầu ra ghi mã commit, cấu hình, phiên bản thư viện, mã kiểm tra dữ liệu và mã kiểm tra trọng số.
- Bảng Markdown, bảng LaTeX và biểu đồ phải được sinh tự động từ kết quả thô.

## 11. Cấu trúc kết quả của một lần chạy

```text
results/<run-id>/
├── run_manifest.json
├── environment.json
├── dataset_manifest.json
├── resolved_config.yaml
├── training/
│   ├── lbp_svm.json
│   ├── cnn_scratch_run_1.json
│   ├── cnn_scratch_run_2.json
│   ├── cnn_scratch_run_3.json
│   ├── cnn_transfer_run_1.json
│   ├── cnn_transfer_run_2.json
│   └── cnn_transfer_run_3.json
├── predictions/
│   └── <method>.jsonl
├── metrics/
│   ├── per_class.csv
│   ├── summary.csv
│   └── confusion_matrices/
├── latency/
│   └── latency.jsonl
├── figures/
├── tables/
├── selection.json
└── test_results.txt
```

`selection.json` phải ghi phương pháp được chọn, các chỉ số làm căn cứ và lý do không chọn hai phương pháp còn lại.

## 12. Tích hợp phương pháp được chọn vào hệ thống

Chỉ thực hiện sau khi kết quả chính thức đã được kiểm tra:

1. Xuất mô hình được chọn cùng thứ tự nhãn và cấu hình tiền xử lý.
2. Tính SHA-256 của tệp trọng số và ghi mã mô hình cụ thể.
3. Tạo giao diện `EmotionClassifier` trong dịch vụ vision.
4. RetinaFace tiếp tục phát hiện từng khuôn mặt; mỗi vùng khuôn mặt được chuyển cho `EmotionClassifier`.
5. Kết quả gồm nhãn, điểm của bảy lớp, mức tin cậy, trạng thái và mã mô hình.
6. Chạy lại kiểm thử API, khung nhiều người, dữ liệu lỗi và đo độ trễ đầu-cuối.

Benchmark trên FER-2013 và kiểm thử tích hợp là hai bằng chứng khác nhau: benchmark đo chất lượng bộ phân loại trên dữ liệu có nhãn; kiểm thử tích hợp chứng minh mô hình được chọn hoạt động đúng trong hệ thống.

## 13. Nội dung sẽ đưa vào Chương 5

Phần thực nghiệm phân loại biểu cảm dự kiến gồm:

1. Mục tiêu và câu hỏi thực nghiệm.
2. FER-2013, hệ nhãn và lý do lựa chọn.
3. Hai họ phương pháp và ba cấu hình thực nghiệm.
4. Cách chia tập và biện pháp ngăn rò rỉ dữ liệu.
5. Chỉ số đánh giá và ý nghĩa của từng chỉ số.
6. Bảng so sánh chất lượng.
7. Ma trận nhầm lẫn của từng phương pháp.
8. Bảng độ trễ và kích thước mô hình.
9. Phân tích trường hợp đúng, sai và các lớp thường bị nhầm.
10. Lý do lựa chọn phương pháp tích hợp.
11. Giới hạn của dữ liệu và phạm vi kết luận.

Không ghi kết quả dự kiến trước khi chạy. Không sử dụng ảnh giao diện CRM để thay cho bảng chất lượng mô hình.

## 14. Trình tự triển khai sau khi kế hoạch được duyệt

### Giai đoạn 1 — Khóa đặc tả

- Duyệt hai họ phương pháp, ba cấu hình thực nghiệm và kiến trúc MobileNetV3-Small.
- Duyệt tiêu chí lựa chọn mô hình.
- Xác nhận cách tiếp nhận FER-2013 và điều kiện sử dụng dữ liệu.
- Khóa phiên bản Python và thư viện.

### Giai đoạn 2 — Xây dựng mã nền

- Tạo dự án và cấu hình.
- Viết bộ đọc, kiểm tra và kê khai FER-2013.
- Viết giao diện chung cho ba cấu hình.
- Viết hàm chỉ số và kiểm thử tự động.

### Giai đoạn 3 — Cài đặt ba cấu hình

- Cài đặt LBP--SVM.
- Cài đặt MobileNetV3-Small huấn luyện từ đầu.
- Cài đặt MobileNetV3-Small học chuyển giao.
- Chạy smoke test và sửa lỗi đường ống.

### Giai đoạn 4 — Chạy thực nghiệm chính thức

- Chọn cấu hình bằng `Training` và `PublicTest`.
- Khóa cấu hình.
- Chạy `PrivateTest` và benchmark độ trễ.
- Sinh bảng, biểu đồ và báo cáo kiểm tra tự động.

### Giai đoạn 5 — Tích hợp và cập nhật luận văn

- Tích hợp phương pháp được chọn vào dịch vụ vision.
- Chạy kiểm thử tích hợp và đo đầu-cuối.
- Viết kết quả vào Chương 5.
- Cập nhật Chương 2 và Chương 3 để tên mô hình, tiền xử lý và lý do lựa chọn đồng bộ với mã đã chạy.

## 15. Tiêu chí hoàn thành

Thực nghiệm chỉ được coi là hoàn thành khi:

- Ba cấu hình chạy trên cùng `PrivateTest` và cùng danh sách mẫu.
- Không dùng `PrivateTest` để chọn cấu hình.
- Có dự đoán từng ảnh, không chỉ có một bảng tổng hợp.
- Có Macro-F1, Accuracy, chỉ số từng lớp và ma trận nhầm lẫn.
- Có độ trễ trên cùng phần cứng và cùng giao thức đo.
- Các lần huấn luyện CNN được lưu đầy đủ, kể cả lần có kết quả thấp.
- Phương pháp được chọn bằng tiêu chí đã khóa trước.
- Mọi số liệu trong Chương 5 truy ngược được đến một `run-id` và tệp kết quả thô.
- Mô hình được chọn đã được kiểm tra lại sau khi tích hợp vào dịch vụ vision.
- Kết luận chỉ nói về khả năng phân loại bảy nhãn trên dữ liệu thực nghiệm, không suy diễn thành mức độ hài lòng của khách hàng.

## 16. Các điểm cần duyệt trước khi coding

1. Có chấp thuận sử dụng `MobileNetV3-Small` làm kiến trúc chung cho CNN huấn luyện từ đầu và CNN học chuyển giao hay không?
2. Có giữ Macro-F1 là chỉ số lựa chọn chính hay không?
3. Có chấp thuận tiêu chí ưu tiên tốc độ khi chênh lệch Macro-F1 nhỏ hơn 0,01 hay không?
4. FER-2013 sẽ được cung cấp dưới dạng `fer2013.csv` từ nguồn nào và có đáp ứng điều kiện sử dụng cho luận văn hay không?
