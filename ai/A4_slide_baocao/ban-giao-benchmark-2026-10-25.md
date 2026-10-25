# Bàn giao A2 live — lần người dùng tự chạy ngày 25/10/2026

Đã kiểm tra [log tự chạy](../A2_fuzzer_benchmark/results/live_manual_check_02.json): `status=completed`, đủ 9 lượt; snapshot nhất quán và source hash trước/sau khớp. Kết quả tái hiện tuyên bố của Long: **LLM feedback 3/3, 4 request tấn công/lượt**. Dùng lần này làm nguồn cho slide bàn giao hiện tại.

| Chiến lược | Thành công cũ 20/10 | Thành công mới | Request tấn công/lượt mới | Tổng tấn công mới | Tổng SUT mới |
|---|---|---|---|---|---|
| Wordlist | 3/3 | 3/3 | 5, 5, 5 | 15 | 27 |
| LLM static | 0/3 | 0/3 | 7, 7, 7; chưa đạt | 21 | 33 |
| LLM feedback | 0/3 | 3/3 | 4, 4, 4 | 12 | 24 |

Tổng **48 tấn công + 36 phụ = 84 request SUT**; 13 API call đều thành công, 7.906 token được báo. Request launcher chờ server sẵn sàng nằm ngoài tổng. Không suy ra chi phí tiền từ token.

Ở cả ba lượt feedback, chuỗi HTTP là **200 → 403 → 200 → 200**; chỉ request thứ tư đạt checkpoint SQLi. Hai response 200 trước đó không được tính thành công. Model nhận lịch sử, gồm từ khóa bị chặn và checkpoint, để đề xuất tiếp. Log này có quá trình thử tiếp sau phản hồi, nhưng chưa tách được đóng góp riêng của prompt, chuẩn hóa payload và feedback qua thực nghiệm ablation.

So với Wordlist, feedback dùng **4 thay vì 5 request tấn công/lượt** (ít hơn 20%) trong lần này. Chưa kết luận nhanh hơn về thời gian hoặc rẻ hơn vì có thêm API call và thời gian chờ. Cùng lab nhỏ, model/prompt cụ thể và temperature 0; oracle vẫn cần nhóm review, chưa đánh giá XSS.

[Lần chạy độc lập trước](bao-cao-live-2026-10-25.md) đạt feedback 3/3 với 1 request/lượt. Giữ nguyên log, summary và biểu đồ lần đó để ghi nhận biến thiên giữa các lần chạy; không khẳng định mọi lần sẽ ra 4 request. Bản sửa lỗi lưu file chỉ thêm thử lại khi Windows khóa file, không đổi payload, oracle hay tiêu chí pass. 46/46 test đã pass sau bản sửa này.

Kiểm tra độc lập đã thực hiện trên log tự chạy:

- Đủ run 1, 2, 3 cho mỗi chiến lược; số attack bằng số attempts, tổng SUT bằng attack + phụ.
- Tính lại oracle cho từng payload thành công từ snapshot và ID quan sát lưu trong log: đều đạt.
- Source hash trong log khớp file code hiện tại; không có API call lỗi; không chứa giá trị key trong `ai/.env`.
- Log/cache 20/10 và các lần xác minh trước được giữ nguyên. `live_manual_check_01.json` và `.tmp` là lần gián đoạn, không dùng làm kết quả đủ ba lượt.

## File dùng bàn giao

- [Slide live hiện tại, đặc biệt Slide 5](slide-live-2026-10-20.md).
- [Biểu đồ từ log tự chạy](benchmark-manual-2026-10-25.png).
- [Summary từ log tự chạy](live-summary-manual-2026-10-25.json); dữ liệu triage vẫn là ngày 20/10.
- [Log đầy đủ](../A2_fuzzer_benchmark/results/live_manual_check_02.json).
- `ai/A1_ai_triage/live.py` và `ai/tests/test_live.py`: bản sửa/test xử lý khóa file Windows.

Các file mới và thay đổi vẫn nằm local trên `update/benchmark-results`, chưa commit/push. Có thể gửi log và tài liệu này trực tiếp; để đồng đội lấy qua Git cần commit các file cần bàn giao rồi push nhánh khi người dùng cho phép. Không gửi `.env`, key hay lấy file `.tmp` làm kết quả hoàn tất. Nếu slide thật ở PowerPoint/Canva ngoài repo, cần ghép lại biểu đồ và số liệu **84 request SUT** từ nội dung Markdown này.
