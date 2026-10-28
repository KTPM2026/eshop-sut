# Nội dung thuyết trình phần Nguyễn Đức Phát

**Chủ đề nhóm:** Security Testing in Website — môn Testing.  
**Thời lượng:** 3–4 phút, **4 slide trong tổng ~10 slide của nhóm** (nếu cần gọn, có thể gộp Slide 4 vào phần AI của Lân).  
**Phạm vi phân công:** P1 (thiết kế & hoàn thiện bộ **bài tập thực hành Lab cho lớp**), P2 (gán nhãn Ground Truth), P3a (pilot), P4 (slide/báo cáo **thao tác Lab**). Trọng tâm slide là **bài tập Lab**.  
**Căn cứ:** đề cương mục 6, tài liệu Lab và kết quả chạy thật ngày 17/10/2026 (bổ sung A02/A07 ngày 22/10/2026).

Chỉ đưa phần "Nội dung trên slide" vào PowerPoint. Lời thuyết trình và ghi chú dùng để chuẩn bị. Ảnh gợi ý nằm trong `../../Phat/P1_labs/evidence/`. Khi ghép bài, đánh số slide theo thứ tự chung của nhóm.

## Slide 1 — Bộ bài tập thực hành (Hands-on Lab) cho lớp

### Nội dung trên slide

**3 bài Lab trên EShop (localhost) — độ khó tăng dần, lớp tự thực hành trong buổi**

| Lab | Lỗ hổng (OWASP) | Cấp độ | Thao tác | Thời lượng |
|---|---|---|---|---|
| **Lab 1** | Reflected XSS (A03) | 🟢 Cơ bản | GUI — OWASP ZAP | ~10 phút |
| **Lab 2** | SQL Injection (A03) | 🟡 Nâng cao | CLI — sqlmap | ~15–20 phút |
| **Lab 3** | Brute-force OTP (A07) | 🟡 Nâng cao | ZAP Fuzzer / Burp Intruder | ~15 phút |

- Mỗi Lab có **hướng dẫn từng bước + Hints tăng dần + Đáp án + Pass/Fail** → lớp tự làm theo.
- **Bàn giao cho lớp:** wordlist payload XSS (`xss-payloads.txt`), script reset DB (`database.sqlite.bak`).

### Lời thuyết trình — khoảng 45 giây

"Phần em phụ trách là bộ bài tập để chính các bạn trong lớp làm trực tiếp. Nhóm thiết kế ba bài độ khó tăng dần trên EShop localhost: Lab 1 Reflected XSS mức cơ bản thao tác trên giao diện ZAP khoảng 10 phút; Lab 2 SQL Injection bằng sqlmap khoảng 15–20 phút; Lab 3 vét cạn OTP khoảng 15 phút. Mỗi bài có hướng dẫn từng bước, gợi ý, đáp án và tiêu chí Pass/Fail, kèm wordlist và script reset để lớp làm lại được."

## Slide 2 — Hướng dẫn thao tác: ZAP Fuzzer (Lab 1 XSS) & Fuzzer số (Lab 3 OTP)

### Nội dung trên slide

**Lab 1 — ZAP Fuzzer (XSS):**
1. **Manual Explore → Launch Browser**, vào EShop (5173), tìm kiếm 1 từ khóa.
2. Tab **History** → tìm request `GET /api/products?search=...` → chuột phải → **Attack → Fuzz**.
3. Bôi đen **giá trị tham số `search`** → **Add** (điểm chèn).
4. **Payloads → Add → Type: File** → chọn `xss-payloads.txt` → **Start Fuzzer**.
5. Lọc theo **Size Resp. Body / Code** để tìm phản hồi bất thường → tab **Response** kiểm payload chưa escape.
6. **Xác thực:** gõ `<img src=x onerror=alert(...)>` vào ô tìm kiếm → **alert bung** (browser execution).

**Lab 3 — ZAP Fuzzer / Burp Intruder (vét cạn OTP):**
1. Gọi `POST /api/forgot-password` (body `{"email":"test@eshop.com"}`) để tạo `reset_token`.
2. Bắt request `POST /api/reset-password` → **Attack → Fuzz**, đánh dấu giá trị `resetToken`.
3. **Payloads → Type: Numberzz**, From `1000` To `9999` Step `1` → **Start** *(Burp: Intruder → Sniper → Payload Numbers 1000–9999)*.
4. Lọc dòng **HTTP 200 "Password reset successfully"** = OTP đúng → chiếm tài khoản.

### Lời thuyết trình — khoảng 1 phút

"Đây là phần cốt lõi lớp thao tác — dùng ZAP Fuzzer.

Với Lab 1, các bạn mở trình duyệt qua ZAP, tìm kiếm để ZAP bắt được request, rồi chuột phải chọn Attack → Fuzz. Bôi đen giá trị tham số search làm điểm chèn, nạp file payload XSS rồi Start Fuzzer. Sau đó lọc theo kích thước phản hồi để tìm payload đáng ngờ, và xác thực bằng cách gõ payload onerror vào ô tìm kiếm cho bung alert.

Lab 3 dùng đúng kỹ thuật Fuzzer nhưng nạp dải số: trước hết gọi forgot-password để sinh mã, rồi fuzz tham số resetToken với payload số từ 1000 đến 9999. Vì không có giới hạn số lần thử, chỉ cần tìm dòng trả về 200 là ra mã đúng."

## Slide 3 — Hướng dẫn sqlmap (Lab 2) & Kết quả kiểm chứng 3 Lab

### Nội dung trên slide

**Lab 2 — sqlmap (SQL Injection):**
```bash
sqlmap -r search.raw --batch                                  # xác nhận injectable
sqlmap -r search.raw --batch --tables                         # liệt kê bảng
sqlmap -r search.raw --batch -T users -C "name,email,password,role" --dump
```
> SQLite: dùng `--tables` trực tiếp; `--dump` cần chỉ cột `-C`.

**Kết quả chạy thử (bằng chứng 3 Lab chạy được):**
- **Lab 1:** alert thực thi trên trình duyệt (`evidence/lab1-xss-alert.jpg`).
- **Lab 2:** dump `users` → mật khẩu **plaintext** `Admin123!`, `Test1234!` → cũng là **A02** (`evidence/sqlmap_users_dump.csv`).
- **Lab 3:** vét cạn 9000 OTP, không rate-limit → đổi được mật khẩu (**A07**).
- **Khắc phục:** Output Encoding/CSP; Parameterized Query + hash mật khẩu; rate-limit + OTP mạnh (CSPRNG) + TTL.

### Lời thuyết trình — khoảng 1 phút

"Lab 2 chuyển sang dòng lệnh. Các bạn lưu request tìm kiếm thành file rồi nạp vào sqlmap với cờ `-r` và `--batch`; sqlmap tự xác nhận lỗi, liệt kê bảng bằng `--tables` rồi dump bảng users — vì là SQLite nên cần chỉ rõ cột khi dump.

Để chứng minh ba Lab chạy thật, em đã tự chạy: Lab 1 bung được alert; Lab 2 dump ra mật khẩu dạng thô như Admin123!, nên vừa là SQL Injection vừa là lỗi A02 lưu mật khẩu không băm; Lab 3 đổi được mật khẩu nạn nhân qua vét cạn OTP, đại diện A07. Cách khắc phục tương ứng là mã hóa đầu ra, truy vấn tham số hóa kèm băm mật khẩu, và giới hạn số lần thử kèm OTP mạnh có thời hạn."

## Slide 4 — Gán nhãn Ground Truth cho đối chứng AI Triage (P2)

### Nội dung trên slide

- Gán nhãn **độc lập 17 cảnh báo** (15 từ ZAP + 2 mở rộng A02/A07) làm **đáp án chuẩn** chấm AI Triage.
- Phân loại: **10 Thật / 4 Giả–False Positive / 3 Informational**; ưu tiên P1–P4.
- Gán tay **~30 phút** → mốc đối chứng tốc độ với AI. Gán **độc lập, chưa xem kết quả AI**.
- **Đang chờ:** đối chiếu bất đồng với người gán nhãn thứ 2 (Như) để chốt Ground Truth cuối.

### Lời thuyết trình — khoảng 45 giây

"Ngoài bộ Lab, em gán nhãn làm đáp án chuẩn cho module AI Triage của bạn Lân. Em xem độc lập 17 cảnh báo, phán xử thật / giả / thông tin kèm ưu tiên — kết quả 10 thật, 4 giả, 3 thông tin — mất khoảng 30 phút làm tay để đối chứng tốc độ với AI. Em gán độc lập, chưa xem kết quả AI; bước còn lại là chốt bất đồng với bạn Như."

## Ghi chú khi được hỏi — không đưa lên slide

- **Thời lượng Lab có vừa buổi không? (GVTH #4):** ~10 / 15–20 / 15 phút hợp lý khi môi trường đã dựng sẵn; lần đầu cài ZAP/sqlmap/npm nên chuẩn bị trước buổi, không tính vào giờ Lab.
- **Vì sao vào URL `?search=<payload>` không bung alert?** App không đọc tham số từ URL (phải gõ vào ô tìm kiếm); cửa sổ trình duyệt do ZAP điều khiển nuốt hộp `alert` → xác thực bằng Chrome thường.
- **`<script>` có chạy không?** Không — `<script>` chèn qua `dangerouslySetInnerHTML`/innerHTML không tự thực thi; phải dùng event handler (`onerror`/`onload`). Payload có `'` lại vỡ SQL → 500.
- **sqlmap báo DB tên gì?** `SQLite_masterdb` (placeholder của sqlmap, không phải `main`); `--dump` trên SQLite cần `-C`.
- **Mật khẩu dump có phải dữ liệu thật?** Không — dữ liệu seed thử nghiệm của lab.
- **Lab OTP có "ăn gian"?** API còn trả `resetToken` trong response (lỗi lộ thông tin), nhưng lab giả định kẻ tấn công không thấy mã và chỉ brute-force.
- **Nhãn Ground Truth đã chốt chưa?** Chưa — mới có nhãn độc lập; chờ đối chiếu với Như. Người viết module AI (Lân) không gán nhãn chuẩn.

## Nguồn đối chiếu — không tạo slide riêng

- [Hướng dẫn 3 bài Lab](../../../seminar/docs/lab-huong-dan.md) — bước, hints, đáp án, Pass/Fail.
- [Báo cáo thực nghiệm phần Lab](../../Phat/P4_slide_baocao/bao-cao-lab.md) — có ảnh từng bước.
- [Minh chứng](../../Phat/P1_labs/evidence/) — ảnh XSS, bảng dump sqlmap CSV.
- [Bảng gán nhãn Ground Truth P2](../../Phat/P2_nhan_alert/alert-labeling-template.md).

Các số liệu (sqlmap dump, 17 nhãn, ~30 phút, thời lượng Lab) lấy từ kết quả đã chạy và tài liệu bàn giao; không chạy lại khi biên soạn.
