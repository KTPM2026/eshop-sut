# N2 - Thạch Như (23120312): review có AI hỗ trợ

**Không phải nhãn người độc lập / Ground Truth đã chốt.**

Cùng 15 nhóm gốc với Phát; 2 nhóm ngoài scope bị loại, còn 13 nhóm / 29 instance.

| # Phat | Alert | Nhu (de xuat) | Priority | Phat | Doi chieu | Can cu / gioi han |
|---|---|---|---|---|---|---|
| 1 | Strict-Transport-Security Header Not Set | excluded | - | Giả (ngoài phạm vi) | excluded | Host Google bên ngoài phạm vi EShop; loại khỏi tập chấm, không gán false để tăng TN. |
| 2 | Re-examine Cache-control Directives | excluded | - | Giả (ngoài phạm vi) | excluded | Host Google bên ngoài phạm vi EShop; không scan/replay dịch vụ này. |
| 3 | SQL Injection | true | P1 | Thật | same_provisional_classification | Đối chứng tên không tồn tại trả 0 sản phẩm; cùng prefix với OR 1=1 trả 5, OR 1=2 trả 0; dấu nháy gây 500. Có hiệu ứng boolean trên dữ liệu thật và source nối chuỗi SQL, không kết luận chỉ từ 500. Chưa dump users trong lượt Như. |
| 4 | Cross-Domain Misconfiguration | unknown | - | Thật | pending_joint_verification | Wildcard có thật nhưng các instance alert là API sản phẩm công khai. Browser đọc được sản phẩm khi omit credentials; include credentials bị chặn; /api/users/me không có token trả 401, không lộ profile. Chưa có policy origin hoặc bằng chứng đọc dữ liệu riêng qua CORS. Không suy wildcard thành lỗ hổng, cũng không kết luận toàn bộ CORS an toàn. |
| 5 | Server Leaks Information via "X-Powered-By" HTTP Response Header Field(s) | true | P4 | Thật | same_provisional_classification | Response sản phẩm/detail xác nhận X-Powered-By: Express. Ghi nhận lộ tech stack/hardening mức thấp; chưa chứng minh khai thác độc lập hoặc lộ dữ liệu riêng từ header. |
| 6 | X-Content-Type-Options Header Missing | true | P4 | Thật | same_provisional_classification | API sản phẩm/detail không có X-Content-Type-Options; MIME quan sát là JSON. Xác nhận điều kiện thiếu header theo rubric cấu hình/hardening, chưa chứng minh MIME-sniffing exploit. Nhóm cần đồng ý đưa hardening vào lớp dương khi chấm N3. |
| 7 | Authentication Request Identified | false | P4 | Không phải lỗ hổng (Informational) | same_provisional_classification | Authentication Request Identified là nhận diện endpoint đăng nhập, không phải chứng cứ lỗi xác thực. Không suy ra mọi chức năng login an toàn; các lỗi login khác nằm ngoài kết luận của alert này. |
| 8 | Path Traversal | unknown | - | Giả (False Positive) | pending_joint_verification | Chunk Vite cũ và query attack đều trả 200 text/html, body hash giống trang root: SPA fallback, không phải JavaScript hay nội dung file vượt thư mục. Không có đối chứng asset cũ hợp lệ và thiếu response/commit scan gốc, nên chưa đủ xác nhận traversal hoặc chốt false positive chỉ từ tham số v. |
| 9 | Content Security Policy (CSP) Header Not Set | true | P3 | Thật | same_provisional_classification | Root và /forgot-password thiếu CSP. Browser chạy onerror từ payload tự nhập trong ô tìm kiếm; source Home dùng dangerouslySetInnerHTML. Query URL không kích hoạt payload: mới chứng minh sink/script execution từ local input, chưa chứng minh delivery tới nạn nhân hoặc account takeover. P3 là ưu tiên kiểm chứng đề xuất; CSP là phòng vệ bổ sung, không phải cách sửa duy nhất và không đếm sink thành bug riêng trong tập alert này. |
| 10 | Missing Anti-clickjacking Header | true | P4 | Thật | same_provisional_classification | Hai trang thiếu X-Frame-Options và CSP frame-ancestors; trang /forgot-password render form trong iframe từ origin 5174. Xác nhận có thể nhúng trang, chưa thực hiện thao tác nhạy cảm hay chứng minh account takeover bằng clickjacking. |
| 11 | Timestamp Disclosure - Unix | false | P4 | Giả (False Positive) | same_provisional_classification | Source React DOM 19.2.6 dùng số 2080374784 trong biểu thức lanes & 2080374784 chọn nhánh Idle; đây là bitmask, không phải thời điểm nhạy cảm của EShop. Có context và hash source dependency; không suy mọi timestamp đều vô hại. |
| 12 | X-Content-Type-Options Header Missing | true | P4 | Thật | same_provisional_classification | Response CSS/module dev server kiểm tra được thiếu X-Content-Type-Options; MIME được ghi trong log. Đây là hardening trên môi trường Vite development, không suy thành MIME-sniffing exploit hay cấu hình production. |
| 13 | Information Disclosure - Sensitive Information in URL | unknown | - | Thật | pending_joint_verification | Scan ghi token trong query nhưng thiếu provenance giá trị/flow. Frontend hiện xử lý OTP 4 số trong JSON, không đọc query token ở ForgotPassword; marker query giả cho cùng HTML root. Chưa chứng minh token scan là reset/session token hoặc đã rò qua log/Referer; cũng không đủ căn cứ coi token dev là vô hại. Không gửi lại token gốc. |
| 14 | Information Disclosure - Suspicious Comments | false | P4 | Không phải lỗ hổng (Informational) | same_provisional_classification | Các mảnh comment ZAP chỉ ra nằm trong React Refresh/React DOM; lượt replay xác nhận tài nguyên React Refresh chứa TODO. Chưa chỉ ra bí mật hoặc logic nghiệp vụ EShop trong chính các mảnh này; ghi nhận thông tin, không phải lỗi từ bằng chứng hiện có. Không khẳng định toàn bộ source không có secret. |
| 15 | Modern Web Application | false | P4 | Không phải lỗ hổng (Informational) | same_provisional_classification | Modern Web Application là phát hiện SPA/script module để scanner lựa chọn cách crawl, không phải lỗ hổng. Root/module React được xác nhận; không kết luận về độ an toàn của SPA từ alert này. |

Summary (not accuracy): `{'instances': {'true': 14, 'unknown': 5, 'false': 10}, 'groups': {'excluded': 2, 'true': 6, 'unknown': 3, 'false': 4}, 'comparison': {'excluded': 2, 'same_provisional_classification': 10, 'pending_joint_verification': 3}}`.

Evidence: [HTTP/browser log](../evidence/main-13f4d88/verification.json), [XSS](../evidence/main-13f4d88/xss-executed.png), [frame](../evidence/main-13f4d88/frame-rendered.png).

Human timing is unmeasured. Automated request milliseconds are not human labeling time.
P4 on non-vulnerabilities means low review priority, not an exploitable bug.
Groups 4, 8, 13 remain pending joint verification; do not auto-adjudicate.
