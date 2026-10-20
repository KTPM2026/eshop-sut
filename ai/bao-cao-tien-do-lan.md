# Báo cáo tiến độ công việc của Nguyễn Nhật Lân

## Cập nhật 18/10/2026

- Đã khóa input 11 alert thật, manifest SHA-256 và hai bản review trống riêng tại [review_bundle_v1](A1_ai_triage/review_bundle_v1/README.md). Chưa có nhãn reviewer hoặc inference cloud.
- Entry point mới: `python -X utf8 -m ai.A2_fuzzer_benchmark.isolated_lab --output ai/outputs/offline-new-run.json`. Launcher dùng database tạm riêng, không reset database backend hiện hữu.
- Đã chạy HTTP thật 3 nhánh × 3 lượt trên lab tách biệt. [Kết quả mới](A2_fuzzer_benchmark/results/offline_v1.json): wordlist/fixed candidates/heuristic đạt checkpoint sau 5/6/2 request mỗi lượt; tổng 39 request tấn công + 36 request phụ benchmark. Request launcher chờ server sẵn sàng ở ngoài tổng này.
- Mỗi lượt reset và xác nhận WAF level 1; snapshot id/name giống nhau. Checkpoint từng attempt so sánh SQL ghép chuỗi và truy vấn parameterized. Oracle đề xuất cho H3 SQLi còn cần nhóm duyệt; không bao gồm XSS.
- Danh sách cũ tên `ai_static` đổi nhãn thành `fixed_candidates` vì chưa xác minh nguồn sinh AI. Nhánh feedback ghi đúng `heuristic_feedback`, không gọi cloud và không ghi đè cache L2.
- [Cache mới](A3b_video_cache/cache/offline_v1.json) có hash nguồn/payload. Công cụ replay kiểm tra hash, gắn nhãn replay và báo lỗi khi thiếu dữ liệu.
- Test mới bao phủ budget, nguồn cạn, WAF/baseline lỗi, timeout, checkpoint riêng từng attempt, tìm kiếm hợp lệ không phải SQLi, bundle không ghi đè và cache bị sửa.
- Kết quả kiểm thử cập nhật: **38/38 unittest pass** và 9/9 lượt benchmark HTTP thật đạt oracle đề xuất. Chưa phải kiểm thử model cloud.
- Còn cần: quyền/cấu hình/key cloud, nhãn độc lập, duyệt oracle và N3. Video/slide vẫn ngoài đợt này.

Phần từ đây trở xuống giữ báo cáo ngày 17/10. Đường chạy hiện tại dùng theo [README](README.md).

**MSSV:** 23120289  
**Ngày cập nhật:** 17/10/2026  
**Phạm vi:** A1, A2, A3a, A3b và phần báo cáo kỹ thuật liên quan  
**Ngoài phạm vi báo cáo này:** video demo và slide

## 1. Tổng quan

Phần công việc của Lân tập trung vào:

- AI Vulnerability Triage từ dữ liệu ZAP.
- Benchmark đối chứng cho Fuzzer.
- Giao diện/cấu hình AI dùng chung.
- Cache kết quả và chuẩn bị minh chứng dữ liệu.

Trong quá trình triển khai, nhóm đã bổ sung các tài nguyên thực tế:

- H1: report ZAP thật của EShop.
- H3: WAF/input filter lab của Hùng.
- L2: AI Fuzzer feedback loop của Long.

Vì vậy, phần triển khai hiện tại ưu tiên tích hợp các tài nguyên trên, thay vì
dùng các fixture/mock ban đầu để tạo kết quả thực nghiệm.

## 2. Những phần đã hoàn thành

### 2.1. A3a - Giao diện AI dùng chung

Đã có:

- Cấu hình provider, model, timeout, token limit và approval trong
  [`config.py`](A3a_ai_config/config.py).
- Hợp đồng dữ liệu Pydantic trong
  [`contracts.py`](A3a_ai_config/contracts.py).
- JSON Schema dùng chung tại
  [`contracts.json`](A3a_ai_config/contracts.json).
- Adapter AI trong [`client.py`](A3a_ai_config/client.py).
- Cơ chế chạy `mock` và `live`.
- Kiểm tra đầu vào/đầu ra theo schema.
- Không tự chuyển từ lỗi live sang mock.
- Không tự đóng hoặc xóa alert.
- Redaction best-effort cho API key, cookie, token và một số secret trong
  [`safety.py`](A3a_ai_config/safety.py).

Trạng thái thực tế:

- Đã kiểm thử adapter bằng HTTP transport giả.
- Chưa gọi API cloud thật.
- Model/provider/ngân sách vẫn cần nhóm xác nhận.

### 2.2. A1 - AI Vulnerability Triage

Đã triển khai:

- Parser JSON alert chuẩn hóa.
- Parser native ZAP có `site`, `alerts` và `instances`.
- Chuẩn hóa risk, CWE, URL, evidence và parameter.
- Sinh ID ổn định khi ZAP không cung cấp ID phù hợp.
- Từ chối record trùng ID.
- Lọc dữ liệu theo origin đầy đủ, ví dụ:
  `http://localhost:3000`.
- CLI Triage trong [`run.py`](A1_ai_triage/run.py).
- Công cụ tạo biểu mẫu review trong
  [`prepare_ground_truth.py`](A1_ai_triage/prepare_ground_truth.py).

Đã tích hợp report thật:

- Nguồn: [`2026-10-14-ZAP-Report-.json`](../alert/2026-10-14-ZAP-Report-.json).
- Scope: `http://localhost:3000`.
- Số record đã chuẩn hóa: **11 ZAP instances**.
- Output kiểm tra mapping:
  [`triage_real_backend_mock.json`](outputs/triage_real_backend_mock.json).

Output này vẫn là mock để kiểm tra pipeline, không phải kết quả inference AI.

### 2.3. Ground truth review

Đã tạo:

[`ground_truth_template.json`](A1_ai_triage/ground_truth_template.json)

File này chứa 11 alert thật thuộc backend EShop và các trường để Như/Phát
review độc lập:

- `is_real`
- `priority`
- `reviewer_reason`
- `evidence_reference`
- `review_status`

Các nhãn vẫn để trống có chủ ý. File này chưa phải ground truth và chưa được
dùng để tính Precision/Recall.

### 2.4. A2 - Benchmark Fuzzer

Đã sửa benchmark trong
[`benchmark_fuzzer.py`](../demo/ai_fuzzer/benchmark_fuzzer.py) để:

- Không còn hard-code `success` và số request.
- Gọi trực tiếp H3 local lab.
- Dùng implementation L2 hiện có của Long cho nhánh feedback.
- Chạy ba nhánh:
  - `wordlist_static`
  - `ai_static`
  - `ai_feedback`
- Chạy ba lượt cho mỗi nhánh.
- Ghi từng payload và HTTP status.
- Ghi số request đến lần bypass đầu tiên.
- Kiểm tra baseline trước khi đánh giá kết quả.
- Chỉ công nhận bypass khi:
  - Baseline trả về `[]`.
  - Ứng viên trả về HTTP 200.
  - Backend trả về JSON không rỗng.

Kết quả nằm tại:

[`benchmark_results.json`](../demo/ai_fuzzer/benchmark_results.json)

Kết quả local lab hiện tại:

| Nhánh | Số lượt | Request đến bypass | Kết quả |
|---|---:|---:|---|
| Wordlist tĩnh | 3 | 5, 5, 5 | 3/3 thành công |
| AI tĩnh | 3 | 6, 6, 6 | 3/3 thành công |
| AI feedback | 3 | 2, 2, 2 | 3/3 thành công |

Lưu ý: nhánh AI feedback hiện chạy bằng **offline heuristic** của L2, không
phải inference cloud. Kết quả chỉ phản ánh local WAF lab hiện tại, không được
ngoại suy thành kết luận tổng quát về mọi WAF.

### 2.5. H3 và L2 đã được sử dụng

H3 được dùng từ:

- [`waf_middleware.js`](../backend/waf_middleware.js)
- [`server_fuzzer_lab.js`](../backend/server_fuzzer_lab.js)

L2 được dùng từ:

- [`ai_fuzzer.py`](../demo/ai_fuzzer/ai_fuzzer.py)

Smoke test H3 đã xác nhận:

- Request hợp lệ: HTTP 200.
- SQLi cơ bản: HTTP 403.
- Payload inline comment: HTTP 200.
- Response bypass có dữ liệu backend.

### 2.6. A3b - Cache dữ liệu

Đã cập nhật cache Fuzzer tại:

[`fuzzer_result.json`](A3b_video_cache/cache/fuzzer_result.json)

Cache ghi rõ:

- `data_origin: real_local_h3_l2_run`
- `is_replay: false`
- Chế độ `offline_heuristic`
- Log HTTP 403 rồi HTTP 200
- Checkpoint backend

Cache Triage vẫn là template rỗng vì chưa có inference live và ground truth
đã khóa.

## 3. Những phần đang thực hiện hoặc còn chờ

### 3.1. A1 inference live

Chưa thực hiện vì cần:

- Nhóm duyệt provider/model.
- API key hợp lệ được cấp qua biến môi trường.
- Xác nhận được phép gửi alert đã làm sạch ra dịch vụ cloud.
- Chốt ngân sách và giới hạn gọi API.

Không dùng output mock thay cho inference live.

### 3.2. Ground truth và benchmark Triage

Còn chờ:

1. Như review độc lập lần 1.
2. Phát review độc lập lần 2.
3. Hai bên khóa nhãn ban đầu trước khi xem output AI.
4. Chốt các trường hợp bất đồng/chưa đủ bằng chứng.
5. Như thực hiện N3:
   - Precision.
   - Recall.
   - False positive/false negative.
   - Alert thật bị xếp thấp hoặc bị bỏ sót.
   - Thời gian thủ công và thời gian có review AI.
   - Tối thiểu ba lượt chạy nếu nhóm giữ yêu cầu trong proposal.

### 3.3. Tích hợp A3a với L2

Hiện L2 đang dùng Groq hoặc heuristic offline, trong khi A3a của Lân đang có
adapter OpenAI. Cần nhóm thống nhất một trong các hướng:

- Giữ adapter riêng của L2 và ghi rõ provider.
- Chuyển L2 sang `AIClient.suggest_payload()`.
- Tạo adapter chung hỗ trợ provider đã được nhóm duyệt.

Không tự đổi provider trong benchmark vì sẽ làm thay đổi điều kiện so sánh.

### 3.4. Benchmark Fuzzer cần củng cố thêm

Đã có benchmark 3 lượt/nhánh, nhưng trước khi dùng làm kết quả cuối cần:

- Chốt chính thức oracle SQLi/XSS với nhóm.
- Xác nhận reset/seed và phiên bản rule H3.
- Ghi SUT commit, WAF level và cấu hình chạy.
- Tách rõ request tới SUT và request tới AI API.
- Nếu dùng LLM live, ghi model, chi phí, lỗi và thời gian gọi.
- Xác nhận kết quả bypass bằng checkpoint được Như/Phát duyệt.

### 3.5. Video và slide

Không thực hiện trong đợt này theo phạm vi đã thống nhất.

## 4. Cách chạy kiểm thử và tái lập

Tất cả lệnh dưới đây chạy từ thư mục:

```powershell
cd seminar\eshop-sut
```

### 4.1. Cài dependency Python

Nếu môi trường Python chưa có dependency:

```powershell
python -m pip install -r ai\requirements.txt
```

### 4.2. Chạy toàn bộ test workspace

Trên Windows, nên chạy từ thư mục `eshop-sut`:

```powershell
python -X utf8 -m unittest discover -s ai\tests -v
```

Kết quả đã xác nhận:

```text
Ran 31 tests
OK
```

Các test bao phủ parser ZAP, origin filter, schema, redaction, mock/live
guard, A2 guard, cache provenance và CLI.

### 4.3. Kiểm tra cú pháp

```powershell
node --check backend\waf_middleware.js
node --check backend\server_fuzzer_lab.js
python -m py_compile `
  ai\A1_ai_triage\parser.py `
  ai\A1_ai_triage\run.py `
  ai\A1_ai_triage\prepare_ground_truth.py `
  demo\ai_fuzzer\ai_fuzzer.py `
  demo\ai_fuzzer\benchmark_fuzzer.py
```

### 4.4. Chạy A1 trên report ZAP thật ở chế độ mock

```powershell
python -X utf8 -m ai.A1_ai_triage.run `
  --mode mock `
  --origin http://localhost:3000 `
  --input alert\2026-10-14-ZAP-Report-.json `
  --output ai\outputs\triage_real_backend_mock.json
```

Lệnh này kiểm tra parser và mapping, không gọi API cloud.

### 4.5. Tạo lại ground-truth template

```powershell
python -X utf8 -m ai.A1_ai_triage.prepare_ground_truth `
  --input alert\2026-10-14-ZAP-Report-.json `
  --output ai\A1_ai_triage\ground_truth_template.json `
  --origin http://localhost:3000
```

Không điền nhãn tự động vào file này.

### 4.6. Cài dependency và chạy H3 lab

Nếu dependency Node chưa được cài:

```powershell
cd backend
npm.cmd install
cd ..
```

Khởi động server:

```powershell
node backend\server_fuzzer_lab.js
```

Mở terminal khác và kiểm tra nhanh:

```powershell
Invoke-RestMethod http://localhost:3001/api/waf/status
Invoke-WebRequest `
  "http://localhost:3001/api/products?search=phone" `
  -UseBasicParsing
```

Sau khi kiểm tra xong, dừng đúng process server đang chạy.

### 4.7. Chạy benchmark ba nhánh

Trong khi H3 server đang chạy:

```powershell
python -X utf8 demo\ai_fuzzer\benchmark_fuzzer.py
```

Kết quả được ghi vào:

```text
demo\ai_fuzzer\benchmark_results.json
demo\ai_fuzzer\fuzzer_cache.json
```

Benchmark hiện sử dụng local lab và heuristic offline, không cần API key.

## 5. Kết luận trạng thái

### Đã hoàn thành ở mức có thể bàn giao

- A3a: cấu hình, schema, adapter và kiểm thử.
- A1: parser và pipeline đã tích hợp được report ZAP thật theo backend origin.
- Ground-truth template cho reviewer độc lập.
- H3 smoke test.
- A2 benchmark 3 lượt/nhánh trên H3/L2 local lab.
- Cache Fuzzer có provenance.
- 31/31 unittest pass.

### Chưa được phép kết luận

- AI Triage có Precision/Recall đạt mục tiêu.
- AI Triage đạt Recall 90%.
- AI tiết kiệm 50% thời gian.
- AI Fuzzer live tốt hơn baseline trong điều kiện cloud.
- Kết quả local heuristic có thể tổng quát hóa sang hệ thống khác.

Các kết luận trên chỉ được đưa vào báo cáo cuối sau khi nhóm khóa ground truth,
chốt cấu hình AI và hoàn thành các lượt benchmark được phê duyệt.
