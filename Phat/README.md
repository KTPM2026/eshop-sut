# Không gian làm việc của Nguyễn Đức Phát

**MSSV:** 23120317. Cập nhật: 17/10/2026.

Phạm vi **P1, P2, P3 (P3a/P3b), P4** theo [đề cương](../docs/de-cuong-seminar.md) và [hướng dẫn Lab](../../seminar/docs/lab-huong-dan.md). Không thay phần N/L/A/H của các thành viên khác, không viết thay nhãn chuẩn (chỉ gán nhãn độc lập của mình), không viết thay phần báo cáo của người khác khi đóng gói P3b.

> ⚠️ **Phần lớn tài liệu trong thư mục này là KHUNG/ TEMPLATE, chưa phải kết quả thực nghiệm.** Mọi ô `[CHỜ TỰ CHẠY]` phải do Phát tự chạy tool thật trên máy rồi điền. AI không chạy được ZAP/sqlmap tương tác và không quay video.

## Trạng thái bàn giao

| Phần | Đã có (AI dựng được từ source) | Còn chờ (Phát tự làm) |
|---|---|---|
| P1 | `xss-payloads.txt`; script reset DB; ghi chú xác minh 3 giá trị lab + sửa luồng XSS; đã vá các chỗ sai trong `lab-huong-dan.md` | Chạy thật ZAP Fuzzer (Lab 1) và sqlmap (Lab 2), chụp ảnh/log; quay clip; xác nhận "chạy được" trên máy |
| P2 | Template bảng gán nhãn với 15 loại alert thật đã liệt kê sẵn từ `alert/2026-10-14-ZAP-Report-.json` | **Tự gán nhãn độc lập** (thật/giả/chưa đủ bằng chứng, ưu tiên, lý do, timing) — chưa xem N2/kết quả AI; sau đó chốt bất đồng với Như |
| P3a | Checklist pilot + bảng ghi lỗi/timing rỗng | Chạy pilot 2 Lab, điền kết quả thật |
| P3b | Checklist đóng gói theo mục 7 đề cương | Chờ 3 video + benchmark N3/A2 của nhóm; đóng gói bản cuối |
| P4 | Outline slide + outline báo cáo phần Lab | Điền số liệu/ảnh thật sau khi chạy pilot |

## Cơ sở dữ kiện đã xác minh từ source (ngày 17/10/2026)

Ba giá trị mà `lab-huong-dan.md` ghi là "sinh viên phải tự xác minh" — đã đối chiếu trực tiếp mã nguồn EShop:

| Giá trị | Kết luận | Bằng chứng |
|---|---|---|
| Endpoint tìm kiếm | **`GET /api/products?search=`** | `backend/server.js:141-144`; `search.req` đã dùng đúng |
| Câu truy vấn (gốc lỗi SQLi) | `SELECT * FROM products WHERE name LIKE '%${searchQuery}%'` — nối chuỗi | `backend/server.js:144` |
| Tên DB SQLite | **`main`** | File sqlite đơn, mặc định `main`; `--tables` dùng trực tiếp không cần `-D` |
| Bảng dữ liệu người dùng | **`users`** tồn tại (cột `id,name,email,password,role,...`), seed `admin@eshop.com` | `backend/database.js:50-64, 91-92` |
| Sink Reflected XSS | `Home.jsx:64` `dangerouslySetInnerHTML={{ __html: search }}` — ở **frontend SPA**, không phải JSON API | `frontend-web/src/pages/Home.jsx:63-64` |

> **Lưu ý luồng Lab 1:** XSS phản xạ xảy ra ở frontend (route SPA) khi render tham số `search`. ZAP Fuzzer nhắm vào API `/api/products?search=` lại trả **JSON**, nên payload không tự "thực thi trong trình duyệt" ngay trong response của Fuzzer. Phát cần tự kiểm chứng điểm này khi chạy pilot (xem `P1_labs/lab-verify-notes.md`).

## Tài liệu từng phần
- [P1: labs, payload, reset DB, ghi chú xác minh](P1_labs/README.md)
- [P2: template gán nhãn alert độc lập](P2_nhan_alert/README.md)
- [P3: pilot + đóng gói](P3_pilot_donggoi/README.md)
- [P4: outline slide & báo cáo](P4_slide_baocao/slide-outline.md)

## Kiểm chứng còn thiếu (chưa làm được tại thời điểm này)
Chưa chạy ZAP/sqlmap thật, chưa quay video, chưa gán nhãn độc lập, chưa đóng gói bản cuối. Các số liệu Precision/Recall, timing, tỷ lệ phát hiện đều chưa có — không điền số khi chưa chạy.
