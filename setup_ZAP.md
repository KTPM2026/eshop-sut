# Các bước cấu hình ZAP

  ## Bước 1: Khởi chạy các dịch vụ EShop
  Mở 2 terminal độc lập để chạy Backend và Frontend Web:
  1. Terminal 1 (Backend API - cổng 3000):                                                        
    cd /home/hung/26-27/Kiem_thu/seminar/eshop-sut/backend                                        
    node server.js
  2. Terminal 2 (Frontend Web - cổng 5173):                                                       
    cd /home/hung/26-27/Kiem_thu/seminar/eshop-sut/frontend-web                                   
    npm run dev
  ──────
  ## Bước 2: Cấu hình ZAP Scope & Context (Khắc phục bẫy khác Origin)
  Vì ZAP đang chạy trên máy của bạn (port 8080):
  1. Trên giao diện ZAP Desktop, ở tab Sites (bên trái), click chuột phải chọn Include in Context 
  ➔ New Context... (Đặt tên Context là EShop).
  2. Trong cửa sổ cấu hình Context:

      • In Scope: Chọn mục Include in Context.

      • Bấm nút Add, nhập biểu thức Regex: http://localhost.*

      • Lưu ý nghiệp vụ: Frontend chạy ở :5173 nhưng gọi API ở :3000. Nếu chỉ cấu hình localhost:5173, ZAP sẽ coi các request gọi sang :3000 là ngoài phạm vi và bỏ qua không quét
      các API backend. Regex trên đảm bảo bao quát cả 2 cổng.
  3. Bấm Save / OK.
  ## Bước 3: Cấu hình Token JWT cho ZAP quét các API yêu cầu đăng nhập
  EShop dùng JWT qua header Authorization: Bearer <token>. Cách cấu hình tự động nhanh và chuẩn
  nhất trong ZAP:
  1. Mở trình duyệt, truy cập http://localhost:5173, đăng nhập với tài khoản user:

      • Email: test@eshop.com / Password: Test1234!

      • Bấm F12 ➔ Vào tab Application (hoặc Storage) ➔ Chọn Local Storage ➔ Copy giá trị chuỗi token.

  2. Trên ZAP Desktop, vào menu thanh công cụ: Tools ➔ Replacer...
  3. Bấm Add và điền các trường sau:

      • Description: Add JWT to EShop API

      • Match Type: Request Header (add if not present)

      • Match String: Authorization         

      • Replacement String: Bearer <dán_chuỗi_token_bạn_vừa_copy_vào> 

      • Target URL Regex: http://localhost:3000*        
      • Tích chọn Enable.                  
  4. Bấm Save. Từ lúc này, mọi request ZAP gửi đến backend :3000 sẽ tự động mang token xác thực.     
  ## Bước 4: Chạy Crawl & Scan thực tế                                                          
  1. Chạy AJAX Spider (Bắt buộc với React SPA):          
      • Trong ZAP, click vào tab Quick Start ➔ chọn Manual Explore, gõ URL: http://localhost:5173 
      và bấm Launch Browser (để ZAP nhận diện site).              

      • Sau khi site http://localhost:5173 hiện lên trong cây Sites: Click chuột phải vào node đó 
      ➔ Attack ➔ AJAX Spider...  

      • Chọn Context EShop ➔ Bấm Start Scan. ZAP sẽ dùng trình duyệt headless tự động click các
      nút trên React app và thu thập các endpoint API.                                            
  2. Chạy Active Scan:                                                                            
      • Sau khi AJAX Spider hoàn tất, click chuột phải vào Context EShop (hoặc node               
      http://localhost:3000) ➔ Attack ➔ Active Scan...               
      • Đảm bảo Context đã chọn là EShop.          

      • Bấm Start Scan và đợi tiến trình chạy đến 100%.
  
# Nội dung bàn giao cho đồng đội (Hoàn tất H3):
  • Target Endpoint Fuzzer: http://localhost:3001/api/products?search=<payload>

  • Cơ chế phản hồi khi bị chặn: HTTP 403 Forbidden kèm body JSON có trường blocked_keyword để Long đưa vào thuật toán Feedback Loop của AI.

  • API Điều khiển tự động: POST http://localhost:3001/api/waf/toggle để Lân dùng trong script chạy benchmark đối chứng 3 nhánh (wordlist tĩnh vs AI tĩnh vs AI feedback loop).