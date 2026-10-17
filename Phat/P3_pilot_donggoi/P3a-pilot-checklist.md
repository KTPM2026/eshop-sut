# P3a — Chạy thử (pilot) 2 Lab & ghi lỗi/timing

**Phát (23120317).** Mục tiêu: chạy thử trọn vẹn 2 Lab như một sinh viên trong lớp, phát hiện lỗi hướng dẫn và đo thời lượng thật. Điền `[CHỜ TỰ CHẠY]`.

## Môi trường pilot
| Mục | Giá trị |
|---|---|
| Ngày/máy chạy | [CHỜ TỰ CHẠY] |
| Commit EShop | [CHỜ TỰ CHẠY] |
| Phiên bản ZAP | [CHỜ TỰ CHẠY] |
| Phiên bản sqlmap (`sqlmap --version`) | [CHỜ TỰ CHẠY] |
| Backend 3000 / Frontend 5173 sống? | [CHỜ TỰ CHẠY] |

## Lab 1 — ZAP / Reflected XSS (dự kiến ~10 phút)
| Bước | Làm được? | Thời gian | Lỗi/ghi chú |
|---|:---:|---|---|
| Mở ZAP + browser (Manual Explore) |  |  |  |
| Ghi nhận request tìm kiếm (`GET /api/products?search=`) |  |  |  |
| Chuyển Fuzzer, đánh dấu điểm chèn |  |  |  |
| Nạp `xss-payloads.txt`, Start Fuzzer |  |  |  |
| Xác thực payload chưa escape (response) |  |  |  |
| **Kiểm chứng thực thi trên frontend 5173** (điểm cần lưu ý) |  |  |  |
| **Tổng thời gian Lab 1** |  |  |  |

## Lab 2 — sqlmap / SQLi (dự kiến ~15–20 phút)
| Bước | Làm được? | Thời gian | Lỗi/ghi chú |
|---|:---:|---|---|
| Chuẩn bị `search.req` (đã có sẵn) |  |  |  |
| `sqlmap -r search.req --batch` → báo injectable |  |  |  |
| `--tables` (SQLite, không cần `--dbs`/`-D`) |  |  |  |
| `-T users --dump` ra dữ liệu |  |  |  |
| Chạy `reset-db` khôi phục DB |  |  |  |
| **Tổng thời gian Lab 2** |  |  |  |

## Kết luận pilot
- Lỗi hướng dẫn phát hiện: [CHỜ TỰ CHẠY]
- Thời lượng thực tế so với dự kiến (câu hỏi GVTH #4): [CHỜ TỰ CHẠY]
- Hạng mục cần sửa lại trong `lab-huong-dan.md`: [CHỜ TỰ CHẠY]
