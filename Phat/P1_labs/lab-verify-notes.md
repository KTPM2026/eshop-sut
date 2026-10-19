# P1 - Ghi chú xác minh Lab & những chỗ đã sửa trong `lab-huong-dan.md`

**Phát (23120317) · 17/10/2026.** Tài liệu này ghi lại các giá trị đã kiểm chứng từ source EShop và các chỗ đã vá trong hướng dẫn Lab. Mục "CÒN PHẢI TỰ CHẠY" là phần không thể thay thế bằng đọc code.

## 1. Ba giá trị "sinh viên tự xác minh" — đã đối chiếu source

| Giá trị | Bản Lab cũ ghi (đoán) | Thực tế | Nguồn |
|---|---|---|---|
| Endpoint tìm kiếm | `/search` hoặc `/api/search` | **`GET /api/products?search=`** | `backend/server.js:141-144` |
| Tên DB SQLite | `main` / `SQLite_masterdb` | **`main`** (chỉ `main`; `SQLite_masterdb` là sai) | File sqlite đơn |
| Bảng người dùng | `users`? | **`users`** có thật | `backend/database.js:50-64` |

Câu truy vấn gây lỗi (để giải thích root cause ở Lab 2):
```js
// backend/server.js:144
const query = `SELECT * FROM products WHERE name LIKE '%${searchQuery}%'`;
```
Nối chuỗi trực tiếp tham số người dùng vào SQL → SQL Injection (CWE-89). Khắc phục: parameterized query / prepared statement.

## 2. Điểm quan trọng về luồng Lab 1 (XSS) — cần đọc kỹ

- Sink XSS nằm ở **frontend** `frontend-web/src/pages/Home.jsx:63-64`:
  ```jsx
  {search && !errorHtml && (
    <span dangerouslySetInnerHTML={{ __html: search }} />
  )}
  ```
  Tham số `search` được render thẳng vào HTML, không escape → **Reflected XSS** khi người dùng duyệt route SPA với từ khóa chứa payload.
- Ngoài ra còn một sink thứ hai: khi backend lỗi SQL, thông điệp lỗi `<h1>Database Error</h1><p>${err.message}</p>` (`server.js:149-151`) được frontend render qua `dangerouslySetInnerHTML={{ __html: errorHtml }}` (`Home.jsx:71`) → có thể dẫn tới lộ thông tin/HTML injection qua thông báo lỗi.
- **Hệ quả cho Lab 1:** ZAP Fuzzer bắn payload vào API `/api/products?search=` sẽ nhận **JSON** (danh sách sản phẩm), payload KHÔNG tự thực thi trong response JSON đó. Việc "thực thi trong trình duyệt" chỉ xảy ra khi payload được render qua route frontend.
- **Khuyến nghị khi chạy pilot:** kiểm chứng XSS bằng cách duyệt frontend `http://localhost:5173` với payload trong ô tìm kiếm (quan sát alert box / payload chưa escape trong DOM), và dùng ZAP Fuzzer để minh họa bước "bơm payload + so sánh kích thước/encoding response". Ghi rõ sự phân biệt này trong báo cáo thay vì khẳng định Fuzzer API trực tiếp chứng minh thực thi trình duyệt.

## 3. Các chỗ đã vá trong `seminar/docs/lab-huong-dan.md`
1. Endpoint tìm kiếm: sửa thành `GET /api/products?search=`.
2. Bước lấy `search.req`: đã có sẵn file `eshop-sut/search.req` trỏ đúng endpoint (kèm Authorization Bearer token mẫu).
3. Lệnh sqlmap: SQLite là file đơn → dùng `--tables` trực tiếp, bỏ bước `--dbs`/`-D` của MySQL/Postgres; nếu cần chỉ DB thì là `main`.
4. Hint 3 (Lab 2): bỏ tên sai `SQLite_masterdb`; tên đúng là `main`.
5. Mục "Ghi chú rà soát": cập nhật trạng thái 3 giá trị đã xác minh (vẫn giữ yêu cầu Phát tự chạy để ký xác nhận).
6. Thêm cảnh báo luồng XSS frontend/API ở Lab 1.

## 4. CÒN PHẢI TỰ CHẠY (AI không làm thay được)
- [ ] Khởi động EShop (backend 3000 + frontend 5173), kiểm tra `search.req` còn chạy được (token còn hạn không).
- [ ] Chạy ZAP Fuzzer với `xss-payloads.txt`, chụp bảng kết quả + response có payload chưa escape; kiểm chứng thực thi trên frontend.
- [ ] Chạy `sqlmap -r search.req --batch` → `--tables` → `-T users --dump`; lưu log + ảnh.
- [ ] Chạy `reset-db.ps1`/`.sh` sau khi dump, xác nhận DB về trạng thái sạch.
- [ ] Ghi timing từng bước (phục vụ P3a) và quay clip.
