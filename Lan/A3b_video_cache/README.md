# A3b: Cache và video AI

**BLOCK:** chờ benchmark N3 của Như, kết quả A1/A2 và clip Fuzzer L3 của Long. Hiện chỉ có hai template **rỗng**, không có video hoặc kết quả AI đã lưu:

- [cache/triage_result.json](cache/triage_result.json)
- [cache/fuzzer_result.json](cache/fuzzer_result.json)

`results: []`, `data_origin: empty_template`, thời điểm/hash null không được đưa vào bảng số liệu. `is_replay: true` trong template là nhắc rõ mục đích cache phát lại; không chứng minh đã có run thật.

## Quy trình khi đủ đầu vào

1. Nhận output A1, báo cáo/log N3 đã khóa nhãn, log A2 và clip L3; đối chiếu cùng commit SUT, model, cấu hình, dataset/checkpoint. Chủ mỗi phần xác nhận nguồn và kết quả.
2. Làm sạch secret/PII thủ công trước khi đưa vào cache hoặc quay màn hình. Không quay key, cookie, token, tài khoản thật hoặc log chưa kiểm tra; redaction trong code chỉ là hỗ trợ.
3. Lưu bản kết quả thật cùng UTC timestamp, hash file nguồn, run ID, mode/inference, cấu hình và trạng thái review. Giữ rõ mock/synthetic nếu nguồn là mẫu; không đổi cờ để gọi đó là live. Cấu trúc metadata đang là TỰ ĐỀ XUẤT - CẦN NHÓM CHỐT.
4. Quay Triage: đầu vào H1 -> cách chạy A1 -> output theo ID -> người review -> bảng đối chứng N3 với nguồn. Không cho phần quay sửa nhãn chuẩn đã khóa.
5. Nhận clip L3 của Long, ghép tiếp sau Triage thành video AI; giữ nhãn phần việc và nguồn số liệu. Định dạng/độ dài và template video chờ nhóm/Phát thống nhất.
6. Nếu không có mạng và dùng cache, hiển thị rõ **PHÁT LẠI KẾT QUẢ ĐÃ LƯU**, ghi ngày/model/run ID, đặt `is_replay: true` trong bản metadata trình chiếu. Không cắt dựng làm người xem hiểu là lượt inference mới. Lượt chạy mới dùng `is_replay: false`, nhưng mock vẫn phải ghi là mock.
7. Xem lại toàn bộ video, kiểm tra đọc được output, nhãn replay và không lộ secret; chủ phần xác nhận trước khi gửi Phát ghép bài chung P3b.

Chưa thực hiện bước 1–7 với dữ liệu thật. Không có chức năng tự phát lại/quay/ghép video được triển khai trong lần này; README là quy trình bàn giao khi hết block.
