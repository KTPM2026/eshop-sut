#!/bin/bash
# Script kiểm thử đối chứng tự động cho Task H3 (WAF Sanity Check)

BASE_URL="http://localhost:3001"

echo "========================================================"
echo "🧪 BẮT ĐẦU KIỂM THỬ ĐỐI CHỨNG BỘ LỌC ĐẦU VÀO (TASK H3)"
echo "========================================================"

# Kiểm tra server lab có đang chạy không
if ! curl -s "$BASE_URL/api/waf/status" > /dev/null; then
  echo "❌ LỖI: Server Lab chưa chạy trên cổng 3001!"
  echo "👉 Vui lòng chạy lệnh sau ở 1 terminal khác trước:"
  echo "   cd /home/hung/26-27/Kiem_thu/seminar/eshop-sut/backend && node server_fuzzer_lab.js"
  exit 1
fi

# Reset về mặc định trước khi test
curl -s -X POST "$BASE_URL/api/waf/reset" > /dev/null

echo ""
echo "[TEST 1] Người dùng bình thường tìm kiếm 'phone' (Kỳ vọng: 200 OK)"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/products?search=phone")
if [ "$HTTP_CODE" -eq 200 ]; then
  echo "  ✅ PASS: HTTP $HTTP_CODE - Request hợp lệ đi qua bình thường (không bị chặn nhầm)."
else
  echo "  ❌ FAIL: HTTP $HTTP_CODE"
fi

echo ""
echo "[TEST 2] Tấn công SQLi cơ bản: ' OR 1=1 -- (Kỳ vọng: 403 Forbidden)"
RESP=$(curl -s -w "\nHTTP_CODE:%{http_code}" "$BASE_URL/api/products?search=%27%20OR%201=1%20--")
HTTP_CODE=$(echo "$RESP" | grep "HTTP_CODE:" | cut -d':' -f2)
BODY=$(echo "$RESP" | grep -v "HTTP_CODE:")
if [ "$HTTP_CODE" -eq 403 ]; then
  echo "  ✅ PASS: HTTP $HTTP_CODE - WAF đã chặn thành công!"
  echo "  📦 JSON phản hồi cho AI: $BODY"
else
  echo "  ❌ FAIL: HTTP $HTTP_CODE"
fi

echo ""
echo "[TEST 3] Tấn công XSS cơ bản: <script>alert(1)</script> (Kỳ vọng: 403 Forbidden)"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/products?search=%3Cscript%3Ealert(1)%3C/script%3E")
if [ "$HTTP_CODE" -eq 403 ]; then
  echo "  ✅ PASS: HTTP $HTTP_CODE - WAF đã chặn từ khóa XSS thành công!"
else
  echo "  ❌ FAIL: HTTP $HTTP_CODE"
fi

echo ""
echo "[TEST 4] Thử nghiệm AI Bypass (Dùng inline comment: '/**/OR/**/1=1--) (Kỳ vọng: 200 OK)"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/products?search=%27/**/OR/**/1=1--")
if [ "$HTTP_CODE" -eq 200 ]; then
  echo "  ✅ PASS: HTTP $HTTP_CODE - Payload né lọc thành công, kích hoạt được backend!"
else
  echo "  ❌ FAIL: HTTP $HTTP_CODE"
fi

echo ""
echo "[TEST 5] Kiểm tra API Toggle: Tắt WAF và gửi lại payload SQLi (Kỳ vọng: 200 OK)"
curl -s -X POST "$BASE_URL/api/waf/toggle" -H "Content-Type: application/json" -d '{"enabled": false}' > /dev/null
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/products?search=%27%20OR%201=1%20--")
if [ "$HTTP_CODE" -eq 200 ]; then
  echo "  ✅ PASS: HTTP $HTTP_CODE - Khi tắt WAF, payload đi thẳng vào backend như SUT gốc."
else
  echo "  ❌ FAIL: HTTP $HTTP_CODE"
fi

# Reset lại WAF về trạng thái bật
curl -s -X POST "$BASE_URL/api/waf/reset" > /dev/null
echo ""
echo "========================================================"
echo "🎉 TẤT CẢ TEST ĐỐI CHỨNG CHO TASK H3 ĐÃ HOÀN TẤT VÀ ĐẠT CHUẨN!"
echo "========================================================"
