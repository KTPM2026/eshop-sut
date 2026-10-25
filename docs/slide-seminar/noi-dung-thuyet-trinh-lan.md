# Nội dung thuyết trình phần Nguyễn Nhật Lân

> Cập nhật 25/10/2026: tài liệu này giữ phần trình bày benchmark offline (5/6/2). Khi trình bày kết quả LLM live mới, dùng [Slide 5 đã cập nhật](../../ai/A4_slide_baocao/slide-live-2026-10-20.md): Wordlist 3/3, static 0/3, feedback 3/3; request tấn công/lượt 5/7/4. Không dùng các nhận định chưa gọi model dưới đây để mô tả lần live mới.

**Chủ đề nhóm:** Security Testing in Website — môn Testing.  
**Thời lượng:** 3–4 phút, **3 slide trong tổng 10 slide của nhóm**.  
**Căn cứ:** tài liệu và kết quả cập nhật ngày 18/10/2026.

Chỉ đưa phần “Nội dung trên slide” vào PowerPoint. Lời thuyết trình và ghi chú dùng để chuẩn bị, không tạo thêm slide. Khi ghép bài, đánh số slide theo thứ tự chung của nhóm.

## Slide 1 — Chuẩn hóa cảnh báo và pipeline AI Triage

### Nội dung trên slide

**ZAP JSON → Lọc backend → Chuẩn hóa → AI Triage → Người review**

- Đã chuẩn hóa **11 instance cảnh báo** của backend EShop.
- Xây dựng parser, ID đối chiếu và giao diện AI dùng chung.
- Triage: gợi ý tính xác thực, ưu tiên và lý do; người review quyết định.
- **Hiện tại:** kiểm tra pipeline bằng mock; chưa chạy AI cloud và chưa có Precision/Recall.

### Lời thuyết trình — khoảng 1 phút

“Phần em thực hiện tập trung vào xử lý cảnh báo và đánh giá kết quả kiểm thử bảo mật.

Đầu tiên, em xây dựng parser đọc báo cáo ZAP, lọc đúng phạm vi backend EShop và chuẩn hóa được 11 instance cảnh báo. Mỗi record có ID để đối chiếu dữ liệu gốc, kết quả phân tích và nhận xét của người review. Đây là 11 cảnh báo cần xác minh, chưa phải 11 lỗ hổng đã được xác nhận.

Tiếp theo, em xây dựng pipeline AI Triage, tức hỗ trợ nhận định cảnh báo và gợi ý ưu tiên xử lý. Giao diện AI dùng chung kiểm tra định dạng đầu ra; quyết định cuối vẫn thuộc người review.

Hiện tại, pipeline đã được kiểm tra bằng mock nhưng chưa chạy model cloud. Bộ review độc lập đã được chuẩn bị, còn chờ chốt nhãn nên chưa có Precision hay Recall.”

## Slide 2 — Thiết kế benchmark Fuzzer và tiêu chí thành công

### Nội dung trên slide

- **3 nhánh:** wordlist, danh sách cố định, heuristic theo phản hồi.
- **Đối chứng:** cùng dữ liệu, WAF level 1; reset mỗi lượt; trần 50 request tấn công/lượt; 3 lượt/nhánh.
- **Oracle SQLi:** kết quả backend khớp SQL ghép chuỗi và khác truy vấn dùng tham số.
- **HTTP 200 chưa đủ để kết luận thành công.** Oracle đề xuất đang chờ nhóm review.

### Lời thuyết trình — khoảng 1 phút

“Phần thứ hai là benchmark Fuzzer. Em tích hợp lab của bạn Hùng và cơ chế heuristic từ Fuzzer của bạn Long để so sánh ba cách cung cấp đầu vào: wordlist, danh sách cố định và điều chỉnh theo phản hồi.

Mỗi nhánh chạy ba lượt trên lab tách biệt, cùng dữ liệu, cùng WAF level 1 và cùng trần 50 request tấn công. Trước mỗi lượt, chương trình reset và xác minh WAF; khi đạt checkpoint thì dừng sớm.

Điểm chính là test oracle, tức tiêu chí xác định lần thử thành công. HTTP 200 có thể chỉ là tìm kiếm bình thường. Vì vậy, em so sánh ID kết quả backend với truy vấn SQL ghép chuỗi và truy vấn dùng tham số trên cùng snapshot. Checkpoint chỉ đạt khi có dữ liệu hợp lệ, khớp truy vấn dễ bị tác động và khác đối chứng an toàn.

Oracle này dành cho SQL Injection trong lab hiện tại và còn chờ nhóm review.”

## Slide 3 — Kết quả thực nghiệm và đóng góp

### Nội dung trên slide

| Chiến lược | Request tấn công đến checkpoint ở 3 lượt |
|---|---|
| Wordlist | 5 / 5 / 5 |
| Danh sách cố định | 6 / 6 / 6 |
| Heuristic feedback | 2 / 2 / 2 |

- **9/9 lượt đạt oracle đề xuất** trên lab; không gọi AI cloud.
- Log/cache có hash để đối chiếu; báo cáo ghi **38/38 unittest pass**.
- **Nhận xét:** heuristic dùng ít request hơn trong cấu hình này; cần thêm thực nghiệm để khái quát.

### Lời thuyết trình — khoảng 1 phút

“Kết quả đã lưu cho thấy wordlist đạt checkpoint sau năm request tấn công, danh sách cố định sau sáu request và heuristic feedback sau hai request ở mỗi lượt. Cả chín lượt đều đạt oracle đề xuất.

Trong cấu hình này, heuristic feedback dùng ít request hơn hai danh sách cố định. Đây là HTTP thật đến lab, nhưng các chiến lược đều chạy offline, chưa gọi LLM cloud. Ba lượt cùng điều kiện cũng chưa đủ để kết luận hiệu quả trên nhiều website hoặc WAF khác.

Em lưu log và cache kèm hash để đối chiếu nguồn dữ liệu. Báo cáo hiện ghi nhận 38 trên 38 unittest pass cho phần triển khai; số này chưa phản ánh độ chính xác AI hay mức an toàn của website.

Đóng góp chính của em là chuẩn hóa cảnh báo và xây dựng phép đo có đối chứng, kết luận dựa trên hiệu ứng backend. Bước tiếp theo là duyệt oracle, hoàn thành nhãn độc lập và chạy AI live để đánh giá Triage.”

## Ghi chú khi được hỏi — không đưa lên slide

- **AI đã chạy thật chưa?** Chưa chạy model cloud. Pipeline Triage được kiểm tra bằng mock/HTTP giả; benchmark gửi HTTP thật đến lab bằng các chiến lược offline.
- **Vì sao chưa có Precision/Recall?** Chưa có output AI live và nhãn chuẩn đã chốt. Hai bộ review độc lập được chuẩn bị cho Như và Phát.
- **HTTP 200 có chứng minh SQLi không?** Chưa đủ. Trong log, request thứ ba của nhánh wordlist trả HTTP 200 nhưng không đạt checkpoint vì không có hiệu ứng SQLi.
- **Heuristic nhanh hơn 2,5 lần?** Chỉ nên nói dùng 2 request so với 5 request trong cấu hình này. Số request và thời gian thực thi là hai đại lượng khác nhau.
- **38 test pass có nghĩa website an toàn?** Các test kiểm tra hành vi phần triển khai trong ai/; đánh giá website cần bằng chứng bảo mật riêng.
- **Tổng request:** 39 request tấn công + 36 request phụ benchmark. Request launcher chờ server sẵn sàng nằm ngoài tổng này.
- **Tên nhánh:** dùng fixed_candidates và heuristic_feedback; chưa xác minh nguồn sinh AI của danh sách cố định.

## Nguồn đối chiếu — không tạo slide riêng

- [Trạng thái mới nhất](../README.md), [báo cáo tiến độ](../bao-cao-tien-do-lan.md).
- [Bundle review độc lập](../A1_ai_triage/review_bundle_v1/README.md).
- [Kết quả benchmark](../A2_fuzzer_benchmark/results/offline_v1.json).
- [Checkpoint và runner](../A2_fuzzer_benchmark/offline.py).
- [Cache và replay](../A3b_video_cache/README.md).

Con số 38/38 là kết quả được ghi trong tài liệu bàn giao; không chạy lại test hoặc benchmark khi biên soạn nội dung này.

