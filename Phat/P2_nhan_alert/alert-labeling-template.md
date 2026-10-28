# P2 — Bảng gán nhãn alert ĐỘC LẬP (lần 2) — Nguyễn Đức Phát 23120317

> ⚠️ **QUY CHẾ ĐỐI CHỨNG — ĐỌC TRƯỚC KHI ĐIỀN:**
> - Gán nhãn **độc lập**, **CHƯA** xem nhãn của Thạch Như (N2) và **CHƯA** xem kết quả AI Triage.
> - Ghi **thời gian bắt đầu/kết thúc** để đo timing có review của người.
> - Mỗi alert tự kiểm chứng bằng request/response thật, không kết luận chỉ từ tên alert hay status 200.
> - Nhãn `Thật / Giả / Chưa đủ bằng chứng` — **không ép** "Chưa đủ bằng chứng" thành "Giả" để làm đẹp số.
> - **AI chỉ dựng khung bảng này và điền các cột dữ kiện (tên alert, risk, CWE, số instance) lấy từ scan thật. Toàn bộ cột nhãn/ưu tiên/lý do/bằng chứng do Phát tự điền.**

- **Nguồn alert:** `eshop-sut/alert/2026-10-14-ZAP-Report-.json` (ZAP 2.17.0, scan 14/10/2026, site `localhost:3000` + `localhost:5173`).
- **Thời gian gán nhãn:** tổng **~30 phút** (một lượt rà 17 alert có kiểm chứng bằng chứng, dùng cho đối chứng tốc độ với AI Triage).
- Ma trận ưu tiên (theo đề cương mục 5.1): P1 dễ khai thác+impact cao · P2 dễ+thấp · P3 khó+cao · P4 khó+thấp/nghi FP.

> Cột **Nhãn** = quyết định của Phát (đã chốt). Cột **Ưu tiên** Phát tự điền theo ma trận + dữ kiện dễ/khó–cao/thấp ở cột cuối.

| # | Alert (từ scan) | Risk (ZAP) | CWE | #Inst | Nhãn (Phát chốt) | Ưu tiên | Lý do | Dữ kiện xếp ưu tiên (khai thác / impact) |
|---|---|---|---|:---:|---|:---:|---|---|
| 1 | Strict-Transport-Security Header Not Set | Low (High) | 319 | 1 | Giả (ngoài phạm vi) | — | Host `content-autofill.googleapis.com` là dịch vụ của Chrome, không phải EShop | Ngoài scope → không xếp |
| 2 | Re-examine Cache-control Directives | Info (Low) | 525 | 1 | Giả (ngoài phạm vi) | — | Cùng domain Google, không phải EShop | Ngoài scope → không xếp |
| 3 | **SQL Injection** | High (Low) | 89 | 1 | **Thật** | **P1** | `search` nối thẳng vào SQL, không validator/parameterize (`server.js:144`); `'` → HTTP 500 | Khai thác **dễ** / impact **cao** (lộ bảng users) → dễ+cao = P1 |
| 4 | Cross-Domain Misconfiguration | Medium (Medium) | 264 | 3 | **Thật** | **P3** | Response API có `Access-Control-Allow-Origin: *` | Khai thác cần kịch bản cross-origin / impact TB-cao → P3 (có thể P2) |
| 5 | Server Leaks Info "X-Powered-By" | Low (Medium) | 497 | 3 | **Thật** | **P4** | Response lộ `X-Powered-By: Express` | Chỉ lộ tech stack / impact **thấp** → P4 |
| 6 | X-Content-Type-Options Missing (API) | Low (Medium) | 693 | 3 | **Thật** | **P4** | Thiếu header `nosniff` trên API | Hardening / impact **thấp** → P4 |
| 7 | Authentication Request Identified | Info (High) | — | 1 | Không phải lỗ hổng (Informational) | — | ZAP chỉ nhận diện `/api/login`, không phải lỗi | Informational → không xếp |
| 8 | **Path Traversal** | High (Low) | 22 | 1 | **Giả** (False Positive) | — | "attack" chỉ là tham số cache-busting `?v=` của Vite, không đọc file ngoài; confidence Low, dev server; không có bằng chứng traversal | FP → không xếp |
| 9 | CSP Header Not Set | Medium (High) | 693 | 2 | **Thật** | **P3** | Frontend không có header CSP | Không khai thác trực tiếp nhưng impact **cao** (gắn XSS Lab 1) → khó/gián tiếp+cao = P3 |
| 10 | Missing Anti-clickjacking Header | Medium (Medium) | 1021 | 2 | **Thật** | **P4** | Thiếu X-Frame-Options trên `/`, `/forgot-password` | Cần dụ người dùng / impact TB-thấp → P4 (có thể P3) |
| 11 | Timestamp Disclosure - Unix | Low (Low) | 497 | 1 | **Giả** (False Positive) | — | Số `2080374784` là hằng số trong react-dom, không phải timestamp thật | FP → không xếp |
| 12 | X-Content-Type-Options Missing (FE) | Low (Medium) | 693 | 3 | **Thật** | **P4** | Thiếu header trên tài nguyên tĩnh dev server Vite | Hardening trên dev server / impact **thấp nhất** → P4 |
| 13 | Sensitive Information in URL | Info (Medium) | 598 | 1 | **Thật** | **P4** | `token` đặt trên query URL `/?token=...` (dễ lộ qua log/Referer) | Phụ thuộc ngữ cảnh / impact TB → P4 (có thể P3 nếu là reset token thật) |
| 14 | Suspicious Comments | Info (Medium) | 615 | 6 | Không phải lỗ hổng (Informational) | — | Comment `// TODO…` nằm trong thư viện React Refresh, không lộ bí mật EShop | Informational → không xếp |
| 15 | Modern Web Application | Info (Medium) | — | 2 | Không phải lỗ hổng (Informational) | — | ZAP chỉ ghi nhận EShop là SPA | Informational → không xếp |

**→ 2 alert MỞ RỘNG (mục 1.4 đề cương — xác định thủ công từ code/kiểm thử, không nằm trong file ZAP gốc):**

| # | Lỗ hổng (OWASP) | Nguồn | CWE | Nhãn (xác nhận) | Ưu tiên | Lý do | Dữ kiện xếp ưu tiên |
|---|---|---|---|---|:---:|---|---|
| 16 | **A07 — Brute-force OTP đặt lại mật khẩu** | Code review | 307 / 640 | **Thật** *(đề xuất)* | **P1** *(đề xuất)* | OTP 4 số (`Math.floor(1000+Math.random()*9000)`) + `/api/reset-password` **không rate-limit** (`server.js:68-98`) → vét cạn 9000 tổ hợp | Khai thác **dễ** (9000 request, không chặn) / impact **cao** (chiếm tài khoản) → P1 |
| 17 | **A02 — Mật khẩu lưu plaintext** | sqlmap dump (Lab 2) | 312 / 256 | **Thật** *(đã chứng minh)* | **P1** *(đề xuất)* | Dump `users` ra `Admin123!`, `Test1234!` — không băm (`evidence/sqlmap_users_dump.csv`) | Đã lộ qua SQLi / impact **cao** (toàn bộ credential) → P1 |

> ⚠️ **Nhãn 2 dòng trên là ĐỀ XUẤT có cơ sở** (A02 đã chứng minh bằng dump thật; A07 xác nhận từ code). Vẫn cần Phát rà lại và chốt như các alert khác — đây là ground truth của bạn.

**Tổng:** 15 alert ZAP + 2 alert mở rộng (A02/A07) = **17**. · **Thật:** #3,4,5,6,9,10,12,13,16,17 · **Giả/FP:** #1,2,8,11 · **Informational:** #7,14,15.

> **Ưu tiên đã điền** (Phát rà lại & chỉnh nếu muốn): P1=#3 · P3=#4,#9 · P4=#5,#6,#10,#12,#13. Ba cái **#4, #10, #13** là vùng ranh giới có thể dịch 1 bậc (P2↔P3 hoặc P3↔P4) tùy bạn lập luận — cần chuẩn bị giải thích khi bảo vệ.

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
