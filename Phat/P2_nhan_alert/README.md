# P2 — Gán nhãn alert độc lập (lần 2)

**Phát (23120317).** 3 điểm. Đầu vào: alert thật từ H1 (`../../alert/2026-10-14-ZAP-Report-.json`).

- `alert-labeling-template.md` — khung bảng, **15 loại alert thật đã liệt kê sẵn** (tên/risk/CWE/instance lấy từ scan). Cột nhãn/ưu tiên/lý do/bằng chứng để trống.
- `alert-evidence-pack.md` — **bộ dữ kiện đã trích sẵn** (evidence/URI/param/bối cảnh) + câu hỏi quyết định cho từng alert, giúp gán nhãn nhanh. AI không điền nhãn.

## Ranh giới AI / Phát
AI **chỉ** dựng khung và điền dữ kiện khách quan từ file scan. AI **không** gán nhãn thật/giả, không đặt ưu tiên, không viết lý do — vì quy chế yêu cầu đây là nhãn **độc lập của con người** để tạo Ground Truth đối chứng. Nếu AI điền hộ, nhãn mất tính độc lập và không dùng benchmark được.

## Quy trình
1. Chạy/đọc request-response thật của từng alert (có thể mở lại trong ZAP hoặc đọc trường `evidence`/`attack`/`otherinfo` trong JSON).
2. Điền nhãn + ưu tiên + lý do + bằng chứng. Ghi timing.
3. Khóa nhãn → đối chiếu Như → chốt nhãn chuẩn (bảng cuối file template).
