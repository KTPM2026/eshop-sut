# Nội dung slide bàn giao — Lân, 20/10/2026

Nội dung Markdown để Phát ghép vào mẫu chung. Nguồn: [báo cáo live](bao-cao-live-2026-10-20.md).

## Slide 1 — Phần triển khai

- A1: chuẩn hóa ZAP, giữ ID, gợi ý phân loại và ưu tiên.
- A3a: cấu hình model, schema, redaction, adapter và log API.
- A2: benchmark wordlist/AI tĩnh/AI feedback trên H3 tách biệt.
- A3b: cache có hash, replay không gọi mạng.

Lời trình bày: “Em nối dữ liệu ZAP với model, kiểm tra bằng schema và giữ lại cho người review. Với Fuzzer, em đo từng request và checkpoint.”

## Slide 2 — Dữ liệu và model thật

- 11 instance từ origin `http://localhost:3000`; input/ID đã khóa hash.
- Groq, model `qwen/qwen3.8-27b`, OpenAI-compatible SDK.
- Temperature 0; tối đa 1.200 completion token; không tự retry/fallback.
- Output phải đúng schema và ID; chưa là quyết định cuối.

Lời trình bày: “Tên adapter là OpenAI, nhưng endpoint và model thực tế ở Groq. Em lưu model trả về, latency và usage từng call để truy vết.”

## Slide 3 — Kết quả Triage

- Inference thật trên đủ 11 ID, lưu từng lượt độc lập.
- Lượt 1: P2 = 1, P3 = 9, P4 = 1; true = 6, chưa kết luận = 5.
- Checkpoint giữ kết quả khi mất kết nối hoặc 429; resume chỉ chạy ID thiếu.
- Precision/Recall và thời gian tiết kiệm: chưa có nhãn/thời gian review để tính.

Lời trình bày: “Đây là phân bố dự đoán. Chưa thể nói có sáu lỗi thật vì còn cần nhãn độc lập và đối chiếu của Như/Phát.”

## Slide 4 — Thiết kế benchmark

- Lab sao chép H3, database tạm riêng; reset WAF level 1 trước mỗi lượt.
- Ba lượt/nhánh, xoay thứ tự; trần 50 request tấn công/lượt.
- AI tĩnh: sinh 7 ứng viên trước feedback, dùng lại cả ba lượt.
- Feedback: nhận lịch sử và checkpoint; tối đa 10 API call/lượt.
- Oracle so hiệu ứng SQLite với truy vấn parameterized; chỉ SQLi.

Lời trình bày: “HTTP 200 chưa chứng minh SQLi. Kết quả phải khớp truy vấn dễ lỗi và khác truy vấn an toàn trên cùng snapshot.”

## Slide 5 — Kết quả benchmark live

| Nhánh | Đạt oracle | Request đến thành công | Tổng request tấn công |
|---|---:|---|---:|
| Wordlist | 3/3 | 5, 5, 5 | 15 |
| AI tĩnh | 0/3 | Chưa đạt | 21 |
| AI feedback | 0/3 | Chưa đạt, model dừng | 3 |

Tổng 75 request benchmark tới SUT: 39 tấn công + 36 phụ. API AI: 7 call, 2.775 token được báo. Request chờ server sẵn sàng của launcher nằm ngoài tổng benchmark.

Lời trình bày: “Trong phép thử này LLM chưa tốt hơn wordlist. AI tĩnh hết ứng viên; AI feedback dừng sau khi WAF chặn. Em giữ cả kết quả không thành công.”

## Slide 6 — Demo có thể tái lập

```powershell
python -X utf8 -m ai.A3b_video_cache.artifacts --source ai/A3b_video_cache/cache/triage_live_2026-10-20_run1.json --replay
python -X utf8 -m ai.A3b_video_cache.artifacts --source ai/A3b_video_cache/cache/fuzzer_live_2026-10-20_v1.json --replay
```

- Gắn nhãn **PHÁT LẠI KẾT QUẢ ĐÃ LƯU** khi trình chiếu.
- Kiểm tra hash; thiếu cache không tạo phiên thành công.
- Quay input, lệnh chạy, output ID và checkpoint; không quay `.env`.

## Slide 7 — Giới hạn và bàn giao

- Dataset nhỏ, model/prompt cụ thể, temperature 0; chưa đánh giá XSS.
- Oracle cần nhóm rà soát; chưa có nhãn N3/thời gian người review.
- 43 test kiểm tra phần mềm; chất lượng model cần nhãn riêng.
- Đã có code, inference, benchmark, cache và báo cáo; còn review, clip L3 và mẫu slide chung.

Lời trình bày: “Pipeline đã chạy được và log kiểm tra lại được. Chưa đủ dữ liệu để kết luận độ chính xác hoặc tiết kiệm thời gian cho người kiểm thử.”
