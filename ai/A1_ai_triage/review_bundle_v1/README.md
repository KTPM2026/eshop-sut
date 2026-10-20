# Bộ review độc lập v1

Chuẩn bị ngày 18/10/2026 từ H1 thật: **11 instance**, origin `http://localhost:3000`. `alerts.json` đã qua redaction best-effort; ID giữ mapping parser. `manifest.json` ghi hash nguồn/input và hai bản review trống tại thời điểm bàn giao.

1. Như nhận riêng `review_nhu.json`, Phát nhận riêng `review_phat.json`; dùng input và bằng chứng H1/SUT, không xem nhãn của nhau hoặc output AI.
2. Tạo bản làm việc riêng, ghi thời điểm bắt đầu, nhãn, lý do, bằng chứng và thời gian review. Thiếu bằng chứng thì giữ null và ghi trạng thái chưa xác định, không ép thành false.
3. Review đủ ID thì ghi `locked_at_utc`, lưu bản mới và hash bản đã khóa. Hash sheet trong manifest chỉ xác nhận bản trống.
4. Tổng hợp bất đồng thành artifact riêng, giữ hai bản độc lập. Như/Phát thống nhất xử lý trước N3; không dùng kết quả AI làm nhãn chuẩn.

Không ghi đè v1. Tạo bundle khác khi thay dữ liệu/schema:

```powershell
python -X utf8 -m ai.A1_ai_triage.freeze_dataset --input alert/2026-10-14-ZAP-Report-.json --output ai/outputs/review-bundle-new --origin http://localhost:3000
```

Đây là bộ chuẩn bị bàn giao, chưa gửi ra ngoài và chưa có người gán nhãn.
