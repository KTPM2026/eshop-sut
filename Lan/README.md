# Không gian làm việc của Nguyễn Nhật Lân

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
python -m venv Lan/.venv
Lan/.venv/Scripts/python.exe -m pip install -r Lan/requirements.txt
Lan/.venv/Scripts/python.exe -X utf8 -m unittest discover -s Lan/tests -v
Lan/.venv/Scripts/python.exe -m Lan.A1_ai_triage.run --mode mock --output Lan/outputs/triage_sample_mock.json
Lan/.venv/Scripts/python.exe -m Lan.A2_fuzzer_benchmark.runner --write-template Lan/outputs/a2-template
```

Nếu đã cài đúng dependencies trong môi trường hiện tại, có thể thay `Lan/.venv/Scripts/python.exe` bằng `python`. Chế độ mock không cần key, không gửi request đến AI hoặc EShop. Lệnh A2 chỉ tạo CSV có header và JSON có `rows: []`; chạy lần hai cùng đường dẫn sẽ từ chối ghi đè.

**Không dùng đầu ra mock làm số liệu báo cáo.** Ba alert trong sample là tự tạo; `is_real: null`, `confidence: 0`, `priority: P3` chỉ kiểm tra hợp đồng dữ liệu, không phải kết quả phân loại. Thư mục `outputs/`, môi trường ảo, bytecode và `.env` bị Git bỏ qua; `.env.example` được giữ lại.

## Tài liệu từng phần

- [A3a: cấu hình, JSON và cách tích hợp](A3a_ai_config/README.md)
- [A1: đầu vào ZAP, cách chạy Triage](A1_ai_triage/README.md)
- [A2: runner đang block và định dạng log](A2_fuzzer_benchmark/README.md)
- [A3b: cache và quy trình ghép video](A3b_video_cache/README.md)
- [A4: slide](A4_slide_baocao/slide-outline.md) và [báo cáo](A4_slide_baocao/report-outline.md)

## Kiểm chứng ngày 16/10/2026

`python -X utf8 -m unittest discover -s Lan/tests -v`: **30/30 ca qua** tại thời điểm bàn giao. Test adapter dùng `httpx.MockTransport`, không phải inference của model. Đã kiểm tra schema, parsing ZAP, secret redaction cơ bản, lỗi/refusal không fallback mock, nhánh A2 không tiêu thụ payload, cache rỗng và CLI mẫu.

Chưa gọi API thật, chưa scan EShop, chưa chạy benchmark, chưa kiểm chứng chất lượng phân loại hay hiệu quả bypass. Không có nhãn chuẩn hoặc video trong lần này.
