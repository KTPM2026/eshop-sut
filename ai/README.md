# Không gian làm việc của Nguyễn Nhật Lân

## Cập nhật live — 20/10/2026

A3a/A1 đã gọi thật model `qwen/qwen3.8-27b` tại Groq qua OpenAI-compatible API trong `ai/.env`: hoàn tất 3 lượt, mỗi lượt đủ 11/11 ID. CLI mới đọc dotenv tường minh, lưu checkpoint mỗi alert, resume bỏ qua ID đã thành công, giữ lỗi/usage/latency và hash input/prompt/schema. Không ghi key vào artifact.

A2 đã chạy 3 lượt/nhánh trên lab/database tạm riêng: wordlist đạt oracle 3/3, AI tĩnh 0/3 (hết 7 ứng viên), AI feedback 0/3 (model chủ động dừng). Trần 50 request tấn công/lượt; feedback tối đa 10 API call/lượt; danh sách AI tĩnh sinh một lần và dùng chung. Có 39 request tấn công + 36 request phụ benchmark; 7 API call sinh AI được ghi riêng.

Xem [báo cáo thực nghiệm live](A4_slide_baocao/bao-cao-live-2026-10-20.md), [kết quả benchmark](A2_fuzzer_benchmark/results/live_2026-10-20_v1.json) và [lượt triage đầu](A1_ai_triage/results/live_2026-10-20_run1.json). Nhãn reviewer/N3, thời gian review thủ công và clip/video vẫn cần đầu vào của người phụ trách.

```powershell
python -X utf8 -m ai.A1_ai_triage.live --output ai/outputs/triage-new.json
python -X utf8 -m ai.A1_ai_triage.live --output ai/outputs/triage-new.json --resume
python -X utf8 -m ai.A2_fuzzer_benchmark.isolated_lab --mode live --output ai/outputs/benchmark-new.json
python -X utf8 -m ai.A3b_video_cache.artifacts --source ai/A3b_video_cache/cache/triage_live_2026-10-20_run1.json --replay
```

Live có sử dụng API theo `.env`; SDK không tự retry hoặc fallback. Giãn cách mặc định 20 giây, có thể dùng `--interval` cho triage. Resume yêu cầu cùng input/config/prompt/schema và bỏ qua ID đã thành công. Log giữ các lần lỗi kết nối/429 của lượt đầu. Chi phí tiền chưa có hóa đơn/đơn giá được xác minh nên không suy ra từ token. `AI_PROVIDER=openai` mô tả adapter SDK; endpoint thực tế là Groq.

Các mục ngày 16–18/10 dưới đây là lịch sử. Riêng `outputs/triage_zap_report.json` được giữ trong Git sau khi chuyển từ `Lan/outputs`; các output tạm khác vẫn bị bỏ qua.

## Trạng thái hiện tại — 18/10/2026

| Phần | Đã chuẩn bị | Còn phụ thuộc |
|---|---|---|
| A3a | Config/schema, adapter OpenAI, test HTTP giả | Provider/model, quyền gửi dữ liệu, hạn mức/key và cloud smoke test |
| A1 | H1 thật, 11 ID backend, input khóa hash và hai bản review riêng | Nhãn độc lập Như/Phát, inference live và N3 |
| A2 | Runner offline mới, reset WAF, budget chung, checkpoint SQLi từng attempt; 9 lượt HTTP thật trên lab tách biệt | Nhóm duyệt oracle; nguồn AI tĩnh và benchmark LLM live |
| A3b | Cache offline có hash nguồn/payload; replay kiểm tra hash và không gọi mạng | Output A1 live; video nếu đưa vào phạm vi |

[Kế hoạch hoàn thiện](01_ke-hoach-hoan-thien-lan.md), [báo cáo](bao-cao-tien-do-lan.md), [bộ review độc lập](A1_ai_triage/review_bundle_v1/README.md).

Chạy từ gốc repo với dependency Python trong `ai/requirements.txt` và Node tại `backend/node_modules`:

Kiểm chứng cập nhật: **38/38 unittest pass**, 9/9 lượt benchmark offline HTTP thật đạt oracle đề xuất. [Danh mục hash bàn giao](artifact_inventory_2026-10-18.json) bảo toàn hash nguồn/đầu ra hiện tại; không xác nhận nhãn hay chất lượng AI.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -X utf8 -m unittest discover -s ai/tests -v
python -X utf8 -m ai.A2_fuzzer_benchmark.isolated_lab --output ai/outputs/offline-new-run.json
python -X utf8 -m ai.A3b_video_cache.artifacts --source ai/A3b_video_cache/cache/offline_v1.json --replay
```

Launcher sao chép ba file H3 vào thư mục tạm, khởi động cổng trống với database riêng, chạy benchmark rồi dừng đúng process. Server gốc tự reset database khi khởi động nên không khởi động nó để chạy lại trên dữ liệu hiện hữu.

[Kết quả mới](A2_fuzzer_benchmark/results/offline_v1.json): `wordlist_static`, `fixed_candidates`, `heuristic_feedback`, 3 lượt/nhánh, đạt checkpoint sau 5/6/2 request tấn công mỗi lượt. Tổng 39 request tấn công + 36 request phụ benchmark; launcher có request chờ server sẵn sàng ngoài tổng này. Không có lời gọi cloud.

Oracle đề xuất cho câu SQLi H3 so sánh ID kết quả với SQL ghép chuỗi và truy vấn parameterized trên cùng snapshot id/name. Cần nhóm rà soát; không đánh giá XSS hoặc hiệu quả LLM cloud. Danh sách cố định chưa có provenance sinh AI. N=50 là trần đề xuất; nguồn cạn hoặc đạt checkpoint thì dừng sớm.

Entry point chính mới là `isolated_lab` ở trên. `ai/A2_fuzzer_benchmark/runner.py` chỉ giữ scaffold/template cũ để tương thích; script/kết quả tại `demo/ai_fuzzer` là thực nghiệm cũ. Công cụ cache mới từ chối thiếu dữ liệu, hash sai và ghi đè artifact.

## Nội dung bàn giao lịch sử ngày 16–17/10

Các bảng trạng thái cũ bên dưới được giữ làm lịch sử; dùng mục ngày 18/10 ở trên cho công việc hiện tại. Liên kết tới proposal/đề cương trong bản cũ chưa có file đích tại checkout này.

**MSSV:** 23120289. **Nhánh:** `lan/ai-workspace`. Cập nhật: 16/10/2026.

Phạm vi A1, A2, A3a, A3b, A4 theo [đề cương](../docs/de-cuong-seminar.md) và [proposal AI](../docs/ai_proposal.md). Không thay phần N1–N4 của Thạch Như, không tạo nhãn chuẩn N2/P2, không triển khai Fuzzer L2 hoặc bộ lọc H3.

## Trạng thái bàn giao

| Phần | Đã có | Còn chờ |
|---|---|---|
| A3a | Adapter gọi AI, cấu hình môi trường, JSON schema, kiểm tra lỗi; mock không dùng mạng | Nhóm duyệt model/cấu hình; kiểm thử API thật bằng tài khoản được phép |
| A1 | Parser ZAP, prompt, pipeline và CLI; chạy được bằng alert mẫu tự tạo | JSON ZAP thật từ H1; kiểm tra lại mapping và đơn vị alert |
| A2 | Chữ ký runner, định dạng log, lệnh tạo template rỗng | H3, L2 và checkpoint được Như/Phát rà soát |
| A3b | Cache rỗng có nhãn replay, quy trình video | N3 và clip L3; chưa có video thật |
| A4 | Outline slide và báo cáo | Số liệu thật A1–A3, N3 |

Chi tiết phụ thuộc và câu hỏi cần nhóm trả lời nằm trong [kế hoạch](00_ke-hoach-lam-viec.md).

## Chạy thử từ thư mục gốc repo

Python 3.12 được dùng để kiểm tra. Nên dùng môi trường ảo riêng:

```powershell
python -m venv ai/.venv
ai/.venv/Scripts/python.exe -m pip install -r ai/requirements.txt
ai/.venv/Scripts/python.exe -X utf8 -m unittest discover -s ai/tests -v
ai/.venv/Scripts/python.exe -m ai.A1_ai_triage.run --mode mock --output ai/outputs/triage_sample_mock.json
ai/.venv/Scripts/python.exe -m ai.A2_fuzzer_benchmark.runner --write-template ai/outputs/a2-template
```

Nếu đã cài đúng dependencies trong môi trường hiện tại, có thể thay `ai/.venv/Scripts/python.exe` bằng `python`. Chế độ mock không cần key, không gửi request đến AI hoặc EShop. Lệnh A2 chỉ tạo CSV có header và JSON có `rows: []`; chạy lần hai cùng đường dẫn sẽ từ chối ghi đè.

**Không dùng đầu ra mock làm số liệu báo cáo.** Ba alert trong sample là tự tạo; `is_real: null`, `confidence: 0`, `priority: P3` chỉ kiểm tra hợp đồng dữ liệu, không phải kết quả phân loại. Thư mục `outputs/`, môi trường ảo, bytecode và `.env` bị Git bỏ qua; `.env.example` được giữ lại.

## Tài liệu từng phần

- [A3a: cấu hình, JSON và cách tích hợp](A3a_ai_config/README.md)
- [A1: đầu vào ZAP, cách chạy Triage](A1_ai_triage/README.md)
- [A2: runner đang block và định dạng log](A2_fuzzer_benchmark/README.md)
- [A3b: cache và quy trình ghép video](A3b_video_cache/README.md)
- [A4: slide](A4_slide_baocao/slide-outline.md) và [báo cáo](A4_slide_baocao/report-outline.md)

## Kiểm chứng ngày 16/10/2026

`python -X utf8 -m unittest discover -s ai/tests -v`: **31/31 ca qua** tại thời điểm bàn giao. Test adapter dùng `httpx.MockTransport`, không phải inference của model. Đã kiểm tra schema, parsing ZAP, secret redaction cơ bản, lỗi/refusal không fallback mock, nhánh A2 không tiêu thụ payload, cache rỗng và CLI mẫu.

Chưa gọi API thật cho A1, chưa có nhãn chuẩn hoặc video trong lần này.

### Cập nhật tích hợp tài nguyên nhóm ngày 17/10/2026

- H1: report ZAP thật được lọc theo origin `http://localhost:3000`; A1 đã
  chuẩn hóa 11 instance bằng mock để kiểm tra mapping.
- H3/L2: server lab và Fuzzer của Long đã chạy tại localhost:3001 bằng
  heuristic offline, không gửi API cloud.
- A2: benchmark đã chạy 3 lượt/nhánh, ghi log thật tại
  `demo/ai_fuzzer/benchmark_results.json`.
- Ground truth: `A1_ai_triage/ground_truth_template.json` chỉ là biểu mẫu chờ
  Như/Phát review độc lập, không phải nhãn chuẩn.

Chưa có inference live cho A1, Precision/Recall, video hoặc slide. Không dùng
output mock hay cache replay làm kết quả AI.
