# Kiểm tra độc lập LLM feedback — 25/10/2026

> Bản bàn giao mới nhất: [log người dùng tự chạy đủ 9 lượt](../A2_fuzzer_benchmark/results/live_manual_check_02.json) xác nhận feedback 3/3 với 4 request/lượt; xem [bản bàn giao](ban-giao-benchmark-2026-10-25.md). Phần dưới giữ kết quả của lần xác minh trước.

> Cập nhật sau lần chạy lại: đã hoàn tất đủ 9 lượt, feedback 3/3 với 1 request/lượt; xem [báo cáo mới](bao-cao-live-2026-10-25.md). Nội dung dưới đây ghi nhận lần kiểm tra ban đầu bị 429; không còn là kết luận mới nhất. Log đồng đội vẫn chưa có để đối chiếu.


Chưa đủ bằng chứng xác nhận tuyên bố **3/3 lượt, khoảng 4 request/lượt**. Chạy độc lập xác nhận một lượt feedback đạt oracle sau 4 request; lượt tiếp theo bị provider giới hạn HTTP 429, khiến toàn bộ benchmark chưa hoàn tất. Giữ nguyên slide và báo cáo lịch sử 20/10, chưa thay kết luận bằng số liệu dự đoán.

## Nhánh và bảo toàn dữ liệu

- Đã `fetch origin`; nhánh làm việc local `update/benchmark-results` tách từ `origin/fix/llm-feedback-adaptation`, commit `61e87bc3b272a55cf1b9366762fad1a0ed034212`.
- Nhánh ban đầu có tên local viết khác: `fix/llm-feedback-adpatation`.
- Thay đổi dở được lưu trong stash `Backup before independent feedback benchmark review 2026-10-25`; stash cũ vẫn giữ nguyên. Không push, merge hay commit trong lần kiểm tra này.

## Review code

So với `origin/main`, nhánh chỉ có commit `61e87bc` sửa hai file:

- `ai/A3a_ai_config/client.py`: yêu cầu model trả giá trị tham số thuần; khi bị chặn, phân tích `blocked_keyword` và thử biến đổi tương đương (prompt nêu ví dụ comment, dấu ngoặc, toán tử); chỉ dừng khi hết ngân sách hoặc lỗi hệ thống nghiêm trọng.
- `ai/A2_fuzzer_benchmark/live.py`: bỏ khoảng trắng/dấu quote/backtick ở biên và tiền tố `search=` khỏi payload feedback trước khi gửi.

Luồng feedback đã tồn tại từ trước: `offline.run_branch` ghi payload, HTTP status, `blocked_keyword`, checkpoint vào `attempts`; `propose` gửi lịch sử đó qua `previous_attempts` cùng ngân sách còn lại. Vòng lặp vẫn dừng khi oracle xác nhận thành công, model yêu cầu dừng, hết ngân sách, hết trần API call hoặc gặp lỗi. Không fallback heuristic khi API thất bại.

Không thấy hardcode payload thắng mới, đọc đáp án từ test, tắt WAF hay nới lỏng oracle. Các file `offline.py`, WAF, database và server lab không đổi. Oracle vẫn đòi kết quả khớp truy vấn nối chuỗi, khác truy vấn parameterized và khớp snapshot; HTTP 200 đơn thuần chưa đủ.

Các giới hạn cần giữ trong kết luận:

- Prompt được chia sẻ với LLM static, nên thay đổi cũng ảnh hưởng static generation. Không được mặc định số liệu static mới bằng số liệu cũ.
- Đây là phép thử có thông tin về cấu trúc truy vấn và checkpoint; prompt gợi ý sẵn kỹ thuật biến đổi. Không phải đánh giá black box hay bằng chứng LLM tự khám phá kỹ thuật hoàn toàn mới. Bối cảnh truy vấn và checkpoint đã có trước bản sửa.
- Prompt mới bỏ câu coi HTTP/payload cũ là dữ liệu không tin cậy và câu không suy ra bypass từ status. Oracle bên ngoài vẫn kiểm chứng, nhưng chỉ dẫn chống prompt injection bị giảm.
- Chuẩn hóa payload kiểm tra rỗng trước khi bỏ tiền tố: `search=` có thể thành chuỗi rỗng; `search="phone"` thành `"phone` do bỏ quote ở biên trước khi bỏ tiền tố. Đây là trường hợp biên cần sửa/test thêm, không phải bằng chứng gian lận. Không sửa code chiến lược trong lần review này.
- Oracle vẫn ghi `pending_group_review`; chưa đánh giá XSS hoặc WAF khác.

Quét cả 270 file được theo dõi bằng mẫu provider key/private key không phát hiện secret; diff chỉ có hai file Python, không có `.env` thật được commit. Quét mẫu không đảm bảo phát hiện mọi dạng secret. Trước khi xuất bằng chứng, cũng kiểm tra log không chứa giá trị key đang dùng; không in giá trị key.

## Tìm log đồng đội

Không tìm thấy `ai/outputs/live_run_lan_env.json` trong working directory hoặc lịch sử Git đã fetch. Tìm cả JSON bị ignore không thấy log live khác phù hợp tuyên bố. `ai/outputs/*` bị ignore, nên có khả năng log chỉ nằm trên máy đồng đội; chưa thể xác nhận nguyên nhân.

Các file gần nghĩa đã kiểm tra:

- `demo/ai_fuzzer/benchmark_results.json`: feedback mang mode `live_local_lab_offline_heuristic`, không chứng minh LLM feedback gọi model.
- `ai/A2_fuzzer_benchmark/results/offline_v1.json`: `model_inference_performed=false`, feedback heuristic 2 request/lượt; không phải log live được nêu.
- `ai/A2_fuzzer_benchmark/results/live_2026-10-20_v1.json`: log live cũ, feedback 0/3.

`Lan/.env` không tồn tại trong workspace này. `ai/.env` có key và cờ cho phép live; lần chạy mạng xác nhận gọi model được. Không xác minh được đồng đội đã dùng key từ file nào.

## Số liệu đối chiếu

“Request/lượt” dưới đây là request tấn công thực gửi, bao gồm các lượt không thành công. Không coi số request thấp ở lượt lỗi là lợi thế.

| Chiến lược | Cũ: thành công | Cũ: request/lượt | Cũ: tổng tấn công / tổng SUT | Xác minh 25/10: các lượt đã ghi | Mới: request/lượt | Mới: tổng tấn công / tổng SUT |
|---|---|---|---|---|---|---|
| Wordlist | 3/3 | 5, 5, 5 | 15 / 27 | 1 thành công; 2 lượt chưa chạy | 5 | 5 / 9 |
| LLM static | 0/3 | 7, 7, 7 | 21 / 33 | 0 thành công trong 2 lượt; 1 lượt chưa chạy | 7, 7 | 14 / 22 |
| LLM feedback | 0/3 | 1, 1, 1 | 3 / 15 | Lượt 1 thành công; lượt 2 lỗi API 429 trước tấn công; lượt 3 chưa chạy | 4, 0 (lỗi API) | 4 / 12 |

Cũ: **39 tấn công + 36 phụ = 75 request SUT**. Lần xác minh chưa hoàn tất: **23 tấn công + 20 phụ = 43 request SUT** qua 5 row, không phải benchmark đủ 9 lượt. Request launcher chờ lab sẵn sàng nằm ngoài các tổng này. Có 6 API call: 5 thành công (1 sinh danh sách, 4 feedback) và 1 lỗi 429.

Một lượt feedback dùng 4 so với 5 request tấn công của Wordlist: ít hơn 1 request (20%) trong lượt đó. Chưa suy ra kết quả 3/3, nhanh hơn về thời gian, tiết kiệm tiền hay ưu thế tổng quát; feedback còn tốn API call và thời gian chờ.

## Bằng chứng và kiểm thử

- `python -X utf8 -m unittest discover -s ai/tests -v`: **43/43 pass**. Đây là test phần mềm với fake API, không phải 43 lần kiểm chứng hiệu quả model.
- Lần live trong sandbox: `ai/outputs/live_verify_2026-10-25_independent.json`, `incomplete`, lỗi `APIConnectionError`, chưa có row.
- Lần live có quyền mạng: `ai/outputs/live_verify_2026-10-25_network_retry.json`, `incomplete`, 5 row; dừng ở `RateLimitError`, HTTP 429. Không ghi đè log nào.
- [Bản sao nguyên byte của log xác minh chưa hoàn tất](../A2_fuzzer_benchmark/results/live_verify_2026-10-25_partial.json), đưa vào thư mục không bị ignore để có thể bàn giao bằng Git. SHA-256: `2e0c015943c2d102cde88d597362cb9f1ee29dce1f6e161fe1cf8241363ba578`.
- Model trả kết quả theo cấu hình `qwen/qwen3.8-27b`, temperature 0, trần 1.200 completion token. Không in key.
- Tự tính lại từ log: cả 5 row cùng snapshot hash; các source hash vẫn khớp file hiện tại. Trường `snapshot_consistent`/`sources_unchanged` ở report chưa được runner ghi vì thoát sớm, không tự sửa log để thêm trạng thái hoàn tất.
- Log cũ và cache cũ có blob Git giống hệt commit `9fd8512`: lần lượt `aa4d280f52f2c89c4bc290c88bb4381c236137e9` và `a64be7ef089702787d6317743704420322554e03`. Diff so với main không đổi hai file; lịch sử log gốc chỉ có commit `9fd8512`.

## Tài liệu và bước tiếp

Chưa thay số liệu trên slide, README, báo cáo hay biểu đồ vì thiếu log đồng đội và chưa chạy đủ 3 lượt. Vị trí cần cập nhật sau khi xác minh đủ:

- `ai/A4_slide_baocao/slide-live-2026-10-20.md`, Slide 5: bảng kết quả và lời trình bày; đây là nội dung slide live tìm được. Chưa thấy file biểu đồ cột hoặc script vẽ chart tương ứng trong repo.
- `ai/README.md`, `ai/A2_fuzzer_benchmark/README.md`, `ai/bao-cao-tien-do-lan.md`, `ai/01_ke-hoach-hoan-thien-lan.md`: thêm cập nhật có ngày và nguồn log mới.
- `ai/A4_slide_baocao/bao-cao-live-2026-10-20.md`: giữ bảng lịch sử, liên kết báo cáo mới thay vì viết lại dữ liệu 20/10.
- `ai/A4_slide_baocao/slide-outline.md`: đổi liên kết bản trình bày mới khi đã đủ bằng chứng.
- `ai/summarize_live.py`: script đọc số liệu từ log, không hardcode kết quả; khi có log hoàn tất, tạo summary mới, không ghi đè `live-summary-2026-10-20.json`.
- Hai bản `noi-dung-thuyet-trinh-lan.md` trong `ai/A4_slide_baocao/` và `docs/slide-seminar/` đang mô tả benchmark offline 5/6/2; cần phân biệt chúng với slide live, không thay số liệu offline bằng kết quả model.

Đề nghị lấy log gốc từ đồng đội để đối chiếu provenance/hash, kiểm tra hạn mức provider rồi chạy lại đủ 9 row với đường dẫn mới, ví dụ:

```powershell
python -X utf8 -m ai.A2_fuzzer_benchmark.isolated_lab --mode live --output ai/outputs/live_verify_2026-10-25_full_retry.json
```

Chỉ công bố 3/3 khi log đủ ba lượt mỗi chiến lược và `status=completed`, snapshot/source hash nhất quán. Sau đó mới cập nhật slide và biểu đồ ba chiến lược, phân biệt request tấn công, request phụ, API call và thời gian. Các log trong `outputs/` vẫn bị ignore; bản sao bằng chứng ở `results/` có thể được add cùng báo cáo này khi người dùng muốn commit/push nhánh.
