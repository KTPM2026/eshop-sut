# N1: Runbook Burp Suite của Như

**Trạng thái:** đã chạy 11 ca API thật trên main của nhóm tại commit `ab5dd4f7ac0d8562800311dc94109939d3c6d930`, **5 pass / 6 vi phạm quyền truy cập / 0 chưa đủ bằng chứng**. Có request/response và 3 ảnh trình duyệt trong [báo cáo lượt chạy](evidence/main-run-20261016/README.md). Lượt này do Codex thực thi bằng Node.js và Edge headless; demo Burp của sinh viên còn cần thực hiện.

## Tái lập lượt kiểm chứng API

Node.js 24 và Python 3.12 được dùng. Tạo bản clone riêng bên trong `Nhu/private`; backend reset database khi khởi động. Từ root repo:

```powershell
git clone https://github.com/KTPM2026/eshop-sut.git Nhu/private/eshop-burp-lab
git -C Nhu/private/eshop-burp-lab checkout --detach ab5dd4f7ac0d8562800311dc94109939d3c6d930
npm.cmd --prefix Nhu/private/eshop-burp-lab/backend ci --no-audit --no-fund
node Nhu/N1_burp/run_preflight.cjs --sut Nhu/private/eshop-burp-lab --reset-lab --output-dir Nhu/outputs/n1-new-run
```

Runner tạo tài khoản B, dùng A/admin có sẵn, tạo hai đơn riêng và chạy [ma trận](case-matrix.csv). Mỗi ca kiểm tra dữ liệu thật cùng owner/role; output có JSON, CSV và báo cáo. `--reset-lab` chỉ dùng cho clone bỏ được; runner từ chối khởi động SUT bên ngoài `Nhu/private` hoặc khi port 3000 đã có dịch vụ. Trên máy lần này đã tái sử dụng dependency của sandbox có cùng phiên bản; phiên bản thực được lưu trong `results.json`.

Muốn giữ lab hoạt động để Như thao tác Burp, thêm `--keep-lab --session-file Nhu/private/burp-session.json` và dùng output/session path mới. Token chỉ nằm trong file private đó; Ctrl+C dừng server. Thông tin user/order có trong session và báo cáo để đối chiếu.

Ảnh API được chụp bằng Edge headless, JSON/status đối chiếu với ca kiểm thử. Tái lập ảnh tùy chọn: cài `playwright-core` vào `Nhu/private/browser-tools`, thêm `--browser-module Nhu/private/browser-tools/node_modules/playwright-core` vào lệnh runner trên máy có Edge. Tham chiếu [Playwright screenshots](https://playwright.dev/docs/screenshots). Đây là ảnh response trình duyệt, chưa phải ảnh Burp.

## 1. Đầu vào và ranh giới

Hùng đã có [ZAP export](../../alert/2026-10-14-ZAP-Report-.json) và [setup](../../setup_ZAP.md). Lượt N1 mới dùng main của nhóm trong clone riêng, có user A/B/admin và hai đơn có owner xác minh được. Export ZAP không ghi commit scan 14/10; chỉ cần Hùng xác nhận chi tiết đó nếu đối chiếu môi trường scan. Khi dùng lab khác, ghi lại frontend/API origin, seed/reset, **user ID/role, order ID, owner ID** từ dữ liệu thật; không giả định ID giữ nguyên. Không reset hoặc ghi/xóa dữ liệu ngoài bản lab được phép.

Tại commit main đã chạy, source có `GET /api/orders/:id` và `GET /api/admin/users`; route thứ hai có xác thực nhưng chưa kiểm tra role. Hành vi được kiểm chứng bằng request/response, không chỉ suy từ source. [Source EShop cố định](https://github.com/KTPM2026/eshop-sut/blob/ab5dd4f7ac0d8562800311dc94109939d3c6d930/backend/server.js).

TỰ ĐỀ XUẤT - CẦN NHÓM CHỐT: policy API cá nhân chỉ owner được đọc; guest/cross-user bị từ chối; API admin chỉ admin được phép. Ngoại lệ admin với đơn cá nhân chưa chốt nên không tự kết luận ô đó.

## 2. Kịch bản 1: Cài/cấu hình và ghi nhận request

1. Dùng Burp Community từ nguồn PortSwigger, ghi phiên bản thực cài vào manifest, không ghi “latest” thay phiên bản.
2. Mở browser của Burp, truy cập frontend lab nếu đã chạy frontend, hoặc mở trực tiếp API đơn lab để ghi request. Cấu hình scope chính xác cho origin đang dùng: `http://127.0.0.1:3000` của runner; nếu frontend chạy thêm thì bao gồm `http://localhost:5173`. Không tự đổi qua `localhost:3000` rồi giả định scope cũ vẫn khớp; chỉ giữ traffic lab.
3. Bật Proxy intercept cho một thao tác đọc dữ liệu hợp lệ, forward để hoàn tất, sau đó tắt intercept nếu app bị chờ. Kiểm tra HTTP history có đúng host/path và response.

Thao tác Proxy/scope tham chiếu [hướng dẫn intercept](https://portswigger.net/burp/documentation/desktop/getting-started/intercepting-http-traffic) và [target scope](https://portswigger.net/burp/documentation/desktop/getting-started/setting-target-scope). Phiên bản UI có thể khác; ghi lại cài đặt thực tế, không giả định chỉ frontend nằm trong scope là đủ.

**Bằng chứng cần ghi mới:** version, scope, request/response đọc hợp lệ đã làm sạch, clip thao tác ngắn. Không quay bước nhập key/token hoặc mật khẩu.

## 3. Kịch bản 2: Record & Playback có đối chứng

Từ HTTP history, gửi request đọc đơn của A sang Repeater, đặt tên tab theo case ID. Gửi lại bản nguyên gốc trước; sau đó chỉ đổi ID đơn hoặc Authorization, mỗi lần một biến. Lưu từng cặp request/response và note biến đã đổi. Repeater hỗ trợ sửa/gửi lại message và giữ history từng tab. [PortSwigger Repeater](https://portswigger.net/burp/documentation/desktop/tools/repeater).

**Đối chứng bắt buộc:** A xem đơn A, B xem đơn B; kiểm tra response JSON đúng `id` và `user_id` đã biết. Nếu đối chứng không chạy được, dừng diễn giải cross-user: có thể đang sai phiên/ID/endpoint.

[requests.http](requests.http) chỉ là template với placeholder, không chứa token thật và chưa được gửi. Với guest phải xóa hẳn Authorization/Cookie; không gọi “guest” khi vẫn còn phiên của user.

## 4. Kịch bản 3: Data-driven IDOR và API admin

[case-matrix.csv](case-matrix.csv) là danh sách ca **kỳ vọng**, chưa có actual result. Dùng hai order ID thuộc A/B đã xác minh; không quét dãy ID không thuộc dữ liệu lab. Chạy từng dòng với đúng danh tính và đối chứng.

Có thể dùng Intruder Sniper với **một vị trí order ID**, chỉ hai ID lab, token cố định cho một actor; chạy riêng từng actor. Không dùng Cluster bomb để trộn token/ID ngoài phạm vi. Cơ chế Sniper thay từng payload ở từng vị trí được mô tả trong [tài liệu attack types](https://portswigger.net/burp/documentation/desktop/tools/intruder/configure-attack/attack-types). Nếu bản cài không thuận tiện, dùng Repeater thủ công theo cùng CSV vẫn là data-driven; phải nói rõ thao tác thực tế.

API admin: chạy guest, user A, user B và admin hợp lệ với request đọc danh sách. Không thử DELETE/PUT, tự nâng role hoặc dùng token giả trong phần này. User thường không có menu admin vẫn phải kiểm tra API trực tiếp; HTML SPA trả 200 không chứng minh API đã lộ dữ liệu.

## 5. Checkpoints và kết luận

| Tình huống | Bằng chứng cần đọc | Cách ghi kết luận |
|---|---|---|
| Owner hợp lệ | Đúng order ID, owner ID, dữ liệu lab tương ứng | Đối chứng hợp lệ; chưa chứng minh mọi ca an toàn |
| Guest/cross-user | Response thực sự chứa đơn của owner khác và dữ liệu riêng; request chứng minh không dùng token của owner | Có bằng chứng truy cập trái phép; gom nguyên nhân cùng route, không đếm mỗi ID thành bug riêng |
| User thường gọi API admin | Xác minh role bằng nguồn tin cậy; body chứa danh sách user lab, so với admin control | Có bằng chứng vượt quyền đọc; không suy ra sửa/xóa được |
| Bị từ chối | Không trả dữ liệu riêng; status 401/403/404 phù hợp policy | Không tái hiện trong ca này; vẫn cần đối chứng hợp lệ |
| 200 HTML/JSON rỗng, 500, timeout hoặc thiếu owner | Không xác minh được nội dung/quyền | Chưa đủ bằng chứng, không ép thành pass/bug |

Nếu response lỗi vẫn kèm dữ liệu riêng thì status lỗi không làm mất bằng chứng lộ dữ liệu. Lưu riêng case ID, actor, owner, status, kết quả checkpoint và bằng chứng đã làm sạch. Chỉ status 200/403, độ dài body hoặc tên alert không đủ kết luận.

## 6. Ghi hình và bàn giao

Quay ba phần với thuyết minh Như, lưu nguồn/log, cho thấy đối chứng và một ca đã xác minh; nếu không tái hiện thì báo đúng giới hạn. Gửi clip Burp cho Long ghép với sqlmap thành video 2; tiêu chuẩn chung trong đề cương là 1080p. Nếu phát lại request log/clip cũ phải ghi rõ, không gọi là live run.

Checklist hoàn tất; đánh dấu khi đã thực hiện và có bằng chứng:

- [x] Có commit/scope/seed/reset và ánh xạ user/role/order/owner của lượt API trong results.json.
- [x] Owner A/B và admin control của lượt API chạy được; guest không có phiên đăng nhập.
- [x] Lượt API có actual status, checkpoint và request/response đã làm sạch.
- [ ] Như tự thực hiện ba kịch bản Burp, lưu phiên bản công cụ, ảnh/history và điền manifest từ phiên đó.
- [ ] Clip 1080p có thuyết minh và nhãn replay nếu có; đã gửi Long clip Burp và Phát nội dung N4.
