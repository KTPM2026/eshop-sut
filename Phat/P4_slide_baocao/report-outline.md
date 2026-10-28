# P4 — Outline báo cáo phần Lab (Phát 23120317)

> TỰ ĐỀ XUẤT - CẦN NHÓM CHỐT. Outline, **không phải báo cáo đã có kết quả**. `[CHỜ PILOT]` = số liệu thật từ P3a.

## 1. Phạm vi & trách nhiệm
Phát phụ trách hoàn thiện/chạy thử 2 Lab và đóng gói (P1–P4). Không viết lại lý thuyết Security Testing/SDLC (đã có trong `docs/`).

## 2. Môi trường tái lập
| Thông tin | Giá trị |
|---|---|
| Commit EShop, cổng 3000/5173, seed/reset | [CHỜ PILOT] |
| Phiên bản ZAP / sqlmap | [CHỜ PILOT] |
| Endpoint, DB, bảng (đã xác minh) | `GET /api/products?search=`; DB `main`; bảng `users` |

## 3. Lab 1 — Reflected XSS (ZAP)
- Thiết kế, các bước, checkpoint.
- Phân tích sink: `Home.jsx:64` `dangerouslySetInnerHTML`; phân biệt reflection JSON API vs thực thi trình duyệt.
- Kết quả thật: [CHỜ PILOT] ảnh/log + payload phát hiện.
- Khắc phục: Output Encoding, render `{value}` của React, tránh `dangerouslySetInnerHTML`, CSP. CWE-79/116.

## 4. Lab 2 — SQL Injection (sqlmap)
- Root cause: `server.js:144` nối chuỗi.
- Quy trình: `-r` → injectable → `--tables` → `-T users --dump` → reset.
- Kết quả thật: [CHỜ PILOT] kỹ thuật phát hiện (boolean/time/UNION?), bảng dump.
- Khắc phục: Parameterized Query/Prepared Statement, ORM, input validation, least privilege. CWE-89.

## 5. Kết quả pilot & giới hạn
- Timing thật từng Lab vs dự kiến; lỗi hướng dẫn đã sửa. [CHỜ PILOT]
- Giới hạn: môi trường localhost, lỗ hổng cài sẵn để học; token trong `search.raw` có thể hết hạn cần cấp lại.
- Không khẳng định kết quả khi chưa chạy.

## 6. Liên kết minh chứng
Link clip Lab, ảnh/log, `P1_labs/`, commit cá nhân, `progress-log.md`. [CHỜ PILOT]
