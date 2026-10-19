# Minh chứng Burp do Như cung cấp ngày 19/10/2026

**Thạch Như - 23120312. Trạng thái: đã có ảnh Response cho cả 11 ca, chưa đủ để chốt toàn bộ N1.** Bộ chia sẻ có 11 ảnh Response, 2 ảnh Proxy và 1 ảnh Scope từ phiên Burp Community 2026.3.3 do Như cung cấp. Codex tìm đúng file gốc trong thư mục Screenshots của Windows, xem ảnh và sao chép nguyên bytes vào đây theo yêu cầu của Như; không tạo lại, cắt, sửa hoặc thay nội dung ảnh. File gốc không bị xóa/thay đổi.

[manifest.json](manifest.json) ghi tên ảnh gốc, SHA256, kích thước, timestamp file UTC và nội dung đã đọc trên ảnh. Ảnh toàn Repeater có Authorization không được đưa vào bộ chia sẻ; chỉ dùng bản chụp Response không có token. Các tài khoản, địa chỉ và số tiền hiển thị là dữ liệu lab EShop.

## Cấu hình quan sát được

- [Proxy Intercept](proxy-intercept.png): giữ request `GET /api/products` tới `127.0.0.1:3000`; tiêu đề app ghi Burp Community 2026.3.3.
- [HTTP history](proxy-http-history.png): cùng request có status 200, MIME JSON và body sản phẩm.
- Lab được launcher chuẩn bị ở commit `ab5dd4f7ac0d8562800311dc94109939d3c6d930`; commit này lấy từ session setup, không được đọc trực tiếp từ ảnh Burp. A có user ID 2/đơn 1, B có user ID 3/đơn 2, admin có user ID 1 theo setup.
- [Scope](scope.png): một prefix được bật `http://127.0.0.1:3000/`, không bật include subdomains; bảng exclude trống. Đây là cấu hình phạm vi, chưa chứng minh Burp đã chặn mọi request ngoài scope.
- Intruder đã chạy xong với hai payload `1`, `2`, cả hai trả 200; response lần lượt chứa đơn 1/owner 2 và đơn 2/owner 3. Hai ảnh gốc được giữ trong `Nhu/private/burp-intruder-20261019/` vì có JWT, không nằm trong 14 ảnh chia sẻ ở đây. Manifest lưu hash và quan sát không chứa token. Dòng 0 là request baseline không đổi, không phải ID 0.
- Ảnh chọn payload `2` có response đơn 2 nhưng khung Request vẫn hiện `/api/orders/1`. Chưa rõ nguyên nhân; cần export đúng item để xác minh cặp request/response. Chưa có ảnh cấu hình positions/attack type nên không khẳng định đã dùng Sniper hay cấu hình vị trí cụ thể. Chưa nhận clip.

## Bảng quan sát Response

**Actor và mã ca dưới đây theo file request đã hướng dẫn, chưa được xác minh bằng export Burp.** Bảy ảnh mới được ghép theo thứ tự thao tác và thời gian response. Ảnh chỉ có Response không tự chứng minh người gửi là A/B/guest, URL đang gọi hoặc token đã dùng. Kết luận pass/vi phạm chính thức vẫn cần request đi kèm.

| Ca | Actor theo kế hoạch | HTTP nhìn thấy | Nội dung nhìn thấy | Ảnh |
|---|---|---|---|---|
| N1-01 | A đọc đơn A | 200 | Đơn 1, owner 2, tổng 30.000.000, địa chỉ lab A | [Response](N1-01.response.png) |
| N1-02 | B đọc đơn B | 200 | Đơn 2, owner 3, tổng 6.000.000, địa chỉ lab B | [Response](N1-02.response.png) |
| N1-03 | Guest đọc đơn A | 200 | Đơn 1, owner 2 và dữ liệu đơn A | [Response](N1-03.response.png) |
| N1-04 | Guest đọc đơn B | 200 | Đơn 2, owner 3 và dữ liệu đơn B | [Response](N1-04.response.png) |
| N1-05 | A đọc đơn B | 200 | Đơn 2, owner 3 và dữ liệu đơn B | [Response](N1-05.response.png) |
| N1-06 | B đọc đơn A | 200 | Đơn 1, owner 2 và dữ liệu đơn A | [Response](N1-06.response.png) |
| N1-07 | Guest gọi API admin | 401 | `Unauthorized`, không có danh sách user trong ảnh | [Response](N1-07.response.png) |
| N1-08 | A gọi API admin | 200 | Thấy user ID 1/2/3 với role admin/user; body bị cắt phần cuối | [Response](N1-08.response.png) |
| N1-09 | B gọi API admin | 200 | Thấy user ID 1/2/3 với role admin/user; body bị cắt phần cuối | [Response](N1-09.response.png) |
| N1-10 | Admin đối chứng | 200 | Đầy đủ danh sách 3 user: ID 1 admin, ID 2/3 user; actor theo hướng dẫn, chờ export | [Response](N1-10.response.png) |
| N1-11 | A đọc đơn không tồn tại | 404 | `Order not found` | [Response](N1-11.response.png) |

Nếu export khớp đúng các actor/file đã hướng dẫn, 11 response này tương ứng sơ bộ 5 ca đúng kỳ vọng và 6 ca vi phạm quyền. **Chưa chốt kết quả cuối 5 pass/6 fail khi chưa xác minh request/actor.** Ảnh N1-10 được cung cấp sau hướng dẫn chạy admin đối chứng, có Date `2026-10-19T04:29:01Z`; bản chụp Response không tự chứng minh token admin đã dùng. Không lấy kết quả API tự động của lượt trước thay export của phiên Burp.

## Hai nhóm dấu hiệu cần hoàn thiện bằng chứng

1. **Đọc đơn không đúng quyền:** các ảnh dự kiến N1-03/04/05/06 trả dữ liệu riêng của A/B. Cần request để kiểm tra guest đã bỏ cả Authorization/Cookie, hoặc token thực sự thuộc người khác. Nếu xác nhận, gom các ca cùng route `GET /api/orders/:id` thành một phát hiện, không đếm mỗi ảnh thành bug riêng.
2. **User thường đọc danh sách quản trị:** các ảnh dự kiến N1-08/09 trả danh sách user; đã có ảnh Response dự kiến admin đối chứng N1-10. Cần export để xác minh token role user/admin và hoàn thiện chuỗi bằng chứng. Chỉ kiểm tra quyền đọc; không suy ra quyền sửa/xóa.

Ngày giờ trong header Date là thời điểm server trả response UTC. Timestamp ảnh là metadata file. Không dùng chúng làm thời gian gán nhãn N2 hoặc thời lượng thao tác thủ công của Như.

## Giới hạn và bàn giao tiếp

- Cần cặp request/response thật để xác minh actor/URL. Có thể dùng ảnh ghép hoặc log đã che token; XML qua **Save item** chỉ là cách lưu tùy chọn, không phải yêu cầu bắt buộc của phân công. Không dựng lại bằng chứng từ template/ảnh.
- N1-10 đã có ảnh Response riêng; Data-driven cũng đã có bảng kết quả, không cần chụp/chạy lại chỉ để đủ ảnh. Cần đối chiếu request admin và cặp request/response của payload `2` đang lệch; bản chứa token giữ private.
- Clip Burp để Long ghép video 2 theo phân công nhóm. Chưa có đề nộp chính thức để suy ra clip phải nộp ngay trong đợt PR hiện tại; hoàn tất N1 theo kế hoạch nhóm vẫn cần bàn giao clip đã dự kiến.

Các file trong bộ này không phải nhãn chuẩn N2 hoặc benchmark N3. Manifest giữ `n1_complete: false`, các tham chiếu export/video còn null; không tự tạo bằng chứng còn thiếu.
