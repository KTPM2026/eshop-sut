# N3: Bộ chấm benchmark AI Triage

**Đã lập trình bộ chấm offline, chưa có benchmark thật.** Không gọi API, không phân loại/prompt lại alert và không sửa A1. Tương thích hợp đồng `lan-ai-v1-proposed` của [A1 hiện có trong main](../../Lan/A1_ai_triage/README.md).

## 1. Đầu vào chờ bàn giao

| Đầu vào | Điều kiện |
|---|---|
| Dataset normalized | Hợp đồng [N2](../N2_gan_nhan/README.md), cùng ID và hash file nguồn H1 mà A1 đã dùng |
| Nhãn chuẩn | Như/Phát gán độc lập, khóa trước khi xem AI, kiểm chứng/chốt bất đồng; unknown giữ null |
| Ít nhất ba output A1 | Ba lượt độc lập, cùng provider/model/config và hash nguồn; có đủ mọi ID, không replay |
| Timing sidecar | Thời gian toàn pipeline/inference có I/O và người review từng lượt; xác nhận review đã hoàn tất |
| Protocol | Nhóm chốt baseline, rubric, cách chấm abstain/unknown và phạm vi tính thời gian trước khi chạy |

Dataset thật đã chuẩn bị tại [N2/data/h1-20261014](../N2_gan_nhan/data/h1-20261014): 29 ID từ parser của Lân. Lân dùng **a1-input.json** làm input A1; N3 dùng **dataset.json**. Hai bên phải khớp hash `5586507dc3cd3d292c7359df32760291a8eb2629cf115df88b9ecbefa751f5e7`, không dùng hash raw export thay thế.

N3 không tự tạo ground truth hoặc đo lại inference từ file cache. Adapter N2 chỉ lọc scope và gọi parser H1/A1 sẵn có, không viết lại logic Triage. Các field metadata là khai báo của người cung cấp, không thay bằng chứng thực nghiệm. Chỉ chạy AI sau khi Như/Phát đã khóa nhãn và nhóm duyệt protocol/model.

## 2. Tệp nhãn chuẩn

[ground_truth.template.json](templates/ground_truth.template.json) là khung **rỗng và chưa được chấp nhận**. Khi nhóm thực sự hoàn tất, điền:

- `schema_version: nhu-benchmark-v1-proposed`.
- `_meta.dataset_id/source_sha256/data_origin` trùng dataset; nguồn thật dùng `real_zap`.
- `_meta.review_status: adjudicated`, `human_adjudication_confirmed: true` chỉ sau khi đã chốt.
- `_meta.reviewers`: tên hai người khác nhau; `independent_lock_sha256`: SHA256 của hai file JSON khóa nhãn gốc. Ghi hash bằng `Get-FileHash -Algorithm SHA256` và dùng hex viết thường. Hash không chứng minh hai người làm độc lập.
- `labels`: mỗi ID có `is_real: true/false/null`, `priority: P1–P4` (unknown có thể null), `reason`, `evidence_ref` từ người kiểm chứng.

Không tự chuyển mọi null thành false để chạy được. Chưa chốt thì giữ trạng thái đó và ghi giới hạn báo cáo.

## 3. Manifest và timing

[manifest.template.json](templates/manifest.template.json) chỉ là khung. Mọi đường dẫn input tính tương đối từ thư mục chứa manifest. Cấu trúc một run:

```json
{
  "run_id": "a1-run-01",
  "result_path": "a1_run_01.json",
  "inference_seconds": null,
  "review_seconds": null,
  "review_completed": false
}
```

Thêm ít nhất ba run **thật** trong `runs`, điền số giây đã đo. `protocol_approved` mặc định false; chỉ bật khi nhóm đã duyệt. `manual_total_seconds` là thời gian xử lý thủ công cùng tập alert đến danh sách cuối có thể so sánh; nếu chưa đo giữ null. Timing null/thiếu review bị từ chối trong chế độ thật. Không lấy các số ví dụ trong fixture làm timing thật.

Thời gian AI để so sánh = `inference_seconds + review_seconds`. Dù tên field là inference, phạm vi đo đề xuất phải bao gồm toàn pipeline A1 và I/O, không chỉ phần sinh token. N2/P2/adjudication, setup, chi phí API nên báo riêng và thống nhất có tính hay không; không trộn tổng thời gian hai người tạo ground truth với một pipeline AI một người review. Ghi rõ việc người review đã biết nhãn chuẩn có thể tạo learning bias.

Chạy sau khi có đủ dữ liệu:

```powershell
python -m Nhu.N3_benchmark_triage.run --manifest Nhu/private/manifest.json --output-dir Nhu/outputs/benchmark-real-01
```

Output `benchmark.json` có metadata/provenance, baseline, từng lượt và summary; `benchmark.csv` chứa chỉ số từng lượt. Không ghi đè báo cáo cũ. CSV dùng ô trống cho chỉ số null; giữ kèm JSON để đọc đúng nguồn và mẫu số.

## 4. Định nghĩa chỉ số, CHƯA chốt với nhóm

Lớp dương là **lỗ hổng thật**. Trên tập nhãn chuẩn true/false:

| Chỉ số | Cách tính/ý nghĩa |
|---|---|
| TP/FP/TN/FN | FN ở trường `fn_explicit_false` chỉ là AI kết luận false trên nhãn thật |
| Precision | `TP / (TP + FP)` |
| Recall bảo thủ | `TP / tổng lỗi thật có nhãn chuẩn`; AI null trên lỗi thật vẫn nằm trong mẫu số, không được loại để nâng Recall |
| Abstain | Đếm riêng AI null trên truth true và false; không coi null là false positive |
| Coverage | Số AI đã kết luận true/false / số truth đã rõ |
| Priority accuracy | Số P1–P4 khớp truth / số truth đã rõ; kể cả AI abstain classification nhưng vẫn gán priority |
| Truth unknown | Không tham gia chấm classification/priority; báo `excluded_unresolved_truth` và tổng record |
| Chỉ số an toàn | Số lỗi thật bị gán false, P4, hợp hai tập không đếm trùng; lỗi thật P1/P2 bị xuống P3/P4; ID để review |
| Tiết kiệm thời gian | `(manual_total - AI_total) / manual_total`; manual thiếu/0 hoặc chưa review thì null, có thể âm nếu AI chậm hơn |

Mẫu số 0 trả **null**, không tự gọi là 0%/100%. Recall này đo AI **nhận diện true**, không phải số alert chương trình giữ lại: A1 luôn phải giữ mọi alert để người review.

Summary chỉ mean/min/max và số lượt xác định/không xác định; không tự kiểm định thống kê hay kết luận ba lượt là đủ để suy rộng. JSON phân biệt metric undefined và zero.

## 5. Baseline risk đề xuất

| ZAP risk | is_real baseline | Priority baseline |
|---|---|---|
| High | true | P1 |
| Medium | true | P2 |
| Low | false | P3 |
| Informational | false | P4 |
| Unknown | null | P3 |

Đây là quy tắc đối chứng đơn giản trong tinh thần proposal, **không phải nhãn chuẩn** hay cách N2 phải gán. Cả classification mapping, priority mapping và cách chấm abstain cần khóa trước khi xem số liệu. Baseline không có timing đo thật trong code; báo cáo không tự bịa thời gian baseline.

## 6. Kiểm tra đầu vào và giới hạn

Scorer từ chối thiếu/thừa/trùng ID; hash nguồn khác; số record sai; JSON A1 không đủ đúng sáu trường; kiểu/enum/confidence sai; replay; ít hơn ba lượt; trùng run ID/thời điểm; khác cấu hình giữa lượt. Chế độ thật cần cờ live/inference, nguồn không synthetic, cấu hình đã duyệt và timing có review. Không xuất key hoặc URL cấu hình có thông tin đăng nhập/query; lỗi CLI không in nguyên dữ liệu.

Không thể dùng các cờ/hash để chứng minh một run thực sự đã chạy, một nhãn thực sự độc lập hoặc bằng chứng đúng. Lưu log/timestamp/config và video thật; chủ phần chịu trách nhiệm về dữ liệu. Cùng kết quả ba lượt không bị xem là gian lận nếu metadata các lượt thật khác nhau, nhưng không được sửa timestamp của cache để vượt kiểm tra.

## 7. Mẫu kỹ thuật và kiểm thử

```powershell
python -m Nhu.N3_benchmark_triage.make_sample --output-dir Nhu/outputs/sample-input
python -m Nhu.N3_benchmark_triage.run --manifest Nhu/outputs/sample-input/manifest.json --allow-synthetic --output-dir Nhu/outputs/sample-report
python -X utf8 -m unittest discover -s Nhu/tests -v
```

Fixture cố ý có TP/FP/FN/TN, AI abstain và truth unknown để test công thức. Mọi nhãn/timing/output đều **tự tạo**, không phải A1 đã chạy, không phải Như/Phát gán nhãn hoặc review thật. `--allow-synthetic` chỉ cho phép chạy thử, không nâng thành benchmark thật, dù mẫu có đủ ba tệp.

Đề xuất phương pháp dựa trên [proposal nhóm](https://github.com/KTPM2026/seminar/blob/main/docs/ai_proposal.md); phần thực thi/ràng buộc ở [scoring.py](scoring.py), không phải thuật toán phân loại của Lân.
