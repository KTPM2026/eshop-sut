# KỊCH BẢN DEMO CHI TIẾT: OWASP ZAP — BURP SUITE — SQLMAP
## Case study: EShop (ttbhanh/eshop-sut)

---

## 0. Thông tin chung về case study

Repo [eshop-sut](https://github.com/ttbhanh/eshop-sut) là ứng dụng được xây dựng riêng cho môn Kiểm thử phần mềm, và quan trọng nhất: tài liệu `setup_guide.md` của repo xác nhận rõ **"Hệ thống này CỐ Ý được thiết kế chứa nhiều lỗi liên quan đến: SQL Injection, XSS, Phân quyền, Lỗi Logic nghiệp vụ"**. Điều này rất thuận lợi cho seminar vì nhóm không cần giả định mơ hồ — nhiệm vụ của 3 kịch bản dưới đây là **dùng công cụ để xác minh hệ thống thực tế có tuân thủ đúng đặc tả `README.md` hay không**, đúng tinh thần mà tài liệu môn học đề ra.

### 0.1 Thông tin hệ thống

| Thành phần | URL | Ghi chú |
|---|---|---|
| Backend API | `http://localhost:3000` | Node.js + Express + SQLite |
| Frontend Web | `http://localhost:5173` | React SPA — quan trọng khi cấu hình crawl (xem mục 1.3) |
| Web Admin | `http://localhost:5174` | React SPA riêng cho Admin |

**Tài khoản demo:**
- User thường: `test@eshop.com` / `Test1234!`
- Admin: `admin@eshop.com` / `Admin123!` *(lưu ý: `setup_guide.md` lại ghi mật khẩu admin là `admin123` — hai tài liệu trong repo không khớp nhau; nhóm nên thử cả hai khi setup thật. Đây cũng là một ví dụ nhỏ hay để đưa vào seminar: đối chiếu tài liệu với hệ thống thật đôi khi tự nó đã lộ ra sự thiếu nhất quán.)*

Khởi động theo đúng `setup_guide.md`: `node database.js` (seed data) → `node server.js` (backend) → `npm run dev` ở `frontend-web` và/hoặc `frontend-admin`.

### 0.2 Bảng ánh xạ: yêu cầu bảo mật (SEC) → công cụ kiểm tra

Đây là bảng nên đưa vào slide seminar — cho thấy nhóm không chọn công cụ ngẫu nhiên mà có chiến lược phủ đủ các yêu cầu đặc tả:

| Mã | Yêu cầu bảo mật (theo README) | Công cụ chính | Công cụ phụ trợ |
|---|---|---|---|
| SEC-01 | Mật khẩu không lưu plaintext | sqlmap (dump bảng `users` để quan sát) | — |
| SEC-02 | API nhạy cảm yêu cầu JWT hợp lệ | Burp (Repeater: bỏ token) | ZAP (Active Scan) |
| SEC-03 | API Admin phải kiểm tra `role=admin` trong token | **Burp Suite** (Repeater, đổi token) | ZAP (Access Control) |
| SEC-04 | Input hiển thị lên UI phải escape (chống XSS) | **ZAP** (Active Scan + Fuzzer) | Burp (Repeater xác nhận) |
| SEC-05 | Truy vấn CSDL dùng Parameterized Query (chống SQLi) | **sqlmap** | ZAP (Active Scan rule SQLi) |
| SEC-06 | API cập nhật hồ sơ không cho đổi `role` từ client | **Burp Suite** (Repeater, chèn field `role`) | — |
| SEC-07 | OTP đủ entropy, có hạn dùng, vô hiệu sau khi dùng | **Burp Suite** (Intruder brute-force) | — |

### 0.3 Lưu ý đạo đức & phạm vi

Toàn bộ demo **chỉ thực hiện trên `localhost`**, trong môi trường do nhóm tự dựng theo `setup_guide.md`. Không áp dụng kỹ thuật/payload trong tài liệu này lên bất kỳ hệ thống nào khác không thuộc quyền sở hữu hoặc chưa được phép kiểm thử.

---

# 1. KỊCH BẢN 1 — OWASP ZAP

## 1.1 Mục tiêu & phạm vi áp dụng

ZAP đóng vai trò công cụ quét diện rộng (broad coverage): crawl toàn bộ site, tự động dò nhiều lớp lỗ hổng cùng lúc (XSS, SQLi, security header, info disclosure...). Trong case study eshop-sut, ZAP phụ trách chính: **SEC-04 (XSS)**, **SEC-05 (SQLi — chéo kiểm với sqlmap)**, và rà soát tổng thể.

## 1.2 Demo cài đặt

1. Tải ZAP từ trang chính thức zaproxy.org (bản Desktop, có kèm JRE riêng, không cần cài Java thủ công).
2. Cài đặt theo OS (Windows installer / `.dmg` macOS / gói Linux).
3. Lần đầu mở: chọn chế độ "I do not want to persist this session" khi demo nhanh, hoặc persist nếu muốn giữ lại lịch sử làm minh chứng nộp bài.
4. Giới thiệu nhanh giao diện: cây **Sites**, tab **History/Alerts**, **Quick Start**, thanh công cụ Spider/Active Scan.
5. Khởi động backend + frontend-web của eshop-sut theo `setup_guide.md`.
6. Kiểm tra kết nối: dùng **Manual Explore** (nút trên tab Quick Start) để ZAP tự mở trình duyệt đã cấu hình sẵn proxy, truy cập `http://localhost:5173` → xác nhận request xuất hiện trong cây Sites.

*(App chạy HTTP nội bộ nên bỏ qua bước cài chứng chỉ CA — nhóm nên nêu rõ bước này trong slide là "bỏ qua vì môi trường demo dùng HTTP", để thể hiện hiểu biết đầy đủ chứ không phải thiếu sót.)*

## 1.3 Demo chức năng cơ bản

**Lưu ý cấu hình trước khi crawl:** Frontend (`:5173`) và Backend (`:3000`) là 2 *origin* khác nhau (cùng host, khác cổng). Nếu Context chỉ chứa `http://localhost:5173`, ZAP sẽ coi mọi request gọi sang `:3000` là out-of-scope và Spider/AJAX Spider có thể bỏ sót, không crawl/test các API đó. Trước khi chạy Spider, vào Context → Include in Context → thêm Regex `http://localhost:.*` để bao hàm cả 2 cổng.

1. **Spider thông thường** trên `http://localhost:5173` — chạy xong, so sánh số URL tìm được với số trang thực tế của app. Vì frontend là React SPA (điều hướng bằng JavaScript phía client), Spider truyền thống sẽ **tìm được rất ít** — đây là điểm cần nhấn mạnh ngay trong demo cơ bản, không đợi đến phần điểm yếu.
2. **AJAX Spider** (dùng trình duyệt headless, thực thi JS) chạy lại cùng target với scope đã mở rộng ở trên — so sánh kết quả: số trang/route tìm được tăng rõ rệt (Trang chủ, Chi tiết sản phẩm, Giỏ hàng...), và giờ các request gọi sang `:3000` cũng được ghi nhận thay vì bị bỏ qua.
3. **Passive Scan** — vì chạy tự động nền khi duyệt, chỉ cần mở tab **Alerts** sau bước 1-2, chỉ ra các cảnh báo passive điển hình (thiếu header `Content-Security-Policy`, `X-Content-Type-Options`...).
4. **Active Scan trên 1 node đơn lẻ**: click phải vào `GET /api/products?search=` trong Sites → Attack → Active Scan — minh hoạ việc quét 1 điểm cụ thể trước khi quét toàn site.

## 1.4 Demo luồng xử lý phức tạp (case study xuyên suốt)

**Bước 1 — Thiết lập xác thực cho Context (đây là phần kỹ thuật khó nhất, nên làm kỹ):**

eshop-sut dùng JWT qua header `Authorization: Bearer <token>`, không dùng cookie session, nên ZAP không tự quản lý phiên như web truyền thống. Hai cách cấu hình, nên trình bày cả hai để thể hiện chiều sâu:

- **Cách nhanh (đủ cho demo):** Tools → Replacer → thêm rule: nếu request tới `localhost:3000`, thêm header `Authorization: Bearer <token lấy thủ công từ lần đăng nhập đầu>`. Hạn chế: token tĩnh, không tự làm mới.
- **Cách chuẩn hơn (tự động hoá thật sự):** Trong Context → Authentication, chọn **JSON-based Authentication**, trỏ tới `POST /api/login` với Login Request Data `{"email":"{%username%}","password":"{%password%}"}`. Lưu ý: Session Management mặc định của ZAP (**HTTP Authentication Session Management**) chỉ xử lý cơ chế HTTP Basic/Digest Auth chuẩn — **không** nhận diện được Bearer JWT trong header `Authorization`. Để ZAP tự động gắn JWT vào mọi request, bắt buộc phải cài thêm add-on **Authentication Helper** (miễn phí, từ ZAP Marketplace) và chọn **Header Based Session Management**, khai báo `Authorization: Bearer {%json:token%}` — ZAP sẽ tự trích token từ response JSON của `/api/login` và gắn vào mọi request sau đó, kể cả khi re-run scan nhiều lần. (Không cài add-on này thì lựa chọn còn lại là tự viết Script-Based Session Management.)

**Bước 2 — Crawl có xác thực:** chạy lại AJAX Spider với Context vừa cấu hình → giờ ZAP crawl được cả vùng cần đăng nhập (Giỏ hàng, Thanh toán, Lịch sử đơn hàng).

**Bước 3 — Case study đầy đủ (mô phỏng luồng mua hàng thật):** dùng Manual Explore thao tác tuần tự: Đăng ký → Đăng nhập → Tìm kiếm sản phẩm → Thêm giỏ hàng → Áp mã giảm giá (`SAVE10`) → Checkout → Xem lịch sử đơn hàng. Toàn bộ traffic này được ghi lại trong History (xem mục 1.5).

**Bước 4 — Active Scan toàn bộ Context đã xác thực** → chạy quét, đợi hoàn tất.

**Bước 5 — Đối chiếu Alerts với đặc tả SEC:** mở tab Alerts, lọc theo Risk (High/Medium/Low), với mỗi alert liên quan XSS/SQLi, đối chiếu ngay với SEC-04/SEC-05 trong README, ghi chú endpoint + payload làm bằng chứng.

**Bước 6 — Export report** (HTML/JSON) — file JSON này chính là input cho phần **AI Vulnerability Triage** đã thiết kế ở tài liệu AI trước đó, tạo sự liên kết xuyên suốt giữa các phần của seminar.

## 1.5 Record & Playback trong ZAP

- **Record**: toàn bộ thao tác ở Bước 3 (mục 1.4) được ghi lại tự động trong tab **History** khi đi qua proxy ZAP — đây là "ghi" theo nghĩa rộng. Để có bản ghi tường minh kiểu macro, dùng tab **Scripts** → **Record a new Zest Script**, thực hiện lại luồng mua hàng — ZAP sinh ra 1 script Zest chứa từng bước request.
- **Playback**: chạy lại script Zest vừa ghi (nút Run trong Scripts tab) — toàn bộ luồng mua hàng được "diễn lại" tự động, hữu ích để làm **regression test bảo mật** (chạy lại sau mỗi lần code thay đổi, không cần thao tác tay lại từ đầu). Đây là tính năng khớp chính xác với thuật ngữ "Record and Playback" mà đề bài yêu cầu.

## 1.6 Data-driven trong ZAP

- **Fuzzer**: chọn tham số `search` trong `GET /api/products?search=` (hoặc field `code` trong body của `POST /api/apply-coupon`) → right-click → Fuzz → nạp Payloads (dùng sẵn file payload SQLi/XSS tích hợp của ZAP, hoặc file `.txt` tự chuẩn bị) → Start.
- **Ứng dụng cụ thể vào case study**: fuzz field `code` của `apply-coupon` với danh sách `["SAVE10","BIGBUY","VIP100","EXPIRED","INVALIDCODE","' OR '1'='1","<script>alert(1)</script>"]` — kết hợp test chức năng (đúng/sai mã) **và** test bảo mật (payload injection) trong cùng 1 lần chạy data-driven, bám sát đúng bảng 5 điều kiện coupon (C1-C5) trong đặc tả FR-09.
- Xem bảng kết quả Fuzzer: cột Code, Reason, Size Resp Body — tìm response bất thường (size khác biệt, status code 500 thay vì 400).

## 1.7 Checkpoints trong ZAP

- **Mặc định**: mỗi Active/Passive Scan Rule chính là 1 checkpoint tự động — so khớp response với pattern lỗi đã biết, gắn Risk Level (High/Medium/Low/Informational).
- **Checkpoint tuỳ chỉnh cho business logic**: viết 1 Active Scan Script đơn giản (tab Scripts → Active Rules) kiểm tra riêng cho eshop-sut, ví dụ: "nếu response của `POST /api/checkout` chấp nhận `total_amount` khác với tổng tiền thực tính từ giỏ hàng, đánh dấu Medium" — đây chính là cách kiểm chứng tự động cho yêu cầu FR-08 ("Backend phải tự tính lại tổng tiền; không chấp nhận `total_amount` do client gửi lên"), một checkpoint vượt ra ngoài các rule có sẵn, thể hiện công sức tìm hiểu sâu.

## 1.8 Điểm yếu của ZAP trên case study này

- Spider thường gần như vô dụng với React SPA — bắt buộc phải dùng AJAX Spider (chậm hơn, cần trình duyệt headless).
- Không tự quản lý JWT trong header như cookie — phải cấu hình Session Management thủ công, không "cắm là chạy" ngay.
- Active Scan mặc định **không** tự phát hiện lỗi phân quyền kiểu "role check" (SEC-03, SEC-06) vì ZAP không có khái niệm "user A không được phép gọi API admin" — cần add-on Access Control Testing hoặc kết hợp thủ công với Burp (mục 2).
- Dễ phát sinh false positive trên app nhỏ dùng SQLite, cần người kiểm chứng lại (đã thiết kế quy trình xử lý ở phần AI Triage).

## 1.9 Mức độ tự động hoá

Spider/Active Scan/Fuzzer: **fully automated** sau khi Context + Authentication đã cấu hình xong (bước cấu hình ban đầu là semi-automated/thủ công một lần).

---

# 2. KỊCH BẢN 2 — BURP SUITE COMMUNITY EDITION

## 2.1 Mục tiêu & phạm vi áp dụng

**Lưu ý quan trọng cần nói rõ ngay từ đầu phần này**: bản Community **không có Active Scanner tự động** (chỉ có ở bản Pro trả phí). Do đó Burp trong seminar không đóng vai trò "quét diện rộng" như ZAP, mà đóng vai trò **công cụ kiểm thử thủ công có chủ đích, chính xác cao** — rất phù hợp để khai thác đúng 2 lớp lỗ hổng cần tư duy logic: **SEC-03 (phân quyền)**, **SEC-06 (đổi role qua client)**, và **SEC-07 (OTP brute-force)**.

## 2.2 Demo cài đặt

1. Tải Burp Suite Community từ PortSwigger, cài đặt (Java được đóng gói sẵn).
2. Mở ứng dụng, chọn **Temporary project** (bản Free không lưu project lại được — cần export thủ công nếu muốn giữ minh chứng).
3. Vào tab Proxy → Options, xác nhận listener mặc định `127.0.0.1:8080`.
4. Dùng trình duyệt tích hợp sẵn của Burp: Proxy → Intercept → **Open Browser** — cách đơn giản nhất cho sinh viên, không cần cấu hình proxy hệ điều hành thủ công.
5. (Kiến thức đầy đủ, dù không bắt buộc với case study HTTP nội bộ) nêu bước cài chứng chỉ CA của Burp vào trình duyệt nếu test HTTPS.
6. Kiểm tra: mở `localhost:5173` qua trình duyệt Burp, xác nhận traffic hiện ở **Proxy → HTTP History**.

## 2.3 Demo chức năng cơ bản

1. **Intercept**: bật Intercept is on, thực hiện đăng nhập trên trình duyệt Burp — request bị giữ lại, cho xem/sửa nội dung trước khi bấm Forward — minh hoạ khái niệm chặn & chỉnh sửa request.
2. **HTTP History**: duyệt lại toàn bộ request đã ghi, lọc theo `/api/` để chỉ xem traffic backend.
3. **Repeater**: gửi `GET /api/products/1` sang Repeater, đổi `id` thành `2`, `9999`, gửi lại, so sánh response.
4. **Decoder**: lấy chuỗi JWT token từ response đăng nhập, decode phần payload (Base64) trong Decoder để sinh viên thấy rõ cấu trúc bên trong token (trường `role`, `exp`...) — kiến thức nền cho phần 2.4.

## 2.4 Demo luồng xử lý phức tạp (case study)

### Luồng A — Broken Access Control (SEC-03, SEC-06)

1. Đăng nhập bằng `test@eshop.com` (user thường), bắt token qua Proxy.
2. Gửi 1 request bất kỳ sang **Repeater**, sửa thành `GET /api/admin/users`, giữ nguyên token user thường ở header `Authorization` → Send.
3. Quan sát: nếu response trả **200 + dữ liệu người dùng** thay vì 401/403 → bằng chứng vi phạm SEC-03 ("API Admin phải kiểm tra `role=admin` trong Token, không chỉ kiểm tra sự tồn tại của Token").
4. Thử tiếp `PUT /api/users/me` với body gốc theo spec (`name`, `shipping_address`, `phone`) nhưng chèn thêm field không có trong tài liệu: `"role": "admin"` → gửi → đăng nhập lại, decode token mới xem `role` có đổi thật không → kiểm tra SEC-06.
5. Đây là kỹ thuật "thao túng tham số rồi Repeater" — bán tự động đúng nghĩa: con người quyết định bước tiếp theo dựa trên response, Burp chỉ lo gửi/nhận chính xác.

### Luồng B — OTP Brute-force (SEC-07, đối chiếu FR-02)

FR-02 quy định: đăng nhập sai ≥3 lần sẽ khoá tài khoản 30 giây. Nhưng đặc tả **không nói rõ** `POST /api/reset-password` (OTP 6 chữ số) có áp dụng cơ chế giới hạn tương tự hay không — đây chính là "khoảng trống" đáng kiểm thử.

1. Gọi `POST /api/forgot-password` với email `test@eshop.com` để sinh OTP.
2. Gửi request `POST /api/reset-password` sang **Intruder**, đánh dấu vị trí payload ở trường `resetToken`.
3. Payload type: **Numbers**, range rút gọn để demo trong thời lượng seminar (ví dụ `000000`–`001000`).
4. Chạy Attack, quan sát cột **Status/Length** — request nào khác biệt (đổi mật khẩu thành công) sẽ nổi bật trong bảng kết quả.
5. Kết luận: nếu không có cơ chế khoá sau nhiều lần sai (không có status 429/khoá tạm thời xuất hiện) **và** OTP có thể bị dò trúng trong đúng khoảng thời gian hiệu lực thực tế của nó, đây là bằng chứng SEC-07 chưa được tuân thủ đầy đủ.

**Rủi ro cần xử lý trước khi demo trực tiếp**: Intruder bản Community bị giới hạn tốc độ khá nặng (ước tính khoảng 10-15 phút cho 1.000 request). Nếu OTP có hạn dùng ngắn (vài phút, đúng tinh thần SEC-07 "có hạn dùng"), dò hết dù chỉ 1.000 giá trị cũng có thể không kịp trước khi OTP hết hạn — demo sẽ "trông như thất bại" dù cách làm đúng. Hai cách xử lý, chọn 1 theo khả năng truy cập mã nguồn backend của nhóm:
- **Rút ngắn OTP tạm thời cho mục đích demo**: nếu nhóm có quyền sửa backend cục bộ, tạm đổi độ dài OTP sinh ra từ 6 xuống 2 chữ số (`00`–`99`, chỉ 100 khả năng) → Intruder dò hết trong vài chục giây dù vẫn bị throttle.
- **Kéo dài thời hạn OTP cho mục đích demo**: muốn giữ nguyên 6 chữ số cho sát thực tế, tạm tăng thời gian hết hạn OTP trong backend (ví dụ lên 30-60 phút) chỉ trong lúc demo.

Cả hai đều là thay đổi **tạm thời, chỉ phục vụ trình diễn** — cần nói rõ trong slide đây không phải cấu hình thật của hệ thống, và kết luận "có lỗ hổng SEC-07" trong báo cáo cuối cùng nên dựa trên cấu hình OTP gốc (6 chữ số, hạn dùng thật), không dựa trên bản đã chỉnh để demo.

## 2.5 Record & Playback trong Burp

- **Record**: toàn bộ Luồng A/B ở trên được ghi tự động vào **Proxy → HTTP History**.
- **Playback**: "Send to Repeater" từng request đã ghi, chỉnh sửa và gửi lại có kiểm soát từng request một. Khác biệt quan trọng cần nêu khi so sánh với ZAP: Burp Community **không có macro tự động phát lại cả 1 phiên nhiều bước** (như Zest Script của ZAP) — playback trong Burp Community mang tính "từng request, có chủ đích" hơn là "tự động diễn lại nguyên luồng".

## 2.6 Data-driven trong Burp

**Intruder** là engine data-driven cốt lõi, với 4 kiểu tấn công:

| Kiểu tấn công | Ứng dụng trong case study |
|---|---|
| **Sniper** | OTP brute-force (Luồng B) — 1 vị trí, nhiều payload. Cũng dùng để test IDOR trên `GET /api/orders/:id`: **giữ cố định** token của 1 user (để trong header tĩnh, không đánh dấu làm payload), chỉ đổi `:id` trong URL qua 1 dải số thứ tự — nếu user này xem được đơn hàng của người khác, đó là IDOR |
| **Cluster bomb** | Test coupon đa chiều: vị trí 1 = mã (`SAVE10`,`BIGBUY`,`VIP100`,`EXPIRED`,`INVALID`), vị trí 2 = `total_amount` (0, số âm, số cực lớn) — kết hợp test functional (đúng 5 điều kiện C1-C5 của FR-09) và test input validation/bảo mật cùng lúc |
| **Pitchfork** | Test kiểu credential-stuffing trên `POST /api/login`: 2 danh sách ghép theo đúng chỉ số (không thử chéo như Cluster bomb) — vị trí 1 = danh sách email, vị trí 2 = danh sách mật khẩu tương ứng từng email — mô phỏng tấn công dùng danh sách tài khoản rò rỉ, đồng thời kiểm tra cơ chế khoá tài khoản (FR-02) có kích hoạt đúng sau 3 lần sai hay không |

## 2.7 Checkpoints trong Burp

Vì Community không có Scanner gắn risk level tự động như ZAP, "checkpoint" trong Burp thể hiện qua:

- **Intruder → Grep - Match**: định nghĩa chuỗi cần tìm trong response (ví dụ `"role":"admin"`, hoặc đoạn thông báo lỗi khoá tài khoản) → Burp tự động đánh dấu cột Match cho từng dòng kết quả — đây là checkpoint tự động hoá cho toàn bộ lượt chạy data-driven.
- **Comparer**: so sánh response hợp lệ và không hợp lệ theo từng byte, làm bằng chứng rõ ràng cho báo cáo.

## 2.8 Điểm yếu của Burp Suite Community trên case study này

- Không có Active Scanner tự động → không thể "bấm 1 nút quét hết toàn site" như ZAP; mọi phát hiện phụ thuộc hoàn toàn vào thao tác và tư duy thủ công của người test.
- Intruder bản Free bị giới hạn tốc độ nghiêm trọng → không khả thi để brute-force không gian lớn trong thời gian thực tế (phải rút gọn phạm vi khi demo, như đã nêu ở Luồng B).
- Không lưu project giữa các phiên làm việc (Temporary Project) → dễ mất minh chứng nếu quên export.
- Phù hợp để đào sâu 1-2 lỗ hổng cụ thể đã nghi ngờ hơn là rà soát toàn diện — ngược lại với thế mạnh của ZAP.

## 2.9 Mức độ tự động hoá

Intercept/Repeater: **hoàn toàn thủ công**. Intruder: **bán tự động** (người định nghĩa vị trí/payload/checkpoint, Burp tự động lặp gửi request và tổng hợp kết quả).

---

# 3. KỊCH BẢN 3 — SQLMAP

## 3.1 Mục tiêu & phạm vi áp dụng

sqlmap là công cụ chuyên biệt — chỉ giải quyết đúng 1 nội dung nhưng ở mức sâu nhất: **xác minh SEC-05 (Parameterized Query)**. Các endpoint ứng viên hợp lý để thử nghiệm (có tham số do người dùng kiểm soát và rất có thể được dùng trực tiếp trong truy vấn CSDL theo `api_specification.md`):

- `GET /api/products?search=` — tham số tìm kiếm.
- `GET /api/products/:id` — tham số định danh trên URL.
- `POST /api/login` — trường `email`/`password` dùng để tra cứu user.
- `POST /api/apply-coupon` — trường `code` dùng để tra cứu mã giảm giá.

*(Đây là các điểm **cần xác minh**, không phải khẳng định chắc chắn có lỗi — nếu backend tuân thủ đúng SEC-05, sqlmap sẽ báo "không injectable", và đó cũng là một kết quả kiểm thử hợp lệ cần trình bày, xem mục 3.4.)*

## 3.2 Demo cài đặt

```bash
# Yêu cầu Python 3.x
git clone --depth 1 https://github.com/sqlmapproject/sqlmap.git
cd sqlmap
python sqlmap.py --version
```

Khởi động backend eshop-sut theo `setup_guide.md` để có target thật trước khi chạy các lệnh bên dưới.

## 3.3 Demo chức năng cơ bản

**Test tham số không cần xác thực** (`search`):

```bash
python sqlmap.py -u "http://localhost:3000/api/products?search=test" --batch
```

Giải thích output cho lớp: sqlmap tự động thử lần lượt các kỹ thuật — boolean-based blind, error-based, UNION query, time-based blind, stacked queries — và báo cáo tham số nào (nếu có) injectable, cùng DBMS được fingerprint (ở đây dự kiến là SQLite).

**Test endpoint cần JWT** (`apply-coupon`):

```bash
python sqlmap.py -u "http://localhost:3000/api/apply-coupon" \
  --data='{"code":"SAVE10","total_amount":500000,"user_id":1}' \
  --headers="Authorization: Bearer <token_lay_tu_buoc_dang_nhap>" \
  --batch
```

## 3.4 Demo luồng xử lý phức tạp (case study)

**Bước 1 — Kết hợp liên công cụ (điểm nhấn của phần này):** thay vì gõ lại tham số thủ công, dùng chính request đã bắt được từ Burp ở Kịch bản 2. Trong Burp, chọn request `GET /api/products?search=test` (từ HTTP History) → "Copy to file" (hoặc Save item) → lưu thành `search_request.txt` (nguyên văn HTTP request) → chạy:

```bash
python sqlmap.py -r search_request.txt --batch
```

Đây là cách sqlmap đọc toàn bộ raw HTTP request thay vì phải tái tạo thủ công từng tham số — thể hiện quy trình làm việc thực tế: **ghi 1 lần qua Proxy, phát lại nhiều lần với payload khác nhau qua sqlmap** (ánh xạ trực tiếp sang khái niệm Record & Playback, xem mục 3.5).

*(Chọn endpoint `search` — không phải `login` — cho bước demo chính, vì `/api/login` có cơ chế khoá tài khoản sau 3 lần sai theo FR-02; chạy sqlmap dồn dập vào đó dễ tự khoá mất tài khoản test đang dùng cho cả buổi demo, xem thêm mục 3.8. Muốn minh hoạ thêm kịch bản kinh điển "SQLi bypass đăng nhập", nên làm riêng như 1 demo phụ với tài khoản test tách biệt, không dùng chung với các demo khác.)*

**Bước 2 — Nếu phát hiện injectable, khai thác thêm (chỉ trên môi trường demo cục bộ):**

```bash
python sqlmap.py -r search_request.txt --batch --dbs
```

SQLite không có khái niệm nhiều "database" như MySQL/PostgreSQL — nó chỉ có 1 schema mặc định mà sqlmap sẽ liệt kê (thường có tên `main`, theo đúng quy ước nội bộ của SQLite). **Dùng đúng tên mà lệnh `--dbs` vừa trả về**, không gõ cứng theo thói quen MySQL như `-D eshop` (tên database đó không tồn tại trong SQLite):

```bash
python sqlmap.py -r search_request.txt --batch -D main --tables
python sqlmap.py -r search_request.txt --batch -D main -T users --columns
```

Nếu dump được cột `password`, đối chiếu ngay giá trị lấy được với **SEC-01** (mật khẩu không được lưu plaintext) — xem giá trị có dạng hash (bcrypt/argon2, bắt đầu bằng `$2b$`...) hay là chuỗi dễ đọc. Một lệnh sqlmap ở đây đồng thời kiểm tra chéo 2 yêu cầu bảo mật (SEC-05 và SEC-01) — rất đáng đưa vào slide vì thể hiện tư duy liên kết, không chỉ chạy lệnh đơn lẻ.

**Bước 3 — Trường hợp không injectable:** nếu sqlmap báo "all tested parameters do not appear to be injectable" ở mọi endpoint đã thử, **đây không phải demo thất bại**. Kết luận cần trình bày: backend eshop-sut (ở các endpoint đã kiểm) tuân thủ đúng SEC-05 bằng parameterized query. Nhóm nên chuẩn bị nội dung trình bày cho **cả hai khả năng** (có lỗi / không có lỗi) thay vì mặc định trước kết quả — đúng tinh thần kiểm thử thật.

## 3.5 Record & Playback với sqlmap

sqlmap không có GUI "ghi" theo nghĩa UFT/Selenium, nhưng ánh xạ qua 2 tính năng cụ thể:

- `-r <file>`: phát lại (playback) 1 request đã ghi từ Burp/ZAP, như đã demo ở Bước 1 mục 3.4.
- `-l <burp_log_file>`: đọc **toàn bộ** Burp Proxy log, tự động quét lần lượt mọi request đã ghi được trong đó — hình thức "playback hàng loạt", nên demo thêm nếu còn thời gian để thể hiện khả năng mở rộng quy mô.

## 3.6 Data-driven với sqlmap

Đây là bản chất lõi của công cụ: với mỗi tham số, sqlmap tự nạp một tập payload nội bộ rất lớn (nhiều kỹ thuật × nhiều DBMS) mà nhóm không cần tự chuẩn bị wordlist như ZAP Fuzzer — đây là điểm khác biệt quan trọng cần nêu khi so sánh 2 công cụ. Có thể tinh chỉnh độ phủ bằng:

```bash
python sqlmap.py -r search_request.txt --batch --technique=BEUST --level=3 --risk=2
```

Demo thay đổi `--level` (1-5) và `--risk` (1-3) để lớp thấy rõ đánh đổi giữa độ phủ payload và thời gian chạy — `--risk` cao hơn thử cả payload có khả năng ảnh hưởng dữ liệu, nên chỉ dùng trên môi trường demo cục bộ.

## 3.7 Checkpoints với sqlmap

sqlmap tự đánh giá "injectable: yes/no" cho từng tham số dựa trên so sánh response giữa payload true/false (boolean-based) hoặc độ trễ thời gian phản hồi (time-based) — đây là checkpoint **nội tại**, không cần nhóm tự định nghĩa luật như ở ZAP/Burp. Thêm cờ `--output-dir=./sqlmap-logs` để lưu log/report từng session làm minh chứng nộp bài.

## 3.8 Điểm yếu của sqlmap trên case study này

- Chỉ chuyên về SQL Injection — hoàn toàn không phát hiện XSS, broken access control hay lỗi logic nghiệp vụ (coupon, state machine đơn hàng) → bắt buộc phối hợp với ZAP/Burp mới phủ hết các SEC còn lại.
- Cần chuẩn bị token/phiên đăng nhập thủ công trước khi quét endpoint yêu cầu xác thực — không "cắm chạy" ngay với toàn bộ app.
- Cần cẩn trọng thứ tự demo: nếu chạy dồn dập trên `/api/login` (có cơ chế khoá sau 3 lần sai theo FR-02), có thể vô tình tự khoá tài khoản test trước khi kịp phân tích kết quả — nên ưu tiên test các endpoint không yêu cầu đăng nhập trước, hoặc dùng tài khoản phụ riêng cho sqlmap.
- Nếu team code tuân thủ tốt SEC-05, sqlmap sẽ không tìm ra gì — nhóm cần chuẩn bị tâm lý và nội dung cho cả kịch bản "không phát hiện lỗi" (mục 3.4, Bước 3).

## 3.9 Mức độ tự động hoá

Dò tìm injectable: **fully automated**. Chuẩn bị target (đăng nhập lấy token, tạo file request mẫu từ Burp): **semi-automated**, cần thao tác thủ công ban đầu.

---

## 4. Bảng tổng hợp nhanh 3 công cụ trên case study eshop-sut

| Tiêu chí | ZAP | Burp Suite Community | sqlmap |
|---|---|---|---|
| Vai trò chính | Quét diện rộng, tự động | Kiểm thử thủ công có chủ đích | Chuyên sâu 1 loại lỗ hổng |
| SEC bao phủ tốt nhất | SEC-04, SEC-05 (sơ bộ) | SEC-02, SEC-03, SEC-06, SEC-07 | SEC-05 (sâu), SEC-01 (gián tiếp) |
| Record & Playback | Zest Script (macro cả luồng) | Repeater (từng request có kiểm soát) | `-r` / `-l` (phát lại request đã ghi từ Burp/ZAP) |
| Data-driven | Fuzzer (cần tự chuẩn bị payload) | Intruder (4 kiểu tấn công) | Payload nội bộ tự động, không cần chuẩn bị |
| Checkpoints | Scan Rules + Alert Risk Level | Grep-Match (Intruder) + Comparer | Tự đánh giá injectable yes/no nội tại |
| Mức tự động hoá | Fully automated (sau khi cấu hình auth) | Semi-automated | Fully automated (dò tìm), semi (chuẩn bị) |
| Điểm yếu lớn nhất | Không hiểu logic phân quyền | Không có Active Scanner (bản Free) | Chỉ chuyên SQLi, cần phiên đăng nhập sẵn |

---