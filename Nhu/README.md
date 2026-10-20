# Seminar của Thạch Như

**MSSV:** 23120312. **Lớp:** CQ2023/31. **Học phần:** CS423 / CSC13003 - Software Testing, FIT@HCMUS. **Giảng viên:** ThS. Trần Thị Bích Hạnh.

Repo: [KTPM2026/eshop-sut](https://github.com/KTPM2026/eshop-sut), nhánh `nhu/seminar-workspace`, đã đồng bộ `main` tại `c1ed1de`. Phần đóng góp nằm trong `Nhu/`; không sửa source SUT hay phần của thành viên khác. Lượt kiểm chứng N1 trước đó dùng commit `ab5dd4f`.

Ngày 20/10 đã có [báo cáo N4 riêng](N4_slide_baocao/bao-cao-thuc-nghiem.md), [đối chiếu ba output A1 live](N3_benchmark_triage/evidence/live-20261020/README.md) và phương pháp AI-assisted không độc lập theo xác nhận của Như. [PR #1](https://github.com/KTPM2026/eshop-sut/pull/1) dùng để bàn giao; trạng thái merge không chứng nhận các phần thực nghiệm con người chưa đo.

## Đã thực hiện

| Phần | Sản phẩm hiện có |
|---|---|
| [N1: Burp/phân quyền](N1_burp/README.md) | [14 ảnh Burp](N1_burp/evidence/burp-manual-20261019/README.md): 11 Response + 2 Proxy + 1 Scope. Hai ảnh Intruder chứa token giữ private. Cần bổ sung cặp request/response xác minh actor và clip nhóm; XML không bắt buộc. [Lượt API tự động riêng](N1_burp/evidence/main-run-20261016/README.md): 5 pass, 6 vi phạm quyền, 2 phát hiện. |
| [N2: Gán nhãn](N2_gan_nhan/README.md) | Đã có **bản AI-assisted 29 ID: 14 true / 10 false / 5 unknown**, đối chiếu đủ 15 nhóm Phát (loại 2 ngoài scope), 15 HTTP checks trực tiếp + browser và 2 ảnh thật. 10 nhóm cùng kết luận sơ bộ, 3 nhóm cần kiểm chứng chung; chưa là nhãn người độc lập hoặc ground truth. |
| [N3: Đối chiếu live](N3_benchmark_triage/README.md) | Đã tính trên **ba output live, 11 ID API**, đối chiếu tham chiếu assisted: Precision 100%, Recall 85,71%, F1 92,31%, Accuracy 75%, khớp ưu tiên 12,5%. Đây không phải benchmark nhãn chuẩn độc lập; human timing/tiết kiệm giữ null. Bộ chấm độc lập vẫn giữ guard riêng. |
| [N4: Báo cáo](N4_slide_baocao/README.md) | Đã viết [báo cáo thực nghiệm riêng](N4_slide_baocao/bao-cao-thuc-nghiem.md), có ảnh, số liệu, provenance, phân tích bất đồng và giới hạn để ghép bài nhóm. Slide theo mẫu/clip bàn giao riêng. |

Ảnh `burp-manual-20261019` do Như cung cấp, được lưu nguyên bytes và kiểm tra SHA256. Kết quả API/browser do Codex hỗ trợ thực thi được ghi riêng, không gọi là Burp. Review N2 có AI hỗ trợ sau khi tham khảo Phát; chưa phải nhãn người độc lập, ground truth hoặc benchmark thật. Thời gian người chưa đo giữ trống.

**Phạm vi PR:** code, dataset, review có ghi nguồn và minh chứng hiện có. Các việc còn lại dưới đây theo kế hoạch nhóm, không phải yêu cầu định dạng nộp chính thức của giảng viên.

## Việc Như cần tự làm

1. **N1:** bổ sung minh chứng cặp request/response xác định actor/URL và clip bàn giao Long. XML chỉ là một lựa chọn lưu, có thể dùng ảnh ghép hoặc log đã che token. Chi tiết giới hạn của ảnh Intruder nằm trong bộ minh chứng.
2. **N2:** phương pháp AI-assisted không độc lập đã được Như chấp nhận ngày 20/10. Nhãn cuối nếu cần ground truth vẫn phải được người review xác nhận; CORS, Path Traversal và token URL còn thiếu căn cứ. Human timing chưa đo, không hồi dựng hoặc đổi tên bản assisted thành độc lập.
3. **N3:** đã có đối chiếu live 11 ID theo phương pháp assisted. Muốn nâng thành benchmark độc lập hoặc kết luận tiết kiệm thời gian cần nhãn chuẩn/protocol đúng và timing thực đo; không đổi cờ để vượt guard.
4. **N4:** báo cáo riêng đã có; còn slide theo mẫu, clip và ghép bài chung.

Hùng đã bàn giao [ZAP export](../alert/2026-10-14-ZAP-Report-.json) và [setup](../setup_ZAP.md). Chỉ cần hỏi thêm commit scan/request gốc khi thiếu căn cứ cho alert. Có thể kiểm tra metadata/ID bằng `python -X utf8 -m Nhu.check_handoff --output Nhu/outputs/handoff-check-new.json`; tool không tự merge hoặc chứng nhận benchmark.

## File dùng chung

- Nếu nhóm chốt giữ pack 29, Lân chạy AI bằng `Nhu/N2_gan_nhan/data/h1-20261014/a1-input.json`, không dùng raw export chứa traffic ngoài scope/token; cấu hình scope A1 phải giữ đủ API + frontend.
- Như/Phát dùng `dataset.json` cùng thư mục. Hash `source_sha256` là SHA256 bytes của **a1-input.json**, không phải hash export gốc; cả hai hash và mapping về export nằm trong `provenance.json`.
- `nhu-labels.blank.csv` là mẫu chưa điền, giữ nguyên. `Nhu/private/nhu-labels.csv` hiện đã có 29 đề xuất AI-assisted theo yêu cầu của Như, kèm metadata nguồn; không ghi đè hoặc gọi đây là nhãn người độc lập. File private không lên Git; bản assisted chia sẻ nằm trong `N2_gan_nhan/assisted-review/`.
- Nội dung ghép báo cáo/slide: [N4](N4_slide_baocao/README.md). Các bản khóa, timing và output thật sẽ bàn giao sau; không tạo file giả để đủ checklist.

## Kiểm tra và tái lập

Từ root repo, Python 3.12 và Node.js 24. N2 chuẩn bị ZAP dùng dependency có sẵn của Lân:

```powershell
python -m pip install -r ai/requirements.txt
python -X utf8 -m unittest discover -s Nhu/tests -v
python -X utf8 -m unittest discover -s ai/tests -v
python -X utf8 -m Nhu.N2_gan_nhan.prepare_zap --output-dir Nhu/outputs/h1-rebuilt
```

N2/N3 core dùng thư viện chuẩn; adapter ZAP/bundle dùng trực tiếp `ai.A1_ai_triage.parser`. Lệnh chuẩn bị từ chối ghi đè, không truy cập URL trong report và không gọi AI. Pack cũ giữ nguyên provenance của parser lịch sử `Lan/`; pack mới ghi `ai/`. Lệnh N1 và N3 ở README tương ứng.

Tests không gọi model hay thay thế thực nghiệm người/AI. Kiểm chứng HTTP/browser và hash bằng chứng được ghi riêng trong các phần tương ứng.

Phân công N1–N4 lấy từ [đề cương nhóm](https://github.com/KTPM2026/seminar/blob/main/docs/de-cuong-seminar.md); phương pháp từ [proposal](https://github.com/KTPM2026/seminar/blob/main/docs/ai_proposal.md). Đây là tài liệu kế hoạch của nhóm, không phải hướng dẫn upload chính thức của giảng viên. [Nhật ký thực hiện](progress-log.md) ghi rõ phần AI hỗ trợ.

`private/`, `outputs/`, dependency, bytecode và secret được bỏ qua khi đưa Git. Không đưa clone lab hoặc database riêng vào bài nộp.
