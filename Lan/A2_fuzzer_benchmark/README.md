# A2: Khung benchmark Fuzzer

**BLOCK HOÀN TOÀN đối với benchmark thật.** Chưa có H3/L2 trong repo để tích hợp. Không dựng bộ lọc H3 hoặc viết thay vòng lặp L2 của Long.

## Giao diện đang chờ

```python
from Lan.A2_fuzzer_benchmark.runner import run_branch

# TỰ ĐỀ XUẤT - CẦN NHÓM CHỐT: tên nhánh và budget.
run_branch("wordlist_static", payload_source=[],
           filter_endpoint="http://localhost:3000/CHUA_CHOT", budget=50)
```

Ví dụ trên **luôn ném `DependencyBlockedError`**, không gửi HTTP và không đọc payload source. Đây là chữ ký khung, không phải lệnh chạy benchmark được. Hai tên nhánh còn lại: `ai_static`, `ai_feedback`.

Trước khi nối code cần Hùng/Long bàn giao endpoint/method/auth của bản lab, reset/seed, phiên bản rule, payload source, feedback từng request và stop condition. Như/Phát rà soát checkpoint SQLi/XSS. `filter_endpoint` không được dùng để nhắm hệ thống ngoài lab được phép.

## Log template rỗng

```powershell
python -m Lan.A2_fuzzer_benchmark.runner --write-template Lan/outputs/a2-template
```

CSV chỉ có header `branch,attempt_no,payload,response_code,bypass,note`. JSON có cùng danh sách cột, `rows: []`, `request_count: 0`, `status: blocked`, `is_benchmark_result: false`. Chạy lại sẽ từ chối ghi đè file đang có. Không tính tỷ lệ từ template rỗng.

**TỰ ĐỀ XUẤT - CẦN NHÓM CHỐT:** log hoàn thiện dùng `attempt_no` bắt đầu từ 1, response code là HTTP status, `bypass` là boolean khi đã xác minh được. Trường hợp timeout/chưa đủ bằng chứng cần chốt cách biểu diễn trước khi chạy, không ép thành kết luận thật/giả. Metadata run ID, model, rule hash, seed và budget nên đặt ở wrapper JSON hoặc manifest riêng để giữ đúng sáu cột.

## Thiết kế đối chứng chờ thực hiện

- Ba nhánh dùng cùng SUT commit, endpoint, bộ lọc/rule, seed/reset và tối đa N request SUT.
- N=50 là **tự đề xuất theo proposal, chưa chốt**. Tối thiểu ba lượt/nhánh theo đề cương; ghi cấu hình, input, thời gian, tổng request, chi phí/lượt gọi AI riêng.
- Bypass tạm đề xuất = không bị chặn (status khác 403/400) **và** checkpoint xác nhận hiệu ứng mong đợi ở backend. HTTP 200 hay vượt lọc đơn thuần không đủ.
- Nhóm cần chốt oracle theo SQLi/XSS; XSS phải xác minh execution phù hợp luồng thực tế, không chỉ tìm chuỗi phản xạ. Timeout, 500 và redirect không mặc định thành công.
- Khi đủ dữ liệu mới báo tỷ lệ bypass và request đến lần đầu theo từng lượt; trường hợp không thành công ghi chưa đạt trong budget, không tự gán bằng 50.

Hiện không có request đã gửi, không có lượt benchmark hoặc số liệu bypass. A3a chỉ là giao diện gọi AI, không làm A2 hết block.
