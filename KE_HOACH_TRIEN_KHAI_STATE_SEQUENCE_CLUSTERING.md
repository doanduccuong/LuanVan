# Kế hoạch triển khai State Sequence Clustering và cập nhật Chương 3–5

## Trạng thái thực hiện ngày 08/10/2026

- Đã triển khai mô-đun tạo chuỗi, Optimal Matching bằng Sequenzo, PAM, chọn K, lưu kết quả, API và giao diện.
- Đã chạy lớp B bằng dữ liệu tổng hợp có kiểm soát với 25 khách hàng, 125 lần mua sắm và 500 quan sát; artefact và bốn ảnh giao diện có truy vết đã được khóa.
- Đã chạy lớp C đầu-cuối bằng ảnh thật từ bản KDEF trên Kaggle với 5 nhóm nguồn, 5 hồ sơ, 25 lần mua sắm và 100 khung Camera. Kết quả: 100/100 ảnh hợp lệ, 96/100 khung ghép đúng hồ sơ dự kiến, 4 `NO_MATCH`, 0 ghép nhầm sang hồ sơ khác.
- Đã tạo run phân cụm Camera `a845f266-7dab-4dff-ba42-a61a46930d7a`: nhận 25 chuỗi, dùng 22, loại 3 chuỗi thiếu bốn trạng thái, chọn K=5 và ASW=0,445.
- Đã cập nhật Chương 3, Chương 4 và Chương 5; PDF cuối được biên dịch lại và kiểm tra trực quan sau khi hoàn tất ảnh minh chứng.
- Đã chạy 15 kiểm thử API, 3 kiểm thử vision và build web thành công.
- Docker Compose đã chạy PostgreSQL, Vision, API, Simulator và Web; migration kết thúc mã 0. Các endpoint API, Vision, Simulator và Web đều trả HTTP 200 tại thời điểm chụp bằng chứng.

Chi tiết bằng chứng và các mục còn thiếu nằm tại `SYSTEM/HANDOVER_EVIDENCE.md`.

## 1. Mục tiêu và phạm vi

Mục tiêu của đợt triển khai là thêm một thành phần phân tích chuỗi có thể tái lập vào sau luồng nhận dạng và hình thành lần mua sắm đang có. Thành phần này không thay thế phương pháp nhận diện khuôn mặt, phân loại biểu cảm hoặc các thống kê hiện hữu. Luồng xử lý của thành phần gồm:

1. tạo một chuỗi trạng thái biểu cảm cho mỗi `visit_id`;
2. tính ma trận khoảng cách giữa các chuỗi bằng Optimal Matching;
3. phân cụm chuỗi bằng PAM/K-medoids;
4. chọn số cụm bằng chất lượng phân cụm và các điều kiện diễn giải;
5. lưu, cung cấp qua API và hiển thị kết quả trên CRM.

Đợt triển khai đồng thời thay dữ liệu demo ảnh hiện tại bằng một luồng có cùng chủ thể ở nhiều biểu cảm. KDEF được dùng cho **demo nghiên cứu chạy cục bộ** để tái hiện đầy đủ các bước: đăng ký khách hàng bằng ảnh khuôn mặt, phát lại ảnh camera ở nhiều điểm chạm, nhận dạng lại khách hàng, dự đoán biểu cảm, tổng hợp thành chuỗi và phân cụm. Luồng ảnh này là kiểm thử tích hợp đầu-cuối; nó không thay thế bộ dữ liệu kiểm soát dùng để đánh giá riêng thuật toán phân cụm.

Phạm vi báo cáo cần cập nhật:

- Chương 3: mô tả phương pháp đề xuất và cơ sở lựa chọn;
- Chương 4: mô tả cách phương pháp được hiện thực hóa trong hệ thống;
- Chương 5: mô tả giao thức, số liệu, kết quả và giới hạn thực nghiệm;
- Chương 2 không nằm trong phạm vi chỉnh sửa của kế hoạch này;
- kết quả định lượng chỉ được viết sau khi mã chạy trên dữ liệu cố định và artifact đã được lưu.

Phương pháp chỉ tạo ra **các kiểu diễn biến biểu cảm**. Không đặt tên cụm là “hài lòng” hoặc “không hài lòng” nếu chưa có CSAT hay biến kết quả nghiệp vụ độc lập để kiểm chứng.

## 2. Hiện trạng cần thay đổi

Hệ thống hiện có:

- bảng `observations` lưu `visit_id`, `touchpoint_id`, `observed_at`, nhãn, confidence và véc-tơ bảy điểm số;
- API xem chuỗi của từng lần mua sắm;
- báo cáo phân bố bảy nhãn tại khu vực;
- báo cáo đếm cặp nhãn giữa hai khu vực liên tiếp;
- giao diện biểu đồ phân bố, Sankey thay đổi nhãn và chất lượng dữ liệu.

Phần còn thiếu:

- chưa tạo một chuỗi phân tích nhất quán cho toàn bộ lần mua sắm;
- chưa tính khoảng cách giữa các lần mua sắm;
- chưa tìm các mẫu chuỗi lặp lại trong tập dữ liệu;
- chưa có chỉ số chất lượng cụm, chuỗi đại diện và mức phù hợp của từng lần mua sắm;
- chưa lưu tham số phân tích nên kết quả chưa có khả năng tái lập theo từng lần chạy;
- demo ảnh hiện tại lấy một ảnh FairFace của mỗi bản ghi rồi biến đổi vị trí/độ sáng; FairFace không cung cấp nhiều biểu cảm có định danh ổn định của cùng một người, nên chưa tái hiện được chuỗi biểu cảm bằng ảnh;
- phần lớn khách hàng demo hiện chỉ có một sự kiện ảnh, chỉ năm khách hàng đầu có bốn điểm chạm, nên chưa tạo được số chuỗi ảnh đủ cân bằng cho thực nghiệm phân cụm;
- ngưỡng nhận dạng và manifest hiện gắn với FairFace, vì vậy phải được tạo lại khi chuyển nguồn ảnh sang KDEF.

Báo cáo “thay đổi giữa các khu vực” hiện tại được giữ lại làm phân tích mô tả/baseline. State Sequence Clustering được nối vào sau bước hình thành chuỗi để phân tích toàn bộ lần mua sắm.

## 3. Quy tắc dữ liệu được khóa trước khi viết mã

### 3.1. Đơn vị phân tích

- Một `visit_id` là một đơn vị phân tích.
- Chỉ dùng quan sát có `image_status=VALID`, `expression_status=VALID` và nhãn thuộc bảy lớp hợp lệ.
- Không trộn dữ liệu `CAMERA` và `SIMULATOR` trong cùng một lần phân tích.
- Các bản ghi không có `visit_id` không tham gia phân cụm chuỗi.

### 3.2. Xử lý xung đột và thứ tự

- Sắp xếp theo `observed_at`, sau đó theo `observation_id` để kết quả xác định.
- Nếu cùng thời điểm xuất hiện ở nhiều điểm chạm, đánh dấu xung đột và loại các bản ghi đó khỏi chuỗi phân tích.
- Không nội suy điểm chạm hoặc trạng thái bị thiếu.
- Giữ thông tin các bản ghi bị loại trong thống kê chất lượng của lần chạy.

### 3.3. Tạo trạng thái đại diện theo đoạn điểm chạm

Các quan sát liên tiếp tại cùng một `touchpoint_id` được gom thành một đoạn. Mỗi đoạn tạo đúng một trạng thái biểu cảm đại diện:

1. chọn nhãn xuất hiện nhiều nhất trong đoạn;
2. nếu hòa, chọn nhãn có tổng confidence lớn hơn;
3. nếu vẫn hòa, dùng thứ tự cố định của bảy nhãn để bảo đảm kết quả tái lập.

Chuỗi dùng cho phân cụm gồm các trạng thái đại diện của những đoạn điểm chạm liên tiếp. Dữ liệu gốc không bị ghi đè. Mỗi phần tử chuỗi vẫn giữ metadata gồm điểm chạm, thời gian đầu/cuối đoạn, số quan sát hỗ trợ và confidence trung bình.

Quy tắc này tránh để số khung hình không đều tại một điểm chạm làm một trạng thái bị lặp quá nhiều. Phiên bản đầu phân tích thứ tự trạng thái theo các đoạn điểm chạm, không tuyên bố đo chính xác thời lượng biểu cảm.

### 3.4. Điều kiện đủ dữ liệu

- Một lần mua sắm cần ít nhất ba đoạn hợp lệ để tham gia phân cụm.
- Nếu số lần mua sắm đủ điều kiện quá ít để tạo ít nhất hai cụm hợp lệ, API trả trạng thái “không đủ dữ liệu” thay vì sinh kết quả giả.
- Ngưỡng số đoạn và quy tắc lọc là tham số có phiên bản, đồng thời phải xuất hiện trong kết quả phân tích.

## 4. Đặc tả thuật toán phiên bản đầu

### 4.1. Optimal Matching

Optimal Matching không được tự hiện thực lại trong code nghiệp vụ. Phiên bản đầu dùng `sequenzo.SequenceData` để biểu diễn tập chuỗi và `sequenzo.get_distance_matrix(...)` để tính khoảng cách với cấu hình:

- `method="OM"`;
- `sm="CONSTANT"`, tương ứng chi phí thay thế hai trạng thái khác nhau bằng `2` và cùng trạng thái bằng `0`;
- `indel=1`, tương ứng chi phí chèn hoặc xóa bằng `1`;
- `norm="none"`, tức giữ khoảng cách OM thô;
- `full_matrix=True`, để nhận ma trận khoảng cách vuông dùng cho phân cụm.

Đầu vào của thư viện là bảng chuỗi dạng rộng: mỗi hàng là một `visit_id`, các cột thời gian chứa bảy trạng thái biểu cảm. Chuỗi ngắn hơn được đệm ở cuối bằng ký hiệu void `%`; `%` không phải trạng thái biểu cảm và phải được khai báo đúng theo quy ước của `SequenceData`.

Đầu ra là ma trận số vuông `N × N`: phần tử tại hàng `i`, cột `j` là khoảng cách OM giữa hai visit; đường chéo bằng `0`. Đây là dữ liệu đưa vào PAM, không phải các chuỗi đã bị biến đổi. Phiên bản đầu không thực hiện chuẩn hóa `maxdist`.

Bộ chi phí trên là cấu hình baseline, không được mô tả là lựa chọn duy nhất đúng. Mã phải cho phép truyền cấu hình và phần thực nghiệm phải kiểm tra độ nhạy ít nhất với một cấu hình thay thế. Nếu các chuỗi khác độ dài do thời lượng lần mua sắm khác nhau, khoảng cách OM thô giữ chênh lệch đó như một phần thông tin của diễn biến. Nếu độ dài khác nhau do lỗi lấy mẫu, mất khung hình hoặc tần suất ghi không đồng đều, vấn đề phải được xử lý ở bước tạo chuỗi theo mốc thời gian/điểm chạm, không dùng chuẩn hóa khoảng cách để che sai lệch dữ liệu.

### 4.2. PAM/K-medoids

- Đầu vào là ma trận khoảng cách OM thô $D$.
- Phiên bản Python tiếp tục dùng Sequenzo: `sequenzo.KMedoids(..., method="PAM")` thực hiện PAM trên ma trận khoảng cách đã tính trước. Không thêm thư viện `kmedoids` riêng.
- Kết quả gốc của `KMedoids` là chỉ số medoid gán cho từng quan sát theo quy ước đánh số từ `1` của thư viện. Dùng `medoid_indices_from_kmedoids_result(...)` để lấy các chỉ số medoid dạng `0`-based và `cluster_labels_from_kmedoids_result(...)` để tạo nhãn cụm `0..K-1`, sau đó ánh xạ các chỉ số này về `visit_id` và chuỗi biểu cảm tương ứng.
- Xác định kích thước cụm tối thiểu theo cả ngưỡng tuyệt đối và tỷ lệ mẫu:
  $$
  n_{\min}(N)=\max\left(n_{\mathrm{abs}},\left\lceil\pi_{\min}N\right\rceil\right),
  $$
  trong đó `n_abs` ngăn các cụm quá ít phần tử khi tập nhỏ, còn `pi_min` ngăn số cụm ứng viên tăng không kiểm soát khi số lượt mua sắm lớn. Hai giá trị này phải được khai báo trước và kiểm tra độ nhạy trong thực nghiệm, không được chọn sau khi xem kết quả.
- Thử các giá trị `K` từ 2 đến
  $$
  K_{\max}=\min\left(N-1,\left\lfloor\frac{N}{n_{\min}(N)}\right\rfloor,U\right),
  $$
  trong đó `N` là số chuỗi đủ điều kiện và `U` là số chuỗi trạng thái phân biệt. Thành phần `U` ngăn yêu cầu nhiều medoid hơn số mẫu chuỗi khác nhau, đặc biệt khi dữ liệu kiểm soát lặp lại cùng một số archetype. Sau khi phân cụm, vẫn loại các nghiệm có cụm thực tế nhỏ hơn `n_min(N)`; công thức trên chỉ xác định phạm vi khảo sát chứ không bảo đảm PAM tạo các cụm cân bằng.
- Nếu phương án tốt nhất nằm đúng tại `K_max`, mở rộng phạm vi hoặc xem lại các ngưỡng trước khi kết luận; không dùng một giới hạn cố định như 8 nếu chưa có căn cứ từ thiết kế thực nghiệm.
- Mỗi cụm được đại diện bằng một medoid là chuỗi có thật trong dữ liệu.
- Thuật toán phải xác định với cùng dữ liệu và cùng seed.

#### Medoid trong phân cụm

Medoid là một phần tử có thật trong cụm được chọn làm đại diện vì nó gần toàn bộ các thành viên cùng cụm nhất. Việc tối ưu và chọn medoid do Sequenzo thực hiện; code nghiệp vụ không tự cài lại phép tối ưu này.

Ví dụ, một cụm gồm ba chuỗi:

```text
A: Neutral → Happy → Happy
B: Neutral → Happy → Happy → Happy
C: Sad → Neutral → Happy
```

Nếu thư viện trả A làm medoid, đầu ra đại diện của cụm là chuỗi có thật `Neutral → Happy → Happy`, không phải một chuỗi trung bình được tạo mới. Medoid được dùng để mô tả kiểu diễn biến của cụm, tính khoảng cách của từng lần mua sắm đến đại diện và gán một chuỗi mới vào cụm có medoid gần nhất. Cấu hình seed và thứ tự đầu vào phải được cố định để kết quả có khả năng tái lập.

### 4.3. Chọn số cụm

Không chọn `K` chỉ bằng một chỉ số. Thứ tự ra quyết định:

1. loại phương án có cụm quá nhỏ theo ngưỡng cấu hình;
2. dùng `sequenzo.clustering.k_medoids_range(...)` để chạy PAM và lấy bảng chỉ số chất lượng theo các giá trị `K`; dùng cột `ASW` để so sánh các phương án, đồng thời dùng `observation_silhouette(...)` để lấy silhouette của từng chuỗi ở phương án cuối;
3. nếu chất lượng gần tương đương, ưu tiên số cụm nhỏ hơn;
4. kiểm tra khả năng diễn giải qua medoid và biểu đồ chuỗi;
5. ở pha kiểm chứng, bổ sung đánh giá độ ổn định qua bootstrap.

### 4.4. Đầu ra bắt buộc

Mỗi lần chạy phân tích phải trả:

- tham số lọc và phiên bản tiền xử lý;
- số lần mua sắm được nhận, được sử dụng và bị loại;
- `K` được chọn và ASW toàn cục;
- với mỗi cụm: mã cụm, medoid, số lượng, tỷ lệ, ASW trung bình;
- với mỗi lần mua sắm: `cluster_id`, chuỗi trạng thái đã tiền xử lý, khoảng cách đến medoid và silhouette;
- danh sách cảnh báo chất lượng dữ liệu.

Tên diễn giải như “ổn định trung tính” hoặc “kết thúc bằng Happy” là metadata do người phân tích đặt sau khi xem medoid. Thuật toán không tự tạo nhãn “tích cực”, “tiêu cực” hoặc “hài lòng”.

## 5. Kế hoạch thay đổi code

### Giai đoạn 0 — Triển khai lại demo ảnh bằng KDEF

#### 0.1. Phạm vi sử dụng và ràng buộc dữ liệu

KDEF gốc có 70 chủ thể, bảy biểu cảm, năm góc nhìn và hai phiên chụp; nguồn mô tả: [About KDEF](https://kdef.se/home/aboutKDEF). Dữ liệu thực tế của demo được lấy từ bản phân phối đã xử lý [chenrich/kdef-database trên Kaggle](https://www.kaggle.com/datasets/chenrich/kdef-database), gồm 2.938 ảnh trong bảy thư mục nhãn và 140 mã nhóm nguồn. Bản Kaggle không giữ mã phiên, mã góc hoặc tên tệp chính thức; kế hoạch vì vậy không gọi nó là bộ KDEF gốc đầy đủ 4.900 ảnh.

KDEF chỉ được dùng cho nghiên cứu khoa học phi thương mại và không được phân phối lại nếu chưa có chấp thuận bằng văn bản. Vì vậy:

- ghi rõ Kaggle là nguồn phân phối tệp thực tế và lưu URL nguồn trong manifest;
- người chạy demo tải bộ dữ liệu từ Kaggle và khai báo đường dẫn cục bộ bằng `KDEF_ROOT`;
- ảnh gốc, ảnh đã dựng thành khung camera và ảnh đại diện sinh từ KDEF đều nằm trong thư mục bị Git bỏ qua;
- repository chỉ lưu script, tên tệp nguồn, phép biến đổi, checksum và kết quả số; không lưu hoặc phát hành lại ảnh KDEF;
- ảnh chỉ được phục vụ trong môi trường demo cục bộ có kiểm soát, không đưa lên bản triển khai web công khai;
- nếu cần triển khai demo công khai, phải có chấp thuận của chủ sở hữu KDEF hoặc thay bằng dữ liệu tự thu thập/có giấy phép phù hợp.

Điều khoản phải được kiểm tra lại trước khi phát hành artifact: [Using and publishing KDEF and AKDEF](https://kdef.se/faq/using-and-publishing-kdef-and-akdef).

#### 0.2. Đọc mã nhóm nguồn và nhãn từ cấu trúc Kaggle

Script chuẩn bị dữ liệu đọc bảy thư mục `angry`, `disgust`, `fear`, `happy`, `neutral`, `sad`, `surprise`. Tên tệp có dạng `<group_id>_<image_id>.jpg`; tiền tố số được chuẩn hóa thành mã nhóm nguồn `KGxxx`. Mã này chỉ liên kết các ảnh trong bản Kaggle và không được diễn giải thành mã chủ thể chính thức, phiên A/B hoặc góc chụp.

Khóa nội bộ của demo là `source_group_id`, ví dụ `KG003`. Bảng ánh xạ nhãn:

| Thư mục Kaggle | Nhãn hệ thống |
|---|---|
| `fear` | `Fear` |
| `angry` | `Angry` |
| `disgust` | `Disgust` |
| `happy` | `Happy` |
| `neutral` | `Neutral` |
| `sad` | `Sad` |
| `surprise` | `Surprise` |

Script phải dừng với lỗi rõ ràng nếu cấu trúc tệp không hợp lệ, thiếu một trong bảy biểu cảm hoặc một mã nhóm nguồn bị ánh xạ thành nhiều khách hàng.

#### 0.3. Chọn nhóm nguồn cho demo

Chọn xác định 5 mã nhóm nguồn và lưu danh sách trong `kdef_demo_manifest.json`; cùng seed phải luôn tạo cùng danh sách. Lần chạy đã khóa dùng `KG011`, `KG039`, `KG061`, `KG074` và `KG112`. Mỗi mã nhóm ánh xạ đúng một `customer_code`. Các nhóm còn lại không tham gia demo và không cần tạo thêm tập người lạ, tập gây nhiễu hoặc tập lỗi.

Con số 5 phục vụ việc trình bày rõ luồng đầu-cuối, không phải giới hạn của hệ thống; `customer_count`, `visits_per_customer` và seed là tham số cấu hình. Chỉ kiểm tra các điều kiện cần để chạy luồng như đọc được tệp, phát hiện đúng một khuôn mặt và tạo được embedding; không dùng kết quả FER để lựa chọn nhóm nguồn.

#### 0.4. Ảnh đăng ký và ảnh đại diện khách hàng

Với mỗi mã nhóm, xếp hạng các ảnh `Neutral` bằng bộ dò khuôn mặt chính diện và dùng ảnh có điểm ưu tiên cao nhất làm nguồn đăng ký. Do bản Kaggle không giữ mã góc, manifest ghi `frontal_selected_by_detector` thay vì suy đoán mã góc KDEF.

Từ cùng ảnh nguồn tạo hai đầu ra có vai trò khác nhau:

1. ảnh đại diện CRM kích thước `256×256`, chỉ dùng để hiển thị;
2. khung đăng ký một khuôn mặt kích thước `640×480`, gửi qua `POST /customers/{id}/face-templates` để hệ thống tạo ArcFace embedding.

Manifest phải lưu `customer_code`, `source_group_id`, tên tệp nguồn Kaggle, vai trò `profile/enrollment`, phép resize/crop và checksum. Không dùng ảnh đăng ký chính xác này làm sự kiện camera.

#### 0.5. Sinh hành trình ảnh tại nhiều điểm chạm

Mỗi khách hàng demo có năm lượt mua sắm, mỗi lượt tương ứng một `archetype_id`; như vậy 5 khách hàng tạo 25 lượt và mỗi archetype có 5 lượt. Mỗi lượt có bốn điểm chạm theo đúng thứ tự:

```text
TP-ENTRANCE → TP-DISPLAY → TP-CONSULT → TP-CHECKOUT
```

Mỗi sự kiện dùng ảnh của **một người**. Không ghép người gây nhiễu, không tạo ảnh nhiều người, không thêm người chưa đăng ký và không sinh ca ảnh lỗi trong bộ demo này. Mục tiêu duy nhất là tái hiện đúng luồng một khách hàng đi qua nhiều điểm chạm.

Với nhãn mục tiêu tại một điểm chạm, script chọn ảnh trong đúng thư mục nhãn và cùng `source_group_id`; các ảnh được ưu tiên theo khả năng phát hiện khuôn mặt chính diện. Do mỗi nhóm chỉ có một số ít ảnh cho từng nhãn, script quay vòng danh sách khi mẫu chuỗi cần lặp trạng thái. Manifest phải ghi rõ tệp được dùng lại và mỗi khung camera chỉ được biến đổi bằng danh sách cố định như vị trí, kích thước, độ sáng và nền; không dùng biến đổi làm thay đổi nội dung biểu cảm.

Các lượt của cùng khách phải cách nhau lớn hơn `visit_idle_timeout_seconds` hiện hành; cấu hình mặc định đặt các lượt ở các ngày khác nhau để API tạo năm `visit_id` độc lập. Trong một lượt, bốn sự kiện có thời gian tăng dần và nằm trong cùng cửa sổ phiên. Mỗi đợt replay có một `experiment_run_id` riêng; trường này được lưu ở capture event hoặc một bảng run liên kết, không chỉ tồn tại trong tên tệp, để lớp phân tích lọc đúng đợt ảnh KDEF.

#### 0.6. Phát lại qua đúng luồng camera

Mở rộng `prepare_demo_dataset.py`, `seed_demo_crm.py`, `enroll_demo_faces.py` và `replay_demo_journeys.py` hoặc tách các script tương đương cho KDEF. Toàn bộ ảnh điểm chạm phải được gửi tới `POST /api/v1/observations`, không chèn thẳng nhãn KDEF vào bảng và không dùng `/simulation/observations/batch` cho luồng đầu-cuối này.

Với mỗi ảnh, hệ thống thực hiện đúng chuỗi xử lý thật:

```text
ảnh KDEF → phát hiện mặt → ArcFace → ghép customer
          → DeepFace Emotion → observation → visit → chuỗi → OM → PAM
```

Nhãn KDEF là nhãn nguồn để đối chiếu. Trạng thái đưa vào chuỗi phân cụm đầu-cuối là `expression_label` do vision service thực sự trả về. Không được thay nhãn dự đoán bằng nhãn KDEF khi mô hình dự đoán sai.

#### 0.7. Kiểm tra hậu điều kiện của luồng demo

Demo này không thêm dữ liệu người lạ hoặc dữ liệu gây nhiễu. Ngưỡng vận hành được hiệu chỉnh bằng 35 ảnh dành riêng, không xuất hiện trong 100 khung phát lại. Quy tắc chọn ngưỡng ưu tiên không ghép nhầm giữa các nhóm trong tập hiệu chỉnh, sau đó tối đa hóa tỷ lệ chấp nhận cặp cùng nhóm. Kết quả chỉ dùng cho phạm vi demo và không được trình bày là độ chính xác định danh trên quần thể.

Sau replay, script kiểm tra tối thiểu:

- mỗi ảnh đăng ký tạo đúng một face template;
- mỗi sự kiện hợp lệ phát hiện đúng một khuôn mặt;
- `subject_id` mong đợi được ánh xạ đúng `customer_id` hoặc được báo cáo là lỗi nhận dạng;
- mỗi lượt đủ bốn điểm chạm theo đúng thứ tự hoặc được ghi rõ lý do thiếu;
- các lượt của cùng khách có `visit_id` khác nhau;
- chuỗi cuối cùng dùng nhãn do mô hình trả về và truy ngược được đến tệp ảnh;
- tổng số visit nhận, visit đủ điều kiện và visit bị loại khớp manifest.

Không yêu cầu toàn bộ 25 lượt phải hoàn hảo bằng cách âm thầm thay dữ liệu. Mọi ca lỗi phải xuất hiện trong artifact; nếu cần thay ảnh vì lỗi kỹ thuật, quyết định và lý do phải được ghi vào một manifest phiên bản mới trước khi chạy lại.

#### 0.8. Hai mục đích đánh giá phải tách biệt

- **Demo KDEF đầu-cuối:** chứng minh hệ thống nhận ảnh, nhận dạng cùng người qua nhiều biểu cảm/điểm chạm, tạo visit, tạo chuỗi và phân cụm. Có thể báo cáo tỷ lệ nhận dạng, đối chiếu FER với nhãn KDEF và số chuỗi hợp lệ, nhưng không dùng kết quả này một mình để khẳng định PAM khôi phục đúng năm archetype vì sai số FER/nhận dạng đã tham gia vào đầu vào.
- **Dữ liệu chuỗi kiểm soát:** gửi nhãn trạng thái đã biết qua endpoint simulator để cô lập và đo riêng OM + PAM bằng ARI/NMI. Luồng này không được trình bày như dữ liệu đi qua camera.

Điều kiện hoàn thành Giai đoạn 0 là có manifest lựa chọn KDEF, 5 khách đã đăng ký, artifact replay ảnh, bảng đối chiếu nhãn KDEF–nhãn dự đoán và tập chuỗi đầu-cuối có thể truy vết. Chỉ sau đó mới dùng các chuỗi này làm dữ liệu CRM đầu vào cho phần phân tích.

### Giai đoạn A — Tách logic phân tích thuần

Tạo mô-đun mới trong API, dự kiến `SYSTEM/apps/api/app/sequence_analysis.py`, gồm:

- kiểu dữ liệu cho phần tử chuỗi, chuỗi của một lần mua sắm và kết quả cụm;
- lọc và gom đoạn điểm chạm;
- chuyển các chuỗi sang bảng rộng có padding void `%` và tạo `SequenceData`;
- gọi `get_distance_matrix(...)` để nhận ma trận khoảng cách OM;
- gọi `KMedoids(...)` hoặc `k_medoids_range(...)` để phân cụm và nhận medoid;
- gọi `observation_silhouette(...)` để nhận silhouette của từng chuỗi;
- hàm điều phối chọn `K`.

Logic này không truy cập HTTP hoặc ORM để có thể kiểm thử độc lập.

Phân chia trách nhiệm khi hiện thực:

- code của hệ thống tự thực hiện truy vấn dữ liệu, tạo chuỗi, chuyển đổi long-to-wide, sinh phạm vi `K`, kiểm tra kích thước cụm, ánh xạ chỉ số về `visit_id` và lưu kết quả;
- Sequenzo thực hiện Optimal Matching, tạo ma trận khoảng cách, PAM/K-medoids và tính các chỉ số silhouette;
- `NumPy` chỉ dùng để kiểm tra, lưu và truy xuất ma trận khoảng cách do Sequenzo trả về;
- không chép lại công thức hoặc tự hiện thực Optimal Matching, PAM, medoid và silhouette khi Sequenzo đã cung cấp chức năng tương ứng.

Khóa phiên bản Sequenzo đã kiểm thử trong dependency/lockfile. Mốc triển khai ban đầu dự kiến dùng `sequenzo==0.1.42`; vì dự án hiện vẫn công bố trạng thái Alpha, không tự động nâng phiên bản nếu chưa chạy lại fixture hồi quy.

Điều kiện hoàn thành:

- khoảng cách của hai chuỗi giống nhau bằng 0;
- khoảng cách đối xứng và không âm;
- fixture có chuỗi dài ngắn khác nhau được padding bằng `%` nhưng không coi `%` là trạng thái cảm xúc;
- ma trận OM của Sequenzo khớp các giá trị kỳ vọng đã tính độc lập trên fixture nhỏ;
- kết quả PAM xác định với cùng input/seed;
- trường hợp chuỗi rỗng, một chuỗi hoặc không đủ cụm trả lỗi nghiệp vụ rõ ràng.

### Giai đoạn B — Lớp lấy dữ liệu và persistence

Thêm migration và các bảng dự kiến:

1. `sequence_analysis_runs`: phạm vi dữ liệu, nguồn, tham số, phiên bản thuật toán, trạng thái, `K`, ASW và số mẫu;
2. `sequence_cluster_summaries`: cụm, medoid, quy mô, tỷ lệ, ASW trung bình và tên mô tả tùy chọn;
3. `sequence_cluster_assignments`: liên kết `run_id`–`visit_id`, chuỗi đầu vào, cụm, khoảng cách đến medoid và silhouette.

Để truy vết luồng ảnh KDEF, bổ sung khóa `experiment_run_id` có chỉ mục cho capture event hoặc một quan hệ run tương đương. Endpoint nhận ảnh chỉ nhận giá trị này trong chế độ demo/nghiên cứu có xác thực; dữ liệu camera vận hành bình thường có thể để trống.

Không lưu toàn bộ ma trận khoảng cách vào cơ sở dữ liệu ở phiên bản đầu. Ma trận là kết quả trung gian và có kích thước bậc hai.

Mỗi lần chạy phải lưu đủ tham số để có thể giải thích vì sao hai lần chạy cho kết quả khác nhau.

### Giai đoạn C — API

Thiết kế resource API dự kiến:

- `POST /api/v1/sequence-analyses`: tạo và chạy một phân tích;
- `GET /api/v1/sequence-analyses`: liệt kê các lần chạy;
- `GET /api/v1/sequence-analyses/{run_id}`: kết quả tổng quát và tham số;
- `GET /api/v1/sequence-analyses/{run_id}/clusters`: danh sách cụm và medoid;
- `GET /api/v1/sequence-analyses/{run_id}/assignments`: danh sách lượt mua sắm và cụm;
- `PATCH /api/v1/sequence-analyses/{run_id}/clusters/{cluster_id}`: đặt tên mô tả thủ công nếu cần.

Phiên bản demo có thể chạy đồng bộ khi tập dữ liệu nhỏ. Phải đo thời gian và đặt giới hạn cấu hình; nếu vượt giới hạn thì chuyển sang background job hoặc từ chối có thông báo rõ ràng, không để request treo.

Khi số lượt mua sắm lớn, không tạo ma trận đầy đủ một cách mù quáng. Lộ trình mở rộng gồm:

1. gộp các chuỗi trùng hoàn toàn và mang theo trọng số;
2. tính khoảng cách trên tập chuỗi duy nhất;
3. dùng PAM có trọng số khi quy mô còn phù hợp;
4. chuyển sang CLARA hoặc k-medoids xấp xỉ trên nhiều mẫu khi ma trận cặp không còn phù hợp bộ nhớ;
5. chạy phân tích nền, lưu run và dùng lại kết quả thay vì tính lại theo mỗi lần mở trang.

Ngưỡng chuyển chiến lược không được ấn định bằng suy đoán; nó được chọn sau benchmark theo số chuỗi, độ dài chuỗi, thời gian và bộ nhớ trên môi trường triển khai.

### Giai đoạn D — Giao diện

Bổ sung tab `Kiểu chuỗi biểu cảm` trong trang `Phân tích biểu cảm`:

- bộ lọc khoảng thời gian và nguồn dữ liệu;
- nút tạo lần phân tích;
- thông tin số mẫu, `K`, ASW và cảnh báo;
- thẻ cho từng cụm: medoid, quy mô, tỷ lệ, ASW;
- biểu đồ chuỗi/trạng thái đại diện theo thứ tự điểm chạm;
- bảng các lần mua sắm với `cluster_id`, khoảng cách và silhouette;
- liên kết từ một assignment đến màn hình chi tiết lần mua sắm.

Giao diện phải ghi rõ: “Cụm mô tả kiểu diễn biến biểu cảm; không phải kết luận mức độ hài lòng”.

Các tab phân bố, thay đổi giữa khu vực và chất lượng dữ liệu hiện tại tiếp tục hoạt động.

### Giai đoạn E — Kiểm thử và bằng chứng

Kiểm thử đơn vị:

- tạo đoạn điểm chạm, quy tắc hòa và thứ tự xác định;
- loại xung đột cùng thời điểm;
- OM qua Sequenzo cho các cặp chuỗi có kết quả biết trước;
- PAM, medoid và silhouette trên tập dữ liệu nhỏ có cấu trúc rõ;
- chọn `K` và xử lý cụm quá nhỏ.

Kiểm thử API:

- tách `CAMERA` và `SIMULATOR`;
- không đưa observation thiếu `visit_id` vào phân tích;
- không đủ dữ liệu trả lỗi phù hợp;
- tạo run, đọc cụm và assignment nhất quán;
- hai run cùng tham số/seed tạo cùng kết quả;
- phân quyền và nhật ký thao tác nếu endpoint làm thay đổi dữ liệu.

Kiểm thử giao diện và tích hợp:

- build TypeScript thành công;
- trạng thái loading/error/empty đầy đủ;
- từ tab phân tích mở được chi tiết một visit;
- đối chiếu một run với tập fixture tính tay;
- lưu ảnh chụp giao diện sau khi kết quả đã được xác minh.

Artifact thực nghiệm phải được sinh tự động, dự kiến gồm:

- manifest dữ liệu chuỗi đầu vào;
- tham số và phiên bản của mỗi run;
- ma trận khoảng cách hoặc checksum của ma trận;
- kết quả theo từng giá trị `K`;
- cluster summary và assignment dạng JSON/CSV;
- số liệu baseline, độ nhạy và hiệu năng;
- hình dùng trong Chương 5 được tạo từ đúng artifact của run đã khóa.

## 6. Kế hoạch viết lại Chương 3

Chương 3 mô tả **phương pháp**, không mô tả tên file, endpoint hoặc component giao diện.

Giữ các phần tạo quan sát, nhận dạng khách hàng và hình thành lần mua sắm. Viết lại phần phân tích theo cấu trúc:

1. **Bài toán và đầu ra phân tích**: từ chuỗi rời rạc sang kiểu diễn biến; nêu rõ giới hạn không suy ra hài lòng.
2. **Xây dựng chuỗi trạng thái**: đơn vị `visit_id`, bảy trạng thái, gom đoạn điểm chạm, xử lý thiếu và xung đột.
3. **Khoảng cách Optimal Matching**: giải thích ba phép biến đổi, ý nghĩa cấu hình chi phí và đầu ra là ma trận khoảng cách OM thô. Nêu Sequenzo là công cụ hiện thực; không trình bày mã quy hoạch động như phần đóng góp của hệ thống.
4. **Phân cụm PAM/K-medoids**: mô tả đầu vào là ma trận khoảng cách, đầu ra gồm assignment và medoid; định nghĩa medoid là chuỗi thật đại diện cho cụm; nêu Sequenzo là thư viện hiện thực và lý do medoid phù hợp với dữ liệu chuỗi phân loại không thể lấy trung bình. Không trình bày lại phép tối ưu chi tiết vì phần này được thực hiện bằng thư viện.
5. **Lựa chọn số cụm**: ASW, quy mô cụm, độ ổn định và khả năng diễn giải.
6. **Đầu ra và nguyên tắc đặt tên cụm**: cluster ID, medoid, distance, silhouette.
7. **Liên hệ với dữ liệu nghiệp vụ**: chỉ đánh giá sự liên hệ với CSAT/đơn hàng khi có biến đối chứng; không diễn giải nhân quả.
8. **Phạm vi và giới hạn**: biểu cảm là tín hiệu quan sát, dữ liệu không đều, sai số FER và nhận dạng ảnh hưởng chuỗi.

Phần “Sự thay đổi giữa các khu vực liên tiếp” hiện tại được giữ nhưng xác định là baseline mô tả, sau đó dẫn sang phân tích toàn chuỗi.

Nguồn cần bổ sung và kiểm tra BibTeX trước khi trích dẫn:

- Abbott và Forrest (1986) cho Optimal Matching trong phân tích chuỗi xã hội;
- Abbott và Hrycak (1990) cho việc tìm các kiểu chuỗi điển hình;
- Kaufman và Rousseeuw (1990) cho PAM và silhouette;
- Studer (2013) cho xây dựng và đánh giá typology chuỗi;
- Pacca và cộng sự, DOI `10.1093/aje/kwaf065`, cho quy trình sequence + cluster analysis hiện đại.
- tài liệu chính thức và mã nguồn Sequenzo cho chi tiết hiện thực phần mềm; nguồn này chỉ chứng minh API được sử dụng, không thay thế nguồn lý thuyết của OM, PAM hoặc silhouette.

Không đưa kết quả số, số cụm cuối cùng hoặc tên cụm thực nghiệm vào Chương 3.

### 6.1. Hình và bằng chứng phải cập nhật trong Chương 3

Chương 3 là chương phương pháp nên hình ở đây có chức năng giải thích thiết kế, không được dùng ảnh giao diện để thay cho lập luận phương pháp. Tối thiểu phải có:

1. sơ đồ đầu-cuối `đăng ký → camera tại điểm chạm → observation → visit → chuỗi → OM → PAM → cụm`;
2. sơ đồ tạo một chuỗi bốn điểm chạm từ các observation của cùng `visit_id`;
3. sơ đồ đầu vào/đầu ra của Optimal Matching và PAM, ghi rõ đầu ra OM là ma trận khoảng cách và đầu ra PAM là assignment cùng medoid;
4. bảng ánh xạ bảy mã biểu cảm KDEF sang bảy nhãn hệ thống.

Mỗi thành phần trong sơ đồ phải khớp với module, bảng dữ liệu hoặc endpoint thực sự tồn tại sau triển khai. Không đưa vào Chương 3 một bước chỉ có trong ý tưởng nhưng chưa có trong code. Công thức, tên tham số Sequenzo và quy tắc tạo chuỗi phải được kiểm tra lại với phiên bản thư viện đã khóa trước khi bàn giao.

## 7. Kế hoạch viết lại Chương 4

Chương 4 mô tả **mã đã triển khai và đã kiểm chứng**, không mô tả tính năng dự kiến.

Cập nhật các phần:

1. **Cấu trúc chức năng**: bổ sung phân tích kiểu chuỗi ở nhóm phân tích và báo cáo.
2. **Kiến trúc**: bổ sung mô-đun sequence analysis trong máy chủ nghiệp vụ; không đưa thuật toán sang frontend hoặc vision service.
3. **Mô hình dữ liệu**: trình bày ba bảng run/cluster/assignment và quan hệ với `visits`.
4. **Quy trình backend**: lấy observation, tạo chuỗi, tính khoảng cách, chạy PAM, lưu kết quả.
5. **Hợp đồng API**: mô tả request, response, trạng thái không đủ dữ liệu và tham số tái lập.
6. **Giao diện**: trình bày tab kiểu chuỗi, medoid, chỉ số chất lượng và bảng assignment.
7. **Kiểm soát chất lượng**: tách nguồn dữ liệu, cảnh báo số mẫu, xung đột, dữ liệu bị loại và phiên bản thuật toán.
8. **Giới hạn vận hành**: độ phức tạp ma trận khoảng cách và giới hạn chạy đồng bộ.
9. **Dữ liệu demo cục bộ**: mô tả parser KDEF, danh sách chủ thể được chọn, lựa chọn ảnh đăng ký, dựng sự kiện camera và cơ chế không phân phối lại ảnh; chỉ viết các chi tiết đã được hiện thực và kiểm tra.

Ảnh chụp, tên endpoint và schema chỉ được đưa vào Chương 4 sau khi code tương ứng tồn tại và kiểm thử thành công.

### 7.1. Bộ ảnh minh chứng bắt buộc cho Chương 4

Chương 4 phải dùng ảnh chụp từ hệ thống đang chạy sau lần replay KDEF cuối cùng. Tối thiểu gồm:

1. trạng thái toàn bộ service đang hoạt động và các health check đạt;
2. danh sách khách hàng có ảnh đại diện sinh từ đúng các chủ thể KDEF đã chọn;
3. hồ sơ một khách hàng và trạng thái đã có face template;
4. kết quả gửi ảnh camera tại bốn điểm chạm của cùng một lượt;
5. màn hình chi tiết visit thể hiện đúng thứ tự bốn điểm chạm và nhãn biểu cảm thực tế hệ thống đã dự đoán;
6. màn hình danh sách các lần mua sắm cho thấy cùng khách có các `visit_id` tách biệt;
7. màn hình tạo/xem một lần chạy phân tích chuỗi;
8. màn hình danh sách cụm có số cụm, quy mô và medoid;
9. màn hình assignment liên kết một visit với `cluster_id`, distance và silhouette;
10. màn hình truy ngược từ assignment về chi tiết visit và các observation nguồn;
11. tài liệu API đang chạy có các endpoint sequence analysis mới;
12. kết quả test backend, vision và build frontend thực sự vừa chạy.

Các ảnh “quan sát chưa xác định”, ảnh nhiều người và dữ liệu gây nhiễu của demo FairFace hiện tại không thuộc luồng KDEF mới và phải được bỏ khỏi phần mô tả luồng chính. File `SYSTEM/evidence/chapter4_evidence.html` chỉ là trang tổng hợp; ảnh chụp trang này không được xem là bằng chứng hệ thống đã chạy. Kết quả service và kiểm thử phải được chụp trực tiếp từ terminal, API hoặc giao diện thật.

Script `capture_chapter4.mjs` phải được viết lại để tự tìm đúng `experiment_run_id`, assert dữ liệu KDEF tồn tại rồi mới chụp. Nếu thiếu khách hàng, face template, visit bốn điểm chạm hoặc kết quả phân cụm thì script phải thất bại thay vì tạo ảnh trống.

## 8. Kế hoạch viết lại Chương 5

### 8.1. Vị trí trong chương

Chèn một mục mới **Thực nghiệm phân tích chuỗi biểu cảm** sau thực nghiệm phân loại biểu cảm và trước thực nghiệm vận hành hệ thống. Cấu trúc dự kiến của Chương 5:

1. Thực nghiệm phát hiện khuôn mặt;
2. Thực nghiệm phân loại biểu cảm;
3. Thực nghiệm State Sequence Clustering;
4. Thực nghiệm vận hành hệ thống.

### 8.2. Câu hỏi thực nghiệm

Thực nghiệm mới phải trả lời riêng các câu hỏi:

- **RQ1:** Optimal Matching có phân biệt được các chuỗi có cùng tỷ lệ nhãn nhưng khác thứ tự không?
- **RQ2:** PAM có khôi phục được các kiểu chuỗi đã biết trên dữ liệu kiểm soát không?
- **RQ3:** Số cụm nào phù hợp nhất với dữ liệu của lần chạy CRM theo các tiêu chí đã khóa?
- **RQ4:** Kết quả có ổn định khi thay đổi seed mẫu/bootstrap và cấu hình chi phí hay không?
- **RQ5:** Chi phí tính toán có phù hợp với quy mô dữ liệu demo không?
- **RQ6:** Khi ảnh KDEF đi qua toàn bộ vision pipeline, hệ thống giữ lại được bao nhiêu lượt mua sắm và chuỗi dự đoán khác chuỗi KDEF dự kiến như thế nào?

Không đặt câu hỏi “khách hàng có hài lòng không” vì dữ liệu hiện tại chưa có nhãn hài lòng.

### 8.3. Ba lớp dữ liệu thực nghiệm

#### Lớp A — Fixture tính tay

Tạo một fixture rất nhỏ gồm 5–10 chuỗi để kiểm thử từng bước bằng tay. Fixture phải có khoảng cách OM, medoid, assignment và silhouette kỳ vọng đã được xác nhận trước. Lớp này dùng cho unit test và giải thích phương pháp, không dùng để báo cáo chất lượng trên dữ liệu lớn.

#### Lớp B — Bộ chuỗi kiểm soát có nhãn mẫu

Tạo bằng script với seed cố định và năm archetype định trước. Cấu hình kiểm soát dùng 125 lượt mua sắm, tương ứng 25 lượt cho mỗi archetype, để có đủ mẫu kiểm tra việc khôi phục cấu trúc cụm. Quy mô này lớn hơn lớp ảnh KDEF và chỉ là cấu hình thực nghiệm có thể tái lập, không phải giới hạn của phương pháp hoặc hệ thống.

Năm archetype dùng các nhãn thuộc đúng bảy lớp của hệ thống và mô tả các dạng chuỗi khác nhau, chẳng hạn:

1. trạng thái tương đối ổn định;
2. chuyển dần về `Happy`;
3. chuyển dần về `Sad` hoặc `Angry`;
4. duy trì `Happy` ở nhiều điểm chạm;
5. dao động qua nhiều trạng thái.

Tên kỹ thuật trong manifest là `archetype_01` đến `archetype_05`. Các mô tả trên chỉ giải thích cấu trúc dữ liệu mô phỏng, không phải nhãn hành vi hoặc mức hài lòng của khách hàng.

Mỗi lượt gồm đúng bốn đoạn tương ứng bốn điểm chạm. Không bỏ điểm chạm, không thay nhãn ngẫu nhiên và không sinh dữ liệu gây nhiễu trong bản demo đầu. Bộ dữ liệu vẫn phải có ít nhất một cặp archetype dùng cùng tỷ lệ nhãn nhưng khác thứ tự để kiểm tra trực tiếp phần thông tin mà baseline tỷ lệ trạng thái làm mất.

Nhãn `archetype_id` chỉ được lưu trong manifest thực nghiệm và chỉ dùng để tính ARI/NMI sau phân cụm. Thuật toán không được đọc trường này khi tính Optimal Matching hoặc chạy PAM.

Hiện thực lớp B bằng chế độ `sequence_experiment` của simulator, nhưng giữ nguyên chế độ demo hiện có:

- nhận `seed` và số lượt trên mỗi archetype;
- tạo observation qua đúng endpoint `/simulation/observations/batch` để hệ thống sinh `visit_id` như luồng hiện tại;
- gắn một `simulation_run_id` riêng cho toàn bộ lần chạy;
- xuất manifest gồm `simulation_run_id`, `visit_id`, `archetype_id`, chuỗi dự kiến và kết quả mua hàng mô phỏng;
- không ghi `archetype_id` vào trường đầu vào của thuật toán phân cụm;
- không trộn observation `SIMULATOR` với observation `CAMERA` hoặc với một run mô phỏng khác.

Để minh họa bước nối cụm với kết quả nghiệp vụ, chế độ thực nghiệm có thể tạo kết quả mua hàng theo tỷ lệ khác nhau đã khai báo trước cho từng archetype. Các tỷ lệ này là giả định của bộ sinh dữ liệu, phải xuất hiện trong manifest và không được trình bày như kết quả hành vi khách hàng thật. Ngoài ra cần một kịch bản đối chứng trong đó mua hàng độc lập với archetype; ở kịch bản này, phương pháp không được kỳ vọng tạo ra chênh lệch tỷ lệ mua có ý nghĩa.

#### Lớp C — Dữ liệu ảnh KDEF chạy đầu-cuối

Lớp C dùng 5 hồ sơ KDEF đã chọn và quy trình tại Giai đoạn 0. Mỗi hồ sơ có năm lượt, mỗi lượt có bốn ảnh ở bốn điểm chạm, tổng cộng 25 lượt và 100 khung. Ảnh được gửi qua endpoint camera thực, vì vậy chuỗi cuối cùng chịu ảnh hưởng đồng thời của phát hiện khuôn mặt, nhận dạng khách hàng, mô hình FER và quy tắc tạo visit.

Lớp C trả lời các câu hỏi tích hợp:

- ảnh biểu cảm khác với ảnh đăng ký có còn được ghép đúng vào cùng khách hàng không;
- bốn ảnh điểm chạm có được nối thành đúng một chuỗi theo thứ tự thời gian không;
- sau năm khoảng thời gian tách biệt, cùng khách có tạo thành năm visit khác nhau không;
- có bao nhiêu chuỗi đủ điều kiện để đưa vào OM/PAM;
- các cụm trên nhãn dự đoán khác các archetype dự kiến bao nhiêu sau khi đi qua toàn bộ vision pipeline.

Nhãn KDEF và `archetype_id` chỉ dùng làm dữ liệu đối chiếu sau chạy. Đầu vào của OM/PAM ở lớp C là nhãn do hệ thống dự đoán và đã lưu trong `observations`. ARI/NMI ở lớp C, nếu được báo cáo, phải gọi là kết quả **đầu-cuối**, không được diễn giải là chất lượng riêng của thuật toán clustering.

#### Tiền xử lý trước phân cụm

Với mỗi run được khóa:

1. với lớp B, lọc đúng `source_type=SIMULATOR` và `simulation_run_id`; với lớp C, lọc `source_type=CAMERA`, `demo_data=true` và đúng `experiment_run_id`; tuyệt đối không trộn hai nguồn;
2. chỉ giữ observation có `image_status=VALID`, `expression_status=VALID`, `visit_id` và nhãn thuộc bảy lớp;
3. loại các observation không xác định khách hàng và các capture lỗi khỏi tập phân cụm, đồng thời báo cáo riêng số lượng bị loại;
4. sắp xếp theo `observed_at`, sau đó theo ID để phá hòa;
5. gom các observation liên tiếp cùng điểm chạm thành một trạng thái đại diện theo quy tắc tại Mục 3.3;
6. loại visit còn dưới ba trạng thái hợp lệ;
7. tạo manifest chuỗi đầu vào cuối cùng và checksum trước khi tính ma trận OM.

Lớp B đưa nhãn trạng thái đã kiểm soát trực tiếp vào CRM để đo riêng phân tích chuỗi. Lớp C đưa ảnh KDEF qua vision service để kiểm tra tích hợp. Hai lớp phải có run ID, bảng kết quả và cách diễn giải riêng; không lấy kết quả tốt của lớp B để che lỗi của lớp C và không quy lỗi FER ở lớp C cho OM/PAM.

#### Artifact bắt buộc cho dữ liệu demo

Mỗi run phải lưu:

- cấu hình sinh dữ liệu và seed;
- manifest ground truth của simulator đối với lớp B;
- manifest chủ thể KDEF, manifest ảnh, tên tệp nguồn, checksum, phép biến đổi và nhãn KDEF đối với lớp C;
- bảng đối chiếu `subject_id`–`customer_id`–`visit_id`–`event_id` cho lớp C;
- kết quả nhận dạng và nhãn FER thực tế cho từng sự kiện ảnh;
- danh sách observation/visit bị loại và lý do;
- chuỗi cuối cùng thực sự đưa vào OM;
- checksum ma trận khoảng cách;
- assignment, medoid và silhouette do thư viện trả về;
- bảng đối chiếu `archetype_id`–`cluster_id`;
- bảng tỷ lệ mua hàng theo archetype và theo cụm;

### 8.4. Baseline so sánh

Baseline biểu diễn mỗi lần mua sắm bằng véc-tơ tỷ lệ bảy trạng thái:

$$
r_v=(r_{v,1},\ldots,r_{v,7}),\qquad
r_{v,k}=\frac{N_{v,k}}{\sum_j N_{v,j}}.
$$

Sau đó tính khoảng cách Euclid và chạy cùng thuật toán PAM. Baseline này giữ thành phần nhãn nhưng mất thứ tự, nên phù hợp để chứng minh đóng góp của biểu diễn chuỗi.

So sánh:

- `Tỷ lệ trạng thái + Euclidean + PAM`;
- `Optimal Matching + PAM`.

Không so sánh trực tiếp với HMM, Soft-DTW hoặc mô hình học sâu trong đợt này vì khác mục tiêu, dữ liệu đầu vào và điều kiện huấn luyện.

### 8.5. Các số liệu phải báo cáo

#### Mô tả dữ liệu và tiền xử lý

- tổng số visit và observation ban đầu;
- số visit/observation theo nguồn;
- số bản ghi bị loại theo từng nguyên nhân;
- số visit đủ điều kiện;
- min, median, mean, max độ dài chuỗi;
- phân bố bảy trạng thái sau gom đoạn;
- số chuỗi duy nhất và số chuỗi trùng hoàn toàn.

#### Chất lượng khôi phục trên dữ liệu kiểm soát

- Adjusted Rand Index (ARI);
- Normalized Mutual Information (NMI);
- ASW;
- confusion/cross-tab giữa kiểu gốc và cụm, sau khi ánh xạ chỉ để trình bày;
- tỷ lệ cặp chuỗi cùng phân bố nhưng khác thứ tự được tách đúng.

Ở lớp B, ARI/NMI đo riêng khả năng khôi phục các archetype của OM/PAM. Ở lớp C, nếu tính ARI/NMI với archetype dự kiến, kết quả phải được gọi là chất lượng đầu-cuối vì đã bao gồm lỗi nhận dạng và FER. Không tính các chỉ số này cho dữ liệu khách hàng thật nếu không có nhãn chuẩn.

#### Chất lượng luồng ảnh KDEF đầu-cuối

- số chủ thể đăng ký thành công/tổng số chủ thể dự kiến;
- số sự kiện phát hiện đúng một khuôn mặt;
- tỷ lệ sự kiện ghép đúng `subject_id` với `customer_id`;
- confusion matrix và macro-F1 giữa nhãn KDEF với nhãn FER dự đoán, trình bày như phép kiểm tra trên KDEF chứ không phải kết quả FER2013;
- số visit có đủ bốn điểm chạm và số visit còn tối thiểu ba trạng thái;
- tỷ lệ chuỗi dự đoán trùng hoàn toàn với chuỗi KDEF dự kiến;
- khoảng cách OM giữa từng chuỗi dự kiến và chuỗi dự đoán để mô tả mức biến đổi do vision pipeline;
- ASW và phân bố cụm của chính tập chuỗi dự đoán;
- ARI/NMI đầu-cuối giữa archetype dự kiến và cụm dự đoán, kèm cảnh báo không đại diện cho chất lượng riêng của clustering.

#### Lựa chọn số cụm

- bảng `K`, ASW, kích thước cụm nhỏ nhất/lớn nhất và số cụm vi phạm ngưỡng kích thước;
- đồ thị ASW theo `K`;
- lý do chọn `K` cuối cùng;
- kết quả độ ổn định bootstrap cho phương án được chọn.

#### Mô tả cụm cuối

- số lượng và tỷ lệ từng cụm;
- medoid của từng cụm;
- ASW trung bình từng cụm;
- median khoảng cách đến medoid;
- phân bố độ dài chuỗi trong cụm;
- các chuỗi có silhouette thấp hoặc âm để minh họa trường hợp không phù hợp.

#### Độ nhạy

- ít nhất hai cấu hình chi phí OM;
- các ngưỡng số đoạn tối thiểu hợp lý;
- ARI giữa các nghiệm cụm của các cấu hình để đo mức thay đổi, không dùng ARI này như độ chính xác.

#### Hiệu năng

- thời gian tiền xử lý;
- thời gian tạo ma trận khoảng cách;
- thời gian thử các giá trị `K`;
- tổng thời gian;
- bộ nhớ cực đại nếu đo được;
- số chuỗi và độ dài chuỗi của từng phép đo.

### 8.6. Bảng và hình bắt buộc

Tối thiểu gồm:

1. bảng mô tả dữ liệu trước/sau tiền xử lý;
2. bảng so sánh baseline với Optimal Matching;
3. đồ thị ASW theo số cụm;
4. bảng tóm tắt cụm cuối cùng;
5. hình medoid/chuỗi đại diện của từng cụm;
6. heatmap ma trận khoảng cách sắp theo cụm;
7. bảng độ nhạy tham số;
8. bảng thời gian chạy;
9. ảnh đăng ký của một khách và bốn khung camera KDEF tương ứng bốn điểm chạm, nếu việc đưa ảnh vào luận văn đáp ứng điều khoản KDEF;
10. ảnh chi tiết visit chứng minh bốn observation được nối thành một chuỗi;
11. ảnh giao diện tab phân cụm đã hiển thị đúng `analysis_run_id` của thực nghiệm;
12. ảnh medoid và danh sách thành viên của ít nhất một cụm;
13. ảnh truy vết một assignment từ cụm về visit và observation;
14. ảnh terminal của lần kiểm thử cuối và trạng thái các service.

Không tạo hình hoặc điền số thủ công. Script thực nghiệm phải sinh CSV/JSON và hình từ cùng một run. Ảnh giao diện phải được chụp sau khi hệ thống đã nạp đúng run; không dùng mock, dữ liệu hard-code, ảnh cũ từ FairFace hoặc trang HTML tĩnh để thay thế. Mỗi hình phải có tên tệp ổn định, chú thích nêu `experiment_run_id`/`analysis_run_id` liên quan và truy ngược được đến artifact.

Script `capture_chapter5.mjs` phải được cập nhật để kiểm tra các điều kiện dữ liệu trước khi chụp. Nếu không tìm thấy run KDEF, chuỗi bốn điểm chạm, medoid hoặc assignment, script phải trả mã lỗi và không ghi đè bộ ảnh đã được xác minh trước đó.

### 8.7. Cách diễn giải kết quả

- Kết quả lớp A kiểm tra phép tính và ánh xạ đầu ra của thư viện trên fixture nhỏ có giá trị kỳ vọng.
- Kết quả lớp B đánh giá khả năng khôi phục các archetype do kịch bản kiểm soát tạo ra; không chứng minh hành vi khách hàng thật.
- Kết quả lớp C chứng minh hệ thống có thể lấy dữ liệu CRM, tạo chuỗi, phân cụm và hiển thị kết quả có truy vết.
- Các cụm trên dữ liệu mô phỏng chỉ là mẫu của simulator.
- Chỉ dữ liệu cửa hàng thật mới có thể hỗ trợ phát biểu về các kiểu diễn biến thực tế.
- Chỉ khi có CSAT hoặc biến kết quả độc lập mới được đánh giá liên hệ giữa cụm và sự hài lòng.

### 8.8. Điều kiện để viết số liệu vào Chương 5

- run có ID, seed, manifest và checksum;
- danh sách chủ thể KDEF được khóa theo seed và không có ảnh KDEF trong Git/artifact phát hành;
- số liệu lớp B và lớp C nằm trong bảng/artifact riêng, ghi rõ lớp nào dùng nhãn kiểm soát và lớp nào dùng nhãn FER dự đoán;
- tất cả kiểm thử liên quan đều đạt;
- bảng/hình truy ngược được đến artifact;
- số liệu được kiểm tra bằng ít nhất một fixture tính tay;
- không dùng các con số tạm thời từ giao diện hoặc log chưa khóa;
- phần giới hạn nêu rõ nguồn mô phỏng và phạm vi kết luận;
- mọi phát biểu “hệ thống đã thực hiện”, “hệ thống hiển thị” hoặc “kết quả đạt” phải có ít nhất một artifact số và một hình minh chứng tương ứng; nếu chưa có thì phải viết là “dự kiến” hoặc loại khỏi báo cáo.

## 9. Thứ tự thực hiện

1. Chốt đặc tả trong tài liệu này.
2. Chuẩn bị KDEF cục bộ, kiểm tra điều khoản, viết parser tên tệp và khóa danh sách 5 mã nhóm nguồn dùng cho demo.
3. Sửa script tạo CRM/profile/enrollment/camera manifest và xác nhận cấu hình nhận dạng hiện hành xử lý được các ảnh KDEF đã chọn.
4. Đăng ký 5 khách hàng, replay ảnh ở bốn điểm chạm và kiểm tra hậu điều kiện của 25 visit dự kiến; khóa artifact lớp C.
5. Tạo fixture chuỗi nhỏ và test kỳ vọng trước khi viết thuật toán.
6. Viết mô-đun phân tích thuần và test đơn vị.
7. Thêm migration, model và API.
8. Thêm giao diện và kiểm thử tích hợp.
9. Xây dựng bộ chuỗi kiểm soát lớp B, baseline và script sinh artifact thực nghiệm.
10. Chạy riêng lớp B và lớp C; kiểm tra bằng tay medoid, assignment và truy vết về observation/ảnh nguồn.
11. Khóa phiên bản thuật toán, tham số baseline và hợp đồng đầu ra.
12. Viết lại Chương 3 theo phương pháp đã khóa.
13. Viết lại Chương 4 theo code thực tế, bao gồm luồng demo KDEF đã triển khai.
14. Viết mục thực nghiệm mới trong Chương 5 từ artifact lớp A, B và C đã khóa.
15. Chạy sạch toàn bộ Docker Compose, thực hiện lại luồng KDEF và phân tích chuỗi từ đầu đến cuối.
16. Chụp bộ ảnh nghiệm thu Chương 4–5 bằng script có assertion và tạo `HANDOVER_EVIDENCE.md`.
17. Biên dịch LaTeX, sửa lỗi tham chiếu và kiểm tra chéo code–báo cáo–artifact–ảnh minh chứng.

## 10. Tiêu chí hoàn thành chung

- Kết quả không thay đổi khi chạy lại cùng dữ liệu, tham số và seed.
- Mọi assignment truy ngược được đến `visit_id` và các observation tạo chuỗi.
- Không trộn dữ liệu mô phỏng với dữ liệu camera thật.
- Ảnh đăng ký dùng ảnh Neutral được bộ dò ưu tiên theo hướng chính diện; manifest không bịa mã phiên hoặc mã góc đã bị bản Kaggle loại bỏ.
- Mỗi sự kiện KDEF truy ngược được đến `subject_id`, nhãn nguồn, khách hàng, điểm chạm và nhãn FER dự đoán.
- Không commit hoặc phát hành lại ảnh KDEF; demo công khai bị chặn nếu chưa có quyền phù hợp.
- Có test cho tiền xử lý, khoảng cách, phân cụm, API và trạng thái lỗi.
- UI hiển thị medoid, quy mô cụm, ASW, distance và silhouette.
- Báo cáo không gọi cụm là mức hài lòng khi chưa có biến đối chứng.
- Chương 3 khớp với đặc tả toán học; Chương 4 khớp với code thực tế; Chương 5 khớp với artifact thực nghiệm.
- Tài liệu tham khảo có DOI/URL đã kiểm tra và LaTeX biên dịch thành công.

## 11. Ngoài phạm vi của đợt này

- HMM/HSMM, Soft-DTW, LSTM, Transformer hoặc Dynamic FER trên video;
- suy luận nguyên nhân thay đổi biểu cảm;
- tự động tạo điểm cảm xúc hoặc điểm hài lòng;
- huấn luyện mô hình dự đoán CSAT khi chưa có nhãn CSAT;
- sửa Chương 2;
- viết kết quả Chương 5 trước khi hệ thống tạo được bằng chứng.

## 12. Tiêu chí bàn giao để nghiệm thu

### 12.1. Phải chạy lại toàn bộ hệ thống

Trước khi bàn giao, không chỉ chạy test từng module. Phải thực hiện một lần chạy sạch của toàn bộ stack gồm `postgres`, migration, `vision`, `api`, `simulator` và `web`, sau đó hoàn thành luồng KDEF từ đầu đến cuối.

Quy trình nghiệm thu tối thiểu:

1. build và khởi động toàn bộ Docker Compose;
2. xác nhận tất cả container cần thiết ở trạng thái chạy/healthy và migration hoàn tất;
3. chạy toàn bộ test API, test vision và build frontend;
4. reset riêng dữ liệu demo theo cơ chế có xác nhận;
5. chuẩn bị dữ liệu KDEF từ `KDEF_ROOT` và tạo manifest;
6. seed khách hàng/điểm chạm cần thiết;
7. đăng ký face template bằng ảnh Neutral được bộ dò ưu tiên theo hướng chính diện;
8. replay ảnh một người tại bốn điểm chạm qua `/api/v1/observations`;
9. kiểm tra hệ thống tạo đúng customer, visit và chuỗi observation;
10. chạy phân tích `chuỗi → OM → PAM → silhouette`;
11. mở giao diện và kiểm tra cluster, medoid, assignment và truy vết về visit;
12. sinh artifact, bảng, biểu đồ và ảnh chụp báo cáo từ đúng run vừa chạy;
13. biên dịch lại luận văn và kiểm tra Chương 3, 4, 5 cùng danh mục hình/bảng.

Các lệnh nghiệm thu cuối cùng phải được gom thành target/script có thể chạy lại và ghi trong README bàn giao. Nếu một bước cần thao tác thủ công do điều khoản tải KDEF, README phải chỉ rõ tệp/thư mục người kiểm tra cần cung cấp; các bước còn lại phải tự động và dừng ngay khi hậu điều kiện không đạt.

### 12.2. Bộ bằng chứng bắt buộc

Tạo `SYSTEM/artifacts/handover/<run-id>/` cho lần bàn giao, tối thiểu chứa:

- thông tin commit, thời gian chạy, seed và phiên bản dependency;
- kết quả `docker compose ps` và health check;
- log tóm tắt test API, test vision và build frontend;
- `kdef_demo_manifest.json` không chứa dữ liệu ảnh;
- kết quả enrollment và replay theo từng sự kiện;
- bảng ánh xạ `subject_id → customer_id → visit_id → event_id`;
- chuỗi thực tế đưa vào OM;
- cấu hình OM/PAM, bảng lựa chọn `K`, ASW, medoid và assignment;
- CSV/JSON nguồn của mọi bảng và hình trong Chương 5;
- checksum của artifact và ảnh chụp;
- bản PDF luận văn đã biên dịch thành công.

Ảnh KDEF gốc và ảnh dẫn xuất không được sao chép vào artifact bàn giao nếu điều khoản không cho phép; artifact chỉ lưu tham chiếu tên tệp và checksum. Ảnh chụp giao diện dùng trong luận văn phải tuân thủ điều khoản KDEF và ghi nguồn/chủ thể theo yêu cầu áp dụng.

### 12.3. Danh sách ảnh nghiệm thu

Bộ ảnh nghiệm thu phải được chụp tự động sau khi run hoàn tất, ít nhất gồm:

| Mã ảnh | Nội dung phải nhìn thấy |
|---|---|
| `E01` | Toàn bộ service chạy và health check đạt |
| `E02` | Kết quả test API, vision và build web đạt |
| `E03` | Danh sách 5 khách hàng KDEF trên CRM |
| `E04` | Hồ sơ một khách và trạng thái face template đã đăng ký |
| `E05` | Bốn sự kiện ảnh ở bốn điểm chạm của cùng một visit |
| `E06` | Chi tiết visit với thứ tự điểm chạm và bốn nhãn dự đoán |
| `E07` | Màn hình tạo hoặc chọn đúng `analysis_run_id` |
| `E08` | Tổng quan kết quả có số mẫu, `K`, ASW và cảnh báo |
| `E09` | Danh sách cụm và medoid của từng cụm |
| `E10` | Bảng assignment có visit, cluster, distance và silhouette |
| `E11` | Truy vết một assignment về đúng visit/observation |
| `E12` | Các đồ thị/bảng thực nghiệm Chương 5 sinh từ run đã khóa |
| `E13` | Luận văn biên dịch thành công, Chương 3–5 và danh mục hình hiển thị đúng |

Ảnh chụp phải có độ phân giải đọc được, không cắt mất tiêu đề/chỉ số cần chứng minh và không dùng cùng một ảnh để khẳng định nội dung không xuất hiện trong ảnh. Với kết quả chạy terminal, ảnh phải thấy lệnh và dòng kết quả cuối. Với kết quả UI, script phải kiểm tra nội dung bằng selector trước khi chụp.

### 12.4. Ma trận phát biểu–bằng chứng

Tạo file `HANDOVER_EVIDENCE.md` ánh xạ từng phát biểu quan trọng trong Chương 3–5 tới:

```text
phát biểu trong báo cáo
→ file/mục code hiện thực
→ test hoặc artifact số
→ ảnh minh chứng
→ vị trí bảng/hình trong luận văn
```

Quy tắc nghiệm thu là: **không có code chạy, artifact và hình tương ứng thì không được viết như một kết quả đã hoàn thành**. Không chấp nhận ảnh mock, số liệu nhập tay, ảnh từ run cũ, ảnh của trang HTML tĩnh tự tổng hợp hoặc mô tả bằng lời thay cho bằng chứng trực tiếp.

### 12.5. Điều kiện hoàn thành việc viết lại Chương 3–5

- **Chương 3:** phương pháp, đầu vào/đầu ra, OM, PAM, medoid, chọn `K` và sơ đồ luồng khớp với code đã khóa; không chứa kết quả giả định.
- **Chương 4:** kiến trúc, schema, API, script demo và giao diện khớp với hệ thống đang chạy; mọi màn hình được mô tả đều có ảnh chụp trực tiếp.
- **Chương 5:** mọi con số lấy từ artifact của run bàn giao; mọi bảng/hình được sinh lại; ảnh chứng minh đủ luồng đăng ký, camera, visit, chuỗi và phân cụm.
- PDF cuối không lỗi biên dịch, không mất hình, không sai tham chiếu và không còn hình FairFace cũ được dùng để minh họa cho luồng KDEF mới.
