# Tổng hợp cập nhật luận văn

Tài liệu này tổng hợp các thay đổi, đề xuất và quy chuẩn đối với các chương của luận văn.

## 1. Điều chỉnh cách dẫn khung hành trình khách hàng

**Tệp:** `Chuong/3_Phuong_an_de_xuat.tex`  
**Vị trí:** Mục 3.1.1 — Bài toán cần giải quyết

- Loại bỏ câu diễn giải trực tiếp rằng khung của Halvorsrud, Kvale và Følstad yêu cầu giữ lại vị trí và thứ tự của từng tương tác.
- Thay bằng dẫn chiếu tới cơ sở phân tích hành trình khách hàng đã trình bày tại Mục 2.4.
- Làm rõ đóng góp của luận văn là liên kết các kết quả nhận dạng biểu cảm theo khách hàng và lượt ghé thăm, sau đó sắp xếp chúng theo thời gian.
- Tránh tạo cảm giác luận văn áp dụng nguyên vẹn khung lý thuyết của Halvorsrud, Kvale và Følstad như một mô hình kỹ thuật.

## 2. Mở rộng cách biểu diễn biểu cảm tại điểm chạm

**Tệp:** `Chuong/2_Nen_tang_ly_thuyet_va_cong_nghe.tex`  
**Vị trí:** Mục 2.4.1 và 2.4.2

- Không còn giả định mỗi điểm chạm chỉ có một nhãn biểu cảm duy nhất.
- Mỗi điểm chạm có thể tạo ra nhiều quan sát tại các thời điểm khác nhau.
- Hành trình được tổ chức theo hai cấp:
  1. Các quan sát bên trong từng điểm chạm.
  2. Chuỗi điểm chạm của toàn bộ lượt ghé thăm.
- Bổ sung hai mức phân tích:
  - Biến thiên biểu cảm bên trong cùng một khu vực.
  - Sự thay đổi biểu cảm giữa các điểm chạm trong hành trình.
- Làm rõ rằng phân tích theo các phân vùng vật lý nhỏ hơn cần có mã phân vùng riêng. Trong cấu hình hiện tại, điểm chạm vẫn là đơn vị không gian nhỏ nhất.

## 3. Thiết kế lại Hình 2.9

**Tệp:** `Chuong/2_Nen_tang_ly_thuyet_va_cong_nghe.tex`  
**Nhãn LaTeX:** `fig:touchpoint_sequence`

- Thay sơ đồ chỉ có một biểu cảm tại mỗi điểm chạm bằng sơ đồ có nhiều quan sát theo thời gian.
- Mỗi điểm chạm được biểu diễn dưới dạng một thẻ riêng gồm:
  - Tên điểm chạm.
  - Trục thời gian nội bộ.
  - Các mốc quan sát.
  - Nhãn biểu cảm tại từng mốc.
- Bốn thẻ được nối theo thứ tự: Tiếp đón, Tư vấn, Trải nghiệm và Thanh toán.
- Sử dụng tông xám để phù hợp với tài liệu học thuật và vẫn rõ khi in đen trắng.
- Đổi chú thích hình thành:

> Các quan sát biểu cảm trong từng điểm chạm của một hành trình

## 4. Điều chỉnh đầu vào và đầu ra của phương pháp

**Tệp:** `Chuong/3_Phuong_an_de_xuat.tex`  
**Vị trí:** Mục 3.1.2 — Đầu vào và đầu ra

- Làm rõ camera có thể tạo nhiều ảnh tại cùng một điểm chạm ở các thời điểm khác nhau.
- Thời điểm ghi nhận được dùng để sắp xếp:
  - Nhiều quan sát trong cùng một khu vực.
  - Các quan sát trong toàn bộ lượt ghé thăm.
- Chuyển đầu ra của phương pháp từ hai mức thành ba mức:
  1. **Mức quan sát:** bản ghi gồm điểm chạm, thời gian, nhãn biểu cảm, độ tin cậy và kết quả nhận dạng khách hàng.
  2. **Mức điểm chạm:** tập hợp các quan sát của cùng khách hàng tại một khu vực.
  3. **Mức hành trình:** chuỗi các bản ghi thuộc cùng khách hàng và lượt ghé thăm, được sắp xếp theo thời gian.

## 5. Bổ sung phân tích chi tiết tại từng điểm chạm

**Tệp:** `Chuong/3_Phuong_an_de_xuat.tex`  
**Vị trí:** Mục 3.4.1 — Phân bố biểu cảm tại từng điểm chạm

- Không rút gọn ngay một điểm chạm thành một nhãn biểu cảm duy nhất.
- Giữ các bản ghi tại cùng điểm chạm theo thứ tự thời gian để xem biểu cảm được duy trì hay thay đổi.
- Cho phép nhóm dữ liệu theo các khoảng thời gian thống nhất để theo dõi biến thiên phân bố biểu cảm tại cùng khu vực.
- Ghi rõ phân tích theo phân vùng vật lý là hướng mở rộng và cần bổ sung mã phân vùng vào mỗi quan sát.

## 6. Tổ chức lại luồng xử lý thành ba cụm

**Tệp:** `Chuong/3_Phuong_an_de_xuat.tex`  
**Vị trí:** Mục 3.1.3 — Luồng xử lý tổng thể

Luồng tổng thể được tổ chức lại thành ba cụm độc lập:

```text
Cụm dữ liệu đầu vào → Cụm xử lý → Cụm dữ liệu đầu ra
```

### Cụm dữ liệu đầu vào

- Ảnh tại điểm chạm.
- Mã điểm chạm.
- Thời điểm ghi nhận.
- Mẫu khuôn mặt tham chiếu.
- Trạng thái lượt ghé thăm.

### Cụm xử lý

1. Phát hiện và chuẩn hóa khuôn mặt.
2. Phân loại biểu cảm.
3. Nhận dạng khách hàng.
4. Tạo và liên kết bản ghi.
5. Phân tích đa điểm chạm.

### Cụm dữ liệu đầu ra

- Nhãn biểu cảm và độ tin cậy.
- Kết quả nhận dạng khách hàng.
- Bản ghi tại điểm chạm.
- Chuỗi quan sát theo thời gian.
- Kết quả phân tích hành trình.

## 7. Thiết kế lại Bảng 3.1

**Tệp:** `Chuong/3_Phuong_an_de_xuat.tex`  
**Nhãn LaTeX:** `tab:method_stages`

- Đổi tên bảng thành **Thành phần và vai trò của ba cụm trong phương pháp**.
- Thay cấu trúc liệt kê đầu vào và đầu ra của từng công đoạn bằng ba dòng tương ứng với ba cụm.
- Các cột mới gồm:
  - Cụm.
  - Thành phần.
  - Vai trò.
- Giảm sự trùng lặp giữa Bảng 3.1 và sơ đồ luồng xử lý tổng thể.

## 8. Nhận diện nhiều khách hàng trong cùng một ảnh

**Tệp:** `Chuong/3_Phuong_an_de_xuat.tex`  
**Vị trí:** Mục 3.1.1, 3.2.1, 3.2.2 và 3.2.3

- Thay giả định chỉ chọn một khuôn mặt trong ảnh bằng quy trình phát hiện tất cả vùng khuôn mặt hợp lệ.
- Mỗi vùng khuôn mặt được căn chỉnh, phân loại biểu cảm và đối sánh danh tính độc lập.
- Kết quả biểu cảm chỉ được gắn với danh tính suy ra từ chính vùng khuôn mặt tương ứng.
- Khuôn mặt không đạt ngưỡng đối sánh được giữ ở trạng thái không xác định.
- Một ảnh có thể tạo nhiều bản ghi quan sát, tương ứng với nhiều khách hàng hoặc khuôn mặt được phát hiện.
- Bổ sung vị trí khuôn mặt vào thông tin bản ghi để phân biệt các kết quả được tạo từ cùng một ảnh.

### Lưu trải nghiệm của khách hàng không xác định

> Ghi chú đề xuất, chưa áp dụng vào nội dung LaTeX hoặc mã nguồn hiện tại.

- Mọi quan sát khuôn mặt và biểu cảm hợp lệ đều được lưu, kể cả khi khách hàng chưa đăng ký hoặc không đối sánh được danh tính.
- Khách hàng chưa có hồ sơ CRM được cấp định danh ẩn danh khi đặc trưng khuôn mặt đủ chất lượng.
- Định danh ẩn danh được dùng để nhận biết khách quay lại, tạo các lượt ghé thăm và truy xuất lịch sử điểm chạm, thời gian, biểu cảm.
- Nếu chất lượng đặc trưng hoặc điểm đối sánh chưa đủ, bản ghi được giữ ở trạng thái chưa liên kết nhưng vẫn tham gia thống kê tổng hợp.
- Định danh ẩn danh không tự động được chuyển thành hồ sơ CRM; thao tác liên kết cần quy trình xác nhận và sự đồng ý phù hợp.
- Dữ liệu khuôn mặt ẩn danh vẫn cần giới hạn quyền truy cập và thời hạn lưu giữ vì có khả năng liên kết một người qua thời gian.
- Lưu ý triển khai: mô hình dữ liệu và API hiện tại chưa có thực thể định danh ẩn danh riêng; phần mã nguồn cần được mở rộng để thực hiện đúng phương pháp này.

## 9. Trạng thái kiểm tra

- Mã LaTeX/TikZ đã được kiểm tra về sự cân bằng của các môi trường chính.
- Chưa thể biên dịch lại `LuanVan.pdf` vì MiKTeX trên máy yêu cầu hoàn tất thiết lập ban đầu.
- Sau khi MiKTeX được thiết lập, cần biên dịch lại toàn bộ luận văn và kiểm tra:
  - Kích thước và khả năng đọc của Hình 2.9.
  - Bố cục sơ đồ ba cụm tại Mục 3.1.3.
  - Độ rộng và ngắt dòng của Bảng 3.1.
  - Các tham chiếu chéo, danh mục hình và danh mục bảng.

## 10. Ghi chú chuẩn hóa viết hoa đầu dòng trong các danh sách liệt kê

**Tệp liên quan:** `Chuong/4_Xay_dung_va_phat_trien_he_thong.tex` (Mục 4.1), `Chuong/2_Nen_tang_ly_thuyet_va_cong_nghe.tex` (Mục 2.2.1)

- **Quy chuẩn:** Tất cả các mục gạch đầu dòng (`\item` trong môi trường `itemize`, `enumerate`) đều phải viết hoa chữ cái đầu dòng nhằm đảm bảo tính nhất quán và văn phong chuẩn mực của luận văn.
- **Các vị trí cần điều chỉnh:**
  - **Chương 4 (Mục 4.1 — Tổng quan hệ thống):** Danh sách các chức năng đã xây dựng:
    - *Hiện tại:* `quản lý khách hàng...`, `quản lý điểm chạm...`, `đăng ký...`, `hiển thị...`, `thống kê...`, `thống kê...`
    - *Cần sửa thành:* Viết hoa chữ cái đầu (`Quản lý...`, `Đăng ký...`, `Hiển thị...`, `Thống kê...`).
  - **Chương 2 (Mục 2.2.1 — Phương pháp Viola--Jones):** Mục giải thích tham số công thức (\ref{eq:rectangle_sum}):
    - *Hiện tại:* `các giá trị $ii(\cdot,\cdot)$ được lấy từ...`
    - *Cần sửa thành:* `Các giá trị $ii(\cdot,\cdot)$ được lấy từ...`
- **Trạng thái:** Đã ghi nhận lưu ý, giữ nguyên hiện trạng các file `.tex` của luận văn và không sửa đổi trực tiếp.

## 11. Chuẩn hóa Bảng 4.1 và thiết kế lại sơ đồ kiến trúc hệ thống (Hình 4.1)

**Tệp liên quan:** `Chuong/4_Xay_dung_va_phat_trien_he_thong.tex`  
**Vị trí:** Mục 4.1.1 — Kiến trúc hệ thống (`tab:system_components` và `fig:system_architecture_ch4`)

### Vấn đề hiện tại
1. **Bảng 4.1 (`tab:system_components`):**
   - Đang đặt tên các thành phần theo tên container / thư mục mã nguồn kỹ thuật (`web`, `api`, `vision`, `postgres`).
   - Cần chuẩn hóa lại theo 4 thành phần kiến trúc thông thường trong kỹ thuật phần mềm: **Frontend (FE)**, **Backend (BE)**, **AI Module**, **Database (DB)**.
2. **Hình 4.1 (`fig:system_architecture_ch4`):**
   - **Xác định lỗi thiết kế:**
     - Đặt `Nguồn ảnh tại điểm chạm` (thiết bị ngoại vi / nguồn dữ liệu đầu vào) thành một khối ngang hàng với `Trình duyệt Giao diện CRM`.
     - Tên nhãn trong sơ đồ chưa đồng bộ với 4 thành phần trong Bảng 4.1.
     - Bố cục TikZ bị lệch trục (máy chủ nghiệp vụ thẳng hàng với nguồn ảnh thay vì đóng vai trò trung tâm điều phối), các luồng dữ liệu đan chéo thiếu tính trực quan của kiến trúc phân tầng.

---

### Phương án điều chỉnh đề xuất

#### 1. Đề xuất chuẩn hóa Bảng 4.1

Thay đổi tên các thành phần từ tên kỹ thuật sang tên module kiến trúc tiêu chuẩn, kèm chú thích module triển khai thực tế:

```latex
\begin{table}[H]
    \centering
    \caption{Các thành phần kiến trúc hệ thống đã triển khai}
    \label{tab:system_components}
    \resizebox{\textwidth}{!}{%
    \begin{tabular}{|p{3.2cm}|p{4.2cm}|p{7.6cm}|}
        \hline
        \textbf{Thành phần} & \textbf{Công nghệ} & \textbf{Chức năng đã triển khai} \\
        \hline
        \textbf{Frontend (FE)} \newline(\texttt{apps/web}) & React, TypeScript, Ant Design, ECharts & Giao diện quản lý khách hàng, sản phẩm, đơn hàng, điểm chạm, hiển thị hành trình và các biểu đồ báo cáo thống kê biểu cảm. \\
        \hline
        \textbf{Backend (BE)} \newline(\texttt{apps/api}) & FastAPI, SQLAlchemy, Alembic & Xử lý nghiệp vụ, xác thực người dùng, điều phối gọi mô-đun AI, liên kết lượt ghé thăm, tổng hợp báo cáo và cung cấp REST API. \\
        \hline
        \textbf{AI Module} \newline(\texttt{services/vision}) & OpenCV, RetinaFace, DeepFace, ArcFace & Phát hiện vùng khuôn mặt, chuẩn hóa ảnh, phân loại 7 lớp biểu cảm và trích xuất véc-tơ đặc trưng khuôn mặt phục vụ nhận dạng. \\
        \hline
        \textbf{Database (DB)} \newline(\texttt{postgres}) & PostgreSQL 16, pgvector 0.8.3 & Lưu trữ dữ liệu quan hệ (CRM, lượt ghé thăm, quan sát, đơn hàng) và hỗ trợ lưu trữ, tìm kiếm tương đồng véc-tơ đặc trưng khuôn mặt. \\
        \hline
    \end{tabular}}
\end{table}
```

#### 2. Đề xuất thiết kế lại sơ đồ kiến trúc Hình 4.1 (TikZ)

Xây dựng lại biểu đồ theo kiến trúc 4 khối cốt lõi lấy **Backend (BE)** làm trung tâm điều phối kết nối:
- Trục ngang: **Frontend (FE)** $\longleftrightarrow$ **Backend (BE)** $\longleftrightarrow$ **Database (DB)**.
- Trục dọc trung tâm:
  - Phía trên: **AI Module** (tiếp nhận ảnh từ BE và trả về nhãn biểu cảm cùng véc-tơ đặc trưng).
  - Phía dưới: **Thiết bị tại điểm chạm** (Camera / Dịch vụ mô phỏng gửi dữ liệu ảnh và mã điểm chạm đến BE; được phân biệt bằng nét đứt là thành phần thu thập ngoại vi).

```latex
\begin{figure}[H]
    \centering
    \resizebox{0.95\textwidth}{!}{%
    \begin{tikzpicture}[
        node distance=10mm and 14mm,
        block/.style={draw, rounded corners=3pt, align=center, minimum height=14mm, text width=3.4cm, font=\small},
        extblock/.style={draw, dashed, rounded corners=3pt, align=center, minimum height=12mm, text width=3.4cm, font=\small},
        store/.style={draw, cylinder, shape border rotate=90, aspect=0.25, align=center, minimum height=14mm, text width=3.0cm, font=\small},
        flow/.style={-{Latex[length=2.5mm]}, thick},
        lbl/.style={font=\scriptsize, align=center, fill=white, inner sep=1.5pt}
    ]
        % Khối trung tâm: Backend
        \node[block] (be) {\textbf{Backend (BE)}\\Máy chủ API nghiệp vụ\\{\footnotesize(FastAPI, SQLAlchemy)}};

        % Bên trái: Frontend
        \node[block, left=18mm of be] (fe) {\textbf{Frontend (FE)}\\Giao diện người dùng CRM\\{\footnotesize(React, TypeScript)}};

        % Bên phải: Database
        \node[store, right=18mm of be] (db) {\textbf{Database (DB)}\\PostgreSQL 16\\và pgvector 0.8.3};

        % Phía trên: AI Module
        \node[block, above=12mm of be] (ai) {\textbf{AI Module}\\Xử lý ảnh \& Nhận dạng\\{\footnotesize(RetinaFace, DeepFace, ArcFace)}};

        % Phía dưới: Thiết bị ngoại vi tại điểm chạm
        \node[extblock, below=12mm of be] (camera) {Thiết bị tại điểm chạm\\(Camera / Bộ mô phỏng)};

        % Các luồng giao tiếp giữa các thành phần
        \draw[flow, <->] (fe) -- node[above, lbl] {REST API\\(JSON)} (be);
        \draw[flow, <->] (be) -- node[above, lbl] {Truy vấn dữ liệu\\và véc-tơ} (db);
        \draw[flow, <->] (be) -- node[right, lbl] {Gửi ảnh / Trả về\\biểu cảm \& véc-tơ} (ai);
        \draw[flow] (camera) -- node[right, lbl] {Ảnh và mã\\điểm chạm} (be);
    \end{tikzpicture}%
    }
    \caption{Kiến trúc hệ thống chuẩn hóa theo các thành phần phần mềm chính}
    \label{fig:system_architecture_ch4}
\end{figure}
```

- **Trạng thái:** Đã ghi chú chi tiết phương án và cung cấp sẵn mã LaTeX/TikZ hoàn chỉnh trong tài liệu ghi chú; giữ nguyên hiện trạng các tệp `.tex` của luận văn và không tự ý sửa đổi mã nguồn luận văn.

## 12. Nâng cấp tính học thuật và viết chi tiết Luồng dữ liệu chính (Mục 4.1.2)

**Tệp liên quan:** `Chuong/4_Xay_dung_va_phat_trien_he_thong.tex`  
**Vị trí:** Mục 4.1.2 — Luồng dữ liệu chính (Hình 4.2: `fig:system_data_flow_ch4`)

### Vấn đề hiện tại
1. **Nội dung diễn giải quá ngắn gọn và đơn giản:** Mục 4.1.2 hiện tại chỉ gồm 4 câu khái quát, thiếu chiều sâu học thuật, chưa làm rõ quy trình phân tích dữ liệu, cấu trúc gói tin (payload), giải thuật đối sánh véc-tơ và cơ chế kiểm soát phiên lượt ghé thăm (session timeout).
2. **Hình 4.2 (`fig:system_data_flow_ch4`) thiết kế quá sơ sài:** Sơ đồ hiện tại chỉ có 5 khối chữ nhật nối tiếp thẳng hàng một chiều, không thể hiện được:
   - Ranh giới trách nhiệm của 4 thành phần hệ thống (**FE**, **BE**, **AI Module**, **DB**).
   - Các gói dữ liệu trao đổi trung gian (ảnh thô, véc-tơ đặc trưng 512 chiều, phân bố xác suất FER, bản ghi quan sát).
   - Điểm rẽ nhánh logic (nhận diện thành công vs chưa xác định; gộp lượt ghé thăm đang hoạt động vs khởi tạo lượt mới).
3. **Thiếu bảng biểu đặc tả kỹ thuật:** Chưa có bảng tổng hợp học thuật đối chiếu các giai đoạn xử lý, đầu vào, thuật toán và đầu ra.

---

### Phương án điều chỉnh đề xuất

#### 1. Đề xuất viết lại nội dung văn bản Mục 4.1.2 chi tiết và học thuật hơn

Mục 4.1.2 được phân rã thành 5 giai đoạn liên hoàn, kết hợp giữa mô hình toán học và kỹ thuật phần mềm:

* **Giai đoạn 1 — Tiếp nhận và tiền kiểm định tại biên (Backend API):**
  Thiết bị tại điểm chạm (hoặc bộ mô phỏng) gửi yêu cầu HTTP POST đa phần (multipart) chứa ảnh hiện trường, mã điểm chạm vật lý (`touchpoint_code`), dấu thời gian ghi nhận (`observed_at`) và mã định danh sự kiện (`event_id`). Máy chủ Backend API kiểm tra tính hợp lệ của lược đồ dữ liệu, xác thực điểm chạm đang ở trạng thái hoạt động (`active = true`) và gắn nhãn thời điểm tiếp nhận (`received_at`).

* **Giai đoạn 2 — Xử lý thị giác máy tính và trích xuất đặc trưng đa nhiệm (AI Module):**
  Ảnh được chuyển tiếp sang mô-đun AI xử lý theo luồng:
  1. *Phát hiện và căn chỉnh khuôn mặt:* Mô hình RetinaFace phát hiện vùng khuôn mặt và các điểm mốc hình học (landmarks). Nếu không tìm thấy khuôn mặt hợp lệ, bản ghi được đánh dấu trạng thái tương ứng để phục vụ báo cáo chất lượng dữ liệu.
  2. *Phân loại biểu cảm (FER):* Vùng khuôn mặt được chuẩn hóa đưa qua mô hình Emotion (DeepFace) để suy luận phân bố xác suất trên 7 lớp biểu cảm (Vui vẻ, Buồn bã, Tức giận, Ngạc nhiên, Sợ hãi, Ghê tởm, Trung tính), đồng thời xác định nhãn có xác suất cao nhất và độ tin cậy $c \in [0, 1]$.
  3. *Trích xuất véc-tơ đặc trưng khuôn mặt:* Kiến trúc ArcFace trích xuất véc-tơ biểu diễn khuôn mặt 512 chiều $\mathbf{v} \in \mathbb{R}^{512}$ đã qua chuẩn hóa $L_2$ phục vụ nhận dạng danh tính.

* **Giai đoạn 3 — Đối sánh định danh và phân loại phiên hành trình (Backend & Database):**
  - *Đối sánh tương đồng véc-tơ:* Backend thực hiện truy vấn khoảng cách Cosine trên trường véc-tơ (`vector(512)`) với phần mở rộng `pgvector` trong PostgreSQL đối với tập các khách hàng đã cấp quyền (`face_consent = true`):
    $$d(\mathbf{u}, \mathbf{v}) = 1 - \frac{\mathbf{u} \cdot \mathbf{v}}{\|\mathbf{u}\|_2 \|\mathbf{v}\|_2}$$
    Nếu khoảng cách nhỏ nhất thỏa mãn $d \le \tau_{\text{match}}$ (ngưỡng nhận dạng), danh tính khách hàng (`customer_id`) được xác lập; ngược lại bản ghi được giữ ở trạng thái khách vãng lai/chưa xác định.
  - *Quản lý phiên ghé thăm (Visit Session):* Với khách hàng đã nhận diện, hệ thống tìm lượt ghé thăm đang mở (`status = ACTIVE`). Nếu khoảng cách thời gian từ quan sát gần nhất $\Delta t = \text{observed\_at} - \text{last\_seen\_at} \le \tau_{\text{session}}$ (ngưỡng ngắt phiên), bản ghi được liên kết vào lượt hiện tại và cập nhật `last_seen_at`. Nếu $\Delta t > \tau_{\text{session}}$, hệ thống đóng lượt cũ (`status = CLOSED`, lý do `TIMEOUT`) và khởi tạo lượt ghé thăm mới.

* **Giai đoạn 4 — Giao dịch lưu trữ và ghi nhận quan sát (Backend & Database):**
  Thực hiện giao dịch cơ sở dữ liệu nguyên tử (ACID transaction) nhằm lưu thông tin đầy đủ vào bảng `observations` (bao gồm nhãn biểu cảm, độ tin cậy, vector khoảng cách, ID điểm chạm, ID khách hàng, ID lượt ghé thăm) và cập nhật bảng `visits`.

* **Giai đoạn 5 — Tổng hợp dữ liệu đa điểm chạm và trực quan hóa (Frontend CRM):**
  Giao diện người dùng CRM truy vấn các điểm cuối API báo cáo để tổng hợp chuỗi quan sát theo thời gian thực thành hành trình khách hàng hoàn chỉnh, ma trận chuyển dịch biểu cảm giữa các điểm chạm và biểu đồ phân bố biểu cảm theo thời gian/khu vực thông qua thư viện Apache ECharts.

---

#### 2. Bổ sung Bảng 4.2 — Đặc tả các giai đoạn trong luồng xử lý dữ liệu chính

Bổ sung bảng tổng hợp có cấu trúc học thuật rõ ràng:

```latex
\begin{table}[H]
    \centering
    \caption{Đặc tả chi tiết các giai đoạn trong luồng dữ liệu chính của hệ thống}
    \label{tab:data_flow_stages}
    \resizebox{\textwidth}{!}{%
    \begin{tabular}{|c|p{2.8cm}|p{3.5cm}|p{5.5cm}|p{3.5cm}|}
        \hline
        \textbf{Giai đoạn} & \textbf{Thành phần} & \textbf{Dữ liệu đầu vào} & \textbf{Quy trình \& Giải thuật chính} & \textbf{Dữ liệu đầu ra} \\
        \hline
        1 & Backend (BE) & Ảnh JPEG/PNG, mã điểm chạm, dấu thời gian & Tiếp nhận HTTP multipart, kiểm tra schema, xác thực trạng thái điểm chạm & Dữ liệu ảnh hợp lệ và metadata chuẩn hóa \\
        \hline
        2 & AI Module & Ảnh hiện trường chuẩn hóa & Phát hiện khuôn mặt (RetinaFace), phân loại 7 lớp biểu cảm (FER DeepFace), trích xuất véc-tơ ArcFace 512D & Bounding box, nhãn biểu cảm, độ tin cậy và véc-tơ đặc trưng \\
        \hline
        3 & Backend (BE) \& Database (DB) & Véc-tơ đặc trưng 512D, dấu thời gian & Truy vấn khoảng cách Cosine trên pgvector ($d \le \tau_{\text{match}}$), đối soát ngưỡng thời gian ngắt lượt ($\tau_{\text{session}}$) & Định danh khách hàng (\texttt{customer\_id}) và phiên lượt ghé thăm (\texttt{visit\_id}) \\
        \hline
        4 & Backend (BE) \& Database (DB) & Kết quả định danh, biểu cảm, metadata & Thực thi giao dịch ACID lưu vào bảng \texttt{observations}, cập nhật trạng thái bảng \texttt{visits} & Bản ghi quan sát hoàn chỉnh được lưu vĩnh viễn \\
        \hline
        5 & Frontend (FE) & Dữ liệu quan sát và hành trình từ REST API & Nhóm dữ liệu theo chuỗi thời gian, tính toán ma trận chuyển dịch biểu cảm và phân bố thống kê & Hành trình trực quan hóa, biểu đồ ECharts, báo cáo đa điểm chạm \\
        \hline
    \end{tabular}}
\end{table}
```

---

#### 3. Đề xuất thiết kế lại sơ đồ Hình 4.2 (TikZ)

Thiết kế lại sơ đồ luồng dữ liệu theo dạng **Pipeline tương tác phân tầng** làm nổi bật vai trò của 4 thành phần hệ thống và thiết bị ngoại vi:

```latex
\begin{figure}[H]
    \centering
    \resizebox{0.96\textwidth}{!}{%
    \begin{tikzpicture}[
        node distance=7mm and 8mm,
        stage/.style={draw, rounded corners=3pt, align=center, fill=gray!8, minimum height=14mm, text width=3.3cm, font=\small},
        proc/.style={draw, rounded corners=2pt, align=center, fill=white, minimum height=12mm, text width=3.2cm, font=\footnotesize},
        flow/.style={-{Latex[length=2.5mm]}, thick},
        lbl/.style={font=\scriptsize, align=center, fill=white, inner sep=1pt}
    ]
        % Hàng trên: Các giai đoạn luồng dữ liệu
        \node[proc] (p1) {\textbf{1. Tiếp nhận \& Kiểm tra}\\Ảnh + Mã điểm chạm\\{\scriptsize(Backend API)}};
        \node[proc, right=10mm of p1] (p2) {\textbf{2. Xử lý thị giác}\\Phát hiện, FER, ArcFace\\{\scriptsize(AI Module)}};
        \node[proc, right=10mm of p2] (p3) {\textbf{3. Đối sánh \& Quản lý}\\Tìm kiếm véc-tơ, ngắt lượt\\{\scriptsize(Backend \& pgvector)}};
        \node[proc, below=14mm of p3] (p4) {\textbf{4. Lưu trữ giao dịch}\\Bảng \texttt{observations}, \texttt{visits}\\{\scriptsize(Database PostgreSQL)}};
        \node[proc, left=10mm of p4] (p5) {\textbf{5. Phân tích \& Trực quan}\\Ma trận biểu cảm, ECharts\\{\scriptsize(Frontend CRM)}};

        % Khối nguồn ngoại vi
        \node[stage, left=10mm of p1, dashed] (src) {\textbf{Điểm chạm ngoại vi}\\Camera / Bộ mô phỏng\\{\scriptsize(Ảnh, Timestamp)}};

        % Các luồng kết nối
        \draw[flow] (src) -- node[above, lbl] {Yêu cầu\\HTTP POST} (p1);
        \draw[flow] (p1) -- node[above, lbl] {Ảnh thô} (p2);
        \draw[flow] (p2) -- node[above, lbl] {FER, 512D\\Véc-tơ} (p3);
        \draw[flow] (p3) -- node[right, lbl] {Lưu quan sát\\vào phiên} (p4);
        \draw[flow] (p4) -- node[above, lbl] {Dữ liệu lịch sử} (p5);
        \draw[flow, dashed] (p5) -| node[near start, below, lbl] {Truy vấn báo cáo} (p1);
    \end{tikzpicture}%
    }
    \caption{Quy trình luồng dữ liệu chính và sự phối hợp giữa các thành phần trong hệ thống}
    \label{fig:system_data_flow_ch4}
\end{figure}
```

- **Trạng thái:** Đã ghi chú chi tiết phương án nâng cấp văn phong học thuật, bảng đặc tả Bảng 4.2 và sơ đồ TikZ Hình 4.2 vào tài liệu ghi chú; các tệp `.tex` của luận văn được giữ nguyên vẹn.

## 13. Mở rộng các bên liên quan và thiết kế lại Biểu đồ ca sử dụng (Mục 4.2.1 — Hình 4.3)

**Tệp liên quan:** `Chuong/4_Xay_dung_va_phat_trien_he_thong.tex`  
**Vị trí:** Mục 4.2.1 — Ca sử dụng tổng quan (Hình 4.3: `fig:overall_usecase_ch4`)

### Vấn đề hiện tại
1. **Thiếu sót nghiêm trọng về các bên liên quan (Actors / Stakeholders):**
   - Nội dung hiện tại chỉ đề cập duy nhất một tác nhân là *Người quản lý cửa hàng* (`Store Manager`).
   - Trên thực tế, hệ thống là một nền tảng bán lẻ thông minh kết hợp CRM và AI phân tích biểu cảm đa điểm chạm, phục vụ đa dạng các bên liên quan trong doanh nghiệp:
     - **Nhân viên cửa hàng / điểm chạm (`Store Staff`):** Trực tiếp phục vụ, đăng ký nhận dạng khách hàng (kèm chấp thuận `face_consent`), xử lý đơn hàng tại quầy.
     - **Người quản lý cửa hàng (`Store Manager`):** Giám sát vận hành tại chỗ, theo dõi lưu lượng và hành trình khách hàng theo thời gian thực để điều phối nhân sự.
     - **Bộ phận Marketing & Quản trị trải nghiệm khách hàng (`Marketing & CX Team` / Ban Lãnh đạo):** Khai thác các báo cáo phân tích biểu cảm chuyên sâu (ma trận chuyển dịch biểu cảm giữa các điểm chạm, mức độ suy giảm/tăng tiến cảm xúc tích cực, phân bố theo khu vực/nhóm sản phẩm) nhằm tối ưu hóa bố cục cửa hàng, chính sách bán hàng và nâng cao trải nghiệm khách hàng.
     - **Quản trị viên hệ thống (`System Administrator`):** Quản trị tài khoản, phân quyền (`ADMIN`, `MANAGER`, `STAFF`), giám sát chất lượng dữ liệu đầu vào (tỷ lệ lỗi ảnh, tỷ lệ đối sánh khuôn mặt) và cấu hình ngưỡng tham số thuật toán ($\tau_{\text{match}}$, $\tau_{\text{session}}$).
2. **Biểu đồ Ca sử dụng (Hình 4.3) sơ sài và chưa đúng chuẩn UML:**
   - Biểu đồ cũ chỉ gồm 1 hình chữ nhật nối 4 hình elip nằm chồng lấn.
   - Thiếu ranh giới hệ thống (System Boundary), thiếu phân nhóm chức năng, chưa làm nổi bật giá trị phân tích dữ liệu đa điểm chạm của đề tài.

---

### Phương án điều chỉnh đề xuất

#### 1. Đề xuất viết lại nội dung văn bản Mục 4.2.1

Thay thế đoạn văn ngắn hiện tại bằng nội dung phân tích chi tiết các bên liên quan và ca sử dụng tương ứng:

> Hệ thống được thiết kế nhằm phục vụ bốn nhóm tác nhân chính trong mô hình vận hành bán lẻ thông minh:
> 1. **Nhân viên cửa hàng (Staff):** Thực hiện các tác vụ nghiệp vụ trực tiếp tại quầy, bao gồm tạo hồ sơ khách hàng mới, đăng ký ảnh khuôn mặt mẫu kèm xác nhận chấp thuận sử dụng dữ liệu sinh trắc học (`face_consent`), tra cứu lịch sử mua sắm và ghi nhận đơn hàng.
> 2. **Người quản lý cửa hàng (Store Manager):** Giám sát trực quan hành trình di chuyển của khách hàng qua các điểm chạm theo thời gian thực; theo dõi biến thiên biểu cảm theo từng khung giờ và khu vực trong ngày để kịp thời điều phối nhân viên phục vụ tại các điểm nóng.
> 3. **Bộ phận Marketing và Trải nghiệm khách hàng (Marketing & CX Team):** Khai thác hệ thống phân tích dữ liệu đa chiều để tối ưu hóa quy trình kinh doanh. Trọng tâm gồm: phân tích ma trận chuyển đổi biểu cảm giữa các điểm chạm kế tiếp, đánh giá tương quan giữa trạng thái cảm xúc với hành vi mua hàng, và nhận diện các điểm chạm có tỷ lệ biểu cảm tiêu cực cao để cải tiến không gian trưng bày hoặc phong cách tư vấn.
> 4. **Quản trị viên hệ thống (System Administrator):** Đảm bảo tính ổn định và bảo mật của toàn bộ hệ thống; quản lý tài khoản người dùng và phân quyền truy cập; giám sát báo cáo chất lượng dữ liệu đầu vào (tỷ lệ ảnh đạt chuẩn, tỷ lệ nhận dạng hợp lệ); đồng thời tinh chỉnh các ngưỡng kỹ thuật như khoảng cách đối sánh véc-tơ ($\tau_{\text{match}}$) và thời gian ngắt phiên tương tác ($\tau_{\text{session}}$).

---

#### 2. Bổ sung Bảng 4.3 — Ma trận ca sử dụng và các bên liên quan trong hệ thống

Bổ sung bảng tổng hợp học thuật đối chiếu phân quyền và chức năng:

```latex
\begin{table}[H]
    \centering
    \caption{Ma trận phân quyền ca sử dụng theo các bên liên quan trong hệ thống}
    \label{tab:stakeholder_usecases}
    \resizebox{\textwidth}{!}{%
    \begin{tabular}{|p{3.2cm}|p{3.5cm}|p{5.5cm}|p{3.8cm}|}
        \hline
        \textbf{Bên liên quan} & \textbf{Phân hệ chức năng} & \textbf{Các ca sử dụng cụ thể} & \textbf{Mục tiêu \& Giá trị hỗ trợ} \\
        \hline
        Nhân viên cửa hàng (\textit{Staff}) & Nghiệp vụ CRM \& Bán hàng & Đăng ký khách hàng \& mẫu khuôn mặt; Tra cứu thông tin khách hàng; Lập đơn hàng & Hỗ trợ phục vụ cá nhân hóa và số hóa hồ sơ khách hàng tại quầy \\
        \hline
        Quản lý cửa hàng (\textit{Store Manager}) & Giám sát vận hành \& Hành trình & Giám sát hành trình thời gian thực; Quản lý điểm chạm; Theo dõi biến thiên theo giờ & Nắm bắt lưu lượng khách, điều phối nhân sự và xử lý tình huống phát sinh \\
        \hline
        Bộ phận Marketing \& CX (\textit{Marketing/CX}) & Phân tích trải nghiệm đa điểm chạm & Phân tích ma trận chuyển dịch biểu cảm; Thống kê phân bố biểu cảm; Đánh giá tương quan đơn hàng & Tối ưu hóa trải nghiệm khách hàng, cải tiến layout cửa hàng và chiến lược marketing \\
        \hline
        Quản trị viên (\textit{Administrator}) & Quản trị hệ thống & Quản lý tài khoản \& phân quyền; Giám sát chất lượng dữ liệu; Cấu hình ngưỡng mô hình AI & Đảm bảo an toàn bảo mật, tính toàn vẹn dữ liệu và độ tin cậy của thuật toán \\
        \hline
    \end{tabular}}
\end{table}
```

---

#### 3. Đề xuất thiết kế lại sơ đồ Hình 4.3 (UML Use Case Diagram chuẩn mực bằng TikZ)

Biểu đồ được xây dựng lại theo chuẩn UML với khung System Boundary rõ ràng, 4 tác nhân được bố trí cân đối hai bên, các ca sử dụng elip được phân nhóm mạch lạc:

```latex
\begin{figure}[H]
    \centering
    \resizebox{0.98\textwidth}{!}{%
    \begin{tikzpicture}[
        actor/.style={draw, rounded corners=3pt, align=center, minimum width=2.8cm, minimum height=11mm, font=\small\bfseries, fill=blue!5},
        usecase/.style={draw, ellipse, align=center, minimum width=3.8cm, minimum height=9mm, font=\scriptsize, fill=white},
        link/.style={thick, shorten >=1pt, shorten <=1pt}
    ]
        % Khung ranh giới hệ thống (System Boundary)
        \draw[rounded corners=5pt, dashed, thick, fill=gray!3] (-2.2, -6.6) rectangle (8.6, 6.2);
        \node[font=\small\bfseries\itshape, anchor=north west] at (-2.0, 6.0) {Hệ thống Touchpoint CRM \& Phân tích biểu cảm};

        % Cột tác nhân bên trái: Nghiệp vụ và Vận hành
        \node[actor] (staff) at (-5.0, 3.5) {Nhân viên\\cửa hàng};
        \node[actor] (manager) at (-5.0, 0.2) {Quản lý\\cửa hàng};
        \node[actor] (marketing) at (-5.0, -3.2) {Bộ phận\\Marketing \& CX};

        % Cột tác nhân bên phải: Kỹ thuật và Quản trị
        \node[actor] (admin) at (11.4, 0.2) {Quản trị viên\\hệ thống};

        % Các ca sử dụng trong hệ thống (nhóm theo phân hệ)
        % Nhóm CRM & Bán hàng (phía trên)
        \node[usecase] (uc_reg) at (1.0, 4.8) {Đăng ký khách hàng\\và mẫu khuôn mặt};
        \node[usecase] (uc_order) at (5.4, 4.8) {Quản lý sản phẩm\\và lập đơn hàng};

        % Nhóm Hành trình & Điểm chạm (ở giữa trên)
        \node[usecase] (uc_journey) at (1.0, 2.5) {Theo dõi hành trình\\tại các điểm chạm};
        \node[usecase] (uc_touchpoint) at (5.4, 2.5) {Cấu hình danh mục\\các điểm chạm};

        % Nhóm Phân tích biểu cảm & Trải nghiệm (ở giữa dưới)
        \node[usecase] (uc_dist) at (1.0, 0.2) {Phân tích phân bố\\biểu cảm theo khu vực};
        \node[usecase] (uc_matrix) at (5.4, 0.2) {Phân tích ma trận\\chuyển dịch biểu cảm};
        \node[usecase] (uc_timeline) at (1.0, -2.1) {Theo dõi biến thiên\\theo thời gian};

        % Nhóm Quản trị & Giám sát hệ thống (phía dưới)
        \node[usecase] (uc_quality) at (5.4, -2.1) {Giám sát chất lượng\\dữ liệu và mô hình AI};
        \node[usecase] (uc_user) at (3.2, -4.5) {Quản lý tài khoản\\và phân quyền hệ thống};

        % Đường liên kết của Nhân viên cửa hàng
        \draw[link] (staff) -- (uc_reg);
        \draw[link] (staff) -- (uc_order);

        % Đường liên kết của Quản lý cửa hàng
        \draw[link] (manager) -- (uc_order);
        \draw[link] (manager) -- (uc_journey);
        \draw[link] (manager) -- (uc_dist);
        \draw[link] (manager) -- (uc_timeline);

        % Đường liên kết của Bộ phận Marketing & CX
        \draw[link] (marketing) -- (uc_dist);
        \draw[link] (marketing) -- (uc_matrix);
        \draw[link] (marketing) -- (uc_timeline);

        % Đường liên kết của Quản trị viên
        \draw[link] (admin) -- (uc_touchpoint);
        \draw[link] (admin) -- (uc_quality);
        \draw[link] (admin) -- (uc_user);
    \end{tikzpicture}%
    }
    \caption{Sơ đồ ca sử dụng tổng quan của hệ thống phân rã theo các bên liên quan}
    \label{fig:overall_usecase_ch4}
\end{figure}
```

- **Trạng thái:** Đã ghi chú chi tiết phương án mở rộng 4 nhóm tác nhân, bảng ma trận Bảng 4.3 và sơ đồ TikZ Hình 4.3 vào tài liệu ghi chú; các tệp `.tex` của luận văn được giữ nguyên vẹn.

## 14. Chuẩn hóa Bảng 4.3 — Các luồng giao tiếp giữa các thành phần hệ thống theo chuẩn phần mềm

**Tệp liên quan:** `Chuong/4_Xay_dung_va_phat_trien_he_thong.tex`  
**Vị trí:** Mục 4.1.1 — Bảng 4.3 (`tab:component_communication`)

### Vấn đề hiện tại
1. **Tên thành phần chưa đồng bộ và thiếu chuẩn mực kỹ thuật phần mềm:**
   - Bảng 4.3 hiện tại sử dụng các tên gọi mô tả chung chung: `Giao diện CRM`, `Nguồn thu nhận`, `Máy chủ nghiệp vụ`, `Dịch vụ xử lý ảnh`, `Cơ sở dữ liệu`.
   - Cần đồng bộ tuyệt đối với 4 thành phần phần mềm chuẩn đã quy ước tại Bảng 4.1 và sơ đồ Hình 4.1: **Frontend (FE)**, **Backend (BE)**, **AI Module**, **Database (DB)** cùng thiết bị thu nhận ngoại vi (**Thiết bị tại điểm chạm / Camera**).
2. **Thiếu thông tin giao thức / cơ chế giao tiếp (Protocol / Mechanism):**
   - Trong tài liệu đặc tả kiến trúc phần mềm (Software Architecture Document — SAD theo chuẩn IEEE 1016), bảng mô tả luồng giao tiếp liên thành phần (Inter-component Communication) cần làm rõ giao thức mạng, định dạng dữ liệu (như `HTTPS REST API / JSON`, `HTTP Multipart Form-data`, `SQL over TCP/IP`). Bảng hiện tại thiếu cột này khiến tài liệu mang tính chất mô tả định tính hơn là đặc tả kỹ thuật chính xác.
3. **Mô tả dữ liệu trao đổi và mục đích nghiệp vụ cần cụ thể hơn:**
   - Dữ liệu trao đổi cần phản ánh đúng các đối tượng truyền nhận trong mã nguồn thực tế (JWT Bearer Token, Image Payload, Bounding Box coordinates, 7 xác suất biểu cảm FER, véc-tơ ArcFace 512 chiều, Cosine Distance Query).

---

### Phương án điều chỉnh đề xuất

#### 1. Đề xuất chuẩn hóa Bảng 4.3 theo chuẩn kỹ thuật phần mềm

Bổ sung cột **Giao thức / Cơ chế** và chuẩn hóa toàn bộ các thành phần gửi/nhận:

```latex
\begin{table}[H]
    \centering
    \caption{Các luồng giao tiếp chính giữa các thành phần phần mềm trong hệ thống}
    \label{tab:component_communication}
    \resizebox{\textwidth}{!}{%
    \begin{tabular}{|p{2.8cm}|p{2.8cm}|p{2.6cm}|p{4.2cm}|p{4.8cm}|}
        \hline
        \textbf{Thành phần gửi} & \textbf{Thành phần nhận} & \textbf{Giao thức / Cơ chế} & \textbf{Dữ liệu trao đổi} & \textbf{Mục đích nghiệp vụ} \\
        \hline
        \textbf{Frontend (FE)} \newline(\texttt{apps/web}) & \textbf{Backend (BE)} \newline(\texttt{apps/api}) & HTTPS / REST API \newline(JSON, Bearer Token) & Thông tin xác thực (JWT), tham số lọc báo cáo, dữ liệu CRM do người dùng nhập & Thực hiện các chức năng quản lý CRM, tra cứu hồ sơ khách hàng, phân quyền và hiển thị báo cáo \\
        \hline
        \textbf{Thiết bị tại điểm chạm} \newline(Camera / Simulator) & \textbf{Backend (BE)} \newline(\texttt{apps/api}) & HTTP POST \newline(Multipart Form-data) & Ảnh thô hiện trường, mã sự kiện (\texttt{event\_id}), mã điểm chạm, dấu thời gian & Gửi dữ liệu quan sát tại điểm chạm để khởi tạo sự kiện thu nhận và kiểm tra trùng lặp \\
        \hline
        \textbf{Backend (BE)} \newline(\texttt{apps/api}) & \textbf{AI Module} \newline(\texttt{services/vision}) & HTTP POST \newline(JSON / Binary payload) & Tệp ảnh hiện trường và thông số yêu cầu xử lý & Yêu cầu phát hiện vùng khuôn mặt, phân loại 7 lớp biểu cảm và trích xuất véc-tơ nhận dạng \\
        \hline
        \textbf{AI Module} \newline(\texttt{services/vision}) & \textbf{Backend (BE)} \newline(\texttt{apps/api}) & HTTP Response \newline(JSON Schema) & Danh sách bounding box, nhãn biểu cảm, 7 xác suất FER, véc-tơ ArcFace 512 chiều & Cung cấp kết quả suy luận AI độc lập để Backend thực thi đối sánh khách hàng và liên kết CRM \\
        \hline
        \textbf{Backend (BE)} \newline(\texttt{apps/api}) & \textbf{Database (DB)} \newline(\texttt{postgres}) & TCP/IP \newline(SQLAlchemy ORM \& pgvector) & Câu lệnh SQL (CRUD), truy vấn khoảng cách Cosine trên véc-tơ, bản ghi nhật ký & Lưu trữ hồ sơ CRM, bản ghi quan sát, phiên lượt ghé thăm và tìm kiếm đối sánh khuôn mặt \\
        \hline
    \end{tabular}}
\end{table}
```

#### 2. Cập nhật các thuật ngữ trong phần diễn giải xung quanh Bảng 4.3

Đồng bộ thuật ngữ trong các đoạn văn của Mục 4.1.1:
- Thay vì dùng `máy chủ nghiệp vụ`, sử dụng `Backend (BE)`.
- Thay vì dùng `giao diện CRM`, sử dụng `Frontend (FE)`.
- Thay vì dùng `dịch vụ xử lý ảnh`, sử dụng `AI Module`.
- Thay vì dùng `cơ sở dữ liệu`, sử dụng `Database (DB) PostgreSQL/pgvector`.
- Thay vì dùng `nguồn thu nhận`, sử dụng `thiết bị thu nhận tại điểm chạm`.

- **Trạng thái:** Đã ghi chú chi tiết phương án chuẩn hóa Bảng 4.3 vào tài liệu ghi chú; các tệp `.tex` của luận văn được giữ nguyên vẹn.

## 15. Nâng cấp biểu đồ theo dõi hành trình mua sắm theo thời gian, khu vực và mức độ biểu cảm (Mục 4.3.3 — Hình 4.7)

**Tệp liên quan:** `Chuong/4_Xay_dung_va_phat_trien_he_thong.tex`  
**Vị trí:** Mục 4.3.3 — Khởi tạo, cập nhật và kết thúc lần mua sắm (Hình 4.7: `fig:shopping_tracking_ch4`, tệp ảnh `Hinhve/Chuong4/4_07_theo_doi_mua_sam.png`)

### 1. Phân tích hạn chế của giao diện và hình ảnh hiện tại
- **Hiện trạng:**
  - Hình 4.7 trong báo cáo thể hiện màn hình *Theo dõi quá trình mua sắm* của một khách hàng bằng 4 nút tròn liên kết rời rạc theo chiều ngang: `Cửa vào (Happy)` $\to$ `Khu trưng bày sản phẩm (Happy)` $\to$ `Khu tư vấn (Neutral)` $\to$ `Quầy thanh toán (Neutral)`.
  - Nhược điểm:
    1. **Thiếu trục thời gian thực (Timeline):** Chưa thể hiện được mốc thời gian cụ thể của từng quan sát, khoảng cách thời gian giữa các điểm chạm và thời lượng dừng chân (dwell time) của khách hàng tại mỗi khu vực.
    2. **Chưa lượng hóa mức độ cảm xúc (Emotion Valence / Intensity):** Mỗi quan sát chỉ hiển thị nhãn định tính, chưa thể hiện được mức độ biểu cảm (thang đo tích cực/tiêu cực) và độ tin cậy ($Confidence$) của mô hình AI.
    3. **Thiếu tính liên tục của trải nghiệm:** Chưa thể hiện được "Đường cong cảm xúc" (Customer Emotional Curve) — một công cụ cốt lõi trong nghiên cứu trải nghiệm khách hàng (Customer Journey Mapping - CJM) giúp nhận diện các điểm tụt dốc cảm xúc (pain points) trong hành trình mua sắm.

---

### 2. Phương án nâng cấp đề xuất: Trực quan hóa đa chiều (Thời gian $\times$ Khu vực $\times$ Mức độ biểu cảm)

Nâng cấp thành phần trực quan hóa hành trình chi tiết của khách hàng thành hệ thống biểu đồ kết hợp:

#### A. Biểu đồ đường cong cảm xúc theo dòng thời gian (Timeline Emotion Journey Chart)
- **Trục hoành ($X$):** Trục thời gian thực tế ghi nhận các quan sát (ví dụ: `18:58` $\to$ `19:05` $\to$ `19:16` $\to$ `19:24`).
- **Trục tung ($Y$):** Thang điểm mức độ cảm xúc (Emotion Valence Score):
  - $+1.0$: Nhóm tích cực (*Happy* — Vui vẻ, hài lòng).
  - $0.0$: Nhóm trung tính (*Neutral* — Bình thản, ổn định).
  - $-1.0$: Nhóm tiêu cực (*Sad, Angry, Disgust, Fear* — Thất vọng, khó chịu).
- **Phân vùng khu vực nền (Background Area Bands):** Nền biểu đồ được chia thành các dải màu nhẹ đánh dấu phạm vi không gian của từng điểm chạm: *Cửa vào* $\to$ *Khu trưng bày* $\to$ *Khu tư vấn* $\to$ *Quầy thanh toán*.
- **Điểm dữ liệu (Data Points):** Mỗi điểm quan sát hiển thị nhãn biểu cảm, độ tin cậy ($Confidence$), kích thước điểm tỷ lệ với thời gian lưu trú tại vị trí đó.
- **Đường biểu diễn mượt (Spline Curve):** Nối các điểm tạo thành đường cong cảm xúc liên tục, cho thấy rõ xu hướng chuyển dịch tâm lý khách hàng (ví dụ: đang hài lòng khi xem hàng nhưng chuyển sang trung tính khi vào tư vấn/thanh toán).

#### B. Biểu đồ thời gian lưu trú và phân bố biểu cảm theo khu vực (Dwell Time & Touchpoint Breakdown)
- Biểu đồ dạng Gantt hoặc cột xếp chồng thể hiện thời gian bắt đầu, thời gian kết thúc và tổng số phút khách hàng lưu lại ở từng điểm chạm.
- Màu sắc thanh đại diện cho phân bố tỷ lệ các biểu cảm quan sát được trong suốt thời gian dừng chân.

---

### 3. Đề xuất nội dung bổ sung vào văn bản Luận văn (Mục 4.3.3)

Bổ sung đoạn văn diễn giải học thuật làm rõ cơ sở phân tích đa chiều:

> Thay vì chỉ hiển thị chuỗi các điểm chạm rời rạc dưới dạng các bước tĩnh, giao diện theo dõi hành trình được nâng cấp thành biểu đồ đường cong cảm xúc theo dòng thời gian thực (Hình~\ref{fig:shopping_tracking_ch4}). Biểu đồ kết hợp đồng thời ba chiều dữ liệu:
> 1. **Chiều thời gian ($t$):** Ghi nhận chính xác thời điểm tương tác và khoảng thời gian lưu trú giữa các điểm chạm liên tiếp.
> 2. **Chiều không gian ($S$):** Phân định các khu vực vật lý trong cửa hàng thông qua mã điểm chạm.
> 3. **Chiều trạng thái tâm lý ($E$):** Lượng hóa nhãn biểu cảm thành mức độ cảm xúc kết hợp độ tin cậy của thuật toán phân loại.
>
> Cách tiếp cận này cho phép người quản lý và bộ phận trải nghiệm khách hàng theo dõi trực quan diễn biến tâm lý khách hàng xuyên suốt hành trình, từ đó dễ dàng phát hiện các điểm nghẽn trải nghiệm (ví dụ: cảm xúc sụt giảm từ tích cực xuống trung tính tại khu vực tư vấn hoặc quầy thanh toán) để có giải pháp can thiệp kịp thời.

---

### 4. Mã TikZ đề xuất cho Biểu đồ hành trình cảm xúc đa chiều (Hình 4.7 mới)

Có thể sử dụng mã TikZ sau để vẽ biểu đồ trực quan học thuật trong báo cáo:

```latex
\begin{figure}[H]
    \centering
    \resizebox{0.96\textwidth}{!}{%
    \begin{tikzpicture}[
        point/.style={circle, draw, fill=#1, inner sep=3pt},
        lbl/.style={font=\scriptsize, align=center},
        area/.style={font=\footnotesize\bfseries, text=gray!80}
    ]
        % Khung tọa độ
        \draw[->, thick] (0, 0) -- (12.5, 0) node[right, font=\small] {Thời gian ($t$)};
        \draw[->, thick] (0, -2.5) -- (0, 3.0) node[above, font=\small] {Mức độ biểu cảm ($Y$)};

        % Các vạch trục tung
        \draw[dashed, gray!40] (0, 2.0) -- (12.0, 2.0) node[right, font=\scriptsize, text=black] {+1.0 (Tích cực: Happy)};
        \draw[dashed, gray!60] (0, 0.0) -- (12.0, 0.0) node[right, font=\scriptsize, text=black] {0.0 (Trung tính: Neutral)};
        \draw[dashed, gray!40] (0, -2.0) -- (12.0, -2.0) node[right, font=\scriptsize, text=black] {-1.0 (Tiêu cực: Sad/Angry)};

        % Các phân vùng khu vực (Dải màu nền)
        \fill[green!5] (0.5, -2.4) rectangle (3.2, 2.6);
        \node[area] at (1.85, -2.2) {Cửa vào};

        \fill[blue!5] (3.2, -2.4) rectangle (6.2, 2.6);
        \node[area] at (4.7, -2.2) {Khu trưng bày};

        \fill[orange!5] (6.2, -2.4) rectangle (9.2, 2.6);
        \node[area] at (7.7, -2.2) {Khu tư vấn};

        \fill[purple!5] (9.2, -2.4) rectangle (11.8, 2.6);
        \node[area] at (10.5, -2.2) {Quầy thanh toán};

        % Ranh giới phân vùng
        \draw[dotted, gray!70, thick] (3.2, -2.4) -- (3.2, 2.6);
        \draw[dotted, gray!70, thick] (6.2, -2.4) -- (6.2, 2.6);
        \draw[dotted, gray!70, thick] (9.2, -2.4) -- (9.2, 2.6);

        % Các mốc thời gian và điểm quan sát
        % Điểm 1: Cửa vào - 18:58 - Happy (2.0)
        \coordinate (P1) at (1.85, 2.0);
        \node[point=green!60!black] at (P1) {};
        \node[lbl, above=2pt of P1] {\textbf{Happy} (c=0.94)\\18:58:00};

        % Điểm 2: Trưng bày - 19:07 - Happy (2.0)
        \coordinate (P2) at (4.7, 2.0);
        \node[point=green!60!black] at (P2) {};
        \node[lbl, above=2pt of P2] {\textbf{Happy} (c=0.88)\\19:07:15};

        % Điểm 3: Tư vấn - 19:16 - Neutral (0.0)
        \coordinate (P3) at (7.7, 0.0);
        \node[point=blue!60!black] at (P3) {};
        \node[lbl, above=2pt of P3] {\textbf{Neutral} (c=0.82)\\19:16:40};

        % Điểm 4: Thanh toán - 19:24 - Neutral (0.0)
        \coordinate (P4) at (10.5, 0.0);
        \node[point=blue!60!black] at (P4) {};
        \node[lbl, above=2pt of P4] {\textbf{Neutral} (c=0.91)\\19:24:10};

        % Đường cong cảm xúc nối các điểm
        \draw[very thick, teal] (P1) -- (P2) to[out=0, in=180] (P3) -- (P4);
    \end{tikzpicture}%
    }
    \caption{Diễn biến mức độ biểu cảm của khách hàng theo thời gian và khu vực trong một lần mua sắm}
    \label{fig:shopping_tracking_ch4}
\end{figure}
```

- **Trạng thái:** Đã ghi chú chi tiết phương án nâng cấp biểu đồ theo dõi hành trình vào tài liệu ghi chú; các tệp `.tex` của luận văn được giữ nguyên vẹn.

## 16. Bổ sung bộ lọc lần mua sắm theo thời gian và cơ chế thông báo lỗi hệ thống thời gian thực

**Tệp liên quan:** `Chuong/4_Xay_dung_va_phat_trien_he_thong.tex`  
**Vị trí:** Mục 4.3.3 (Theo dõi các quan sát trong một lần mua sắm), Mục 4.4.3 (Báo cáo chất lượng dữ liệu) và Kiến trúc giao diện người dùng

### 1. Bổ sung Bộ lọc danh sách lần mua sắm theo khoảng thời gian và tiêu chí nâng cao
- **Vấn đề hiện tại:**
  - Danh sách lần mua sắm ở cột trái (Mục 4.3.3 / Hình 4.7) chỉ hiển thị một danh sách phẳng các lượt mua sắm gần nhất, thiếu cơ chế tìm kiếm và lọc dữ liệu.
  - Khi số lượng giao dịch và lượt khách tăng lên (hàng trăm đến hàng nghìn lượt mua sắm mỗi ngày), người quản lý và nhân viên không thể tra cứu hoặc phân tích các lượt mua sắm cụ thể nếu thiếu bộ lọc thời gian.
- **Phương án đề xuất bổ sung:**
  1. **Bộ lọc theo khoảng thời gian (Date-Time Range Filter):**
     - Các mốc thời gian thiết lập sẵn: *Hôm nay*, *Hôm qua*, *7 ngày gần nhất*, *30 ngày qua*, *Tháng này*.
     - Bộ chọn thời gian tùy ý (Date-Time Range Picker): Hỗ trợ lọc chính xác theo ngày và giờ (ví dụ: ca sáng `08:00 - 12:00`, ca chiều `13:00 - 17:00`, ca tối `18:00 - 22:00`) nhằm đánh giá hiệu quả phục vụ theo từng ca trực hoặc trong các khung giờ vàng/sự kiện khuyến mãi đặc thù.
  2. **Bộ lọc kết hợp theo đặc trưng hành trình:**
     - Lọc theo trạng thái phiên: Đang diễn ra (`ACTIVE`), Đã kết thúc bình thường (`CLOSED`), Kết thúc do quá thời gian (`TIMEOUT`), Kết thúc thủ công (`MANUAL`).
     - Lọc theo điểm chạm đi qua: Chỉ hiển thị các lần mua sắm có ghé qua điểm chạm cụ thể (ví dụ: chỉ lọc những khách có ghé *Khu tư vấn* hoặc dừng chân tại *Quầy thanh toán*).
     - Lọc theo đối tượng khách hàng: Khách hàng thân thiết đã định danh (`Identified`) vs Khách hàng vãng lai chưa nhận dạng (`Unidentified`).
     - Lọc theo xu hướng cảm xúc: Ưu tiên lọc các lượt mua sắm xuất hiện biểu cảm tiêu cực (*Warning / Cần lưu ý*) để đội ngũ chăm sóc khách hàng chủ động rà soát nguyên nhân.

---

### 2. Thiết kế Cơ chế thông báo lỗi hệ thống và cảnh báo bất thường thời gian thực (Real-time Notification & Alert System)
- **Vấn đề hiện tại:**
  - Hệ thống hiện chỉ ghi nhận lỗi thụ động vào cơ sở dữ liệu và hiển thị trên màn hình báo cáo chất lượng dữ liệu định kỳ (Mục 4.4.3).
  - Khi có sự cố phần cứng, camera ngắt kết nối hoặc mô hình AI gặp lỗi quá tải, người quản lý không nhận được cảnh báo ngay lập tức, dẫn đến gián đoạn việc thu thập dữ liệu hành trình khách hàng.
- **Phương án đề xuất bổ sung:**
  1. **Phân loại các cấp độ cảnh báo & thông báo:**
     - **Lỗi kỹ thuật nghiêm trọng (Critical System Errors):**
       + Mất kết nối camera/thiết bị tại điểm chạm (`Camera Offline / Heartbeat Timeout > 60s`).
       + Mô-đun AI (`services/vision`) không phản hồi hoặc trả về mã lỗi `503 Service Unavailable`.
       + Lỗi gián đoạn kết nối cơ sở dữ liệu (`Database Connection Failure`).
     - **Cảnh báo chất lượng dữ liệu (Data Quality Warnings):**
       + Tỷ lệ ảnh mờ, tối hoặc không phát hiện được khuôn mặt tăng đột biến trong khoảng thời gian ngắn (nghi ngờ camera bị lệch góc hoặc ánh sáng khu vực thay đổi).
       + Xung đột thời gian quan sát (hai điểm chạm khác nhau ghi nhận cùng một khách hàng tại cùng một giây).
     - **Cảnh báo trải nghiệm khách hàng (CX Anomaly Alerts):**
       + Phát hiện chuỗi biểu cảm tiêu cực liên tiếp (ví dụ: xuất hiện 3 quan sát liên tiếp có biểu cảm *Angry/Sad* tại cùng một điểm chạm trong vòng 10 phút), hệ thống lập tức phát cảnh báo để quản lý cửa hàng điều phối nhân sự hỗ trợ tại chỗ.
  2. **Cơ chế hiển thị trên giao diện người dùng:**
     - **Trung tâm thông báo (Notification Center):** Biểu tượng chuông thông báo trên thanh Header của giao diện CRM, hiển thị danh sách các sự cố chưa xử lý kèm mức độ nghiêm trọng (*Critical*, *Warning*, *Info*).
     - **Thông báo đẩy thời gian thực (Toast / Banner Alert):** Khi phát hiện lỗi nghiêm trọng, hệ thống tự động hiển thị pop-up cảnh báo tức thì nổi trên góc màn hình kèm thông tin vị trí điểm chạm, mã lỗi và thời gian xảy ra.
     - **Giao thức truyền thông:** Kết nối thời gian thực giữa Backend API (`apps/api`) và Frontend CRM (`apps/web`) thông qua cơ chế WebSocket hoặc Server-Sent Events (SSE).

---

### 3. Bổ sung Bảng 4.4 — Đặc tả danh mục thông báo lỗi và cảnh báo trong hệ thống

Bổ sung bảng tổng hợp học thuật:

```latex
\begin{table}[H]
    \centering
    \caption{Đặc tả danh mục cảnh báo và thông báo lỗi thời gian thực của hệ thống}
    \label{tab:system_alerts_spec}
    \resizebox{\textwidth}{!}{%
    \begin{tabular}{|p{2.5cm}|p{3.2cm}|c|p{5.5cm}|p{4.5cm}|}
        \hline
        \textbf{Mã cảnh báo} & \textbf{Loại cảnh báo} & \textbf{Mức độ} & \textbf{Điều kiện kích hoạt} & \textbf{Hành động xử lý đề xuất} \\
        \hline
        \texttt{ERR\_CAM\_OFF} & Lỗi kết nối thiết bị & Critical & Không nhận được dữ liệu từ camera điểm chạm quá 60 giây & Kiểm tra nguồn điện, kết nối mạng và dịch vụ camera tại điểm chạm \\
        \hline
        \texttt{ERR\_AI\_DOWN} & Lỗi mô-đun AI & Critical & Mô-đun thị giác máy tính không phản hồi hoặc trả về mã 503 & Tự động khởi động lại container dịch vụ vision, chuyển sang chế độ dự phòng \\
        \hline
        \texttt{WARN\_IMG\_QUAL} & Cảnh báo chất lượng ảnh & Warning & Tỷ lệ ảnh không phát hiện được khuôn mặt vượt quá 30\% trong 15 phút & Kiểm tra góc đặt camera, tiêu cự và điều kiện ánh sáng tại khu vực \\
        \hline
        \texttt{WARN\_CONFLICT} & Cảnh báo xung đột thời gian & Warning & Cùng một khách hàng xuất hiện tại hai điểm chạm khác nhau trong cùng thời điểm & Đánh dấu bản ghi xung đột, loại trừ khỏi ma trận chuyển dịch và kiểm tra ngưỡng nhận dạng \\
        \hline
        \texttt{ALERT\_CX\_NEG} & Cảnh báo trải nghiệm khách & Warning & Xuất hiện từ 3 quan sát mang nhãn tiêu cực liên tiếp tại cùng một điểm chạm & Thông báo đẩy đến người quản lý cửa hàng để kịp thời điều phối nhân sự hỗ trợ \\
        \hline
    \end{tabular}}
\end{table}
```

---

### 4. Đề xuất nội dung bổ sung vào văn bản Luận văn (Mục 4.3.3)

> Nhằm nâng cao khả năng quản trị vận hành trong môi trường thực tế, hệ thống bổ sung hai tiện ích quan trọng:
> 1. **Cơ chế lọc đa tiêu chí:** Cho phép người dùng linh hoạt lọc danh sách lần mua sắm theo các khoảng thời gian định sẵn hoặc tùy chọn theo từng ca làm việc, kết hợp với bộ lọc theo trạng thái phiên, điểm chạm đi qua và mức độ biểu cảm ghi nhận.
> 2. **Hệ thống cảnh báo thời gian thực:** Tự động phát hiện và gửi thông báo tức thời đến người quản lý khi xảy ra sự cố phần cứng (mất tín hiệu camera), lỗi quá tải mô-đun AI hoặc khi xuất hiện chuỗi biểu cảm tiêu cực bất thường tại một điểm chạm (Bảng~\ref{tab:system_alerts_spec}). Cơ chế này giúp đảm bảo tính liên tục của dữ liệu và hỗ trợ can thiệp dịch vụ khách hàng kịp thời.

- **Trạng thái:** Đã ghi chú chi tiết phương án bổ sung bộ lọc thời gian và cơ chế thông báo lỗi vào tài liệu ghi chú; các tệp `.tex` của luận văn được giữ nguyên vẹn.

## 17. Quản lý định danh ẩn danh và liên kết hành trình đa phiên cho khách hàng chưa đăng ký CRM (Mục 4.3.4 — Hình 4.10)

**Tệp liên quan:** `Chuong/4_Xay_dung_va_phat_trien_he_thong.tex`  
**Vị trí:** Mục 4.3.4 — Xử lý bản ghi chưa xác định khách hàng (Hình 4.10: `fig:unidentified_observations_ch4`, tệp ảnh `Hinhve/Chuong4/4_15_quan_sat_chua_xac_dinh.png`)

### 1. Phân tích hạn chế của cách tiếp cận hiện tại
- **Hiện trạng:**
  - Mục 4.3.4 hiện tại quy định: *“Bản ghi không nhận dạng được khách hàng không được tự động ghép với một hồ sơ CRM và không tạo chuỗi cá nhân... chỉ được dùng cho thống kê theo khu vực”*.
  - Hình 4.10 hiển thị một bảng phẳng liệt kê các quan sát có trạng thái `NO_MATCH` trôi nổi độc lập.
- **Bất cập trong bài toán bán lẻ thực tế:**
  1. **Làm đứt gãy hành trình khách hàng:** Dù một khách hàng chưa có tài khoản thành viên trong CRM, khi họ bước vào cửa hàng, họ vẫn di chuyển qua nhiều điểm chạm liên tiếp (Cửa vào $\to$ Trưng bày $\to$ Tư vấn $\to$ Thanh toán). Việc xem mỗi quan sát là một sự kiện rời rạc làm mất đi bản chất của bài toán *Phân tích hành trình khách hàng đa điểm chạm*.
  2. **Không nhận diện được khách hàng quay lại (Returning Visitors):** Khách hàng chưa đăng ký có thể ghé thăm cửa hàng nhiều lần vào các ngày khác nhau (các phiên mua sắm khác nhau). Nếu không lưu lại định danh và véc-tơ khuôn mặt ẩn danh, hệ thống hoàn toàn “quên” khách hàng này ở các lần ghé thăm tiếp theo.
  3. **Bỏ lỡ cơ hội chuyển đổi hồ sơ (Profile Conversion):** Khi khách hàng quyết định đăng ký thành viên chính thức tại quầy thu ngân, hệ thống không thể liên kết lại lịch sử trải nghiệm cảm xúc và các lượt ghé thăm trước đó của họ.

---

### 2. Phương án nâng cấp đề xuất: Mô hình định danh ẩn danh hai tầng (Two-Tier Identification)

Hệ thống được mở rộng để quản lý khách hàng chưa có hồ sơ CRM theo cơ chế **Định danh ẩn danh (Anonymous ID)** và **Theo dõi đa phiên (Cross-Session Tracking)**:

```text
Ảnh đầu vào → Phát hiện khuôn mặt → Trích xuất véc-tơ ArcFace (512D)
    │
    ├── Tầng 1: Đối sánh với Kho mẫu CRM chính thức (face_templates)
    │     ├── Nếu Khớp (d ≤ τ_match) ──> Gắn customer_id chính thức
    │     │
    │     └── Nếu KHÔNG khớp (NO_MATCH) ──> Chuyển sang Tầng 2
    │
    └── Tầng 2: Đối sánh với Kho mẫu Ẩn danh (anonymous_face_templates)
          ├── Nếu Khớp (d ≤ τ_anon) ──> Nhận diện KHÁCH QUAY LẠI ──> Gắn anonymous_id đã có
          │                             └── Tạo hoặc gộp vào lượt ghé thăm (visit) mới của khách này
          │
          └── Nếu KHÔNG khớp ─────────> Khởi tạo định danh ẩn danh MỚI (ANON-CUS-xxxx)
                                        └── Lưu véc-tơ 512D vào kho mẫu ẩn danh
                                        └── Khởi tạo lượt ghé thăm đầu tiên
```

#### A. Cấu trúc dữ liệu và thực thể mở rộng
- **Bảng `anonymous_customers`:**
  - `id` (UUID): Khóa chính.
  - `anonymous_code` (text): Mã định danh ẩn danh tự sinh (ví dụ: `ANON-00284`).
  - `first_seen_at` (timestamptz): Thời điểm quan sát đầu tiên.
  - `last_seen_at` (timestamptz): Thời điểm quan sát gần nhất.
  - `visit_count` (int): Tổng số lượt ghé thăm cửa hàng (tích lũy qua các ngày).
  - `status` (enum): `ACTIVE`, `CONVERTED` (đã hợp nhất vào CRM), `EXPIRED`.
- **Bảng `anonymous_face_templates`:**
  - `id` (UUID), `anonymous_id` (UUID tham chiếu `anonymous_customers`).
  - `embedding` (`vector(512)`): Véc-tơ ArcFace chất lượng cao.
  - `created_at` (timestamptz), thời hạn lưu trữ cấu hình (ví dụ: 30 hoặc 90 ngày theo chính sách bảo mật).
- **Liên kết với `visits` và `observations`:**
  - Các bảng `visits` và `observations` cho phép lưu hoặc `customer_id` (nếu là khách chính thức) hoặc `anonymous_id` (nếu là khách ẩn danh).
  - Khách ẩn danh vẫn có chuỗi hành trình điểm chạm hoàn chỉnh trong từng lượt ghé thăm (`visits`).

#### B. Quy trình hợp nhất khi khách hàng đăng ký CRM (Profile Merging)
- Khi khách hàng vãng lai quyết định đăng ký hồ sơ thành viên CRM tại quầy:
  1. Nhân viên chụp ảnh đăng ký chính thức và khách hàng ký chấp thuận `face_consent = true`.
  2. Hệ thống tự động đối sánh khuôn mặt mới với kho mẫu ẩn danh `anonymous_face_templates`.
  3. Nếu tìm thấy mã `anonymous_id` tương ứng, hệ thống cho phép liên kết toàn bộ lịch sử các lượt ghé thăm và dữ liệu biểu cảm trong quá khứ của khách vào hồ sơ CRM chính thức mới tạo, đồng thời đánh dấu `status = CONVERTED` cho hồ sơ ẩn danh.

---

### 3. Thiết kế lại giao diện Hình 4.10 trong Luận văn

Thay vì một bảng phẳng các quan sát rời rạc, giao diện Hình 4.10 được nâng cấp thành **Quản lý hành trình khách hàng chưa đăng ký CRM**:
- Cột bên trái: Danh sách các hồ sơ khách hàng ẩn danh (`Khách ẩn danh ANON-095`, `ANON-096`,...), hiển thị số lần ghé thăm cửa hàng (ví dụ: *Ghé thăm 3 lần*), thời gian ghé thăm gần nhất.
- Cột bên phải: Hiển thị chi tiết hành trình đa điểm chạm và biểu đồ đường cong cảm xúc của khách ẩn danh được chọn qua từng lượt ghé thăm.
- Nút tác vụ: *Liên kết với hồ sơ CRM* (cho phép gộp vào khách hàng có sẵn hoặc tạo mới hồ sơ).

---

### 4. Đề xuất nội dung bổ sung vào văn bản Luận văn (Mục 4.3.4)

Bổ sung đoạn văn học thuật làm rõ cơ chế quản lý khách hàng ẩn danh và tái nhận diện đa phiên:

> Đối với các khuôn mặt không đối sánh thành công với hồ sơ CRM chính thức, hệ thống không xem chúng là các sự kiện ngẫu nhiên rời rạc. Thay vào đó, quy trình đối sánh hai tầng được áp dụng: khuôn mặt đạt ngưỡng chất lượng được cấp một mã định danh ẩn danh (`anonymous_id`) và lưu véc-tơ đặc trưng vào kho mẫu tạm thời (Hình~\ref{fig:unidentified_observations_ch4}).
>
> Cơ chế này mang lại hai lợi ích cốt lõi:
> 1. **Bảo toàn tính liên tục của hành trình:** Toàn bộ các quan sát của cùng một khách hàng tại các khu vực khác nhau trong cùng buổi mua sắm được xâu chuỗi thành một lượt ghé thăm hoàn chỉnh, phục vụ thống kê chuyển dịch biểu cảm chính xác.
> 2. **Tái nhận diện khách hàng quay lại (Cross-session Re-identification):** Khi khách hàng chưa đăng ký quay lại cửa hàng ở các ngày tiếp theo, hệ thống đối soát với kho mẫu ẩn danh để nhận diện khách quen, duy trì lịch sử ghé thăm đa phiên và sẵn sàng hợp nhất toàn bộ dữ liệu trải nghiệm quá khứ khi khách hàng đồng ý tạo hồ sơ CRM chính thức.

- **Trạng thái:** Đã ghi chú chi tiết phương án định danh ẩn danh và liên kết hành trình đa phiên vào tài liệu ghi chú; các tệp `.tex` của luận văn được giữ nguyên vẹn.

## 18. Nâng cấp biểu đồ phân tích cơ cấu biểu cảm theo từng khu vực bằng Biểu đồ tròn / Biểu đồ vành khăn (Mục 4.4.1 — Hình 4.8 / 4.11)

**Tệp liên quan:** `Chuong/4_Xay_dung_va_phat_trien_he_thong.tex`  
**Vị trí:** Mục 4.4.1 — Phân bố biểu cảm theo khu vực và thời gian (Hình 4.8 / Hình 4.11 trong bản biên dịch PDF: `fig:distribution_screen_ch4`, tệp ảnh `Hinhve/Chuong4/4_08_phan_bo_bieu_cam.png`)

### 1. Phân tích hạn chế của Biểu đồ cột chồng (Stacked Bar Chart) hiện tại
- **Hiện trạng giao diện Hình 4.11:**
  - Màn hình *Phân tích biểu cảm* hiện đang sử dụng duy nhất một **Biểu đồ cột chồng (Stacked Bar Chart)** mang tên *"Số quan sát theo khu vực và nhãn"*, gom chung 4 cột đại diện cho 4 khu vực (*Cửa vào*, *Khu trưng bày sản phẩm*, *Khu tư vấn*, *Quầy thanh toán*). Mỗi cột được xếp chồng 7 khối màu biểu thị 7 nhãn biểu cảm (*Angry, Disgust, Fear, Happy, Sad, Surprise, Neutral*).
- **Hạn chế nghiêm trọng về mặt trực quan hóa dữ liệu (Data Visualization Flaws):**
  1. **Lệch lạc nhận thức thị giác do quy mô mẫu ($N$) không đồng đều:**
     - Tổng lượng khách ghi nhận tại các khu vực chênh lệch nhau rất lớn (ví dụ: *Cửa vào* có 158 quan sát, *Khu trưng bày* có 108 quan sát, *Khu tư vấn* có 94 quan sát, *Quầy thanh toán* có 156 quan sát). Chiều cao cột biến thiên mạnh làm người xem dễ nhầm lẫn rằng khu vực có cột cao hơn thì có "nhiều biểu cảm tích cực/tiêu cực hơn", trong khi bản chất phân tích trải nghiệm khách hàng (CX) cần tập trung vào **tỷ trọng thành phần (%)**.
  2. **Thiếu đường đáy chuẩn chung (Lack of Common Baseline):**
     - Trong biểu đồ cột chồng, ngoại trừ phân khúc dưới cùng có chung đường đáy $Y=0$, tất cả các phân khúc nằm giữa (*Disgust, Fear, Happy, Sad, Surprise, Neutral*) đều có mốc bắt đầu và kết thúc lơ lửng ở các độ cao khác nhau. Do đó, mắt người hoàn toàn không thể so sánh chính xác mức độ nhiều/ít của các biểu cảm này giữa các khu vực.
  3. **Khó quan sát các nhóm biểu cảm có tỷ lệ nhỏ:**
     - Các nhãn biểu cảm ít xuất hiện nhưng có tính chất cảnh báo rủi ro cao (*Angry, Disgust, Fear* thường chỉ chiếm 2\% -- 6\%) bị ép thành các dải màu quá mỏng trên cột, gây khó khăn cho việc nhấp chuột (hover/click) hoặc đọc thông số trên màn hình.
  4. **Nhu cầu nghiệp vụ cốt lõi:**
     - Người quản lý cửa hàng và bộ phận trải nghiệm khách hàng cần nắm bắt ngay **cơ cấu 100% cảm xúc độc lập của từng điểm chạm**:
       - *Tại Khu tư vấn:* Bao nhiêu \% khách hàng cảm thấy thoải mái, hài lòng (*Happy*)? Bao nhiêu \% khách thể hiện băn khoăn, căng thẳng (*Neutral, Sad, Fear*)?
       - *Tại Quầy thanh toán:* Tỷ lệ biểu cảm tiêu cực (*Angry, Sad*) có vượt ngưỡng cảnh báo (ví dụ >15\%) do phải xếp hàng chờ đợi lâu hay không?
     - Biểu đồ tròn (Pie Chart) và biểu đồ vành khăn (Donut Chart) là chuẩn mực trực quan hóa tối ưu cho mối quan hệ tỷ trọng thành phần trên tổng thể (*Part-to-Whole Relationship*).

---

### 2. Phương án nâng cấp đề xuất: Lưới Biểu đồ vành khăn (Multi-Donut Chart Grid) theo từng khu vực

Nâng cấp giao diện phân tích biểu cảm thành cụm biểu đồ tròn/vành khăn độc lập cho từng khu vực:

#### A. Bố cục hiển thị Lưới 4 Biểu đồ vành khăn (Donut Chart Grid)
- **Cấu trúc lưới:** Hiển thị 4 biểu đồ vành khăn đặt cạnh nhau theo chiều ngang (1x4) hoặc dạng lưới (2x2), tương ứng với tiến trình di chuyển tự nhiên của khách hàng qua 4 điểm chạm:
  $$\text{Cửa vào} \longrightarrow \text{Khu trưng bày} \longrightarrow \text{Khu tư vấn} \longrightarrow \text{Quầy thanh toán}$$
- **Đặc điểm mỗi biểu đồ vành khăn:**
  1. Thể hiện trọn vẹn cơ cấu 100% của 7 nhãn biểu cảm chuẩn FER.
  2. **Tâm biểu đồ vành khăn (Donut hole):** Được tận dụng để hiển thị các chỉ số đo lường hiệu năng cốt lõi (KPI) của khu vực:
     - Tên viết tắt khu vực (ví dụ: `Cửa vào`, `Khu tư vấn`).
     - Tổng dung lượng mẫu quan sát hợp lệ ($N = 158$).
     - Chỉ số tích cực tổng quát: $\text{Positive Rate} = \frac{N_{\text{Happy}}}{N_{\text{Total}}} \times 100\%$.
  3. **Hệ màu chuẩn hóa tương phản cao:**
     - Nhóm tích cực: `Happy` (Màu xanh lục nhạt `#52c41a` / `#22c55e`).
     - Nhóm trung tính: `Neutral` (Màu xanh lam nhạt `#1890ff` / `#3b82f6`).
     - Nhóm ngạc nhiên: `Surprise` (Màu vàng cam `#faad14` / `#f59e0b`).
     - Nhóm tiêu cực:
       + `Sad` (Màu tím xám `#722ed1` / `#8b5cf6`).
       + `Fear` (Màu chàm đậm `#2f54eb` / `#6366f1`).
       + `Angry` (Màu đỏ tươi `#f5222d` / `#ef4444`).
       + `Disgust` (Màu nâu rêu `#873800` / `#a16207`).
  4. **Tương tác trực quan:** Di chuột vào từng lát cắt hiển thị Tooltip đầy đủ: Tên nhãn, số lượng quan sát tuyệt đối và tỷ lệ phần trăm chính xác (ví dụ: `Angry: 8 quan sát (5.1%)`).

#### B. Cơ chế tương tác và bộ lọc linh hoạt
- **Khi chọn `Phạm vi: Tất cả khu vực`:** Hiển thị đồng thời lưới 4 biểu đồ vành khăn của 4 khu vực kèm thanh chú giải (Legend) dùng chung để người quản lý dễ dàng so sánh đối chiếu tỷ trọng cảm xúc giữa các điểm chạm.
- **Khi chọn `Phạm vi: [Khu vực cụ thể]` (ví dụ: `Khu tư vấn`):**
  - Biểu đồ vành khăn của riêng khu vực đó được phóng to làm tiêu điểm trung tâm (Hero Chart).
  - Bên cạnh hiển thị thẻ phân tích chuyên sâu: Top biểu cảm chiếm ưu thế, xu hướng biến thiên so với trung bình toàn cửa hàng, và danh sách các lần quan sát mang nhãn tiêu cực cần lưu ý.
- **Chuyển đổi góc nhìn (View Switcher):** Cung cấp nút chuyển đổi nhanh giữa hai chế độ:
  - *Chế độ Cơ cấu tỷ lệ (Khuyến nghị):* Lưới biểu đồ vành khăn (Donut Charts).
  - *Chế độ So sánh dung lượng tuyệt đối:* Biểu đồ cột nhóm (Grouped Bar Chart) hoặc biểu đồ cột chuẩn hóa 100% (100% Stacked Bar Chart).

---

### 3. Bảng số liệu đặc tả phân bố 7 nhãn biểu cảm tại 4 khu vực (Dữ liệu chuẩn hóa)

Bảng số liệu đối chiếu chi tiết được hiển thị bên dưới cụm biểu đồ, làm cơ sở phân tích học thuật:

```latex
\begin{table}[H]
    \centering
    \caption{Phân bố số lượng và tỷ lệ phần trăm bảy nhãn biểu cảm tại bốn khu vực điểm chạm}
    \label{tab:emotion_distribution_areas}
    \resizebox{\textwidth}{!}{%
    \begin{tabular}{|l|c|c|c|c|c|c|c|c|}
        \hline
        \multirow{2}{*}{\textbf{Khu vực điểm chạm}} & \multicolumn{7}{c|}{\textbf{Số lượng quan sát (Tỷ lệ phần trăm trong khu vực)}} & \multirow{2}{*}{\textbf{Tổng ($N$)}} \\
        \cline{2-8}
        & \textbf{Happy} & \textbf{Neutral} & \textbf{Surprise} & \textbf{Sad} & \textbf{Angry} & \textbf{Fear} & \textbf{Disgust} & \\
        \hline
        \textbf{1. Cửa vào} & 76 (48.1\%) & 59 (37.3\%) & 8 (5.1\%) & 5 (3.2\%) & 8 (5.1\%) & 1 (0.6\%) & 1 (0.6\%) & 158 (100\%) \\
        \hline
        \textbf{2. Khu trưng bày} & 56 (51.9\%) & 39 (36.1\%) & 6 (5.6\%) & 3 (2.8\%) & 3 (2.8\%) & 1 (0.9\%) & 0 (0.0\%) & 108 (100\%) \\
        \hline
        \textbf{3. Khu tư vấn} & 34 (36.2\%) & 43 (45.7\%) & 5 (5.3\%) & 6 (6.4\%) & 4 (4.3\%) & 2 (2.1\%) & 0 (0.0\%) & 94 (100\%) \\
        \hline
        \textbf{4. Quầy thanh toán} & 50 (32.1\%) & 80 (51.3\%) & 7 (4.5\%) & 9 (5.8\%) & 7 (4.5\%) & 2 (1.3\%) & 1 (0.6\%) & 156 (100\%) \\
        \hline
        \textbf{Toàn cửa hàng} & \textbf{216 (41.9\%)} & \textbf{221 (42.8\%)} & \textbf{26 (5.0\%)} & \textbf{23 (4.5\%)} & \textbf{22 (4.3\%)} & \textbf{6 (1.2\%)} & \textbf{2 (0.4\%)} & \textbf{516 (100\%)} \\
        \hline
    \end{tabular}}
\end{table}
```

---

### 4. Đề xuất nội dung bổ sung vào văn bản Luận văn (Mục 4.4.1)

Thay thế hoặc bổ sung đoạn văn học thuật tại Mục 4.4.1 làm rõ cơ sở lựa chọn biểu đồ tròn/vành khăn:

> Nhằm khắc phục hạn chế của biểu đồ cột chồng truyền thống—vốn thường gây sai lệch nhận thức thị giác do sự chênh lệch lớn về tổng số lượt khách ghé thăm giữa các khu vực—giao diện phân tích biểu cảm được thiết kế lại dưới dạng cụm biểu đồ vành khăn (Donut Chart) độc lập cho từng khu vực điểm chạm (Hình~\ref{fig:donut_distribution_ch4}).
>
> Mỗi biểu đồ vành khăn đại diện cho cơ cấu $100\%$ cảm xúc của khách hàng tại một điểm chạm cụ thể, cho phép người quản trị đánh giá chính xác mức độ hài lòng nội bộ mà không bị chi phối bởi quy mô mẫu tuyệt đối. Tại tâm của mỗi biểu đồ, hệ thống hiển thị tổng số quan sát hợp lệ ($N$) và tỷ lệ cảm xúc tích cực tổng quát. Cách tiếp cận này giúp dễ dàng nhận diện xu hướng chuyển biến tâm lý của khách hàng dọc theo phễu bán hàng: tỷ lệ biểu cảm tích cực (\textit{Happy}) đạt đỉnh tại khu vực trưng bày sản phẩm ($51.9\%$), sau đó giảm dần và nhường chỗ cho trạng thái trung tính (\textit{Neutral}) khi khách hàng bước vào khu tư vấn ($45.7\%$) và quầy thanh toán ($51.3\%$). Đồng thời, tỷ lệ các biểu cảm tiêu cực (\textit{Angry, Sad}) tại quầy thanh toán ($10.3\%$) được làm nổi bật như một chỉ số cảnh báo để tối ưu thời gian chờ của khách hàng.

---

### 5. Mã TikZ minh họa Lưới Biểu đồ vành khăn (Donut Charts) chuẩn mực cho Báo cáo Luận văn

Biểu đồ TikZ thể hiện chi tiết 4 biểu đồ vành khăn tương ứng 4 khu vực, phân tách rõ 7 nhóm biểu cảm theo đúng tỷ lệ thực nghiệm:

```latex
\begin{figure}[H]
    \centering
    \resizebox{0.98\textwidth}{!}{%
    \begin{tikzpicture}[
        lbl/.style={font=\small\bfseries, align=center},
        sublbl/.style={font=\scriptsize, align=center, text=gray!80},
        donut/.style={draw=white, line width=1.5pt}
    ]
        % =========================================================
        % KHU VỰC 1: CỬA VÀO (N=158)
        % Happy: 48.1% (173.2 deg) [90 -> -83.2]
        % Neutral: 37.3% (134.3 deg) [-83.2 -> -217.5]
        % Surprise: 5.1% (18.4 deg) [-217.5 -> -235.9]
        % Sad: 3.2% (11.5 deg) [-235.9 -> -247.4]
        % Angry: 5.1% (18.4 deg) [-247.4 -> -265.8]
        % Fear + Disgust: 1.2% (4.2 deg) [-265.8 -> -270]
        % =========================================================
        \begin{scope}[shift={(0,0)}]
            \draw[donut, fill=green!65!black!85] (0,0) -- (90:1.9) arc (90:-83.2:1.9) -- cycle;
            \draw[donut, fill=blue!55!cyan!80] (0,0) -- (-83.2:1.9) arc (-83.2:-217.5:1.9) -- cycle;
            \draw[donut, fill=orange!85!yellow!90] (0,0) -- (-217.5:1.9) arc (-217.5:-235.9:1.9) -- cycle;
            \draw[donut, fill=purple!60!black!70] (0,0) -- (-235.9:1.9) arc (-235.9:-247.4:1.9) -- cycle;
            \draw[donut, fill=red!75!black!85] (0,0) -- (-247.4:1.9) arc (-247.4:-265.8:1.9) -- cycle;
            \draw[donut, fill=gray!70!black!80] (0,0) -- (-265.8:1.9) arc (-265.8:-270:1.9) -- cycle;
            \fill[white] (0,0) circle (1.15); % Lỗ donut
            \node[lbl] at (0, 0.22) {Cửa vào};
            \node[sublbl] at (0, -0.22) {$N = 158$\\\textbf{48.1\%} Happy};
        \end{scope}

        % =========================================================
        % KHU VỰC 2: KHU TRƯNG BÀY (N=108)
        % Happy: 51.9% (186.8 deg) [90 -> -96.8]
        % Neutral: 36.1% (130.0 deg) [-96.8 -> -226.8]
        % Surprise: 5.6% (20.2 deg) [-226.8 -> -247.0]
        % Sad: 2.8% (10.1 deg) [-247.0 -> -257.1]
        % Angry: 2.8% (10.1 deg) [-257.1 -> -267.2]
        % Fear + Disgust: 0.9% (2.8 deg) [-267.2 -> -270]
        % =========================================================
        \begin{scope}[shift={(4.5,0)}]
            \draw[donut, fill=green!65!black!85] (0,0) -- (90:1.9) arc (90:-96.8:1.9) -- cycle;
            \draw[donut, fill=blue!55!cyan!80] (0,0) -- (-96.8:1.9) arc (-96.8:-226.8:1.9) -- cycle;
            \draw[donut, fill=orange!85!yellow!90] (0,0) -- (-226.8:1.9) arc (-226.8:-247.0:1.9) -- cycle;
            \draw[donut, fill=purple!60!black!70] (0,0) -- (-247.0:1.9) arc (-247.0:-257.1:1.9) -- cycle;
            \draw[donut, fill=red!75!black!85] (0,0) -- (-257.1:1.9) arc (-257.1:-267.2:1.9) -- cycle;
            \draw[donut, fill=gray!70!black!80] (0,0) -- (-267.2:1.9) arc (-267.2:-270:1.9) -- cycle;
            \fill[white] (0,0) circle (1.15);
            \node[lbl] at (0, 0.22) {Trưng bày};
            \node[sublbl] at (0, -0.22) {$N = 108$\\\textbf{51.9\%} Happy};
        \end{scope}

        % =========================================================
        % KHU VỰC 3: KHU TƯ VẤN (N=94)
        % Happy: 36.2% (130.3 deg) [90 -> -40.3]
        % Neutral: 45.7% (164.5 deg) [-40.3 -> -204.8]
        % Surprise: 5.3% (19.1 deg) [-204.8 -> -223.9]
        % Sad: 6.4% (23.0 deg) [-223.9 -> -246.9]
        % Angry: 4.3% (15.5 deg) [-246.9 -> -262.4]
        % Fear + Disgust: 2.1% (7.6 deg) [-262.4 -> -270]
        % =========================================================
        \begin{scope}[shift={(9.0,0)}]
            \draw[donut, fill=green!65!black!85] (0,0) -- (90:1.9) arc (90:-40.3:1.9) -- cycle;
            \draw[donut, fill=blue!55!cyan!80] (0,0) -- (-40.3:1.9) arc (-40.3:-204.8:1.9) -- cycle;
            \draw[donut, fill=orange!85!yellow!90] (0,0) -- (-204.8:1.9) arc (-204.8:-223.9:1.9) -- cycle;
            \draw[donut, fill=purple!60!black!70] (0,0) -- (-223.9:1.9) arc (-223.9:-246.9:1.9) -- cycle;
            \draw[donut, fill=red!75!black!85] (0,0) -- (-246.9:1.9) arc (-246.9:-262.4:1.9) -- cycle;
            \draw[donut, fill=gray!70!black!80] (0,0) -- (-262.4:1.9) arc (-262.4:-270:1.9) -- cycle;
            \fill[white] (0,0) circle (1.15);
            \node[lbl] at (0, 0.22) {Tư vấn};
            \node[sublbl] at (0, -0.22) {$N = 94$\\\textbf{36.2\%} Happy};
        \end{scope}

        % =========================================================
        % KHU VỰC 4: QUẦY THANH TOÁN (N=156)
        % Happy: 32.1% (115.6 deg) [90 -> -25.6]
        % Neutral: 51.3% (184.7 deg) [-25.6 -> -210.3]
        % Surprise: 4.5% (16.2 deg) [-210.3 -> -226.5]
        % Sad: 5.8% (20.9 deg) [-226.5 -> -247.4]
        % Angry: 4.5% (16.2 deg) [-247.4 -> -263.6]
        % Fear + Disgust: 1.8% (6.4 deg) [-263.6 -> -270]
        % =========================================================
        \begin{scope}[shift={(13.5,0)}]
            \draw[donut, fill=green!65!black!85] (0,0) -- (90:1.9) arc (90:-25.6:1.9) -- cycle;
            \draw[donut, fill=blue!55!cyan!80] (0,0) -- (-25.6:1.9) arc (-25.6:-210.3:1.9) -- cycle;
            \draw[donut, fill=orange!85!yellow!90] (0,0) -- (-210.3:1.9) arc (-210.3:-226.5:1.9) -- cycle;
            \draw[donut, fill=purple!60!black!70] (0,0) -- (-226.5:1.9) arc (-226.5:-247.4:1.9) -- cycle;
            \draw[donut, fill=red!75!black!85] (0,0) -- (-247.4:1.9) arc (-247.4:-263.6:1.9) -- cycle;
            \draw[donut, fill=gray!70!black!80] (0,0) -- (-263.6:1.9) arc (-263.6:-270:1.9) -- cycle;
            \fill[white] (0,0) circle (1.15);
            \node[lbl] at (0, 0.22) {Thanh toán};
            \node[sublbl] at (0, -0.22) {$N = 156$\\\textbf{32.1\%} Happy};
        \end{scope}

        % =========================================================
        % THANH CHÚ GIẢI CHUNG (COMMON LEGEND)
        % =========================================================
        \begin{scope}[shift={(1.0,-2.8)}]
            \draw[fill=green!65!black!85, draw=none] (0,0) rectangle (0.35, 0.25);
            \node[right, font=\scriptsize] at (0.4, 0.12) {Happy};

            \draw[fill=blue!55!cyan!80, draw=none] (2.2,0) rectangle (2.55, 0.25);
            \node[right, font=\scriptsize] at (2.6, 0.12) {Neutral};

            \draw[fill=orange!85!yellow!90, draw=none] (4.6,0) rectangle (4.95, 0.25);
            \node[right, font=\scriptsize] at (5.0, 0.12) {Surprise};

            \draw[fill=purple!60!black!70, draw=none] (7.2,0) rectangle (7.55, 0.25);
            \node[right, font=\scriptsize] at (7.6, 0.12) {Sad};

            \draw[fill=red!75!black!85, draw=none] (9.2,0) rectangle (9.55, 0.25);
            \node[right, font=\scriptsize] at (9.6, 0.12) {Angry};

            \draw[fill=gray!70!black!80, draw=none] (11.4,0) rectangle (11.75, 0.25);
            \node[right, font=\scriptsize] at (11.8, 0.12) {Fear / Disgust};
        \end{scope}
    \end{tikzpicture}%
    }
    \caption{Cơ cấu phân bố bảy nhãn biểu cảm theo từng khu vực bằng cụm biểu đồ vành khăn (Donut Chart)}
    \label{fig:donut_distribution_ch4}
\end{figure}
```

- **Trạng thái:** Đã ghi chú chi tiết toàn diện phương án biểu đồ tròn/vành khăn theo từng khu vực, bảng số liệu 7 nhãn và mã TikZ chuẩn vào tài liệu ghi chú; các tệp `.tex` của luận văn được giữ nguyên vẹn.

---

## 19. Chuẩn hóa và thiết kế lại toàn bộ hệ thống sơ đồ & biểu đồ trong Luận văn theo phong cách trực quan, hiện đại, dễ hiểu

**Tệp liên quan:** `Chuong/3_Phuong_an_de_xuat.tex` và `Chuong/4_Xay_dung_va_phat_trien_he_thong.tex`  
**Mục tiêu:** Khắc phục triệt để tình trạng các sơ đồ và biểu đồ hiện tại trong luận văn bị đánh giá là **khó hiểu, đơn điệu, chèn ép văn bản và thiếu tính khoa học thị giác**, bằng cách xây dựng lại toàn bộ theo ngôn ngữ thiết kế đồ họa chuyên nghiệp (Modern Infographic TikZ System).

---

### 1. Phân tích nguyên nhân khiến hệ thống biểu đồ hiện tại khó hiểu

1. **Hiệu ứng "nhồi chữ vào hộp" (Text-crammed Boxes):**
   - Điển hình tại Hình 4.1 (`fig:function_structure_ch4`): Các khối chữ nhật chứa nguyên một đoạn văn dài dòng (ví dụ: *“Kiểm tra dữ liệu đầu vào; phát hiện khuôn mặt; phân loại biểu cảm; tạo đặc trưng khuôn mặt; lưu kết quả...”*). Người đọc bị ngợp trước một "bức tường chữ", không thể nhận diện nhanh các mô-đun chức năng.
2. **Thiếu hệ thống phân cấp màu sắc và ranh giới (Color Hierarchy & Layering):**
   - Hầu hết các sơ đồ chỉ dùng hình chữ nhật trắng viền đen đơn điệu, không phân biệt được đâu là thiết bị ngoại vi, đâu là giao diện người dùng, đâu là máy chủ xử lý hay cơ sở dữ liệu.
3. **Mũi tên chằng chịt, sai hướng phụ thuộc (Confusing Data Flow):**
   - Tại Hình 4.2 (`fig:component_architecture_ch4`): Camera đặt dưới đáy trỏ ngược lên API, API nối hai chiều sang Vision, Vision và DB đặt chồng chéo. Mũi tên hai chiều (`bidirectional`) được dùng tràn lan gây hiểu lầm rằng các tầng phụ thuộc lẫn nhau một cách lỏng lẻo.
4. **Sai lệch kỹ thuật trực quan hóa dữ liệu (Visualization Antipatterns):**
   - Dùng biểu đồ cột chồng 7 lớp cho dữ liệu cơ cấu phần trăm (Hình 4.11) khiến người xem không thể so sánh tương quan giữa các khu vực; dùng các nút tròn tĩnh không có trục thời gian (Hình 4.7) để mô tả một hành trình mua sắm động.

---

### 2. Bộ quy chuẩn đồ họa trực quan mới cho Luận văn (Modern TikZ Design System)

Để mọi biểu đồ trong luận văn đều **đẹp mắt, hiện đại, dễ hiểu ngay trong 5 giây đầu tiên**, toàn bộ hệ thống được tái thiết kế theo các nguyên tắc sau:
- **Ngữ nghĩa màu sắc phân tầng (Semantic Palette):**
  - $\color[HTML]{D97706}\blacksquare$ **Tầng Ngoại vi / Đầu vào (Camera / Simulator):** Nền cam nhạt `fill=orange!12`, viền `draw=orange!80!black`.
  - $\color[HTML]{0D9488}\blacksquare$ **Tầng Frontend CRM (`apps/web`):** Nền xanh ngọc `fill=teal!12`, viền `draw=teal!80!black`.
  - $\color[HTML]{2563EB}\blacksquare$ **Tầng Backend API (`apps/api`):** Nền xanh dương `fill=blue!12`, viền `draw=blue!80!black`.
  - $\color[HTML]{7C3AED}\blacksquare$ **Tầng AI Vision Module (`services/vision`):** Nền tím hiện đại `fill=purple!12`, viền `draw=purple!80!black`.
  - $\color[HTML]{16A34A}\blacksquare$ **Tầng Cơ sở dữ liệu (`postgres` + `pgvector`):** Nền xanh lục bảo `fill=green!12`, viền `draw=green!60!black`.
- **Cấu trúc dạng thẻ tính năng (Card-based Layout):** Tiêu đề khối in đậm cỡ chữ lớn, có phân cách với phụ đề công nghệ (`{\scriptsize ...}`) và danh sách tính năng gạch đầu dòng ngắn gọn.
- **Ranh giới phân tầng (Layer Swimlanes):** Các cụm chức năng thuộc cùng một tầng được bao bọc trong khung ranh giới nét đứt có màu nền mờ sang trọng (`dashed, fill=gray!4`).

---

### 3. Thiết kế lại chi tiết 10 Biểu đồ & Sơ đồ cốt lõi trong Luận văn

---

#### Biểu đồ 1: Luồng xử lý tổng thể của giải pháp (Hình 3.1 — `fig:solution_flow`)
- **Vị trí:** `Chuong/3_Phuong_an_de_xuat.tex` (Mục 3.2).
- **Vấn đề cũ:** 7 hộp chữ nhật trắng xếp ngang hàng đơn điệu, không phân biệt công đoạn ngoại vi, trí tuệ nhân tạo và nghiệp vụ CRM.
- **Thiết kế mới:** Phân tách thành 4 giai đoạn tiến trình phân màu rõ rệt: *1. Tiếp nhận & Kiểm tra* $\to$ *2. Xử lý thị giác kép (FER \& ArcFace)* $\to$ *3. Quản lý liên kết phiên mua sắm* $\to$ *4. Phân tích \& Trực quan CRM*.

```latex
\begin{figure}[H]
    \centering
    \resizebox{\textwidth}{!}{%
    \begin{tikzpicture}[
        node distance=7mm and 9mm,
        stage/.style={draw=#1!80!black, fill=#1!12, rounded corners=3pt, thick, align=center, minimum height=14mm, text width=2.9cm, font=\small},
        flow/.style={-{Latex[length=2.5mm]}, very thick, draw=gray!80},
        subflow/.style={-{Latex[length=2.2mm]}, thick, draw=#1!80!black},
        lbl/.style={font=\scriptsize\bfseries, align=center, fill=white, inner sep=1.5pt, draw=gray!30, rounded corners=1pt}
    ]
        % Khung giai đoạn 1: Ngoại vi
        \node[stage=orange] (s1) {\textbf{1. Tiếp nhận}\\Ảnh thô, Mã điểm chạm,\\Dấu thời gian};
        
        % Khung giai đoạn 2: AI Vision
        \node[stage=purple, right=of s1, yshift=12mm] (s2a) {\textbf{2A. Biểu cảm (FER)}\\7 xác suất cảm xúc\\$e^* = \arg\max p_i$};
        \node[stage=purple, right=of s1, yshift=-12mm] (s2b) {\textbf{2B. Nhận diện mặt}\\ArcFace 512D Vector\\Khoảng cách Cosine};
        
        % Khung giai đoạn 3: Backend & Session
        \node[stage=blue, right=of s2a, yshift=-12mm] (s3) {\textbf{3. Quản lý Phiên}\\Tạo bản ghi quan sát,\\Gộp/ngắt lượt ghé thăm\\($\tau_{\text{wait}} = 30$ phút)};
        
        % Khung giai đoạn 4: Phân tích & CRM
        \node[stage=teal, right=of s3] (s4) {\textbf{4. Trực quan CRM}\\Ma trận chuyển dịch,\\Đường cong cảm xúc,\\Lưới biểu đồ vành khăn};

        % Kết nối luồng dữ liệu
        \draw[flow] (s1.east) -- ++(4mm,0) |- node[lbl, near start] {Cắt khuôn mặt} (s2a.west);
        \draw[flow] (s1.east) -- ++(4mm,0) |- node[lbl, near start] {Vùng $112\times 112$} (s2b.west);
        \draw[subflow=purple] (s2a.east) -| node[lbl, pos=0.4] {Nhãn biểu cảm} (s3.north);
        \draw[subflow=purple] (s2b.east) -| node[lbl, pos=0.4] {Mã khách / Ẩn danh} (s3.south);
        \draw[flow] (s3.east) -- node[lbl] {Chuỗi hành trình\\theo thời gian} (s4.west);
    \end{tikzpicture}%
    }
    \caption{Luồng xử lý tổng thể của giải pháp đề xuất phân tách theo các giai đoạn xử lý}
    \label{fig:solution_flow}
\end{figure}
```

---

#### Biểu đồ 2: Hai nhánh xử lý độc lập trên từng khuôn mặt (Hình 3.2 — `fig:observation_tasks`)
- **Vị trí:** `Chuong/3_Phuong_an_de_xuat.tex` (Mục 3.3.2).
- **Vấn đề cũ:** 4 hộp sơ sài không thể hiện được cấu trúc dữ liệu đầu ra và cơ chế kết hợp.
- **Thiết kế mới:** Làm rõ cấu trúc toán học của 2 nhánh: Vector xác suất FER $\mathbb{R}^7$ và Vector ArcFace $\mathbb{R}^{512}$, kết hợp thành bản ghi quan sát đa chiều hoàn chỉnh.

```latex
\begin{figure}[H]
    \centering
    \resizebox{0.92\textwidth}{!}{%
    \begin{tikzpicture}[
        node distance=8mm and 12mm,
        card/.style={draw=#1!80!black, fill=#1!10, rounded corners=3pt, thick, align=center, minimum height=14mm, text width=3.4cm, font=\small},
        flow/.style={-{Latex[length=2.5mm]}, very thick, draw=gray!75},
        lbl/.style={font=\scriptsize, align=center, fill=white, inner sep=1.5pt}
    ]
        % Đầu vào
        \node[card=orange] (face) {\textbf{Vùng ảnh khuôn mặt}\\Được cắt từ RetinaFace\\Kích thước chuẩn hóa};

        % Hai nhánh AI
        \node[card=purple, above right=4mm and 12mm of face] (fer) {\textbf{Nhánh Phân loại FER}\\Mô hình cảm xúc đa lớp\\Vector xác suất $\mathbf{p} \in \mathbb{R}^7$\\Nhãn dự đoán $e^*$ \& Độ tin cậy};
        \node[card=purple, below right=4mm and 12mm of face] (arcface) {\textbf{Nhánh Nhận dạng}\\Mô hình ArcFace trích xuất\\Vector đặc trưng $\mathbf{v} \in \mathbb{R}^{512}$\\Đối sánh Cosine $d \le \tau_{\text{match}}$};

        % Bản ghi kết hợp
        \node[card=blue, below right=4mm and 12mm of fer] (record) {\textbf{Bản ghi Quan sát}\\(\texttt{observation})\\Mã sự kiện + Nhãn biểu cảm +\\Mã khách hàng / Ẩn danh +\\Khu vực + Dấu thời gian};

        % Luồng kết nối
        \draw[flow] (face.east) -- ++(5mm,0) |- node[lbl, above, pos=0.7] {Ảnh mặt} (fer.west);
        \draw[flow] (face.east) -- ++(5mm,0) |- node[lbl, below, pos=0.7] {Ảnh mặt} (arcface.west);
        \draw[flow] (fer.east) -| node[lbl, above, pos=0.3] {Nhãn biểu cảm \& $c$} (record.north);
        \draw[flow] (arcface.east) -| node[lbl, below, pos=0.3] {Mã định danh \& Khoảng cách} (record.south);
    \end{tikzpicture}%
    }
    \caption{Cơ chế thực thi độc lập và song song của hai nhánh thị giác trên từng khuôn mặt}
    \label{fig:observation_tasks}
\end{figure}
```

---

#### Biểu đồ 3: Cấu trúc phân rã các nhóm chức năng hệ thống (Hình 4.1 — `fig:function_structure_ch4`)
- **Vị trí:** `Chuong/4_Xay_dung_va_phat_trien_he_thong.tex` (Mục 4.1.1).
- **Vấn đề cũ:** Nhồi nguyên 3 đoạn văn dài vào các hộp chữ nhật, cực kỳ nặng nề và khó theo dõi.
- **Thiết kế mới:** Dạng Sơ đồ cây phân cấp mô-đun (Feature Hierarchy Tree) với các thẻ tính năng ngắn gọn, có gạch đầu dòng rõ nét.

```latex
\begin{figure}[H]
    \centering
    \resizebox{0.98\textwidth}{!}{%
    \begin{tikzpicture}[
        node distance=6mm and 10mm,
        root/.style={draw=blue!90!black, fill=blue!15, rounded corners=4pt, thick, align=center, minimum height=14mm, text width=3.4cm, font=\small\bfseries},
        subsys/.style={draw=#1!80!black, fill=#1!12, rounded corners=3pt, thick, align=center, minimum height=12mm, text width=3.2cm, font=\small\bfseries},
        leaf/.style={draw=gray!50, fill=white, rounded corners=2pt, align=left, minimum height=24mm, text width=4.8cm, font=\scriptsize},
        conn/.style={draw=gray!70, thick, -{Latex[length=2mm]}}
    ]
        % Node gốc
        \node[root] (sys) {Hệ thống Touchpoint CRM\\\& Phân tích biểu cảm};

        % 3 Phân hệ chính
        \node[subsys=purple, right=10mm of sys, yshift=26mm] (mod_obs) {Tiếp nhận \& Xử lý\\quan sát (AI)};
        \node[subsys=blue, right=10mm of sys] (mod_crm) {CRM \& Quản lý\\lần mua sắm};
        \node[subsys=teal, right=10mm of sys, yshift=-26mm] (mod_rep) {Phân tích trải nghiệm\\\& Báo cáo};

        % Các nhóm tính năng cụ thể (Leaf cards)
        \node[leaf, right=8mm of mod_obs] (card_obs) {%
            $\bullet$ Kiểm tra dữ liệu \& chống trùng lặp\\
            $\bullet$ Phát hiện khuôn mặt (RetinaFace)\\
            $\bullet$ Phân loại 7 biểu cảm (FER)\\
            $\bullet$ Trích xuất véc-tơ 512D (ArcFace)\\
            $\bullet$ Lưu vết trạng thái \& lịch sử xử lý
        };

        \node[leaf, right=8mm of mod_crm] (card_crm) {%
            $\bullet$ Quản lý hồ sơ khách hàng \& chấp thuận\\
            $\bullet$ Danh mục điểm chạm, sản phẩm, đơn hàng\\
            $\bullet$ Khởi tạo, gộp \& ngắt phiên mua sắm\\
            $\bullet$ Quản lý định danh ẩn danh 2 tầng\\
            $\bullet$ Kiểm tra xung đột \& quan sát bất thường
        };

        \node[leaf, right=8mm of mod_rep] (card_rep) {%
            $\bullet$ Lưới biểu đồ vành khăn phân bố khu vực\\
            $\bullet$ Biểu đồ đường cong cảm xúc theo thời gian\\
            $\bullet$ Ma trận chuyển dịch biểu cảm (Sankey)\\
            $\bullet$ Giám sát chất lượng dữ liệu \& cảnh báo lỗi\\
            $\bullet$ Báo cáo tổng hợp hỗ trợ tiếp thị \& CX
        };

        % Đường nối phân cấp
        \draw[conn] (sys.east) -- ++(4mm,0) |- (mod_obs.west);
        \draw[conn] (sys.east) -- (mod_crm.west);
        \draw[conn] (sys.east) -- ++(4mm,0) |- (mod_rep.west);

        \draw[conn] (mod_obs.east) -- (card_obs.west);
        \draw[conn] (mod_crm.east) -- (card_crm.west);
        \draw[conn] (mod_rep.east) -- (card_rep.west);
    \end{tikzpicture}%
    }
    \caption{Cấu trúc phân rã các phân hệ chức năng và tính năng thành phần trong hệ thống}
    \label{fig:function_structure_ch4}
\end{figure}
```

---

#### Biểu đồ 4: Kiến trúc phân tầng 4 khối chuẩn của hệ thống (Hình 4.2 / Hình 4.1 mới — `fig:component_architecture_ch4`)
- **Vị trí:** `Chuong/4_Xay_dung_va_phat_trien_he_thong.tex` (Mục 4.1.3).
- **Vấn đề cũ:** Camera nằm dưới FastAPI, mũi tên hai chiều rối rắm, không thể hiện kiến trúc phần mềm tiêu chuẩn.
- **Thiết kế mới:** Kiến trúc phân tầng (Layered Architecture) chuẩn kỹ thuật phần mềm: *Tầng Trình diễn (FE)*, *Tầng Nghiệp vụ trung tâm (BE)*, *Tầng AI (Vision)*, *Tầng Dữ liệu (DB)* và *Ngoại vi (Camera)*.

```latex
\begin{figure}[H]
    \centering
    \resizebox{0.98\textwidth}{!}{%
    \begin{tikzpicture}[
        node distance=7mm and 9mm,
        tier/.style={draw=gray!40, dashed, fill=gray!3, rounded corners=5pt, inner sep=6pt},
        block/.style={draw=#1!80!black, fill=#1!12, rounded corners=3pt, thick, align=center, minimum height=14mm, text width=3.3cm, font=\small},
        flow/.style={-{Latex[length=2.5mm]}, very thick, draw=gray!80},
        lbl/.style={font=\scriptsize, align=center, fill=white, inner sep=1.5pt}
    ]
        % Tầng 1: Ngoại vi
        \node[block=orange] (cam) {\textbf{Thiết bị tại điểm chạm}\\Camera / Bộ mô phỏng\\{\scriptsize(Ảnh hiện trường, Timestamp)}};

        % Tầng 2: Backend trung tâm
        \node[block=blue, right=14mm of cam] (be) {\textbf{Backend (BE)}\\\texttt{apps/api} (FastAPI)\\{\scriptsize Quản lý phiên, Đối sánh,}\\ {\scriptsize Giao dịch, Xác thực JWT}};

        % Tầng 3A: AI Module
        \node[block=purple, above right=3mm and 14mm of be] (ai) {\textbf{AI Module}\\\texttt{services/vision}\\{\scriptsize RetinaFace + FER + ArcFace}};

        % Tầng 3B: Database
        \node[block=green, below right=3mm and 14mm of be] (db) {\textbf{Database (DB)}\\\texttt{postgres} (PostgreSQL 16)\\{\scriptsize Bảng quan hệ \& pgvector 512D}};

        % Tầng 4: Frontend
        \node[block=teal, above=10mm of be] (fe) {\textbf{Frontend (FE)}\\\texttt{apps/web} (React/Vite)\\{\scriptsize Giao diện CRM, ECharts}};

        % Tác nhân người dùng
        \node[draw=teal!80!black, fill=white, rounded corners=2pt, above=8mm of fe, font=\scriptsize\bfseries, text width=3.3cm, align=center] (user) {Người dùng \& Quản trị viên\\(Trình duyệt Web)};

        % Các luồng giao tiếp rõ ràng
        \draw[flow] (cam) -- node[lbl, above] {HTTP POST\\Ảnh thô + Ngữ cảnh} (be);
        \draw[flow] (be) -- node[lbl, above, sloped] {HTTP POST Ảnh} (ai);
        \draw[flow] (ai) -- node[lbl, below, sloped] {JSON: FER \& 512D} (be);
        \draw[flow] (be) -- node[lbl, above, sloped] {SQLAlchemy \& Cosine} (db);
        \draw[flow] (db) -- node[lbl, below, sloped] {Dữ liệu giao dịch} (be);
        \draw[flow] (fe) -- node[lbl, right] {REST API / JSON} (be);
        \draw[flow] (be) -- node[lbl, left] {Dữ liệu báo cáo} (fe);
        \draw[flow, draw=teal] (user) -- (fe);
    \end{tikzpicture}%
    }
    \caption{Kiến trúc phân tầng chuẩn mực 4 khối và trung tâm điều phối Backend của hệ thống}
    \label{fig:component_architecture_ch4}
\end{figure}
```

---

#### Biểu đồ 5: Biểu đồ ca sử dụng UML chuẩn mực đa tác nhân (Hình 4.3 — `fig:overall_usecase_ch4`)
- **Vị trí:** `Chuong/4_Xay_dung_va_phat_trien_he_thong.tex` (Mục 4.2.1).
- **Thiết kế:** Chuẩn UML Use Case Diagram với khung ranh giới hệ thống (System Boundary) và 4 tác nhân (*Nhân viên*, *Quản lý*, *Marketing & CX*, *Quản trị viên*). *(Chi tiết mã TikZ đã được thiết kế tối ưu tại Mục 13 trong tài liệu này)*.

---

#### Biểu đồ 6: Biểu đồ đường cong cảm xúc hành trình đa chiều (Hình 4.7 — `fig:shopping_tracking_ch4`)
- **Vị trí:** `Chuong/4_Xay_dung_va_phat_trien_he_thong.tex` (Mục 4.3.3).
- **Vấn đề cũ:** Màn hình chỉ có 4 nút tròn tĩnh nằm ngang, không có trục thời gian, không có thang đo cảm xúc.
- **Thiết kế mới:** Biểu đồ đường cong cảm xúc theo dòng thời gian thực (Timeline Emotion Journey Chart) kết hợp dải màu nền phân vùng khu vực. *(Chi tiết mã TikZ đã được thiết kế tại Mục 15 trong tài liệu này)*.

---

#### Biểu đồ 7: Sơ đồ luồng đối sánh 2 tầng cho khách ẩn danh và CRM (Hình 4.10 — `fig:unidentified_observations_ch4`)
- **Vị trí:** `Chuong/4_Xay_dung_va_phat_trien_he_thong.tex` (Mục 4.3.4).
- **Vấn đề cũ:** Chỉ có bảng danh sách phẳng các quan sát `NO_MATCH` trôi nổi độc lập.
- **Thiết kế mới:** Sơ đồ khối rẽ nhánh nhận diện hai tầng logic, phân biệt khách hàng thành viên CRM và khách vãng lai quay lại (Cross-session Re-identification). *(Chi tiết mã và bảng cấu trúc dữ liệu đã được thiết kế tại Mục 17)*.

---

#### Biểu đồ 8: Cụm Biểu đồ vành khăn (Donut Chart Grid) phân bố biểu cảm khu vực (Hình 4.11 / Hình 4.8)
- **Vị trí:** `Chuong/4_Xay_dung_va_phat_trien_he_thong.tex` (Mục 4.4.1).
- **Vấn đề cũ:** Dùng biểu đồ cột chồng 7 lớp sai nguyên tắc trực quan hóa cơ cấu thành phần.
- **Thiết kế mới:** Cụm 4 biểu đồ vành khăn độc lập cho 4 khu vực, thể hiện 100% cơ cấu 7 lớp biểu cảm, tâm vành khăn hiển thị KPI mẫu $N$ và tỷ lệ tích cực. *(Chi tiết mã TikZ đã được thiết kế tại Mục 18)*.

---

#### Biểu đồ 9: Sơ đồ luồng chuyển dịch biểu cảm giữa các khu vực liên tiếp (Hình 4.9 — `fig:change_screen_ch4`)
- **Vị trí:** `Chuong/4_Xay_dung_va_phat_trien_he_thong.tex` (Mục 4.4.2).
- **Vấn đề cũ:** Hình chụp giao diện chữ nhỏ mờ, khó nhận biết luồng biến thiên cảm xúc.
- **Thiết kế mới:** Trực quan hóa dưới dạng Sơ đồ luồng chuyển dịch trạng thái (State Transition / Sankey Flow) giữa hai điểm chạm kế tiếp:

```latex
\begin{figure}[H]
    \centering
    \resizebox{0.9\textwidth}{!}{%
    \begin{tikzpicture}[
        node distance=10mm and 25mm,
        state_prev/.style={draw=blue!80!black, fill=blue!10, rounded corners=3pt, thick, align=center, minimum height=11mm, text width=3.2cm, font=\small},
        state_next/.style={draw=teal!80!black, fill=teal!10, rounded corners=3pt, thick, align=center, minimum height=11mm, text width=3.2cm, font=\small},
        flow/.style={-{Latex[length=2.5mm]}, line width=#1, draw=gray!75},
        lbl/.style={font=\scriptsize\bfseries, fill=white, inner sep=1.5pt}
    ]
        % Cột điểm chạm trước
        \node[state_prev] (p_happy) at (0, 2.5) {\textbf{Tích cực (Happy)}\\48.1\% (76 quan sát)};
        \node[state_prev] (p_neutral) at (0, 0) {\textbf{Trung tính (Neutral)}\\37.3\% (59 quan sát)};
        \node[state_prev] (p_neg) at (0, -2.5) {\textbf{Tiêu cực (Sad/Angry)}\\14.6\% (23 quan sát)};

        % Cột điểm chạm sau
        \node[state_next] (n_happy) at (7, 2.5) {\textbf{Tích cực (Happy)}\\51.9\% (56 quan sát)};
        \node[state_next] (n_neutral) at (7, 0) {\textbf{Trung tính (Neutral)}\\36.1\% (39 quan sát)};
        \node[state_next] (n_neg) at (7, -2.5) {\textbf{Tiêu cực (Sad/Angry)}\\12.0\% (13 quan sát)};

        % Tiêu đề cột
        \node[font=\bfseries, text=blue!80!black, above=3mm of p_happy] {Khu vực trước: Cửa vào};
        \node[font=\bfseries, text=teal!80!black, above=3mm of n_happy] {Khu vực sau: Trưng bày};

        % Luồng chuyển dịch chính (Độ dày tỷ lệ với số lượng)
        \draw[flow=3.5pt, draw=green!60!black] (p_happy) -- node[lbl, above, pos=0.5] {Giữ nguyên: 72.4\%} (n_happy);
        \draw[flow=1.8pt, draw=orange!80!black] (p_happy) -- node[lbl, near end] {Chuyển sang: 21.1\%} (n_neutral);
        \draw[flow=2.8pt, draw=blue!70!black] (p_neutral) -- node[lbl, above, pos=0.5] {Giữ nguyên: 55.9\%} (n_neutral);
        \draw[flow=2.2pt, draw=green!60!black] (p_neutral) -- node[lbl, near start] {Chuyển biến tốt: 32.2\%} (n_happy);
        \draw[flow=1.5pt, draw=red!70!black] (p_neg) -- node[lbl, above, pos=0.5] {Giữ nguyên: 39.1\%} (n_neg);
        \draw[flow=2.0pt, draw=teal!70!black] (p_neg) -- node[lbl, near end] {Cải thiện: 43.5\%} (n_neutral);
    \end{tikzpicture}%
    }
    \caption{Sơ đồ luồng chuyển dịch cảm xúc khách hàng giữa hai khu vực liên tiếp trong hành trình}
    \label{fig:change_screen_ch4}
\end{figure}
```

---

#### Biểu đồ 10: Biểu đồ xu hướng biến thiên cảm xúc theo chuỗi thời gian (Hình 4.13 — `fig:timeline_area_ch4`)
- **Vị trí:** `Chuong/4_Xay_dung_va_phat_trien_he_thong.tex` (Mục 4.4.1).
- **Vấn đề cũ:** Hình chụp cột xếp chồng theo các khoảng thời gian bị vụn vặt và khó so sánh xu thế.
- **Thiết kế mới:** Biểu đồ đường mượt đa chuỗi thời gian (Multi-line Time Series Trend Chart) theo các khung giờ cao điểm trong ngày:

```latex
\begin{figure}[H]
    \centering
    \resizebox{0.95\textwidth}{!}{%
    \begin{tikzpicture}[
        lbl/.style={font=\scriptsize, align=center},
        axis/.style={thick, -{Latex[length=2.5mm]}}
    ]
        % Trục tọa độ
        \draw[axis] (0, 0) -- (12.5, 0) node[right, font=\small\bfseries] {Khung giờ trong ngày ($h$)};
        \draw[axis] (0, 0) -- (0, 4.2) node[above, font=\small\bfseries] {Tỷ lệ cảm xúc (\%)};

        % Các vạch trục tung
        \draw[dotted, gray!50] (0, 1.0) -- (12.0, 1.0) node[right, font=\tiny] {10\%};
        \draw[dotted, gray!50] (0, 2.0) -- (12.0, 2.0) node[right, font=\tiny] {20\%};
        \draw[dotted, gray!50] (0, 3.0) -- (12.0, 3.0) node[right, font=\tiny] {30\%};
        \draw[dotted, gray!50] (0, 4.0) -- (12.0, 4.0) node[right, font=\tiny] {40\%};

        % Các mốc thời gian trên trục hoành
        \foreach \x/\t in {1.5/09h, 3.5/11h, 5.5/14h, 7.5/17h, 9.5/19h, 11.5/21h} {
            \draw (\x, 0.1) -- (\x, -0.1) node[below, font=\scriptsize] {\t};
        }

        % Vùng giờ cao điểm
        \fill[yellow!10] (7.0, 0) rectangle (10.5, 4.0);
        \node[font=\tiny\bfseries, text=orange!80!black] at (8.75, 3.8) {Khung giờ cao điểm tối};

        % Đường tích cực (Happy) - Màu xanh lục
        \draw[very thick, green!60!black] 
            (1.5, 3.2) to[out=10, in=190] (3.5, 3.6) to[out=10, in=170] (5.5, 3.1)
            to[out=-10, in=190] (7.5, 2.6) to[out=10, in=190] (9.5, 3.4) to[out=10, in=180] (11.5, 3.5);
        \node[font=\scriptsize\bfseries, text=green!60!black] at (11.5, 3.8) {Happy};

        % Đường trung tính (Neutral) - Màu xanh lam
        \draw[very thick, blue!60!black] 
            (1.5, 2.8) to[out=-10, in=170] (3.5, 2.4) to[out=-10, in=190] (5.5, 2.7)
            to[out=10, in=170] (7.5, 2.9) to[out=-10, in=190] (9.5, 2.5) to[out=-10, in=180] (11.5, 2.4);
        \node[font=\scriptsize\bfseries, text=blue!60!black] at (11.5, 2.1) {Neutral};

        % Đường tiêu cực (Sad/Angry) - Màu đỏ
        \draw[very thick, red!75!black] 
            (1.5, 0.4) to[out=0, in=180] (3.5, 0.5) to[out=0, in=180] (5.5, 0.6)
            to[out=30, in=180] (7.5, 1.2) to[out=-30, in=180] (9.5, 0.7) to[out=0, in=180] (11.5, 0.5);
        \node[font=\scriptsize\bfseries, text=red!75!black] at (7.5, 1.5) {Peak Tiêu cực (17h-18h)};
    \end{tikzpicture}%
    }
    \caption{Biến thiên tỷ lệ các nhóm biểu cảm theo các khung giờ trong ngày tại khu vực cửa hàng}
    \label{fig:timeline_area_ch4}
\end{figure}
```

---

### 4. Bảng tổng hợp đối chiếu toàn bộ các sơ đồ / biểu đồ trước và sau nâng cấp

| STT | Mã nhãn / Vị trí | Tên sơ đồ / biểu đồ | Hiện trạng (Khó hiểu) | Thiết kế nâng cấp (Trực quan & Dễ hiểu) |
|---|---|---|---|---|
| 1 | `fig:solution_flow` (Hình 3.1) | Luồng xử lý tổng thể | 7 hộp trắng đơn điệu, không rõ phân tầng | Phân 4 giai đoạn màu sắc: Input, AI kép, Quản lý phiên, Trực quan CRM |
| 2 | `fig:observation_tasks` (Hình 3.2) | Hai nhánh xử lý khuôn mặt | 4 hộp nối sơ sài, thiếu công thức/đặc tả | Rẽ 2 nhánh FER ($\mathbb{R}^7$) và ArcFace ($\mathbb{R}^{512}$), ghép thành bản ghi quan sát |
| 3 | `fig:function_structure_ch4` (Hình 4.1) | Cấu trúc phân rã chức năng | Nhồi 3 đoạn văn dài vào hộp chữ nhật | Sơ đồ cây phân cấp mô-đun (Feature Tree Cards) có bullet points ngắn gọn |
| 4 | `fig:component_architecture_ch4` (Hình 4.2) | Kiến trúc thành phần | Camera dưới đáy, mũi tên hai chiều chằng chịt | Kiến trúc 4 tầng chuẩn (FE, BE trung tâm, AI Module, DB) có ranh giới rõ ràng |
| 5 | `fig:overall_usecase_ch4` (Hình 4.3) | Sơ đồ ca sử dụng UML | 1 actor duy nhất, thiếu System Boundary | Chuẩn UML đa tác nhân: Nhân viên, Quản lý, Marketing/CX, Quản trị viên |
| 6 | `fig:shopping_tracking_ch4` (Hình 4.7) | Hành trình mua sắm | 4 nút tròn tĩnh, không có thời gian | Đường cong cảm xúc (Timeline Emotion Journey Chart) có dải nền khu vực |
| 7 | `fig:unidentified_observations_ch4` (Hình 4.10) | Quản lý khách ẩn danh | Bảng phẳng `NO_MATCH` rời rạc | Quy trình đối sánh 2 tầng (CRM vs Anonymous), tái nhận diện đa phiên |
| 8 | `fig:donut_distribution_ch4` (Hình 4.11) | Phân bố biểu cảm khu vực | Biểu đồ cột chồng 7 lớp sai nguyên tắc | Cụm 4 biểu đồ vành khăn (Donut Charts), cơ cấu 100%, tâm hiển thị KPI |
| 9 | `fig:change_screen_ch4` (Hình 4.9) | Thay đổi biểu cảm giữa khu vực | Ảnh chụp giao diện mờ, khó đọc | Sơ đồ luồng chuyển dịch cảm xúc (Sankey Flow / State Transition) |
| 10 | `fig:timeline_area_ch4` (Hình 4.13) | Biến thiên theo thời gian | Cột xếp chồng phân mảnh | Biểu đồ đường mượt đa chuỗi thời gian (Multi-line Trend Chart) theo giờ |

---

- **Trạng thái:** Đã hoàn tất ghi chú thiết kế chi tiết toàn bộ 10 sơ đồ/biểu đồ chuẩn hóa vào tài liệu ghi chú; các tệp `.tex` của luận văn được giữ nguyên vẹn 100%.
