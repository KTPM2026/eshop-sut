# P2 — Bộ dữ kiện & câu hỏi quyết định cho 15 alert (hỗ trợ gán nhãn)

**Phát 23120317.** File này do AI trích **dữ kiện khách quan** từ `../../alert/2026-10-14-ZAP-Report-.json` để bạn gán nhãn nhanh. 
**AI KHÔNG điền cột Nhãn/Ưu tiên** — đó là phán xử độc lập của bạn (Ground Truth). Đọc "Câu hỏi quyết định" rồi tự kết luận.

> Cách dùng: với mỗi alert, đọc *Bằng chứng* + *Bối cảnh*, trả lời *Câu hỏi quyết định*, rồi ghi Nhãn (`Thật`/`Giả`/`Chưa đủ`) + Ưu tiên (P1–P4) + 1 câu lý do vào `alert-labeling-template.md`. Ghi giờ bắt đầu/kết thúc.

Nhắc ma trận ưu tiên: P1 dễ+cao · P2 dễ+thấp · P3 khó+cao · P4 khó+thấp/nghi giả.

---

### #1 — Strict-Transport-Security Header Not Set · Low(High) · CWE-319 · x1
- **Host:** `content-autofill.googleapis.com` (dịch vụ autofill của Chrome).
- **Bằng chứng:** `GET https://content-autofill.googleapis.com/v1/pages/...`
- **Bối cảnh:** URL này **không phải EShop** — là traffic trình duyệt Chrome tự gọi, lọt vào do scope ZAP chưa giới hạn.
- **Câu hỏi quyết định:** Alert này nằm trên hệ thống của nhóm (EShop localhost) hay của bên thứ ba? Có thuộc phạm vi kiểm thử không?
- Nhãn: ____ · Ưu tiên: ____ · Lý do: __________

### #2 — Re-examine Cache-control Directives · Info(Low) · CWE-525 · x1
- **Host:** `content-autofill.googleapis.com` (autofill Chrome).
- **Bằng chứng:** `param=cache-control | evidence=private,max-age=604800`
- **Bối cảnh:** Cũng là domain Google, không phải EShop. Mức Informational.
- **Câu hỏi quyết định:** Giống #1 — có trong phạm vi EShop không? Mức ảnh hưởng?
- Nhãn: ____ · Ưu tiên: ____ · Lý do: __________

### #3 — SQL Injection · High(Low) · CWE-89 · x1  ⭐ (alert quan trọng)
- **Host:** `localhost:3000` (API EShop).
- **Bằng chứng:** `GET /api/products?search=%27` (một dấu nháy `'`) · `param=search` · `evidence=HTTP/1.1 500 Internal Server Error` · `attack='`
- **Bối cảnh:** Bơm 1 dấu nháy vào `search` làm server trả lỗi 500 — dấu hiệu câu SQL bị vỡ cú pháp.
- **Câu hỏi quyết định:** Lỗi 500 khi thêm `'` chứng tỏ input đi thẳng vào câu SQL? Bạn có kiểm chứng thêm được bằng payload boolean/union (hoặc chạy sqlmap ở Lab 2) không? Khả năng khai thác & mức ảnh hưởng (lộ bảng `users`) cao hay thấp?
- Nhãn: ____ · Ưu tiên: ____ · Lý do: __________

### #4 — Cross-Domain Misconfiguration (CORS) · Medium(Medium) · CWE-264 · x3
- **Host:** `localhost:3000` (API).
- **Bằng chứng:** `GET /api/products?search=` & `/api/products/1` · `evidence=Access-Control-Allow-Origin: *`
- **Bối cảnh:** API trả header `Access-Control-Allow-Origin: *` → cho mọi origin gọi.
- **Câu hỏi quyết định:** Header `*` có thật trong response không (đã có evidence)? Với API có dữ liệu đăng nhập, việc mở CORS `*` đáng lo ở mức nào?
- Nhãn: ____ · Ưu tiên: ____ · Lý do: __________

### #5 — Server Leaks Info via "X-Powered-By" · Low(Medium) · CWE-497 · x3
- **Host:** `localhost:3000`.
- **Bằng chứng:** `evidence=X-Powered-By: Express`
- **Bối cảnh:** Response lộ công nghệ backend (Express). Rò rỉ thông tin mức thấp.
- **Câu hỏi quyết định:** Header này có thật không (có evidence)? Mức ảnh hưởng — chỉ lộ tech stack hay cho phép khai thác trực tiếp?
- Nhãn: ____ · Ưu tiên: ____ · Lý do: __________

### #6 — X-Content-Type-Options Header Missing · Low(Medium) · CWE-693 · x3
- **Host:** `localhost:3000` (API).
- **Bằng chứng:** `param=x-content-type-options` (thiếu header `nosniff`).
- **Bối cảnh:** Thiếu header chống MIME-sniffing. Phòng thủ chiều sâu.
- **Câu hỏi quyết định:** Header có thực sự vắng mặt không? Thiếu nó gây rủi ro cao hay chỉ là hardening?
- Nhãn: ____ · Ưu tiên: ____ · Lý do: __________

### #7 — Authentication Request Identified · Info(High) · CWE=-1 · x1
- **Host:** `localhost:3000`.
- **Bằng chứng:** `POST /api/login` · `param=email` · `evidence=password`
- **Bối cảnh:** ZAP chỉ **nhận diện** đây là request đăng nhập — mang tính thông tin, không khẳng định lỗ hổng.
- **Câu hỏi quyết định:** Đây là một lỗ hổng hay chỉ là ghi nhận thông tin (informational)? Có "ảnh hưởng" gì để xếp ưu tiên không?
- Nhãn: ____ · Ưu tiên: ____ · Lý do: __________

### #8 — Path Traversal · High(Low) · CWE-22 · x1  ⭐ (dễ nhầm)
- **Host:** `localhost:5173` (dev server Vite của frontend).
- **Bằng chứng:** `GET /node_modules/.vite/deps/chunk-CYJPkc-J.js?v=%2Fchunk-CYJPkc-J.js` · `param=v` · `attack=/chunk-CYJPkc-J.js`
- **Bối cảnh:** "attack" chỉ là tham số cache-busting `v=` của Vite trỏ tới chính file chunk, không phải đọc file hệ thống (vd `/etc/passwd`). Confidence ZAP = Low.
- **Câu hỏi quyết định:** Có bằng chứng server thật sự đọc được file ngoài ý muốn không, hay payload chỉ trùng tên file chunk của Vite? Confidence Low + chạy trên dev server gợi ý điều gì?
- Nhãn: ____ · Ưu tiên: ____ · Lý do: __________

### #9 — Content Security Policy (CSP) Header Not Set · Medium(High) · CWE-693 · x2
- **Host:** `localhost:5173`.
- **Bằng chứng:** `GET /` và `/forgot-password` — không có header CSP.
- **Bối cảnh:** Thiếu CSP → giảm khả năng chặn XSS (liên quan trực tiếp Lab 1). Confidence High.
- **Câu hỏi quyết định:** Header CSP có thật sự vắng không? Kết hợp với lỗ hổng XSS đã biết, mức ảnh hưởng cao hay thấp?
- Nhãn: ____ · Ưu tiên: ____ · Lý do: __________

### #10 — Missing Anti-clickjacking Header · Medium(Medium) · CWE-1021 · x2
- **Host:** `localhost:5173`.
- **Bằng chứng:** `param=x-frame-options` thiếu trên `/` và `/forgot-password`.
- **Bối cảnh:** Thiếu X-Frame-Options/CSP frame-ancestors → nguy cơ bị nhúng iframe (clickjacking).
- **Câu hỏi quyết định:** Header có vắng thật không? Clickjacking trên EShop khai thác dễ/khó, ảnh hưởng tới đâu?
- Nhãn: ____ · Ưu tiên: ____ · Lý do: __________

### #11 — Timestamp Disclosure - Unix · Low(Low) · CWE-497 · x1
- **Host:** `localhost:5173`.
- **Bằng chứng:** `GET /node_modules/.vite/deps/react-dom_client.js?v=...` · `evidence=2080374784`
- **Bối cảnh:** Con số `2080374784` nằm trong mã nguồn React (hằng số nội bộ), ZAP đoán là timestamp. Confidence Low, trong file thư viện.
- **Câu hỏi quyết định:** Con số này có thật là một timestamp nhạy cảm của ứng dụng, hay chỉ là hằng số trong code React? → gợi ý đây là loại gì?
- Nhãn: ____ · Ưu tiên: ____ · Lý do: __________

### #12 — X-Content-Type-Options Header Missing (frontend) · Low(Medium) · CWE-693 · x3
- **Host:** `localhost:5173`.
- **Bằng chứng:** `param=x-content-type-options` trên `/node_modules/vite/dist/client/env.mjs`, `/src/index.css`...
- **Bối cảnh:** Giống #6 nhưng trên tài nguyên tĩnh của dev server Vite.
- **Câu hỏi quyết định:** Header thiếu thật không? Trên dev server tài nguyên tĩnh, rủi ro mức nào?
- Nhãn: ____ · Ưu tiên: ____ · Lý do: __________

### #13 — Information Disclosure - Sensitive Information in URL · Info(Medium) · CWE-598 · x1
- **Host:** `localhost:5173`.
- **Bằng chứng:** `GET /?token=Rpbdl6bfRWhO` · `param=token` · `evidence=token`
- **Bối cảnh:** Có `token` nằm trên query string URL (có thể là reset token quy trình forgot-password). Token trên URL dễ bị log/lộ qua Referer.
- **Câu hỏi quyết định:** `token` trên URL là dữ liệu nhạy cảm của EShop hay tham số vô hại? Nếu là reset token thì việc đặt trên URL đáng lo không?
- Nhãn: ____ · Ưu tiên: ____ · Lý do: __________

### #14 — Information Disclosure - Suspicious Comments · Info(Medium) · CWE-615 · x6
- **Host:** `localhost:5173`.
- **Bằng chứng:** `GET /@react-refresh` · `evidence=// TODO: rename these field`, `ogic is copy-pasted from similar logic...`
- **Bối cảnh:** Các comment `TODO`/ghi chú nằm trong mã thư viện React Refresh (dev), không phải code nghiệp vụ EShop.
- **Câu hỏi quyết định:** Comment này lộ bí mật của EShop hay chỉ là comment trong thư viện framework? Có khai thác được gì không?
- Nhãn: ____ · Ưu tiên: ____ · Lý do: __________

### #15 — Modern Web Application · Info(Medium) · CWE=-1 · x2
- **Host:** `localhost:5173`.
- **Bằng chứng:** `evidence=<script type="module">import { injectIntoGlobalHook } ... @react-refresh ...`
- **Bối cảnh:** ZAP chỉ ghi nhận đây là ứng dụng web hiện đại (SPA) để điều chỉnh cách crawl — thuần thông tin.
- **Câu hỏi quyết định:** Đây là lỗ hổng hay chỉ là ghi chú kỹ thuật của ZAP về loại ứng dụng?
- Nhãn: ____ · Ưu tiên: ____ · Lý do: __________

---

## Sau khi điền xong
1. Chép Nhãn/Ưu tiên/Lý do sang bảng chính `alert-labeling-template.md`, ghi tổng thời gian.
2. Khóa nhãn (không sửa) **trước khi** xem N2/AI.
3. Đối chiếu với Như → chốt nhãn chuẩn (bảng cuối template).

> Mẹo kiểm chứng thêm: với alert `localhost`, có thể gửi lại request trong ZAP (chuột phải → Resend/Open in Requester) để tự xác nhận header/evidence thay vì chỉ tin tên alert.
