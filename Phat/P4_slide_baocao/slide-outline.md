# P4 — Outline slide phần Lab (Phát 23120317)

> TỰ ĐỀ XUẤT - CẦN NHÓM CHỐT bố cục chung. Đây là **outline**, chưa có số liệu thật. Mọi `[CHỜ PILOT]` điền sau khi chạy P3a.

Phần của Phát dự kiến **6–8 slide** trong bài chung (nền trắng, chữ đen, font to rõ).

1. **Mở đầu phần thực hành** — vị trí 2 Lab trong luồng DAST; độ khó tăng dần (Lab 1 GUI → Lab 2 CLI).
2. **Lab 1 — Reflected XSS bằng ZAP**
   - Luồng: Record → Fuzz → Checkpoint.
   - Endpoint thật `GET /api/products?search=`; sink frontend `Home.jsx` (`dangerouslySetInnerHTML`).
   - Ảnh: bảng Fuzzer + response payload chưa escape + alert box trên frontend. [CHỜ PILOT]
3. **Lab 1 — Phân biệt reflection API (JSON) vs thực thi trình duyệt** (điểm dễ nhầm).
4. **Lab 2 — SQL Injection bằng sqlmap**
   - Root cause: nối chuỗi `LIKE '%${search}%'` (`server.js:144`).
   - Lệnh: `-r search.raw --batch` → `--tables` → `-T users --dump`. SQLite dùng `--tables` trực tiếp.
   - Ảnh: sqlmap báo injectable + dump bảng `users`. [CHỜ PILOT]
5. **Khắc phục** — Output Encoding/CSP (XSS); Parameterized Query/ORM (SQLi).
6. **Kết quả pilot & thời lượng** — timing thật so dự kiến (10' / 15–20'). [CHỜ PILOT]
7. **Pass/Fail & bài học cho lớp.**
