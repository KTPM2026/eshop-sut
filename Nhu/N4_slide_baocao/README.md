# N4: Phần báo cáo và slide của Như

**Thạch Như - 23120312.** Nội dung thực nghiệm để ghép bài seminar chung, cập nhật ngày 16/10/2026. Kết quả API do Codex hỗ trợ thực thi; Như cần rà soát và tự thao tác/thuyết minh phần Burp. Không coi ảnh API là ảnh Burp hoặc fixture là benchmark AI.

## 1. Phạm vi, nguồn và môi trường

Theo [đề cương N1–N4](https://github.com/KTPM2026/seminar/blob/main/docs/de-cuong-seminar.md), Như phụ trách demo Burp về IDOR/phân quyền API, nhãn độc lập lần 1, benchmark Triage và nội dung thực nghiệm cá nhân. Phần lý thuyết OWASP đã có ở [tài liệu nhóm](https://github.com/KTPM2026/seminar/blob/main/docs/owasp_top10.md); không nghiên cứu lại ở đây.

| Thành phần | Giá trị đã ghi nhận |
|---|---|
| Repo | [KTPM2026/eshop-sut](https://github.com/KTPM2026/eshop-sut), fork từ SUT môn học |
| Commit lượt API N1 | `ab5dd4f7ac0d8562800311dc94109939d3c6d930`, main có ZAP/WAF của Hùng và AI của Lân |
| Cách chạy | Clone lab riêng dưới `Nhu/private`, source backend không sửa; database reset/seed trước lượt chạy |
| Backend | `http://127.0.0.1:3000`, `NODE_ENV=development` |
| Runtime | Node v24.11.1; Express 5.2.1; body-parser 2.2.2; cors 2.8.6; jsonwebtoken 9.0.3; sqlite3 6.0.1 |
| Công cụ N1 đã chạy | Node HTTP; Edge headless qua Playwright chụp response thật 1920×1080 |
| Dữ liệu đối chứng | Admin ID 1, user A ID 2, user B ID 3; đơn A ID 1/owner 2, đơn B ID 2/owner 3 |
| Provenance N1 | Timestamp, hash source/runner/ma trận, phiên bản dependency, request/response trong [results.json](../N1_burp/evidence/main-run-20261016/results.json) |
| Đầu vào H1 | [Export ZAP của Hùng](../../alert/2026-10-14-ZAP-Report-.json), ZAP 2.17.0; scan timestamp `2026-10-14T12:03:34.601803939Z` |
| Cấu hình H1 được mô tả | [setup_ZAP.md](../../setup_ZAP.md): frontend 5173, API 3000, AJAX Spider/Active Scan và phiên đăng nhập |

Không khẳng định commit N1 cũng là commit scan ngày 14/10: export không ghi commit SUT chính xác. Bằng chứng chỉ hỗ trợ điều kiện thực nghiệm đã nêu.

## 2. Dữ liệu scanner dùng cho Triage

Dùng parser A1 sẵn có của Lân để chuẩn hóa từng instance. Lọc cả site và URL instance theo hai origin localhost 3000/5173 trước khi chuẩn hóa, che token theo redactor hiện có, giữ nguyên 29 ID khi A1 parse lại.

| Tập dữ liệu | Instance | Nhóm alert theo site |
|---|---:|---:|
| Export gốc của Hùng | 31 | 15 |
| Trong scope localhost | 29 | 13 |
| Loại khỏi benchmark: dịch vụ Google ngoài scope | 2 | 2 |

Trong 29 record: **2 High, 7 Medium, 10 Low, 10 Informational**. Backend có 11 instance, frontend có 18. Đây là số cảnh báo, **không phải 29 lỗ hổng thật**. Hai record High mang tên SQL Injection và Path Traversal vẫn cần kiểm chứng độc lập, không suy nhãn từ tên/risk.

[A1 input, dataset, phiếu trống và provenance](../N2_gan_nhan/data/h1-20261014) đã có sẵn. `source_sha256` dùng chung N2/P2/A1/N3 là hash input A1 đã scope/redact:
`5586507dc3cd3d292c7359df32760291a8eb2629cf115df88b9ecbefa751f5e7`.
Hash raw export và mapping về từng instance được lưu riêng. Không gửi raw export chứa token/traffic ngoài scope cho AI.

Các cảnh báo frontend có thể liên quan dev server/bundle phát triển; không suy rộng sang production. Export không có đầy đủ HTTP response cho mọi alert, nên phải replay hoặc giữ unknown khi không đủ bằng chứng.

## 3. Kiểm chứng phân quyền API

Chạy ma trận actor × owner/resource, có owner A/B và admin hợp lệ làm đối chứng. Checkpoint đọc order ID, owner ID, địa chỉ/tổng tiền lab hoặc danh sách user/role trong body, đồng thời kiểm tra status.

| Case | Actor/tài nguyên | Kỳ vọng | Actual/checkpoint | Kết quả |
|---|---|---|---|---|
| N1-01 | A / đơn A | Cho phép | 200, đúng đơn và owner A | Pass |
| N1-02 | B / đơn B | Cho phép | 200, đúng đơn và owner B | Pass |
| N1-03 | Guest / đơn A | Từ chối | 200, trả dữ liệu riêng đơn A | Vi phạm quyền |
| N1-04 | Guest / đơn B | Từ chối | 200, trả dữ liệu riêng đơn B | Vi phạm quyền |
| N1-05 | A / đơn B | Từ chối | 200, trả đơn của owner B | Vi phạm quyền |
| N1-06 | B / đơn A | Từ chối | 200, trả đơn của owner A | Vi phạm quyền |
| N1-07 | Guest / admin users | Từ chối | 401, Unauthorized | Pass |
| N1-08 | A role user / admin users | Từ chối | 200, trả ba tài khoản lab và role | Vi phạm quyền |
| N1-09 | B role user / admin users | Từ chối | 200, trả ba tài khoản lab và role | Vi phạm quyền |
| N1-10 | Admin / admin users | Cho phép | 200, đúng danh sách user/role | Pass |
| N1-11 | A / đơn không tồn tại | Từ chối | 404, Order not found | Pass |

Tổng **5 pass, 6 vi phạm quyền, 0 chưa đủ bằng chứng**, gom thành **2 phát hiện** theo route/nguyên nhân. Không đếm mỗi actor/ID thành một bug riêng và không gộp hai phát hiện thủ công này vào 29 record ZAP để thay đổi dataset benchmark.

**N1-ACCESS-01: Đọc đơn trái quyền.** Guest hoặc user khác đọc được `GET /api/orders/:id`, trong khi owner control trả đúng đơn. Body xác nhận owner/địa chỉ/tổng tiền nên kết luận không chỉ dựa status 200. Source tại [server.js L344](https://github.com/KTPM2026/eshop-sut/blob/ab5dd4f7ac0d8562800311dc94109939d3c6d930/backend/server.js#L344). Hướng sửa: xác thực và kiểm tra owner ở backend; giữ cả owner control và ca trái quyền trong test hồi quy.

**N1-ACCESS-02: User đọc API quản trị.** Hai token role user đọc danh sách user tại `GET /api/admin/users`; admin control trả cùng dữ liệu, guest bị 401. Xác thực đã có nhưng không đủ bảo vệ role. Source tại [server.js L494](https://github.com/KTPM2026/eshop-sut/blob/ab5dd4f7ac0d8562800311dc94109939d3c6d930/backend/server.js#L494). Hướng sửa: kiểm tra role ở backend, hồi quy với admin/user/guest.

Minh chứng [báo cáo và ba ảnh thật](../N1_burp/evidence/main-run-20261016/README.md), [CSV 11 ca](../N1_burp/evidence/main-run-20261016/results.csv), request/response trong JSON ở mục 1. Chỉ xác minh quyền đọc hai route; chưa kiểm tra sửa/xóa hoặc ngoại lệ admin đọc đơn cá nhân.

## 4. Kịch bản Burp để Như thực hiện và thuyết minh

| Đoạn quay | Thao tác | Nội dung thuyết minh |
|---|---|---|
| Cài/cấu hình | Hiển thị version Burp Community, browser/proxy, scope đúng origin lab; intercept một request hợp lệ | Phạm vi chỉ localhost, có dữ liệu lab riêng và không quay token/mật khẩu |
| Record & Playback | History → Repeater; A đọc đơn A, B đọc đơn B; replay request gốc trước khi đổi biến | Đối chứng xác nhận phiên/owner đúng, đổi mỗi lần một biến để giải thích nguyên nhân |
| Data-driven/Checkpoints | Dùng hai ID lab trong CSV; guest/cross-user; so user và admin ở API quản trị | Đọc body/owner/role cùng status, không coi 200 hay độ dài response là đủ |

Runbook, request template, lệnh giữ lab/session private và checklist ở [N1](../N1_burp/README.md). Dữ liệu 11 ca ở trên là HTTP đã chạy bằng script; Như cần ghi phiên Burp và clip thực tế riêng, không gọi ảnh Edge là ảnh Burp. Clip 1080p gửi Long ghép video 2; nếu phát lại phải ghi rõ.

## 5. Nhãn chuẩn và phương pháp benchmark

Như/Phát cùng dùng dataset 29 ID, mỗi người kiểm chứng riêng, ghi lý do/bằng chứng/thời gian và khóa phiếu trước khi xem nhãn nhau hoặc output AI. Sau đó cùng xử lý bất đồng và khóa nhãn chung. Unknown được giữ null; người viết A1 không tạo nhãn chuẩn.

Bộ chấm N3 đã có baseline risk và các chỉ số theo [định nghĩa chi tiết](../N3_benchmark_triage/README.md): Precision; Recall có tính AI abstain trên lỗi thật trong mẫu số; coverage; khớp ưu tiên; số lỗi thật bị false/P4 và hợp hai tập không đếm trùng; thời gian pipeline cộng review. Truth unknown báo riêng; mẫu số 0 là null.

Đo ít nhất ba lượt A1 thật trên cùng input/model/config đã duyệt, không dùng mock/replay. So thời gian với xử lý thủ công cùng phạm vi; ghi learning bias nếu reviewer đã biết nhãn chuẩn. Quy tắc baseline và rubric là đề xuất cần nhóm chốt trước khi đo.

**Chưa có số liệu Precision/Recall hay tiết kiệm thời gian để báo cáo.** Đầu vào còn thiếu là hai bản khóa nhãn và nhãn chung, ba run A1 live, timing thủ công/review. Vì vậy không đưa bảng fixture hoặc mục tiêu proposal thành kết quả. Khi có dữ liệu, N3 xuất bảng từng lượt và mean/min/max để thêm vào mục này.

## 6. Ghép slide và bàn giao

| Slide cá nhân | Nội dung đã có |
|---|---|
| 1 | Phạm vi Như và môi trường, commit main nhóm (mục 1) |
| 2 | ZAP: 31 → 29 instance, scope/token/ID/hash; giới hạn dev server (mục 2) |
| 3 | Ma trận 11 ca và checkpoints; ghép cảnh Burp thực tế sau khi quay (mục 3–4) |
| 4 | Hai phát hiện và ảnh API thật N1-03/N1-06/N1-08 (mục 3) |
| 5 | Nhãn độc lập và phương pháp benchmark/baseline (mục 5) |
| 6 | Điền bảng N3 chỉ sau khi có nhãn/run/timing thật; trước đó ghi chưa đo |
| 7 | Giới hạn, nguồn code/log và link clip thật sau khi upload |

Gửi Long clip Burp; Lân nhận input 29 record và hợp đồng/timing N3; Phát nhận nội dung này cùng minh chứng để ghép bài. Không có clip nào được tạo/upload trong lượt API. [Nhật ký](../progress-log.md) ghi công việc đã thực hiện và phần AI hỗ trợ.
