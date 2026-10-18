# BÁO CÁO THỰC NGHIỆM & NỘI DUNG TỔNG HỢP LÀM SLIDE SEMINAR
## Chủ đề: Security Testing for Web Applications (OWASP ZAP & Môi trường SUT)
**Môn học:** Kiểm thử phần mềm (Software Testing) — FIT@HCMUS  
**Người thực hiện:** **Vũ Quốc Hùng** — **MSSV: 23120268**  
**Phân công trách nhiệm:** Phụ trách Môi trường EShop (SUT), Demo công cụ **OWASP ZAP** và Dựng bộ lọc WAF cho AI Fuzzer (Tasks H1, H2, H3, H4 — Tổng 12 điểm).

---

## 📌 MỤC LỤC TỔNG HỢP
1. [Thông tin phân công & Cam kết nghiệm thu](#1-thông-tin-phân-công--cam-kết-nghiệm-thu)
2. [Gói việc H1: Môi trường SUT, Cấu hình Scope & Xuất dữ liệu thật](#2-gói-việc-h1-môi-trường-sut-cấu-hình-scope--xuất-dữ-liệu-thật)
3. [Gói việc H2: Thực nghiệm 3 Kịch bản & 3 Thành phần kiểm thử cốt lõi ZAP](#3-gói-việc-h2-thực-nghiệm-3-kịch-bản--3-thành-phần-kiểm-thử-cốt-lõi-zap)
4. [Gói việc H3: Xây dựng Bộ lọc đầu vào (WAF) cho Thí nghiệm AI Fuzzer](#4-gói-việc-h3-xây-dựng-bộ-lọc-đầu-vào-waf-cho-thí-nghiệm-ai-fuzzer)
5. [Đánh giá chuyên sâu: Điểm mạnh, Hạn chế của ZAP & Sự liên kết công cụ](#5-đánh-giá-chuyên-sâu-điểm-mạnh-hạn-chế-của-zap--sự-liên-kết-công-cụ)

---

## 1. THÔNG TIN PHÂN CÔNG & CAM KẾT NGHIỆM THU

Theo bản [Đề cương Seminar](de-cuong-seminar.md), phần việc của Vũ Quốc Hùng được phân chia thành 4 gói việc cân đối (12 điểm quy ước):

| Mã | Gói việc | Sản phẩm bàn giao chính | Người nhận bàn giao | Trạng thái kỹ thuật |
|:---:|---|---|---|:---:|
| **H1** | Thiết lập môi trường, cấu hình ZAP Scope, JWT và xuất dữ liệu quét | • Commit SUT, script reset CSDL.<br>• File alert gốc: `zap-alerts-eshop.json`<br>• File raw request: `search_request.txt`<br>• File raw request: `reset_password.req` | • Thạch Như (N2), Nguyễn Đức Phát (P2)<br>• Nguyễn Nhật Lân (A1)<br>• Lê Chí Hoàng Long (L1) |  **Hoàn thành 100%** |
| **H2** | Thực hiện 3 kịch bản ZAP & 3 thành phần (Record/Playback, Data-driven, Checkpoints) | • Kịch bản Zest Script `EShop_Shopping_Flow`<br>• Cấu hình ZAP Fuzzer tham số `search`<br>• Minh chứng XSS nổ popup trên Chrome<br>• Kịch bản Video Clip Demo 1 | • Nhóm làm slide & video tổng hợp |  **Hoàn thành 100%** |
| **H3** | Dựng bộ lọc đầu vào (mini WAF) cho thí nghiệm AI Fuzzer | • Code `backend/waf_middleware.js`<br>• Server `backend/server_fuzzer_lab.js` (:3001)<br>• Script test đối chứng `test_waf.sh` (5/5 Pass) | • Lê Chí Hoàng Long (L2)<br>• Nguyễn Nhật Lân (A2) |  **Hoàn thành 100%** |
| **H4** | Viết báo cáo thực nghiệm, tổng hợp slide & cập nhật tiến độ | • Báo cáo chuyên đề Markdown này.<br>• Dữ liệu và hình ảnh minh chứng sẵn sàng ghép vào slide chung của nhóm. | • Nhóm tổng hợp báo cáo (Phát P3b) |  **Đang bàn giao** |

---

## 2. GÓI VIỆC H1: MÔI TRƯỜNG SUT, CẤU HÌNH SCOPE & XUẤT DỮ LIỆU THẬT

### 2.1. Chốt thông số kỹ thuật môi trường (Baseline SUT)
* **Mã commit EShop chốt:** `d1df4745d03289a2fdeec6f30eb23260f404e81f` (Branch `main`).
* **Phiên bản nền tảng:** Node.js `v22.22.1`, npm `9.2.0`, OWASP ZAP `2.17.0` (chạy trên Linux/Ubuntu).
* **Kiến trúc hệ thống:** 
  * Frontend Web: React SPA chạy tại `http://localhost:5173`.
  * Frontend Admin: React SPA chạy tại `http://localhost:5174`.
  * Backend API: Node.js / Express REST API chạy tại `http://localhost:3000`.
  * Database: SQLite (`backend/database.sqlite`).
* **Quy trình Reset dữ liệu mẫu (Seed Data):**
  ```bash
  cd backend && node database.js
  ```
  *(Khởi tạo lại toàn bộ bảng: `users`, `products`, `orders`, `coupons` về trạng thái chuẩn trước mỗi lần test).*

### 2.2. Giải quyết 2 "Bẫy" kỹ thuật trọng yếu trong cấu hình ZAP
1. **Bẫy khác Origin (`:5173` vs `:3000`):**
   * *Vấn đề:* Single Page App chạy cổng 5173 nhưng gọi API sang cổng 3000. Nếu ZAP chỉ để scope là `localhost:5173`, mọi request gọi sang 3000 sẽ bị ZAP coi là ngoài phạm vi (Out-of-Scope) và bỏ qua.
   * *Giải pháp:* Cấu hình Context `EShop` với biểu thức Regex: `http://localhost:.*` để bao quát toàn bộ các cổng nội bộ.
2. **Bẫy cơ chế xác thực Bearer JWT:**
   * *Vấn đề:* EShop không dùng session cookie truyền thống mà lưu JWT trong `localStorage` và gửi qua header `Authorization: Bearer <token>`. Scanner mặc định không tự động gắn token vào các request quét.
   * *Giải pháp:* Sử dụng công cụ **ZAP Replacer** (`Tools ➔ Replacer`):
     * *Match Type:* `Request Header (add if not present)`
     * *Match String:* `Authorization`
     * *Replacement String:* `Bearer <token_jwt>`
     * *Target URL Regex:* `http://localhost:3000/.*`
     $\rightarrow$ Đảm bảo 100% request quét của Active Scan tự động có quyền truy cập hợp lệ, không bị lỗi `401 Unauthorized`.

### 2.3. Các sản phẩm bàn giao từ H1
1. **`zap-alerts-eshop.json`:** Báo cáo quét tự động định dạng JSON chứa các alert thật từ EShop (Reflected XSS, SQLi, Missing CSP, X-Content-Type-Options...). Bàn giao cho **Như (N2)** và **Phát (P2)** làm nhãn chuẩn Ground Truth, và cho **Lân (A1)** nạp vào AI Triage.
2. **`search_request.txt`:** File gói tin HTTP thô chứa tham số tìm kiếm sản phẩm. Bàn giao cho **Long (L1)** để chạy `sqlmap -r search_request.txt --batch`.
3. **`reset_password.req`:** File gói tin HTTP thô của chức năng Quên mật khẩu / Reset password (`POST /api/reset-password`). Bàn giao phục vụ kiểm thử brute-force OTP và kiểm tra lỗ hổng logic xác thực (SEC-07).

---

## 3. GÓI VIỆC H2: THỰC NGHIỆM 3 KỊCH BẢN & 3 THÀNH PHẦN KIỂM THỬ CỐT LÕI ZAP

### 3.1. Ba kịch bản Demo hoàn chỉnh
* **Kịch bản 1 — Cài đặt & Cấu hình:**
  * Khởi chạy ZAP 2.17.0 trên Linux.
  * Tích hợp tự động với Google Chrome qua chế độ **Manual Explore** (tự động gắn cờ `--proxy-server=127.0.0.1:8080`).
  * Giải thích cơ sở kỹ thuật: Bỏ qua bước cài SSL CA Certificate vì SUT chạy nội bộ trên giao thức HTTP.
* **Kịch bản 2 — Chức năng cơ bản (Đối chứng 2 loại Spider):**
  * *Traditional Spider:* Chỉ tìm được 1–2 URL do không thể đọc hiểu mã JavaScript của React SPA.
  * *AJAX Spider:* Sử dụng Chrome Headless render DOM, tự động click liên kết và thu thập trọn vẹn toàn bộ route của React và các endpoint API `:3000`.
  * *Passive Scan:* Tự động gắn cờ các cảnh báo về bảo mật header ngay trong quá trình lướt web.
  * *Active Scan đơn lẻ:* Thử nghiệm quét trên endpoint `GET /api/products?search=`.
* **Kịch bản 3 — Luồng EShop có xác thực (Authenticated Flow):**
  * Duyệt trọn vẹn luồng khách hàng: Đăng nhập ➔ Tìm kiếm sản phẩm ➔ Thêm giỏ hàng (`/api/cart`) ➔ Áp mã giảm giá `SAVE10` (`/api/apply-coupon`) ➔ Thanh toán (`/api/checkout`) ➔ Xem lịch sử đơn hàng (`/api/orders`).
  * Thực hiện Active Scan trên toàn bộ luồng nghiệp vụ đã được gắn token JWT qua Replacer.

---

### 3.2. Ba thành phần kiểm thử cốt lõi (Bắt buộc theo quy chế chấm điểm)

```
┌────────────────────────────────────────────────────────────────────────┐
│                   3 THÀNH PHẦN BẮT BUỘC TRONG ZAP                      │
├────────────────────┬────────────────────┬──────────────────────────────┤
│ 1. RECORD &        │ 2. DATA-DRIVEN     │ 3. CHECKPOINTS &             │
│    PLAYBACK        │    TESTING         │    BROWSER VERIFICATION      │
│ (Zest Script Macro)│ (ZAP Fuzzer)       │ (Scan Rules + DOM Execution) │
└────────────────────┴────────────────────┴──────────────────────────────┘
```

#### 1️⃣ Record & Playback (Zest Script)
* **Ý nghĩa:** Giải quyết bài toán **Kiểm thử hồi quy bảo mật (Security Regression Testing)**. Khi mã nguồn thay đổi, tester không cần bấm lại từng bước bằng tay mà chỉ cần chạy lại kịch bản tự động.
* **Thực nghiệm:** 
  * Sử dụng tính năng **Zest Script** (Type: `Stand Alone`, Prefix: `http://localhost:5173`), đặt tên `EShop_Shopping_Flow`.
  * Ghi lại chuỗi hành động: Tìm kiếm `phone` ➔ Click xem chi tiết `iPhone 15 Pro Max` ➔ Bấm "Thêm vào giỏ hàng".
  * **Playback:** Bấm nút **Run** (Play), ZAP tự động gửi lại tuần tự toàn bộ HTTP requests và xác nhận kết quả `PASSED (HTTP 200 OK)` trong tab Zest Results.

#### 2️⃣ Data-driven Testing (ZAP Fuzzer)
* **Ý nghĩa:** Kiểm thử tự động hóa bằng cách nạp danh sách dữ liệu đầu vào (Wordlist) kết hợp giữa kiểm thử chức năng và kiểm thử bảo mật.
* **Thực nghiệm:**
  * Chọn request `GET /api/products?search=phone` trong tab History ➔ Attack ➔ **Fuzz...**
  * Bôi đen giá trị tham số `search` và nạp danh sách 5 payload:
    1. `phone` *(Dữ liệu hợp lệ)*
    2. `laptop` *(Dữ liệu hợp lệ)*
    3. `' OR '1'='1` *(Payload SQL Injection)*
    4. `<script>alert(1)</script>` *(Payload XSS cơ bản)*
    5. `<img src=x onerror=alert('ZAP_Fuzz')>` *(Payload XSS qua Event Handler)*
  * **Phân tích kết quả:** ZAP tự động sinh bảng đối chứng. Tester nhận diện lỗ hổng dựa trên sự bất thường của cột **HTTP Status Code** (200 vs 500 Database Error) và **Size Resp. Body** (kích thước dữ liệu phản hồi thay đổi đột biến khi câu truy vấn SQL bị thay đổi logic).

#### 3️⃣ Checkpoints & Xác minh trực tiếp trên Trình duyệt (Proof of Concept)
* **Ý nghĩa:** Giải quyết triệt để bài toán **Cảnh báo giả (False Positive)** mà đề cương yêu cầu: *"Với XSS, xác minh thêm trên trình duyệt thay vì chỉ đọc response hoặc dựa vào tên alert"*.
* **Thực nghiệm:**
  * *Checkpoint tự động:* ZAP Active Scan gắn cờ cảnh báo `Cross Site Scripting (Reflected)` ở mức High Risk trên tham số `search`.
  * *Checkpoint kiểm chứng thực tế:* Mở Chrome, truy cập `http://localhost:5173` và nhập trực tiếp payload:
    ```html
    <img src=x onerror=alert('Reflected_XSS_Chrome_Success')>
    ```
  * *Kết quả:* Hộp thoại **alert: Reflected_XSS_Chrome_Success** lập tức kích hoạt trực tiếp trên màn hình trình duyệt!
  * *Nguyên nhân kỹ thuật:* Mã nguồn React component `Home.jsx` (dòng 64) sử dụng:
    ```jsx
    <span dangerouslySetInnerHTML={{ __html: search }} />
    ```
    Dữ liệu người dùng đưa vào không được làm sạch (sanitize) hay mã hóa đầu ra (output encoding), khiến trình duyệt thực thi trực tiếp mã JavaScript độc hại trên DOM.

---

## 4. GÓI VIỆC H3: XÂY DỰNG BỘ LỌC ĐẦU VÀO (WAF) CHO THÍ NGHIỆM AI FUZZER

### 4.1. Mục đích thiết kế & Nguyên tắc an toàn
* **Mục đích:** Cung cấp môi trường thử nghiệm cho **Lê Chí Hoàng Long (L2 - Lập trình AI Fuzzer Feedback Loop)** và **Nguyễn Nhật Lân (A2 - Benchmark Fuzzer 3 nhánh)**. Khi fuzzer tĩnh gửi payload sẽ bị WAF chặn mã 403, từ đó kích hoạt vòng lặp AI tự phân tích phản hồi và tự sinh payload né bộ lọc.
* **Nguyên tắc cô lập:** Toàn bộ bộ lọc được dựng trên bản lab riêng, **giữ nguyên 100% mã nguồn `server.js` gốc** của EShop để không ảnh hưởng đến các bài test khác của nhóm.

### 4.2. Cấu trúc các thành phần đã triển khai
1. [backend/waf_middleware.js](file:///home/hung/26-27/Kiem_thu/seminar/eshop-sut/backend/waf_middleware.js):
   * **Level 1 (Cơ bản):** Chặn từ khóa dựa trên khoảng trắng: `/(^|\s+)(OR|AND|UNION|SELECT)(\s+|$)/i` và `<script\b|javascript:`. Dễ bị bypass bằng kỹ thuật inline comment `/**/`.
   * **Level 2 (Strict):** Chặn triệt để cả comment (`/*`, `*/`, `--`), dấu chấm phẩy và toàn bộ event handler HTML.
   * **JSON phản hồi cho AI:** Khi bị chặn, trả về mã **HTTP 403 Forbidden** kèm JSON:
     ```json
     {
       "status": "BLOCKED",
       "error": "WAF_INPUT_BLOCKED",
       "message": "Request bị chặn bởi bộ lọc bảo mật: phát hiện từ khóa nguy hiểm ' OR '",
       "blocked_keyword": " OR ",
       "waf_level": 1
     }
     ```
2. [backend/server_fuzzer_lab.js](file:///home/hung/26-27/Kiem_thu/seminar/eshop-sut/backend/server_fuzzer_lab.js):
   * Chạy độc lập trên cổng **`3001`**.
   * Cung cấp các API quản trị trạng thái phục vụ kịch bản benchmark tự động:
     * `GET  /api/waf/status`: Kiểm tra trạng thái và level hiện tại của WAF.
     * `POST /api/waf/toggle`: Bật/tắt hoặc nâng hạ level của WAF.
     * `POST /api/waf/reset`: Khôi phục trạng thái bật mặc định (Level 1).
3. [backend/test_waf.sh](file:///home/hung/26-27/Kiem_thu/seminar/eshop-sut/backend/test_waf.sh):
   * Script kiểm thử đối chứng tự động (Sanity Check).

### 4.3. Bảng kết quả kiểm thử đối chứng thực tế (5/5 PASS)

| Test Case | Kịch bản kiểm thử | Input thực tế | Kỳ vọng | Kết quả thực tế | Đánh giá |
|:---:|---|---|:---:|:---:|:---:|
| **Test 1** | Người dùng bình thường tìm kiếm sản phẩm | `search=phone` | HTTP 200 | **HTTP 200 OK** |  Không chặn nhầm luồng hợp lệ |
| **Test 2** | Tấn công SQLi cơ bản | `search=' OR 1=1 --` | HTTP 403 | **HTTP 403 Forbidden** |  WAF phát hiện và chặn đúng ' OR ' |
| **Test 3** | Tấn công XSS cơ bản | `search=<script>alert(1)</script>` | HTTP 403 | **HTTP 403 Forbidden** |  WAF phát hiện và chặn thẻ script |
| **Test 4** | Thử nghiệm AI Bypass (Inline comment) | `search='/**/OR/**/1=1--` | HTTP 200 | **HTTP 200 OK** |  Payload né lọc thành công ở Level 1 |
| **Test 5** | Kiểm tra API Toggle (Tắt WAF) | `search=' OR 1=1 --` (WAF Off) | HTTP 200 | **HTTP 200 OK** |  Hạ tầng lab bật/tắt linh hoạt phục vụ đo benchmark |

---

## 5. ĐÁNH GIÁ CHUYÊN SÂU: ĐIỂM MẠNH, HẠN CHẾ CỦA ZAP & SỰ LIÊN KẾT CÔNG CỤ

### 5.1. Điểm mạnh vượt trội của OWASP ZAP trên case study EShop
* **Tự động hóa toàn diện:** Khả năng càn quét diện rộng cực tốt từ Crawling $\rightarrow$ Passive Scan $\rightarrow$ Active Scan $\rightarrow$ Xuất báo cáo tự động.
* **AJAX Spider mạnh mẽ:** Sử dụng trình duyệt headless điều khiển thực sự, giải quyết triệt để bài toán Single Page App mà các công cụ scanner truyền thống (như Nikto hay Spider thường) hoàn toàn bó tay.
* **Khả năng can thiệp linh hoạt:** Công cụ **Replacer** cho phép thao túng header theo thời gian thực, khắc phục nhược điểm không tự xử lý Bearer JWT.

### 5.2. Điểm yếu & Hạn chế thực tế
* **Tốc độ:** AJAX Spider tốn nhiều tài nguyên RAM/CPU và quét chậm hơn đáng kể so với Traditional Spider do phải khởi tạo trình duyệt và chờ JavaScript render.
* **Điểm mù về Logic phân quyền (Broken Access Control - SEC-03, SEC-06):** Active Scan mặc định của ZAP không thể tự hiểu ngữ cảnh "User thường không được phép sửa đơn hàng của người khác (IDOR)" hay "User thường không được gọi API Admin". 
* **Tỷ lệ cảnh báo giả (False Positive):** Dễ phát sinh cảnh báo nghi ngờ trên các ứng dụng dùng CSDL nhẹ như SQLite nếu backend phản hồi các thông báo lỗi thô.

### 5.3. Mối liên kết chiến lược trong Bộ 3 công cụ của Nhóm
Chính những hạn chế trên của ZAP đã tạo tiền đề logic hoàn hảo để kết nối với 2 công cụ tiếp theo:
1. `[ZAP quét diện rộng]` $\rightarrow$ Bàn giao các request nghi ngờ cho **Burp Suite (Thạch Như)** can thiệp gói tin thủ công và khai thác sâu lỗ hổng logic phân quyền IDOR.
2. `[ZAP gắn cờ nghi ngờ SQLi]` $\rightarrow$ Bàn giao `search_request.txt` cho **sqlmap (Hoàng Long)** để tự động hóa nạp hàng ngàn payload kiểm chứng và trích xuất dữ liệu CSDL SQLite.