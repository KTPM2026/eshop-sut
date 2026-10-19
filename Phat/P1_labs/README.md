# P1 — Hoàn thiện Lab 1 (XSS/ZAP) & Lab 2 (SQLi/sqlmap)

**Phát (23120317).** Gói việc P1 theo đề cương (4 điểm).

## Nội dung thư mục
| File | Mô tả | Trạng thái |
|---|---|---|
| `xss-payloads.txt` | Wordlist payload Reflected XSS nạp vào ZAP Fuzzer (Lab 1), có marker `ZAPX<n>` để dò nhanh | ✅ AI dựng |
| `reset-db.ps1` / `reset-db.sh` | Script khôi phục `database.sqlite` từ `database.sqlite.bak` sau Lab 2 | ✅ AI dựng |
| `lab-verify-notes.md` | 3 giá trị đã xác minh từ source + luồng XSS + danh mục "còn phải tự chạy" | ✅ AI dựng |

## Hướng dẫn Lab (đã vá) 
Bản chính thức ở [`seminar/docs/lab-huong-dan.md`](../../../seminar/docs/lab-huong-dan.md) đã được sửa các giá trị sai (endpoint, DB, sqlmap flags) — chi tiết thay đổi xem `lab-verify-notes.md` mục 3.

## Việc Phát còn phải tự làm
Xem checklist cuối `lab-verify-notes.md` (mục 4): chạy thật ZAP + sqlmap, chụp ảnh/log, kiểm chứng XSS trên frontend, quay clip, ghi timing cho P3a.
