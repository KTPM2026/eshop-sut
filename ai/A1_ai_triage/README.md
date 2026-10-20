# A1: AI Vulnerability Triage

> 20/10/2026: đã chạy live trên bộ 11 alert khóa hash. CLI có checkpoint/resume: `python -X utf8 -m ai.A1_ai_triage.live --output ai/outputs/new-live.json`; thêm `--resume` để chỉ gọi ID còn thiếu, `--max-calls 1` để smoke test, `--interval 15` để chỉnh khoảng nghỉ. Mặc định đọc `ai/.env`; dùng `--env-file` để chọn tệp khác. Output mới không ghi đè lượt cũ. Kết quả và giới hạn nằm ở [báo cáo live](../A4_slide_baocao/bao-cao-live-2026-10-20.md). `run.py` bên dưới là CLI batch cũ, không có checkpoint.

**Block một phần:** đã nhận report ZAP thật, nhưng chưa inference live và chưa có ground truth. [sample_alert_data.json](sample_alert_data.json) vẫn chỉ chứa ba alert **MẪU TỰ TẠO**.

## Luồng xử lý

`JSON đầu vào -> parser/chuẩn hóa -> A3a.classify_alert -> kiểm tra schema/ID -> JSON gợi ý -> người review`

Không lọc bỏ alert theo `is_real` hoặc priority. Bất kỳ lỗi parse/model nào làm lượt chạy báo lỗi thay vì giả lập kết quả còn thiếu. Output chỉ được ghi sau khi tất cả record đã xử lý thành công; kết quả file cũ không được coi là lượt chạy mới nếu CLI lỗi.

## Dạng JSON nhận được

- Danh sách alert chuẩn hóa, hoặc object `{"alerts": [...]}`.
- Native ZAP report `{"site": [{"alerts": [{... , "instances": [...]}]}]}`.
- Flat alert cần `name` (hoặc `alert`), `url`, `risk`; `param/evidence` thiếu dùng chuỗi rỗng, `cweid` chưa biết dùng null. Schema chuẩn hóa còn có `alert_id`.
- Native ZAP dùng `riskcode` 3/2/1/0, hoặc `risk`/`riskdesc`; URL lấy từ `instance.uri/url`; tên/CWE lấy từ alert cha. Risk không nhận ra giữ `Unknown`, không suy ra là an toàn.

**TỰ ĐỀ XUẤT - CẦN NHÓM CHỐT:** một instance là một record. Giữ ID tường minh khi có một instance; nếu thiếu ID hoặc có nhiều instance, sinh `zap-<hash>` từ nội dung chuẩn hóa đã làm sạch. Số record không nhất thiết bằng số alert type mà ZAP hiển thị. Bản ghi trùng ID bị từ chối để nhóm quyết định deduplicate, không tự bỏ record. Đổi evidence/URL hoặc quy tắc làm sạch có thể đổi hash: phải khóa input/ID trước N2/P2/N3.

H1 cần giao JSON gốc đã làm sạch secret, commit SUT, phiên bản ZAP, scope xác thực và số alert thực tế. Không ép thành 40–80 alert. H1/N3 phải đối chiếu mapping trên file thật trước khi đo.

## Chạy CLI

Từ thư mục gốc repo:

```powershell
python -m ai.A1_ai_triage.run --mode mock --output ai/outputs/triage_sample_mock.json
```

Chỉ sau khi nhóm duyệt cấu hình A3a, làm sạch dữ liệu và cấp key qua môi trường mới chạy API thật:

```powershell
python -m ai.A1_ai_triage.run --mode live --input <duong-dan-json-H1> --output ai/outputs/triage_live.json
```

Thay placeholder bằng đường dẫn H1 thực tế; không dùng nguyên lệnh placeholder. Các biến và điều kiện live xem [A3a](../A3a_ai_config/README.md). Lệnh không tự tạo nhãn hoặc benchmark N3.

Report thật hiện có tại `alert/2026-10-14-ZAP-Report-.json`. Chỉ xử lý
backend EShop bằng origin đầy đủ:

```powershell
python -m ai.A1_ai_triage.run --mode mock `
  --origin http://localhost:3000 `
  --input alert/2026-10-14-ZAP-Report-.json `
  --output ai/outputs/triage_real_backend_mock.json
```

Lượt này chuẩn hóa 11 instance thật nhưng vẫn là **mock**, không phải
inference hay benchmark. Biểu mẫu review độc lập nằm tại
`ai/A1_ai_triage/ground_truth_template.json`.

## Đầu ra

Mỗi phần tử `results` có đúng sáu trường theo [schema](../A3a_ai_config/contracts.json):

```json
{
  "alert_id": "sample-sqli-001",
  "is_real": null,
  "priority": "P3",
  "reason": "MÔ PHỎNG: chưa gọi model, chưa xác minh; P3 chỉ để kiểm tra schema.",
  "confidence": 0.0,
  "trang_thai_bang_chung": "can_xac_minh"
}
```

Ví dụ trên là **mock**, không phải model inference hay đánh giá SQLi. Wrapper `_meta` ghi mode, nguồn dữ liệu, hash input, thời điểm UTC, số record, cấu hình không chứa key, `review_required: true`, `final_decision: pending_human_review`, `is_benchmark_result: false`. `is_replay: false` chỉ cho biết file vừa được tạo, **không đồng nghĩa gọi model thật**; phải đọc cả `execution_mode` và `model_inference_performed`.

Nguồn input ngoài chưa được xác minh ghi `unverified_external`; adapter không tự tuyên bố đó là scan thật. Lượt chạy live trên sample vẫn là dữ liệu synthetic. Khi phát lại file, người trình bày phải gắn nhãn replay theo [A3b](../A3b_video_cache/README.md).

Như làm N3 trên output A1 và nhãn độc lập đã chốt với Phát. Lân không tạo nhãn chuẩn, không cho dữ liệu mock tham gia tính Precision/Recall, không tự kết luận đạt mục tiêu proposal.
