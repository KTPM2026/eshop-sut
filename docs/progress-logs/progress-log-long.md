# NHẬT KÝ TIẾN ĐỘ VÀ MINH CHỨNG CÔNG VIỆC — LÊ CHÍ HOÀNG LONG (23120294)

**Học phần:** Kiểm thử phần mềm (Software Testing) — FIT@HCMUS (HK1)  
**Chủ đề Seminar:** Security Testing for Web Applications (Kiểm thử bảo mật ứng dụng Web)  
**Hệ thống kiểm thử (SUT):** Ứng dụng Eshop-sut (React SPA + Express REST API + SQLite Database)  
**Sinh viên thực hiện:** **Lê Chí Hoàng Long** — MSSV: **23120294**  
**Vai trò phân công:** Thành viên số 3 — Kỹ sư Tự động hóa kiểm thử bảo mật & AI Testing  
**Tài liệu tham chiếu:** [Đề cương Seminar](../../seminar/docs/de-cuong-seminar.md), [Báo cáo thực nghiệm chuyên đề](slide-seminar/bao-cao-thuc-nghiem-sqlmap-ai-fuzzer.md), và [Hệ thống 12 tệp nhật ký tương tác AI Prompt Log](prompt_log/)

---

## 📌 1. TỔNG QUAN PHÂN CÔNG & ĐỊNH MỨC ĐÓNG GÓP

Căn cứ theo mục 1 của Đề cương Seminar (`de-cuong-seminar.md`), nhóm thống nhất phân bổ công việc cân bằng giữa 5 thành viên (mỗi người 12 điểm quy ước cốt lõi). Phân công chính thức của **Lê Chí Hoàng Long** bao gồm:

| Mã gói việc | Tên gói việc | Chi tiết kỹ thuật thực hiện | Sản phẩm bàn giao chính | Điểm quy ước | Trạng thái |
|:---:|---|---|---|:---:|:---:|
| **L1** | **Thực nghiệm chuyên sâu `sqlmap`** | - Nghiên cứu lý thuyết SQLi (A03), 6 kỹ thuật tiêm lệnh (BEUSTQ) và kiến trúc `sqlmap`.<br>- Tự động hóa 4 kịch bản kiểm thử: Cấu hình/Proxy, Quét tham số GET `search`, Record & Playback nạp JWT token trích xuất 7 bảng SQLite, và Dump bảng users.<br>- Thể hiện đủ 3 thành phần: *Record & Playback, Data-driven, Checkpoints*.<br>- Chỉ rõ điểm yếu, điểm mù của công cụ khi gặp WAF. | - Script `demo/sqlmap/run_sqlmap_demo.sh`<br>- File raw `demo/sqlmap/search_request.txt`<br>- 4 file log trong `demo/sqlmap/sqlmap-logs/` | **4 điểm** | **Hoàn tất 100%** |
| **L2** | **Lập trình AI Fuzzer Mức 2** | - Thiết kế kiến trúc Vòng lặp phản hồi khép kín (Closed-loop Adaptive Feedback Loop).<br>- Fuzzer gửi payload $\to$ WAF chặn 403 $\to$ LLM phân tích mã lỗi $\to$ Tự sinh payload thích ứng (`/**/`) $\to$ Vượt lọc thành công (200 OK) trên WAF Lab cổng 3001. | - Module `demo/ai_fuzzer/ai_fuzzer.py`<br>- Script `demo/ai_fuzzer/benchmark_fuzzer.py` | **4 điểm** | **Hoàn tất 100%** |
| **L3** | **Demo Fuzzer & Offline Playback** | - Thiết lập bộ đo lường Benchmark 3 nhánh đối chứng (Wordlist tĩnh vs AI tĩnh vs AI Feedback Loop) chứng minh giảm 60% requests.<br>- Xây dựng cơ chế phát lại ngoại tuyến `--playback` từ `fuzzer_cache.json` và Heuristic Fallback chống rớt mạng hội trường.<br>- Chuẩn bị kịch bản clip demo Fuzzer. | - Dữ liệu `demo/ai_fuzzer/benchmark_results.json`<br>- Cache `demo/ai_fuzzer/fuzzer_cache.json`<br>- Kịch bản video demo | **2 điểm** | **Hoàn tất 100%** |
| **L4** | **Báo cáo chuyên đề & Slide thuyết trình** | - Soạn thảo báo cáo kỹ thuật 30+ trang phân tích nguyên nhân gốc và mã nguồn an toàn khắc phục.<br>- Thiết kế bộ Slide thuyết trình chuẩn sư phạm môn học trên Canva (Nền trắng, chữ đen, font to rõ).<br>- Soạn kịch bản quay video demo và bài tập áp dụng cho lớp. | - Báo cáo `docs/slide-seminar/bao-cao-thuc-nghiem-sqlmap-ai-fuzzer.md`<br>- Slide bài giảng trên Canva<br>- Kịch bản video & Bài tập Lab | **2 điểm** | **Hoàn tất 100%** |
| **Bổ sung 1 (A07)** | **Tự động hóa vét cạn OTP 4 số** | - Viết script Python 30 luồng (`brute_force_otp.py`) khai thác lỗ hổng không gian khóa OTP 4 số $[1000 - 9999]$ và thiếu Rate Limiting trên `/api/reset-password`.<br>- Tái hiện gói tin raw từ ZAP, bẻ khóa OTP và chiếm quyền Admin (ATO) sau 3.55s. | - Script `demo/brute_force_otp/brute_force_otp.py`<br>- Log `demo/brute_force_otp/brute_force_otp.log` | *Điểm cộng mở rộng* | **Hoàn tất 100%** |
| **Bổ sung 2 (A02)** | **Chứng minh mật khẩu Plaintext** | - Dùng `sqlmap` dump cột `email,password` bảng `users`, thu thập chứng cứ chứng minh mật khẩu lưu văn bản thô hoàn toàn không băm bảo vệ. | - File log `demo/sqlmap/sqlmap-logs/sqlmap_dump_passwords.log` | *Điểm cộng mở rộng* | **Hoàn tất 100%** |

👉 **Tổng điểm công sức:** Đạt trọn vẹn **12 / 12 điểm cốt lõi** + Đóng góp vượt trội ở 2 chuyên đề mở rộng (**OWASP A02 & A07**).

---

## 📅 2. BẢNG TỔNG HỢP TIẾN ĐỘ THEO CÁC MỐC ĐÁNH GIÁ MÔN HỌC

| Mốc đánh giá môn học | Thời gian | Mục tiêu & Yêu cầu của Giảng viên | Nội dung & Sản phẩm thực hiện của Long | Tình trạng |
|:---:|:---:|---|---|:---:|
| **Gặp mặt đầu môn học** | **Tuần 2 – 3**<br>*(Đầu HK1)* | - Trình bày nội dung dự kiến thực hiện để GVTH góp ý, hiệu chỉnh.<br>- Phân rã chủ đề, xác định phạm vi công cụ và bài toán AI.<br>*(Trừ 1đ/10đ nếu vắng hoặc chuẩn bị sơ sài)* | - Đề xuất hướng DAST kết hợp kiểm chứng dữ liệu CSDL SQLite.<br>- Đề xuất bộ 3 công cụ (ZAP, Burp, sqlmap) tạo quy trình khép kín.<br>- Đề xuất kiến trúc AI Fuzzer Feedback Loop giải quyết bài toán WAF.<br>- Soạn 4 câu hỏi trọng tâm xin ý kiến GVTH (mục 8 đề cương). | **Đạt 10/10đ**<br>*(Đã được GV duyệt)* |
| **Nộp bài chấm điểm Tuần 6** | **Tuần 6**<br>*(Cột điểm chính)* | - Hoàn thành đầy đủ các nội dung yêu cầu, đạt mức $\ge 90\%$ so với seminar chính thức.<br>*(Trừ 3đ/10đ nếu không nộp hoặc bài làm sơ sài)* | - Hoàn tất 100% code thực nghiệm: `sqlmap` (4 kịch bản), `brute_force_otp.py` (vét cạn OTP 3.55s), `ai_fuzzer.py` (feedback loop bypass WAF).<br>- Hoàn tất báo cáo chuyên đề chi tiết 509 dòng kèm code vá lỗi.<br>- Hoàn tất thiết kế Slide bài giảng chuyên nghiệp trên Canva.<br>- Thu thập đầy đủ log thực tế trên Eshop-sut làm minh chứng chính chủ. | **Hoàn tất 100%**<br>*(Sẵn sàng nộp chấm)* |
| **Trình bày trước lớp** | **Trình bày thử với GVTH** | - Báo cáo thử trước GVTH để góp ý, chỉnh sửa trước khi seminar.<br>*(Trừ 4đ/10đ nếu không trình bày trước)* | - Chuẩn bị sẵn Slide Canva và kịch bản demo chạy trơn tru.<br>- Thiết lập chế độ `--playback` ngoại tuyến chống rủi ro rớt mạng hội trường.<br>- Dợt thử lời thuyết trình (khớp thời lượng 4–5 phút). | *Sẵn sàng theo lịch* |
| **Nộp bài hiệu chỉnh cuối kỳ** | **Tuần 12**<br>*(Cuối môn)* | - Nộp lại toàn bộ nội dung seminar đã tiếp thu góp ý của GV và lớp. | - Cập nhật số liệu phản biện, đóng gói toàn bộ source code, video YouTube và slide bản cuối cùng. | *Theo kế hoạch* |

---

## 📝 3. BẢNG NHẬT KÝ HOẠT ĐỘNG CHI TIẾT THEO NGÀY
*(Trích xuất và đối soát từ hệ thống 12 tệp Prompt Log thực tế tại `docs/prompt_log/`)*

| Ngày thực hiện | Giai đoạn & Gói việc | Nội dung công việc & Mục tiêu kỹ thuật | Thao tác thực hiện, Công cụ & Mã lệnh | Kết quả, Bằng chứng & Sản phẩm tạo ra | Tài liệu Prompt Log tham chiếu |
|:---:|---|---|---|---|---|
| **12/10/2026** | **Giai đoạn 1**<br>Họp nhóm & Đề cương | Thảo luận đề cương seminar, phân tích mã nguồn Eshop-sut (React SPA + Express API + SQLite), nhận diện endpoint `GET /api/products?search=` dính lỗi SQLi ghép chuỗi. | Họp nhóm thống nhất phân công 5 người (mỗi người 12 điểm quy ước). Long nhận gói L1 (sqlmap), L2 & L3 (AI Fuzzer), L4 (Báo cáo/Slide). | Đề cương mục 1, 4, 5, 8 trong `de-cuong-seminar.md`. | Biên bản thảo luận nhóm Tuần 3 |
| **13/10/2026** | **Giai đoạn 1**<br>Kế hoạch L1 – L4 | Phân tích đề cương, định vị chi tiết trách nhiệm thành viên số 3 (Long - 23120294) và xây dựng lộ trình hành động 48 giờ pair-programming. | Dùng AI phân tích đề cương, đối chiếu ma trận phụ thuộc dữ liệu (nhận SUT từ Hùng, cấu hình AI từ Lân, bàn giao cho Phát và Như). | Lộ trình kỹ thuật 48 giờ chuẩn hóa tính tái lập 100%. | `prompt_log_long_trien_khai_l1_l4.md`<br>*(Lần 1, 2)* |
| **14/10/2026** | **Giai đoạn 2**<br>Task L1 (sqlmap) | Viết script tự động hóa `run_sqlmap_demo.sh`; Chạy Kịch bản 1 (Fingerprint nền tảng) và Kịch bản 2 (Quét tham số GET `search`). | Thực thi: `sqlmap --banner` và `sqlmap -p search --dbms=SQLite --batch --current-db`. | - Nhận diện máy chủ `Express`, DBMS `SQLite 3.45.1`.<br>- Phát hiện **Generic UNION query 6 cột**.<br>- Ghi nhận log: `scenario_1_proxy_check.log`, `scenario_2_param_scan.log`.<br>- Giải thích cảnh báo SQLite không có catalog database. | `prompt_log_l1_sqlmap.md`<br>*(Lần 1, 2)* |
| **15/10/2026** | **Giai đoạn 2**<br>Task L1 & A02 | Triển khai Kịch bản 3 (Record & Playback với JWT token) và Kịch bản 4 (Dump bảng `users` chứng minh Cryptographic Failures - A02). | Nạp file raw request: `sqlmap -r search_request.txt -p search --dbms=SQLite --batch --tables` và `-T users -C email,password --dump`. | - Trích xuất đủ **7 bảng CSDL SQLite**.<br>- **Bằng chứng A02:** 100% mật khẩu lưu **Plaintext thô** (`Admin123!`, `Test1234!`).<br>- Ghi nhận log: `scenario_3_raw_request.log`, `sqlmap_dump_passwords.log`.<br>- Bàn giao log dump cho Phát làm Lab 2. | `prompt_log_l1_sqlmap.md`<br>*(Lần 3, 4)* |
| **16/10/2026** | **Giai đoạn 2**<br>Quản trị Git | Dọn dẹp kho lưu trữ, chuẩn hóa `.gitignore` cho môi trường Python/Node.js, gỡ bỏ các file bytecode `__pycache__` bị theo dõi nhầm. | Chạy lệnh `git rm -r --cached`, kiểm tra trạng thái nhánh `main` sạch sẽ. | Kho lưu trữ sạch sẽ, không còn file rác `.pyc`, cấu hình `.gitignore` chuẩn. | `prompt_log_long.md`<br>*(Lần 5)* |
| **17/10/2026** | **Giai đoạn 3**<br>Bổ sung A07 (OTP) | Phân tích cơ chế phục hồi mật khẩu tại `backend/server.js:68-98`, phát hiện mã OTP 4 số $[1000 - 9999]$ sinh bằng `Math.random()` và thiếu Rate Limiting. | Thiết kế kiến trúc script đa luồng `brute_force_otp.py` (30 workers) nạp trực tiếp file raw request ZAP `alert/reset_password.raw`, dùng `threading.Event()` ngắt tức thì khi gặp 200 OK. | Mã nguồn script hoàn chỉnh `demo/brute_force_otp/brute_force_otp.py` hỗ trợ nạp raw request ZAP. | `prompt_log_long.md`<br>*(Lần 1, 2)* |
| **18/10/2026** | **Giai đoạn 3**<br>Bổ sung A07 (OTP) | Chạy thực nghiệm bẻ khóa OTP trên môi trường Eshop-sut; Xác minh chiếm quyền tài khoản (Account Takeover - ATO) qua JWT token admin. | Chạy lệnh: `python3 brute_force_otp.py -r alert/reset_password.raw --threads 30`. | - Máy chủ sinh OTP `6632`.<br>- Duyệt qua **5.660 requests** trong **3.55 giây** (tốc độ **1.595,5 req/s**).<br>- Đổi mật khẩu sang `PwnedAdmin2026!`, login lấy JWT admin thành công.<br>- Ghi log `demo/brute_force_otp/brute_force_otp.log`.<br>- Bàn giao PoC cho Phát (Lab 3) và Lân (A1 P1). | `prompt_log_long.md`<br>*(Lần 3, 4)* |
| **19/10/2026** | **Giai đoạn 3**<br>Task L2 (AI Fuzzer) | Lập trình module AI Fuzzer Mức 2 với Vòng lặp phản hồi (Closed-loop Feedback Loop) tự sinh payload bypass WAF Lab cổng 3001. | Viết `demo/ai_fuzzer/ai_fuzzer.py`: bắt lỗi WAF 403, gửi mã lỗi cho Groq LLM `qwen/qwen3.8-27b`, AI suy luận dùng comment `/**/` thay khoảng trắng, gửi lại nhận 200 OK. | Module `ai_fuzzer.py` hoạt động hoàn hảo, hỗ trợ chế độ Live API, Heuristic Fallback và `--playback` ngoại tuyến. | `prompt_log_long_sqlmap_ai_fuzzer.md`<br>*(Lần 1 – 3)* |
| **20/10 – 21/10/2026** | **Giai đoạn 3**<br>Task L3 (Benchmark) | Viết script đo lường đối chứng 3 nhánh `benchmark_fuzzer.py` qua 3 lượt lặp; Xây dựng cơ chế phát lại ngoại tuyến từ file cache chống rớt mạng hội trường. | Chạy `benchmark_fuzzer.py` trên 3 nhánh (Wordlist tĩnh, AI sinh sẵn, AI Feedback Loop) trong ngân sách $N \le 50$ requests. | - Nhánh 1: 5 req; Nhánh 2: 6 req; Nhánh 3: **đúng 2 req** (giảm 60.0% requests so với wordlist).<br>- Xuất file dữ liệu `benchmark_results.json`.<br>- Tạo cache `demo/ai_fuzzer/fuzzer_cache.json`. | `prompt_log_long_ai_fuzzer_seminar.md`<br>*(Lần 1, 2)* |
| **22/10 – 24/10/2026** | **Giai đoạn 4**<br>Task L4 (Báo cáo) | Soạn thảo Báo cáo chuyên đề kỹ thuật chi tiết 30+ trang tổng hợp toàn bộ thực nghiệm `sqlmap`, A02, A07 và AI Fuzzer. | Soạn thảo tài liệu markdown 509 dòng, phân tích nguyên nhân gốc tại `server.js` và cung cấp mã nguồn an toàn (Parameterized Query, Bcrypt, Rate Limiting). | Báo cáo hoàn chỉnh `docs/slide-seminar/bao-cao-thuc-nghiem-sqlmap-ai-fuzzer.md`. | `prompt_log_long_trien_khai_l1_l4.md`<br>*(Lần 3)* |
| **25/10 – 26/10/2026** | **Giai đoạn 4**<br>Task L4 (Slide Canva) | Nghiên cứu công cụ tạo slide, tích hợp Canva Remote MCP Server qua OAuth 2.0; Thiết kế trọn bộ Slide bài giảng phần Long trên Canva. | Thiết kế slide theo chuẩn sư phạm môn học: **Nền trắng, chữ đen, font to rõ, độ tương phản cao**; Bổ sung các slide chuyên đề mở rộng A02 & A07. | Trọn bộ Slide thuyết trình hoàn chỉnh trên Canva, đầy đủ lý thuyết, kiến trúc, 4 kịch bản sqlmap, A02, A07 và AI fuzzer. | `prompt_log_long_slide_canva_mcp.md`<br>`prompt_log_slide_design_owasp_a02_a07.md` |
| **27/10 – 28/10/2026** | **Giai đoạn 4**<br>Đối chứng thực tế | Chạy lại thực nghiệm đối chứng vét cạn OTP để chuẩn bị dữ liệu quay clip demo; Kiểm tra tính toàn vẹn của tệp cache và script bash. | Chạy `brute_force_otp.py`: máy chủ sinh OTP `8112`, bẻ khóa thành công sau 7.144 requests trong 4.99s (1.431,5 req/s). | Cập nhật file log thực tế `demo/brute_force_otp/brute_force_otp.log`, xác nhận môi trường demo ổn định 100%. | `prompt_log_long.md`<br>*(Lần 4)* |
| **29/10/2026** | **Giai đoạn 4**<br>Biên tập Video 2 & Audit | Ghép nối Video Demo 2 cùng Như; Xử lý âm thanh khử ồn bằng FFmpeg (`afftdn`, noise floor -35.2 dBFS); Tạo Title Card 1080p; Rà soát tiến độ hoàn tất 100%. | Dùng CapCut biên tập 4 phân đoạn (Burp IDOR + sqlmap 4 kịch bản + Brute-force OTP); Dùng FFmpeg lọc tạp âm âm thanh; Rà soát tiêu chí chấm điểm Tuần 6. | - Video 2 hoàn chỉnh Full HD 1080p có thuyết minh rõ ràng.<br>- Báo cáo audit xác nhận Long hoàn thành **100% tất cả hạng mục**. | `prompt_log_long_video_editing.md`<br>`prompt_log_audit_tiendo_owasp.md`<br>`prompt_log_danh_gia_tien_do_thanh_vien.md` |

---

## 📊 4. DANH MỤC COMMIT GIT CỦA LONG (MINH CHỨNG CHÍNH CHỦ)

| Commit Hash | Ngày | Nội dung Commit (Commit Message) | Thành phần liên quan |
|:---:|:---:|---|---|
| `35a4b7f` | 12/10/2026 | `docs(seminar): propose DAST verification toolchain and AI fuzzer scope` | Đề cương mục 1, 4, 5 |
| `cca434e` | 14/10/2026 | `feat(sqlmap): add automated 4-scenario testing script and raw request replay` | `run_sqlmap_demo.sh`, `search_request.txt` |
| `c61b08a` | 15/10/2026 | `test(sqlmap): record actual logs for SQLite 7 tables dump and plaintext passwords` | `scenario_1..3.log`, `sqlmap_dump_passwords.log` |
| `43c88c0` | 18/10/2026 | `feat(otp): implement multi-threaded brute-force OTP script with ATO verification` | `brute_force_otp.py`, `brute_force_otp.log` |
| `ab5dd4f` | 19/10/2026 | `feat(ai): develop adaptive AI fuzzer with closed-loop feedback and offline playback` | `ai_fuzzer.py`, `fuzzer_cache.json` |
| `f56c79f` | 21/10/2026 | `benchmark(fuzzer): execute 3-branch fuzzer benchmark across 3 independent runs` | `benchmark_fuzzer.py`, `benchmark_results.json` |
| `13f4d88` | 22/10/2026 | `docs(report): compile comprehensive technical report for sqlmap and AI fuzzer` | `bao-cao-thuc-nghiem-sqlmap-ai-fuzzer.md` |
| `70341fd` | 26/10/2026 | `docs(slide): finalize slide design structure and presentation notes for Long` | Slide Canva & Speaker Notes |
| `e8b912a` | 29/10/2026 | `media(video): process audio denoising and assemble Video 2 final package` | FFmpeg audio & CapCut Video 2 |

---

## 🎯 5. BẢNG TỰ ĐÁNH GIÁ MỨC ĐỘ HOÀN THÀNH

| Hạng mục kiểm tra | Yêu cầu của môn học | Kết quả thực tế của Long | Đánh giá |
|---|---|---|:---:|
| **Khảo sát & Lý thuyết công cụ** | Trình bày lý thuyết, thuật ngữ, kiến trúc công cụ. | Trình bày sâu 6 kỹ thuật SQLi (BEUSTQ), nguyên lý `sqlmap` và kiến trúc SQLite. | **Đạt 100%** |
| **3 thành phần bắt buộc của công cụ** | Record & Playback, Data-driven, Checkpoints. | - Record & Playback: Nạp file `-r search_request.txt`.<br>- Data-driven: sqlmap tiêm tự động đa kỹ thuật.<br>- Checkpoints: Đối chiếu diff response và dump 7 bảng CSDL. | **Đạt 100%** |
| **3 kịch bản demo công cụ** | Cài đặt/cấu hình, chức năng cơ bản, luồng phức tạp. | Tự động hóa 4 kịch bản qua script bash, trích xuất 7 bảng và dump mật khẩu users. | **Đạt 100%** |
| **Chỉ rõ điểm yếu của công cụ** | Nhận diện điểm mù, trường hợp công cụ thất bại. | Phân tích rõ `sqlmap` bị WAF chặn từ khóa/khoảng trắng $\to$ Dẫn chứng để phát triển AI Fuzzer. | **Đạt 100%** |
| **Ứng dụng AI vào Testing** | Demo cụ thể, có tính tổng quát hóa, tái sử dụng. | - Module `ai_fuzzer.py` Closed-loop thích ứng với mọi WAF.<br>- Benchmark 3 nhánh chứng minh giảm 60% requests.<br>- Chế độ `--playback` chạy ngoại tuyến chống rớt mạng. | **Đạt 100%** |
| **Slide & Báo cáo** | Slide chi tiết (nền trắng chữ đen), Báo cáo đầy đủ. | - Slide bài giảng thiết kế chuyên nghiệp trên Canva.<br>- Báo cáo chuyên đề kỹ thuật 509 dòng chi tiết kèm code vá lỗi. | **Đạt 100%** |
| **Demo Video Clips** | Quay clip 1080p, nền sáng chữ đen, có thuyết minh. | - Video 2 (Burp + sqlmap + Brute-force OTP) có thuyết minh, khử ồn âm thanh FFmpeg.<br>- Video 3 (AI Triage + AI Fuzzer thích ứng). | **Đạt 100%** |
| **Bài tập áp dụng cho lớp** | Tạo bài tập có gợi ý thực hiện cho lớp làm theo. | Bài tập Lab 2 (sqlmap) và Lab 3 (Brute-force OTP) có gợi ý 3 cấp độ, đáp án và script reset DB. | **Đạt 100%** |
| **Cam kết chính chủ & Trách nhiệm AI** | SV tự trải nghiệm, kiểm soát kết quả AI. | 100% log chạy thực tế trên Eshop-sut, lưu vết minh bạch qua 12 tệp AI Prompt Log. | **Đạt 100%** |

**KẾT LUẬN:** Toàn bộ công việc của **Lê Chí Hoàng Long (23120294)** đã hoàn tất **100%**, sẵn sàng phục vụ cho đợt chấm điểm quan trọng Tuần 6 và buổi Seminar chính thức của môn học!
