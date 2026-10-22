# Nội dung thuyết trình phần Nguyễn Đức Phát

**Chủ đề nhóm:** Security Testing in Website — môn Testing.  
**Thời lượng:** 3–4 phút, **3 slide trong tổng ~10 slide của nhóm**.  
**Căn cứ:** tài liệu Lab và kết quả chạy thật ngày 17/10/2026 (cập nhật A02/A07 ngày 22/10/2026).

Chỉ đưa phần "Nội dung trên slide" vào PowerPoint. Lời thuyết trình và ghi chú dùng để chuẩn bị, không tạo thêm slide. Ảnh gợi ý nằm trong `../../Phat/P1_labs/evidence/`. Khi ghép bài, đánh số slide theo thứ tự chung của nhóm.

## Slide 1 — Bộ bài thực hành (Hands-on Lab) & Reflected XSS

### Nội dung trên slide

**Quy trình DAST: bắt request → fuzz/kiểm chứng → xác thực → khắc phục**

- **3 bài Lab** trên EShop localhost (lỗ hổng cài sẵn để học): Lab 1 XSS (ZAP), Lab 2 SQLi (sqlmap), Lab 3 Brute-force OTP (ZAP/Burp).
- **Lab 1 — Reflected XSS (A03):** payload `<img src=x onerror=alert(...)>` phản xạ qua `dangerouslySetInnerHTML` → **alert thực thi trên trình duyệt**.
- Điểm bẫy đã kiểm chứng: `<script>` không chạy qua innerHTML; payload có `'` làm vỡ SQL (500); xác thực phải trên trình duyệt chứ không trên JSON API.
- *Ảnh gợi ý:* `evidence/lab1-xss-alert.jpg` (alert bung `localhost`), `evidence/lab1-zap-fuzzer.jpg`.

### Lời thuyết trình — khoảng 1 phút

"Phần em phụ trách là bộ bài thực hành cho lớp và việc gán nhãn kết quả kiểm thử.

Nhóm thiết kế ba bài Lab độ khó tăng dần trên ứng dụng EShop chạy localhost, với lỗ hổng cố ý cài để học tập. Cả ba đi theo cùng quy trình kiểm thử động: bắt gói tin, bơm payload hoặc kiểm chứng, rồi xác thực lỗ hổng và nêu cách khắc phục.

Bài 1 là Reflected XSS. Dữ liệu tìm kiếm được đưa thẳng ra HTML qua dangerouslySetInnerHTML nên payload chạy được trên trình duyệt; em đã cho bung hộp alert để chứng minh.

Em cũng ghi lại ba điểm dễ nhầm: thẻ script chèn qua innerHTML không tự chạy, payload chứa dấu nháy đơn lại làm vỡ câu SQL và trả lỗi 500, và việc xác thực XSS phải làm trên trình duyệt chứ không nhìn vào JSON của API."

## Slide 2 — SQL Injection & Brute-force OTP (kết quả thật)

### Nội dung trên slide

- **Lab 2 — SQL Injection (A03):** tham số `search` nối chuỗi vào SQL → sqlmap xác nhận **UNION query, 6 cột, DBMS SQLite**; dump bảng `users`.
  - Mật khẩu lưu **plaintext**: `Admin123!`, `Test1234!` → đồng thời là minh chứng **A02 Cryptographic Failures**.
- **Lab 3 — Brute-force OTP (A07):** OTP 4 số (`Math.random`, 1000–9999) + `/api/reset-password` **không rate-limit** → vét cạn 9000 tổ hợp đến khi HTTP 200 → **chiếm tài khoản**.
- **Khắc phục:** Parameterized Query + hash mật khẩu (bcrypt); rate-limit + OTP mạnh (CSPRNG) + hạn dùng (TTL).
- *Ảnh gợi ý:* `evidence/sqlmap_users_dump.csv` (bảng dump), output 3 lệnh sqlmap.

### Lời thuyết trình — khoảng 1 phút

"Bài 2 là SQL Injection. Câu truy vấn tìm kiếm nối chuỗi trực tiếp, nên sqlmap xác nhận tham số search bị inj(kỹ thuật UNION, sáu cột) và cơ sở dữ liệu là SQLite. Em dump được bảng users và thấy mật khẩu lưu dạng thô, ví dụ Admin123! và Test1234!. Đây vừa chứng minh SQL Injection, vừa là bằng chứng cho lỗi A02 — lưu mật khẩu không băm.

Bài 3 là tấn công vét cạn OTP đặt lại mật khẩu. Mã OTP chỉ bốn chữ số, sinh bằng Math.random, và endpoint reset không giới hạn số lần thử. Vì vậy chỉ cần dò hết chín nghìn tổ hợp cho tới khi nhận HTTP 200 là đổi được mật khẩu nạn nhân — đại diện cho nhóm lỗi A07.

Về khắc phục: dùng truy vấn tham số hóa và băm mật khẩu cho A02 và A03; thêm giới hạn số lần thử, dùng OTP đủ mạnh sinh bằng bộ sinh ngẫu nhiên an toàn và có thời hạn cho A07."

## Slide 3 — Gán nhãn Ground Truth cho đối chứng AI Triage (P2)

### Nội dung trên slide

- Gán nhãn **độc lập 17 cảnh báo** (15 từ ZAP + 2 mở rộng A02/A07) làm **đáp án chuẩn** để chấm AI Triage.
- Phân loại: **10 Thật / 4 Giả–False Positive / 3 Informational**; gán ưu tiên P1–P4 theo ma trận Exploitability × Impact.
- Thời gian gán nhãn thủ công **~30 phút** → mốc đối chứng tốc độ với AI.
- **Đang chờ:** đối chiếu bất đồng với người gán nhãn thứ 2 (Như) để chốt Ground Truth cuối.

### Lời thuyết trình — khoảng 1 phút

"Phần cuối là gán nhãn làm đáp án chuẩn cho module AI Triage của bạn Lân.

Em xem xét độc lập 17 cảnh báo — 15 cái từ lần quét ZAP và 2 cái mở rộng là lưu mật khẩu plaintext và vét cạn OTP — rồi tự phán xử từng cái là lỗ hổng thật, báo động giả, hay chỉ mang tính thông tin, kèm mức ưu tiên từ P1 đến P4. Kết quả có 10 cái thật, 4 cái giả và 3 cái chỉ là thông tin.

Việc này được làm thủ công, mất khoảng 30 phút — con số này dùng để đối chứng với tốc độ xử lý của AI. Điểm quan trọng là em gán nhãn độc lập, chưa xem kết quả AI, để đáp án chuẩn khách quan.

Hiện em đã có bảng nhãn riêng; bước còn lại là ngồi với bạn Như đối chiếu các điểm bất đồng để chốt đáp án chuẩn cuối cùng."

## Ghi chú khi được hỏi — không đưa lên slide

- **Vì sao vào URL `?search=<payload>` không bung alert?** App không đọc tham số từ URL (phải gõ vào ô tìm kiếm), và cửa sổ trình duyệt do ZAP điều khiển tự nuốt hộp `alert` → xác thực bằng Chrome thường.
- **sqlmap báo DB tên gì?** `SQLite_masterdb` — đây là tên placeholder sqlmap đặt cho SQLite (không phải `main`); `--dump` trên SQLite cần chỉ rõ cột `-C`.
- **Mật khẩu dump có phải dữ liệu thật?** Không — là dữ liệu seed thử nghiệm của lab (`admin@eshop.com`...), không phải người dùng thật.
- **Lab OTP có "ăn gian" không?** API hiện còn trả `resetToken` trong response (một lỗi lộ thông tin), nhưng lab **giả định kẻ tấn công không thấy mã** và chỉ brute-force — đúng kịch bản thực tế.
- **Nhãn Ground Truth đã chốt chưa?** Chưa — mới có nhãn độc lập của em; còn chờ đối chiếu với Như. Người viết module AI (Lân) không tham gia gán nhãn chuẩn.
- **17 alert ở đâu ra?** 15 từ file ZAP scan ngày 14/10; 2 mở rộng (A02/A07) xác định thủ công từ mã nguồn và kiểm thử, theo mục 1.4 đề cương.

## Nguồn đối chiếu — không tạo slide riêng

- [Báo cáo thực nghiệm phần Lab](../../Phat/P4_slide_baocao/bao-cao-lab.md) (có ảnh từng bước).
- [Hướng dẫn 3 bài Lab](../../../seminar/docs/lab-huong-dan.md).
- [Minh chứng](../../Phat/P1_labs/evidence/) — ảnh XSS, bảng dump sqlmap CSV.
- [Bảng gán nhãn Ground Truth P2](../../Phat/P2_nhan_alert/alert-labeling-template.md) và [bộ dữ kiện alert](../../Phat/P2_nhan_alert/alert-evidence-pack.md).

Các số liệu (sqlmap dump, 17 nhãn, ~30 phút) lấy từ kết quả đã chạy và tài liệu bàn giao; không chạy lại khi biên soạn nội dung này.
