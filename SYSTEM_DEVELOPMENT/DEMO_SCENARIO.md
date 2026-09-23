# Kịch bản demo hệ thống không sử dụng camera

## 1. Trạng thái và mục đích

- **Trạng thái:** Kế hoạch để triển khai mã nguồn; các lệnh trong tài liệu chưa tồn tại cho tới khi hoàn thành các công việc `DATA-01` đến `DATA-05`.
- **Mục đích:** Trình diễn đầy đủ luồng CRM, xử lý ảnh và hành trình đa điểm chạm khi không có camera vật lý.
- **Nguyên tắc:** Chương trình mô phỏng camera gửi ảnh vào cùng API mà thiết bị thật sẽ sử dụng. Không ghi trực tiếp vào cơ sở dữ liệu và không bỏ qua các bước phát hiện, phân loại hay nhận dạng.

Demo phải chứng minh được:

1. Có thể đăng ký khuôn mặt cho khách hàng mô phỏng.
2. Có thể tìm khách hàng bằng một ảnh khác với ảnh đăng ký.
3. Có thể tiếp nhận ảnh tại nhiều điểm chạm.
4. Có thể liên kết các ảnh của cùng khách hàng vào một lượt ghé thăm.
5. Có thể phân biệt hai lượt đến khác nhau của cùng khách hàng.
6. Có thể xem sản phẩm, đơn hàng và lịch sử mua hàng.
7. Có thể tạo phân bố biểu cảm và bảng thay đổi giữa các điểm chạm.
8. Có thể xử lý khách không xác định, ảnh không có mặt và ảnh nhiều mặt.

## 2. Nguồn ảnh

### 2.1. Nguồn chính: Yale Face Database

Trang chính thức mô tả bộ dữ liệu gồm 165 ảnh xám của 15 người, mỗi người có 11 ảnh trong các điều kiện như bình thường, vui, buồn, ngạc nhiên, đeo kính, nhắm mắt và thay đổi ánh sáng. Trang cũng nêu bộ dữ liệu được cung cấp công khai cho mục đích phi thương mại: [Yale Face Database](http://cvc.cs.yale.edu/cvc/projects/yalefaces/yalefaces.html).

Nguồn này phù hợp với demo vì:

- Có nhiều ảnh của cùng một mã người để tách ảnh đăng ký và ảnh truy vấn.
- Có thay đổi về biểu hiện khuôn mặt và điều kiện chụp.
- Dung lượng nhỏ, thuận tiện để dựng lại demo.
- Danh tính được biểu diễn bằng mã người; hệ thống không cần biết tên thật.

Giới hạn:

- Dữ liệu nhỏ, cũ và được chụp trong môi trường kiểm soát.
- Ảnh xám không đại diện cho camera tại cửa hàng hiện đại.
- Tên điều kiện `happy`, `sad` hoặc `surprised` không đồng nghĩa với nhãn chuẩn của bài toán FER bảy lớp.
- Bộ dữ liệu chỉ dùng để trình diễn luồng hệ thống, không dùng để kết luận mô hình hoạt động tốt trong môi trường bán lẻ.

### 2.2. Nguồn dự phòng: DigiFace-1M

DigiFace-1M là bộ ảnh khuôn mặt tổng hợp dành cho nghiên cứu nhận dạng khuôn mặt. Kho chính thức nêu một phần có 10.000 danh tính với 72 ảnh mỗi danh tính và một phần có 100.000 danh tính với 5 ảnh mỗi danh tính. Dữ liệu được cấp cho nghiên cứu phi thương mại: [Microsoft DigiFace-1M](https://github.com/microsoft/DigiFace1M).

Chỉ dùng nguồn này khi:

- Việc sử dụng ảnh người thật trong Yale không được chấp nhận; hoặc
- Chất lượng ảnh Yale làm bộ phát hiện không hoạt động ổn định.

DigiFace-1M có dung lượng tải lớn. Chương trình chuẩn bị dữ liệu phải chỉ lấy một tập con cần thiết hoặc yêu cầu người triển khai đặt tệp nguồn vào thư mục cục bộ. Không tự tải toàn bộ dữ liệu trong quá trình khởi động hệ thống.

### 2.3. Quyết định cho phiên bản đầu

Phiên bản đầu chuẩn bị bộ dữ liệu từ Yale Face Database. DigiFace-1M là phương án dự phòng, không trộn hai nguồn trong cùng một lần demo.

Ảnh nguồn và ảnh dẫn xuất không được đưa vào kho mã. Kho mã chỉ lưu:

- Địa chỉ nguồn.
- Nội dung giấy phép hoặc đường dẫn giấy phép.
- Mã kiểm tra của tệp nguồn đã dùng.
- Danh sách mã người được chọn.
- Chương trình tạo dữ liệu.
- Tệp manifest không chứa véc-tơ khuôn mặt.

## 3. Phân chia người trong dữ liệu

Với Yale Face Database, bản chia mặc định:

| Nhóm | Mã người | Mục đích |
|---|---|---|
| Hiệu chỉnh ngưỡng | `subject01`–`subject08` | Tạo cặp cùng người/khác người để xác định ngưỡng nhận dạng |
| Khách hàng đã đăng ký | `subject09`–`subject13` | Tạo năm hồ sơ khách hàng mô phỏng |
| Khách không xác định | `subject14`–`subject15` | Gửi ảnh vào điểm chạm nhưng không đăng ký trong CRM |

Không dùng ảnh của `subject09`–`subject15` để chọn ngưỡng. Việc tách này giúp demo không tự chọn ngưỡng trên chính những người sẽ được trình diễn.

### 3.1. Ảnh đăng ký

Mỗi khách hàng mô phỏng sử dụng hai ảnh đăng ký lấy từ các điều kiện ổn định, ví dụ:

- `normal`.
- `noglasses` hoặc `centerlight`.

Tên tệp thật phải được ghi trong manifest. Không được dùng lại cùng tệp cho ảnh quan sát.

### 3.2. Ảnh quan sát

Ảnh tại điểm chạm lấy từ các tệp còn lại của cùng mã người, chẳng hạn:

- `happy`.
- `sad`.
- `surprised`.
- `glasses`.
- `leftlight` hoặc `rightlight`.

Những tên này chỉ mô tả điều kiện do bộ dữ liệu cung cấp. `events.csv` không có cột `expected_expression_label`. Nhãn biểu cảm được lưu trong hệ thống phải là đầu ra thật của mô hình Emotion.

## 4. Tạo ảnh mô phỏng camera

Ảnh Yale là ảnh khuôn mặt đã được cắt. Để mô phỏng ảnh từ camera, chương trình chuẩn bị dữ liệu thực hiện các bước xác định trước:

1. Đọc ảnh gốc và chuyển sang ảnh ba kênh màu.
2. Thay đổi kích thước nhưng giữ nguyên tỷ lệ.
3. Đặt ảnh lên một khung nền 640 × 480 pixel.
4. Thay đổi vị trí và kích thước khuôn mặt theo cấu hình của từng điểm chạm.
5. Có thể thay đổi nhẹ độ sáng hoặc độ mờ bằng tham số đã ghi trong manifest.
6. Lưu ảnh JPEG với cấu hình cố định.

Mọi phép biến đổi dùng cùng một hạt giống ngẫu nhiên cố định. Manifest phải lưu:

- Tên tệp nguồn.
- Mã kiểm tra tệp nguồn.
- Kích thước, vị trí và phép biến đổi.
- Mã kiểm tra ảnh đầu ra.

Không dùng mô hình sinh ảnh để thay đổi biểu cảm của người trong ảnh. Việc đó có thể làm thay đổi danh tính hoặc tạo nhãn biểu cảm không kiểm chứng được.

### 4.1. Ảnh cho các trường hợp lỗi

- `NO_FACE`: chỉ có khung nền, không có ảnh khuôn mặt.
- `MULTIPLE_FACES`: đặt hai ảnh của hai mã người khác nhau trên cùng khung.
- `INVALID_IMAGE`: tạo tệp có phần mở rộng `.jpg` nhưng nội dung không phải ảnh.
- `UNIDENTIFIED`: dùng ảnh hợp lệ của `subject14` hoặc `subject15`.

Các ảnh lỗi do chương trình tạo phải được đánh dấu rõ `generated_test_case=true` trong manifest.

## 5. Dữ liệu CRM mô phỏng

### 5.1. Khách hàng

Không dùng tên thật hoặc suy đoán thông tin của người trong ảnh. Tạo năm hồ sơ:

| Mã khách hàng | Tên hiển thị | Mã người nguồn |
|---|---|---|
| `CUS-DEMO-001` | Khách hàng mô phỏng 01 | `subject09` |
| `CUS-DEMO-002` | Khách hàng mô phỏng 02 | `subject10` |
| `CUS-DEMO-003` | Khách hàng mô phỏng 03 | `subject11` |
| `CUS-DEMO-004` | Khách hàng mô phỏng 04 | `subject12` |
| `CUS-DEMO-005` | Khách hàng mô phỏng 05 | `subject13` |

Tất cả số điện thoại và email dùng miền dành cho ví dụ, không giống dữ liệu cá nhân thật. Các hồ sơ này được đánh dấu `demo_data=true`.

### 5.2. Các điểm chạm trong cửa hàng

| Thứ tự | Mã điểm chạm | Tên hiển thị |
|---:|---|---|
| 1 | `TP-ENTRANCE` | Cửa vào |
| 2 | `TP-DISPLAY` | Khu trưng bày sản phẩm |
| 3 | `TP-CONSULT` | Khu tư vấn |
| 4 | `TP-CHECKOUT` | Quầy thanh toán |

Hệ thống demo chỉ có một cửa hàng nên không tạo bảng hoặc mã chi nhánh. Bốn điểm chạm được dùng trực tiếp trong toàn hệ thống.

### 5.3. Sản phẩm

Bộ dữ liệu có tối thiểu ba nhóm và sáu sản phẩm:

| Nhóm | Ví dụ sản phẩm |
|---|---|
| Đồ uống | Nước khoáng, trà đóng chai |
| Đồ ăn nhẹ | Bánh quy, hạt dinh dưỡng |
| Chăm sóc cá nhân | Khăn giấy, nước rửa tay |

Mỗi sản phẩm có mã, tên, nhóm, giá hiện tại và trạng thái. Đây là dữ liệu hoàn toàn mô phỏng.

### 5.4. Đơn hàng và lịch sử mua hàng

- `CUS-DEMO-001` có một đơn cũ trước ngày demo và một đơn được tạo trong lượt demo.
- `CUS-DEMO-002` có ít nhất hai đơn ở hai thời điểm để kiểm tra bộ lọc lịch sử.
- `CUS-DEMO-003` có một đơn đã hủy để kiểm tra trạng thái.
- Một sản phẩm được đổi giá sau đơn cũ để xác nhận lịch sử vẫn hiển thị đơn giá tại thời điểm mua.
- Các khách hàng còn lại có thể chưa mua hàng để kiểm tra trạng thái không có dữ liệu.

## 6. Cấu trúc thư mục

```text
SYSTEM/
├── data/
│   └── raw/                         # Bị loại khỏi Git
│       └── yale/
├── fixtures/
│   └── demo_dataset/
│       ├── README.md
│       ├── sources.json
│       ├── customers.csv
│       ├── product_categories.csv
│       ├── products.csv
│       ├── touchpoints.csv
│       ├── journeys.csv
│       ├── events.csv
│       ├── orders.csv
│       ├── order_items.csv
│       ├── image_manifest.csv
│       ├── enrollment/             # Bị loại khỏi Git
│       ├── observations/           # Bị loại khỏi Git
│       └── expected/
│           └── expected_visits.json
├── scripts/
│   ├── prepare_demo_dataset.py
│   ├── calibrate_face_threshold.py
│   ├── seed_demo_crm.py
│   ├── enroll_demo_faces.py
│   ├── replay_demo_journeys.py
│   └── verify_demo_results.py
└── artifacts/
    └── demo-runs/                   # Bị loại khỏi Git
```

## 7. Hợp đồng dữ liệu sự kiện

`events.csv` có các trường:

| Trường | Nội dung |
|---|---|
| `scenario_id` | Mã tình huống demo |
| `event_id` | Mã sự kiện duy nhất |
| `expected_customer_code` | Mã khách mong đợi hoặc để trống |
| `expected_visit_key` | Mã lượt logic dùng để đối chiếu, không gửi lên API |
| `touchpoint_code` | Điểm chạm gửi dữ liệu |
| `observed_at` | Thời gian ISO 8601 có múi giờ |
| `image_path` | Đường dẫn ảnh tương đối |
| `expected_image_status` | Trạng thái ảnh mong đợi |
| `expected_identity_status` | `MATCHED`, `NO_MATCH` hoặc `NOT_RUN` |
| `source_subject_id` | Mã người của bộ dữ liệu, không gửi lên API |
| `source_condition` | Điều kiện ảnh nguồn, không phải nhãn FER |

`expected_customer_code`, `expected_visit_key` và các trường `expected_*` chỉ dùng cho chương trình đối chiếu. Chương trình mô phỏng không được gửi những trường này vào API để tránh tiết lộ đáp án cho hệ thống.

## 8. Các tình huống demo

### DEMO-01 – Khách hàng đi qua đủ bốn điểm chạm

- Khách hàng: `CUS-DEMO-001`.
- Gửi bốn ảnh khác nhau của `subject09` theo thứ tự cửa vào, trưng bày, tư vấn và thanh toán.
- Khoảng cách thời gian nằm trong một lượt ghé thăm.
- Sau sự kiện thanh toán, tạo một đơn hàng có hai sản phẩm.

Kết quả mong đợi:

- Cả bốn quan sát cùng thuộc một khách hàng và một `visit_id`.
- Dòng thời gian có bốn điểm chạm đúng thứ tự.
- Đơn hàng được liên kết với lượt ghé thăm khi quy tắc thời gian xác định được duy nhất một lượt.
- Hồ sơ khách hàng hiển thị đơn hàng mới trong lịch sử.

### DEMO-02 – Hành trình thiếu một điểm chạm

- Khách hàng: `CUS-DEMO-002`.
- Chỉ gửi ảnh tại cửa vào, khu trưng bày và quầy thanh toán.
- Không tạo bản ghi giả tại khu tư vấn.

Kết quả mong đợi:

- Một lượt ghé thăm có ba quan sát.
- Giao diện thể hiện khu tư vấn bị thiếu.
- Báo cáo thay đổi chỉ dùng các cặp quan sát thực sự có trong lượt.

### DEMO-03 – Cùng khách hàng quay lại

- Khách hàng: `CUS-DEMO-001`.
- Phát lại hai nhóm sự kiện cách nhau lâu hơn `VISIT_IDLE_TIMEOUT`.

Kết quả mong đợi:

- Hệ thống tạo hai `visit_id` khác nhau.
- Hai lượt cùng xuất hiện trong hồ sơ khách hàng.
- Bản ghi của lượt sau không bị nối vào lượt trước.

### DEMO-04 – Khách hàng không xác định

- Dùng ảnh của `subject14`, không tạo hồ sơ và không đăng ký mẫu.
- Gửi ảnh tại khu trưng bày.

Kết quả mong đợi:

- Nếu phân loại biểu cảm thành công, bản ghi tham gia phân bố tại điểm chạm.
- `identity_status=NO_MATCH`.
- Không có `customer_id` và `visit_id`.
- Không tự tạo hồ sơ khách hàng.

### DEMO-05 – Dữ liệu ảnh không hợp lệ

Gửi lần lượt:

1. Ảnh nền không có mặt.
2. Ảnh có hai khuôn mặt.
3. Tệp hỏng.

Kết quả mong đợi:

- Các trạng thái tương ứng là `NO_FACE`, `MULTIPLE_FACES` và lỗi ảnh.
- Không tạo lượt ghé thăm.
- Các lỗi xuất hiện trên trang chất lượng dữ liệu.

### DEMO-06 – Tìm khách hàng bằng ảnh

- Tải lên một ảnh chưa dùng để đăng ký của `subject10`.

Kết quả mong đợi:

- Kết quả là `CUS-DEMO-002` nếu đạt ngưỡng đã hiệu chỉnh.
- Ảnh truy vấn không được lưu sau khi yêu cầu kết thúc.
- Nhật ký ghi người thực hiện và thời gian tìm kiếm, không ghi nội dung ảnh hoặc véc-tơ.

### DEMO-07 – Quản lý sản phẩm và lịch sử mua hàng

1. Tìm sản phẩm theo mã hoặc tên.
2. Lọc sản phẩm theo nhóm.
3. Mở chi tiết một sản phẩm.
4. Mở hồ sơ `CUS-DEMO-001` và xem lịch sử mua hàng.
5. Lọc lịch sử theo thời gian.
6. Mở đơn cũ và đối chiếu đơn giá đã lưu.
7. Thay đổi giá hiện tại của sản phẩm rồi mở lại đơn cũ.

Kết quả mong đợi:

- Đơn cũ vẫn giữ tên, mã và đơn giá tại thời điểm mua.
- Sản phẩm ngừng kinh doanh vẫn hiển thị trong lịch sử nhưng không thể thêm vào đơn mới.

## 9. Các lệnh cần triển khai

Tên lệnh mục tiêu:

```bash
make demo-prepare DEMO_SOURCE=/duong-dan/yalefaces.tar
make demo-calibrate
make demo-reset
make demo-seed
make demo-enroll
make demo-replay SCENARIO=all SPEED=0
make demo-verify
```

Ý nghĩa:

- `demo-prepare`: kiểm tra nguồn và tạo ảnh/tệp CSV mô phỏng.
- `demo-calibrate`: tạo tệp ngưỡng từ nhóm `subject01`–`subject08`.
- `demo-reset`: chỉ xóa dữ liệu có cờ `demo_data=true`.
- `demo-seed`: tạo điểm chạm, khách hàng, sản phẩm và đơn hàng mẫu.
- `demo-enroll`: gửi ảnh đăng ký qua API.
- `demo-replay`: gửi sự kiện theo thứ tự; `SPEED=0` gửi ngay nhưng giữ nguyên `observed_at`.
- `demo-verify`: đọc dữ liệu qua API và đối chiếu với `expected_visits.json`.

Không dùng lệnh SQL để chèn quan sát hoặc kết quả nhận dạng. Riêng dữ liệu danh mục CRM có thể dùng API seed hoặc một tiến trình seed chính thức chạy qua lớp nghiệp vụ.

## 10. Trình tự trình diễn

### Bước 1 – Khởi động và giới thiệu dữ liệu

- Khởi động toàn bộ dịch vụ.
- Cho xem `sources.json`, số khách hàng mô phỏng, số sản phẩm, số hành trình và số sự kiện.
- Nêu rõ ảnh đến từ bộ dữ liệu nghiên cứu và không phải khách hàng thật.

### Bước 2 – Chức năng CRM

- Đăng nhập.
- Mở danh sách khách hàng.
- Mở danh mục sản phẩm và thử bộ lọc.
- Mở hồ sơ `CUS-DEMO-001` và lịch sử mua hàng có sẵn.

### Bước 3 – Đăng ký và tìm kiếm bằng khuôn mặt

- Chạy đăng ký ảnh cho năm khách hàng mô phỏng.
- Dùng màn hình tìm kiếm ảnh để tìm `CUS-DEMO-002`.
- Cho xem trạng thái khớp và phiên bản ngưỡng, không tuyên bố đây là độ chính xác tổng quát.

### Bước 4 – Phát lại hành trình

- Chạy `DEMO-01`.
- Mở danh sách lượt ghé thăm và chi tiết lượt mới.
- Kiểm tra bốn điểm chạm, thời gian, nhãn biểu cảm và độ tin cậy.
- Tạo hoặc mở đơn hàng tại quầy thanh toán.

### Bước 5 – Trường hợp hành trình khác

- Chạy `DEMO-02` để xem hành trình thiếu điểm chạm.
- Chạy `DEMO-03` để chứng minh cùng khách hàng có hai lượt ghé thăm khác nhau.
- Chạy `DEMO-04` để xem khách không xác định chỉ tham gia thống kê điểm chạm.

### Bước 6 – Dữ liệu lỗi

- Chạy `DEMO-05`.
- Mở trang chất lượng dữ liệu và chỉ ra số trường hợp không mặt, nhiều mặt và ảnh hỏng.

### Bước 7 – Báo cáo

- Mở phân bố biểu cảm theo điểm chạm.
- Chọn một cặp điểm chạm và mở bảng thay đổi nhãn.
- Chỉ ra đồng thời số mẫu và tỷ lệ.
- Nêu rõ đây là nhãn biểu cảm quan sát được, không phải điểm hài lòng.

### Bước 8 – Đối chiếu tự động

- Chạy `demo-verify`.
- Cho xem số điều kiện đạt, không đạt và nguyên nhân.
- Lưu kết quả cùng mã phiên bản hệ thống.

## 11. Đầu ra của mỗi lần demo

Mỗi lần chạy tạo một thư mục:

```text
SYSTEM/artifacts/demo-runs/<run_id>/
├── run.json
├── environment.json
├── source_checksums.json
├── threshold_snapshot.json
├── replay_results.jsonl
├── verification.json
├── report_distribution.json
├── report_changes.json
└── screenshots/
```

`run.json` tối thiểu chứa:

- Thời gian chạy.
- Phiên bản mã nguồn.
- Phiên bản ba mô hình.
- Phiên bản migration.
- Các tình huống đã chạy.
- Số sự kiện thành công và lỗi.

## 12. Tiêu chí chấp nhận bộ demo

1. Dữ liệu có thể tạo lại từ cùng tệp nguồn và cùng cấu hình.
2. Không có ảnh nguồn hoặc ảnh dẫn xuất trong kho mã.
3. Không có tên thật, email thật hoặc số điện thoại thật.
4. Ảnh đăng ký và ảnh truy vấn của một khách hàng không phải cùng một tệp.
5. Nhóm hiệu chỉnh ngưỡng không trùng nhóm khách hàng demo.
6. Chương trình mô phỏng chỉ gọi API công khai.
7. Chạy lại cùng `event_id` không tạo quan sát trùng.
8. Hai lượt của cùng khách hàng được tách đúng theo cấu hình thời gian.
9. Khách không xác định không tạo hồ sơ hoặc hành trình cá nhân.
10. Các lỗi ảnh xuất hiện trong thống kê chất lượng dữ liệu.
11. Lịch sử mua hàng giữ nguyên đơn giá cũ sau khi giá sản phẩm thay đổi.
12. `verification.json` ghi rõ từng điều kiện đạt hay không đạt.

## 13. Những điều không được kết luận từ demo

- Không dùng demo để công bố độ chính xác FER.
- Không dùng năm khách hàng mô phỏng để công bố độ chính xác nhận dạng tổng quát.
- Không gọi thay đổi nhãn là thay đổi cảm xúc thật hoặc mức độ hài lòng.
- Không coi ảnh ghép trên nền là mô phỏng đầy đủ môi trường camera bán lẻ.
- Không đưa dữ liệu demo vào kết quả benchmark nếu chưa có giao thức đánh giá riêng.
