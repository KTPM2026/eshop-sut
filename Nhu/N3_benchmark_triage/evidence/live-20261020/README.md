# Đối chiếu Triage live ngày 20/10/2026

**Tham chiếu AI-assisted, không độc lập; không phải ground truth hoặc benchmark người-AI đã hoàn tất.** Như xác nhận chấp nhận cách trình bày này ngày 20/10. Không ghi nhận thay Phát việc chốt nhãn và không tạo thời gian người review.

- [comparison.json](comparison.json): tham chiếu 11 ID được lấy nguyên quyết định từ bản Như 29 ID, kết quả từng ID/run, baseline risk, timing có ghi giới hạn và SHA256 nguồn.
- [comparison.csv](comparison.csv): chỉ số có điều kiện theo tham chiếu assisted, luôn giữ `is_benchmark_result=False`; thời gian người/tiết kiệm để trống.
- [input.json](input.json): bản LF nguyên bytes từ bundle khóa 11 ID API của Lân.
- [run-1.json](run-1.json), [run-2.json](run-2.json), [run-3.json](run-3.json): bản nguyên bytes từ [commit 9fd8512](https://github.com/KTPM2026/eshop-sut/commit/9fd85126f44a0b323c3b6b475a248bd409272c18), không phải lượt inference mới do Như chạy.

Hash source của run là biến thể CRLF đã được tính lại từ input LF; không sửa metadata run. Ba lượt đủ 11 ID, cùng config/prompt/schema, run ID/thời điểm và response ID không bị dùng lại. Công cụ chỉ kiểm tra artifact được cung cấp, không xác minh trực tiếp tài khoản dịch vụ AI.

Tham chiếu có 7 true/1 false/3 unknown. Trên 8 nhãn đã rõ, mỗi run có TP=6, FP=0, TN=0, FN kết luận false=0, abstain trên true=1 và trên false=1. Precision 100%, Recall 85,71%, F1 92,31%, Accuracy 75%, khớp ưu tiên 12,5%. Đây là **độ khớp có điều kiện**, không chứng minh hiệu quả độc lập; sáu nhãn true là instance thuộc hai nhóm header/hardening.

SQLi ở tham chiếu là true/P1 do có kiểm chứng HTTP bổ sung; AI chỉ đọc evidence scan lỗi 500 nên giữ null/P2. Ba CORS unknown không tính là đúng hoặc false. Thời gian pipeline/người và mức tiết kiệm giữ null; API latency không được đổi tên thành human timing. Phân tích đầy đủ trong [báo cáo N4](../../../N4_slide_baocao/bao-cao-thuc-nghiem.md).

Tái lập ra thư mục mới:

```powershell
python -X utf8 -m Nhu.N3_benchmark_triage.live_review --ref 9fd85126f44a0b323c3b6b475a248bd409272c18 --accept-assisted-reference --output-dir Nhu/outputs/live-recheck-new
```
