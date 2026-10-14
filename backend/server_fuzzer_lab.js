const express = require("express");
const cors = require("cors");
const bodyParser = require("body-parser");
const db = require("./database");
const { wafMiddleware, WAF_CONFIG } = require("./waf_middleware");

const app = express();
const PORT = process.env.PORT || 3001; // Cổng 3001 dành riêng cho Lab Fuzzer

app.use(cors());
app.use(bodyParser.json());

// ==========================================
// API QUẢN TRỊ TRẠNG THÁI BỘ LỌC (BẬT / TẮT / RESET)
// Phục vụ module AI Fuzzer và Benchmark tự động hóa
// ==========================================
app.get("/api/waf/status", (req, res) => {
  res.json({
    waf_enabled: WAF_CONFIG.enabled,
    waf_level: WAF_CONFIG.level,
  });
});

app.post("/api/waf/toggle", (req, res) => {
  const { enabled, level } = req.body;
  if (typeof enabled === "boolean") WAF_CONFIG.enabled = enabled;
  if (typeof level === "number") WAF_CONFIG.level = level;
  res.json({
    message: "Cập nhật cấu hình WAF thành công",
    current_config: WAF_CONFIG,
  });
});

app.post("/api/waf/reset", (req, res) => {
  WAF_CONFIG.enabled = true;
  WAF_CONFIG.level = 1;
  res.json({
    message: "Đã reset cấu hình WAF về mặc định (Bật, Level 1)",
    current_config: WAF_CONFIG,
  });
});

// ==========================================
// ENDPOINT TÌM KIẾM CÓ GẮN BỘ LỌC WAF
// ==========================================
app.get("/api/products", wafMiddleware, (req, res) => {
  const searchQuery = req.query.search;
  if (searchQuery) {
    // Giữ nguyên lỗ hổng SQLi gốc để kiểm chứng sau khi payload vượt qua bộ lọc
    const query = `SELECT * FROM products WHERE name LIKE '%${searchQuery}%'`;
    db.all(query, [], (err, rows) => {
      if (err) {
        return res
          .status(500)
          .send(`<h1>Database Error</h1><p>${err.message}</p>`);
      }
      res.json(rows);
    });
  } else {
    db.all("SELECT * FROM products", [], (err, rows) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json(rows);
    });
  }
});

app.listen(PORT, () => {
  console.log(`=================================================`);
  console.log(`🚀 FUZZER LAB SERVER ĐANG CHẠY TẠI: http://localhost:${PORT}`);
  console.log(`🛡️  BỘ LỌC WAF: ${WAF_CONFIG.enabled ? "BẬT" : "TẮT"} (Level: ${WAF_CONFIG.level})`);
  console.log(`📡 ENDPOINT TEST: http://localhost:${PORT}/api/products?search=...`);
  console.log(`⚙️  API ĐIỀU KHIỂN: POST http://localhost:${PORT}/api/waf/toggle`);
  console.log(`=================================================`);
});
