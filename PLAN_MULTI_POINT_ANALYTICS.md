# Kế hoạch nghiên cứu hai phương pháp phân tích cảm xúc đa điểm chạm

## 1. Trạng thái tài liệu

- **Phiên bản:** 0.2
- **Trạng thái:** Kế hoạch nghiên cứu và kiểm chứng; chưa được coi là phương pháp đã lựa chọn
- **Hai phương pháp cần đánh giá:**
  1. Quy đổi đầu ra FER thành điểm hóa trị cảm xúc.
  2. Tổng hợp chuỗi điểm chạm bằng quy tắc đỉnh–cuối.

Hai phương pháp chỉ được đưa vào Chương 3 sau khi có đặc tả kỹ thuật, mã thực nghiệm và kết quả kiểm chứng. Không sử dụng lại các trọng số và ngưỡng của phiên bản cũ khi chưa có bằng chứng.

---

## 2. Phương pháp 1 – Quy đổi đầu ra FER thành điểm hóa trị

### 2.1. Mục đích

Mô hình FER trả về phân bố xác suất của bảy lớp:

$$
\mathbf{p}(x)=
[p_{\mathrm{angry}},p_{\mathrm{disgust}},p_{\mathrm{fear}},
p_{\mathrm{happy}},p_{\mathrm{sad}},p_{\mathrm{surprise}},p_{\mathrm{neutral}}].
$$

Để phân tích sự thay đổi theo hành trình bằng một đại lượng liên tục, phương pháp dự kiến ước lượng hóa trị $\hat v(x)$ của biểu cảm quan sát được trên ảnh $x$.

Hóa trị biểu diễn mức dễ chịu–khó chịu. Đây chỉ là một chiều của mô hình cảm xúc; nó không biểu diễn đầy đủ mức kích hoạt hoặc quyền kiểm soát. Russell và Mehrabian trình bày cảm xúc theo các chiều pleasure–arousal–dominance, còn Russell mô tả cấu trúc vòng của cảm xúc theo pleasure–displeasure và arousal. Các nghiên cứu này cung cấp nền tảng khái niệm cho chiều hóa trị nhưng không cung cấp trực tiếp bộ trọng số bảy lớp đã dùng trong phiên bản cũ.

Nguồn nền tảng:

- [Russell và Mehrabian (1977), *Evidence for a Three-Factor Theory of Emotions*](https://doi.org/10.1016/0092-6566(77)90037-X).
- [Russell (1980), *A Circumplex Model of Affect*](https://doi.org/10.1037/h0077714).

### 2.2. Vấn đề của công thức cũ

Phiên bản cũ sử dụng:

| Lớp | Trọng số cũ |
|---|---:|
| Happy | +0,80 |
| Surprise | +0,20 |
| Neutral | 0,00 |
| Sad | −0,60 |
| Fear | −0,65 |
| Angry | −0,70 |
| Disgust | −0,80 |

Không tìm thấy bảng giá trị này trong hai nghiên cứu Russell được dẫn. Hai nguồn trên xác lập cấu trúc chiều của cảm xúc, không xác lập rằng đầu ra xác suất của một mô hình FER phải được nhân với đúng các trọng số trên.

Ngoài ra, Surprise không có hóa trị cố định trong mọi ngữ cảnh. Một biểu cảm ngạc nhiên có thể đi kèm sự kiện tích cực hoặc tiêu cực. Việc gán một giá trị dương cố định làm mất đặc điểm này.

Vì vậy, không được viết:

> Các trọng số được lấy từ Russell và Mehrabian.

Nếu tiếp tục dùng phép quy đổi, phải mô tả đây là một bộ ước lượng do luận văn xây dựng và các hệ số phải được học hoặc ước lượng từ dữ liệu có cả nhãn biểu cảm và hóa trị.

### 2.3. Hai hướng triển khai hợp lệ

#### Hướng A – Dự đoán hóa trị trực tiếp

Sử dụng một mô hình được huấn luyện cho nhiệm vụ hồi quy hóa trị từ ảnh khuôn mặt. Đây là hướng ưu tiên vì mô hình học trực tiếp ánh xạ từ ảnh sang hóa trị thay vì đi vòng qua bảy lớp rời rạc.

AffectNet là một nguồn dữ liệu phù hợp để nghiên cứu vì mỗi ảnh được chú thích theo cả mô hình phân loại biểu cảm và mô hình hóa trị–kích hoạt. Giá trị hóa trị và kích hoạt nằm trong không gian hai chiều, đồng thời dữ liệu có các lớp Neutral, Happy, Sad, Surprise, Fear, Disgust và Anger.

Nguồn: [Mollahosseini, Hasani và Mahoor, *AffectNet: A Database for Facial Expression, Valence, and Arousal Computing in the Wild*](https://arxiv.org/abs/1708.03985).

Đầu ra:

$$
\hat v(x)=f_{\theta}(x), \qquad \hat v(x)\in[-1,1].
$$

Mô hình và trọng số chỉ được sử dụng khi xác minh được nguồn, giấy phép, tập huấn luyện và cách tiền xử lý.

#### Hướng B – Kỳ vọng có trọng số từ xác suất FER

Nếu cần giữ mô hình FER bảy lớp, có thể ước lượng một giá trị đại diện cho từng lớp từ tập dữ liệu có nhãn hóa trị:

$$
\mu_k=rac{1}{|D_k|}\sum_{i\in D_k}v_i,
$$

trong đó $D_k$ là tập ảnh huấn luyện thuộc lớp $k$ và $v_i$ là nhãn hóa trị của ảnh $i$.

Hóa trị dự đoán được tính bằng:

$$
\hat v(x)=\sum_{k=1}^{7}p_k(x)\mu_k.
$$

Trong cách này, $\mu_k$ không phải hằng số phổ quát. Chúng là giá trị ước lượng từ tập huấn luyện cụ thể và phải được công bố cùng dữ liệu, phân vùng và khoảng bất định. Không được tính $\mu_k$ trên tập kiểm thử.

Phép tính trên có thể được hiểu là kỳ vọng hóa trị theo phân bố lớp dự đoán, với giả định rằng mỗi lớp được đại diện bởi một giá trị trung bình. Giả định này cần được kiểm chứng, đặc biệt đối với Surprise và các lớp có phân bố hóa trị rộng.

### 2.4. Thiết kế thực nghiệm cho phương pháp 1

So sánh tối thiểu:

1. Mô hình hồi quy hóa trị trực tiếp.
2. Phép kỳ vọng có trọng số từ xác suất FER với $\mu_k$ ước lượng trên tập huấn luyện.
3. Phương án chỉ dùng nhãn lớn nhất:

$$
\hat v_{\mathrm{hard}}(x)=\mu_{\arg\max_k p_k(x)}.
$$

Chỉ số đánh giá:

- Sai số tuyệt đối trung bình.
- Căn sai số bình phương trung bình.
- Hệ số tương quan Pearson hoặc Spearman.
- Hệ số tương hợp nếu giao thức dữ liệu hỗ trợ.
- Sai số riêng theo từng lớp biểu cảm.

Thí nghiệm phải dùng phân vùng huấn luyện, kiểm định và kiểm thử tách biệt. Mọi hệ số $\mu_k$, tham số hiệu chỉnh xác suất và ngưỡng đều chỉ được học trên tập huấn luyện hoặc kiểm định.

### 2.5. Điều kiện chấp nhận phương pháp 1

Phép quy đổi chỉ được sử dụng trong phương pháp đề xuất khi:

- Có tập dữ liệu kèm nhãn hóa trị phù hợp.
- Các hệ số được ước lượng bằng mã, không điền tay.
- Có kết quả trên tập kiểm thử chưa dùng để lựa chọn hệ số.
- Sai số và giới hạn được trình bày rõ.
- Hướng kỳ vọng có trọng số tạo kết quả đủ tốt so với hồi quy trực tiếp hoặc có lợi thế rõ ràng về chi phí triển khai.

Nếu không đạt các điều kiện này, luận văn chỉ dùng bảy nhãn biểu cảm và không tính hóa trị.

---

## 3. Phương pháp 2 – Tổng hợp hành trình bằng quy tắc đỉnh–cuối

### 3.1. Nội dung của quy tắc

Quy tắc đỉnh–cuối được nghiên cứu trong bối cảnh con người đánh giá hồi tưởng một trải nghiệm kéo dài theo thời gian. Đánh giá hồi tưởng có thể chịu ảnh hưởng lớn của thời điểm có cường độ mạnh nhất và thời điểm kết thúc, trong khi thời lượng của trải nghiệm có thể nhận trọng số thấp hơn.

Với chuỗi giá trị trải nghiệm $v_1,v_2,\ldots,v_T$, một dạng ước lượng thường được dùng là:

$$
S_{\mathrm{PE}}=\frac{v_{\mathrm{peak}}+v_T}{2}.
$$

Nguồn gốc:

- [Fredrickson và Kahneman (1993), *Duration Neglect in Retrospective Evaluations of Affective Episodes*](https://doi.org/10.1037/0022-3514.65.1.45).
- [Kahneman và cộng sự (1993), *When More Pain Is Preferred to Less: Adding a Better End*](https://doi.org/10.1111/j.1467-9280.1993.tb00589.x).

Quy tắc này dự đoán **đánh giá hồi tưởng** của con người về một trải nghiệm. Nó không mặc nhiên là phép tính “tổng cảm xúc thật” và không thể được kiểm chứng chỉ bằng chính chuỗi giá trị mà công thức sử dụng.

### 3.2. Những điểm phải xác định lại

#### a. Đại lượng đầu vào

$v_t$ phải là giá trị hóa trị đã được kiểm chứng hoặc đánh giá trực tiếp của người tham gia tại điểm chạm $t$. Không được thay ngay $v_t$ bằng nhãn Angry, Happy hoặc xác suất lớp nếu phương pháp 1 chưa được xác nhận.

#### b. Định nghĩa điểm đỉnh

Với chuỗi chỉ tích cực hoặc chỉ tiêu cực, điểm đỉnh tương đối rõ: thời điểm dễ chịu nhất hoặc khó chịu nhất. Với chuỗi có cả giá trị dương và âm, “mạnh nhất” có thể được hiểu theo nhiều cách:

- Giá trị dương lớn nhất.
- Giá trị âm nhỏ nhất.
- Giá trị có độ lớn tuyệt đối cao nhất.

Phiên bản cũ tự chọn giá trị có $|v_t|$ lớn nhất. Đây là một giả thuyết triển khai, không phải quy tắc duy nhất được hai nghiên cứu gốc quy định cho hành trình có cả biểu cảm tích cực và tiêu cực.

Do đó, định nghĩa điểm đỉnh phải được khóa trước khi xem kết quả và được so sánh bằng dữ liệu thực nghiệm.

#### c. Đánh giá tổng thể dùng làm nhãn kiểm chứng

Muốn biết quy tắc đỉnh–cuối có phù hợp với hành trình khách hàng hay không, sau mỗi hành trình cần một đánh giá tổng thể độc lập do người tham gia cung cấp, ký hiệu là $y_s$.

Không được dùng $S_{\mathrm{PE}}$ làm cả dự đoán và nhãn kiểm chứng. Nếu không có $y_s$, luận văn chỉ có thể gọi $S_{\mathrm{PE}}$ là một chỉ số giả thuyết, chưa thể khẳng định nó phản ánh đánh giá trải nghiệm.

### 3.3. Các mô hình tổng hợp cần so sánh

Với hành trình $s$ có $T_s$ điểm chạm, tối thiểu phải tính:

**Trung bình toàn hành trình**

$$
S_{\mathrm{mean},s}=\frac{1}{T_s}\sum_{t=1}^{T_s}v_{s,t}.
$$

**Điểm cuối**

$$
S_{\mathrm{end},s}=v_{s,T_s}.
$$

**Đỉnh–cuối**

$$
S_{\mathrm{PE},s}=\frac{v_{\mathrm{peak},s}+v_{s,T_s}}{2}.
$$

**Mô hình có trọng số học từ dữ liệu**

$$
\hat y_s=\beta_0+\beta_1v_{\mathrm{peak},s}+\beta_2v_{s,T_s}.
$$

Không giả định trước $\beta_1=\beta_2=0,5$. Phiên bản trung bình bằng nhau được kiểm tra như một giả thuyết riêng.

Nghiên cứu tổng hợp năm 2022 cho thấy hiệu ứng đỉnh–cuối có bằng chứng đáng kể trên nhiều nghiên cứu, nhưng tác động trung bình toàn trải nghiệm cũng có thể có sức dự đoán tương đương. Một nghiên cứu về trải nghiệm nhiều giai đoạn trong ngày còn cho thấy trung bình có trọng số theo thời lượng dự đoán đánh giá hồi tưởng tốt hơn quy tắc đỉnh–cuối. Vì vậy, không được loại phương pháp trung bình trước khi thực nghiệm.

Nguồn về bằng chứng và điều kiện giới hạn:

- [Alaybek và cộng sự (2022), *All’s Well That Ends (and Peaks) Well? A Meta-Analysis of the Peak-End Rule and Duration Neglect*](https://doi.org/10.1016/j.obhdp.2022.104149).
- [Miron-Shatz (2009), *Evaluating Multiepisode Events: Boundary Conditions for the Peak-End Rule*](https://doi.org/10.1037/a0015295).

### 3.4. Thiết kế thực nghiệm cho phương pháp 2

Mỗi hành trình cần tối thiểu:

- Mã hành trình ẩn danh.
- Thứ tự các điểm chạm.
- Giá trị hóa trị tại từng điểm chạm.
- Đánh giá tổng thể sau khi hành trình kết thúc.
- Thông tin điểm chạm bị thiếu hoặc quan sát không hợp lệ.

Đối với mỗi mô hình tổng hợp, đánh giá khả năng dự đoán $y_s$ bằng:

- Sai số tuyệt đối trung bình.
- Căn sai số bình phương trung bình.
- Hệ số tương quan.
- Hệ số xác định trên tập kiểm thử.
- Khoảng tin cậy thu được bằng lấy mẫu lặp lại theo hành trình.

Việc lựa chọn mô hình phải dựa trên tập kiểm thử hoặc kiểm định chéo theo hành trình. Các quan sát của cùng một hành trình không được chia vào cả tập huấn luyện và tập kiểm thử.

### 3.5. Điều kiện chấp nhận phương pháp 2

Chỉ sử dụng quy tắc đỉnh–cuối làm phương pháp tổng hợp chính khi:

- Phương pháp 1 đã tạo được giá trị hóa trị đủ tin cậy hoặc có đánh giá hóa trị trực tiếp.
- Có đánh giá tổng thể độc lập sau hành trình.
- Định nghĩa điểm đỉnh đã được khóa trước thực nghiệm.
- Quy tắc đỉnh–cuối dự đoán đánh giá tổng thể tốt hơn hoặc có lợi thế thực tế rõ ràng so với trung bình và điểm cuối.
- Kết quả ổn định qua các phân vùng dữ liệu hoặc kiểm định chéo.

Nếu không đạt, quy tắc đỉnh–cuối chỉ được trình bày như giả thuyết đã kiểm tra và không được dùng để tạo kết luận chính.

---

## 4. Quan hệ giữa hai phương pháp

Hai phương pháp tạo thành chuỗi phụ thuộc:

```text
Ảnh tại điểm chạm
    → Mô hình FER hoặc mô hình hồi quy hóa trị
    → Giá trị hóa trị tại từng điểm chạm
    → Chuỗi hóa trị của hành trình
    → So sánh trung bình, điểm cuối và đỉnh–cuối
    → Dự đoán đánh giá tổng thể sau hành trình
```

Không thể kiểm chứng quy tắc đỉnh–cuối trước khi đầu vào hóa trị được kiểm chứng. Không thể kết luận điểm tổng hợp phản ánh trải nghiệm nếu không có đánh giá tổng thể độc lập của người tham gia.

---

## 5. Mã và đầu ra phải có trước khi viết báo cáo

### 5.1. Đặc tả và mã phương pháp 1

```text
MULTI_POINT_ANALYTICS/
├── TECH_SPEC_VALENCE.md
├── configs/
├── src/
│   ├── estimate_class_valence.py
│   ├── predict_valence.py
│   └── evaluate_valence.py
├── tests/
└── results/valence/
```

Đầu ra tối thiểu:

- Giá trị $\mu_k$ kèm số mẫu và độ lệch chuẩn của từng lớp.
- Dự đoán hóa trị cho từng ảnh kiểm thử.
- Bảng sai số của ba hướng dự đoán.
- Biểu đồ giá trị thật so với dự đoán.
- Phân bố hóa trị theo từng lớp.
- Tệp cấu hình và thông tin môi trường.

### 5.2. Đặc tả và mã phương pháp 2

```text
MULTI_POINT_ANALYTICS/
├── TECH_SPEC_PEAK_END.md
├── src/
│   ├── build_journeys.py
│   ├── aggregate_journey.py
│   └── evaluate_aggregators.py
├── tests/
└── results/peak_end/
```

Đầu ra tối thiểu:

- Chuỗi hóa trị của từng hành trình.
- Giá trị trung bình, điểm cuối và đỉnh–cuối của từng hành trình.
- Đánh giá tổng thể dùng làm nhãn kiểm chứng.
- Bảng sai số và tương quan của các phương pháp tổng hợp.
- Biểu đồ dự đoán so với đánh giá tổng thể.
- Phân tích độ nhạy theo định nghĩa điểm đỉnh.

Không đưa công thức hoặc kết luận vào Chương 3 trước khi hai thư mục kết quả được kiểm tra.

---

## 6. Quyết định hiện tại

Hai phương pháp có cơ sở để **nghiên cứu như các giả thuyết**, nhưng chưa đủ căn cứ để sử dụng nguyên trạng như phiên bản cũ.

1. Giữ ý tưởng quy đổi sang hóa trị, nhưng bỏ toàn bộ trọng số `+0,80…−0,80`. Trọng số phải được ước lượng từ dữ liệu hoặc thay bằng mô hình hồi quy trực tiếp.
2. Giữ quy tắc đỉnh–cuối như một mô hình cần so sánh, không mặc định là công thức đúng nhất.
3. Bổ sung đánh giá tổng thể sau hành trình làm nhãn kiểm chứng.
4. So sánh đỉnh–cuối với trung bình, điểm cuối và mô hình trọng số học từ dữ liệu.
5. Chỉ lựa chọn và viết vào phương pháp chính sau khi có mã, đầu ra và kết quả tái lập được.
