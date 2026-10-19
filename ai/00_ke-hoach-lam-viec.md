# Kế hoạch A1–A4 của Nguyễn Nhật Lân

**MSSV:** 23120289. **Ngày:** 16/10/2026. **Nhánh:** `lan/ai-workspace`.

Đối chiếu [bảng phân công](../docs/de-cuong-seminar.md) và [proposal](../docs/ai_proposal.md), đặc biệt mục 8–9. Thư mục này thực hiện yêu cầu dựng workspace trong `prompt.md`, không xác nhận thay nhóm các quyết định còn mở.

> TỰ ĐỀ XUẤT - CHƯA chốt với nhóm, cần Lân/nhóm xác nhận lại: mọi mặc định kỹ thuật dưới đây là phương án bàn giao để tích hợp, không phải quyết định đã được nhóm/GVTH duyệt.

## A3a: Giao diện AI dùng chung, bàn giao sớm

| Mục | Nội dung |
|---|---|
| Mô tả | Cấu hình model/provider, kiểm tra JSON, cung cấp `classify_alert()` cho A1 và `suggest_payload()` cho Long/L2. |
| Trạng thái | Không block đối với việc lập trình giao diện; sử dụng API thật cần nhóm duyệt cấu hình và có key hợp lệ. |
| Lý do block (nếu có) | Không chờ module khác để viết adapter. Chưa xác nhận tài khoản, ngân sách, model cuối cùng hoặc quyền gửi alert đến dịch vụ bên ngoài. |
| Đã làm trong lần này | Có: `.env.example`, `config.py`, `contracts.py`/`contracts.json`, adapter SDK thật, mock tách biệt và test bằng HTTP giả. Chưa gọi API thật. |
| Giả định tự đề xuất (nếu có) | TỰ ĐỀ XUẤT - CHƯA chốt với nhóm, cần Lân/nhóm xác nhận lại: OpenAI, snapshot `gpt-4.1-mini-2025-04-14`, temperature 0, tối đa 1200 completion token, timeout 30 giây, không tự retry, schema `lan-ai-v1-proposed`. |

**Bàn giao cho Long ngay:** [README tích hợp](A3a_ai_config/README.md), [schema](A3a_ai_config/contracts.json), input `PayloadRequest` và output `PayloadSuggestion`. Adapter chỉ gợi ý một input; Long vẫn sở hữu vòng lặp gửi request, feedback, budget thực tế và stop condition L2.

## A1: AI Vulnerability Triage

| Mục | Nội dung |
|---|---|
| Mô tả | Chuẩn hóa JSON ZAP, phân loại/đề xuất ưu tiên theo alert ID, giữ toàn bộ alert cho người review. |
| Trạng thái | Block một phần. |
| Lý do block (nếu có) | Chờ Hùng/H1 giao JSON alert thật đã xử lý secret, commit SUT, phiên bản ZAP, scope và format export. Hết block khi đối chiếu parser trên dữ liệu đó và nhóm chốt đơn vị record/ID. |
| Đã làm trong lần này | Khung sườn đầy đủ + chạy mock: parser flat/native ZAP, prompt, CLI, output sáu trường, ba alert mẫu tự tạo và test. Không bỏ alert, không tạo nhãn chuẩn. |
| Giả định tự đề xuất (nếu có) | TỰ ĐỀ XUẤT - CHƯA chốt với nhóm, cần Lân/nhóm xác nhận lại: một ZAP instance là một record; ID băm từ nội dung chuẩn hóa nếu thiếu ID; CWE chưa biết là null; schema evidence status ba giá trị. Mock P3 chỉ là fixture kỹ thuật. |

**Sau khi có H1:** kiểm tra mapping, khóa bộ input và ID cùng Như/Phát trước khi gán nhãn độc lập; không cho người gán nhãn xem output AI trước khi khóa nhãn. Chạy live sau khi duyệt A3a; chuyển kết quả A1 cho Như làm N3. Không tính Precision/Recall thay Như.

## A2: Benchmark Fuzzer

| Mục | Nội dung |
|---|---|
| Mô tả | Khung so sánh wordlist tĩnh, AI tĩnh và AI feedback trong cùng điều kiện. |
| Trạng thái | Block hoàn toàn đối với benchmark thật. |
| Lý do block (nếu có) | Chờ bộ lọc H3 của Hùng, module L2 của Long, API bật/tắt/reset, input/feedback và checkpoint được Như/Phát rà soát. Hết block khi có đủ giao diện, bộ dữ liệu và định nghĩa thành công từng loại lỗi được nhóm xác nhận. |
| Đã làm trong lần này | Khung sườn: `run_branch(...)` chủ động báo `DependencyBlockedError`, không gửi request; lệnh tạo CSV/JSON rỗng và test. |
| Giả định tự đề xuất (nếu có) | TỰ ĐỀ XUẤT - CHƯA chốt với nhóm, cần Lân/nhóm xác nhận lại: N=50 request SUT/nhánh/lượt; ít nhất ba lượt/nhánh theo proposal; tên nhánh và log sáu cột; định nghĩa bypass tạm bên dưới. |

**Bypass tạm đề xuất:** status không thuộc `{400, 403}` **VÀ** có hiệu ứng đúng kỳ vọng được checkpoint xác minh. Status 200, 500, redirect hoặc việc không bị chặn đơn thuần không chứng minh bypass. Nhóm phải chốt cách xác minh SQLi/XSS, cách tính request phụ/retry/reset, input hợp lệ đối chứng và chi phí API AI tách khỏi N request SUT. Hiện chưa có logic chấm hoặc kết quả đo.

## A3b: Cache và video AI

| Mục | Nội dung |
|---|---|
| Mô tả | Lưu kết quả, quay Triage và ghép clip Fuzzer L3 thành video AI. |
| Trạng thái | Block hoàn toàn đối với cache kết quả và video thật. |
| Lý do block (nếu có) | Chờ N3 của Như, kết quả A1/A2 và clip L3 của Long. Hết block khi có log thật đã rà soát secret, số liệu có nguồn và clip được phép dùng. |
| Đã làm trong lần này | Khung sườn: hai cache rỗng, `is_replay: true`, timestamp/hash null, quy trình kiểm tra và ghép video. Chưa có cache inference hoặc clip thật. |
| Giả định tự đề xuất (nếu có) | TỰ ĐỀ XUẤT - CHƯA chốt với nhóm, cần Lân/nhóm xác nhận lại: metadata replay, nguồn dữ liệu và hash; phương án video trong README. |

**Không diễn giải cache rỗng là kết quả.** Kết quả ghi mới có `is_replay: false` chỉ trong lượt chạy mới; khi hiển thị lại phải gắn `is_replay: true` và thông báo rõ trên video, không đổi nguồn mock thành live.

## A4: Slide và báo cáo

| Mục | Nội dung |
|---|---|
| Mô tả | Trình bày triển khai Triage, phương pháp đối chứng và giới hạn, bàn giao để Phát ghép bài chung. |
| Trạng thái | Block hoàn toàn đối với nội dung kết quả cuối. |
| Lý do block (nếu có) | Chờ A1–A3 có minh chứng thật và N3 có benchmark/nhãn đã chốt; số liệu Fuzzer lấy từ A2 với Long xác minh. Hết block khi dữ liệu, clip và bảng chấm được chủ phần xác nhận. |
| Đã làm trong lần này | Khung sườn: outline slide/báo cáo; tất cả phần thực nghiệm ghi `[CHỜ SỐ LIỆU THẬT]`. |
| Giả định tự đề xuất (nếu có) | TỰ ĐỀ XUẤT - CHƯA chốt với nhóm, cần Lân/nhóm xác nhận lại: bố cục bài; không tự khẳng định đạt ngưỡng Recall/tiết kiệm thời gian. |

## Giả định và câu hỏi cần chốt

Tất cả các dòng sau đều **TỰ ĐỀ XUẤT - CHƯA chốt với nhóm, cần Lân/nhóm xác nhận lại**.

| Giả định hiện dùng | Câu hỏi cụ thể / người cần trả lời |
|---|---|
| OpenAI, `gpt-4.1-mini-2025-04-14`, cloud API | Nhóm chọn đúng provider/model/snapshot nào, tài khoản nào chi trả và có được gửi alert đã làm sạch ra dịch vụ đó không? |
| Temperature 0; completion token 1200; timeout 30s; retries 0 | Long/Lân có đồng ý cố định các giá trị này cho cả benchmark và cách xử lý lỗi API không? |
| Chưa đặt trần chi phí tiền hoặc tổng lượt gọi AI; không tự gọi API trong lần này | Nhóm cho phép tối đa bao nhiêu tiền/lượt gọi AI và ai theo dõi chi phí trước khi mở live? |
| N=50 request SUT/nhánh/lượt; tối thiểu ba lượt/nhánh | Nhóm có chốt N=50 không; request đối chứng, reset, xác minh và retry có tính vào N hay ghi riêng? |
| Bypass tạm = không bị chặn (status khác 400/403) và checkpoint có hiệu ứng thật | Hùng/Long đề xuất oracle cụ thể nào cho SQLi và XSS; Như/Phát có duyệt đối chứng và tiêu chí thành công không? |
| Log `branch,attempt_no,payload,response_code,bypass,note`; JSON wrapper có metadata | Long/Hùng có đồng ý giao diện log này; sẽ biểu diễn timeout/chưa đủ bằng chứng ra sao thay vì ép thành bypass false? |
| Input Triage gồm `alert_id,name,risk,url,param,evidence,cweid`; output sáu trường theo schema | H1/N3 có dùng được hợp đồng `contracts.json` không; các enum và nullable `is_real` có cần đổi trước khi khóa dữ liệu? |
| Payload input gồm target URL, SQLi/XSS, previous attempts và remaining requests; output payload/reason/should_stop | Long có cần trường feedback nào thêm không; format và stop condition nào phải thống nhất với H3 trước L2? |
| Target của adapter payload chỉ nhận localhost/127.0.0.1/::1, không gửi request tới target | Môi trường Docker của Hùng/Long có truy cập qua loopback được không, hay nhóm cần phê duyệt allowlist lab khác? |
| Một instance = một record; sinh ID ổn định từ nội dung đã làm sạch; duplicate bị từ chối | Hùng/Như/Phát thống nhất đơn vị nào, cách xử lý duplicate và khóa ID/dataset ở mốc nào? |
| Không ép số alert; CWE chưa biết/risk lạ giữ null/Unknown; ba trạng thái bằng chứng | H1 sẽ bàn giao bao nhiêu record thực tế và N3 sẽ xử lý trường hợp chưa đủ bằng chứng như thế nào? |
| Replay có nhãn, cache lưu nguồn/hash/thời điểm; bố cục slide/video mới là khung | Như/Long/Phát chốt thời hạn bàn giao log/clip, định dạng video và mẫu slide chung nào? |

## Thứ tự tiếp tục

1. Lân bàn giao A3a cho Long và gửi bảng câu hỏi trên cho nhóm; chốt model/schema trước khi đo.
2. Nhận H1, đối chiếu parser và khóa ID/input với Như/Phát; mỗi người gán nhãn độc lập, Lân không tạo nhãn chuẩn.
3. Hoàn thiện A1 trên dữ liệu thật; Như thực hiện N3. Sau khi H3/L2 sẵn sàng mới nối và chạy A2.
4. Nhận N3/L3, tạo cache thật đã làm sạch, quay/ghép video A3b; điền A4 từ dữ liệu có nguồn, bàn giao Phát.

Kiểm chứng kỹ thuật hiện tại: 30/30 unittest qua bằng dữ liệu mẫu/HTTP giả. Đây không phải bằng chứng hiệu quả của AI. Chưa có hạn mới được cung cấp nên không tự đặt deadline thay nhóm.
