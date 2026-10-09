# Trạng thái triển khai hệ thống

Cập nhật ngày 08/10/2026. Thành phần State Sequence Clustering đã được nối vào luồng hệ thống hiện có sau bước hình thành chuỗi của mỗi lần mua sắm; đây không phải phương pháp thay thế nhận diện khuôn mặt hay phân loại biểu cảm.

## 1. Thành phần đã triển khai

- FastAPI, SQLAlchemy, Alembic và PostgreSQL/pgvector cho nghiệp vụ CRM.
- Dịch vụ thị giác dùng RetinaFace để phát hiện, ArcFace để tạo embedding định danh và DeepFace Emotion để dự đoán biểu cảm.
- React/TypeScript cho giao diện quản trị.
- Mô-đun `sequence_analysis.py` tạo chuỗi theo visit, gọi Sequenzo tính Optimal Matching, chạy PAM, tính silhouette và chọn số cụm.
- Ba bảng lưu run phân tích, tóm tắt cụm và assignment; dữ liệu Camera và Simulator được lọc theo loại nguồn cùng mã lần chạy.
- API tạo/xem run, xem cụm, đổi tên hiển thị cụm và truy vấn assignment.
- Giao diện hiển thị ứng viên K, ASW, medoid, assignment và liên kết trở lại hành trình gốc.
- Script chuẩn bị KDEF, đăng ký ảnh, hiệu chỉnh ngưỡng, phát lại khung Camera, xác minh hậu điều kiện, sinh biểu đồ và chụp bằng chứng.

Migration hiện tại là `f4c3d9a8b2e1`.

## 2. Kết quả đầu-cuối bằng KDEF

- Mã dữ liệu: `KDEF-KAGGLE-20261008-LIVE`.
- Nguồn: <https://www.kaggle.com/datasets/chenrich/kdef-database>.
- Bản dữ liệu đã tải: 2.938 ảnh, 7 nhãn, 140 mã nhóm nguồn.
- Nhóm dùng cho demo: `KG011`, `KG039`, `KG061`, `KG074`, `KG112`.
- Đầu vào: 5 hồ sơ, 25 lần mua sắm, 100 khung Camera và 35 ảnh hiệu chỉnh dành riêng.
- Xử lý ảnh: 100/100 ảnh hợp lệ; 96/100 khung ghép đúng hồ sơ dự kiến; 4 `NO_MATCH`; 0 ghép nhầm sang hồ sơ khác.
- Biểu cảm: Accuracy 0,540; Macro-F1 0,405409 trên năm lớp có mẫu đối chiếu.
- Phân cụm: nhận 25 visit, dùng 22, loại 3 visit thiếu bốn trạng thái; K=5; ASW=0,445193.
- Run phân tích: `a845f266-7dab-4dff-ba42-a61a46930d7a`.
- Kiểm tra luồng/tính toàn vẹn: 35/35 đạt.

Artifact nằm tại:

```text
artifacts/experiment-runs/KDEF-KAGGLE-20261008-LIVE/
```

## 3. Thực nghiệm chuỗi có kiểm soát

- Mã dữ liệu: `SIM-CONTROLLED-20261008-LIVE`.
- 25 khách hàng, 125 lần mua sắm, 500 quan sát và năm mẫu chuỗi biết trước.
- Optimal Matching + PAM: K=5, ASW=1,000, ARI=1,000, NMI=1,000.
- Tỷ lệ trạng thái + Euclid + PAM: K=4, ASW=1,000, ARI=0,777, NMI=0,906.
- SHA-256 của ma trận khoảng cách được tính độc lập và khớp giá trị lưu trong API.

Đây là dữ liệu tổng hợp có kiểm soát để kiểm tra phân tích chuỗi; không phải bằng chứng về chất lượng vision hoặc hành vi khách hàng thật.

## 4. Môi trường và kiểm thử cuối

- Docker Compose: PostgreSQL, Vision, API, Simulator và Web hoạt động; migration kết thúc mã 0.
- HTTP: API, Vision, Simulator và Web đều trả 200 tại thời điểm kiểm chứng; Vision báo `DeepFaceRetinaFaceEngine`.
- API: 15/15 kiểm thử đạt.
- Vision: 3/3 kiểm thử đạt.
- Web: TypeScript và Vite build thành công.
- Ảnh trạng thái hệ thống: `artifacts/experiment-runs/KDEF-KAGGLE-20261008-LIVE/screenshots/K05_system_runtime_status.png`.
- Dữ liệu máy đọc của lần kiểm tra: `system_runtime_status.json` trong cùng thư mục.

## 5. Phạm vi kết luận

Hệ thống đã chứng minh được luồng kỹ thuật ảnh đăng ký → ảnh Camera ở nhiều điểm chạm → định danh và biểu cảm → visit → chuỗi → Optimal Matching → PAM → medoid/assignment → giao diện truy vết. Kết quả không tự động cho biết khách hàng hài lòng hay không. Muốn gắn tên nghiệp vụ cho cụm phải thu thêm CSAT hoặc biến kết quả độc lập và kiểm định mối liên hệ trên dữ liệu thực tế.
