# A4: Khung báo cáo triển khai Triage và đối chứng AI

**Nguyễn Nhật Lân – 23120289.** TỰ ĐỀ XUẤT - CẦN NHÓM CHỐT: bố cục bài. Tài liệu này là outline, **không phải báo cáo thực nghiệm đã có kết quả**.

## 1. Phạm vi và trách nhiệm

A1 chuẩn hóa/phân loại alert; A3a cung cấp giao diện dùng chung cho A1/L2; A2 thiết kế chạy đối chứng Fuzzer; A3b chuẩn bị minh chứng/video. Hùng sở hữu môi trường và alert/bộ lọc H1/H3; Long sở hữu Fuzzer L2; Như/Phát tạo nhãn độc lập và Như chấm N3. Không viết lại lý thuyết đã có trong `docs/`.

## 2. Môi trường và đầu vào tái lập

| Thông tin | Giá trị cần điền |
|---|---|
| SUT commit, môi trường/seed/reset, ZAP version/scope | [CHỜ SỐ LIỆU THẬT] H1 |
| JSON gốc đã làm sạch, hash, số type/instance và quy tắc ID/duplicate | [CHỜ SỐ LIỆU THẬT] H1 + nhóm chốt |
| Provider/model snapshot/params và ngân sách được duyệt | [CHỜ SỐ LIỆU THẬT] A3a sau khi nhóm chốt |
| Filter version/rule, endpoint, checkpoint và request budget | [CHỜ SỐ LIỆU THẬT] H3 + L2 + nhóm duyệt |

## 3. Triển khai Triage

Mô tả parser flat/native ZAP, mapping field và cách kiểm tra JSON. Liên kết `A1_ai_triage/parser.py`, `A3a_ai_config/contracts.json`, prompt/adapter trong `client.py`. Phân biệt nullable `is_real`, evidence status và ưu tiên với quyết định cuối của người review.

Giải thích cách tách evidence khỏi chỉ dẫn, kiểm tra ID, từ chối JSON lỗi, không fallback mock khi live lỗi. Nêu giới hạn redaction và việc không có thao tác tự đóng/bỏ alert.

**Minh họa thật:** [CHỜ SỐ LIỆU THẬT] input/output H1 đã làm sạch, hash/run ID, ảnh/log có thể đối chiếu. Không thay bằng `sample_alert_data.json` mà bỏ nhãn mô phỏng.

## 4. Phương pháp và kết quả Triage

Phương pháp theo proposal: Như/Phát gán nhãn độc lập, khóa nhãn, chốt bất đồng; người viết AI không tạo nhãn chuẩn. Như/N3 định nghĩa tập chấm, baseline risk, cách xử lý chưa đủ bằng chứng; so AI với thủ công và baseline, tối thiểu ba lượt cùng cấu hình. Thời gian phải có review của người.

| Lượt/phương pháp | Số record được chấm/chưa chốt | TP/FP/FN; Precision/Recall | Lỗi thật bị xếp giả/P4 | Khớp P1–P4 | Thời gian gồm review |
|---|---|---|---|---|---|
| [CHỜ SỐ LIỆU THẬT] | [CHỜ SỐ LIỆU THẬT] | [CHỜ SỐ LIỆU THẬT] | [CHỜ SỐ LIỆU THẬT] | [CHỜ SỐ LIỆU THẬT] | [CHỜ SỐ LIỆU THẬT] |

Nguồn bảng/định nghĩa công thức và cách xử lý mẫu số 0: [CHỜ SỐ LIỆU THẬT] N3. Không gán 0%/100% khi chưa có dữ liệu hoặc khi không xác định được chỉ số.

**Phân tích lỗi/dao động/giới hạn:** [CHỜ SỐ LIỆU THẬT] ca AI sai, nhận xét có bằng chứng và bảng nhiều lượt từ Như. Không khẳng định đạt ngưỡng trong proposal trước khi có kết quả.

## 5. Phương pháp và kết quả Fuzzer

Ba nhánh wordlist tĩnh, AI tĩnh, AI feedback dùng cùng SUT/filter/reset/budget; tối thiểu ba lượt/nhánh. N=50 và bypass = không bị chặn kèm hiệu ứng được xác minh đang là tự đề xuất. Long phụ trách L2, Hùng cung cấp H3, Như/Phát rà soát checkpoint; A2 hiện chỉ là runner khung.

| Nhánh/lượt | SUT request đã dùng | Số/tỷ lệ bypass đã xác minh | Request đến lần đầu | AI calls/chi phí/lỗi |
|---|---|---|---|---|
| [CHỜ SỐ LIỆU THẬT] | [CHỜ SỐ LIỆU THẬT] | [CHỜ SỐ LIỆU THẬT] | [CHỜ SỐ LIỆU THẬT] | [CHỜ SỐ LIỆU THẬT] |

**Oracle, đối chứng và cách tính tỷ lệ:** [CHỜ SỐ LIỆU THẬT] cấu hình được duyệt, log A2/L2/H3; định nghĩa rõ mẫu số theo request hay theo lượt. Không xem HTTP 200 là bypass; lần không thành công phải ghi chưa đạt trong budget.

## 6. Cache, demo và minh chứng cá nhân

[CHỜ SỐ LIỆU THẬT] clip Triage, clip L3, video AI đã ghép, timestamp/hash và đường dẫn log. Phân biệt inference mới, mock và phát lại cache; nếu replay phải ghi rõ cho người xem. Cache rỗng hiện có không phải minh chứng kết quả.

## 7. Kiểm thử phần mềm và giới hạn

Hiện có unittest với mẫu tự tạo và HTTP transport giả; kiểm tra parser, JSON contract, scope, error/refusal, bảo vệ input và runner bị block. Không dùng số test pass để suy ra Recall hoặc hiệu quả bypass. Chưa có kiểm thử API thật hay EShop trong workspace này.

[CHỜ SỐ LIỆU THẬT] kết quả kiểm thử tích hợp sau H1/H3/L2, thời gian/chi phí, phạm vi dataset và đánh giá khả năng tổng quát hóa. Nêu rõ AI chỉ hỗ trợ, checkpoint/người review vẫn có thể sai và cần đối chứng.

## 8. Nguồn và phụ lục bàn giao

- [Đề cương nhóm](../../docs/de-cuong-seminar.md), [proposal AI](../../docs/ai_proposal.md).
- [Cấu hình và nguồn kỹ thuật A3a](../A3a_ai_config/README.md), [schema JSON](../A3a_ai_config/contracts.json).
- [CHỜ SỐ LIỆU THẬT] H1 input manifest; N3 report; A2/L2 logs; clip và xác nhận của chủ phần trước khi Phát ghép P3b.
