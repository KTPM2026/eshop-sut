# Nội dung thuyết trình phần Nguyễn Đức Phát

**Chủ đề nhóm:** Security Testing in Website — môn Testing.  
**Thời lượng:** 3–4 phút, **3 slide trong tổng ~10 slide của nhóm**.  
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

- Mỗi Lab có **hướng dẫn từng bước + Hints tăng dần + Đáp án + tiêu chí Pass/Fail** → lớp tự làm theo.
- **Bàn giao cho lớp:** wordlist payload XSS (`xss-payloads.txt`), script reset DB (`database.sqlite.bak`).
- Đi từ trực quan (GUI) đến can thiệp sâu (CLI/DB), bám chuẩn OWASP Top 10.

### Lời thuyết trình — khoảng 1 phút

"Phần em phụ trách là bộ bài tập thực hành để chính các bạn trong lớp làm trực tiếp trong buổi seminar.

Nhóm thiết kế ba bài Lab độ khó tăng dần trên ứng dụng EShop chạy localhost, với lỗ hổng cố ý cài để học. Bài 1 là Reflected XSS, mức cơ bản, thao tác hoàn toàn trên giao diện ZAP, khoảng 10 phút. Bài 2 là SQL Injection bằng dòng lệnh sqlmap, nâng cao hơn, khoảng 15 đến 20 phút. Bài 3 là vét cạn OTP, cũng mức nâng cao, khoảng 15 phút.

Mỗi bài đều có hướng dẫn từng bước, gợi ý tăng dần, đáp án và tiêu chí Pass/Fail rõ ràng để các bạn tự kiểm tra. Nhóm bàn giao kèm file wordlist payload và script reset cơ sở dữ liệu để lớp làm lại được. Thời lượng ba bài em thấy vừa với một buổi; đây cũng là điểm nhóm muốn xin ý kiến Thầy/Cô."

## Slide 2 — Kết quả chạy thử (kiểm chứng 3 Lab đều chạy được)

### Nội dung trên slide

- **Lab 1 — XSS:** payload `<img src=x onerror=...>` phản xạ qua `dangerouslySetInnerHTML` → **alert thực thi trên trình duyệt** (checkpoint = browser execution, không chỉ status 200).
- **Lab 2 — SQLi:** sqlmap xác nhận **UNION, 6 cột, SQLite**; dump `users` ra mật khẩu **plaintext** (`Admin123!`, `Test1234!`) → đồng thời minh chứng **A02**.
- **Lab 3 — OTP:** OTP 4 số (`Math.random`) + `/api/reset-password` **không rate-limit** → vét cạn 9000 tổ hợp → chiếm tài khoản.
- **Khắc phục:** Output Encoding/CSP (XSS); Parameterized Query + hash mật khẩu (SQLi/A02); rate-limit + OTP mạnh CSPRNG + TTL (OTP).
- *Ảnh gợi ý:* `evidence/lab1-xss-alert.jpg`, `evidence/sqlmap_users_dump.csv`, `evidence/lab1-zap-fuzzer.jpg`.

### Lời thuyết trình — khoảng 1 phút

"Để chứng minh ba Lab chạy được thật, em đã tự chạy toàn bộ trên EShop.

Bài 1, em cho bung được hộp alert trên trình duyệt — tức payload thực thi thật, chứ không chỉ nhìn mã 200. Bài 2, sqlmap xác nhận lỗi SQL Injection kiểu UNION trên SQLite và dump được bảng users; mật khẩu lưu dạng thô như Admin123!, nên đây vừa là SQL Injection vừa là lỗi lưu mật khẩu không băm, nhóm A02. Bài 3, vì OTP chỉ bốn chữ số và endpoint reset không giới hạn số lần thử, nên dò hết chín nghìn tổ hợp là đổi được mật khẩu nạn nhân.

Về khắc phục: mã hóa đầu ra và CSP cho XSS; truy vấn tham số hóa và băm mật khẩu cho SQL Injection và A02; giới hạn số lần thử, OTP đủ mạnh và có thời hạn cho A07."

## Slide 3 — Gán nhãn Ground Truth cho đối chứng AI Triage (P2)

### Nội dung trên slide

- Gán nhãn **độc lập 17 cảnh báo** (15 từ ZAP + 2 mở rộng A02/A07) làm **đáp án chuẩn** để chấm AI Triage.
- Phân loại: **10 Thật / 4 Giả–False Positive / 3 Informational**; ưu tiên P1–P4.
- Gán nhãn thủ công **~30 phút** → mốc đối chứng tốc độ với AI. Gán **độc lập, chưa xem kết quả AI**.
- **Đang chờ:** đối chiếu bất đồng với người gán nhãn thứ 2 (Như) để chốt Ground Truth cuối.

### Lời thuyết trình — khoảng 1 phút

"Ngoài bộ Lab, em còn đóng góp phần gán nhãn làm đáp án chuẩn cho module AI Triage.

Em xem xét độc lập 17 cảnh báo — 15 từ lần quét ZAP và 2 cái mở rộng là mật khẩu plaintext và vét cạn OTP — rồi tự phán xử là lỗ hổng thật, báo động giả hay chỉ là thông tin, kèm mức ưu tiên. Kết quả 10 thật, 4 giả, 3 thông tin. Việc này mất khoảng 30 phút làm tay, dùng để đối chứng tốc độ với AI. Em gán độc lập, chưa xem kết quả AI, để đáp án khách quan. Bước còn lại là ngồi với bạn Như chốt các điểm bất đồng."

## Ghi chú khi được hỏi — không đưa lên slide

- **Thời lượng Lab có vừa buổi không? (GVTH #4):** ~10 / 15–20 / 15 phút là hợp lý khi môi trường đã dựng sẵn; lần đầu cài môi trường (ZAP/sqlmap/npm) nên chuẩn bị trước buổi, không tính vào giờ Lab.
- **Vì sao vào URL `?search=<payload>` không bung alert?** App không đọc tham số từ URL (phải gõ vào ô tìm kiếm); cửa sổ trình duyệt do ZAP điều khiển nuốt hộp `alert` → xác thực bằng Chrome thường.
- **sqlmap báo DB tên gì?** `SQLite_masterdb` (tên placeholder của sqlmap, không phải `main`); `--dump` trên SQLite cần chỉ cột `-C`.
- **Mật khẩu dump có phải dữ liệu thật?** Không — dữ liệu seed thử nghiệm của lab, không phải người dùng thật.
- **Lab OTP có "ăn gian"?** API hiện còn trả `resetToken` trong response (một lỗi lộ thông tin), nhưng lab giả định kẻ tấn công không thấy mã và chỉ brute-force.
- **Nhãn Ground Truth đã chốt chưa?** Chưa — mới có nhãn độc lập; còn chờ đối chiếu với Như. Người viết module AI (Lân) không gán nhãn chuẩn.

## Nguồn đối chiếu — không tạo slide riêng

- [Hướng dẫn 3 bài Lab](../../../seminar/docs/lab-huong-dan.md) — bước, hints, đáp án, Pass/Fail.
- [Báo cáo thực nghiệm phần Lab](../../Phat/P4_slide_baocao/bao-cao-lab.md) — có ảnh từng bước.
- [Minh chứng](../../Phat/P1_labs/evidence/) — ảnh XSS, bảng dump sqlmap CSV.
- [Bảng gán nhãn Ground Truth P2](../../Phat/P2_nhan_alert/alert-labeling-template.md).

Các số liệu (sqlmap dump, 17 nhãn, ~30 phút, thời lượng Lab) lấy từ kết quả đã chạy và tài liệu bàn giao; không chạy lại khi biên soạn.
