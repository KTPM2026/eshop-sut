# Seminar của Thạch Như

**MSSV:** 23120312. **Lớp:** CQ2023/31. **Học phần:** CS423 / CSC13003 - Software Testing, FIT@HCMUS. **Giảng viên:** ThS. Trần Thị Bích Hạnh.

Repo thực hiện: [KTPM2026/eshop-sut](https://github.com/KTPM2026/eshop-sut), nhánh `nhu/seminar-workspace`, nền `main` tại `ab5dd4f7ac0d8562800311dc94109939d3c6d930`. Giữ nguyên source SUT, file ZAP/WAF của Hùng và module AI của Lân. Phần này chỉ bổ sung `Nhu/`.

## Đã thực hiện

| Phần | Sản phẩm hiện có |
|---|---|
| [N1: Burp/phân quyền](N1_burp/README.md) | Chạy thật 11 ca API trên main của nhóm: **5 pass, 6 vi phạm phân quyền, 2 phát hiện**. Có request/response, CSV và 3 ảnh response 1920×1080 trong [minh chứng](N1_burp/evidence/main-run-20261016/README.md). Có runbook để Như quay Burp. |
| [N2: Gán nhãn](N2_gan_nhan/README.md) | Đã đọc ZAP 2.17.0 của Hùng ngày 14/10: **31 instance gốc, giữ 29 localhost, loại 2 ngoài scope**. Dùng parser của Lân, khóa ID/hash; có input AI đã che token, dataset và phiếu nhãn trống. |
| [N3: Benchmark](N3_benchmark_triage/README.md) | Bộ chấm tương thích A1 của Lân; tính Precision/Recall, coverage, khớp ưu tiên, lỗi thật bị xếp thấp/giả, thời gian gồm review và baseline risk. Có kiểm tra dữ liệu/mock/replay và test công thức. |
| [N4: Báo cáo/slide](N4_slide_baocao/README.md) | Nội dung thực nghiệm đã điền số liệu ZAP và API thật, hai phát hiện, giới hạn, nguồn và nội dung từng slide để ghép bài chung. |

Kết quả API do Codex hỗ trợ thực thi; ảnh là trình duyệt Edge, **không phải ảnh Burp**. Phiếu N2 chưa có nhãn của Như, chưa có nhãn chuẩn Như/Phát hoặc số liệu benchmark AI. Không biến dữ liệu mẫu thành kết quả nộp.

## Ba việc để chốt bài

1. **Như:** tự replay/quay Burp theo [N1](N1_burp/README.md), lưu clip 1080p có thuyết minh rồi gửi Long ghép video 2.
2. **Như và Phát:** đồng ý scope/rubric, mỗi người tự kiểm chứng và gán nhãn riêng trên [29 ID đã chuẩn bị](N2_gan_nhan/data/h1-20261014/dataset.json). Khóa phiếu trước khi xem nhãn nhau hoặc kết quả AI, rồi chốt bất đồng. Không cần chờ Hùng gửi lại export.
3. **Lân và Như:** sau khi khóa nhãn chuẩn, Lân chạy A1 thật ít nhất ba lần trên cùng [a1-input.json](N2_gan_nhan/data/h1-20261014/a1-input.json) và cấu hình đã duyệt; Như review/đo thời gian rồi dùng N3 chấm. Thêm kết quả/clip vào N4 và gửi Phát ghép bài.

Hùng đã có [ZAP export](../alert/2026-10-14-ZAP-Report-.json), [hướng dẫn setup](../setup_ZAP.md) và H3 trong main. Chỉ cần nhờ Hùng bổ sung **commit chính xác của lượt scan 14/10 và request/response gốc nếu một alert không đủ căn cứ**, không ghi toàn bộ H1 là chưa có.

## File dùng chung

- Lân chạy AI bằng `Nhu/N2_gan_nhan/data/h1-20261014/a1-input.json`, không dùng raw export chứa traffic ngoài scope/token.
- Như/Phát dùng `dataset.json` cùng thư mục. Hash `source_sha256` là SHA256 bytes của **a1-input.json**, không phải hash export gốc; cả hai hash và mapping về export nằm trong `provenance.json`.
- `nhu-labels.blank.csv` là mẫu chưa điền. Sao chép vào `Nhu/private/nhu-labels.csv` để làm riêng, không sửa bản mẫu hoặc đưa nhãn draft lên Git trước khi Phát khóa phiếu.
- Nội dung ghép báo cáo/slide: [N4](N4_slide_baocao/README.md). Các bản khóa, timing và output thật sẽ bàn giao sau; không tạo file giả để đủ checklist.

## Kiểm tra và tái lập

Từ root repo, Python 3.12 và Node.js 24. N2 chuẩn bị ZAP dùng dependency có sẵn của Lân:

```powershell
python -m pip install -r Lan/requirements.txt
python -X utf8 -m unittest discover -s Nhu/tests -v
python -X utf8 -m Nhu.N2_gan_nhan.prepare_zap --output-dir Nhu/outputs/h1-rebuilt
```

N2/N3 core dùng thư viện chuẩn; adapter ZAP dùng trực tiếp `Lan.A1_ai_triage.parser`. Lệnh chuẩn bị từ chối ghi đè, không truy cập URL trong report và không gọi AI. Lệnh N1 và N3 ở README tương ứng.

Kiểm tra ngày 16/10/2026: **36/36 test Như và 30/30 test Lân qua**. Đây là kiểm thử code/contract, không phải số liệu benchmark AI. Tạo phiếu làm việc riêng theo lệnh trong N2; nếu đã có phiếu thì tiếp tục trên file đó, không xóa hoặc ghi đè.

Phân công N1–N4 lấy từ [đề cương nhóm](https://github.com/KTPM2026/seminar/blob/main/docs/de-cuong-seminar.md); phương pháp từ [proposal](https://github.com/KTPM2026/seminar/blob/main/docs/ai_proposal.md). Đây là tài liệu kế hoạch của nhóm, không phải hướng dẫn upload chính thức của giảng viên. [Nhật ký thực hiện](progress-log.md) ghi rõ phần AI hỗ trợ.

`private/`, `outputs/`, dependency, bytecode và secret được bỏ qua khi đưa Git. Không đưa clone lab hoặc database riêng vào bài nộp.
