# Kiểm tra hiện trạng và kế hoạch hoàn thiện phần Lân

## Cập nhật thực hiện — 20/10/2026

Theo yêu cầu tiếp tục với cấu hình `ai/.env`, đã triển khai CLI live có dotenv/checkpoint/resume; smoke test và hoàn tất dataset 11 alert; benchmark cloud 3 lượt/nhánh trên lab tách biệt; cache thật có hash; sửa playback cũ để không tự tạo thành công/tỷ lệ cố định. Xem [báo cáo live](A4_slide_baocao/bao-cao-live-2026-10-20.md) và [README](README.md).

- M0: giữ artifact offline/mock và input review đã khóa; kết quả live dùng tên mới.
- M1 phần phần mềm/A3a: cấu hình thực tế hoạt động với Groq, checkpoint từng alert; lỗi không fallback; lưu usage và hash. Hai bản review vẫn trống.
- M2: thực nghiệm LLM đã chạy 9 lượt; wordlist thành công 3/3, AI tĩnh 0/3, feedback 0/3 (model dừng). Oracle SQLi vẫn cần người phụ trách rà soát; chưa đánh giá XSS.
- M3 phần inference: có output thật và chạy các lượt độc lập; N3/Precision/Recall, chốt nhãn và đo thời gian thủ công vẫn cần Như/Phát.
- M4: cache live và báo cáo kỹ thuật có nguồn; replay không gửi mạng. Clip L3/video ghép và mẫu slide chung chưa được cung cấp.

Các mô tả thiếu key/chưa gọi cloud dưới đây là lịch sử. Không dùng đầu ra model làm nhãn chuẩn.

## Kết quả thực hiện phần không bị block — 18/10/2026

- M0: đã thêm trạng thái hiện tại ở README/báo cáo, đánh dấu kế hoạch và scaffold cũ là lịch sử, giữ artifact cũ nguyên vẹn. Điểm còn mở về tài liệu gốc/provider/oracle vẫn chưa tự xác nhận thay nhóm.
- M1: đã tạo `A1_ai_triage/review_bundle_v1` với 11 alert, SHA-256 và hai bản review độc lập trống. Không điền nhãn, không gửi cho người khác và chưa chạy cloud. Cải tiến resume theo từng alert cho A1 live vẫn là việc tiếp theo; CLI A1 hiện chưa có checkpoint trung gian.
- M2: đã bổ sung `offline.py` và `isolated_lab.py` làm đường thực nghiệm offline chính. Budget đồng nhất, nguồn cạn/budget hết/lỗi có trạng thái riêng; reset WAF trước mỗi lượt; SQLi oracle SQLite đối chiếu truy vấn parameterized; checkpoint riêng từng attempt; đổi nhãn nguồn cố định và heuristic đúng thực tế. Không sửa logic feedback/replay riêng của Long.
- Đã chạy HTTP thật 3 lượt/nhánh trên server sao chép vào thư mục tạm với database riêng, cổng trống và tự dừng process. Kết quả `A2_fuzzer_benchmark/results/offline_v1.json`: 5/6/2 request tấn công tới checkpoint; 39 request tấn công + 36 request phụ benchmark. Snapshot nhất quán, không gọi cloud. Request launcher kiểm tra sẵn sàng nằm ngoài tổng benchmark. Oracle vẫn cần nhóm rà soát.
- M4: thêm envelope cache có hash nguồn/payload và công cụ replay kiểm tra toàn vẹn, không gọi mạng, không tự sinh thành công. Cache A1 vẫn chờ inference, không chờ input H1 nữa. Báo cáo cuối còn chờ live/nhãn/N3.
- Kiểm thử sau triển khai: **38/38 unittest pass**, gồm 7 test mới; benchmark HTTP thật thành công 9/9 lượt. `git diff --check` qua. Các mốc này xác nhận phần offline, không xác nhận chất lượng LLM hoặc nhãn chuẩn.

Các mục tiếp theo mô tả phát hiện trước triển khai và tiêu chí nghiệm thu tổng thể; dùng phần cập nhật này cùng README để phân biệt việc đã làm với việc còn mở.

Ngày kiểm tra: 18/10/2026. Nguồn: ảnh nhận xét tiến độ, `00_ke-hoach-lam-viec.md`, `bao-cao-tien-do-lan.md` và mã nguồn trong checkout hiện tại.

Tài liệu này là kế hoạch thực hiện đề xuất, chưa phải xác nhận lựa chọn provider, ngân sách hay deadline của nhóm. Phạm vi chính là A3a, A1, A2, cache A3b và báo cáo kỹ thuật. Video/slide được để thành hạng mục bàn giao riêng vì báo cáo hiện tại loại chúng khỏi đợt này. Chưa sửa implementation hoặc gọi API cloud trong lần kiểm tra này.

## 1. Kết quả đối chiếu

| Phần | Bằng chứng đã kiểm tra | Đánh giá nhận xét trong ảnh |
|---|---|---|
| A3a | Có config, contracts, schema, adapter, redaction và test HTTP giả | 85% là ước lượng tiến độ hợp lý; chưa có bằng chứng kiểm thử cloud thật, chưa thống nhất đường gọi AI với L2 |
| A1 | Parser đọc report thật và lọc đúng 11 instance tại `http://localhost:3000`; template review chưa có nhãn | 60% phản ánh phần pipeline; chưa hoàn tất inference, đối chiếu nhãn và đánh giá N3 |
| A2 | JSON lưu 9 lượt, 39 lần thử payload; số request đến thành công là 5/6/2 cho ba nhánh ở cả ba lượt | Có thực nghiệm local được lưu, nhưng 85% chưa phản ánh đủ thiếu sót phương pháp và provenance; chưa thể dùng làm bằng chứng LLM cloud hiệu quả hơn |
| A3b | Cache Fuzzer có timestamp, mode offline và log 403 → 200; cache Triage rỗng | 50% chỉ nên hiểu là đã có một phần dữ liệu; provenance Fuzzer chưa đủ hash/config/checkpoint để kiểm toán độc lập |
| Doc | Báo cáo mô tả khá rõ giới hạn mock/offline/live | 90% phù hợp với bản báo cáo tiến độ, không tương đương hoàn tất báo cáo thực nghiệm cuối |

Không có tiêu chí trọng số để kiểm chứng chính xác các tỷ lệ phần trăm. Nên quản lý bằng điều kiện nghiệm thu dưới đây.

Kiểm tra đã chạy: `python -X utf8 -m unittest discover -s ai/tests -v` — **31/31 pass**. Các test này không xác nhận chất lượng inference và chưa kiểm chứng phương pháp của benchmark thực trong `demo/ai_fuzzer/benchmark_fuzzer.py`. Số liệu benchmark được đọc từ artifact đã lưu; chưa chạy lại H3 trong đợt kiểm tra này.

## 2. Các điểm cần sửa trước khi kết luận hoàn thành

1. **Tài liệu trạng thái lệch nhau:** kế hoạch ngày 16/10 còn ghi chờ H1/H3/L2; báo cáo ngày 17/10 đã tích hợp. README có bảng cũ rồi bổ sung cập nhật ở cuối. Một số liên kết tới `docs/ai_proposal.md` và `docs/de-cuong-seminar.md` không tồn tại trong checkout này; cần tìm tài liệu gốc hoặc ghi rõ chưa đối chiếu được phạm vi chính thức.
2. **Có hai đường A2:** `ai/A2_fuzzer_benchmark/runner.py` vẫn luôn báo blocked; script thực nghiệm nằm ở `demo/ai_fuzzer/benchmark_fuzzer.py`. Test đang bảo vệ scaffold blocked, không phải runner thực nghiệm. Cần chọn một entrypoint chính và mô tả rõ vai trò đường còn lại.
3. **Nguồn AI tĩnh chưa chứng minh:** `AI_PREGENERATED_PAYLOADS` là list literal, chưa kèm provider/model/prompt/output gốc/hash. Trước khi bổ sung nguồn, chỉ gọi là danh sách ứng viên cố định.
4. **Budget chưa đồng nhất:** hai nhánh tĩnh có 7 và 6 ứng viên, không nhận budget; feedback nhận 50. Cần phân biệt trần N, số ứng viên có sẵn, số request thực gửi và lý do dừng. Không cần cố gửi đủ N nếu đã đạt oracle, nhưng phải công bố cùng quy tắc dừng và giới hạn cho mọi nhánh.
5. **Oracle chưa đủ đặc hiệu:** baseline rỗng và response ứng viên có list không rỗng chưa tự chứng minh SQLi; truy vấn hợp lệ cũng có thể trả dữ liệu. Cần checkpoint dựa trên hiệu ứng SQLi đã xác minh, đối chứng và dữ liệu seed. Benchmark hiện chỉ kiểm tra SQLi, chưa có cơ sở kết luận XSS.
6. **Log feedback suy diễn thành công:** benchmark dùng cờ thành công cuối phiên để gán `bypass` cho các log HTTP 200 không bị chặn; L2 không lưu response/checkpoint từng lần thử. Phải ghi checkpoint tại thời điểm nhận response và dùng kết quả riêng của từng attempt.
7. **Điều kiện chạy chưa khóa:** runner không chủ động reset/kiểm tra WAF trước từng lượt; thiếu SUT commit, hash rule, seed, thứ tự chạy và bộ đếm request phụ. Ba lần lặp giống nhau của heuristic/danh sách cố định chủ yếu chứng minh lặp lại, chưa thể hiện biến thiên của LLM.
8. **Live có thể trộn heuristic:** L2 đang tự fallback khi lỗi Groq; benchmark hiện ép offline nên không có cloud. Khi bổ sung live cần ghi mode từng attempt, lỗi, token/call count và tách lượt bị fallback khỏi nhóm live. Không suy luận provider từ tên biến key; dùng credential đúng provider.
9. **Cache/replay chưa hoàn chỉnh:** cache Fuzzer thiếu source hash và bằng chứng checkpoint có thể kiểm tra lại; cache Triage còn ghi chờ input thật dù đã có H1. Playback L2 còn tự tạo kịch bản thành công khi thiếu cache và in tỷ lệ tiết kiệm cố định 85.7%; cần phối hợp Long sửa trước khi dùng làm minh chứng. Với số đếm đang lưu, 2 so với 5 là giảm 60%, 2 so với 6 là khoảng 66.7%, chỉ trong lab offline này.

## 3. Kế hoạch theo thứ tự ưu tiên

### M0 — Khóa hiện trạng và đồng bộ tài liệu

- Lân lưu danh sách artifact hiện có, SHA-256 của report ZAP, dữ liệu chuẩn hóa, prompt/schema, benchmark và cache; không ghi đè bằng lượt chạy mới.
- Cập nhật kế hoạch/README/báo cáo về cùng trạng thái; thay mô tả “400 dòng log” bằng “382 dòng JSON, 9 lượt, 39 lần thử payload” cho artifact hiện tại. Phân biệt dòng văn bản với số request.
- Chốt entrypoint benchmark chính; ghi scaffold cũ là template hoặc chuyển sang gọi runner chính sau khi tích hợp.
- Tạo danh sách quyết định còn mở: provider/model, hạn mức, dữ liệu được gửi cloud, N, oracle, scope SQLi/XSS, deadline.

**Nghiệm thu:** người khác đọc README xác định đúng lệnh chạy, dữ liệu thật/mock/offline/live và các phần chưa đo; không còn thông tin chờ H1/H3/L2 đã lỗi thời.

### M1 — Khóa dataset và chuẩn bị A3a/A1 live

- Lân xuất input đã làm sạch gồm đúng 11 alert, khóa ID + hash + origin; giữ liên kết về nguồn ZAP và thông tin SUT/ZAP nếu thu thập được.
- Bàn giao hai bản review riêng cho Như/Phát. Mỗi reviewer lưu nhãn, lý do, evidence và thời gian độc lập; khóa nhãn trước khi xem output AI, sau đó xử lý bất đồng bằng bản tổng hợp có lịch sử.
- Chuẩn bị cấu hình live và kiểm tra lỗi timeout/429/refusal/schema sai; bổ sung lưu trạng thái theo alert và khả năng tiếp tục để lỗi ở cuối không làm mất toàn bộ kết quả trước đó.
- Nhóm chọn provider/model và cách tích hợp A3a/L2. Lân chuẩn bị cấu hình tái lập; Long phụ trách thay đổi feedback loop L2.

**Nghiệm thu:** dataset/ID ổn định, có hai bản review độc lập và quy tắc xử lý nhãn chưa xác định; cấu hình không chứa key; test HTTP giả xác nhận không fallback mock và không mất kết quả thành công khi một alert lỗi.

**Phụ thuộc bên ngoài:** tài khoản/key, quyền gửi dữ liệu và hạn mức cloud cần chủ tài khoản/nhóm xác nhận trước lượt gọi có phí. Chưa có các thông tin này vẫn làm được M0, chuẩn bị M1 và phần offline của M2.

### M2 — Củng cố A2 trước khi chạy lại

- Lân cùng Hùng/Như/Phát xác định oracle SQLi, seed và đối chứng. Nếu chưa có endpoint/oracle XSS thì công bố benchmark chỉ SQLi.
- Chuẩn hóa interface ba nhánh với cùng target, WAF rule/level, seed, trần request và quy tắc dừng; ghi rõ `success`, `budget_exhausted`, `source_exhausted`, `error`.
- Kiểm tra/reset WAF trước mỗi lượt, ghi trạng thái sau reset. Tách request tấn công, baseline, reset/xác minh và AI API; ghi tổng số request thực thay vì chỉ số đến bypass.
- Lưu nguồn danh sách tĩnh; nếu dùng AI sinh trước thì lưu prompt/model/thời điểm/hash và lần gọi sinh danh sách. Giữ heuristic làm nhóm đối chứng riêng, nhãn live chỉ dùng cho lượt thực sự gọi LLM.
- Phối hợp Long lưu checkpoint từng attempt, provider/mode, lỗi/fallback và latency. Không gán thành công từng attempt từ cờ cuối phiên.
- Chạy test có ý nghĩa: HTTP 200 nhưng không có hiệu ứng; baseline lỗi; WAF tắt; timeout; nguồn cạn; vượt budget; LLM lỗi/fallback; log trước lần thành công không bị đánh dấu thành công sai.
- Sau khi các guard qua, chạy ít nhất 3 lượt/nhánh nếu nhóm giữ yêu cầu này; thay đổi hoặc luân phiên thứ tự nhánh, lưu log thô và manifest cấu hình. Lượt live thực hiện sau khi đã chốt quyền dùng cloud.

**Nghiệm thu:** từ log và checkpoint có thể tự tính lại request-to-first-success và success rate; mọi nhánh có điều kiện so sánh đã công bố; lượt lỗi/không thành công vẫn được giữ; kết quả cũ được bảo toàn như thực nghiệm sơ bộ.

### M3 — Chạy A1 và bàn giao đánh giá N3

- Sau khi M1 đủ điều kiện, smoke test live một alert đã làm sạch rồi chạy đủ dataset; kiểm tra đủ 11 ID, output hợp lệ, không bỏ alert và không thay đổi nhãn reviewer.
- Lưu run ID, input/prompt/schema hash, cấu hình, thời điểm, lỗi, latency và usage/call count khi API cung cấp. Nếu cần 3 lượt thì giữ từng lượt độc lập với cùng dataset/cấu hình.
- Bàn giao output cho Như tính Precision/Recall, FP/FN và mức ưu tiên theo quy tắc đã thống nhất. Nhãn chưa đủ bằng chứng không bị ép thành âm tính; công bố số mẫu bị loại/chưa xác định và cách xử lý.
- Đo thời gian thủ công và có AI theo protocol Như thống nhất, kiểm soát ảnh hưởng do đã xem trước cùng alert; không suy ra tiết kiệm thời gian từ latency API.

**Nghiệm thu:** có output inference thật truy vết được và bảng N3 gắn đúng phiên bản nhãn; mọi con số có mẫu số/quy tắc tính, không mặc định đạt Recall 90% hoặc giảm 50% thời gian.

### M4 — Hoàn thiện cache và báo cáo bàn giao

- Sinh cache Triage từ output A1 đã kiểm tra, giữ đánh giá N3 thành artifact liên kết riêng. Cache inference không cần chờ N3 mới được lưu; chỉ kết luận chất lượng mới cần N3.
- Sinh cache Fuzzer từ lượt M2, kèm timestamp, source/config hash, mode, checkpoint và nguồn kết quả. Khi replay phải hiển thị nhãn replay, không biến heuristic thành cloud live.
- Phối hợp Long để thiếu cache thì báo thiếu dữ liệu, không tự sinh phiên thành công; mọi tỷ lệ hiển thị tính từ artifact liên quan.
- Viết báo cáo cuối gồm phương pháp, dataset, cấu hình, bảng kết quả, lỗi, giới hạn và cách tái lập; đồng bộ README và bảng trạng thái bằng chứng.

**Nghiệm thu:** người nhận tái tính được bảng từ log; replay không gửi mạng và không tạo kết quả giả; không chứa secret; phân biệt rõ kết quả lab offline với LLM live và template với nhãn chuẩn.

Video/slide A4: chỉ đưa vào lịch khi xác nhận lại phạm vi, nhận clip L3 và mẫu chung từ Long/Phát. Không xem việc chưa làm video/slide là lỗi của báo cáo kỹ thuật hiện tại.

## 4. Phối hợp và đường phụ thuộc

| Chủ việc | Đầu vào/bàn giao cần thiết |
|---|---|
| Lân | Khóa input/ID, A3a/A1, runner A2, provenance cache, đồng bộ tài liệu |
| Hùng | Phiên bản H1/H3/SUT, seed/reset và đối chứng hiệu ứng SQLi |
| Long | Xác nhận đường AI L2, log checkpoint/mode từng attempt, hành vi fallback/replay |
| Như/Phát | Hai bản review độc lập, giải quyết bất đồng, duyệt oracle; Như phụ trách N3 |
| Nhóm/chủ tài khoản | Provider/model, quyền gửi dữ liệu, hạn mức và deadline |

Đường Triage: **M0 → M1 → M3 → M4**. Đường Fuzzer: **M0 → M2 → M4**. Hai đường có thể tiến hành song song về công việc; chưa có hạn nộp được cung cấp nên kế hoạch chưa gán ngày hoàn thành. Ưu tiên bắt đầu bằng đồng bộ tài liệu, khóa 11 ID và sửa tính hợp lệ của A2; key cloud không phải phụ thuộc của các bước này.
