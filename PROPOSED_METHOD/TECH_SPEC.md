# Đặc tả kỹ thuật cũ – Không dùng để triển khai hệ thống CRM

> **Trạng thái: đã thay thế.** Tài liệu này mô tả thử nghiệm dùng mã hành trình được cấp từ bên ngoài và không nhận dạng khách hàng. Phương án hiện tại đã thay đổi. Kế hoạch coding nằm tại `SYSTEM_DEVELOPMENT/IMPLEMENTATION_PLAN.md`; đặc tả dùng để triển khai nằm tại `SYSTEM_DEVELOPMENT/TECH_SPEC.md`.

# Đặc tả kỹ thuật – Phương pháp đề xuất cho Chương 3

## 1. Trạng thái tài liệu

- **Phiên bản:** 0.1
- **Trạng thái:** Bản dự thảo để rà soát trước khi viết mã
- **Phạm vi:** Tạo quan sát biểu cảm tại điểm chạm, hình thành hành trình bằng mã phiên ẩn danh và sinh thống kê đa điểm chạm
- **Không thuộc phạm vi:** Nhận dạng danh tính, theo dõi người giữa nhiều camera, suy luận mức độ hài lòng và tạo điểm cảm xúc chung

Mã phương pháp chỉ được viết sau khi đặc tả này được duyệt. Chương 3 chỉ được viết sau khi mã đã chạy, có đầu ra kiểm chứng và các quyết định còn mở đã được khóa.

---

## 2. Mục tiêu

Xây dựng một quy trình có thể tái lập để:

1. Nhận một ảnh tại một điểm chạm.
2. Phát hiện một khuôn mặt hợp lệ.
3. Phân loại khuôn mặt vào một trong bảy lớp biểu cảm.
4. Tạo một sự kiện quan sát có thể truy vết.
5. Ghép các sự kiện có cùng mã phiên ẩn danh thành một hành trình có thứ tự.
6. Sinh phân bố biểu cảm, thống kê dữ liệu thiếu và ma trận chuyển tiếp giữa các điểm chạm liên tiếp.

Phương pháp chỉ mô tả biểu cảm quan sát được từ ảnh. Đầu ra không được gọi là cảm xúc thật, mức độ hài lòng hoặc đánh giá trải nghiệm tổng thể.

---

## 3. Phụ thuộc phải hoàn thành trước

| Phụ thuộc | Nguồn | Điều kiện sử dụng |
|---|---|---|
| Bộ phát hiện khuôn mặt | `COMPARE_FACE_DETECTION` | Có bảng kết quả đã kiểm tra và cấu hình mô hình được khóa |
| Bộ phân loại biểu cảm | Tài liệu và mã nguồn chính thức của mô hình | Có tên kiến trúc, nguồn trọng số, thứ tự bảy lớp và tiền xử lý được khóa |
| Danh sách điểm chạm | Cấu hình nghiệp vụ | Có mã, tên và thứ tự hợp lệ |
| Mã hành trình | Nguồn dữ liệu bên ngoài | Là mã phiên ẩn danh, không suy ra từ nhận dạng khuôn mặt |
| Dữ liệu kiểm thử | Bộ dữ liệu có nhãn hoặc tình huống kiểm soát | Có quyền sử dụng và nhãn mong đợi |

Không viết cứng tên mô hình hoặc tham số vào luồng xử lý. Mã phải nạp bộ phát hiện, bộ phân loại và cấu hình tương ứng từ tệp cấu hình. Giai đoạn hiện tại không thực hiện benchmark so sánh nhiều mô hình phân loại biểu cảm; bộ phân loại được kiểm tra ở mức tích hợp và tính hợp lệ của đầu ra.

---

## 4. Đơn vị xử lý

### 4.1. Một ảnh tạo tối đa một quan sát

Mỗi yêu cầu đầu vào chứa đúng một ảnh và thông tin ngữ cảnh. Mỗi ảnh được xử lý độc lập.

Nếu nguồn ban đầu là video, thành phần thu nhận ở bên ngoài quy trình phải chọn khung hình theo một tần suất cố định và gửi từng ảnh độc lập. Tần suất lấy ảnh không làm thay đổi nhãn của các ảnh đã xử lý.

### 4.2. Chính sách nhiều khuôn mặt

Phiên bản đầu chỉ chấp nhận ảnh có đúng một khuôn mặt được bộ phát hiện xác nhận là hợp lệ theo cấu hình đã khóa.

- Không có khuôn mặt: trả trạng thái `NO_FACE`.
- Có đúng một khuôn mặt: tiếp tục phân loại.
- Có nhiều hơn một khuôn mặt: trả trạng thái `MULTIPLE_FACES` và không tạo quan sát hành trình.

Quy tắc này tránh gắn nhãn biểu cảm của nhầm người vào một mã hành trình. Phân tích đám đông hoặc nhiều người trong cùng ảnh là phạm vi khác.

---

## 5. Hợp đồng đầu vào

### 5.1. Cấu trúc yêu cầu

```json
{
  "event_id": "evt-000001",
  "journey_id": "journey-anonymous-001",
  "touchpoint_id": "tp-entry",
  "observed_at": "2026-09-22T10:00:00+07:00",
  "image_path": "fixtures/journey-001/entry.jpg"
}
```

### 5.2. Trường bắt buộc

| Trường | Quy tắc |
|---|---|
| `event_id` | Chuỗi không rỗng, duy nhất trong một lần chạy |
| `touchpoint_id` | Phải tồn tại trong cấu hình điểm chạm |
| `observed_at` | Thời gian ISO 8601 có múi giờ |
| `image_path` | Tệp tồn tại, đọc được và có định dạng được hỗ trợ |

`journey_id` có thể thiếu. Khi thiếu trường này, quan sát vẫn được dùng để thống kê riêng tại điểm chạm nhưng không được đưa vào thống kê chuyển tiếp đa điểm chạm.

### 5.3. Kiểm tra đầu vào

- Từ chối `event_id` trùng.
- Từ chối thời gian không có múi giờ.
- Không suy đoán `touchpoint_id` từ tên tệp.
- Không tự sinh `journey_id` từ ảnh khuôn mặt.
- Không lưu ảnh đầu vào sang vị trí khác nếu cấu hình chưa cho phép.

---

## 6. Quy trình xử lý một ảnh

### 6.1. Bước 1 – Đọc và kiểm tra ảnh

Kiểm tra:

- Tệp đọc được.
- Chiều rộng và chiều cao lớn hơn không.
- Số kênh màu hợp lệ.
- Không vượt giới hạn kích thước cấu hình.

Ảnh lỗi trả `INVALID_IMAGE` và không chuyển vào mô hình.

### 6.2. Bước 2 – Phát hiện khuôn mặt

Bộ phát hiện được nạp từ cấu hình đã khóa sau benchmark. Đầu ra chuẩn:

```json
{
  "box": [10.0, 20.0, 110.0, 140.0],
  "score": 0.97,
  "landmarks": [[35.0, 60.0], [80.0, 60.0], [58.0, 85.0], [40.0, 110.0], [76.0, 110.0]]
}
```

Mỗi khung bao có một điểm phát hiện. Khung bao chỉ được xem là một khuôn mặt hợp lệ khi điểm này đạt mức tối thiểu trong cấu hình đã khóa. Mức tối thiểu phải lấy từ cấu hình đã dùng trong thực nghiệm, không đặt lại trong mã phương pháp.

### 6.3. Bước 3 – Cắt và chuẩn hóa khuôn mặt

- Cắt theo khung bao đã giới hạn trong ảnh.
- Căn chỉnh bằng điểm mốc nếu mô hình và kết quả benchmark yêu cầu.
- Đổi kích thước, số kênh và miền giá trị đúng với bộ phân loại được chọn.
- Không áp dụng bộ lọc làm đẹp hoặc biến đổi không có trong giao thức huấn luyện.

Nếu vùng cắt rỗng hoặc không đủ kích thước tối thiểu, trả `INVALID_FACE_CROP`.

### 6.4. Bước 4 – Phân loại biểu cảm

Bộ phân loại trả về bảy giá trị đầu ra theo thứ tự lớp đã khóa. Bộ chuyển đổi phải xác nhận:

- Có đúng bảy giá trị hữu hạn.
- Giá trị không âm sau Softmax.
- Tổng xác suất sai khác `1` không quá dung sai cấu hình.

Nhãn dự đoán là lớp có xác suất lớn nhất. Độ tin cậy bằng xác suất của nhãn đó.

Nếu độ tin cậy dưới ngưỡng vận hành đã được xác định trong thực nghiệm, trả `LOW_CONFIDENCE`. Không tự đổi nhãn thành Neutral.

### 6.5. Bước 5 – Tạo sự kiện quan sát

Một quan sát hợp lệ có cấu trúc:

```json
{
  "event_id": "evt-000001",
  "journey_id": "journey-anonymous-001",
  "touchpoint_id": "tp-entry",
  "observed_at": "2026-09-22T10:00:00+07:00",
  "predicted_label": "Neutral",
  "confidence": 0.73,
  "class_probabilities": {
    "Angry": 0.03,
    "Disgust": 0.01,
    "Fear": 0.02,
    "Happy": 0.15,
    "Sad": 0.03,
    "Surprise": 0.03,
    "Neutral": 0.73
  },
  "quality_status": "VALID",
  "detector_version": "from-config",
  "classifier_version": "from-config"
}
```

`class_probabilities` được lưu trong đầu ra kỹ thuật để kiểm tra và phân tích lỗi. Báo cáo hành trình chính chỉ sử dụng `predicted_label`, `confidence` và trạng thái chất lượng; không quy đổi véc-tơ thành điểm cảm xúc chung.

---

## 7. Mã trạng thái

| Mã | Ý nghĩa | Tạo quan sát hợp lệ |
|---|---|---:|
| `VALID` | Xử lý thành công | Có |
| `INVALID_INPUT` | Thiếu hoặc sai trường đầu vào | Không |
| `INVALID_IMAGE` | Ảnh không đọc được hoặc sai định dạng | Không |
| `NO_FACE` | Không có khuôn mặt hợp lệ theo cấu hình bộ phát hiện | Không |
| `MULTIPLE_FACES` | Có nhiều hơn một khuôn mặt | Không |
| `INVALID_FACE_CROP` | Vùng khuôn mặt không hợp lệ | Không |
| `LOW_CONFIDENCE` | Dự đoán dưới ngưỡng vận hành | Không |
| `MODEL_ERROR` | Mô hình hoặc đầu ra mô hình không hợp lệ | Không |

Không bỏ qua lỗi âm thầm. Mọi đầu vào đều phải tạo một bản ghi trạng thái để tính tỷ lệ dữ liệu không hợp lệ.

---

## 8. Hình thành hành trình

### 8.1. Điều kiện ghép sự kiện

Hai sự kiện chỉ thuộc cùng hành trình khi có cùng `journey_id` do nguồn bên ngoài cung cấp. Không dùng ảnh, đặc trưng khuôn mặt, giới tính, tuổi hoặc biểu cảm để suy ra mã hành trình.

### 8.2. Sắp xếp

Trong mỗi `journey_id`, sự kiện hợp lệ được sắp theo:

1. `observed_at` tăng dần.
2. Thứ tự điểm chạm trong cấu hình khi thời gian bằng nhau.
3. Nếu vẫn không phân giải được, đánh dấu `ORDER_CONFLICT` và loại cặp đó khỏi thống kê chuyển tiếp.

### 8.3. Điểm chạm thiếu

Danh sách điểm chạm mong đợi được định nghĩa trong cấu hình. Với từng hành trình:

- Ghi danh sách điểm chạm đã quan sát.
- Ghi danh sách điểm chạm bị thiếu.
- Không tự sinh sự kiện hoặc nội suy nhãn tại điểm chạm thiếu.

### 8.4. Sự kiện trùng lặp

- Hai bản ghi có cùng `event_id` là trùng lặp cứng; chỉ giữ bản ghi đầu tiên và ghi lỗi.
- Không coi hai sự kiện khác `event_id` nhưng cùng nhãn là trùng lặp.
- Nếu nghiệp vụ cần mỗi hành trình chỉ có một sự kiện tại một điểm chạm, quy tắc chọn sự kiện phải được bổ sung bằng phiên bản đặc tả mới trước khi viết mã.

---

## 9. Các phép phân tích

### 9.1. Phân bố nhãn tại điểm chạm

Với điểm chạm `t` và lớp `k`:

$$
n_{t,k}=\sum_i \mathbf{1}(T_i=t \land Y_i=k \land Q_i=\text{VALID}).
$$

Tỷ lệ:

$$
r_{t,k}=\frac{n_{t,k}}{\sum_j n_{t,j}}.
$$

Nếu điểm chạm không có quan sát hợp lệ, tỷ lệ để trống và ghi số mẫu bằng `0`; không thay bằng `0%` cho từng lớp.

### 9.2. Ma trận chuyển tiếp

Ma trận được tính riêng cho từng cặp điểm chạm liên tiếp `(u, v)`. Với lớp trước `a` và lớp sau `b`:

$$
N_{a,b}^{u\rightarrow v}
=
\sum_s
\mathbf{1}(Y_{s,u}=a \land Y_{s,v}=b),
$$

trong đó `s` là hành trình có quan sát hợp lệ tại cả hai điểm chạm.

Tỷ lệ chuyển theo hàng:

$$
P_{a,b}^{u\rightarrow v}
=
\frac{N_{a,b}^{u\rightarrow v}}
{\sum_j N_{a,j}^{u\rightarrow v}}.
$$

Nếu một hàng không có mẫu, toàn bộ hàng để trống. Ma trận chỉ mô tả tần suất thay đổi nhãn, không thể hiện nguyên nhân và không phải xác suất chuyển trạng thái tâm lý thật.

### 9.3. Chất lượng dữ liệu

Tối thiểu phải xuất:

- Tổng số yêu cầu đầu vào.
- Số và tỷ lệ theo từng mã trạng thái.
- Số hành trình có mã hợp lệ.
- Số hành trình đủ dữ liệu cho từng cặp điểm chạm.
- Tỷ lệ thiếu từng điểm chạm.
- Số xung đột thứ tự và bản ghi trùng.

### 9.4. Các phép tính bị cấm trong phiên bản này

- Gán trọng số dương/âm cho bảy lớp biểu cảm.
- Tính điểm hóa trị từ xác suất FER.
- Tính điểm đỉnh–cuối.
- Tính điểm cảm xúc trung bình toàn hành trình.
- Chuyển nhãn FER thành mức hài lòng.

---

## 10. Đầu ra bắt buộc

```text
PROPOSED_METHOD/results/<run_id>/
├── config.lock.yaml
├── environment.json
├── input_manifest.json
├── event_results.jsonl
├── valid_observations.csv
├── rejected_observations.csv
├── journeys.jsonl
├── touchpoint_distribution.csv
├── transition_counts.csv
├── transition_rates.csv
├── data_quality.csv
├── figures/
│   ├── touchpoint_distribution.pdf
│   ├── touchpoint_distribution.png
│   ├── transition_heatmap.pdf
│   ├── transition_heatmap.png
│   ├── missing_touchpoints.pdf
│   ├── missing_touchpoints.png
│   ├── quality_status.pdf
│   └── quality_status.png
├── run_summary.json
└── audit.json
```

### 10.1. `valid_observations.csv`

```text
event_id,journey_id,touchpoint_id,observed_at,predicted_label,confidence,detector_version,classifier_version
```

### 10.2. `transition_counts.csv`

```text
from_touchpoint,to_touchpoint,from_label,to_label,count,eligible_journeys
```

### 10.3. `audit.json`

Phải lưu:

- Mã phiên bản mã nguồn.
- Mã kiểm tra cấu hình.
- Mã kiểm tra trọng số hai mô hình.
- Thời điểm chạy.
- Số lượng đầu vào và đầu ra.
- Danh sách cảnh báo.

### 10.4. Hình và biểu đồ báo cáo

Mã tạo báo cáo phải sinh tự động:

- Biểu đồ cột chồng thể hiện phân bố bảy lớp biểu cảm tại từng điểm chạm.
- Bản đồ nhiệt ma trận chuyển tiếp cho từng cặp điểm chạm liên tiếp có đủ dữ liệu.
- Biểu đồ tỷ lệ thiếu dữ liệu theo điểm chạm.
- Biểu đồ số lượng hoặc tỷ lệ theo từng mã trạng thái chất lượng.

Không tạo bản đồ nhiệt chuyển tiếp khi không có `journey_id` đáng tin cậy hoặc số hành trình đủ điều kiện bằng `0`. Trong trường hợp đó, chương trình phải xuất cảnh báo và báo cáo “không đủ dữ liệu”, không tạo ma trận toàn số không.

Biểu đồ phải dùng cùng thứ tự bảy lớp trong toàn luận văn, có nhãn tiếng Việt, đơn vị và số mẫu. Tất cả số liệu phải được đọc từ các tệp đầu ra của cùng `run_id`; không sửa hình bằng tay sau khi sinh.

Sơ đồ khối, lưu đồ xử lý và sơ đồ hình thành hành trình dùng ở Chương 3 được dựng từ chính đặc tả này. Các biểu đồ có số liệu chỉ được chèn ở Chương 5 sau khi đã kiểm tra đầu ra.

---

## 11. Thiết kế mã nguồn dự kiến

```text
PROPOSED_METHOD/
├── TECH_SPEC.md
├── README.md
├── pyproject.toml
├── configs/
│   ├── pipeline.yaml
│   └── touchpoints.yaml
├── fixtures/
├── src/
│   └── proposed_method/
│       ├── schemas.py
│       ├── input_validation.py
│       ├── detector_adapter.py
│       ├── classifier_adapter.py
│       ├── observation_pipeline.py
│       ├── journey_builder.py
│       ├── analytics.py
│       ├── build_figures.py
│       ├── audit.py
│       └── cli.py
├── tests/
└── results/
```

Các bộ chuyển đổi mô hình chỉ đọc cấu hình và trọng số đã được lựa chọn từ hai benchmark; không sao chép mã mô hình vào nhiều nơi nếu có thể đóng gói dùng chung.

---

## 12. Bộ tình huống kiểm thử

### 12.1. Xử lý ảnh

- Ảnh có đúng một khuôn mặt hợp lệ.
- Ảnh không có khuôn mặt.
- Ảnh có nhiều khuôn mặt.
- Ảnh hỏng.
- Khung bao vượt biên ảnh.
- Đầu ra bộ phân loại không đủ bảy lớp.
- Độ tin cậy dưới ngưỡng.

### 12.2. Hành trình

- Hành trình có đủ các điểm chạm đúng thứ tự.
- Hành trình thiếu một điểm chạm.
- Sự kiện đến không đúng thứ tự nhưng có thời gian hợp lệ.
- Hai sự kiện trùng `event_id`.
- Hai sự kiện cùng thời gian gây xung đột thứ tự.
- Quan sát không có `journey_id`.

### 12.3. Phân tích

Tạo một bộ dữ liệu nhỏ có thể tính tay để kiểm tra:

- Số lượng và tỷ lệ lớp tại từng điểm chạm.
- Ma trận chuyển tiếp dạng số lượng.
- Chuẩn hóa ma trận theo hàng.
- Mẫu số chỉ gồm hành trình đủ dữ liệu ở cả hai điểm chạm.
- Hàng không có mẫu được để trống.

---

## 13. Đánh giá trước khi viết Chương 3

Phải có hai mức đánh giá.

### 13.1. Kiểm chứng chức năng

- Toàn bộ tình huống ở Mục 12 vượt qua kiểm thử tự động.
- Kết quả phân tích khớp với phép tính tay trên bộ dữ liệu nhỏ.
- Chạy lại cùng cấu hình tạo cùng kết quả thống kê.
- Mọi đầu vào đều truy vết được đến trạng thái cuối.

### 13.2. Kiểm chứng trên dữ liệu thực hoặc dữ liệu kiểm soát

- Có ảnh tại ít nhất hai điểm chạm.
- Có mã hành trình đã được gán độc lập với khuôn mặt.
- Có nhãn mong đợi cho thứ tự và dữ liệu thiếu.
- Nếu dùng ảnh người thật, phải có quyền sử dụng phù hợp.
- Không dùng bộ dữ liệu giả để đưa ra kết luận về độ chính xác biểu cảm ngoài thực tế.

---

## 14. Cổng quyết định

Chỉ bắt đầu viết Chương 3 khi:

1. Đặc tả này đã được duyệt.
2. Mô hình phát hiện đã được khóa từ benchmark.
3. Mô hình phân loại đã được xác định rõ nguồn, trọng số, thứ tự lớp, tiền xử lý và vượt qua kiểm thử tích hợp.
4. Mã phương pháp đã triển khai đúng cấu trúc đầu vào và đầu ra.
5. Kiểm thử tự động đã đạt.
6. Có thư mục kết quả của một lần chạy đầy đủ.
7. Các bảng phân bố, chất lượng dữ liệu và ma trận chuyển tiếp được sinh bằng chương trình.
8. Không còn tham số hoặc quy tắc xử lý được điền tạm.
9. Các hình và biểu đồ có số liệu đã được sinh lại từ đầu ra thô bằng một lệnh và khớp với các bảng CSV.

Sau đó, Chương 3 mô tả đúng phương pháp đã chạy; Chương 5 trình bày dữ liệu, phép đánh giá và kết quả. Không viết ngược từ kết luận mong muốn để điều chỉnh phương pháp.
