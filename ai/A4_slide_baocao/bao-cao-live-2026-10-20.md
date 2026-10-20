# Báo cáo thực nghiệm LLM — Nguyễn Nhật Lân, 20/10/2026

Đã chạy inference trên 11 instance ZAP đã làm sạch và benchmark SQLi 3 lượt/nhánh với model thật. Benchmark hiện tại cho kết quả wordlist thành công 3/3 lượt, AI tĩnh 0/3, AI feedback 0/3. Chưa có nhãn người review để kết luận Precision/Recall hoặc mức tiết kiệm thời gian.

## 1. Cấu hình và phạm vi

| Mục | Giá trị |
|---|---|
| Dịch vụ thực tế | Groq, `https://api.groq.com/openai/v1` |
| Adapter | OpenAI Python SDK; `AI_PROVIDER=openai` là tên adapter |
| Model yêu cầu | `qwen/qwen3.8-27b`; tên model trả về được ghi từng API call |
| Tham số | temperature 0; max_completion_tokens 1200; timeout 30 giây; SDK retries 0 |
| Quyền chạy | Cấu hình `AI_GROUP_APPROVED=1` và yêu cầu tiếp tục của người dùng |
| Dữ liệu Triage | `A1_ai_triage/review_bundle_v1/alerts.json`, 11 ID tại origin `http://localhost:3000` |
| Hash input LF trong manifest | `275f6d14f2f066fe4b1cda3d5ce18f70881e883c469e90ae1d16e6303eb917ea` |
| Hash byte input thực chạy (CRLF Windows) | `ef539a916009c976a2dcffc8028be270e7f9c45646299847fdda89f0d059e2e7` |
| Hash report ZAP nguồn | `fee6ce5be6ab6dc619ec23efa1b1054468c13a29f4847f4c6b27f5d8cad438bf` |
| Benchmark | HTTP local trên bản sao H3, cổng trống, database tạm riêng; không khởi động server gốc |
| Oracle | `proposed_sqlite_differential_v1`, cần nhóm rà soát; chỉ SQLi |

Không xác nhận phiên bản ZAP hoặc commit SUT tại thời điểm quét chỉ từ tên file. Manifest review giữ thông tin nguồn đã có; commit trong benchmark là checkout tại thời điểm thực nghiệm. Không lưu credential trong báo cáo/cache. Giá trị token do provider báo không bao gồm chi phí tiền được xác minh.

Manifest cũ ghi hash LF, checkout Windows chuyển ba file bundle sang CRLF. Đã đối chiếu nội dung với Git và hash sau chuẩn hóa LF: input cùng hai phiếu review không đổi. Run live ghi hash byte thực tế, không sửa manifest cũ để che khác biệt. [Inventory mới](../artifact_inventory_2026-10-20.json) giữ cả hash byte và hash LF; `.gitattributes` giữ LF cho artifact live mới.

## 2. Triage live và khả năng khôi phục

CLI `ai.A1_ai_triage.live` đọc `.env` tường minh qua dotenv, không thực thi nội dung file. Parser giữ đơn vị instance và ID của bộ dữ liệu đã khóa. Request dùng system prompt tách evidence không tin cậy; Structured Outputs được kiểm tra lại bằng Pydantic và phải trả đúng alert ID.

Mỗi alert ghi checkpoint bằng file tạm rồi thay thế output. Resume kiểm tra hash input/prompt/schema, cấu hình và tập ID trước khi tiếp tục; không gọi lại alert đã thành công. Mỗi lần lỗi giữ trong `attempts`, không chuyển sang mock. Output model chỉ là gợi ý, `final_decision=pending_human_review`.

Lượt đầu hoàn tất 11/11: model đề xuất P2 cho 1 alert, P3 cho 9 alert, P4 cho 1 alert; `is_real=true` cho 6 và `null` cho 5. Đây là phân bố dự đoán, không phải số lỗ hổng đã được xác minh. Có 14 API attempt: 11 thành công, 2 lỗi kết nối trong sandbox và 1 lỗi 429. Usage của 11 lần thành công là 4.600 token; usage của lần lỗi không được provider cung cấp. Thực hiện tiếp từ checkpoint với khoảng nghỉ giữa các lần gọi.

Đã hoàn tất ba lượt độc lập, mỗi lượt 11/11 ID trên cùng input/cấu hình. Các lượt lặp và usage được tính lại từ JSON bằng [công cụ tổng hợp](../summarize_live.py). Xem `live-summary-2026-10-20.json` cùng thư mục khi đánh giá dao động. Lượt đầu có gián đoạn/resume nên không dùng wall-clock của nó làm thời gian làm việc của người review.

| Lượt | Output hợp lệ | API attempt / lỗi | Token được báo | Phân bố P2/P3/P4 |
|---|---:|---:|---:|---|
| 1 (có resume) | 11/11 | 14 / 3 | 4.600 | 1 / 9 / 1 |
| 2 | 11/11 | 11 / 0 | 4.600 | 1 / 9 / 1 |
| 3 | 11/11 | 11 / 0 | 4.600 | 1 / 9 / 1 |

Ba lượt có cùng phân bố `true=6`, `null=5`. Tổng Triage 33 output hợp lệ, 13.800 token được báo. Cộng benchmark là 16.575 token được báo; không biết usage của ba attempt lỗi và chưa xác minh chi phí tiền.

Chưa tính TP/FP/FN, Precision/Recall, khớp nhãn ưu tiên, hoặc thời gian tiết kiệm: hai phiếu Như/Phát vẫn là biểu mẫu chưa gán nhãn. Các bản mẫu được giữ nguyên; không chuyển dự đoán AI thành ground truth.

## 3. Benchmark LLM thật

Cả ba nhánh dùng cùng seed/database lab, WAF bật ở level 1, reset trước mỗi lượt, trần 50 request tấn công/lượt và oracle giống nhau. Thứ tự xoay vòng qua ba lượt. Mỗi lượt có 4 request phụ: reset, kiểm tra WAF, snapshot sản phẩm và đối chứng tìm kiếm không khớp. Request launcher chờ server sẵn sàng nằm ngoài tổng benchmark.

AI tĩnh được sinh bằng một API call trả đúng 7 ứng viên, trước mọi phản hồi WAF, dùng lại cùng danh sách ở ba lượt. Nguồn/prompt/output/usage được lưu trong `static_generation`. AI feedback nhận lịch sử payload, HTTP status, `blocked_keyword` và checkpoint; tối đa 10 API call/lượt, không fallback heuristic. Model trả `should_stop=true` thì dừng và giữ nguyên kết quả chưa thành công.

| Nhánh | Thành công/lượt | Request đến lần đầu, từng lượt | Request tấn công tổng | Request phụ tổng | Lý do dừng |
|---|---:|---|---:|---:|---|
| Wordlist tĩnh | 3/3 | 5, 5, 5 | 15 | 12 | Đạt oracle |
| LLM tĩnh | 0/3 | Không đạt | 21 | 12 | Hết 7 ứng viên mỗi lượt |
| LLM feedback | 0/3 | Không đạt | 3 | 12 | Model dừng sau 1 request mỗi lượt |

Tổng 39 request tấn công + 36 request phụ = 75 request benchmark tới SUT; 7 API call riêng (1 sinh danh sách, 6 feedback), 2.775 token được provider báo. Không gán call sinh danh sách dùng chung ba lần cho từng lượt. N=50 là trần, không phải số request thực gửi.

Checkpoint dựng SQLite từ snapshot id/name, so sánh ID quan sát với truy vấn nối chuỗi và truy vấn parameterized. Chỉ ghi thành công khi có kết quả khác đối chứng an toàn, khớp truy vấn dễ lỗi và khớp dữ liệu snapshot. HTTP 200 đơn thuần hoặc status 403→200 không đủ chứng minh bypass.

Trong ba lượt feedback, model gửi giá trị có tiền tố `search=` rồi chủ động dừng sau 403. Runner gửi nguyên chuỗi do model trả về làm giá trị tham số, không tự sửa payload để tạo thành công. Danh sách AI tĩnh chủ yếu chứa mẫu OR/UNION thông thường và không vượt bộ lọc hiện tại. Kết quả phản ánh cả model lẫn prompt/interface này; không suy rộng sang mọi LLM, WAF hay ứng dụng. Ba lượt temperature 0 có kết quả giống nhau, không phải ba mẫu ngẫu nhiên độc lập về hiệu quả tổng quát.

## 4. Artifact, cache và cách tái lập

- [Input và manifest](../A1_ai_triage/review_bundle_v1/manifest.json).
- [Triage lượt 1](../A1_ai_triage/results/live_2026-10-20_run1.json), [lượt 2](../A1_ai_triage/results/live_2026-10-20_run2.json), [lượt 3](../A1_ai_triage/results/live_2026-10-20_run3.json).
- [Benchmark 9 lượt và checkpoint](../A2_fuzzer_benchmark/results/live_2026-10-20_v1.json).
- [Cache triage lượt 1](../A3b_video_cache/cache/triage_live_2026-10-20_run1.json), [cache benchmark](../A3b_video_cache/cache/fuzzer_live_2026-10-20_v1.json).
- [Số liệu tính lại](live-summary-2026-10-20.json), [slide để ghép bài chung](slide-live-2026-10-20.md).

```powershell
python -X utf8 -m unittest discover -s ai/tests -v
python -X utf8 -m ai.A1_ai_triage.live --output ai/outputs/new-triage.json
python -X utf8 -m ai.A1_ai_triage.live --output ai/outputs/new-triage.json --resume
python -X utf8 -m ai.A2_fuzzer_benchmark.isolated_lab --mode live --output ai/outputs/new-benchmark.json
python -X utf8 -m ai.A3b_video_cache.artifacts --source ai/A3b_video_cache/cache/fuzzer_live_2026-10-20_v1.json --replay
```

CLI live mặc định nghỉ 20 giây giữa các lần gọi; lượt triage lặp sử dụng `--interval 15`. Mọi lượt mới phải dùng output mới. Resume chỉ gọi alert còn thiếu; benchmark lỗi giữ artifact và chạy lại bằng tên mới. Cache có hash nguồn và payload, replay kiểm tra hash và không gọi mạng. Playback L2 cũ đã bỏ việc tạo kịch bản thành công khi thiếu cache, lời thoại AI tự chèn và tỷ lệ tiết kiệm 85,7% cố định.

## 5. Kiểm chứng và phần còn phụ thuộc

43 unittest qua, gồm kiểm tra khôi phục sau lỗi, từ chối resume khác input, lỗi API không gửi heuristic, checkpoint riêng từng attempt, cache/replay và playback thiếu dữ liệu. Test dùng HTTP giả; bằng chứng inference thật nằm ở artifact live riêng. Benchmark hoàn tất 9 lượt, snapshot nhất quán, nguồn được hash trước/sau và không đổi trong lượt chạy.

| Phần còn cần người phụ trách | Đầu vào còn thiếu |
|---|---|
| Như/Phát — nhãn độc lập | Phiếu review đã làm và biên bản chốt bất đồng; protocol kiểm soát việc đã xem AI |
| Như — N3 | Tập chấm, công thức/mẫu số, số liệu review thủ công và có AI |
| Hùng/Long/nhóm | Rà soát oracle/điều kiện so sánh, phản hồi kết quả benchmark |
| Long/Phát — video và ghép bài | Clip L3, mẫu trình bày chung; hiện mới có nội dung slide Markdown và cache để quay |

Chưa có video quay/ghép hoặc file slide theo mẫu nhóm. Nội dung kỹ thuật và dữ liệu inference đã sẵn sàng bàn giao; đánh giá chất lượng và kết luận cuối chờ các đầu vào trên.
