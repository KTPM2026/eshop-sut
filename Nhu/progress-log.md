# Nhật ký phần Như

**Thạch Như - 23120312.** Nhánh `nhu/seminar-workspace`, repo `KTPM2026/eshop-sut`. Các công việc dưới đây có Codex hỗ trợ, không tuyên bố sinh viên đã tự chạy Burp/gán nhãn.

| Ngày | Công việc thực hiện | Kết quả/bằng chứng |
|---|---|---|
| 16/10/2026 | Soạn runbook N1, 11 ca, request template; viết công cụ N2/N3 và tests tại workspace cũ | Giữ lại phần Như; không mang clone/dependency/kết quả synthetic sang bản chia sẻ |
| 16/10/2026 | Đọc lịch sử main repo đúng: Hùng có ZAP export, setup và WAF; cập nhật thêm commit Lân `ab5dd4f` | Chuyển phần Như sang nhánh riêng từ main repo đúng; không sửa source SUT/Hùng/Lân |
| 16/10/2026 | Chuẩn bị dữ liệu từ ZAP 2.17.0 của Hùng ngày 14/10 bằng parser Lân | 31 instance gốc, giữ 29 localhost/13 nhóm theo site, loại 2 ngoài scope; ID/hash/mapping trong `N2_gan_nhan/data/h1-20261014/provenance.json` |
| 16/10/2026 | Tạo input A1 đã che token, dataset N2/P2/N3 và phiếu trống | Cùng 29 ID; chưa có nhãn của Như/Phát, không gọi AI |
| 16/10/2026 | Chạy lại N1 trên clone lab riêng tại commit main `ab5dd4f7ac0d8562800311dc94109939d3c6d930` | 11 ca: 5 pass, 6 vi phạm phân quyền, 0 inconclusive, 2 phát hiện; HTTP thật và 3 ảnh response 1920×1080 tại `N1_burp/evidence/main-run-20261016/` |
| 16/10/2026 | Cập nhật N4 từ số liệu ZAP/API và rút gọn hướng dẫn bàn giao | Không còn ghi chờ toàn bộ H1; còn xác nhận commit scan cũ/full response nếu cần, quay Burp, nhãn độc lập và ba run AI thật có review |
| 16/10/2026 | Chạy unittest sau tích hợp và tạo phiếu làm việc private cho Như | 35/35 test Như, 30/30 test Lân qua; `Nhu/private/nhu-labels.csv` có 29 dòng trống, không có nhãn do AI điền |
| 16/10/2026 | Dọn import/ghi chú riêng máy trước khi push; cố định bytes của pack/minh chứng và thêm kiểm tra CRLF/LF | 36/36 test Như qua; giữ hash input A1 chính xác, bổ sung hash nội dung export/source để đối chiếu đa nền tảng; private/database/dependency/cache không đưa vào Git |
| 17/10/2026 | Rút gọn checklist chuẩn bị PR, tách phần kỹ thuật N1–N3 khỏi kế hoạch video và slide/report N4 | Chưa có đề gốc xác nhận video bắt buộc cho lần nộp hiện tại; giữ nguyên code, dataset, minh chứng và dữ liệu private; không đánh dấu nhãn/benchmark là hoàn tất |

Bước tiếp theo về kỹ thuật: Như kiểm chứng Burp và lưu bằng chứng; Như/Phát gán nhãn riêng, khóa rồi chốt; Lân chạy A1 trên input chung, Như đo review và chấm N3. Slide/report N4 để giai đoạn sau; yêu cầu video của lần nộp hiện tại chờ đối chiếu đề gốc. Không đưa thời gian fixture, mock hoặc ảnh Edge thành bằng chứng Burp/benchmark thật.
