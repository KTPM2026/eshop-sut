# P2 — Bảng gán nhãn alert ĐỘC LẬP (lần 2) — Nguyễn Đức Phát 23120317

> ⚠️ **QUY CHẾ ĐỐI CHỨNG — ĐỌC TRƯỚC KHI ĐIỀN:**
> - Gán nhãn **độc lập**, **CHƯA** xem nhãn của Thạch Như (N2) và **CHƯA** xem kết quả AI Triage.
> - Ghi **thời gian bắt đầu/kết thúc** để đo timing có review của người.
> - Mỗi alert tự kiểm chứng bằng request/response thật, không kết luận chỉ từ tên alert hay status 200.
> - Nhãn `Thật / Giả / Chưa đủ bằng chứng` — **không ép** "Chưa đủ bằng chứng" thành "Giả" để làm đẹp số.
> - **AI chỉ dựng khung bảng này và điền các cột dữ kiện (tên alert, risk, CWE, số instance) lấy từ scan thật. Toàn bộ cột nhãn/ưu tiên/lý do/bằng chứng do Phát tự điền.**

- **Nguồn alert:** `eshop-sut/alert/2026-10-14-ZAP-Report-.json` (ZAP 2.17.0, scan 14/10/2026, site `localhost:3000` + `localhost:5173`).
- **Thời gian gán nhãn:** bắt đầu `__:__` — kết thúc `__:__` — tổng `__ phút`.
- Ma trận ưu tiên (theo đề cương mục 5.1): P1 dễ khai thác+impact cao · P2 dễ+thấp · P3 khó+cao · P4 khó+thấp/nghi FP.

| # | Alert (từ scan) | Risk (ZAP) | CWE | #Instance | Nhãn: Thật/Giả/Chưa đủ | Ưu tiên P1–P4 | Lý do (tự viết) | Bằng chứng đã kiểm (URI/param/response) |
|---|---|---|---|:---:|---|---|---|---|
| 1 | Strict-Transport-Security Header Not Set | Low (High) | 319 | 1 |  |  |  |  |
| 2 | Re-examine Cache-control Directives | Info (Low) | 525 | 1 |  |  |  |  |
| 3 | **SQL Injection** | High (Low) | 89 | 1 |  |  |  |  |
| 4 | Cross-Domain Misconfiguration | Medium (Medium) | 264 | 3 |  |  |  |  |
| 5 | Server Leaks Info via "X-Powered-By" | Low (Medium) | 497 | 3 |  |  |  |  |
| 6 | X-Content-Type-Options Header Missing | Low (Medium) | 693 | 3 |  |  |  |  |
| 7 | Authentication Request Identified | Info (High) | — | 1 |  |  |  |  |
| 8 | **Path Traversal** | High (Low) | 22 | 1 |  |  |  |  |
| 9 | Content Security Policy (CSP) Header Not Set | Medium (High) | 693 | 2 |  |  |  |  |
| 10 | Missing Anti-clickjacking Header | Medium (Medium) | 1021 | 2 |  |  |  |  |
| 11 | Timestamp Disclosure - Unix | Low (Low) | 497 | 1 |  |  |  |  |
| 12 | X-Content-Type-Options Header Missing (site 2) | Low (Medium) | 693 | 3 |  |  |  |  |
| 13 | Information Disclosure - Sensitive Info in URL | Info (Medium) | 598 | 1 |  |  |  |  |
| 14 | Information Disclosure - Suspicious Comments | Info (Medium) | 615 | 6 |  |  |  |  |
| 15 | Modern Web Application | Info (Medium) | — | 2 |  |  |  |  |

**Tổng:** 15 loại alert / 31 instance.

## Ghi chú cá nhân khi kiểm chứng (tùy ý)
- Alert #3 (SQL Injection) và #8 (Path Traversal) là High → ưu tiên kiểm chứng kỹ bằng request thật trước.
- Nhiều alert còn lại là thiếu security header (passive) → cân nhắc impact thực tế trên SUT localhost.

## Sau khi khóa nhãn
- [ ] Khóa nhãn (không sửa nữa) trước khi xem N2/AI.
- [ ] Đối chiếu với Như (N2): liệt kê các điểm bất đồng.
- [ ] Cùng Như chốt **nhãn chuẩn (Ground Truth)**. Người viết module AI (Lân) không tham gia chốt nhãn.

| Alert # | Nhãn Phát | Nhãn Như | Bất đồng? | Nhãn chuẩn chốt | Ghi chú |
|---|---|---|---|---|---|
|  |  |  |  |  |  |
