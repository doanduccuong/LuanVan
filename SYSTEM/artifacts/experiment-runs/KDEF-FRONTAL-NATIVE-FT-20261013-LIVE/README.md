# Lần chạy camera gần chính diện, ảnh nguồn nguyên kích thước

Lần chạy này kiểm tra tác động của tư thế khuôn mặt trong dữ liệu camera. Nội dung
luận văn và các hình đang được tham chiếu trong luận văn chưa được cập nhật.

## Đầu vào và nguyên tắc chia dữ liệu

- Giữ nguyên năm nhóm nguồn, 100 nhãn đối chiếu, thời điểm, thứ tự điểm chạm và
  trọng số Emotion đã tinh chỉnh của lần chạy `KDEF-NATIVE-FT-20261013-LIVE`.
- Với mỗi nhóm nguồn và mỗi biểu cảm, ứng viên có điểm chính diện cao nhất được
  dành cho camera. Ảnh Neutral thứ hai được dùng để đăng ký; ảnh còn lại được dùng
  để hiệu chỉnh. Các vai trò không trùng hàm băm nguồn.
- Ảnh camera được gửi nguyên vẹn ở kích thước 562x762, không tạo canvas, không
  thay đổi độ sáng và không thay đổi kích thước.
- Nhãn được lấy ngẫu nhiên theo cùng chuỗi của lần chạy đối chứng; ảnh camera được
  lấy có hoàn lại. Có 34 ảnh nguồn camera khác nhau trong 100 sự kiện.
- Điểm chính diện là thứ tự tương đối do Haar frontal-face xác định. Bản Kaggle
  không còn mã góc chụp gốc, nên không diễn giải đây là nhãn góc chính thức KDEF.

Kiểm tra đầu vào đạt: 100 sự kiện, 25 hành trình dự kiến, đủ bảy nhãn, khoảng cách
giữa hai điểm chạm liên tiếp từ 5 đến 15 phút và không có ảnh nguồn dùng chung giữa
camera với đăng ký/hiệu chỉnh.

## Hiệu chỉnh và chạy đầu cuối

Quy tắc chọn ngưỡng ArcFace không thay đổi: tối đa hóa TPR trong các ứng viên có
FPR thực nghiệm bằng 0, hòa thì chọn ngưỡng lớn nhất. Do tập ảnh hiệu chỉnh được
chia lại, ngưỡng mới là `0.6303331427488639`, chấp nhận 93/105 cặp cùng nhóm và
0/490 cặp khác nhóm.

| Chỉ tiêu | Camera nghiêng trước đó | Camera gần chính diện |
|---|---:|---:|
| Ảnh hợp lệ | 100/100 | 100/100 |
| Ghép đúng hồ sơ | 97/100 | 97/100 |
| Ghép nhầm hồ sơ | 0 | 0 |
| Biểu cảm đúng trên 100 ảnh | 28 | 40 |
| Accuracy biểu cảm | 0.280 | 0.400 |
| Macro-F1 trực tiếp | 0.237 | 0.389 |
| Hành trình đầy đủ | 23/25 | 23/25 |

Đối chiếu theo cùng vị trí sự kiện cho thấy 19 ảnh chuyển từ sai thành đúng, 7 ảnh
chuyển từ đúng thành sai, 21 ảnh đúng ở cả hai lần và 53 ảnh sai ở cả hai lần. Mức
tăng ròng là 12 ảnh đúng, tương ứng 12 điểm phần trăm accuracy; Macro-F1 tăng
0.152. Số ảnh đúng theo lớp thay đổi như sau:

| Nhãn | Trước | Gần chính diện |
|---|---:|---:|
| Angry | 10/12 | 7/12 |
| Disgust | 0/23 | 0/23 |
| Fear | 0/12 | 0/12 |
| Happy | 2/9 | 5/9 |
| Sad | 4/17 | 10/17 |
| Surprise | 12/15 | 11/15 |
| Neutral | 0/12 | 7/12 |

Ba ảnh Disgust không đạt ngưỡng định danh nên hệ thống lưu 97 quan sát. Cả ba ảnh
này cũng bị dự đoán sai ở phép đo trực tiếp; vì vậy số đúng đầu cuối vẫn là 40/100,
còn accuracy trên 97 dự đoán được lưu là 0.412371. Toàn bộ 97 quan sát đều sử dụng
`deepface-emotion-finetuned:f49a354ea2ad`.

## Chuỗi và phân cụm

Hệ thống tạo 25 hành trình, trong đó 23 hành trình đủ bốn trạng thái và hai hành
trình thiếu trạng thái. Optimal Matching--PAM chọn K=3, ASW=0.242180:

- Cụm 1: 3 chuỗi; medoid `Surprise -> Surprise -> Happy -> Happy`.
- Cụm 2: 13 chuỗi; medoid `Neutral -> Angry -> Neutral -> Angry`.
- Cụm 3: 7 chuỗi; medoid `Sad -> Angry -> Angry -> Angry`.

35/35 điều kiện kiểm tra nghiệp vụ đạt. Kiểm tra truy vết xác nhận 100 phản hồi API,
97 quan sát lưu, 23 chuỗi được gán cụm và ba medoid đều liên kết đúng về quan sát.

## Kết luận trong phạm vi lần chạy

Chuyển dữ liệu camera sang các ảnh gần chính diện làm kết quả biểu cảm tăng rõ từ
28% lên 40%, đặc biệt ở Happy, Sad và Neutral. Tuy nhiên, Disgust và Fear vẫn không
có dự đoán đúng, trong khi Angry và Surprise giảm nhẹ. Vì vậy tư thế mặt là một yếu
tố ảnh hưởng nhưng không phải nguyên nhân duy nhất; sự không đồng nhất tiền xử lý
và khả năng chuyển miền của mô hình vẫn cần được xử lý nếu muốn tăng thêm độ
chính xác.

## Bằng chứng

- `input-audit.json`: kiểm tra đầu vào và tách vai trò ảnh.
- `face-threshold.json`: ngưỡng và toàn bộ điểm ROC.
- `replay_results.jsonl`, `kdef_metrics.json`: 100 phản hồi và số liệu đầu cuối.
- `camera-pose-comparison.json`: đối chiếu theo cặp với lần chạy ảnh nghiêng.
- `sequence-analysis/`: kết quả chọn K, cụm, medoid và gán cụm.
- `verification.json`, `trace-audit.json`: kiểm tra nghiệp vụ và truy vết.
- `charts/`: ma trận nhầm lẫn, kết quả định danh và đồ thị chọn K mới nhất.
- `screenshots/`: ảnh giao diện và trạng thái hệ thống mới nhất của lần chạy.
- `backup/`: bản sao cơ sở dữ liệu trước và sau lần chạy.
