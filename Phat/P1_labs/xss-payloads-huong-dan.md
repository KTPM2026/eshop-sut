# Hướng dẫn dùng `xss-payloads.txt` (Lab 1 — ZAP Fuzzer)

> File `xss-payloads.txt` là **danh sách payload thuần**, mỗi dòng 1 payload, **không có dòng comment** — nạp thẳng vào ZAP Fuzzer (Type: File) hoặc Burp Intruder được ngay. ZAP Fuzzer **không tự lược bỏ dòng `#`**, nên file không chứa comment để tránh gửi nhầm comment thành payload.

## Cách nạp
ZAP: request tìm kiếm → **Attack → Fuzz** → bôi đen giá trị `search` → **Payloads → Add → Type: File** → chọn `xss-payloads.txt` → **Start Fuzzer**.

## Lưu ý quan trọng (đã kiểm chứng trên EShop 17/10)
- Endpoint search chạy vào `... WHERE name LIKE '%<payload>%'` → payload **có dấu nháy `'`** sẽ **làm vỡ SQL → trả 500** (đó là dấu hiệu SQLi, không phải XSS).
- Để **xác thực XSS thực thi** (bung alert), gõ payload **không có dấu nháy** vào ô tìm kiếm rồi bấm Tìm (ví dụ `<img src=x onerror=alert(document.domain)>`). SQL không vỡ → `Home.jsx` render qua `dangerouslySetInnerHTML` → `onerror/onload` chạy.
- URL `?search=...` **không dùng được** (app không đọc tham số từ URL) → phải **gõ vào ô tìm kiếm**.
- Cửa sổ trình duyệt do ZAP điều khiển có thể **nuốt hộp `alert`** → xác thực bằng Chrome thường.

## Phân nhóm payload (theo thứ tự dòng trong file)
| Dòng | Payload | Nhóm | Ghi chú |
|:---:|---|---|---|
| 1–4 | `<img onerror>`, `<svg onload>`, `"><img onerror>` | **An toàn SQL** (không dấu nháy) | Dùng xác thực XSS bung alert |
| 5–6 | `<script>...</script>` | Script cơ bản | Kiểm tra output encoding (lưu ý: `<script>` chèn qua innerHTML không tự chạy) |
| 7–10 | `<img>/<svg>` có `'` | Event handler | Có dấu nháy → sẽ vỡ SQL (500) trên endpoint này |
| 11–12 | `" onmouseover=`, `'><script>` | Thoát thuộc tính | |
| 13–14 | `<body onload>`, `<iframe javascript:>` | Thẻ body/iframe | |
| 15–16 | `<ScRiPt>`, `<img ... >` | Biến thể hoa/thường | So sánh khi có filter |
| 17 | `ZAPX13_benign_marker` | Chuỗi đối chứng | KHÔNG phải XSS — nếu phản xạ nguyên văn chỉ là reflection, giúp nhận biết false positive |

> Marker `ZAPX<n>` giúp dò nhanh trong response: gõ `ZAPX` vào ô Search của tab Response.

## Nguồn tham khảo
Các payload thuộc loại phổ biến trong kiểm thử XSS, có thể đối chiếu/bổ sung từ **OWASP XSS Filter Evasion Cheat Sheet** và **SecLists** (`Fuzzing/XSS/`).
