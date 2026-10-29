# NHẬT KÝ TIẾN ĐỘ & BÁO CÁO MINH CHỨNG — VŨ QUỐC HÙNG (23120268)

**Môn học:** Kiểm thử phần mềm (Software Testing) — FIT@HCMUS  
**Seminar:** Security Testing in Website  
**Phân công:** H1 (3đ) + H2 (3đ) + H3 (3đ) + H4 (3đ) + Mở rộng 1.4 (A02 & A07)  
**Tổng cộng:** 12 điểm quy ước  

---

## I. TỔNG QUAN SẢN PHẨM BÀN GIAO

| Nhiệm vụ | Sản phẩm bàn giao | Tệp minh chứng tồn tại | Trạng thái |
|:---:|:---|:---|:---:|
| **H1** | Baseline SUT (commit, thông số) | `git log`, `setup_guide.md` | ✅ 100% |
| **H1** | File alert gốc từ ZAP (JSON) | `alert/2026-10-14-ZAP-Report-.json` (43 KB) | ✅ |
| **H1** | File alert bổ sung (Task 1.4) | `alert/zap-alerts-auth.json` (30 KB, 24 alerts) | ✅ |
| **H1** | Raw HTTP request tìm kiếm | `search.raw` (gốc `/api/products?search=phone`) | ✅ |
| **H1** | Raw HTTP request reset password | `alert/reset_password.raw` | ✅ |
| **H1** | Zest Script Macro EShop | `alert/script_recoed.zst` (2.3 MB) | ✅ |
| **H2** | Fuzzer data-driven kết quả | `alert/data_driven.csv` | ✅ |
| **H2** | Demo 3 kịch bản ZAP | Video quay màn hình (dự kiến upload YouTube) | ⏳ Video |
| **H3** | WAF Middleware | `backend/waf_middleware.js` | ✅ |
| **H3** | Lab Server (cổng 3001) | `backend/server_fuzzer_lab.js` | ✅ |
| **H3** | Script test đối chứng | `backend/test_waf.sh` (5/5 PASS) | ✅ |
| **1.4** | Brute-force OTP Script | `demo/brute_force_otp/brute_force_otp.py` | ✅ |
| **1.4** | Log kết quả tấn công OTP | `demo/brute_force_otp/brute_force_otp.log` | ✅ |
| **H4** | Báo cáo thực nghiệm chi tiết | `docs/slide-seminar/bao_cao_thuc_nghiem_zap_hung.md` | ✅ |
| **H4** | Kịch bản thuyết trình + Live Demo | Soạn thảo bằng văn bản (kịch bản chi tiết) | ✅ |
| **H4** | Nhật ký sử dụng AI (kê khai) | `docs/nhat_ky_su_dung_ai_hung.md` (233 KB) | ✅ |

---

## II. CHI TIẾT THEO TỪNG NHIỆM VỤ

---

### 📦 H1 — Thiết lập Môi trường SUT, ZAP Scope & Xuất Dữ liệu Thật (3 điểm)

**Thời gian hoàn thành:** 14/10/2026 – 18/10/2026

#### 1.1 Chốt Baseline SUT (Môi trường kiểm thử chuẩn)

- **Commit chốt:** `d1df4745d03289a2fdeec6f30eb23260f404e81f` (nhánh `main`).
- **Kiến trúc hệ thống:**

| Thành phần | URL | Công nghệ |
|:---|:---|:---|
| Backend API | `http://localhost:3000` | Node.js v22.22.1 + Express + SQLite |
| Frontend Web | `http://localhost:5173` | React SPA (Vite) |
| Frontend Admin | `http://localhost:5174` | React SPA (Vite) |
| Database | `backend/database.sqlite` | SQLite (reset bằng `node database.js`) |

- **OWASP ZAP:** Phiên bản `2.17.0`, chạy tại `127.0.0.1:8080` trên Linux/Ubuntu.
- **Trình duyệt kiểm thử:** Google Chrome (chạy qua Manual Explore của ZAP, tự gắn cờ `--proxy-server=127.0.0.1:8080`).

> **Lý do chọn Chrome thay Firefox:** Firefox Snap bị AppArmor sandbox chặn `/tmp` → lỗi profile. Chrome không bị vướng sandbox này.

#### 1.2 Giải quyết 2 "Bẫy" kỹ thuật trọng yếu

**Bẫy 1: Khác Origin giữa Frontend `:5173` và Backend `:3000`**

- **Vấn đề:** Single Page App React gọi API sang `localhost:3000` nhưng ZAP chỉ nhận biết `localhost:5173` → coi tất cả request API là Out-of-Scope → bỏ sót toàn bộ backend.
- **Giải pháp:** Tạo Context `EShop` trong ZAP với Regex bao quát:
  ```
  http://localhost:.*
  ```

**Bẫy 2: Xác thực Bearer JWT (không phải Cookie Session)**

- **Vấn đề:** EShop lưu JWT trong `localStorage`, gửi qua header `Authorization: Bearer <token>`. ZAP Active Scanner không tự gắn token → nhận 401 Unauthorized → không quét được endpoint nào sau đăng nhập.
- **Giải pháp:** Cấu hình **ZAP Replacer** (`Tools ➔ Replacer`):
  - Match Type: `Request Header (add if not present)`
  - Match String: `Authorization`
  - Replacement String: `Bearer <jwt_token>`
  - Target URL Regex: `http://localhost:3000/.*`
  - **Kết quả:** 100% request Active Scan tự động mang token hợp lệ.

#### 1.3 Sản phẩm bàn giao H1

**1. File `alert/2026-10-14-ZAP-Report-.json`** (43 KB) — Bàn giao cho **Như (N2)** và **Phát (P2)** gán nhãn Ground Truth, và **Lân (A1)** nạp vào AI Triage.

Tóm tắt 15 alert thật đã được ZAP phát hiện:

| Mức độ | Alert | Endpoint |
|:---:|:---|:---|
| 🔴 High | SQL Injection | `http://localhost:3000` |
| 🔴 High | Path Traversal | `http://localhost:5173` |
| 🟠 Medium | Content Security Policy (CSP) Header Not Set | `http://localhost:5173` |
| 🟠 Medium | Missing Anti-clickjacking Header | `http://localhost:5173` |
| 🟠 Medium | Cross-Domain Misconfiguration | `http://localhost:3000` |
| 🟡 Low | Server Leaks Info via X-Powered-By | `http://localhost:3000` |
| 🟡 Low | X-Content-Type-Options Header Missing | `:3000` và `:5173` |
| 🟡 Low | Timestamp Disclosure - Unix | `http://localhost:5173` |
| ℹ️ Info | Authentication Request Identified | `http://localhost:3000` |
| ℹ️ Info | Information Disclosure - Sensitive Information in URL | `http://localhost:5173` |
| ℹ️ Info | Information Disclosure - Suspicious Comments | `http://localhost:5173` |

**2. File `alert/zap-alerts-auth.json`** (30 KB, 24 alerts) — Bàn giao cho **Lân (A1)** (bổ sung sau Task 1.4):
- 24 instances **User Agent Fuzzer (Informational)** trên 2 endpoint: `/api/reset-password` (12 instances) và `/api/forgot-password` (12 instances).

**3. File `search.raw`** — Raw HTTP request thực của tìm kiếm sản phẩm:
```http
GET http://localhost:3000/api/products?search=phone HTTP/1.1
Host: localhost:3000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
User-Agent: Mozilla/5.0 (X11; Linux x86_64) ...
```
→ Bàn giao cho **Long (L1)** để chạy: `sqlmap -r search.raw --batch`

**4. File `alert/reset_password.raw`** — Raw HTTP request của chức năng Reset Password:
```http
POST http://localhost:3000/api/reset-password HTTP/1.1
Content-Type: application/json
...
{"email":"admin@eshop.com","resetToken":"9767","newPassword":"Password 123"}
```
→ Phục vụ kiểm thử brute-force OTP (Task 1.4) và **Phát (P3a pilot)**.

**5. File `alert/script_recoed.zst`** (2.3 MB) — Zest Script macro `EShop_Shopping_Flow` đã ghi lại toàn bộ luồng mua hàng có xác thực.

---

### 📦 H2 — Thực nghiệm 3 Kịch bản ZAP & 3 Thành phần Kiểm thử (3 điểm)

**Thời gian hoàn thành:** 14/10/2026 – 18/10/2026  
**Minh chứng chính:** Video quay màn hình thực nghiệm trực tiếp trên OWASP ZAP (dự kiến upload YouTube).

#### 2.1 Ba kịch bản Demo hoàn chỉnh

**Kịch bản 1 — Cài đặt & Kết nối (Smoke Test Connectivity):**
- Khởi chạy ZAP 2.17.0, tích hợp Chrome qua **Manual Explore** (tự động proxy `127.0.0.1:8080`).
- **Checkpoint:** Tab `History` của ZAP ghi nhận `GET http://localhost:5173` và `GET http://localhost:3000/api/...` với HTTP 200 OK → Hạ tầng Proxy MitM thông suốt.
- *Bỏ qua cài SSL CA Certificate vì SUT chạy HTTP nội bộ.*

**Kịch bản 2 — Chức năng cơ bản (Crawl + Passive Scan):**
- **Traditional Spider** trên `localhost:5173`: Chỉ tìm được 1–2 URL tĩnh do không thể đọc JavaScript của React SPA.
- **AJAX Spider**: Sử dụng Chrome Headless thực sự render DOM, tự động click liên kết, thu thập toàn bộ routes React và API endpoints `:3000`.
- **Passive Scan**: Tự động gắn cờ `Content Security Policy Not Set`, `Anti-clickjacking Missing`, `X-Content-Type-Options` → Kết quả hiển thị tab **Alerts**.
- **Active Scan đơn lẻ**: Chuột phải vào `GET /api/products?search=` → Attack → Active Scan trên 1 endpoint cụ thể.

**Kịch bản 3 — Luồng có Xác thực JWT (Authenticated Flow):**
- Đăng nhập `test@eshop.com / Test1234!` → Copy JWT Token từ Local Storage → Cấu hình Replacer.
- Duyệt trọn vẹn luồng nghiệp vụ: Tìm kiếm `phone` → Thêm giỏ hàng (`/api/cart`) → Áp mã giảm giá `SAVE10` (`/api/apply-coupon`) → Checkout (`/api/checkout`) → Xem lịch sử đơn hàng (`/api/orders`).
- Chạy **Active Scan** toàn bộ Context `EShop` với JWT token tự động.

#### 2.2 Ba thành phần kiểm thử cốt lõi

**1️⃣ Record & Playback (Zest Script Macro)**

| Bước | Thao tác | Kết quả |
|:---:|:---|:---|
| **Record** | ZAP Scripts → Record a New Zest Script → Đặt tên `EShop_Shopping_Flow` → Thực hiện luồng: Tìm kiếm `phone` → Click `iPhone 15 Pro Max` → Thêm giỏ hàng | Script Zest được tạo tự động chứa chuỗi HTTP requests tuần tự |
| **Playback** | Bấm Run (nút Play xanh) | ZAP tự phát lại toàn bộ luồng, kết quả `PASSED (HTTP 200 OK)` trong tab Zest Results |

→ **Ý nghĩa:** Security Regression Testing — Mỗi khi có bản build mới, chạy lại Zest Script để kiểm tra không có lỗ hổng mới xuất hiện mà không cần thao tác tay lại từ đầu.

**2️⃣ Data-driven Testing (ZAP Fuzzer)**

- **Endpoint:** `GET /api/products?search=phone` trong tab History → Attack → Fuzz...
- **5 payload đã nạp** (bôi đen giá trị tham số `search`):

| STT | Payload | Loại kiểm thử | Kết quả | HTTP Code |
|:---:|:---|:---|:---|:---:|
| 1 | `phone` | Dữ liệu hợp lệ | Trả về danh sách sản phẩm | 200 |
| 2 | `laptop` | Dữ liệu hợp lệ | Trả về danh sách sản phẩm | 200 |
| 3 | `' OR '1'='1` | SQL Injection | Server trả về toàn bộ sản phẩm (lỗ hổng SQLi xác nhận!) | 200 |
| 4 | `<script>alert(1)</script>` | XSS cơ bản | Server phản hồi bình thường | 200 |
| 5 | `<img src=x onerror=alert('ZAP_Fuzz')>` | XSS Event Handler | **Internal Server Error!** | **500** |

→ Kết quả thực tế đã xuất ra file `alert/data_driven.csv`.

→ **Phân tích bất thường:** Payload 5 gây HTTP 500, kích thước phản hồi (`Size Resp. Body`) thay đổi đột biến so với payload hợp lệ (73 bytes vs 185 bytes) → Xác nhận ứng dụng xử lý không an toàn đầu vào.

**3️⃣ Checkpoints & Xác minh Proof-of-Concept trên Trình duyệt**

- **Checkpoint tự động (ZAP):** Active Scan gắn cờ `Cross Site Scripting (Reflected)` mức High Risk trên tham số `search`.
- **Checkpoint kiểm chứng thực tế (Browser PoC):** Nhập trực tiếp trên `localhost:5173`:
  ```html
  <img src=x onerror=alert('Reflected_XSS_Chrome_Success')>
  ```
- **Kết quả:** Hộp thoại `alert: Reflected_XSS_Chrome_Success` kích hoạt trực tiếp trên Chrome.
- **Nguyên nhân kỹ thuật:** `Home.jsx` dòng 64 sử dụng `dangerouslySetInnerHTML={{ __html: search }}` mà không sanitize đầu vào → OWASP A03:2021 - Cross-Site Scripting.
- **Payload PoC lưu trong** `context_fu.md` (danh sách 6 payload XSS đã kiểm chứng).

---

### 📦 H3 — Xây dựng Bộ lọc WAF cho Thí nghiệm AI Fuzzer (3 điểm)

**Thời gian hoàn thành:** 14/10/2026 (đêm)  
**Nguyên tắc:** Không chạm vào `server.js` gốc của SUT, mọi thay đổi đều trong bản lab cô lập.

#### 3.1 Các tệp đã tạo mới

**`backend/waf_middleware.js`** (2.7 KB):
- **Level 1 (Cơ bản):** Chặn dựa trên khoảng trắng (`OR`, `AND`, `UNION`, `SELECT`, `<script`, `javascript:`). Thiết kế CỐ Ý có thể bypass bằng `/**/` để AI Fuzzer có đất "học".
- **Level 2 (Strict):** Chặn triệt để comment (`/*`, `*/`, `--`), dấu chấm phẩy, toàn bộ event handler HTML.
- **Phản hồi JSON chi tiết cho AI:**
  ```json
  {
    "status": "BLOCKED",
    "error": "WAF_INPUT_BLOCKED",
    "blocked_keyword": " OR ",
    "waf_level": 1
  }
  ```

**`backend/server_fuzzer_lab.js`** (2.6 KB) — Lab Server cổng **3001**:
- `GET /api/products?search=<payload>` — Endpoint fuzzing chính.
- `GET /api/waf/status` — Kiểm tra trạng thái WAF.
- `POST /api/waf/toggle` — Bật/tắt hoặc đổi level WAF.
- `POST /api/waf/reset` — Reset về Level 1.

**`backend/test_waf.sh`** (3.3 KB) — Script kiểm thử đối chứng (chmod +x, có thể thực thi):

| Test | Kịch bản | Input | Kỳ vọng | Kết quả |
|:---:|:---|:---|:---:|:---:|
| 1 | Người dùng bình thường | `search=phone` | HTTP 200 | ✅ 200 OK |
| 2 | SQLi cơ bản | `search=' OR 1=1 --` | HTTP 403 | ✅ 403 Blocked |
| 3 | XSS cơ bản | `search=<script>alert(1)</script>` | HTTP 403 | ✅ 403 Blocked |
| 4 | AI Bypass (inline comment) | `search='/**/OR/**/1=1--` | HTTP 200 | ✅ 200 (Bypass thành công!) |
| 5 | Toggle WAF off | `search=' OR 1=1 --` (WAF off) | HTTP 200 | ✅ 200 OK |

**→ Kết quả: 5/5 PASS**

#### 3.2 Thông tin bàn giao cho đồng đội

| Người nhận | Thông tin bàn giao |
|:---|:---|
| **Long (L2)** — AI Fuzzer Feedback Loop | Target: `http://localhost:3001/api/products?search=<payload>` · Phản hồi 403 kèm `blocked_keyword` → đưa vào thuật toán Feedback Loop |
| **Lân (A2)** — Benchmark 3 nhánh | API Toggle: `POST http://localhost:3001/api/waf/toggle` · Reset: `POST http://localhost:3001/api/waf/reset` → Dùng trong script benchmark tự động |

---

### 📦 Nhiệm vụ mở rộng 1.4 — Thực nghiệm A02 & A07 (Bonus)

**Thời gian hoàn thành:** 18/10/2026  
**Nội dung phân công:** Thực nghiệm OWASP A02 (Cryptographic Failures) và A07 (Authentication Failures) trên 2 endpoint `/api/forgot-password` và `/api/reset-password`.

#### 4.1 Xuất alert thực tế Task 1.4

- **Công cụ:** ZAP Core API: `http://localhost:8080/JSON/core/view/alerts/?baseurl=http://localhost:3000&start=0&count=100`
- **Kết quả:** `alert/zap-alerts-auth.json` — 24 instances **User Agent Fuzzer** trên 2 endpoint.
- **Lý do chỉ có Informational:** Passive Scan chỉ phát hiện header User-Agent thay đổi mà không gửi payload tấn công (thiết kế đúng của Passive Scan). Lỗ hổng A07 thực sự cần chứng minh bằng brute-force thực tế (xem mục tiếp theo).

#### 4.2 Stress Test Concurrency SQLite

- **Mục đích:** Kiểm tra khả năng chịu tải đồng thời của SQLite khi nhận 51 requests brute-force song song (OTP range `2000–2050`).
- **Kết quả:**
  - 100% requests trả về `400 Bad Request` (OTP sai).
  - 0 lỗi `500 Internal Server Error`.
  - 0 lỗi `SQLITE_BUSY` (Database lock).
  - Server backend hoàn toàn ổn định sau khi chạy.

#### 4.3 Brute-force OTP (A07 - Authentication Failures) — Kết quả thực tế

**Script:** `demo/brute_force_otp/brute_force_otp.py`  
**Log:** `demo/brute_force_otp/brute_force_otp.log`  

**Tóm tắt kết quả thực nghiệm** (Log ngày 27/10/2026 11:07:43):

| Thông số | Giá trị |
|:---|:---|
| Tài khoản mục tiêu | `admin@eshop.com` |
| Không gian tìm kiếm OTP | 9.000 mã (từ 1000–9999) |
| Số luồng song song | 30 |
| OTP thực tế của server | `8112` |
| Số lượt requests đã thử | 7.144 |
| Thời gian thực thi | **4.99 giây** |
| Tốc độ tấn công | **1.431,5 requests/giây** |
| Kết quả cuối cùng | ✅ **THÀNH CÔNG — Chiếm quyền tài khoản Admin!** |
| Mật khẩu mới được thiết lập | `PwnedAdmin2026!` |

**Nguyên nhân lỗ hổng:**
- OTP chỉ có 4 chữ số (`Math.random()`) → Không gian quá nhỏ.
- Endpoint `/api/reset-password` **không có rate-limit** → Không giới hạn số lần thử.
- OTP không có TTL (Time-To-Live) → Không hết hạn.

**Khuyến nghị khắc phục:**
- OTP tối thiểu 6 số, sinh bằng CSPRNG (Cryptographically Secure Random).
- Rate limit: Tối đa 3–5 lần thử, sau đó khóa tài khoản 15 phút.
- TTL: OTP hết hạn sau 5–10 phút.

---

### 📦 H4 — Báo cáo & Chuẩn bị Thuyết trình (3 điểm)

**Thời gian hoàn thành:** 18/10/2026 – 28/10/2026

#### 5.1 Tài liệu đã tạo

| Tệp | Mô tả | Kích thước |
|:---|:---|:---|
| `docs/slide-seminar/bao_cao_thuc_nghiem_zap_hung.md` | Báo cáo thực nghiệm chi tiết theo 5 mục, đầy đủ kết quả, bảng số liệu, code snippet | 17 KB |
| `docs/nhat_ky_su_dung_ai_hung.md` | Nhật ký kê khai sử dụng AI — 44 lượt tương tác, đầy đủ prompt + phản hồi nguyên văn | 233 KB |
| `setup_ZAP.md` | Hướng dẫn cài đặt và cấu hình ZAP từng bước (tài liệu vận hành) | 4.2 KB |

#### 5.2 Kịch bản thuyết trình Live Demo đã soạn

Tổng hợp kịch bản thuyết trình cho **3 Demo trực tiếp trên giao diện OWASP ZAP**:

| Demo | Mục tiêu | Thao tác cốt lõi |
|:---:|:---|:---|
| **Demo 1** | Kết nối Proxy & Smoke Test | Manual Explore → Chrome Launch → Xem tab History (200 OK) |
| **Demo 2** | AJAX Spider & Passive Scan | AJAX Spider → Tab Alerts → Requester Replay |
| **Demo 3** | JWT Auth + Zest Script + Active Scan | Context EShop → Replacer JWT → Zest Script Run → Active Scan |

---

## III. THỐNG KÊ TỔNG HỢP

### Số lượng sản phẩm bàn giao thực tế:

- **Tệp mã nguồn mới tạo:** 3 tệp (`waf_middleware.js`, `server_fuzzer_lab.js`, `test_waf.sh`)
- **Tệp dữ liệu thực nghiệm:** 7 tệp (`2026-10-14-ZAP-Report-.json`, `zap-alerts-auth.json`, `search.raw`, `reset_password.raw`, `script_recoed.zst`, `data_driven.csv`, `brute_force_otp.log`)
- **Tệp script thực nghiệm:** 1 tệp (`demo/brute_force_otp/brute_force_otp.py`)
- **Tệp tài liệu:** 4 tệp (báo cáo thực nghiệm, nhật ký AI, kịch bản thuyết trình, setup guide)
- **Video demo:** Đã quay màn hình thực nghiệm thực tế trên OWASP ZAP, dự kiến upload YouTube sau seminar.

### Lỗ hổng bảo mật đã xác minh:

| Mã OWASP | Loại lỗ hổng | Trạng thái xác minh |
|:---:|:---|:---:|
| A03:2021 | Cross-Site Scripting (Reflected XSS) — qua `dangerouslySetInnerHTML` trong `Home.jsx:64` | ✅ PoC nổ popup Chrome |
| A03:2021 | SQL Injection — tham số `search` trên `/api/products?search=` | ✅ ZAP Active Scan xác nhận, `' OR '1'='1` trả về toàn bộ data |
| A02:2021 | Mật khẩu lưu plaintext trong SQLite (xác nhận bởi sqlmap dump) | ✅ Tham chiếu kết quả Long (L1) |
| A07:2021 | Authentication Failure — OTP 4 số, không rate-limit, không TTL | ✅ Brute-force 7.144 requests trong 4.99s, chiếm tài khoản Admin |
| Config | Missing Content Security Policy header | ✅ Passive Scan gắn cờ |
| Config | Missing Anti-clickjacking header | ✅ Passive Scan gắn cờ |

---

### 📦 Đóng góp tài liệu chung cho nhóm — `demo_3_tool.md` & `comp_tool.md`

**Thời gian:** 11/10/2026 (soạn thảo) → 22/10/2026 (commit `6adf536` vào repo seminar)  
**Commit:** `6adf536ae27d36cbf536472cbe84a58d8f7a5ed5`  
**Author:** `hungvu09122005 <vuhung09122005@gmail.com>`

#### 6.1 Tệp `docs/slide-seminar/comp_tool.md` (12.7 KB — 148 dòng)

Tài liệu **So sánh ba công cụ thực nghiệm** (ZAP, Burp Suite, sqlmap) làm nền tảng nội dung cho **Slide 10** của bài thuyết trình nhóm. Bao gồm:

- **Phần ZAP:** Tổng quan kiến trúc MitM Proxy, 6 tính năng chính (Active/Passive Scan, Authenticated Scanning, WebSocket, Fuzzer, AJAX Spider), điểm nổi bật và điểm hạn chế thực tế.
- **Phần Burp Suite:** So sánh Community vs Professional vs Enterprise, các module chính (Proxy, Repeater, Intruder, Scanner, Extender/BApp Store), điểm mạnh/hạn chế của bản Community miễn phí (không có Scanner tự động, Intruder bị throttled).
- **Phần sqlmap:** Tổng quan, các tính năng chính (hỗ trợ 40+ DBMS, 6 kỹ thuật SQLi, System Takeover), điểm nổi bật Payload Engine, hạn chế khi gặp WAF.
- **Danh mục tài liệu tham khảo:** 10 nguồn trích dẫn học thuật và tài liệu kỹ thuật chính thức.

Nội dung tài liệu này được đối chiếu và xác nhận chính xác 100% với thực nghiệm kỹ thuật thực tế trên hệ thống SUT `eshop-sut`, đặc biệt các phần:
- Hạn chế của ZAP (Scope/Auth phức tạp với JWT) → Trực tiếp giải quyết trong H1.
- Hạn chế của Burp Community (không tự động) ↔ Điểm mạnh tự động hóa của ZAP.
- Hạn chế của sqlmap (không bao phủ toàn bộ web) → Định vị vai trò công cụ chuyên biệt.

**Giá trị:** Cung cấp nền lý luận kỹ thuật vững chắc cho toàn bộ phần thực nghiệm, giúp người nghe hiểu *tại sao* nhóm chọn 3 công cụ này thay vì chỉ đơn giản giới thiệu.

#### 6.2 Tệp `docs/slide-seminar/demo_3_tool.md` (31.7 KB — 319 dòng)

Tài liệu **Kịch bản Demo chi tiết: OWASP ZAP — Burp Suite — sqlmap** trên Case study `eshop-sut`. Đây là tài liệu kỹ thuật **toàn diện nhất** của cả nhóm, được sử dụng làm:
- Kịch bản tham chiếu cho tất cả thành viên nhóm khi chuẩn bị slide.
- Tài liệu mapping yêu cầu bảo mật (SEC-01 → SEC-07) → Công cụ phụ trách.

**Phần ZAP (Mục 1 — Phụ trách bởi Hùng):**

| Mục | Nội dung |
|:---|:---|
| 1.1 Mục tiêu & Phạm vi | ZAP phụ trách chính SEC-04 (XSS) và SEC-05 (SQLi cross-check) |
| 1.2 Demo cài đặt | 6 bước từ tải ZAP, mở lần đầu, cấu hình persistence, đến Manual Explore kiểm tra kết nối |
| 1.3 Demo chức năng cơ bản | So sánh Traditional Spider vs AJAX Spider trên React SPA, Passive Scan, Active Scan đơn lẻ |
| 1.4 Demo luồng phức tạp | 6 bước: Thiết lập JWT, Crawl xác thực, Luồng mua hàng đầy đủ, Active Scan, Đối chiếu alert với SEC, Export JSON |
| 1.5 Record & Playback | Chi tiết Zest Script: Record luồng mua hàng → Playback tự động → Regression Testing |
| 1.6 Data-driven | Fuzzer: `search` tham số + payload danh sách `[phone, laptop, SQLi, XSS, XSS Event]` |
| 1.7 Checkpoints | XSS Proof-of-Concept trên Chrome + Cross-check Alerts với đặc tả SEC |

**Phần Burp Suite (Mục 2) và sqlmap (Mục 3):** Soạn thảo đầy đủ làm tài liệu tham chiếu chung cho nhóm, phần thực thi do Như và Long đảm nhiệm.

**Bảng ánh xạ SEC → Công cụ** (Mục 0.2) — Đây là đóng góp chiến lược quan trọng:

| Mã | Yêu cầu bảo mật | Công cụ chính | Công cụ phụ |
|:---:|:---|:---:|:---:|
| SEC-01 | Mật khẩu không lưu plaintext | sqlmap | — |
| SEC-02 | API nhạy cảm yêu cầu JWT hợp lệ | Burp (Repeater) | ZAP |
| SEC-03 | API Admin kiểm tra role=admin | Burp | ZAP |
| SEC-04 | Input hiển thị UI phải escape (chống XSS) | **ZAP** | Burp |
| SEC-05 | Parameterized Query (chống SQLi) | **sqlmap** | ZAP |
| SEC-06 | API profile không cho đổi `role` từ client | Burp | — |
| SEC-07 | OTP đủ entropy, có hạn dùng | Burp Intruder / Script | — |

---

## IV. MỐI LIÊN HỆ VỚI CÁC THÀNH VIÊN NHÓM

```
[Vũ Quốc Hùng — Phụ trách ZAP & Môi trường SUT]
        │
        ├──► alert/2026-10-14-ZAP-Report-.json
        │         └──► Thạch Như (N2): Gán nhãn Ground Truth
        │         └──► Nguyễn Đức Phát (P2): Gán nhãn alert độc lập
        │         └──► Nguyễn Nhật Lân (A1): Nạp vào AI Triage
        │
        ├──► search.raw
        │         └──► Lê Chí Hoàng Long (L1): sqlmap -r search.raw --batch
        │
        ├──► alert/reset_password.raw
        │         └──► Lê Chí Hoàng Long (A07 brute-force)
        │         └──► Nguyễn Đức Phát (P3a pilot checklist)
        │
        └──► backend/waf_middleware.js + server_fuzzer_lab.js + test_waf.sh
                  └──► Lê Chí Hoàng Long (L2): AI Fuzzer Feedback Loop Target
                  └──► Nguyễn Nhật Lân (A2): Benchmark 3 nhánh Fuzzer
```

---

## V. GHI CHÚ VỀ VIDEO DEMO

Tất cả các thao tác trực tiếp trên OWASP ZAP trong H2 (3 kịch bản Demo) đã được thực hiện thực tế và quay màn hình lại. Video bao gồm:

- [x] Demo 1: Cài đặt, kết nối Chrome, xem tab History.
- [x] Demo 2: AJAX Spider chạy trên React SPA, tab Alerts Passive Scan, Replay bằng Requester.
- [x] Demo 3: Cấu hình Context EShop, Replacer JWT, chạy Zest Script `EShop_Shopping_Flow`, Active Scan.
- [ ] Upload lên YouTube — **Dự kiến hoàn thành trước ngày thuyết trình seminar**.

---

*Nhật ký tiến độ được cập nhật lần cuối: 29/10/2026 — Vũ Quốc Hùng (23120268)*
