# A4: Khung slide của Lân

> Cập nhật 20/10/2026: dùng [nội dung 7 slide từ kết quả live](slide-live-2026-10-20.md) để ghép bài chung. Outline bên dưới được giữ làm lịch sử, các dòng chờ inference đã có dữ liệu; nhãn/N3 và clip vẫn chưa có.

**Nguyễn Nhật Lân – 23120289.** TỰ ĐỀ XUẤT - CẦN NHÓM CHỐT: bố cục dưới đây để ghép bài chung, không phải slide kết quả đã hoàn thành. Không làm lại phần lý thuyết của các thành viên.

## Slide 1: Phạm vi và kiến trúc thực hiện

- A1 Triage; A3a giao diện AI chung; A2 đối chứng Fuzzer; A3b video.
- Luồng: JSON H1 -> parser -> AI -> schema/ID -> người review -> benchmark N3 của Như.
- Không tự đóng/bỏ alert; Lân không tham gia tạo nhãn chuẩn N2/P2.
- Có thể trình bày code/mẫu kỹ thuật hiện tại nhưng phải ghi **MOCK, DỮ LIỆU TỰ TẠO**.

## Slide 2: Chuẩn hóa ZAP và hợp đồng AI

- Sáu field nguồn ZAP, đơn vị instance/ID; hợp đồng sáu field output.
- Cấu hình/model/giới hạn, cách tách system prompt và evidence không tin cậy.
- [CHỜ SỐ LIỆU THẬT] Commit SUT, ZAP, số record/alert type thực tế và minh họa H1 đã làm sạch.
- [CHỜ SỐ LIỆU THẬT] Cấu hình được nhóm chốt và ảnh output model thật.

## Slide 3: Phương pháp đối chứng Triage

- Như/Phát khóa nhãn độc lập trước khi xem AI; nêu cách chốt bất đồng.
- Như/N3 so thủ công, baseline risk và AI; tối thiểu ba lượt, tính cả thời gian người review.
- Alert chưa chốt phải báo riêng; không coi thiếu bằng chứng là false positive.
- [CHỜ SỐ LIỆU THẬT] Link dataset/ID, bảng nhãn đã chốt, định nghĩa mẫu được N3 tính điểm.

## Slide 4: Kết quả Triage và ca AI sai

- [CHỜ SỐ LIỆU THẬT] Precision/Recall, TP/FP/FN, số alert chưa chốt/AI chưa kết luận.
- [CHỜ SỐ LIỆU THẬT] Lỗi thật bị xếp giả/P4, độ khớp P1–P4, thời gian có review và dao động các lượt.
- [CHỜ SỐ LIỆU THẬT] Một ca AI sai có bằng chứng, cách người review sửa và giới hạn diễn giải.
- Không dùng mục tiêu Recall 90%/tiết kiệm 50% của proposal làm kết quả đã đạt.

## Slide 5: Thiết kế benchmark Fuzzer

- A2 chạy ba nhánh: wordlist tĩnh, AI tĩnh, AI feedback L2 của Long.
- Cùng filter H3, checkpoint, budget và reset; ít nhất ba lượt/nhánh.
- N=50 và định nghĩa bypass đang là tự đề xuất, cần nhóm chốt.
- [CHỜ SỐ LIỆU THẬT] Rule/endpoint và oracle SQLi/XSS đã được rà soát, cấu hình/ngân sách đã duyệt.

## Slide 6: Kết quả Fuzzer

- [CHỜ SỐ LIỆU THẬT] Bảng từng nhánh/lượt: request đã dùng, bypass, request đến lần đầu, chi phí/lỗi API.
- [CHỜ SỐ LIỆU THẬT] Đối chứng hiệu ứng backend và dao động; không kết luận từ status 200.
- [CHỜ SỐ LIỆU THẬT] Link log A2/L2 và nhận xét đã được Long xác minh.

## Slide 7: Minh chứng, giới hạn và bàn giao

- [CHỜ SỐ LIỆU THẬT] Link video AI, cache đúng nguồn, nhãn replay nếu phát lại.
- Giới hạn: bộ dữ liệu nhỏ, phụ thuộc oracle/model, chi phí, AI sai và prompt injection.
- Hiện mới kiểm tra phần mềm bằng unittest/mock; không đồng nghĩa hiệu quả bảo mật được chứng minh.
- Code: `ai/`; bàn giao nội dung cuối cho Phát/P3b sau khi chủ phần xác nhận.
