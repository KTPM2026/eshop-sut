# ZAP

## Tổng quan

Zed Attack Proxy (ZAP) của Checkmarx là một công cụ kiểm tra thâm nhập mã nguồn mở miễn phí. ZAP được thiết kế đặc biệt để thử nghiệm các ứng dụng web và vừa linh hoạt vừa có thể mở rộng.

Về cốt lõi, ZAP là cái được gọi là “người thao tác-trong-middle proxy”. Nó đứng giữa trình duyệt của người kiểm tra và ứng dụng web để nó có thể chặn và kiểm tra các tin nhắn được gửi giữa trình duyệt và ứng dụng web, sửa đổi nội dung nếu cần, và sau đó chuyển tiếp các gói tin đó đến đích. Nó có thể được sử dụng như một ứng dụng độc lập, và như một quá trình daemon.

## Các tính năng chính 
- Active vs. Passive Scans: Quét thụ động kiểm tra các yêu cầu HTTP và phản hồi của ứng dụng để tìm các dấu hiệu đã biết về lỗ hổng bảo mật và không thể thay đổi các yêu cầu. Quét chủ động có thể tạo và sửa đổi các yêu cầu được gửi đến ứng dụng, gửi các yêu cầu thử nghiệm để phát hiện các lỗ hổng mà bạn không thể tìm thấy bằng cách quét thụ động.

- Running Scans: Desktop vs. API: triển khai OWASP ZAP dưới dạng ứng dụng máy tính để bàn hoặc tự động thông qua API, tùy thuộc vào cách bạn dự định sử dụng ZAP

- Authenticated Security Scanning: Nhiều ứng dụng web yêu cầu xác thực. Trong trường hợp này, cần phải cấu hình xác thực trong ZAP trước khi chạy quét. Nếu không, quá trình kiểm tra sẽ không kiểm tra bất kỳ đường dẫn nào hoặc các đường dẫn nào nằm sau lớp bảo vệ xác thực.

- WebSockets: WebSocket tạo ra một kênh giao tiếp không đồng bộ giữa máy khách và máy chủ, truyền dữ liệu theo chế độ song công hoàn toàn. Điều này tạo ra các lỗ hổng bảo mật, bởi vì WebSocket giữ cho kênh luôn mở, cho phép kẻ tấn công nghe lén hoặc chiếm đoạt phiên giao dịch. ZAP liên tục quét WebSocket để xác định các lỗ hổng.

- OWASP ZAP Fuzzer: Fuzzing là một kỹ thuật gửi một lượng lớn dữ liệu đầu vào không mong muốn đến ứng dụng cần kiểm thử. OWASP ZAP cho phép kiểm thử fuzzing các ứng dụng web. Bạn có thể chọn một trong các payload tích hợp sẵn, tải xuống nhiều payload khác nhau do cộng đồng ZAP cung cấp hoặc tự tạo payload của riêng mình.

- AJAX Spidering: Thu thập dữ liệu bằng AJAX có thể giúp phát hiện các yêu cầu từ các ứng dụng web giàu AJAX mà các trình thu thập dữ liệu thông thường không thể phát hiện. ZAP cung cấp cửa sổ AJAX Spider, có thể truy cập thông qua menu công cụ.

## Điểm nổi bật

- Miễn phí và mã nguồn mở
- Thân thiện với người dùng
- Hệ thống plugin cá khả năng mở rộng
- Hỗ trợ quét tự động và kiểm thử đa nền tảng
- Tương thích đa nền tảng và dễ tích hợp

## Điểm hạn chế

- Nguy cơ làm hỏng hoặc gián đoạn dữ liệu: Tính năng Active Scan (quét chủ động) gửi các payload tấn công giả lập vào ứng dụng. Nếu chạy trực tiếp trên môi trường Production (thực tế), nó có thể tạo, sửa đổi, hoặc xóa dữ liệu quan trọng hoặc làm sập hệ thống.

- Cảnh báo sai (False Positives/Negatives): Công cụ tự động không thể hiểu hết ngữ cảnh logic nghiệp vụ của ứng dụng, dễ báo động giả gây mất thời gian kiểm tra, hoặc bỏ sót các lỗหổng bảo mật phức tạp.

- Vấn đề pháp lý: Thực hiện quét chủ động hoặc Spider lên một website mà không có sự cho phép bằng văn bản của chủ sở hữu có thể bị xem là hành vi tấn công mạng bất hợp pháp.

- Đòi hỏi kiến thức chuyên môn: Không phải dạng "mì ăn liền", người dùng cần có nền tảng về HTTP, bảo mật ứng dụng web và hiểu rõ kết quả trả về để không cấu hình sai gây quá tải server.

# Burp Suite

## Tổng quan

Burp Suite được hiểu là một ứng dụng được tích hợp nhiều tính năng phục vụ kiểm tra tính bảo mật của ứng dụng web. Các tính năng này sẽ phục vụ kiểm tra bảo mật những thành phần khác nhau trong ứng dụng web hiện đại ngày nay.

Burp Suite giúp người dùng đánh giá các tiêu chí bảo mật web như: Tiến hành kiểm tra cơ chế xác thực, kiểm tra các vấn đề về phiên bản người dùng hay liệt kê cũng như đánh giá các tham số đầu vào của ứng dụng trang web.

- Community Edition (Miễn phí): Bản cơ bản dành cho người học và kiểm thử thủ công; gồm có Proxy (chặn và xem lại HTTP/HTTPS), Repeater, Decoder và bản dùng thử của Intruder.

- Professional Edition (Có phí): Dành cho chuyên gia bảo mật; có thêm trình quét lỗ hổng tự động (Scanner), Burp Collaborator, lưu tệp dự án và không giới hạn Intruder.

- Enterprise Edition (Có phí): Dành cho tổ chức, doanh nghiệp tích hợp quét DAST tự động trong quy trình CI/CD.

## Các tính năng chính

- Proxy: Đứng giữa trình duyệt và máy chủ web, cho phép người dùng chặn (intercept), kiểm tra và chỉnh sửa các gói tin HTTP/HTTPS trước khi chúng được gửi đi hoặc phản hồi về.

- Repeater: Dùng để gửi lại một yêu cầu (request) nhiều lần với các tham số đã bị thay đổi nhằm kiểm tra phản hồi từ máy chủ.

- Intruder: Công cụ tự động hóa để thực hiện tấn công dạng brute-force, fuzzing hoặc dò quét danh sách dữ liệu.

- Target / Site Map: Xây dựng cấu trúc cây thư mục và sơ đồ ứng dụng web, phân loại các vùng nằm trong phạm vi (scope) kiểm thử.

- Extender (BApp Store): Kho tiện ích mở rộng với hơn 300 plugin giúp nâng cao tính năng của phần mềm.

## Điểm nổi bật

- Interception Proxy: được thiết kế để bắt các request từ đó có thể tùy ý sửa đổi trước khi các request này được gửi lên server.

- Repeater: cho phép sử dụng một request trước đó và tùy sửa đổi nội dung request một cách nhanh chóng nhiều lần khác nhau.

- Intruder: tự động hóa việc gửi hàng loạt các request có chứa các payload tương tự nhau lên server.

- Decoder: decode và encode string theo các format khác nhau (URL, Base64, HTML,…).

- Comparer: chỉ ra sự khác nhau giữa các requests/responses

- Extender: API để mở rộng chức năng của Burp Suite. Bạn có thể download các extensions thông qua Bapp Store.

- Spider & Discover Content: crawl link có trong ứng dụng web.
Scanner (chỉ có trong bản Pro): đây là một mô đun khác mạnh mẽ, nó tự động quét các lỗ hổng trong ứng dụng web (XSS, SQLi, Command Injection, File Inclusion,…).

## Điểm hạn chế

- Đòi hỏi thời gian làm quen – Giao diện và độ phức tạp có thể gây khó khăn cho người mới bắt đầu.

- Phiên bản Pro có phí – Các tính năng nâng cao như quét tự động chỉ có trong bản Professional. 

- Tiêu tốn tài nguyên – Có thể chiếm nhiều RAM và CPU khi chạy quét quy mô lớn.

- Giới hạn tự động hóa ở bản miễn phí – Bản Community không hỗ trợ tính năng quét tự động.

# sqlmap

## Tổng quan

sqlmap là một công cụ mã nguồn mở mạnh mẽ giúp tự động hóa quá trình phát hiện và khai thác các lỗ hổng SQL Injection (SQLi) cũng như chiếm quyền điều khiển hệ thống cơ sở dữ liệu. Đây là một trong những công cụ kiểm thử xâm nhập (penetration testing) phổ biến nhất thế giới dành cho các chuyên gia bảo mật và quản trị viên hệ thống.

## Các tính năng chính

- Hỗ trợ đa cơ sở dữ liệu: Tự động nhận diện và tương thích với hơn 40 hệ quản trị cơ sở dữ liệu (DBMS) lớn nhỏ bao gồm MySQL, Oracle, PostgreSQL, Microsoft SQL Server, SQLite, MongoDB, v.v.

- Trích xuất dữ liệu: Tự động quét và liệt kê danh sách cơ sở dữ liệu, bảng, cột, cũng như tải xuống (dump) dữ liệu nhạy cảm hoặc giải mã các chuỗi băm (hash) mật khẩu.

- Chiếm quyền điều khiển (System Takeover): Cho phép đọc/ghi tệp tin trên hệ thống máy chủ, thực thi các lệnh hệ điều hành (OS commands) từ xa hoặc tạo kết nối shell ngược (reverse shell) nếu tài khoản cấu hình có đủ đặc quyền.

## Điểm nổi bật

- Hỗ trợ đầy đủ cho sáu kỹ thuật SQL injection: boolean-based blind, time-based blind, error-based, UNION query, stacked queries và inline queries

- Hỗ trợ kết nối trực tiếp với cơ sở dữ liệu mà không cần thông qua SQL injection, bằng cách cung cấp thông tin đăng nhập DBMS, địa chỉ IP, cổng và tên cơ sở dữ liệu.

- Khả năng tự động hóa cao: Tự động dò tìm sơ đồ cơ sở dữ liệu (schemas), bảng (tables), cột (columns), và trích xuất dữ liệu (exfiltrating data) nhạy cảm một cách nhanh chóng.

- Hỗ trợ kiểm soát hệ thống (Database & System Takeover): Cho phép đọc/ghi tập tin từ hệ thống tập tin (file system) của máy chủ, thực thi các lệnh hệ điều hành (OS commands), và thiết lập kết nối out-of-band khi có đủ quyền.

- Mã nguồn mở và miễn phí: Phát hành dưới giấy phép GPLv2, được cộng đồng an ninh mạng phát triển và cập nhật thường xuyên trên trang chủ

## Điểm hạn chế

- Yêu cầu cấu hình thích hợp: Cài đặt được cấu hình sai có thể dẫn đến dương tính giả hoặc bỏ lỡ các lỗ hổng.

- Ý nghĩa pháp lý: Sử dụng trái phép SQLMap trên các trang web hoặc máy chủ bạn không sở hữu là bất hợp pháp. Luôn luôn có được sự cho phép rõ ràng trước khi thử nghiệm bất kỳ hệ thống.

- WAFs nâng cao: Một số tường lửa ứng dụng web hiện đại (WAF) có thể chặn tải trọng mặc định của SQLMap. Các kịch bản giả mạo tùy chỉnh có thể được yêu cầu để bỏ qua các biện pháp bảo vệ này.


# Tài liệu kham khảo

 \[1\] ZAP - Checkmarx, "Getting Started" [Online]. Available: https://www.zaproxy.org/getting-started/. [Accessed: Oct. 8, 2026] 

 \[2\] Hackerone, "OWASP ZAP: 6 Key Capabilities and a Quick Tutorial" [Online]. Available: https://www-hackerone-com.translate.goog/knowledge-center/owasp-zap-6-key-capabilities-and-quick-tutorial?_x_tr_sl=en&_x_tr_tl=vi&_x_tr_hl=vi&_x_tr_pto=tc. [Accessed: Oct. 8. 2026]

  \[3\] L.N.Son, "Burp Suite Cơ Bản - Dò Lỗ Hổng Bảo Mật Trên Ứng Dụng Web " [Online]. Available: https://viblo.asia/p/burp-suite-co-ban-do-lo-hong-bao-mat-tren-ung-dung-web-L4x5xreqZBM. [Accessed: Oct. 8, 2026] 

  \[4\] PortSwigger, "Burp Suite Community Edition" [Online]. Available: https://portswigger.net/burp/communitydownload. [Accessed: Oct. 8, 2026] 

  \[5\] N.V.Thien, "Burp Suite - "trợ thủ đắc lực" cho tester và pentester trong kiểm tra ứng dụng web" [Online]. Available: https://viblo.asia/p/burp-suite-tro-thu-dac-luc-cho-tester-va-pentester-trong-kiem-tra-ung-dung-web-E375z4GWZGW. [Accessed: Oct. 8, 2026] 

  \[6\] PACISOFT, "Tất tần tật về Burp Suite" [Online]. Available: https://www.pacisoft.vn/tin-san-pham/tat-tan-tat-ve-burp-suite-phan-mem-do-quet-va-phat-hien-lo-hong-ung-dung-web/. [Accessed: Oct. 8, 2026] 

  \[7\] sqlmap, "Intro" [Online]. Available: https://sqlmap.org/. [Accessed: Oct. 8, 2026]

  \[8\] sqlmap, "Features" [Online]. Available: https://github.com/sqlmapproject/sqlmap/wiki/Features. [Accessed: Oct. 8, 2026]

  \[9\] Blog CyberSources, "SQLMap: Your Ultimate Tool for Automating SQL Injection Testing" [Online]. Available: https://cybersources.hashnode.dev/sqlmap. [Accessed: Oct. 8, 2026]

  \[10\] , "" [Online]. Available: . [Accessed: Oct. 8, 2026]