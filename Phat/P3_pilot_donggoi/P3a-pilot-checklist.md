# P3a — Chạy thử (pilot) 2 Lab & ghi lỗi/timing

**Phát (23120317).** Buổi chạy thử **có hỗ trợ (assisted pilot) ngày 17/10/2026** trên máy Windows 11. Dưới đây là dữ liệu thật ghi lại trong buổi; phần timing là **ước lượng** (buổi có xen kẽ xử lý lỗi nên không bấm giờ liên tục). Khi chạy lại một mình nên bấm giờ sạch để chốt con số cho câu hỏi GVTH #4.

## Môi trường pilot
| Mục | Giá trị |
|---|---|
| OS / máy | Windows 11 |
| Node / npm | v22.19.0 / 10.9.3 |
| Python | 3.13.0 |
| sqlmap | 1.10.10 (cài qua `pip install sqlmap`) |
| OWASP ZAP | 2.17.0 |
| Chrome | 155 |
| Vite (frontend) | 8.0.12 |
| Backend 3000 / Frontend 5173 | Chạy được sau khi `npm install` |

## Lab 1 — ZAP / Reflected XSS
| Bước | Làm được? | Ghi chú |
|---|:---:|---|
| Mở ZAP + browser | ✅ (gián tiếp) | "Open Browser" của ZAP lỗi ChromeDriver (xem lỗi #2); phải dùng proxy thủ công / Chrome thường |
| Ghi nhận request `GET /api/products?search=` | ✅ | ZAP History bắt được |
| Fuzzer + nạp `xss-payloads.txt` | ✅ | 13 payload, 0 error |
| Đọc kết quả Fuzzer | ✅ | Payload có `'` → 500 (SQLi); payload không `'` → 200/`[]` |
| Xác thực XSS thực thi trên trình duyệt | ✅ | `<img src=x onerror=alert(document.domain)>` → alert `localhost` (ảnh `evidence/lab1-xss-alert.jpg`) |
| **Thời gian Lab 1** | ~8–10 phút | *(ước lượng, sau khi môi trường đã sẵn)* |

## Lab 2 — sqlmap / SQLi
| Bước | Làm được? | Ghi chú |
|---|:---:|---|
| Chuẩn bị `search.raw` | ✅ | Lưu từ ZAP (Save Raw → Request → Header) hoặc dùng file repo |
| `sqlmap ... --batch` → injectable | ✅ | UNION query, 6 cột, DBMS = SQLite (98 requests, ~1 phút) |
| `--tables` | ✅ | 7 bảng; sqlmap gọi DB là `SQLite_masterdb` |
| `-T users -C "..." --dump` | ✅ | Dump 2 user, password plaintext (`evidence/sqlmap_users_dump.csv`) |
| Reset DB | ✅ | Restart backend (tự seed lại) hoặc `reset-db.ps1` |
| **Thời gian Lab 2** | ~10–15 phút | *(ước lượng; riêng sqlmap chạy <1 phút, còn lại là đọc/giải thích)* |

## Lỗi hướng dẫn / môi trường phát hiện trong pilot (phần quan trọng nhất)
1. **`node_modules` chưa cài** → phải `npm install` ở `backend/` và `frontend-web/` trước. Nên ghi bước này vào "Chuẩn bị chung".
2. **ZAP "Open Browser" lỗi** `The provided browser was not found` — do ChromeDriver không khớp Chrome 155. Workaround: mở Chrome thủ công trỏ proxy `--proxy-server=...` hoặc dùng Firefox.
3. **Vite bind IPv6-only** → ZAP (gọi IPv4 `127.0.0.1`) bị *Connection refused*. Fix: chạy `npm run dev -- --host`.
4. **XSS — 3 điểm bẫy:** (a) URL `?search=` bị bỏ qua, phải GÕ vào ô tìm kiếm; (b) `<script>` không chạy qua `dangerouslySetInnerHTML`, phải dùng `onerror/onload`; (c) payload có dấu `'` làm vỡ SQL (500) → dùng payload không dấu nháy; (d) cửa sổ ZAP (WebDriver) nuốt `alert()` → dùng Chrome thường hoặc payload đổi `document.title`.
5. **sqlmap trên SQLite:** DB hiển thị là `SQLite_masterdb` (không phải `main`), **không dùng `-D`**; `--dump` cần `-C "cột"` vì không tự enumerate được cột.

→ Tất cả đã được cập nhật vào `lab-huong-dan.md` và `P1_labs/lab-verify-notes.md`.

## Kết luận pilot
- **Cả 2 Lab chạy được, lỗ hổng xác nhận thật** (XSS alert + SQLi dump password plaintext).
- **Trả lời sơ bộ GVTH #4:** thời lượng thao tác Lab 1 ~10 phút, Lab 2 ~15 phút là **hợp lý** — *với điều kiện môi trường đã dựng sẵn*. Lần đầu dựng môi trường + xử lý quirk (ChromeDriver, IPv6, npm install) tốn thêm ~30–45 phút → nên chuẩn bị/kiểm tra môi trường cho lớp **trước buổi**, không tính vào thời lượng lab.

## Minh chứng
- `../P1_labs/evidence/lab1-xss-alert.jpg` — alert XSS.
- `../P1_labs/evidence/lab1-zap-fuzzer.jpg` — bảng kết quả ZAP Fuzzer.
- `../P1_labs/evidence/sqlmap_users_dump.csv` + `lab2-sqlmap-results.md` — kết quả sqlmap.
