# N2: Như gán nhãn độc lập lần 1

**Đã có dữ liệu thật của Hùng, chưa có nhãn người kiểm thử.** Không gọi AI, không suy nhãn từ risk và không tạo phiếu của Phát.

## Bộ dữ liệu sẵn dùng

Nguồn: [ZAP export ngày 14/10/2026](../../alert/2026-10-14-ZAP-Report-.json), ZAP 2.17.0. File gốc có 31 instance trong 15 nhóm alert theo site; lọc còn **29 instance, 13 nhóm alert theo site** trên `http://localhost:3000` và `http://localhost:5173`. Hai instance Google ngoài scope bị loại, không truy cập/scan lại dịch vụ đó.

Phân bố risk: **2 High, 7 Medium, 10 Low, 10 Informational**. Đây là risk do scanner báo, không phải số lỗi thật hoặc ground truth. Một instance là một record; nhiều instance có thể cùng nguyên nhân.

| File trong [data/h1-20261014](data/h1-20261014) | Dùng cho |
|---|---|
| [a1-input.json](data/h1-20261014/a1-input.json) | Input A1 của Lân, chỉ localhost, đã che token bằng redactor/parser hiện có của Lân |
| [dataset.json](data/h1-20261014/dataset.json) | N2/P2/N3, cùng 29 ID với input A1, không có nhãn/ưu tiên AI |
| [provenance.json](data/h1-20261014/provenance.json) | Hash export gốc và input A1, phiên bản ZAP, mapping ID tới vị trí instance gốc, scope và số bản ghi loại |
| [nhu-labels.blank.csv](data/h1-20261014/nhu-labels.blank.csv) | Phiếu trống để Như làm riêng; không phải bài gán nhãn đã hoàn tất |

Dataset ID: `h1-zap-20261014-localhost-v1`.
Hash input A1: `5586507dc3cd3d292c7359df32760291a8eb2629cf115df88b9ecbefa751f5e7`.

`source_sha256` là hash bytes của **a1-input.json** mà Lân phải đưa vào A1; hash export Hùng riêng là `raw_zap_sha256`. Không chạy A1 trên raw export rồi sửa metadata cho khớp. Đổi scope/redaction/parser/ID cần tạo phiên bản dataset mới và khóa lại tất cả nhãn/run.

`.gitattributes` giữ nguyên bytes của pack và minh chứng khi clone trên Windows/Linux. Hash bytes của export/parser/redactor ghi môi trường đã dùng; các trường `raw_zap_content_sha256`, `normalizer_text_sha256`, `redactor_text_sha256` cho phép kiểm tra cùng nội dung khi Git đổi CRLF/LF. Hash input A1 vẫn luôn là hash bytes chính xác, không chuẩn hóa khi chấm.

Hùng đã có [setup_ZAP.md](../../setup_ZAP.md). Export chưa ghi chính xác commit SUT của scan và không chứa đủ full HTTP response cho mọi alert. Khi không đủ căn cứ, replay trên lab và lưu bằng chứng; không dùng risk/name làm kết luận.

## Quy trình độc lập

1. Như/Phát chốt scope, đơn vị instance và rubric trước khi đo. Mỗi người xem bằng chứng, không xem phiếu nhau hoặc output AI.
2. Như làm trên phiếu private. Với mỗi ID, ghi `true/false/unknown`, ưu tiên, lý do, bằng chứng và số giây thực đo. Trống nghĩa là chưa làm; thiếu bằng chứng dùng unknown, không ép false.
3. Khóa phiếu trước khi xem P2/AI. Cờ xác nhận là tuyên bố của người gán nhãn, tool không thể tự chứng minh tính độc lập.
4. Sau khi Phát cũng khóa, đối chiếu; hai người replay/chốt bất đồng thành nhãn chuẩn. Compare không tự chọn người đúng hoặc tự tạo ground truth.

Rubric theo đề xuất nhóm: P1 dễ khai thác/tác động cao; P2 dễ khai thác/tác động thấp; P3 khó khai thác/tác động cao; P4 khó khai thác/tác động thấp hoặc nghi false positive. **Nhóm cần duyệt trước khi dùng.** Alert thông tin không tự động là lỗi thật hoặc false positive; nhóm cần thống nhất cách gán và giải thích. Unknown có thể chưa có priority.

## Các cột phiếu

| Cột | Người kiểm thử ghi |
|---|---|
| `alert_id`, `risk` | Lấy từ dataset, không sửa |
| `is_real` | `true`, `false`, `unknown` |
| `priority` | P1–P4; unknown có thể trống |
| `reason` | Căn cứ kết luận hoặc lý do chưa đủ căn cứ |
| `evidence_ref` | Request/response/ảnh/log lab đã làm sạch, hoặc bằng chứng còn thiếu |
| `elapsed_seconds` | Giây thực đo, không dùng timing mẫu hoặc tự điền 0 |

Đo thêm thời gian xử lý thủ công end-to-end cho cùng tập alert đến danh sách cuối, tách khỏi tổng thời gian hai người tạo ground truth. Ghi rõ phạm vi setup/replay/adjudication, tránh so sánh hai công việc khác nhau.

## Lệnh thực hiện

Từ root repo, tạo phiếu riêng bằng lệnh sau (tool tạo thư mục và từ chối ghi đè):

Nếu đã có `Nhu/private/nhu-labels.csv`, tiếp tục điền file đó; không chạy lại cùng output hoặc xóa phiếu đang làm.

```powershell
python -m Nhu.N2_gan_nhan.labels prepare --dataset Nhu/N2_gan_nhan/data/h1-20261014/dataset.json --output Nhu/private/nhu-labels.csv
```

Như tự kiểm chứng/điền xong, chưa xem P2/AI, mới khóa:

```powershell
python -m Nhu.N2_gan_nhan.labels lock --dataset Nhu/N2_gan_nhan/data/h1-20261014/dataset.json --sheet Nhu/private/nhu-labels.csv --reviewer "Thạch Như - 23120312" --confirm-independent --output Nhu/private/nhu-labels.lock.json
```

Nhận bản khóa thật của Phát (không tạo thay Phát), rồi đối chiếu:

```powershell
python -m Nhu.N2_gan_nhan.labels compare --first Nhu/private/nhu-labels.lock.json --second Nhu/private/phat-labels.lock.json --output Nhu/private/disagreements.json
```

Compare báo bất đồng và độ khớp thô có tính unknown; không phải accuracy. Giữ CSV/file khóa nguyên bản và hash. Sau khi chốt mới dùng [hợp đồng nhãn chuẩn N3](../N3_benchmark_triage/README.md).

Tái lập pack từ export bằng parser A1 của Lân, không gọi model/mạng:

```powershell
python -m Nhu.N2_gan_nhan.prepare_zap --output-dir Nhu/outputs/h1-rebuilt
```

Tool kiểm tra scope cả site/instance, che secret theo parser Lân, không deduplicate, kiểm tra ID ổn định khi parse lại và không ghi đè. Bản chia sẻ vẫn cần người rà soát; raw export có giá trị token trong URL, không gửi trực tiếp cho model.
