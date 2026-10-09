# Nghiên cứu phương pháp xử lý chuỗi biểu cảm theo thời gian

## 1. Bài toán hiện tại

Hệ thống đang lưu mỗi quan sát với các trường chính:

- `visit_id`: lần mua sắm;
- `customer_id`: khách hàng nếu nhận dạng được;
- `touchpoint_id`: khu vực/điểm chạm;
- `observed_at`: thời điểm ghi nhận;
- `expression_label`: nhãn có xác suất cao nhất;
- `expression_confidence`: độ tin cậy của nhãn đã chọn;
- `expression_scores`: véc-tơ điểm hoặc xác suất của đủ bảy lớp;
- trạng thái ảnh, phân loại, nhận dạng và phiên bản mô hình.

Endpoint báo cáo hiện tại sắp xếp quan sát theo `visit_id` và `observed_at`, gom các quan sát liên tiếp tại cùng khu vực, chọn một bản ghi đại diện theo một trong ba quy tắc `first`, `last` hoặc `highest_confidence`, sau đó đếm cặp nhãn giữa hai khu vực liên tiếp.

Như vậy, đầu ra hiện tại là một **bảng chuyển đổi nhãn trước--sau**, chưa phải một mô hình chuỗi thời gian hoàn chỉnh. Dữ liệu cũng có tính chất **chuỗi sự kiện theo thời gian không đều** hơn là chuỗi thời gian lấy mẫu đều: số quan sát trong mỗi lần mua sắm khác nhau, khoảng cách thời gian khác nhau và có thể thiếu khu vực.

Mục tiêu phù hợp ở giai đoạn hiện tại là:

1. mô tả xác suất chuyển đổi giữa các biểu cảm;
2. giảm dao động nhãn do nhiễu của mô hình FER;
3. tìm các kiểu hành trình biểu cảm tương tự nhau;
4. phát hiện thời điểm phân bố biểu cảm thay đổi khi có chuỗi đủ dày;
5. không suy diễn nhãn biểu cảm thành mức độ hài lòng nếu chưa có nhãn khảo sát hoặc kết quả nghiệp vụ để kiểm chứng.

## 2. Kết luận lựa chọn phương pháp

| Mức ưu tiên | Phương pháp | Có thể dùng với dữ liệu hiện tại? | Mục tiêu chính |
|---|---|---|---|
| **1** | Ma trận chuyển trạng thái/chuỗi Markov bậc một | Có | Mô tả xác suất nhãn tiếp theo theo nhãn hiện tại và cặp khu vực |
| **2** | HMM để làm trơn chuỗi nhãn | Có điều kiện | Ước lượng trạng thái biểu cảm ổn định hơn từ dự đoán FER nhiễu |
| **3** | Soft-DTW + phân cụm | Có, nếu giữ đủ bảy xác suất | Nhóm các lần mua sắm có quỹ đạo biểu cảm tương tự nhưng độ dài khác nhau |
| **4** | Mixture of Markov Models | Có khi số lần mua sắm đủ lớn | Tự động tìm nhiều kiểu chuỗi chuyển trạng thái khác nhau |
| **5** | PELT hoặc Bayesian Online Change-Point Detection | Chưa phù hợp với chuỗi rất ngắn | Phát hiện thời điểm chế độ/phân bố biểu cảm thay đổi |
| **6** | HSMM | Chỉ phù hợp khi có chuỗi dày và thời lượng đáng tin cậy | Mô hình hóa cả trạng thái ẩn và thời gian lưu trong trạng thái |
| **7** | CRF, LSTM/GRU, Transformer hoặc mô hình DFER | Chưa nên dùng với bảng hiện tại | Học phụ thuộc dài hạn khi có dữ liệu chuỗi đã gán nhãn hoặc video gốc |

Đề xuất thực tế nhất cho đồ án là triển khai **ma trận chuyển trạng thái có điều kiện theo cặp khu vực** làm baseline, sau đó thử **HMM làm trơn chuỗi**. Soft-DTW và phân cụm là hướng mở rộng phù hợp nếu có đủ số lần mua sắm thật.

## 3. Phương pháp 1 — Ma trận chuyển trạng thái và chuỗi Markov

### 3.1. Ý tưởng

Với chuỗi nhãn quan sát \(y_1,y_2,\ldots,y_T\), đếm số lần chuyển từ nhãn \(i\) sang nhãn \(j\):

\[
N_{ij}=\sum_{t=1}^{T-1}\mathbb{1}(y_t=i,y_{t+1}=j).
\]

Xác suất chuyển trạng thái bậc một được ước lượng bởi:

\[
P_{ij}=P(y_{t+1}=j\mid y_t=i)=\frac{N_{ij}}{\sum_k N_{ik}}.
\]

Có thể tính một ma trận chung hoặc một ma trận riêng cho từng cặp khu vực, ví dụ `Cửa vào → Trưng bày` và `Trưng bày → Thanh toán`.

### 3.2. Khác biệt với bảng hiện tại

Endpoint hiện tại tính tỷ lệ trên **tổng số cặp của hai khu vực**. Ma trận Markov cần chuẩn hóa theo **nhãn nguồn**, nghĩa là tổng mỗi hàng bằng 1. Khi đó mới trả lời được câu hỏi: “Nếu nhãn trước là Neutral thì xác suất nhãn sau là Happy, Sad, Neutral... bằng bao nhiêu?”

### 3.3. Nên dùng véc-tơ xác suất thay vì chỉ nhãn cực đại

Nếu quan sát \(t\) có véc-tơ xác suất \(p_t\in\mathbb{R}^7\), có thể cộng “chuyển đổi mềm”:

\[
N_{ij}^{soft}=\sum_t p_t(i)p_{t+1}(j).
\]

Đây là một mở rộng phù hợp với dữ liệu của hệ thống vì nó giữ lại độ bất định. Ví dụ một dự đoán 0,36 Happy và 0,34 Neutral không nên được xử lý như chắc chắn 100% Happy.

### 3.4. Đầu ra nên báo cáo

- ma trận xác suất chuyển đổi 7 x 7;
- số mẫu hỗ trợ của từng hàng và từng cặp khu vực;
- tỷ lệ giữ nguyên nhãn (đường chéo);
- tỷ lệ đổi nhãn;
- entropy của phân bố trạng thái kế tiếp;
- khoảng tin cậy bootstrap theo **lần mua sắm**, không bootstrap từng dòng độc lập;
- so sánh Markov bậc một với bậc hai bằng log-likelihood trên tập giữ lại và AIC/BIC.

### 3.5. Lý do phù hợp

- Dữ liệu hiện tại đã có chuỗi nhãn, thời gian và cặp khu vực nên không cần thu thêm nhãn để làm phân tích mô tả.
- Kết quả dễ giải thích và phù hợp với giao diện Sankey/bảng hiện tại.
- Có thể kiểm tra giả định bậc một trước khi dùng mô hình phức tạp hơn.
- Nghiên cứu về customer journey đã dùng first- và higher-order Markov walks để phản ánh bản chất tuần tự của đường đi khách hàng; đây là cơ sở gần nhất với cấu trúc điểm chạm của hệ thống ([Anderl et al., 2016](https://doi.org/10.1016/j.ijresmar.2016.03.001)).

### 3.6. Giới hạn

- Markov bậc một giả định trạng thái tiếp theo chỉ phụ thuộc trạng thái hiện tại.
- Chuỗi ngắn làm nhiều ô trong ma trận có số mẫu rất thấp.
- Tần suất chuyển nhãn không chứng minh trải nghiệm tốt lên hoặc xấu đi.
- Nếu chỉ dùng nhãn cực đại, dao động nhỏ trong điểm số FER có thể tạo chuyển trạng thái giả.

## 4. Phương pháp 2 — Hidden Markov Model để làm trơn chuỗi

### 4.1. Ý tưởng

HMM phân biệt:

- \(z_t\): trạng thái biểu cảm ẩn, ổn định hơn nhưng không quan sát trực tiếp;
- \(y_t\) hoặc \(p_t\): nhãn/véc-tơ xác suất do bộ phân loại FER trả về.

Mô hình học:

1. ma trận chuyển giữa các trạng thái ẩn;
2. phân bố phát xạ cho biết một trạng thái ẩn có thể tạo ra dự đoán FER nào.

Sau đó dùng thuật toán Viterbi hoặc xác suất hậu nghiệm để suy ra chuỗi trạng thái ẩn phù hợp nhất. HMM là nền tảng kinh điển cho dữ liệu chuỗi ([Rabiner, 1989](https://doi.org/10.1109/5.18626)). Trong nhận dạng biểu cảm video, Cohen và cộng sự đã dùng kiến trúc nhiều tầng gồm HMM và Markov model để tự động phân đoạn và nhận dạng biểu cảm theo thời gian ([Cohen et al., 2003](https://doi.org/10.1016/S1077-3142(03)00081-X)).

### 4.2. Hai cách áp dụng

**Cách A — dùng nhãn rời rạc:**

- quan sát là một trong bảy nhãn;
- ma trận phát xạ có thể khởi tạo từ confusion matrix của bộ phân loại;
- trạng thái ẩn có thể đặt tương ứng với bảy biểu cảm.

**Cách B — dùng đủ bảy xác suất:**

- quan sát là véc-tơ `expression_scores`;
- phát xạ có thể dùng phân bố phù hợp với dữ liệu xác suất, hoặc biến đổi log-ratio rồi dùng Gaussian;
- giữ được nhiều thông tin hơn nhãn cực đại nhưng cài đặt phức tạp hơn.

### 4.3. Khi nào nên dùng

HMM phù hợp khi một khách hàng có nhiều quan sát liên tiếp và nhãn FER dao động kiểu `Neutral → Happy → Neutral` trong thời gian rất ngắn. Nó có thể giảm các lần đổi nhãn do nhiễu mà không phải dùng quy tắc cứng “chọn confidence cao nhất”.

Với chuỗi giữa các khu vực, không nên coi hai quan sát cách nhau 2 giây và 10 phút là tương đương. Có ba lựa chọn:

1. resample về khoảng thời gian đều nếu có dữ liệu đủ dày;
2. chia ma trận chuyển theo cặp khu vực và khoảng thời gian;
3. chuyển sang HSMM hoặc mô hình thời gian liên tục khi dữ liệu đủ lớn.

### 4.4. Cách đánh giá

Cần một tập chuỗi camera được gán nhãn thủ công để so sánh:

- Macro-F1 theo khung hoặc quan sát;
- Macro-F1 theo đoạn biểu cảm;
- số lần chuyển trạng thái giả;
- edit distance giữa chuỗi dự đoán và chuỗi chuẩn;
- độ trễ phát hiện khi biểu cảm thực sự thay đổi;
- log-likelihood trên chuỗi giữ lại.

Không nên tuyên bố HMM cải thiện độ chính xác nếu chỉ quan sát thấy đường biểu diễn “mượt hơn” mà không có nhãn chuẩn.

## 5. Phương pháp 3 — Hidden Semi-Markov Model

HMM ngầm tạo thời gian lưu trạng thái theo phân bố hình học. HSMM mở rộng HMM bằng cách mô hình hóa trực tiếp thời lượng của từng trạng thái ([Yu, 2010](https://doi.org/10.1016/j.artint.2009.11.011)).

HSMM có thể trả lời các câu hỏi như:

- trạng thái Neutral thường kéo dài bao lâu tại một khu vực;
- trạng thái Happy có xu hướng xuất hiện ngắn hay kéo dài;
- thời lượng trạng thái có khác nhau giữa các khu vực hay không.

Tuy nhiên, phương pháp này chỉ có ý nghĩa khi hệ thống có quan sát dày, liên tục và thời điểm bắt đầu/kết thúc trạng thái đủ đáng tin cậy. Với một vài bản ghi rời rạc ở mỗi khu vực, “thời lượng biểu cảm” chủ yếu phản ánh lịch chụp ảnh chứ chưa phản ánh thời lượng thật.

## 6. Phương pháp 4 — Soft-DTW và phân cụm quỹ đạo biểu cảm

Dynamic Time Warping căn chỉnh hai chuỗi có độ dài hoặc tốc độ diễn biến khác nhau. Soft-DTW là phiên bản trơn, có thể dùng để tính trung tâm và phân cụm chuỗi ([Cuturi & Blondel, 2017](https://proceedings.mlr.press/v70/cuturi17a.html)).

Mỗi lần mua sắm được biểu diễn bởi:

\[
X_v=[p_1,p_2,\ldots,p_T],\quad p_t\in\mathbb{R}^7.
\]

Sau đó:

1. tính khoảng cách Soft-DTW giữa các lần mua sắm;
2. dùng k-medoids hoặc phân cụm phân cấp;
3. mô tả mỗi cụm bằng hành trình đại diện, khu vực đi qua và phân bố biểu cảm.

### Lý do phù hợp

- Các lần mua sắm có số quan sát khác nhau.
- Hai chuỗi có thể cùng kiểu diễn biến nhưng xảy ra nhanh/chậm khác nhau.
- Không yêu cầu nhãn đích, phù hợp với phân tích khám phá.

### Điều kiện và giới hạn

- Nên dùng véc-tơ bảy xác suất, không mã hóa bảy nhãn thành các số 0–6 rồi tính khoảng cách Euclid vì các nhãn không có thứ tự tuyến tính.
- Cần ràng buộc căn chỉnh theo thứ tự khu vực để tránh ghép một quan sát ở cửa vào với một quan sát ở quầy thanh toán chỉ vì xác suất giống nhau.
- Chỉ số silhouette và độ ổn định của cụm cần được báo cáo, nhưng cụm vẫn cần chuyên gia kiểm tra để đặt ý nghĩa.

## 7. Phương pháp 5 — Mixture of Markov Models

Thay vì một ma trận chuyển chung cho mọi lượt mua sắm, giả định tồn tại nhiều nhóm hành trình, mỗi nhóm có một ma trận Markov riêng. Cadez và cộng sự dùng mixture of first-order Markov models để phân cụm các chuỗi điều hướng theo thứ tự truy cập ([Cadez et al., 2003](https://www.microsoft.com/en-us/research/publication/model-based-clustering-and-visualization-of-navigation-patterns-on-a-web-site/)).

Áp dụng tương ứng cho hệ thống:

- cụm 1 có thể chủ yếu giữ Neutral;
- cụm 2 thường chuyển từ Neutral sang Happy;
- cụm 3 có chuỗi dao động hoặc nhiều trạng thái không chắc chắn.

Đây chỉ là ví dụ về cách đọc cụm, không phải nhãn cần gán trước. Số cụm nên được chọn bằng BIC, likelihood trên tập kiểm tra và độ ổn định qua bootstrap. Phương pháp cần nhiều lượt mua sắm hơn ma trận Markov đơn; không nên dùng trên dữ liệu mô phỏng để kết luận về khách hàng thật.

## 8. Phương pháp 6 — Phát hiện điểm thay đổi

Nếu hệ thống thu được chuỗi xác suất dày theo thời gian, có thể tìm thời điểm phân bố biểu cảm thay đổi rõ rệt.

- **PELT** là phương pháp offline, tìm phân đoạn tối ưu với pruning và có chi phí tuyến tính dưới các điều kiện của phương pháp ([Killick, Fearnhead & Eckley, 2012](https://doi.org/10.1080/01621459.2012.737745)).
- **Bayesian Online Change-Point Detection** cập nhật trực tuyến phân bố xác suất của thời gian kể từ điểm thay đổi gần nhất ([Adams & MacKay, 2007](https://arxiv.org/abs/0710.3742)).

Đầu vào nên là véc-tơ bảy xác suất hoặc một embedding liên tục. Nếu chuyển bảy nhãn sang một trục “tích cực--tiêu cực”, phải có cơ sở thực nghiệm cho ánh xạ đó; không được tự mặc định Happy là hài lòng và Sad/Angry là không hài lòng.

Với chuỗi hiện tại chỉ có vài điểm cho mỗi lượt mua sắm, change-point detection chưa đáng tin cậy. Hướng này phù hợp hơn khi lưu dự đoán theo khung hình hoặc theo cửa sổ thời gian ngắn.

## 9. Phương pháp 7 — CRF và mô hình học sâu theo chuỗi

CRF mô hình hóa phụ thuộc giữa các nhãn liên tiếp khi thực hiện sequence tagging. Một nghiên cứu về emotion recognition in conversation dùng encoder LSTM/Transformer và lớp CRF để học tính nhất quán biểu cảm trong hội thoại ([Wang et al., 2020](https://aclanthology.org/2020.sigdial-1.23/)). Ý tưởng phụ thuộc nhãn liên tiếp có thể chuyển sang chuỗi biểu cảm khuôn mặt, nhưng miền dữ liệu hội thoại khác miền camera bán lẻ.

LSTM, GRU, Temporal CNN và Transformer có thể học phụ thuộc dài hạn trực tiếp từ chuỗi đặc trưng. Các mô hình Dynamic Facial Expression Recognition gần đây học từ video hoặc đoạn khung hình, không chỉ từ bảng nhãn đã rút gọn. Ví dụ:

- DFEW cung cấp hơn 16.000 đoạn video và phân bố bảy biểu cảm cho Dynamic FER ngoài tự nhiên ([Jiang et al., 2020](https://doi.org/10.1145/3394171.3413620));
- FERV39k có 38.935 đoạn video thuộc nhiều cảnh và bảy lớp biểu cảm ([Wang et al., 2022](https://openaccess.thecvf.com/content/CVPR2022/html/Wang_FERV39k_A_Large-Scale_Multi-Scene_Dataset_for_Facial_Expression_Recognition_in_CVPR_2022_paper.html));
- M3DFEL kết hợp quan hệ ngắn hạn bằng các đoạn 3D và tổng hợp quan hệ dài hạn, được đánh giá trên DFEW và FERV39k ([Wang et al., 2023](https://openaccess.thecvf.com/content/CVPR2023/papers/Wang_Rethinking_the_Learning_Paradigm_for_Dynamic_Facial_Expression_Recognition_CVPR_2023_paper.pdf)).

Nhóm phương pháp này chỉ nên triển khai khi có:

- video hoặc đặc trưng từng khung hình;
- nhiều chuỗi;
- nhãn chuẩn theo đoạn/khung hoặc một biến đích rõ ràng;
- giao thức chia tập theo người để tránh cùng một khách hàng xuất hiện ở cả tập huấn luyện và kiểm tra.

Nếu chỉ còn bảng nhãn/xác suất sau suy luận, mô hình học sâu theo video không thể phục hồi các chuyển động khuôn mặt đã bị mất.

## 10. Đề xuất nâng cấp bảng export

Không nên chỉ export bảng đã tổng hợp thành cặp nhãn. Cần một bảng **observation-level** với mỗi hàng là một quan sát:

| Nhóm trường | Trường đề xuất |
|---|---|
| Định danh chuỗi | `visit_id`, `customer_id`, `observation_id`, `event_id` |
| Thứ tự | `touchpoint_id`, `touchpoint_sequence_order`, `observed_at`, `received_at` |
| Dự đoán FER | `expression_label`, `expression_confidence`, bảy cột `score_*` |
| Chất lượng | `detection_score`, `image_status`, `expression_status`, `identity_status` |
| Truy vết | `emotion_model_version`, `source_type`, `demo_data` |
| Khoảng thời gian | `delta_seconds_from_previous`, `time_in_touchpoint_seconds` nếu tính được |

Quy tắc export:

- sắp xếp theo `visit_id`, `observed_at`, `observation_id`;
- giữ đủ bảy xác suất, không chỉ nhãn cực đại;
- không trộn dữ liệu mô phỏng và camera thật;
- giữ cờ xung đột thời gian, khu vực thiếu và bản ghi đến chậm;
- không âm thầm điền nhãn cho thời điểm/khu vực bị thiếu;
- ghi phiên bản mô hình để tránh nối chuỗi từ các mô hình có phân bố đầu ra khác nhau mà không đánh dấu.

## 11. Lộ trình triển khai đề xuất

### Giai đoạn 1 — Baseline có thể làm ngay

1. Export bảng observation-level.
2. Giữ riêng chuỗi theo `visit_id`.
3. Tính ma trận chuyển nhãn cứng và ma trận chuyển mềm từ `expression_scores`.
4. Tính riêng theo cặp khu vực và báo cáo số mẫu hỗ trợ.
5. Bootstrap theo `visit_id` để tạo khoảng tin cậy.
6. So sánh kết quả khi chọn `first`, `last`, `highest_confidence`, trung bình xác suất và trung vị xác suất trong khu vực.

### Giai đoạn 2 — Làm trơn chuỗi

1. Gán nhãn thủ công cho một tập chuỗi camera nhỏ.
2. Dùng output FER gốc làm baseline.
3. Xây HMM rời rạc trước; chưa cần HSMM.
4. So sánh Macro-F1, edit distance và số chuyển trạng thái giả.
5. Chỉ giữ HMM nếu cải thiện trên chuỗi chưa dùng để ước lượng tham số.

### Giai đoạn 3 — Khai phá kiểu hành trình

1. Chỉ dùng dữ liệu camera thật sau khi có đủ số lần mua sắm.
2. Tạo chuỗi véc-tơ bảy xác suất đã tổng hợp theo khu vực hoặc cửa sổ thời gian.
3. So sánh Soft-DTW + k-medoids với mixture of Markov models.
4. Đánh giá độ ổn định cụm và mô tả cụm, không gọi cụm là “hài lòng/không hài lòng” nếu chưa có nhãn ngoài.

### Giai đoạn 4 — Chuỗi video dày

1. Lưu đoạn video hoặc embedding từng khung theo chính sách quyền riêng tư phù hợp.
2. Dùng DFEW/FERV39k để thiết lập baseline Dynamic FER.
3. Thu và gán nhãn dữ liệu camera tại miền mục tiêu.
4. Chỉ sau đó so sánh HMM/CRF/LSTM/Transformer hoặc một mô hình DFER chuyên dụng.

## 12. Các bài báo nên đọc trước

1. Ira Cohen, Nicu Sebe, Ashutosh Garg, Lawrence S. Chen, Thomas S. Huang (2003), [Facial Expression Recognition from Video Sequences: Temporal and Static Modeling](https://doi.org/10.1016/S1077-3142(03)00081-X).
2. Lawrence R. Rabiner (1989), [A Tutorial on Hidden Markov Models and Selected Applications in Speech Recognition](https://doi.org/10.1109/5.18626).
3. Eva Anderl, Ingo Becker, Florian von Wangenheim, Jan H. Schumann (2016), [Mapping the Customer Journey: Lessons Learned from Graph-Based Online Attribution Modeling](https://doi.org/10.1016/j.ijresmar.2016.03.001).
4. Igor Cadez, David Heckerman, Chris Meek, Padhraic Smyth, Steven White (2003), [Model-Based Clustering and Visualization of Navigation Patterns on a Web Site](https://www.microsoft.com/en-us/research/publication/model-based-clustering-and-visualization-of-navigation-patterns-on-a-web-site/).
5. Marco Cuturi, Mathieu Blondel (2017), [Soft-DTW: a Differentiable Loss Function for Time-Series](https://proceedings.mlr.press/v70/cuturi17a.html).
6. Shun-Zheng Yu (2010), [Hidden Semi-Markov Models](https://doi.org/10.1016/j.artint.2009.11.011).
7. Rebecca Killick, Paul Fearnhead, Idris A. Eckley (2012), [Optimal Detection of Changepoints with a Linear Computational Cost](https://doi.org/10.1080/01621459.2012.737745).
8. Ryan Prescott Adams, David J. C. MacKay (2007), [Bayesian Online Changepoint Detection](https://arxiv.org/abs/0710.3742).
9. Yan Wang, Jiayu Zhang, Jun Ma, Shaojun Wang, Jing Xiao (2020), [Contextualized Emotion Recognition in Conversation as Sequence Tagging](https://aclanthology.org/2020.sigdial-1.23/).
10. Xingxun Jiang et al. (2020), [DFEW: A Large-Scale Database for Recognizing Dynamic Facial Expressions in the Wild](https://doi.org/10.1145/3394171.3413620).
11. Yan Wang et al. (2022), [FERV39k: A Large-Scale Multi-Scene Dataset for Facial Expression Recognition in Videos](https://openaccess.thecvf.com/content/CVPR2022/html/Wang_FERV39k_A_Large-Scale_Multi-Scene_Dataset_for_Facial_Expression_Recognition_in_CVPR_2022_paper.html).
12. Hanyang Wang et al. (2023), [Rethinking the Learning Paradigm for Dynamic Facial Expression Recognition](https://openaccess.thecvf.com/content/CVPR2023/papers/Wang_Rethinking_the_Learning_Paradigm_for_Dynamic_Facial_Expression_Recognition_CVPR_2023_paper.pdf).

## 13. Khuyến nghị cuối cùng cho phạm vi luận văn

Trong phạm vi dữ liệu hiện có, phương án có cơ sở nhất là:

1. giữ bảng dữ liệu chi tiết với đủ bảy xác suất;
2. xây dựng ma trận chuyển trạng thái theo cặp khu vực;
3. báo cáo cả chuyển nhãn cứng và chuyển xác suất mềm;
4. dùng bootstrap theo lần mua sắm để thể hiện độ bất định;
5. thử HMM như một thực nghiệm bổ sung để giảm dao động nhãn;
6. xem Soft-DTW, change-point detection và mô hình học sâu theo chuỗi là hướng phát triển khi có dữ liệu thật dày hơn.

Cách làm này mở rộng trực tiếp từ chức năng “show data” hiện tại mà không đòi hỏi ngay một tập video lớn hoặc nhãn chuỗi hoàn chỉnh, đồng thời vẫn giữ ranh giới diễn giải: chuỗi FER là chuỗi **kết quả quan sát từ mô hình**, không phải phép đo trực tiếp trải nghiệm hay mức độ hài lòng.
