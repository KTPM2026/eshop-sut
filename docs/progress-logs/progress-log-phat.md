# Nhật ký tiến độ — Nguyễn Đức Phát (23120317)

Phạm vi: P1 (2 Lab), P2 (gán nhãn alert), P3 (pilot + đóng gói + video), P4 (báo cáo + script phần Lab).
Nhánh: `phat/labs-workspace`, `phat/search-raw-lab3-cleanup` (eshop-sut, đã merge), `phat/lab-doc-fixes` (seminar, đã merge).

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

## 27–29/10/2026 — Chốt phạm vi, dọn tài liệu, script & hoàn tất

**P1 — Rà soát phạm vi & gỡ Lab 3 (ngoài phạm vi)**
- Rà cả 3 bản đề cương: xác nhận mục 6 chỉ quy định **2 Lab bắt buộc** (Lab 1 XSS, Lab 2 SQLi); phân công ghi rõ "2 bài Lab".
- Phát hiện Lab 3 (brute-force OTP, A07) được thêm trước đó **ngoài phạm vi** và viện dẫn "mục 1.4 đề cương" thực tế không tồn tại (mục 1.4 là "Thứ tự triển khai") → **quyết định gỡ Lab 3**.
- Gỡ toàn bộ section Lab 3 trong `seminar/docs/lab-huong-dan.md`; bảng so sánh độ khó và phần "Bàn giao" trả về đúng 2 Lab.

**P1/P4 — Đổi tên file request & dọn hình thức**
- Đổi `search.req` → **`search.raw`** (rename file thật ở gốc + cập nhật tham chiếu ở 10 tài liệu: lab-huong-dan, bao-cao-lab, report-outline, slide-outline, README, noi-dung-thuyet-trinh-phat, P3a-pilot-checklist, alert-labeling-template, lab-verify-notes, và bản MSSV).
- Lược bớt emoji trang trí trong `lab-huong-dan.md` và `bao-cao-lab.md` cho gọn, hợp tài liệu học thuật.

**P2 — Rà soát số liệu & chốt Ground Truth**
- Kiểm chứng 3 bộ nhãn khớp file nguồn: Phát **17 mục (10 Thật / 4 Giả / 3 Informational)**; Như **29 instance (14 True / 10 False / 5 Unknown, AI-assisted)**; tập đối chiếu A1 **11 instance (7 True / 1 False / 3 Unknown)**. Ba bộ khác đơn vị đếm → chỉ so sau khi ánh xạ theo ID.
- Hoàn tất timing gán nhãn tay **~30 phút**.
- Alert #16 (A07): đổi nguồn ghi "Code review + Lab 3" → "Code review" (do gỡ Lab 3); **nhãn/ưu tiên giữ nguyên, không sửa Ground Truth**.
- Đối chiếu & thống nhất nhãn với Thạch Như (N2) → **chốt Ground Truth**.

**P4 — Script thuyết trình (khớp deck thật)**
- Đọc deck `Seminar_Security_Testing_EShop.pptx.pdf` (49 trang); xác định vị trí phần của mình: **Lab 1 XSS = trang 42**, **Lab 2 SQLi = trang 43**, **gán nhãn P2 = trang 33** (nằm trong khối AI Triage).
- Viết script nói phần Lab (2 Lab, từ ngữ đơn giản, đánh dấu số trang, kèm phần trả lời câu hỏi) → `Phat/P4_slide_baocao/script-thuyet-trinh-phat.md`.
- Viết script slide ZAP "nguyên lý & chức năng" (trang 10) → `docs/slide-seminar/script-zap-trang10.md`.

**P3 — Video demo & đóng gói**
- Hoàn thành **2 clip demo**: Lab 1 (XSS) và Lab 2 (SQLi).
- P3b: đóng gói bản cuối phần Lab (hướng dẫn + payload + script reset + báo cáo + video).

**Kiểm chứng lại**
- Chạy lại `sqlmap -r search.raw --batch --tables` → xác nhận DBMS SQLite, **7 bảng** (gồm `users`). Lưu ý dùng `--flush-session` khi quay demo để kết quả "tươi", không lấy cache cũ.

**Git**
- Commit dọn tài liệu: eshop-sut `3941cd0` (nhánh `phat/search-raw-lab3-cleanup`), seminar `d6384b5` (nhánh `phat/lab-doc-fixes`). Xử lý lỗi fetch TLS (schannel) bằng fetch "blobless".
- **PR đã gộp vào `main`** cả hai repo (xác nhận trên eshop-sut: `search.raw` ở gốc main, P2 #16 nguồn = "Code review").
- Ghi nhật ký này lên `docs/progress-logs/progress-log-phat.md`.

---

## Việc còn lại — ĐÃ HOÀN TẤT (cập nhật 29/10/2026)
- [x] Quay 2 clip demo (Lab 1, Lab 2).
- [x] P2: điền timing (~30 phút) + đối chiếu & chốt nhãn chuẩn với Như.
- [x] Nội dung + script thuyết trình phần Lab (deck nhóm trang 42–43; script đơn giản hóa).
- [x] Mở & gộp PR dọn tài liệu (`phat/search-raw-lab3-cleanup`, `phat/lab-doc-fixes`) vào `main`.
- [x] P3b: đóng gói bản cuối phần Lab.
- [x] Nhật ký tiến độ đã nằm trong `docs/progress-logs/` của repo nhóm.

> **Trạng thái:** các gói việc P1–P4 của Phát đã hoàn tất.
