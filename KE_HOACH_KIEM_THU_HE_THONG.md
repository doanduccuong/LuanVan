# Kế hoạch kiểm thử và đánh giá hệ thống

## 1. Mục đích của tài liệu

Tài liệu này xác định lại toàn bộ kế hoạch kiểm thử cho hệ thống CRM tích hợp phát hiện khuôn mặt, phân loại biểu cảm, nhận dạng khách hàng và phân tích quá trình mua sắm tại nhiều khu vực. Kế hoạch được xây dựng theo nguyên tắc: mỗi kết luận trong luận văn phải có một phép kiểm tra tương ứng, sử dụng dữ liệu phù hợp và tạo ra bằng chứng có thể truy vết.

Kế hoạch tách ba loại bằng chứng:

1. **Đánh giá mô hình:** đo chất lượng của bộ phát hiện khuôn mặt, bộ phân loại biểu cảm hoặc bộ nhận dạng danh tính trên dữ liệu có nhãn phù hợp.
2. **Kiểm thử phần mềm:** kiểm tra API, quy tắc nghiệp vụ, cơ sở dữ liệu, giao diện và cách xử lý lỗi.
3. **Kiểm nghiệm vận hành đầu-cuối:** kiểm tra toàn bộ luồng từ lúc hệ thống nhận khung hình đến khi kết quả được lưu và hiển thị trên CRM.

Kết quả của loại kiểm tra này không được dùng thay cho loại kiểm tra khác. Ví dụ, một sự kiện đi hết luồng và được lưu thành công không đồng nghĩa với mô hình nhận dạng danh tính có độ chính xác cao.

## 2. Tóm tắt các thực nghiệm sẽ thực hiện

### 2.1. So sánh phương pháp phát hiện khuôn mặt

**Đánh giá:** Haar Cascade, MTCNN và RetinaFace trên cùng tập WIDER FACE; đo AP Easy, AP Medium, AP Hard, Precision, Recall, F1 và thời gian phát hiện.

**Mục đích:** lựa chọn bộ phát hiện khuôn mặt phù hợp cho hệ thống và làm rõ khả năng phát hiện khuôn mặt nhỏ, bị che khuất hoặc xuất hiện trong cảnh đông người. Thực nghiệm này không đánh giá nhận dạng danh tính hoặc phân loại biểu cảm.

### 2.2. So sánh các phương pháp phân loại biểu cảm

**Đánh giá:** ba hướng đã trình bày tại Chương 2 gồm LBP kết hợp SVM, CNN được huấn luyện từ đầu và CNN sử dụng học chuyển giao. Các phương pháp được huấn luyện, lựa chọn tham số và kiểm tra trên cùng một bộ dữ liệu bảy lớp, cùng cách chia tập và cùng nguyên tắc tiền xử lý. Kết quả được đo bằng Accuracy, Precision, Recall, Macro-F1, F1 của từng lớp, ma trận nhầm lẫn, tỷ lệ không tạo được kết quả và thời gian suy luận. Thư viện DeepFace chỉ là công cụ nạp và gọi mô hình đang tích hợp, không được xem là một phương pháp phân loại thứ tư.

**Mục đích:** xác định phương pháp nào phân loại biểu cảm tốt hơn trên dữ liệu kiểm tra, phương pháp nào thường nhầm giữa các lớp nào và chi phí xử lý của từng phương pháp. Kết quả này là căn cứ lựa chọn bộ phân loại để tích hợp vào hệ thống, thay vì chọn mô hình chỉ vì thư viện đã cung cấp sẵn.

### 2.3. Đánh giá nhận dạng danh tính

**Đánh giá:** khả năng nhận ra cùng một người từ ảnh đăng ký và các ảnh quan sát được thu nhận độc lập. Danh tính dùng để hiệu chỉnh ngưỡng phải tách khỏi danh tính dùng để kiểm tra. Các chỉ số gồm tỷ lệ xác định đúng khách hàng, từ chối nhầm khách hàng đã đăng ký, gắn nhầm người chưa đăng ký và gắn một khách hàng vào sai hồ sơ.

**Mục đích:** xác định mô hình ArcFace và ngưỡng khoảng cách cosine có phù hợp với bài toán nhận dạng khách hàng hay không. Kết quả `115/115` và ngưỡng `0,269958` của lần chạy cũ không được dùng làm kết quả đánh giá mới vì ảnh đăng ký và ảnh quan sát được tạo từ cùng một ảnh nguồn.

### 2.4. Kiểm nghiệm vận hành luồng xử lý ảnh

**Đánh giá:** các trường hợp không có khuôn mặt, một khuôn mặt, nhiều khuôn mặt, có cả khách hàng đã đăng ký và người chưa đăng ký, ảnh lỗi và sự kiện gửi trùng. Với từng sự kiện, kiểm tra trạng thái ảnh, số khuôn mặt, số quan sát, nhãn biểu cảm, trạng thái nhận dạng, mã khách hàng và dữ liệu được lưu trong PostgreSQL.

**Mục đích:** chứng minh các thành phần phát hiện khuôn mặt, phân loại biểu cảm, tạo đặc trưng, đối sánh và lưu dữ liệu phối hợp đúng; đồng thời chứng minh mỗi khuôn mặt tạo một quan sát riêng và khung nhiều người không bị loại bỏ. Thực nghiệm này kiểm tra tính đúng của luồng phần mềm, không thay thế đánh giá chất lượng mô hình.

### 2.5. Kiểm nghiệm quá trình mua sắm tại nhiều khu vực

**Đánh giá:** cùng một khách hàng xuất hiện tại bốn khu vực bằng bốn ảnh quan sát độc lập; kiểm tra thứ tự thời gian, trường hợp thiếu khu vực, bản ghi đến muộn, xung đột thời gian và quy tắc tạo hoặc kết thúc lần mua sắm.

**Mục đích:** chứng minh hệ thống liên kết được các quan sát rời thành một quá trình mua sắm đa điểm chạm. Nếu luận văn công bố thực nghiệm với 100 khách hàng thì toàn bộ 100 khách hàng phải có chuỗi kiểm tra phù hợp, không chỉ năm khách hàng đầu.

### 2.6. Đo hiệu năng đầu-cuối

**Đánh giá:** thời gian từ lúc nguồn bắt đầu gửi ảnh đến khi hệ thống hoàn tất phát hiện khuôn mặt, phân loại biểu cảm, tạo véc-tơ ArcFace, đối sánh, xử lý nghiệp vụ, ghi PostgreSQL và trả phản hồi. Báo cáo độ trễ trung vị, phân vị 95, phân vị 99, thông lượng, tỷ lệ lỗi và khả năng xử lý nhiều nguồn đồng thời.

**Mục đích:** xác định tốc độ thật của toàn hệ thống và kiểm tra có xuất hiện hàng đợi khi ảnh được gửi liên tục hay không. Chỉ khi kết quả đáp ứng tiêu chí thời gian đã xác định trước mới sử dụng cụm từ “theo thời gian thực”. Kết quả 64,53 ms chỉ thuộc bộ phát hiện RetinaFace và không được dùng thay cho độ trễ đầu-cuối.

### 2.7. Kiểm tra báo cáo và phân tích

**Đánh giá:** phân bố nhãn tại từng khu vực, biến thiên số quan sát theo thời gian, cặp thay đổi nhãn giữa các khu vực, bộ lọc và cách xử lý dữ liệu thiếu hoặc xung đột. Kết quả truy vấn phải được đối chiếu với một bộ dữ liệu nhỏ có đáp án tính trước.

**Mục đích:** chứng minh các phép đếm, tính tỷ lệ, phép nhóm và biểu đồ hoạt động đúng. Dữ liệu đi qua mô hình phải được tách khỏi dữ liệu nghiệp vụ được sinh theo quy tắc. Kết quả này không được dùng để suy luận hành vi hoặc mức độ hài lòng của khách hàng thực tế.

### 2.8. Kiểm thử lỗi, phân quyền và dữ liệu khuôn mặt

**Đánh giá:** người chưa đăng nhập, người dùng sai quyền, khách hàng chưa đồng ý sử dụng dữ liệu khuôn mặt, rút lại đồng ý, dịch vụ xử lý ảnh không phản hồi, khu vực hoặc thời gian không hợp lệ, xác nhận thủ công và xử lý lại kết quả.

**Mục đích:** chứng minh hệ thống xử lý lỗi có kiểm soát, chỉ sử dụng dữ liệu khuôn mặt khi đáp ứng điều kiện đã thiết kế và lưu được lịch sử của các thay đổi thủ công.

Tóm lại, kế hoạch mới phải tạo được bốn nhóm bằng chứng: chất lượng của từng mô hình, tính đúng của luồng phần mềm, khả năng liên kết đa điểm chạm và hiệu năng đầu-cuối của toàn hệ thống.

## 3. Những vấn đề của kế hoạch cũ phải được khắc phục

### 3.1. Chưa chứng minh yêu cầu xử lý theo thời gian thực

- Hệ thống mới tiếp nhận từng khung hình rời, chưa có nguồn phát khung hình liên tục từ camera hoặc video.
- Kết quả 64,53 ms chỉ đo RetinaFace, chưa bao gồm phân loại biểu cảm, tạo véc-tơ ArcFace, đối sánh véc-tơ, xử lý nghiệp vụ và ghi PostgreSQL.
- Chưa xác định giới hạn độ trễ chấp nhận được, chưa đo độ trễ đầu-cuối và chưa kiểm tra hiện tượng tồn đọng yêu cầu khi nhiều nguồn gửi ảnh đồng thời.

### 3.2. Dữ liệu nhận dạng danh tính chưa phù hợp

- Ảnh đăng ký và ảnh quan sát của một khách hàng được tạo từ cùng một ảnh FairFace.
- Ngưỡng đối sánh được xác định từ các biến thể của cùng ảnh nguồn và chưa được kiểm tra trên một tập độc lập.
- Kết quả 115/115 chỉ kiểm tra luồng phần mềm với đầu vào đã sàng lọc, không đo năng lực nhận dạng qua các lần chụp độc lập.

### 3.3. Dữ liệu phân tích đang trộn nhiều nguồn

- Một phần nhãn biểu cảm do mô hình phân loại biểu cảm được gọi qua thư viện DeepFace tạo ra từ ảnh.
- Một phần nhãn được sinh theo quy tắc để tạo đủ quan hệ nghiệp vụ do chưa kết nối camera và hệ thống bán hàng thực tế.
- API báo cáo chưa tách nguồn dữ liệu, nên biểu đồ có thể trộn kết quả mô hình với dữ liệu kiểm tra nghiệp vụ.
- Chỉ năm khách hàng có chuỗi bốn khu vực đi qua lớp xử lý ảnh; 95 khách hàng còn lại chỉ có một quan sát.

### 3.4. Mã nguồn, báo cáo và bằng chứng chạy chưa đồng bộ

- Mã và báo cáo hiện mô tả 118 khung hợp lệ có hai khuôn mặt và tổng cộng 236 quan sát.
- Tệp kết quả phát lại đang lưu một lần chạy cũ với 119 quan sát.
- Mọi kết quả cũ phải được đưa ra khỏi tập bằng chứng chính thức. Báo cáo chỉ được cập nhật sau khi mã, dữ liệu, cấu hình và đầu ra của cùng một lần chạy đã được khóa.

## 4. Câu hỏi kiểm thử và phạm vi kết luận

| Mã | Câu hỏi cần trả lời | Bằng chứng cần có | Không được suy ra |
|---|---|---|---|
| Q1 | Phương pháp nào phát hiện khuôn mặt phù hợp nhất trong ba phương pháp được xét? | AP Easy/Medium/Hard, Precision, Recall, F1 và thời gian xử lý trên cùng tập WIDER FACE | Chất lượng nhận dạng danh tính hoặc biểu cảm |
| Q2 | Trong ba hướng LBP--SVM, CNN huấn luyện từ đầu và CNN sử dụng học chuyển giao, phương pháp nào phù hợp nhất với hệ thống? | Cùng tập kiểm tra bảy lớp, cùng giao thức; Accuracy, Macro-F1, F1 từng lớp, ma trận nhầm lẫn, tỷ lệ lỗi và thời gian suy luận | Mức độ hài lòng hoặc trạng thái tâm lý của khách hàng |
| Q3 | ArcFace có nhận dạng được cùng một người qua các ảnh độc lập hay không? | Nhiều ảnh độc lập cho mỗi danh tính; tập hiệu chỉnh và tập kiểm tra tách rời | Độ chính xác thực tế nếu chỉ dùng biến thể của cùng ảnh |
| Q4 | Hệ thống có xử lý đúng khung nhiều người và các trường hợp lỗi hay không? | Các ca kiểm thử đầu-cuối với hậu điều kiện ở API và cơ sở dữ liệu | Độ chính xác tổng quát của mô hình |
| Q5 | Hệ thống có đáp ứng yêu cầu xử lý theo thời gian đã xác định hay không? | Độ trễ đầu-cuối, thông lượng, tỷ lệ lỗi và độ dài hàng đợi dưới tải | Kết luận thời gian thực chỉ từ thời gian RetinaFace |
| Q6 | Quy tắc hình thành lần mua sắm và báo cáo đa điểm chạm có đúng không? | Bộ dữ liệu nhỏ có kết quả tính tay, kiểm thử tự động và đối chiếu chính xác | Xu hướng hành vi của khách hàng thực tế |
| Q7 | Chuỗi đa điểm chạm có được tạo từ đầu vào đi qua mô hình hay không? | Nhiều khách hàng có quan sát độc lập tại đủ bốn khu vực | Hiệu quả tại cửa hàng thật nếu chỉ dùng ảnh ghép |
| Q8 | Hệ thống có bảo vệ dữ liệu khuôn mặt theo phạm vi đã thiết kế hay không? | Kiểm thử đồng ý, phân quyền, lịch sử thay đổi, vô hiệu hóa mẫu và nhật ký | Tuân thủ đầy đủ một quy định pháp lý nếu chưa có đánh giá pháp lý riêng |

## 5. Nguyên tắc xây dựng dữ liệu

### 5.1. Không sử dụng một bộ dữ liệu cho mục đích mà nó không có nhãn

Không có một bộ dữ liệu hiện tại nào trong đề tài đồng thời cung cấp đầy đủ:

- Khung bao khuôn mặt trong cảnh đông người.
- Nhiều ảnh độc lập của cùng một danh tính.
- Nhãn bảy biểu cảm.
- Chuỗi cùng một người tại bốn khu vực mua sắm.

Vì vậy, mỗi câu hỏi phải sử dụng dữ liệu phù hợp:

- **WIDER FACE:** chỉ dùng cho phát hiện khuôn mặt.
- **Dữ liệu nhận dạng:** phải có nhiều ảnh độc lập cho mỗi người và nhãn danh tính.
- **Dữ liệu biểu cảm:** phải có nhãn biểu cảm chuẩn và được chia cố định thành tập huấn luyện, tập xác thực và tập kiểm tra để so sánh LBP--SVM, CNN huấn luyện từ đầu và CNN sử dụng học chuyển giao.
- **Dữ liệu vận hành đa điểm chạm:** phải có mã người, mã khu vực, thời gian và kết quả mong đợi cho từng sự kiện.
- **Dữ liệu kiểm tra nghiệp vụ:** được sinh theo quy tắc để kiểm tra truy vấn, tính toán và giao diện; không dùng để kết luận về hành vi khách hàng.

Nếu không bổ sung được dữ liệu định danh hoặc biểu cảm phù hợp, luận văn phải thu hẹp mục tiêu và chỉ tuyên bố đã kiểm nghiệm khả năng tích hợp phần mềm. Không được dùng FairFace để thay thế phép đánh giá độ chính xác nhận dạng hoặc phân loại biểu cảm.

### 5.2. Quy mô tối thiểu cho dữ liệu nhận dạng

Kế hoạch đề xuất sử dụng tối thiểu:

- 20 danh tính dành riêng cho hiệu chỉnh ngưỡng.
- 100 danh tính đã đăng ký dành cho kiểm tra.
- 20 danh tính không đăng ký để kiểm tra nguy cơ gắn nhầm.
- Mỗi danh tính đã đăng ký có ít nhất một ảnh đăng ký và bốn ảnh quan sát độc lập, tương ứng bốn khu vực.
- Ảnh đăng ký và ảnh quan sát không được là bản sao, ảnh cắt lại hoặc biến thể ánh sáng của cùng một tệp nguồn.

Tập hiệu chỉnh, tập kiểm tra khách hàng và tập người chưa đăng ký phải tách rời theo danh tính. Không thay ảnh trong tập kiểm tra chỉ vì ảnh đó làm mô hình dự đoán sai.

Nếu chưa thể thu thập đủ 100 danh tính có nhiều ảnh độc lập, phải báo cáo đúng quy mô thực tế và không dùng 100 hồ sơ CRM được tạo bằng dữ liệu nghiệp vụ để thay cho số danh tính đã được đánh giá.

### 5.3. Dữ liệu nhiều người trong một khung hình

Mỗi khu vực cần có các nhóm khung sau:

- Không có khuôn mặt.
- Một khuôn mặt.
- Hai khuôn mặt.
- Từ ba đến năm khuôn mặt.
- Có cả người đã đăng ký và chưa đăng ký.
- Có khuôn mặt nhỏ, che khuất một phần, thay đổi góc nhìn và độ sáng.

Ưu tiên sử dụng khung hình được thu nhận độc lập từ camera hoặc video có sự đồng ý của người tham gia. Nếu phải ghép ảnh, kết quả chỉ được dùng để kiểm tra xử lý nhiều vùng khuôn mặt và không được coi là bằng chứng về hiệu quả trong cảnh đông người thực tế.

### 5.4. Tệp kê khai dữ liệu

Mỗi ảnh hoặc khung hình phải có một bản ghi kê khai gồm:

- Mã tệp và mã kiểm tra SHA-256.
- Nguồn dữ liệu và điều kiện sử dụng.
- Mã danh tính ẩn danh.
- Vai trò: hiệu chỉnh, đăng ký, kiểm tra hoặc người chưa đăng ký.
- Mã khu vực và thời gian quan sát.
- Danh sách khuôn mặt có trong ảnh.
- Kết quả mong đợi.
- Thông tin ảnh có phải ảnh độc lập hay được tạo bằng phép biến đổi.

Chương trình phải kiểm tra tự động rằng không có mã danh tính hoặc mã tệp bị dùng sai giữa các tập.

## 6. Nhóm A — So sánh phương pháp phát hiện khuôn mặt

### 6.1. Mục tiêu

So sánh Haar Cascade, MTCNN và RetinaFace–MobileNet0.25 để lựa chọn bộ phát hiện cho hệ thống.

### 6.2. Dữ liệu và quy trình

- Sử dụng toàn bộ tập xác thực WIDER FACE gồm 3.226 ảnh.
- Giữ nguyên ba nhóm Easy, Medium và Hard do WIDER FACE công bố.
- Ba phương pháp nhận cùng danh sách ảnh.
- Cố định trước cấu hình của từng phương pháp.
- Chạy khởi động trước khi đo thời gian.
- Chạy ba lượt và xoay vòng thứ tự mô hình.
- Không tính thời gian đọc ảnh và ghi kết quả vào thời gian suy luận của bộ phát hiện.

### 6.3. Chỉ số

- AP Easy, AP Medium và AP Hard.
- Precision, Recall và F1 tại ngưỡng vận hành đã cố định.
- Độ trễ trung vị và phân vị 95 của riêng bộ phát hiện.
- Số ảnh xử lý trong một giây.
- Tỷ lệ ảnh có khuôn mặt chuẩn nhưng mô hình không trả về phát hiện.

### 6.4. Điều kiện hoàn thành

- Có kết quả thô cho từng ảnh, từng mô hình và từng lượt chạy.
- Kết quả AP được đối chiếu bằng bộ đánh giá WIDER FACE độc lập.
- Bảng trong luận văn được sinh tự động từ kết quả thô.
- Kết luận chỉ áp dụng cho WIDER FACE, cấu hình mô hình và phần cứng đã đo.

## 7. Nhóm B — So sánh các phương pháp phân loại biểu cảm

### 7.1. Mục tiêu và đối tượng so sánh

Thực nghiệm so sánh đúng ba hướng đã trình bày ở Chương 2:

1. **LBP kết hợp SVM:** đặc trưng LBP được tạo theo quy tắc xác định trước, SVM thực hiện phân loại bảy lớp.
2. **CNN huấn luyện từ đầu:** trọng số được khởi tạo mới và học trực tiếp từ tập huấn luyện biểu cảm.
3. **CNN sử dụng học chuyển giao:** sử dụng mạng nền đã được huấn luyện trước, thay lớp đầu ra bằng bảy lớp biểu cảm và tinh chỉnh trên tập huấn luyện của thực nghiệm.

Học chuyển giao là cách khởi tạo và huấn luyện CNN, không phải một bộ phân loại có dạng đầu ra khác. Vì vậy, cấu trúc CNN cụ thể, nguồn trọng số huấn luyện trước, số lớp được cố định hoặc tinh chỉnh và kích thước đầu vào phải được ghi rõ trước khi chạy. Nếu có thể, CNN huấn luyện từ đầu và CNN học chuyển giao sử dụng cùng một kiến trúc nền để phép so sánh phản ánh ảnh hưởng của việc sử dụng trọng số huấn luyện trước.

DeepFace không phải một phương pháp được đưa vào bảng so sánh. Nếu mã nguồn dùng DeepFace để gọi mô hình CNN hiện có thì báo cáo phải nêu tên và cấu hình của mô hình nằm phía sau thư viện.

### 7.2. Dữ liệu và cách chia tập

- Sử dụng một bộ dữ liệu có nhãn chuẩn cho bảy lớp: tức giận, ghê tởm, sợ hãi, vui vẻ, buồn bã, ngạc nhiên và trung tính.
- FER-2013 là lựa chọn phù hợp với hệ nhãn đã mô tả ở Chương 2. Việc sử dụng phải tuân theo cách chia huấn luyện, xác thực và kiểm tra đã công bố của bộ dữ liệu.
- Tập huấn luyện dùng để học tham số; tập xác thực dùng để chọn cấu hình và thời điểm dừng; tập kiểm tra chỉ dùng sau khi đã khóa cấu hình.
- Cả ba phương pháp phải nhận cùng danh sách mẫu ở từng tập. Không chuyển một ảnh từ tập kiểm tra sang tập huấn luyện chỉ vì ảnh đó bị dự đoán sai.
- Các bước phát hiện, căn chỉnh và cắt khuôn mặt phải được cố định. Nếu sử dụng ảnh khuôn mặt đã được cắt sẵn của FER-2013 thì phải ghi rõ để sai số của bộ phát hiện không bị trộn vào sai số của bộ phân loại.
- Các phép tăng cường dữ liệu chỉ áp dụng cho tập huấn luyện và phải dùng cùng một quy tắc đã công bố cho các mô hình học sâu.
- Mỗi cấu hình học máy được chạy lặp lại ít nhất ba lần với trạng thái khởi tạo ngẫu nhiên được ghi lại; báo cáo giá trị trung bình và độ lệch chuẩn. LBP--SVM tất định chỉ cần chạy lại khi quy trình của nó chứa bước ngẫu nhiên.

FairFace không có nhãn biểu cảm chuẩn nên không được dùng để huấn luyện hoặc tính độ chính xác của ba phương pháp. Ảnh FairFace chỉ giữ vai trò ảnh hồ sơ theo phạm vi dữ liệu đã xác định cho CRM.

### 7.3. Quy trình thực nghiệm

1. Chuẩn hóa nhãn và tạo danh sách ảnh cố định cho ba tập dữ liệu.
2. Tiền xử lý ảnh theo cấu hình đã khóa; lưu thông tin kích thước, ảnh xám hoặc ảnh màu và cách chuẩn hóa giá trị điểm ảnh.
3. Huấn luyện LBP--SVM trên tập huấn luyện; chọn tham số LBP và SVM bằng tập xác thực.
4. Huấn luyện CNN từ đầu; chọn siêu tham số và thời điểm dừng bằng tập xác thực.
5. Huấn luyện CNN theo học chuyển giao; ghi rõ trọng số nguồn, các lớp được cố định và các lớp được tinh chỉnh.
6. Khóa toàn bộ cấu hình, sau đó dự đoán đúng một lần trên tập kiểm tra chung.
7. Lưu dự đoán của từng ảnh, nhãn thật, điểm của các lớp, thời gian suy luận và trạng thái lỗi.
8. So sánh chất lượng, tốc độ và kích thước mô hình; lựa chọn phương pháp tích hợp dựa trên tiêu chí đã công bố trước.
9. Sau khi tích hợp phương pháp được chọn, chạy thêm kiểm thử chức năng để xác nhận API lưu đúng nhãn, điểm dự đoán và trạng thái xử lý.

### 7.4. Chỉ số và ý nghĩa

- **Accuracy:** cho biết tỷ lệ toàn bộ ảnh được phân loại đúng, nhưng có thể bị chi phối bởi lớp có nhiều mẫu.
- **Precision từng lớp:** trong các ảnh được dự đoán là một biểu cảm, có bao nhiêu ảnh thực sự thuộc biểu cảm đó.
- **Recall từng lớp:** trong các ảnh thật sự thuộc một biểu cảm, phương pháp nhận ra được bao nhiêu ảnh.
- **F1 từng lớp:** cân bằng Precision và Recall của từng biểu cảm.
- **Macro-F1:** tính F1 riêng cho bảy lớp rồi lấy trung bình, nhờ đó mỗi lớp có vai trò ngang nhau dù số lượng mẫu khác nhau.
- **Ma trận nhầm lẫn:** chỉ ra cụ thể cặp biểu cảm nào thường bị nhầm với nhau.
- **Tỷ lệ không tạo được kết quả:** ghi nhận ảnh không thể tiền xử lý hoặc mô hình không trả về dự đoán hợp lệ.
- **Độ trễ suy luận và kích thước mô hình:** cho biết chi phí khi đưa phương pháp vào luồng xử lý của hệ thống.

Phương pháp được chọn không nhất thiết là phương pháp có Accuracy cao nhất. Quyết định phải dựa trên Macro-F1, kết quả từng lớp, độ ổn định qua các lần chạy và thời gian xử lý phù hợp với yêu cầu của hệ thống.

### 7.5. Ranh giới diễn giải

- Thực nghiệm chỉ đo khả năng phân loại bảy biểu cảm trên bộ dữ liệu và giao thức đã công bố.
- Nhãn biểu cảm mô tả lớp mà mô hình dự đoán từ hình ảnh khuôn mặt; nó không trực tiếp biểu thị mức độ hài lòng, ý định mua hàng hoặc trạng thái tâm lý của khách hàng.
- Không gộp kết quả thành tích cực, trung tính và tiêu cực nếu chưa xây dựng quy tắc ánh xạ, dữ liệu nhãn và phép đánh giá riêng cho bài toán đó.
- Kết quả trên ảnh khuôn mặt đã cắt sẵn không chứng minh chất lượng của toàn bộ chuỗi xử lý camera. Chất lượng đầu-cuối được kiểm tra riêng ở Nhóm D.

## 8. Nhóm C — Đánh giá nhận dạng danh tính

### 8.1. Hiệu chỉnh ngưỡng

- Chỉ sử dụng 20 danh tính của tập hiệu chỉnh.
- Mỗi danh tính phải có nhiều ảnh độc lập.
- Tạo cặp cùng người và khác người từ các ảnh độc lập.
- Lựa chọn ngưỡng dựa trên tập hiệu chỉnh; sau khi chọn phải khóa ngưỡng.
- Không điều chỉnh lại ngưỡng sau khi xem kết quả của tập kiểm tra.
- Lưu giá trị đầy đủ trong tệp cấu hình để tái lập; trong luận văn chỉ báo cáo đến ba chữ số thập phân cùng giao thức chọn ngưỡng.

### 8.2. Kiểm tra trên danh tính chưa dùng để hiệu chỉnh

Với 100 khách hàng kiểm tra:

- Đăng ký bằng một ảnh độc lập.
- Gửi ít nhất bốn ảnh quan sát độc lập cho mỗi khách hàng.
- So sánh mỗi quan sát với toàn bộ kho 100 mẫu, không chỉ với mẫu đúng.
- Gửi ảnh của 20 người không đăng ký để kiểm tra nguy cơ gắn nhầm.

### 8.3. Chỉ số

- Tỷ lệ xác định đúng khách hàng.
- Tỷ lệ từ chối nhầm khách hàng đã đăng ký.
- Tỷ lệ gắn nhầm người chưa đăng ký vào một hồ sơ.
- Tỷ lệ gắn một khách hàng vào sai hồ sơ.
- Phân bố khoảng cách của cặp cùng người và khác người.
- Đường ROC, EER hoặc TAR tại các mức FAR được xác định trước nếu quy mô dữ liệu cho phép.

### 8.4. Phân tích sai số

Các trường hợp sai phải được phân nhóm theo:

- Góc mặt.
- Che khuất.
- Ánh sáng.
- Kích thước khuôn mặt.
- Chất lượng ảnh.
- Số người trong khung.

Không loại mẫu sai khỏi kết quả. Mọi tiêu chí loại ảnh phải được xác định trước khi chạy.

## 9. Nhóm D — Kiểm nghiệm vận hành đầu-cuối

### 9.1. Các luồng bắt buộc

1. Đăng ký mẫu khuôn mặt khi khách hàng đã đồng ý.
2. Từ chối đăng ký khi không có khuôn mặt hoặc có nhiều khuôn mặt.
3. Xử lý khung có nhiều khuôn mặt thành nhiều quan sát độc lập.
4. Liên kết đúng quan sát với khách hàng đã đăng ký.
5. Không tạo bản ghi quan sát khi kết quả đối sánh là `NO_MATCH`.
6. Không tạo quan sát cho ảnh `NO_FACE` hoặc `INVALID_IMAGE`.
7. Không tạo bản ghi trùng khi gửi lại cùng mã sự kiện.
8. Tạo, cập nhật và kết thúc lần mua sắm theo thời gian quan sát.
9. Xử lý bản ghi đến muộn, xung đột thời gian và thiếu khu vực.
10. Liên kết đơn hàng đúng khách hàng và đúng lần mua sắm.
11. Xử lý lại quan sát phải tạo lịch sử thay đổi và chỉ chấp nhận ảnh khớp khách hàng đã đăng ký.
12. Báo cáo phải tách được dữ liệu theo nguồn, khu vực và thời gian.

### 9.2. Hậu điều kiện của mỗi sự kiện

Mỗi ca chỉ được tính là đạt khi đồng thời đối chiếu được:

- Mã trạng thái HTTP.
- Trạng thái ảnh.
- Số khuôn mặt.
- Số quan sát tạo ra.
- Trạng thái phân loại biểu cảm.
- Trạng thái nhận dạng.
- Mã khách hàng nếu có.
- Mã lần mua sắm nếu có.
- Khu vực và thời gian quan sát.
- Dữ liệu trả về từ API.
- Dữ liệu đã lưu trong PostgreSQL.

Không chỉ kiểm tra phản hồi API. Bộ kiểm tra phải đọc lại bản ghi từ cơ sở dữ liệu hoặc API truy vấn độc lập sau khi giao dịch hoàn tất.

### 9.3. Kiểm nghiệm chuỗi bốn khu vực

- Cả 100 khách hàng kiểm tra cần có ít nhất một chuỗi đủ bốn khu vực nếu luận văn muốn chứng minh phương pháp ở quy mô 100 khách hàng.
- Mỗi khu vực phải dùng một ảnh quan sát độc lập của cùng người.
- Thời gian phải tăng theo đúng thứ tự khu vực.
- Ít nhất một nhóm ca phải có khu vực bị thiếu, bản ghi đến muộn và xung đột thời gian.
- Kết quả phải kiểm tra chính xác chuỗi khu vực, không chỉ kiểm tra rằng truy vấn trả về dữ liệu không rỗng.

## 10. Nhóm E — Đo hiệu năng đầu-cuối

### 10.1. Định nghĩa yêu cầu xử lý theo thời gian

Hệ thống chỉ được gọi là đáp ứng yêu cầu xử lý theo thời gian khi kết quả của một khung được hoàn tất trước khi khung tiếp theo của cùng nguồn cần được xử lý và không hình thành hàng đợi tăng liên tục.

Trong phạm vi thực nghiệm, nguồn thu nhận phải được cấu hình với tần suất cụ thể, ví dụ một khung mỗi giây. Tiêu chí đạt được xác định trước:

- Phân vị 95 của độ trễ đầu-cuối không vượt quá khoảng thời gian giữa hai khung của cùng nguồn.
- Tỷ lệ yêu cầu lỗi không vượt quá ngưỡng đã xác định.
- Hàng đợi không tăng liên tục trong toàn bộ thời gian chạy.

Nếu hệ thống không đạt tiêu chí, báo cáo phải dùng cụm “xử lý theo từng khung hình” thay cho “theo thời gian thực”.

### 10.2. Các mốc thời gian cần ghi nhận

Mỗi yêu cầu cần lưu:

- Thời điểm nguồn bắt đầu gửi ảnh.
- Thời điểm API nhận đủ dữ liệu.
- Thời gian phát hiện khuôn mặt.
- Thời gian phân loại biểu cảm.
- Thời gian tạo véc-tơ ArcFace.
- Thời gian đối sánh kho mẫu.
- Thời gian xử lý nghiệp vụ và ghi cơ sở dữ liệu.
- Thời điểm API trả phản hồi.
- Thời điểm bản ghi có thể được đọc lại từ CRM.

Từ đó tính:

- Độ trễ đầu-cuối trung vị, phân vị 95 và phân vị 99.
- Thông lượng yêu cầu mỗi giây.
- Độ trễ hàng đợi.
- Tỷ lệ lỗi và tỷ lệ hết thời gian chờ.
- CPU, bộ nhớ và dung lượng cơ sở dữ liệu.

### 10.3. Ma trận tải

Chạy riêng các trường hợp:

| Nguồn đồng thời | Số mặt mỗi khung | Tần suất mỗi nguồn | Thời gian chạy |
|---:|---:|---:|---:|
| 1 | 0–1 | 1 khung/giây | 30 phút |
| 1 | 2–5 | 1 khung/giây | 30 phút |
| 2 | 0–2 | 1 khung/giây | 30 phút |
| 4 | 0–2 | 1 khung/giây | 30 phút |

Nếu cấu hình phần cứng không đáp ứng được 1 khung/giây, giảm tần suất và báo cáo đúng năng lực đo được; không thay đổi tiêu chí sau khi đã xem kết quả mà không ghi nhận.

## 11. Nhóm F — Kiểm thử quy tắc CRM và báo cáo

### 11.1. Bộ dữ liệu tính tay

Tạo một bộ dữ liệu nhỏ, cố định và có thể tính bằng tay, gồm:

- Một số khách hàng đã đăng ký.
- Bốn khu vực có thứ tự xác định.
- Các lần mua sắm đủ khu vực, thiếu khu vực và xung đột thời gian.
- Nhãn biểu cảm được quy định trước.
- Quan sát của khách hàng đã đăng ký và sự kiện `NO_MATCH` không tạo quan sát.
- Đơn hàng có và không liên kết lần mua sắm.

Bộ dữ liệu này dùng để kiểm tra thuật toán truy vấn, không đại diện cho hành vi thực tế.

### 11.2. Kết quả phải đối chiếu chính xác

- Số lượng và tỷ lệ từng nhãn tại từng khu vực.
- Kết quả lọc theo khoảng thời gian.
- Xác nhận báo cáo không chứa sự kiện `NO_MATCH`.
- Số lượng trong từng khoảng thời gian 5, 15, 30 và 60 phút.
- Cặp thay đổi nhãn giữa hai khu vực liên tiếp.
- Cách chọn bản ghi đầu tiên, cuối cùng và có mức tin cậy cao nhất.
- Loại bỏ bản ghi xung đột.
- Danh sách khu vực bị thiếu.
- Số lần mua sắm đủ điều kiện phân tích.

Bộ kiểm tra phải so sánh toàn bộ kết quả với tệp mong đợi, không chỉ kiểm tra rằng API trả về danh sách không rỗng.

### 11.3. Tách nguồn dữ liệu trên báo cáo

API và giao diện cần có bộ lọc tối thiểu:

- Kết quả đi qua mô hình xử lý ảnh.
- Dữ liệu kiểm tra nghiệp vụ được sinh theo quy tắc.
- Tất cả nguồn.

Các hình trong Chương 4 có thể dùng dữ liệu kiểm tra nghiệp vụ để minh họa chức năng nhưng phải chú thích rõ. Các biểu đồ trong Chương 5 chỉ được dùng làm kết quả thực nghiệm khi nguồn dữ liệu và giao thức tạo dữ liệu đã được nêu rõ.

## 12. Nhóm G — Kiểm thử độ tin cậy, bảo mật và dữ liệu cá nhân

### 12.1. Độ tin cậy

- Dịch vụ xử lý ảnh không phản hồi.
- PostgreSQL tạm thời mất kết nối.
- Yêu cầu bị gửi lại sau khi hết thời gian chờ.
- Hai yêu cầu có cùng mã sự kiện.
- Ảnh rỗng, sai định dạng hoặc vượt dung lượng.
- Thời gian không có múi giờ hoặc sai định dạng.
- Khu vực không tồn tại hoặc đã ngừng hoạt động.
- Khung bao không tạo được vùng ảnh hợp lệ.

### 12.2. Phân quyền và dữ liệu khuôn mặt

- Người không đăng nhập không truy cập được API nghiệp vụ.
- Vai trò không phù hợp không thể đăng ký, tìm kiếm hoặc xác nhận khuôn mặt.
- Không tạo mẫu khi khách hàng chưa đồng ý.
- Khi rút lại đồng ý, mẫu khuôn mặt không còn được dùng để đối sánh.
- Mỗi thay đổi thủ công phải có người thực hiện, thời gian, lý do và dữ liệu trước thay đổi.
- Phản hồi API và nhật ký không làm lộ véc-tơ khuôn mặt ngoài phạm vi cần thiết.

## 13. Thay đổi mã nguồn cần thực hiện trước khi chạy lại

1. Xây dựng chung một giao diện chạy dự đoán cho LBP--SVM, CNN huấn luyện từ đầu và CNN học chuyển giao.
2. Bổ sung quy trình chuẩn bị FER-2013, kiểm tra trùng lặp và khóa danh sách mẫu của ba tập.
3. Bổ sung chương trình huấn luyện, lựa chọn cấu hình bằng tập xác thực và đánh giá trên tập kiểm tra cho ba phương pháp phân loại biểu cảm.
4. Bổ sung đo thời gian cho từng công đoạn và thời gian đầu-cuối.
5. Bổ sung mã lần chạy, mã cấu hình và mã mô hình vào mọi tệp kết quả.
6. Thay dữ liệu nhận dạng cùng ảnh nguồn bằng ảnh độc lập của cùng danh tính.
7. Chia danh tính thành tập hiệu chỉnh, tập kiểm tra và tập người chưa đăng ký không giao nhau.
8. Loại bỏ bước sàng lọc mẫu dựa trên kết quả dự đoán của tập kiểm tra.
9. Mở rộng bộ phát lại để kiểm tra trạng thái biểu cảm, mã lần mua sắm và dữ liệu đọc lại sau khi lưu.
10. Thêm bộ lọc nguồn dữ liệu vào API báo cáo và giao diện.
11. Thay kiểm tra “kết quả không rỗng” bằng đối chiếu chính xác với kết quả mong đợi.
12. Bổ sung chương trình phát khung hình liên tục từ video hoặc camera với tần suất cấu hình được.
13. Tạo một lệnh duy nhất để chuẩn bị dữ liệu, chạy kiểm thử, khóa đầu ra và sinh bảng cho báo cáo.

## 14. Tổ chức đầu ra thực nghiệm

Mỗi lần chạy chính thức tạo một thư mục bất biến:

```text
artifacts/experiment-runs/<run-id>/
├── run-manifest.json
├── environment.json
├── dataset-manifest.csv
├── model-config.json
├── detector-results.jsonl
├── expression-training-runs.jsonl
├── expression-test-predictions.jsonl
├── expression-confusion-matrices/
├── expression-summary.json
├── identity-calibration.json
├── identity-test-results.jsonl
├── end-to-end-latency.jsonl
├── operational-checks.json
├── report-checks.json
├── database-counts.json
├── test-results.txt
└── summary.json
```

`run-manifest.json` phải ghi:

- Thời gian chạy.
- Mã commit.
- Cấu hình phần cứng và phần mềm.
- Mã kiểm tra của dữ liệu và trọng số mô hình.
- Tham số của từng phép kiểm tra.
- Danh sách tệp đầu ra.
- Trạng thái hoàn thành hoặc thất bại.

Không sử dụng thư mục `latest` làm nguồn trích dẫn duy nhất trong luận văn vì nội dung có thể bị ghi đè. Luận văn phải tham chiếu một `run-id` cố định.

## 15. Thứ tự thực hiện

### Giai đoạn 1 — Khóa yêu cầu và dữ liệu

- Quyết định có giữ mục tiêu “theo thời gian thực” hay đổi thành “xử lý theo từng khung hình”.
- Chọn hoặc thu thập dữ liệu nhận dạng có nhiều ảnh độc lập cho mỗi người.
- Khóa cấu hình cụ thể của LBP--SVM, kiến trúc CNN huấn luyện từ đầu và kiến trúc CNN học chuyển giao.
- Chuẩn bị FER-2013 và khóa danh sách mẫu của tập huấn luyện, xác thực và kiểm tra.
- Hoàn thành tệp kê khai và kiểm tra chồng lặp dữ liệu.

### Giai đoạn 2 — Sửa công cụ kiểm thử

- Viết quy trình huấn luyện và đánh giá thống nhất cho ba phương pháp phân loại biểu cảm.
- Xuất dự đoán từng ảnh, ma trận nhầm lẫn, chỉ số từng lớp và thời gian suy luận.
- Bổ sung đo thời gian đầu-cuối.
- Bổ sung tách nguồn dữ liệu.
- Viết kiểm tra chính xác cho báo cáo.
- Viết kiểm tra dữ liệu sau khi lưu.
- Khóa ngưỡng nhận dạng từ tập hiệu chỉnh.

### Giai đoạn 3 — Chạy từng nhóm độc lập

1. So sánh bộ phát hiện.
2. Huấn luyện, so sánh và lựa chọn phương pháp phân loại biểu cảm.
3. Hiệu chỉnh và đánh giá nhận dạng danh tính.
4. Kiểm nghiệm luồng đầu-cuối.
5. Đo tải và độ trễ.
6. Kiểm thử CRM, báo cáo, lỗi và phân quyền.

Một nhóm thất bại không được che bằng kết quả của nhóm khác.

### Giai đoạn 4 — Chạy tích hợp chính thức

- Xóa dữ liệu của các lần kiểm tra trước theo cơ chế có kiểm soát.
- Khởi động đúng cấu hình mô hình chính thức.
- Chạy toàn bộ quy trình bằng một lệnh.
- Khóa thư mục kết quả theo `run-id`.
- Đối chiếu số liệu giữa JSON/CSV, PostgreSQL, bảng và ảnh giao diện.

### Giai đoạn 5 — Cập nhật luận văn

- Chỉ đưa vào báo cáo các kết quả có tệp nguồn trong lần chạy đã khóa.
- Chương 4 dùng ảnh để minh họa chức năng đã xây dựng.
- Chương 5 trình bày dữ liệu, giao thức, kết quả, phân tích sai số và giới hạn.
- Không trình bày dữ liệu sinh theo quy tắc như quan sát về hành vi khách hàng.

## 16. Tiêu chí chấp nhận cuối cùng

Hệ thống chỉ được coi là hoàn thành kiểm thử khi:

- Toàn bộ kiểm thử tự động của API, dịch vụ xử lý ảnh và giao diện đều đạt.
- Mã, cấu hình, dữ liệu, cơ sở dữ liệu và báo cáo thuộc cùng một lần chạy.
- Mỗi con số trong Chương 5 truy vết được đến tệp kết quả thô.
- Không có ảnh đăng ký và ảnh kiểm tra danh tính được tạo từ cùng một tệp nguồn.
- Ngưỡng nhận dạng được khóa trước khi chạy tập kiểm tra.
- Các biểu đồ tách rõ dữ liệu mô hình và dữ liệu kiểm tra nghiệp vụ.
- Có kết quả độ trễ đầu-cuối nếu tiếp tục sử dụng cụm “theo thời gian thực”.
- Các trường hợp sai và không đạt vẫn được giữ trong kết quả.
- Kết luận không vượt quá phạm vi dữ liệu và tiêu chí đã đo.

## 17. Cách xử lý các kết quả hiện có

| Kết quả hiện có | Cách sử dụng sau khi lập lại kế hoạch |
|---|---|
| AP và thời gian của Haar Cascade, MTCNN, RetinaFace trên WIDER FACE | Giữ lại sau khi xác nhận đầy đủ mã và đầu ra thô |
| 64,53 ms của RetinaFace | Chỉ ghi là thời gian của bộ phát hiện, không dùng làm độ trễ hệ thống |
| Ngưỡng `0.2699579474500632` | Chỉ giữ như cấu hình của lần kiểm nghiệm cũ; không dùng cho đánh giá nhận dạng mới |
| Kết quả 115/115 | Chuyển thành kiểm thử hồi quy luồng phần mềm; không báo cáo là độ chính xác nhận dạng |
| 125 lần mua sắm và 90 đơn hàng | Dùng kiểm thử tải nghiệp vụ, truy vấn và giao diện; không phân tích hành vi |
| Các nhãn được sinh theo quy tắc | Dùng để đối chiếu phép nhóm và báo cáo; không đánh giá mô hình phân loại biểu cảm |
| Năm chuỗi bốn khu vực | Chỉ giữ như ca kiểm tra ban đầu; thực nghiệm mới phải mở rộng theo quy mô đã công bố |
| Tệp kết quả 119 quan sát của lần chạy cũ | Lưu vào thư mục lưu trữ, không dùng làm bằng chứng cho thiết kế 236 quan sát |

## 18. Kết luận của kế hoạch

Kế hoạch mới không cố gắng chứng minh mọi mục tiêu bằng một bộ dữ liệu duy nhất. Chất lượng mô hình, tính đúng của phần mềm, hiệu năng đầu-cuối và khả năng phân tích đa điểm chạm là bốn câu hỏi khác nhau và phải có dữ liệu cùng tiêu chí riêng.

Sau khi thực hiện kế hoạch này, luận văn có thể kết luận ở ba mức rõ ràng:

1. Thành phần nào có chất lượng tốt hơn trong giao thức đánh giá đã chọn.
2. Hệ thống có thực hiện đúng các quy tắc và luồng dữ liệu đã thiết kế hay không.
3. Hệ thống đạt mức hiệu năng nào trên cấu hình phần cứng và tải đã đo.

Các kết luận về cảm xúc, mức độ hài lòng hoặc hành vi của khách hàng chỉ được đưa ra khi có dữ liệu thực tế và nhãn đối chiếu phù hợp; chúng không thuộc phạm vi của dữ liệu kiểm tra nghiệp vụ được sinh theo quy tắc.
