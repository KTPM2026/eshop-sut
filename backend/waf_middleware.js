/**
 * WAF / Input Filter Middleware - Phục vụ thí nghiệm AI Fuzzer (Task H3)
 * Hỗ trợ: Bật/Tắt, 2 cấp độ lọc (Level 1: Basic Regex, Level 2: Strict)
 */

const WAF_CONFIG = {
  enabled: process.env.WAF_ENABLED !== "false", // Mặc định là bật (true)
  level: parseInt(process.env.WAF_LEVEL || "1", 10), // Level 1 (mặc định) hoặc Level 2
};

// Danh sách quy tắc lọc (Rules)
// Level 1: Bộ lọc cơ bản dựa trên khoảng trắng quanh từ khóa (dễ bị bypass bằng inline comment /**/)
const SQLI_KEYWORDS_L1 = /(^|\s+)(OR|AND|UNION|SELECT|INSERT|DROP|UPDATE)(\s+|$)/i;
const XSS_KEYWORDS_L1 = /<script\b|javascript:/i;

// Level 2 (Strict): Chặn cả comment (/*, */, --), dấu chấm phẩy, event handlers và word boundary
const SQLI_KEYWORDS_L2 = /\b(OR|AND|UNION|SELECT)\b|--|\/\*|\*\/|;/i;
const XSS_KEYWORDS_L2 = /<script\b|javascript:|onerror|onload|<img|<svg|<iframe/i;

function wafMiddleware(req, res, next) {
  // Nếu tắt WAF, cho qua ngay
  if (!WAF_CONFIG.enabled) {
    return next();
  }

  // Chỉ áp dụng lọc trên endpoint tìm kiếm của Fuzzer: /api/products?search=...
  const searchInput = req.query.search;
  if (!searchInput) {
    return next();
  }

  let isBlocked = false;
  let detectedKeyword = "";

  if (WAF_CONFIG.level === 1) {
    if (SQLI_KEYWORDS_L1.test(searchInput)) {
      isBlocked = true;
      const match = searchInput.match(SQLI_KEYWORDS_L1);
      detectedKeyword = match ? match[0] : "SQLi_Keyword";
    } else if (XSS_KEYWORDS_L1.test(searchInput)) {
      isBlocked = true;
      const match = searchInput.match(XSS_KEYWORDS_L1);
      detectedKeyword = match ? match[0] : "XSS_Keyword";
    }
  } else {
    // Level 2 (Strict)
    if (SQLI_KEYWORDS_L2.test(searchInput)) {
      isBlocked = true;
      const match = searchInput.match(SQLI_KEYWORDS_L2);
      detectedKeyword = match ? match[0] : "SQLi_Keyword";
    } else if (XSS_KEYWORDS_L2.test(searchInput)) {
      isBlocked = true;
      const match = searchInput.match(XSS_KEYWORDS_L2);
      detectedKeyword = match ? match[0] : "XSS_Keyword";
    }
  }

  // Nếu vi phạm rule: Trả về HTTP 403 kèm JSON phản hồi cho AI Feedback Loop
  if (isBlocked) {
    return res.status(403).json({
      status: "BLOCKED",
      error: "WAF_INPUT_BLOCKED",
      message: `Request bị chặn bởi bộ lọc bảo mật: phát hiện từ khóa nguy hiểm '${detectedKeyword}'`,
      blocked_keyword: detectedKeyword,
      waf_level: WAF_CONFIG.level,
    });
  }

  // Nếu hợp lệ: cho tiếp tục xử lý
  next();
}

module.exports = {
  wafMiddleware,
  WAF_CONFIG,
};
