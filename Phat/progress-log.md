# Nhật ký tiến độ — Nguyễn Đức Phát (23120317)

Phạm vi: P1 (2 Lab), P2 (gán nhãn alert), P3 (pilot + đóng gói), P4 (báo cáo phần Lab).
Nhánh: `phat/labs-workspace` (eshop-sut), `phat/lab-doc-fixes` (seminar).

---

## 17/10/2026

**P1 — Hoàn thiện & chạy thử 2 Lab**
- Xác minh từ source: endpoint `GET /api/products?search=`, DB SQLite, bảng `users`, sink XSS `Home.jsx:64`.
- Tạo `xss-payloads.txt` (có nhóm payload an toàn SQL), `reset-db.ps1/.sh`, `lab-verify-notes.md`.
- Cài môi trường: `npm install` backend + frontend; chạy backend (3000) + frontend (5173, `--host`).
- **Lab 1 (XSS):** chạy ZAP Fuzzer; xác thực thực thi trên trình duyệt bằng `<img src=x onerror=alert(document.domain)>` → alert `localhost`. Minh chứng: `P1_labs/evidence/lab1-xss-alert.jpg`, `lab1-zap-fuzzer.jpg`.
- **Lab 2 (SQLi):** cài sqlmap 1.10.10; xác nhận `search` injectable (UNION, 6 cột, SQLite); dump bảng `users` (mật khẩu plaintext). Minh chứng: `P1_labs/evidence/sqlmap_users_dump.csv`, `lab2-sqlmap-results.md`.
- Sửa `seminar/docs/lab-huong-dan.md` khớp thực tế (endpoint, lệnh sqlmap SQLite, luồng XSS).

**P2 — Gán nhãn alert độc lập**
- Trích 15 alert thật từ `alert/2026-10-14-ZAP-Report-.json` → `alert-evidence-pack.md`.
- Chốt nhãn: 8 Thật, 4 Giả/FP (ngoài phạm vi + Path Traversal FP + Timestamp FP), 3 Informational; điền ưu tiên P1–P4.
- *Còn làm:* điền giờ gán nhãn; đối chiếu & chốt nhãn chuẩn với Thạch Như (N2).

**P3a — Pilot**
- Ghi lại môi trường, lỗi phát hiện (ChromeDriver/Chrome 155, Vite IPv6, npm install, các bẫy XSS, sqlmap SQLite), kết luận thời lượng cho GVTH #4 → `P3_pilot_donggoi/P3a-pilot-checklist.md`.

**P4 — Báo cáo phần Lab**
- Viết `P4_slide_baocao/bao-cao-lab.md` (có nhúng ảnh minh chứng). Slide làm riêng.

**Commit chính:** `1788bd6` (khởi tạo workspace) · `cca434e` (P2) · `c61b08a` (Lab 2 evidence) · `43c88c0` (Lab 1 evidence + P3a) · `70341fd` (báo cáo P4). Repo seminar: `b7b3dd1`, `9f858e4` (sửa lab doc).

---

## Việc còn lại (cập nhật khi xong)
- [ ] Quay 2 clip demo (Lab 1, Lab 2).
- [ ] P2: điền timing + chốt nhãn chuẩn với Như.
- [ ] Làm slide phần Lab.
- [ ] P3b: đóng gói bản cuối (chờ video + benchmark N3/A2 của nhóm).
- [ ] Gộp nhật ký này vào `progress-log.md` chung của nhóm (nếu nhóm dùng file chung).
