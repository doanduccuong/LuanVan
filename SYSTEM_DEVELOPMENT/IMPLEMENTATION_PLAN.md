# Kế hoạch triển khai mã nguồn hệ thống

## 1. Mục đích của tài liệu

Tài liệu này dùng để tổ chức việc viết mã cho hệ thống nhận dạng biểu cảm tại nhiều điểm chạm và quản lý quan hệ khách hàng. Đây không phải dàn ý viết báo cáo.

Chỉ bắt đầu viết phần triển khai trong luận văn sau khi các mô-đun dưới đây đã chạy, có dữ liệu kiểm thử và có đầu ra được lưu lại.

## 2. Phạm vi hệ thống cần xây dựng

Hệ thống gồm bốn phần chính:

1. **Máy chủ nghiệp vụ:** xác thực người dùng, quản lý khách hàng, sản phẩm, lịch sử mua hàng, điểm chạm, lượt ghé thăm, bản ghi biểu cảm và báo cáo.
2. **Dịch vụ xử lý ảnh:** phát hiện khuôn mặt, nhận dạng biểu cảm, tạo đặc trưng khuôn mặt để nhận dạng khách hàng.
3. **Giao diện CRM:** cung cấp các màn hình quản lý và tra cứu dữ liệu.
4. **Dịch vụ mô phỏng:** tạo dữ liệu hành trình, lỗi và đơn hàng khi chưa có camera.

Các chức năng phải có trong phiên bản đầu:

- Đăng nhập và phân quyền.
- Quản lý danh sách khách hàng.
- Đăng ký dữ liệu khuôn mặt cho khách hàng đã đồng ý.
- Tìm kiếm khách hàng bằng ảnh khuôn mặt.
- Quản lý nhóm sản phẩm và danh sách sản phẩm.
- Quản lý lịch sử mua hàng.
- Xem chi tiết từng đơn hàng và các sản phẩm đã mua.
- Lọc lịch sử mua hàng theo khách hàng, thời gian và trạng thái đơn.
- Quản lý danh sách và thứ tự điểm chạm.
- Tiếp nhận ảnh tại một điểm chạm.
- Nhận dạng biểu cảm bảy lớp.
- Nhận dạng khách hàng đã đăng ký.
- Liên kết các bản ghi với một lượt ghé thăm.
- Xem hành trình của một lượt ghé thăm theo thứ tự thời gian.
- Thống kê phân bố biểu cảm tại từng điểm chạm.
- Thống kê thay đổi nhãn biểu cảm giữa các điểm chạm liên tiếp.
- Theo dõi số bản ghi hợp lệ và không hợp lệ.
- Theo dõi biến thiên nhãn trong cùng ngày, cùng khu vực và khoảng thời gian đã chọn.

Phiên bản đầu không xử lý video trực tiếp, không theo dõi người chưa đăng ký giữa nhiều camera, không suy luận cảm xúc thật và không tính điểm hài lòng.

Do không có camera thật, phiên bản demo dùng một dịch vụ mô phỏng độc lập. Dịch vụ gửi sự kiện theo lô qua API nghiệp vụ; mọi bản ghi có `source_type=SIMULATOR` và `simulation_run_id` để không bị nhầm với dữ liệu camera. Nhãn mô phỏng chỉ kiểm tra lưu trữ, hành trình và giao diện, không dùng để đánh giá FER.

## 3. Kiến trúc triển khai

### 3.1. Các thành phần

| Thành phần | Trách nhiệm |
|---|---|
| `web` | Giao diện CRM chạy trên trình duyệt |
| `api` | Xử lý nghiệp vụ CRM, phân quyền, lưu dữ liệu và tạo báo cáo |
| `vision` | Phát hiện khuôn mặt, phân loại biểu cảm và tạo véc-tơ đặc trưng khuôn mặt |
| `simulator` | Tạo và gửi dữ liệu trình diễn cho đúng 100 khách hàng |
| `postgres` | Lưu dữ liệu nghiệp vụ và véc-tơ đặc trưng |
| `docker-compose` | Khởi động các thành phần trong môi trường phát triển |

Luồng chính:

```text
Thiết bị hoặc giao diện gửi ảnh + điểm chạm + thời gian
                         |
                         v
                    API nghiệp vụ
                         |
                         v
                   Dịch vụ xử lý ảnh
                         |
           +-------------+-------------+
           |                           |
           v                           v
  nhãn biểu cảm               véc-tơ khuôn mặt
                                       |
                                       v
                          đối sánh khách hàng trong CRM
                                       |
                                       v
                          xác định lượt ghé thăm và lưu
```

### 3.2. Công nghệ dự kiến

| Phần | Công nghệ |
|---|---|
| Giao diện | React, TypeScript, Vite, Ant Design, TanStack Query, Apache ECharts |
| Máy chủ nghiệp vụ | Python, FastAPI, SQLAlchemy, Alembic |
| Xử lý ảnh | Python, OpenCV, PyTorch, RetinaFace-MobileNet0.25, mô hình Emotion của DeepFace, ArcFace |
| Dữ liệu | PostgreSQL và phần mở rộng `pgvector` |
| Kiểm thử | Pytest, Vitest, Playwright |
| Đóng gói | Docker và Docker Compose |

Tên và phiên bản gói phải được khóa trong tệp phụ thuộc khi khởi tạo dự án. Bảng trên là quyết định thiết kế để bắt đầu triển khai, không phải kết luận rằng các công nghệ này tốt hơn mọi lựa chọn khác.

## 4. Cấu trúc mã nguồn dự kiến

```text
SYSTEM/
├── apps/
│   ├── api/
│   │   ├── app/
│   │   │   ├── api/
│   │   │   ├── core/
│   │   │   ├── models/
│   │   │   ├── repositories/
│   │   │   ├── schemas/
│   │   │   ├── services/
│   │   │   └── main.py
│   │   ├── migrations/
│   │   └── tests/
│   └── web/
│       ├── src/
│       │   ├── api/
│       │   ├── components/
│       │   ├── features/
│       │   ├── layouts/
│       │   ├── pages/
│       │   └── routes/
│       └── tests/
├── services/
│   └── vision/
│       ├── app/
│       │   ├── detection/
│       │   ├── expression/
│       │   ├── embedding/
│       │   └── main.py
│       ├── models/
│       └── tests/
├── packages/
│   └── contracts/
├── fixtures/
├── scripts/
├── docs/
├── compose.yaml
└── .env.example
```

Mã benchmark tại `COMPARE_FACE_DETECTION` được giữ độc lập. Trọng số RetinaFace và cấu hình đã kiểm tra có thể được sao chép hoặc gắn vào dịch vụ `vision`, nhưng không nhập cả thư mục benchmark vào mã ứng dụng.

## 5. Thứ tự triển khai

### Giai đoạn 0 – Khóa quy tắc trước khi viết mã

#### Việc cần làm

- Chốt danh sách bảy nhãn và đúng thứ tự đầu ra của mô hình Emotion.
- Chốt định dạng mã và thứ tự điểm chạm.
- Chốt quy tắc kết thúc một lượt ghé thăm khi khách hàng không xuất hiện trong một khoảng thời gian.
- Chuẩn bị tập ảnh đăng ký và tập ảnh truy vấn để xác định ngưỡng nhận dạng khách hàng.
- Chốt chính sách đồng ý sử dụng dữ liệu khuôn mặt và quyền được dùng chức năng tìm kiếm bằng ảnh.
- Chuẩn bị dữ liệu mẫu gồm khách hàng, đơn mua hàng, điểm chạm và các trường hợp ảnh lỗi.

#### Đầu ra bắt buộc

- `docs/decisions.md` ghi các quyết định đã khóa.
- `fixtures/` chứa dữ liệu mẫu không có thông tin cá nhân thật.
- Tệp cấu hình nhãn biểu cảm.
- Kịch bản hiệu chỉnh ngưỡng nhận dạng; chưa có ngưỡng thì chức năng nhận dạng cá nhân phải ở trạng thái tắt.

### Giai đoạn 1 – Khởi tạo dự án và môi trường chạy

#### Việc cần làm

- Tạo cấu trúc thư mục `SYSTEM`.
- Tạo ứng dụng FastAPI cho `api` và `vision`.
- Tạo ứng dụng React/TypeScript cho `web`.
- Tạo PostgreSQL có `pgvector`.
- Tạo `compose.yaml`, kiểm tra sức khỏe từng dịch vụ và `.env.example`.
- Thiết lập định dạng mã, kiểm tra kiểu dữ liệu và lệnh kiểm thử.
- Tạo quy trình kiểm tra tự động khi đẩy mã.

#### Điều kiện hoàn thành

- Một lệnh khởi động được toàn bộ môi trường.
- Ba dịch vụ trả trạng thái hoạt động.
- API kết nối được cơ sở dữ liệu.
- Các lệnh kiểm tra mã và kiểm thử chạy được dù chưa có nghiệp vụ.

### Giai đoạn 2 – Cơ sở dữ liệu và nền tảng máy chủ nghiệp vụ

#### Việc cần làm

- Khai báo các bảng người dùng, khách hàng, mẫu khuôn mặt, nhóm sản phẩm, sản phẩm, điểm chạm, lượt ghé thăm, quan sát, đơn hàng, chi tiết đơn hàng và nhật ký thao tác.
- Tạo migration đầu tiên và dữ liệu khởi tạo.
- Cài đặt đăng nhập, làm mới phiên đăng nhập và đăng xuất.
- Cài đặt ba vai trò: quản trị viên, quản lý và nhân viên.
- Tạo cơ chế trả lỗi thống nhất và mã theo dõi yêu cầu.

#### Điều kiện hoàn thành

- Có thể tạo mới cơ sở dữ liệu từ migration.
- Không lưu mật khẩu dạng rõ.
- Mỗi API được bảo vệ đúng vai trò.
- Kiểm thử xác nhận nhân viên không truy cập được chức năng quản trị.

### Giai đoạn 3 – Dịch vụ xử lý ảnh

#### Việc cần làm

- Bọc RetinaFace-MobileNet0.25 trong một giao diện phát hiện thống nhất.
- Kiểm tra ảnh đầu vào, số khuôn mặt và chất lượng vùng cắt.
- Căn chỉnh khuôn mặt bằng các điểm mốc do detector trả về.
- Tích hợp mô hình Emotion để trả bảy xác suất và nhãn cao nhất.
- Tích hợp ArcFace để trả véc-tơ đặc trưng 512 chiều đã chuẩn hóa.
- Trả tên và phiên bản của từng mô hình trong kết quả kỹ thuật.
- Không lưu ảnh đầu vào trong dịch vụ.

#### Kiểm thử bắt buộc

- Ảnh hỏng.
- Ảnh không có khuôn mặt.
- Ảnh có một khuôn mặt.
- Ảnh có nhiều khuôn mặt.
- Đầu ra Emotion đủ bảy lớp và tổng xác suất hợp lệ.
- Véc-tơ ArcFace đủ 512 phần tử, không có giá trị vô hạn hoặc không xác định.
- Hai lần xử lý cùng ảnh và cùng phiên bản mô hình cho đầu ra trong dung sai cho phép.

### Giai đoạn 4 – Chức năng CRM cơ bản

#### Việc cần làm

- API và giao diện danh sách khách hàng: tạo, xem, sửa trạng thái và tìm kiếm.
- Trang chi tiết khách hàng.
- API và giao diện quản lý nhóm sản phẩm.
- API và giao diện quản lý sản phẩm: tạo, sửa, ngừng kinh doanh, tìm kiếm và lọc theo nhóm.
- API và giao diện đơn hàng: tạo đơn, xem chi tiết và cập nhật trạng thái.
- Hiển thị lịch sử mua hàng trong hồ sơ khách hàng.
- Lọc lịch sử mua hàng theo khoảng thời gian và trạng thái.
- Hiển thị sản phẩm, số lượng, đơn giá tại thời điểm mua và thành tiền của từng đơn.
- API và giao diện quản lý điểm chạm và thứ tự điểm chạm.
- Phân trang, lọc, sắp xếp và kiểm tra dữ liệu nhập.
- Ghi nhật ký với thao tác xem hoặc thay đổi dữ liệu nhạy cảm.

#### Điều kiện hoàn thành

- Người dùng có thể hoàn thành các thao tác CRM từ giao diện, không cần gọi API thủ công.
- Không xóa cứng khách hàng đang có đơn hàng hoặc lượt ghé thăm.
- Không xóa cứng sản phẩm đã xuất hiện trong lịch sử mua hàng; chỉ chuyển sang trạng thái ngừng kinh doanh.
- Tổng tiền đơn hàng được tính và kiểm tra ở máy chủ.
- Việc thay đổi giá sản phẩm không làm thay đổi đơn giá đã lưu trong đơn hàng cũ.

### Giai đoạn 5 – Đăng ký và tìm kiếm khuôn mặt

#### Việc cần làm

- Tạo API tải ảnh đăng ký cho một khách hàng đã đồng ý.
- Gọi dịch vụ `vision`, nhận véc-tơ và lưu vào `pgvector`.
- Cho phép nhiều mẫu hợp lệ cho một khách hàng.
- Tạo API và giao diện tìm kiếm khách hàng bằng ảnh.
- Trả về danh sách ứng viên kèm khoảng cách; chỉ xác nhận một khách hàng khi đạt ngưỡng đã hiệu chỉnh.
- Tạo chức năng rút lại đồng ý và xóa các mẫu khuôn mặt liên quan.

#### Điều kiện hoàn thành

- Khách hàng chưa đồng ý không thể đăng ký mẫu khuôn mặt.
- Ảnh tìm kiếm chỉ được xử lý tạm thời và không được lưu.
- Thiếu tệp ngưỡng hiệu chỉnh thì API không được tự nhận dạng khách hàng.
- Mọi lần tìm kiếm bằng ảnh đều có nhật ký người thực hiện và thời gian.

### Giai đoạn 6 – Tiếp nhận bản ghi và hình thành lượt ghé thăm

#### Việc cần làm

- Tạo API nhận `event_id`, điểm chạm, thời gian và ảnh.
- Kiểm tra `event_id` để không xử lý trùng.
- Gọi dịch vụ `vision` một lần cho cả biểu cảm và véc-tơ nhận dạng.
- Đối sánh khách hàng trong cơ sở dữ liệu.
- Tạo hoặc lấy lượt ghé thăm đang hoạt động theo quy tắc đã khóa.
- Lưu bản ghi quan sát, trạng thái chất lượng và phiên bản mô hình.
- Khách hàng không xác định vẫn được lưu bản ghi thống kê tại điểm chạm nhưng không được gán vào hồ sơ cá nhân.
- Xử lý an toàn khi hai điểm chạm gửi dữ liệu cùng lúc cho một khách hàng.

#### Điều kiện hoàn thành

- Gửi lại cùng `event_id` không tạo bản ghi thứ hai.
- Hai khách hàng không bị gắn chung một lượt ghé thăm.
- Hai lượt đến khác nhau của cùng khách hàng không bị nhập làm một.
- Bản ghi đến muộn không âm thầm làm sai thứ tự hành trình.
- Có kiểm thử tích hợp từ ảnh đầu vào đến bản ghi trong cơ sở dữ liệu.

### Giai đoạn 7 – Phân tích đa điểm chạm

#### Việc cần làm

- API xem chuỗi bản ghi của một lượt ghé thăm theo thời gian.
- API thống kê số lượng và tỷ lệ bảy nhãn tại mỗi điểm chạm.
- API tạo bảng chéo nhãn trước–sau cho từng cặp điểm chạm liên tiếp.
- API thống kê tỷ lệ bản ghi không hợp lệ theo nguyên nhân.
- Bộ lọc theo điểm chạm và khoảng thời gian.
- Hiển thị biểu đồ cột cho phân bố và bản đồ nhiệt cho bảng thay đổi nhãn.
- Luôn hiển thị số mẫu cùng tỷ lệ.

#### Điều kiện hoàn thành

- Số liệu API đối chiếu đúng với truy vấn kiểm tra trên dữ liệu cố định.
- Không đưa bản ghi thiếu khách hàng vào phân tích hành trình cá nhân.
- Không tự điền nhãn cho điểm chạm bị thiếu.
- Không chuyển bảy nhãn thành điểm tích cực–tiêu cực.

### Giai đoạn 8 – Hoàn thiện giao diện CRM

#### Màn hình bắt buộc

- Đăng nhập.
- Tổng quan.
- Danh sách và chi tiết khách hàng.
- Đăng ký khuôn mặt.
- Tìm khách hàng bằng ảnh.
- Nhóm sản phẩm và danh sách sản phẩm.
- Danh sách và chi tiết đơn hàng.
- Lịch sử mua hàng trong hồ sơ khách hàng.
- Cửa hàng và điểm chạm.
- Danh sách và chi tiết lượt ghé thăm.
- Báo cáo theo điểm chạm.
- Báo cáo thay đổi giữa các điểm chạm.
- Chất lượng dữ liệu và lỗi xử lý ảnh.

#### Yêu cầu chung

- Có trạng thái đang tải, không có dữ liệu và lỗi.
- Không hiển thị kết quả nhận dạng như kết luận chắc chắn khi không đạt ngưỡng.
- Ảnh xem trước trên trình duyệt phải được giải phóng sau khi gửi.
- Các bảng có phân trang phía máy chủ.
- Các thao tác nhạy cảm yêu cầu xác nhận.

### Giai đoạn 9 – Xây dựng bộ dữ liệu và dịch vụ mô phỏng

#### Nguồn ảnh đã sử dụng

- Chọn đúng 100 ảnh từ tập kiểm tra FairFace để làm ảnh đại diện CRM.
- Lưu URL nguồn, giấy phép, chỉ số ảnh và mã kiểm tra trong manifest.
- Không dùng ảnh đại diện làm nhãn đúng cho FER hoặc bằng chứng nhận dạng khách hàng.

#### Cấu trúc bộ dữ liệu mô phỏng

```text
SYSTEM/fixtures/demo_dataset/
├── README.md
├── sources.json
├── customers.csv
├── product_categories.csv
├── products.csv
├── touchpoints.csv
├── journeys.csv
├── events.csv
├── orders.csv
├── order_items.csv
├── enrollment/
├── observations/
└── expected/
```

#### Việc cần làm

- Viết chương trình kiểm tra giấy phép, cấu trúc và mã kiểm tra của tệp dữ liệu nguồn.
- Chọn các mã người cố định để kết quả có thể lặp lại.
- Tách người dùng cho hiệu chỉnh ngưỡng và người dùng cho demo; không dùng ảnh demo để chọn ngưỡng.
- Tạo đúng 100 khách hàng mô phỏng, không dùng tên hoặc thông tin thật của người trong ảnh.
- Tạo bốn điểm chạm, 24 sản phẩm, đơn hàng và lịch sử mua hàng mô phỏng.
- Tạo có kiểm soát trường hợp không có khuôn mặt và ảnh hỏng.
- Gửi các sự kiện theo lô vào API nghiệp vụ và đánh dấu nguồn mô phỏng.
- Dùng hạt giống cố định để tái lập hành trình, nhãn và đơn hàng.
- Chụp ảnh giao diện sau khi kiểm tra số liệu trong PostgreSQL.

#### Nguyên tắc dữ liệu

- Nhãn trong demo do dịch vụ mô phỏng tạo và phải được ghi rõ trên giao diện, báo cáo.
- Không dùng kết quả demo làm kết luận về độ chính xác của mô hình.
- Mọi ảnh dẫn xuất phải truy ngược được tới mã người, tên tệp nguồn, URL và giấy phép.
- Phép biến đổi ảnh phải được ghi trong tệp manifest và dùng hạt giống cố định.
- Không tuyên bố đã nhận dạng khách hàng thật nếu chưa có ngưỡng được hiệu chỉnh độc lập.

#### Điều kiện hoàn thành

- Có thể tạo lại đúng 100 ảnh đại diện và dữ liệu CRM bằng lệnh trong Makefile.
- Có thể xóa dữ liệu demo và chạy lại mà không sửa mã.
- Dịch vụ mô phỏng gửi dữ liệu qua API nghiệp vụ, không ghi trực tiếp vào cơ sở dữ liệu.
- Có khách quay lại, hành trình thiếu điểm chạm, ảnh không có mặt và ảnh hỏng.
- Bộ dữ liệu có sản phẩm, đơn hàng và lịch sử mua hàng liên kết với khách hàng mô phỏng.
- Kết quả đối chiếu được ghi thành tệp JSON để kiểm tra lại.

Kịch bản chi tiết nằm tại `SYSTEM_DEVELOPMENT/DEMO_SCENARIO.md`.

### Giai đoạn 10 – Kiểm thử toàn hệ thống

#### Việc cần làm

- Kiểm thử đơn vị cho quy tắc nghiệp vụ.
- Kiểm thử tích hợp API với PostgreSQL thật trong vùng kiểm thử.
- Kiểm thử hợp đồng giữa `api` và `vision`.
- Kiểm thử từ giao diện đến API cho các luồng chính.
- Kiểm thử quyền truy cập.
- Kiểm thử yêu cầu đồng thời khi tạo lượt ghé thăm.
- Đo thời gian xử lý ảnh, thời gian tìm kiếm véc-tơ và thời gian tải báo cáo.
- Kiểm tra dữ liệu nhạy cảm không xuất hiện trong nhật ký.

#### Bộ tình huống chấp nhận

1. Tạo khách hàng, ghi nhận đồng ý, đăng ký mẫu khuôn mặt và tìm lại bằng ảnh.
2. Cùng khách hàng đi qua nhiều điểm chạm và tạo đúng một lượt ghé thăm.
3. Cùng khách hàng quay lại sau khoảng ngắt và tạo lượt mới.
4. Khách hàng không xác định chỉ xuất hiện trong thống kê tại điểm chạm.
5. Ảnh nhiều khuôn mặt không bị gắn nhầm vào khách hàng.
6. Đơn mua hàng hiển thị đúng trong hồ sơ khách hàng.
7. Tạo sản phẩm, đưa sản phẩm vào đơn hàng và xem lại đúng trong lịch sử mua hàng.
8. Thay đổi giá sản phẩm không làm thay đổi giá trong đơn hàng cũ.
9. Rút lại đồng ý làm mất khả năng tìm kiếm bằng khuôn mặt của khách hàng đó.

### Giai đoạn 11 – Khóa đầu ra triển khai

Chỉ sau khi các giai đoạn trên hoàn thành mới tạo bộ đầu ra để dùng khi viết báo cáo:

- Phiên bản mã nguồn và tệp khóa phụ thuộc.
- Sơ đồ cơ sở dữ liệu được sinh từ schema thật.
- Tài liệu OpenAPI được sinh từ API thật.
- Ảnh giao diện của hệ thống đang chạy.
- Kết quả kiểm thử.
- Kết quả đo thời gian xử lý.
- Dữ liệu và truy vấn dùng để tạo biểu đồ.
- Danh sách giới hạn còn tồn tại.

Không viết trước kết quả, số liệu hoặc mô tả chức năng chưa được triển khai.

### Danh sách công việc để đưa vào bảng theo dõi

| Mã | Công việc | Phụ thuộc | Đầu ra chính |
|---|---|---|---|
| `INF-01` | Khởi tạo cấu trúc `SYSTEM` | Giai đoạn 0 | Cấu trúc thư mục và hướng dẫn chạy |
| `INF-02` | Tạo PostgreSQL có `pgvector` | `INF-01` | Dịch vụ cơ sở dữ liệu hoạt động |
| `INF-03` | Tạo Docker Compose và kiểm tra sức khỏe | `INF-01`, `INF-02` | Một lệnh khởi động toàn hệ thống |
| `INF-04` | Thiết lập kiểm tra mã và kiểm thử tự động | `INF-01` | Quy trình kiểm tra đạt |
| `DB-01` | Tạo bảng người dùng và phân quyền | `INF-02` | Migration và dữ liệu quản trị ban đầu |
| `DB-02` | Tạo bảng khách hàng và mẫu khuôn mặt | `INF-02` | Migration có cột `vector(512)` |
| `DB-03` | Tạo bảng điểm chạm | `INF-02` | Migration và ràng buộc mã/thứ tự |
| `DB-04` | Tạo bảng lượt ghé thăm và quan sát | `DB-02`, `DB-03` | Migration và chỉ mục lượt đang hoạt động |
| `DB-05` | Tạo bảng nhóm sản phẩm và sản phẩm | `INF-02` | Migration, mã sản phẩm và trạng thái |
| `DB-06` | Tạo bảng đơn hàng, chi tiết đơn và nhật ký | `DB-01`, `DB-02`, `DB-05` | Migration và ràng buộc tổng tiền |
| `BE-01` | Xác thực, cookie và chống giả mạo yêu cầu | `DB-01` | API đăng nhập/đăng xuất/làm mới |
| `BE-02` | Phân quyền tại API | `BE-01` | Kiểm thử ma trận quyền |
| `BE-03` | API khách hàng | `DB-02`, `BE-02` | CRUD, tìm kiếm và phân trang |
| `BE-04` | API nhóm sản phẩm và sản phẩm | `DB-05`, `BE-02` | CRUD, tìm kiếm, lọc và ngừng kinh doanh |
| `BE-05` | API đơn hàng và lịch sử mua hàng | `DB-06`, `BE-03`, `BE-04` | Tạo đơn, chi tiết đơn và lịch sử theo khách hàng |
| `BE-06` | API điểm chạm | `DB-03`, `BE-02` | CRUD và kiểm tra thứ tự |
| `VIS-01` | Nạp RetinaFace và kiểm tra trọng số | `INF-01` | Detector trả khung và điểm mốc |
| `VIS-02` | Cắt và căn chỉnh khuôn mặt | `VIS-01` | Ảnh khuôn mặt chuẩn hóa |
| `VIS-03` | Tích hợp mô hình Emotion | `VIS-02` | Bảy xác suất và nhãn |
| `VIS-04` | Tích hợp ArcFace | `VIS-02` | Véc-tơ 512 chiều |
| `VIS-05` | API nội bộ `analyze-face` | `VIS-03`, `VIS-04` | Hợp đồng API và kiểm thử |
| `REC-01` | Công cụ hiệu chỉnh ngưỡng nhận dạng | `VIS-04` | Tệp ngưỡng có phiên bản |
| `REC-02` | Đăng ký và xóa mẫu khuôn mặt | `BE-03`, `VIS-05` | API mẫu khuôn mặt |
| `REC-03` | Tìm khách hàng bằng ảnh | `REC-01`, `REC-02` | API tìm kiếm và nhật ký |
| `JRN-01` | API tiếp nhận quan sát | `DB-04`, `BE-06`, `VIS-05` | Lưu đủ trạng thái xử lý |
| `JRN-02` | Đối sánh khách hàng khi tiếp nhận | `JRN-01`, `REC-03` | `customer_id` hoặc trạng thái không khớp |
| `JRN-03` | Tạo/đóng lượt ghé thăm | `JRN-02` | Quy tắc lượt và kiểm thử đồng thời |
| `JRN-04` | API danh sách/chi tiết lượt | `JRN-03` | Chuỗi điểm chạm theo thời gian |
| `RPT-01` | Truy vấn phân bố biểu cảm | `JRN-01` | API số lượng và tỷ lệ |
| `RPT-02` | Truy vấn thay đổi nhãn | `JRN-03` | API bảng chéo trước–sau |
| `RPT-03` | Truy vấn chất lượng dữ liệu | `JRN-01` | API thống kê lỗi và dữ liệu thiếu |
| `FE-01` | Khung ứng dụng, đăng nhập và điều hướng | `BE-01` | Giao diện có bảo vệ tuyến trang |
| `FE-02` | Khách hàng và lịch sử mua hàng | `BE-03`, `BE-05`, `FE-01` | Hồ sơ khách hàng và lịch sử đơn hàng |
| `FE-03` | Đăng ký/tìm kiếm khuôn mặt | `REC-02`, `REC-03`, `FE-01` | Hai luồng tải ảnh hoàn chỉnh |
| `FE-04` | Nhóm sản phẩm, sản phẩm và đơn hàng | `BE-04`, `BE-05`, `FE-01` | Các trang quản lý sản phẩm và mua hàng |
| `FE-05` | Cửa hàng và điểm chạm | `BE-06`, `FE-01` | Trang cấu hình điểm chạm |
| `FE-06` | Lượt ghé thăm | `JRN-04`, `FE-01` | Danh sách và dòng thời gian |
| `FE-07` | Báo cáo đa điểm chạm | `RPT-01`, `RPT-02`, `RPT-03` | Biểu đồ, bảng chéo và bộ lọc |
| `DATA-01` | Tạo danh mục nguồn và chương trình nhập dữ liệu | `INF-01` | `sources.json` và dữ liệu nguồn đã kiểm tra |
| `DATA-02` | Tạo ảnh đăng ký và ảnh điểm chạm | `DATA-01` | Bộ ảnh dẫn xuất có manifest |
| `DATA-03` | Tạo dữ liệu CRM mô phỏng | `DB-03`, `DB-05`, `DB-06` | Khách hàng, sản phẩm, điểm chạm và đơn hàng |
| `DATA-04` | Viết chương trình mô phỏng camera | `DATA-02`, `JRN-01` | Công cụ phát lại sự kiện qua API |
| `DATA-05` | Viết chương trình đối chiếu demo | `DATA-03`, `DATA-04`, `JRN-04` | Tệp kết quả đối chiếu JSON |
| `QA-01` | Kiểm thử luồng nghiệp vụ chính | Các mục BE/VIS/REC/JRN và `DATA-05` | Bộ kiểm thử tích hợp |
| `QA-02` | Kiểm thử giao diện đầu cuối | `FE-07`, `QA-01` | Bộ kiểm thử Playwright |
| `QA-03` | Đo hiệu năng và khóa đầu ra | `QA-02` | Kết quả đo và phiên bản mã nguồn |

## 6. Thứ tự ưu tiên

### Bắt buộc cho phiên bản đầu

- Đăng nhập và phân quyền.
- Khách hàng và lịch sử mua hàng.
- Nhóm sản phẩm, sản phẩm và đơn hàng.
- Điểm chạm.
- Đăng ký/tìm kiếm khuôn mặt.
- Tiếp nhận ảnh và phân loại biểu cảm.
- Lượt ghé thăm.
- Hai báo cáo đa điểm chạm.
- Nhật ký thao tác nhạy cảm.

### Chỉ làm sau khi phiên bản đầu ổn định

- Nhập danh sách khách hàng/đơn hàng từ tệp.
- Nhận dữ liệu từ camera theo thời gian thực.
- Hàng đợi xử lý nền.
- Thông báo tự động.
- Tối ưu chỉ mục véc-tơ cho dữ liệu rất lớn.

## 7. Quy tắc quản lý công việc

- Mỗi công việc phải có mã, phụ thuộc, đầu ra và kiểm thử chấp nhận.
- Không gộp thay đổi cơ sở dữ liệu, xử lý ảnh và giao diện lớn trong cùng một nhánh mã.
- Thay đổi cấu trúc API phải cập nhật hợp đồng và kiểm thử trước khi sửa giao diện.
- Mọi migration đã dùng chung không được sửa nội dung; phải tạo migration mới.
- Mọi ngưỡng nhận dạng phải đến từ tệp hiệu chỉnh có thông tin dữ liệu và phiên bản mô hình.
- Không đưa ảnh khuôn mặt thật, mật khẩu hoặc khóa bí mật vào kho mã.
- Một hạng mục chỉ được đánh dấu hoàn thành khi mã, kiểm thử và hướng dẫn chạy cùng tồn tại.

## 8. Tiêu chí hoàn thành toàn bộ phần coding

Phần triển khai được xem là hoàn thành khi:

1. Có thể khởi động hệ thống từ một máy mới theo hướng dẫn.
2. Tất cả migration chạy từ cơ sở dữ liệu trống.
3. Các luồng chấp nhận ở Giai đoạn 10 đều đạt.
4. Không còn API giao diện đang dùng dữ liệu giả.
5. Báo cáo trên giao diện được tính từ dữ liệu trong PostgreSQL.
6. Chức năng nhận dạng bị từ chối an toàn khi thiếu ngưỡng hoặc mô hình.
7. Kiểm thử tự động đạt và kết quả đo được lưu lại.
8. Tài liệu kỹ thuật phản ánh đúng mã nguồn tại phiên bản đã khóa.
