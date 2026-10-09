# Bảng bàn giao và bằng chứng

Cập nhật ngày 08/10/2026. Thành phần phân cụm chuỗi được thêm vào sau luồng tạo chuỗi hiện có; nó không thay thế nhận diện khuôn mặt, phân loại biểu cảm hoặc các báo cáo thống kê đang có.

## 1. Trạng thái bàn giao

- Docker Compose: PostgreSQL, Vision, API, Simulator và Web đang hoạt động; migration kết thúc với mã thoát 0.
- Health check trực tiếp: API, Vision, Simulator và Web đều trả HTTP 200; Vision xác nhận backend `DeepFaceRetinaFaceEngine`.
- KDEF Camera: đã chạy đầu-cuối bằng run `KDEF-KAGGLE-20261008-LIVE`.
- Phân cụm Camera: đã hoàn tất bằng run `a845f266-7dab-4dff-ba42-a61a46930d7a`.
- Dữ liệu tổng hợp có kiểm soát: đã hoàn tất bằng run `SIM-CONTROLLED-20261008-LIVE`.
- Kiểm thử: API 15/15, Vision 3/3 và build web đều đạt.
- Luận văn: Chương 3–5 đã cập nhật, biên dịch thành công và kiểm tra trực quan sau lần chạy cuối.

## 2. Luồng KDEF đầu-cuối

Nguồn tệp là bản KDEF đã xử lý trên Kaggle: <https://www.kaggle.com/datasets/chenrich/kdef-database>. Bản đã tải có 2.938 ảnh, bảy thư mục nhãn và 140 mã nhóm nguồn. Bản này không giữ tên tệp KDEF gốc, mã phiên hoặc mã góc; vì vậy báo cáo không gọi 140 mã nhóm là 140 người độc lập và không tuyên bố đã dùng đủ 4.900 ảnh KDEF gốc.

| Mã | Nội dung đã kiểm chứng | Kết quả | Artifact/ảnh trực tiếp |
|---|---|---|---|
| K01 | Chọn dữ liệu và truy vết tệp nguồn | 5 nhóm `KG011`, `KG039`, `KG061`, `KG074`, `KG112`; seed `20261008` | `data/generated/kdef_demo/kdef_demo_manifest.json`, `image_manifest.csv` |
| K02 | Ảnh đăng ký và hồ sơ khách hàng | 5 hồ sơ, mỗi hồ sơ có ảnh KDEF và face template | `screenshots/K01_kdef_customer_list.png`, `K02_kdef_customer_profile.png` |
| K03 | Hiệu chỉnh ngưỡng vận hành | 35 ảnh riêng; 105 cặp cùng nhóm, 490 cặp khác nhóm; ngưỡng `0,639295`; TPR `0,904762`, TNR `1,000000` trên tập hiệu chỉnh | `artifacts/face-threshold.json` |
| K04 | Phát lại ảnh qua Vision/API | 100/100 ảnh hợp lệ; 96 ghép đúng hồ sơ dự kiến; 4 `NO_MATCH`; 0 ghép nhầm sang hồ sơ khác | `replay_results.jsonl`, `replay_summary.json`, `kdef_metrics.json` |
| K05 | Tạo hành trình nhiều điểm chạm | 5 hồ sơ, 25 lần mua sắm, 100 khung; thời gian và thứ tự điểm chạm được giữ | `verification.json`, `screenshots/K03_kdef_four_touchpoint_journey.png`, `K04_kdef_camera_timeline.png` |
| K06 | Đối chiếu biểu cảm | Accuracy `0,540`; Macro-F1 `0,405409` trên năm lớp có mẫu đối chiếu | `kdef_metrics.json`, `charts/expression_confusion_matrix.png` |
| K07 | Phân cụm chuỗi Camera | Nhận 25 visit, dùng 22, loại 3 visit thiếu bốn trạng thái; chọn K=5, ASW `0,445193` | `sequence-analysis/run.json`, `clusters.json`, `assignments.json` |
| K08 | Truy vết cụm về chuỗi gốc | Có medoid, assignment, distance, silhouette và liên kết về visit/observation | `screenshots/E09_cluster_medoids.png`, `E10_cluster_assignments.png`, `E11_assignment_visit_trace.png` |
| K09 | Trạng thái hệ thống tích hợp | Các service cần thiết hoạt động, migration mã 0, bốn endpoint trả HTTP 200 | `screenshots/K05_system_runtime_status.png`, `system_runtime_status.json` |

Toàn bộ artifact của lần chạy nằm tại:

```text
artifacts/experiment-runs/KDEF-KAGGLE-20261008-LIVE/
```

`verification.json` có 35/35 kiểm tra luồng và tính toàn vẹn dữ liệu đạt. Con số này không phải độ chính xác mô hình; chất lượng nhận dạng được báo cáo riêng bằng 96/100 khung ghép đúng và Accuracy biểu cảm 0,540.

## 3. Phân cụm chuỗi có đối chứng

| Mã | Nội dung đã kiểm chứng | Kết quả | Artifact/ảnh trực tiếp |
|---|---|---|---|
| S01 | Run đúng nguồn, đủ dữ liệu | 25 khách hàng, 125 visit, 500 quan sát; không loại chuỗi | `controlled-sequences/results.json`, `screenshots/E07_E08_sequence_run_overview.png` |
| S02 | Optimal Matching + PAM | K=5, ASW=1,000, ARI=1,000, NMI=1,000 | `controlled-sequences/results.json`, `om_k_candidates.csv` |
| S03 | Baseline tỷ lệ trạng thái | K=4, ASW=1,000, ARI=0,777, NMI=0,906 | `controlled-sequences/method_comparison.csv` |
| S04 | Medoid là chuỗi thật | Có năm medoid và thành viên của từng cụm | `screenshots/E09_cluster_medoids.png`, `controlled-sequences/assignments.csv` |
| S05 | Truy vết assignment | Assignment mở lại đúng visit và bốn observation | `screenshots/E11_assignment_visit_trace.png`, `capture_manifest.json` |
| S06 | Ma trận OM có thể kiểm tra lại | SHA-256 của ma trận tái tạo độc lập khớp giá trị lưu bởi API | `controlled-sequences/om_distance_matrix.npy`, `results.json` |

Thư mục artifact:

```text
artifacts/experiment-runs/SIM-CONTROLLED-20261008-LIVE/
```

Đây là dữ liệu tổng hợp có kiểm soát để kiểm tra thuật toán. Nó không đi qua dịch vụ xử lý ảnh, không mô tả hành vi khách hàng thật và không phải điểm hài lòng.

## 4. Ánh xạ báo cáo–code–bằng chứng

| Phát biểu trong Chương 3–5 | Code hiện thực | Kiểm tra/artifact | Hình trong báo cáo |
|---|---|---|---|
| Chuỗi được tạo theo `visit_id`, thứ tự thời gian và đoạn điểm chạm | `apps/api/app/sequence_analysis.py` | `tests/test_sequence_analysis.py`, `assignments.json` | Hình 4.17, 5.18 |
| Optimal Matching trả ma trận khoảng cách, không trả chuỗi đã biến đổi | `build_om_distance_matrix` | checksum trong `run.json`/`results.json` | Hình 5.3 |
| PAM trả assignment và medoid | `cluster_with_pam`, API cluster/assignment | `clusters.json`, `assignments.json` | Hình 4.15–4.17, 5.16–5.18 |
| K được chọn sau khi loại nghiệm có cụm quá nhỏ và áp dụng dung sai ASW | `select_cluster_count` | `candidate_metrics` trong `run.json` | Hình 4.14, 5.14–5.15 |
| KDEF đi qua RetinaFace, ArcFace và DeepFace | `services/vision`, `POST /observations`, các script demo | `replay_results.jsonl`, `kdef_metrics.json` | Hình 4.19–4.21, 5.8–5.18 |
| Kết quả có thể truy vết về run thật | API sequence analysis và giao diện Reports | ba JSON trong `sequence-analysis/`, manifest ảnh | Hình 5.15–5.18 |

## 5. Giới hạn phải giữ nguyên khi diễn giải

- KDEF là ảnh biểu cảm có chủ đích trong điều kiện kiểm soát, không phải dữ liệu khách hàng trong cửa hàng.
- Năm mã nhóm chỉ phục vụ demo luồng; các tỷ lệ 96%, 0,540 và ASW 0,445 không đại diện cho toàn bộ KDEF hoặc môi trường vận hành thật.
- Cụm chỉ biểu thị các chuỗi nhãn có diễn biến tương tự. Không được gọi cụm là “hài lòng” hoặc “không hài lòng” khi chưa có CSAT hoặc biến kết quả độc lập để đối chứng.
- Bốn `NO_MATCH` được giữ nguyên trong artifact; không thay ảnh hoặc chèn nhãn giả để tạo kết quả hoàn hảo.
