# A2: Khung benchmark Fuzzer

> 20/10/2026: đã có nhánh live: `python -X utf8 -m ai.A2_fuzzer_benchmark.isolated_lab --mode live --output ai/outputs/new-live-benchmark.json`. Launcher dùng lab/database tạm; 3 lượt/nhánh, budget 50, tối đa 10 feedback API call/lượt. AI tĩnh sinh đúng 7 ứng viên bằng một call, dùng chung ba lượt, có provenance. Kết quả thật: wordlist 3/3, AI tĩnh 0/3 (hết nguồn), feedback 0/3 (model dừng); không fallback heuristic. [Log](results/live_2026-10-20_v1.json), [báo cáo](../A4_slide_baocao/bao-cao-live-2026-10-20.md). Đường offline vẫn dùng lệnh cũ; scaffold `runner.py` không phải runner thực nghiệm.

> Cập nhật 18/10: entrypoint chính là `python -X utf8 -m ai.A2_fuzzer_benchmark.isolated_lab --output ai/outputs/offline-new-run.json`. Xem [README hiện tại](../README.md) và [kết quả offline v1](results/offline_v1.json). Có budget chung, checkpoint SQLite từng attempt và ba nhánh ghi đúng nguồn offline. `runner.py` dưới đây chỉ giữ scaffold/template cũ để tương thích. Script/kết quả demo được giữ làm lịch sử.

Runner trong thư mục này vẫn là giao diện an toàn và bị block nếu thiếu phụ
thuộc. H3/L2 hiện dùng implementation trong `backend/` và
`demo/ai_fuzzer/`; không dùng runner mock này để tạo số liệu.

## Giao diện đang chờ

```python
from ai.A2_fuzzer_benchmark.runner import run_branch

# TỰ ĐỀ XUẤT - CẦN NHÓM CHỐT: tên nhánh và budget.
run_branch("wordlist_static", payload_source=[],
           filter_endpoint="http://localhost:3000/CHUA_CHOT", budget=50)
```

Ví dụ trên **luôn ném `DependencyBlockedError`**, không gửi HTTP và không đọc payload source. Đây là chữ ký khung, không phải lệnh chạy benchmark được. Hai tên nhánh còn lại: `ai_static`, `ai_feedback`.

Trước khi nối code cần Hùng/Long bàn giao endpoint/method/auth của bản lab, reset/seed, phiên bản rule, payload source, feedback từng request và stop condition. Như/Phát rà soát checkpoint SQLi/XSS. `filter_endpoint` không được dùng để nhắm hệ thống ngoài lab được phép.

## Log template rỗng

```powershell
python -m ai.A2_fuzzer_benchmark.runner --write-template ai/outputs/a2-template
```

CSV chỉ có header `branch,attempt_no,payload,response_code,bypass,note`. JSON có cùng danh sách cột, `rows: []`, `request_count: 0`, `status: blocked`, `is_benchmark_result: false`. Chạy lại sẽ từ chối ghi đè file đang có. Không tính tỷ lệ từ template rỗng.

**TỰ ĐỀ XUẤT - CẦN NHÓM CHỐT:** log hoàn thiện dùng `attempt_no` bắt đầu từ 1, response code là HTTP status, `bypass` là boolean khi đã xác minh được. Trường hợp timeout/chưa đủ bằng chứng cần chốt cách biểu diễn trước khi chạy, không ép thành kết luận thật/giả. Metadata run ID, model, rule hash, seed và budget nên đặt ở wrapper JSON hoặc manifest riêng để giữ đúng sáu cột.

## Thiết kế đối chứng chờ thực hiện

- Ba nhánh dùng cùng SUT commit, endpoint, bộ lọc/rule, seed/reset và tối đa N request SUT.
- N=50 là **tự đề xuất theo proposal, chưa chốt**. Tối thiểu ba lượt/nhánh theo đề cương; ghi cấu hình, input, thời gian, tổng request, chi phí/lượt gọi AI riêng.
- Bypass tạm đề xuất = không bị chặn (status khác 403/400) **và** checkpoint xác nhận hiệu ứng mong đợi ở backend. HTTP 200 hay vượt lọc đơn thuần không đủ.
- Nhóm cần chốt oracle theo SQLi/XSS; XSS phải xác minh execution phù hợp luồng thực tế, không chỉ tìm chuỗi phản xạ. Timeout, 500 và redirect không mặc định thành công.
- Khi đủ dữ liệu mới báo tỷ lệ bypass và request đến lần đầu theo từng lượt; trường hợp không thành công ghi chưa đạt trong budget, không tự gán bằng 50.

Benchmark thực tế chạy bằng:

```powershell
python -X utf8 demo/ai_fuzzer/benchmark_fuzzer.py
```

Kết quả nằm tại `demo/ai_fuzzer/benchmark_results.json`, gồm 3 lượt/nhánh,
log từng request và baseline rỗng trước khi chấp nhận backend trả dữ liệu.
Đây là kết quả local lab/offline heuristic của L2, chưa phải benchmark API
live theo adapter A3a.
