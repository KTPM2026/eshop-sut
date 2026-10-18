# A3a: Cấu hình và giao diện AI chung

**Đã triển khai adapter, chưa chạy API thật.** Dùng cho A1 và để Long tích hợp L2; không chứa vòng lặp Fuzzer hay logic chấm benchmark.

## Cấu hình đề xuất

> TỰ ĐỀ XUẤT - CHƯA chốt với nhóm, cần Lân/nhóm xác nhận lại. Không khẳng định tài khoản của nhóm có quyền gọi model này.

| Biến môi trường | Mặc định | Ý nghĩa |
|---|---|---|
| `AI_PROVIDER` | `openai` | Adapter hiện chỉ hỗ trợ provider này |
| `AI_MODEL` | `gpt-4.1-mini-2025-04-14` | Cố định snapshot đề xuất, không dùng tên latest |
| `AI_BASE_URL` | `https://api.openai.com/v1` | Endpoint HTTPS được phép, không đặt key trong URL |
| `AI_TEMPERATURE` | `0` | Giảm ngẫu nhiên; không bảo đảm tái lập tuyệt đối |
| `AI_MAX_COMPLETION_TOKENS` | `1200` | Giới hạn đầu ra mỗi lần gọi |
| `AI_TIMEOUT_SECONDS` | `30` | Timeout SDK |
| `AI_GROUP_APPROVED` | `0` | Chỉ `1` mới cho phép khởi tạo live |
| `OPENAI_API_KEY` | Rỗng | Secret lấy từ môi trường, không ghi vào cấu hình/report |

SDK không tự retry (`max_retries=0`). Không có trần chi phí bằng tiền trong adapter; nhóm cần chốt trước khi live. N=50 trong A2 là request SUT, không phải giới hạn chi phí API AI.

[.env.example](.env.example) là danh mục biến, **không được tự động nạp**. Thiết lập biến trong process PowerShell hoặc trình quản lý secret nội bộ; không đưa key vào chat, ảnh quay màn hình, git hay lịch sử lệnh. Không bật `AI_GROUP_APPROVED=1` khi nhóm chưa xác nhận. Sau khi được duyệt và cung cấp key qua môi trường, A1 có thể dùng `--mode live` theo README A1. Lỗi key/model/mạng/refusal/JSON đều báo lỗi, không giả làm thành công bằng mock.

## Hợp đồng JSON v1 đề xuất

[contracts.json](contracts.json) sinh từ [contracts.py](contracts.py); Pydantic cấm trường ngoài schema và kiểm tra kiểu, enum, độ dài, giá trị. Sinh lại khi model dữ liệu thay đổi:

```powershell
python -m ai.A3a_ai_config.export_schema
```

| Hàm | Đầu vào bắt buộc | Đầu ra |
|---|---|---|
| `classify_alert(alert)` | `alert_id,name,risk,url,param,evidence,cweid` | `alert_id,is_real,priority,reason,confidence,trang_thai_bang_chung` |
| `suggest_payload(context)` | `target_url,vulnerability_type,previous_attempts,remaining_requests` | `payload,reason,should_stop` |

- Risk: `High/Medium/Low/Informational/Unknown`. `cweid` là string hoặc null. Input A1 parser chuyển số CWE thành string.
- `is_real`: true/false/null; null giữ lại trường hợp chưa kết luận. `priority`: P1/P2/P3/P4. Nhóm cần thống nhất rubric trước benchmark, không coi mock P3 là ưu tiên thật.
- `confidence`: 0–1, chỉ là nhận định của model, không phải xác suất đã hiệu chuẩn.
- `trang_thai_bang_chung`: `can_xac_minh`, `co_bang_chung_ho_tro`, `khong_du_bang_chung`; mọi giá trị vẫn cần người review.
- `vulnerability_type`: `SQLi/XSS`. `previous_attempts` tối đa 50 item, mỗi item có `payload,response_code,blocked,effect_observed`; effect có thể null. Đây chỉ là JSON đã kiểm tra, adapter không tự xác minh backend.
- `target_url` chỉ nhận HTTP(S) loopback và không có user/password. Docker hostname khác phải chốt allowlist và sửa validator có test trước khi dùng.
- Hết budget thì trả `should_stop: true` mà không gọi API. Có budget không có nghĩa adapter sẽ tự gửi request SUT.

## Ví dụ tích hợp cho Long

Chạy từ thư mục gốc repo, với dependencies trong `ai/requirements.txt`:

```python
from ai.A3a_ai_config import AIClient

context = {
    "target_url": "http://localhost:3000/api/products",
    "vulnerability_type": "SQLi",
    "previous_attempts": [],
    "remaining_requests": 50,
}
with AIClient(mode="mock") as client:
    suggestion = client.suggest_payload(context)
    assert suggestion["should_stop"] is True
    assert suggestion["payload"] == ""
```

URL trên là **ví dụ hợp đồng**, chưa xác nhận endpoint thật H3. Mock cố ý không tạo payload khai thác. Khi nhóm cho phép API thật, dùng cùng giao diện với `AIClient(mode="live")`. Long phải kiểm tra `should_stop`, validate/scope-check payload trước khi gửi, theo dõi budget và gọi checkpoint trong L2; adapter không thay các bước đó.

`classify_alert()` giữ nguyên ID; trả sai ID, JSON lỗi hoặc thêm hành động ngoài schema sẽ bị từ chối. AI chỉ gợi ý, không có chức năng đóng/xóa/bỏ alert.

## Giới hạn và an toàn dữ liệu

System prompt tách khỏi JSON user chứa evidence/HTTP không tin cậy. Kiểm tra schema không loại trừ được prompt injection hoặc kết luận sai về mặt chuyên môn. Người review quyết định cuối cùng.

Redaction tự động chỉ là **best effort** cho key/cookie/token và một số mẫu secret, không bảo đảm xóa mọi PII hoặc dữ liệu nghiệp vụ. Hùng/Lân phải kiểm tra và làm sạch dữ liệu trước khi dùng cloud API; không dựa hoàn toàn vào regex. `store=False` được truyền vào SDK, nhưng không được diễn giải thành cam kết không lưu dữ liệu ở mọi lớp hệ thống. Không in body lỗi provider ra CLI.

## Căn cứ kỹ thuật

Code đã đối chiếu chữ ký SDK cài tại máy `openai==2.30.0` (`chat.completions.parse`, Pydantic response model, `store`, `max_completion_tokens`) và kiểm tra adapter bằng HTTP giả. Tài liệu chính thức tham chiếu: [GPT-4.1 mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini) và [Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs). Việc chọn model/các giới hạn ở trên vẫn là đề xuất của workspace, không phải yêu cầu từ tài liệu hay quyết định của nhóm.
