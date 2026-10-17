// Kiểm chứng API thật trước demo Burp. Chỉ khởi động bản lab riêng có thể reset.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const http = require("node:http");
const net = require("node:net");
const crypto = require("node:crypto");
const { spawn, execFileSync } = require("node:child_process");
const { once } = require("node:events");
const { parseArgs } = require("node:util");

const ROOT = path.resolve(__dirname, "../..");
const BASE = "http://127.0.0.1:3000";
const FIELDS = ["case_id", "actor", "method", "path_template", "resource_owner", "expected_access", "checkpoint"];
const REDACT_KEYS = /^(authorization|proxy-authorization|cookie|set-cookie|password|token|reset_token|secret|api_key)$/i;
const sha = value => crypto.createHash("sha256").update(value).digest("hex");

function redact(value) {
  if (Array.isArray(value)) return value.map(redact);
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([key, item]) =>
      [key, REDACT_KEYS.test(key) ? "[REDACTED]" : redact(item)]));
  }
  return value;
}

function save(file, content) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, content, { flag: "wx", encoding: "utf8" });
}

function json(file, value) {
  save(file, JSON.stringify(redact(value), null, 2) + "\n");
}

function readMatrix(file) {
  const parsed = JSON.parse(execFileSync("python", ["-X", "utf8", "-c",
    "import csv,json,sys\nwith open(sys.argv[1],newline='',encoding='utf-8-sig') as f:\n r=csv.DictReader(f)\n json.dump({'fields':r.fieldnames,'rows':list(r)},sys.stdout)",
    file], { encoding: "utf8", windowsHide: true }));
  assert.deepEqual(parsed.fields, FIELDS);
  const rows = parsed.rows;
  assert.equal(rows.length, 11);
  assert.equal(new Set(rows.map(row => row.case_id)).size, rows.length);
  for (const row of rows) {
    assert.equal(Object.keys(row).length, FIELDS.length);
    assert.equal(row.method, "GET");
    assert.match(row.path_template, /^\/api\/(?:orders\/(?:\{order_a\}|\{order_b\}|\{nonexistent_order\})|admin\/users)$/);
    assert(["user_a", "user_b", "guest", "admin"].includes(row.actor));
    assert(["allow", "deny"].includes(row.expected_access));
  }
  return rows;
}

async function checkPort() {
  const probe = net.createServer();
  await new Promise((resolve, reject) => {
    probe.once("error", reject);
    probe.listen(3000, "127.0.0.1", resolve);
  });
  await new Promise((resolve, reject) => probe.close(error => error ? reject(error) : resolve()));
}

async function request(route, { method = "GET", token, body } = {}) {
  assert.match(route, /^\/api\//);
  const started = new Date().toISOString();
  const headers = { Accept: "application/json" };
  if (token) headers.Authorization = "Bearer " + token;
  const payload = body === undefined ? null : JSON.stringify(body);
  if (payload !== null) headers["Content-Type"] = "application/json";
  const before = performance.now();
  return new Promise((resolve, reject) => {
    const req = http.request(BASE + route, { method, headers, timeout: 5000 }, response => {
      const chunks = [];
      response.on("data", chunk => chunks.push(chunk));
      response.on("end", () => {
        const raw = Buffer.concat(chunks).toString("utf8");
        let data;
        try { data = JSON.parse(raw); } catch { data = raw; }
        resolve({
          status: response.statusCode, data,
          record: {
            started_at_utc: started, elapsed_ms: Math.round((performance.now() - before) * 100) / 100,
            request: { method, url: BASE + route, headers: redact(headers), body: redact(body ?? null) },
            response: {
              status: response.statusCode, content_type: response.headers["content-type"] ?? null,
              body: redact(data),
            },
          },
        });
      });
      response.on("error", reject);
    });
    req.on("timeout", () => req.destroy(new Error("Lab request timed out.")));
    req.on("error", reject);
    if (payload !== null) req.write(payload);
    req.end();
  });
}

async function ready(server) {
  for (let count = 0; count < 80; count++) {
    if (server.launchError) throw server.launchError;
    if (server.exitCode !== null) throw new Error("Backend stopped before readiness.");
    try {
      const response = await request("/api/products");
      if (response.status === 200 && Array.isArray(response.data) && response.data.length > 0) return;
    } catch {}
    await new Promise(resolve => setTimeout(resolve, 150));
  }
  throw new Error("Backend did not become ready.");
}

async function captureBrowser(modulePath, report, actors, output) {
  const playwright = require(path.resolve(modulePath));
  const browser = await playwright.chromium.launch({ channel: "msedge", headless: true });
  const screenshots = [];
  try {
    for (const caseId of ["N1-03", "N1-06", "N1-08"]) {
      const item = report.cases.find(row => row.case_id === caseId);
      const actor = actors[item.actor];
      const context = await browser.newContext({
        viewport: { width: 1920, height: 1080 },
        extraHTTPHeaders: actor.token ? { Authorization: "Bearer " + actor.token } : {},
      });
      try {
        const page = await context.newPage();
        const response = await page.goto(item.evidence.request.url, { waitUntil: "load" });
        assert.equal(response.status(), item.evidence.response.status);
        assert.deepEqual(redact(await response.json()), item.evidence.response.body);
        const filename = caseId + ".png";
        const bytes = await page.screenshot({ path: path.join(output, filename), fullPage: true });
        screenshots.push({
          case_id: caseId, file: filename, sha256: sha(bytes),
          captured_at_utc: new Date().toISOString(), url: page.url(),
          tool: "Microsoft Edge headless via Playwright; live API response, not Burp",
          browser_version: browser.version(),
          playwright_version: require(path.join(path.resolve(modulePath), "package.json")).version,
          response_matches_case: true,
        });
      } finally {
        await context.close();
      }
    }
  } finally {
    await browser.close();
  }
  return screenshots;
}

function checkpoint(row, response, actors, orders) {
  const data = response.data;
  const denied = [401, 403, 404].includes(response.status);
  let verified = false;
  let exposed = false;
  let details;
  if (row.resource_owner === "none") {
    verified = response.status === 404 && data?.error === "Order not found";
    return { outcome: verified ? "pass" : "inconclusive", observed_access: "not_found",
      reason: "Đối chứng ID không tồn tại: cần 404 và body Order not found." };
  }
  if (row.resource_owner === "admin") {
    const identities = Object.values(actors).filter(actor => actor.id !== null);
    verified = Array.isArray(data) && identities.every(actor =>
      data.some(user => user.id === actor.id && user.role === actor.role && user.email === actor.email));
    exposed = Array.isArray(data) && identities.some(actor =>
      data.some(user => user.id === actor.id && user.role === actor.role && user.email === actor.email));
    details = verified ? "Body chứa đúng danh sách tài khoản lab và role, đối chiếu admin control." :
      "Chưa xác minh danh sách user lab trong body.";
  } else {
    const order = orders[row.resource_owner];
    verified = data?.id === order.id && data?.user_id === actors[row.resource_owner].id &&
      data?.shipping_address === order.address && data?.total_amount === order.total;
    exposed = data?.id === order.id && data?.user_id === actors[row.resource_owner].id &&
      (Object.hasOwn(data, "shipping_address") || Object.hasOwn(data, "total_amount"));
    details = verified ? "Body khớp order ID, owner ID, địa chỉ và tổng tiền lab đã tạo." :
      "Body chưa khớp dữ liệu riêng của đơn lab.";
  }
  if (row.expected_access === "allow") {
    return { outcome: response.status >= 200 && response.status < 300 && verified ? "pass" : "inconclusive",
      observed_access: verified ? "private_data_returned" : "unverified", reason: details };
  }
  return {
    outcome: exposed ? "fail" : denied ? "pass" : "inconclusive",
    observed_access: exposed ? "unauthorized_private_data_returned" : denied ? "denied" : "unverified",
    reason: verified ? details : exposed ? "Body vẫn lộ dữ liệu riêng của tài nguyên lab dù thiếu một phần trường." :
      denied ? "Server từ chối và body không chứa dữ liệu riêng đã kiểm tra." : details,
  };
}

function markdown(report) {
  const lines = [
    "# N1: Kết quả kiểm chứng API trên main của nhóm", "",
    "**Thạch Như – 23120312.**", "",
    "Đây là lượt kiểm chứng HTTP thực do Codex thực thi bằng Node.js trước khi quay demo Burp.", "",
    "- UTC: " + report.executed_at_utc,
    "- SUT: " + report.repository + ", commit " + report.sut_commit,
    "- Công cụ: " + report.execution_tool + "; Node " + report.node_version,
    "- Backend: " + BASE + "; NODE_ENV=development; source backend không sửa.",
    "- Burp đã chạy: **chưa**. Nhãn độc lập N2 và benchmark AI N3: **chưa thực hiện**.",
    "- Kết quả: **" + report.summary.pass + " pass, " + report.summary.fail + " fail, " +
      report.summary.inconclusive + " chưa đủ bằng chứng**, trên 11 ca.", "",
    "## Kết quả từng ca", "",
    "| Case | Actor | Owner/tài nguyên | Kỳ vọng | HTTP | Kết quả |",
    "|---|---|---|---|---|---|",
    ...report.cases.map(item => "| " + [item.case_id, item.actor, item.resource_owner,
      item.expected_access, item.evidence.response.status, item.checkpoint.outcome].join(" | ") + " |"),
    "", "Mỗi ca có request/response đã làm sạch và giải thích checkpoint trong [results.json](results.json).",
    "", "## Phát hiện được kiểm chứng", "",
  ];
  for (const finding of report.findings) {
    lines.push("### " + finding.id + ": " + finding.title, "", finding.description,
      "", "Ca liên quan: " + finding.case_ids.join(", ") + ".", "");
  }
  if (report.screenshots?.length) {
    lines.push("## Ảnh response API từ trình duyệt", "",
      "Ảnh Edge headless của response thật; JSON/status được đối chiếu với ca tương ứng. Đây chưa phải ảnh Burp.", "");
    for (const capture of report.screenshots) {
      lines.push("![" + capture.case_id + " API response](" + capture.file + ")", "");
    }
  }
  lines.push("## Giới hạn và bước tiếp theo", "",
    ...report.limitations.map(item => "- " + item), "",
    "Đây là bằng chứng API thực tế để Như/Hùng rà soát và làm nền cho N1; " +
    "chưa xác nhận hoàn tất thao tác/quay Burp của sinh viên.", "");
  return lines.join("\n");
}

async function main() {
  const { values } = parseArgs({
    options: {
      sut: { type: "string" }, "output-dir": { type: "string" },
      "reset-lab": { type: "boolean", default: false },
      "keep-lab": { type: "boolean", default: false },
      "session-file": { type: "string" },
      "browser-module": { type: "string" },
    },
  });
  assert(values.sut && values["output-dir"], "Need --sut and --output-dir.");
  assert(values["reset-lab"], "The SUT resets its database on start. Pass --reset-lab only for a disposable checkout.");
  const sut = fs.realpathSync(path.resolve(values.sut));
  const output = path.resolve(values["output-dir"]);
  const privateRoot = path.join(ROOT, "Nhu", "private") + path.sep;
  assert(sut.toLowerCase().startsWith(privateRoot.toLowerCase()),
    "Use a disposable clone inside Nhu/private; never reset the original sandbox.");
  assert(!fs.existsSync(output), "Output directory must be new.");
  const git = args => execFileSync("git", ["-C", sut, ...args], { encoding: "utf8", windowsHide: true }).trim();
  const commit = git(["rev-parse", "HEAD"]);
  assert.equal(git(["status", "--porcelain", "--untracked-files=no", "--", ".", ":(exclude)backend/database.sqlite"]),
    "", "SUT source files must be unchanged; only the disposable database may change.");
  const backend = path.join(sut, "backend");
  const matrixFile = path.join(__dirname, "case-matrix.csv");
  const matrix = readMatrix(matrixFile);
  let sessionFile;
  if (values["session-file"]) {
    sessionFile = path.resolve(values["session-file"]);
    assert(sessionFile.toLowerCase().startsWith(privateRoot.toLowerCase()), "Session secrets must stay in Nhu/private.");
    assert(!fs.existsSync(sessionFile), "Session file must be new.");
  }
  await checkPort();
  const server = spawn(process.execPath, ["server.js"], {
    cwd: backend, env: { ...process.env, NODE_ENV: "development" },
    windowsHide: true, stdio: ["ignore", "pipe", "pipe"],
  });
  server.on("error", error => { server.launchError = error; });
  server.stdout.resume();
  server.stderr.resume();
  const executedAt = new Date().toISOString();
  try {
    await ready(server);
    const setup = [];
    const send = async (route, options) => {
      const response = await request(route, options);
      setup.push(response.record);
      assert.equal(response.status, 200, "Lab setup request failed: " + route);
      return response.data;
    };
    const userA = await send("/api/login", { method: "POST", body: { email: "test@eshop.com", password: "Test1234!" } });
    const admin = await send("/api/login", { method: "POST", body: { email: "admin@eshop.com", password: "Admin123!" } });
    const passwordB = crypto.randomBytes(24).toString("base64url");
    const emailB = "n1-b-23120312@example.invalid";
    await send("/api/register", { method: "POST", body: { name: "N1 Lab B", email: emailB, password: passwordB } });
    const userB = await send("/api/login", { method: "POST", body: { email: emailB, password: passwordB } });
    const actors = {
      guest: { id: null, role: "guest", email: null },
      user_a: { id: userA.user.id, role: userA.user.role, email: userA.user.email, token: userA.token },
      user_b: { id: userB.user.id, role: userB.user.role, email: userB.user.email, token: userB.token },
      admin: { id: admin.user.id, role: admin.user.role, email: admin.user.email, token: admin.token },
    };
    assert.equal(actors.user_a.role, "user");
    assert.equal(actors.user_b.role, "user");
    assert.equal(actors.admin.role, "admin");
    assert.equal(new Set([actors.user_a.id, actors.user_b.id, actors.admin.id]).size, 3);
    const orders = {};
    for (const [actorName, total] of [["user_a", 30000000], ["user_b", 6000000]]) {
      const address = "N1-23120312-LAB-" + actorName;
      const result = await send("/api/checkout", {
        method: "POST", token: actors[actorName].token,
        body: { total_amount: total, shipping_address: address },
      });
      assert(Number.isSafeInteger(result.orderId));
      orders[actorName] = { id: result.orderId, address, total };
    }
    const cases = [];
    for (const row of matrix) {
      const route = row.path_template.replace("{order_a}", orders.user_a.id)
        .replace("{order_b}", orders.user_b.id).replace("{nonexistent_order}", "2147483647");
      const response = await request(route, { token: actors[row.actor].token });
      cases.push({ ...row, requester_id: actors[row.actor].id, requester_role: actors[row.actor].role,
        checkpoint: checkpoint(row, response, actors, orders), evidence: response.record });
    }
    // Các positive control phải đúng trước khi diễn giải ca trái quyền.
    assert(cases.filter(item => item.expected_access === "allow").every(item => item.checkpoint.outcome === "pass"),
      "Positive controls failed; do not conclude an authorization finding.");
    const failed = cases.filter(item => item.checkpoint.outcome === "fail");
    const orderFails = failed.filter(item => item.resource_owner !== "admin");
    const adminFails = failed.filter(item => item.resource_owner === "admin");
    const findings = [];
    if (orderFails.length) findings.push({
      id: "N1-ACCESS-01", title: "Đọc đơn hàng không đúng quyền",
      description: "Guest và/hoặc user khác nhận đúng dữ liệu đơn lab đã tạo, gồm owner ID, địa chỉ và tổng tiền. " +
        "Đối chứng owner đọc được đơn của mình. Cùng route GET /api/orders/:id được gom thành một phát hiện.",
      case_ids: orderFails.map(item => item.case_id),
    });
    if (adminFails.length) findings.push({
      id: "N1-ACCESS-02", title: "User thường đọc API danh sách quản trị",
      description: "Token role user nhận danh sách tài khoản lab tại GET /api/admin/users, " +
        "đối chiếu cùng danh sách với admin control. Đã chứng minh quyền đọc, chưa kiểm tra sửa/xóa.",
      case_ids: adminFails.map(item => item.case_id),
    });
    const dependencyVersions = Object.fromEntries(["express", "body-parser", "cors", "jsonwebtoken", "sqlite3"].map(name =>
      [name, JSON.parse(fs.readFileSync(require.resolve(name + "/package.json", { paths: [backend] }), "utf8")).version]));
    const report = {
      schema_version: "nhu-n1-preflight-v1", owner: "Thạch Như", student_id: "23120312",
      executed_at_utc: executedAt, completed_at_utc: new Date().toISOString(),
      repository: git(["remote", "get-url", "origin"]), sut_commit: commit,
      source_sha256: Object.fromEntries(["server.js", "database.js", "package.json", "package-lock.json"]
        .filter(file => fs.existsSync(path.join(backend, file)))
        .map(file => [file, sha(fs.readFileSync(path.join(backend, file)))])),
      matrix_sha256: sha(fs.readFileSync(matrixFile)), runner_sha256: sha(fs.readFileSync(__filename)),
      node_version: process.version,
      dependency_versions: dependencyVersions, api_origin: BASE, data_origin: "real_local_http",
      execution_tool: "Node.js node:http; scripted API preflight", executed_by: "Codex AI assistant",
      student_performed: false, burp_executed: false, is_replay: false,
      scan_commit_confirmed: false, request_count_cases: cases.length,
      request_count_setup: setup.length, identities: redact(actors), orders,
      setup, cases, findings,
      summary: Object.fromEntries(["pass", "fail", "inconclusive"].map(outcome =>
        [outcome, cases.filter(item => item.checkpoint.outcome === outcome).length])),
      limitations: [
        "SUT chạy ở commit main ghi trong báo cáo; ZAP export ngày 14/10 không ghi commit scan nên chưa chứng minh hai môi trường hoàn toàn trùng nhau.",
        "Burp chưa được cài/chạy; không dùng kết quả này để tuyên bố đã hoàn tất demo Burp.",
        "Lượt chạy do AI thực thi; Như cần tự rà soát, thao tác và thuyết minh theo yêu cầu chính chủ.",
        "Không phải ZAP export, nhãn độc lập N2 hoặc benchmark AI N3.",
        "Chỉ kiểm tra quyền đọc ở hai route; chưa đánh giá sửa/xóa hoặc ngoại lệ admin với đơn cá nhân.",
      ],
    };
    if (values["browser-module"]) {
      fs.mkdirSync(output, { recursive: true });
      report.screenshots = await captureBrowser(values["browser-module"], report, actors, output);
      report.browser_API_navigations = report.screenshots.length;
    }
    report.completed_at_utc = new Date().toISOString();
    json(path.join(output, "results.json"), report);
    execFileSync("python", ["-X", "utf8", "-c",
      "import csv,json,sys\nrows=json.load(sys.stdin)\nwith open(sys.argv[1],'x',newline='',encoding='utf-8') as f:\n w=csv.DictWriter(f,fieldnames=['case_id','actor','resource_owner','expected_access','response_code','outcome'])\n w.writeheader()\n w.writerows(rows)",
      path.join(output, "results.csv")], {
      windowsHide: true, encoding: "utf8", input: JSON.stringify(cases.map(item => ({
        case_id: item.case_id, actor: item.actor, resource_owner: item.resource_owner,
        expected_access: item.expected_access, response_code: item.evidence.response.status,
        outcome: item.checkpoint.outcome,
      }))),
    });
    save(path.join(output, "README.md"), markdown(report));
    if (sessionFile) {
      fs.mkdirSync(path.dirname(sessionFile), { recursive: true });
      fs.writeFileSync(sessionFile, JSON.stringify({
        notice: "PRIVATE LAB SESSION, DO NOT COMMIT OR SHARE", api_origin: BASE,
        sut_commit: commit, created_at_utc: executedAt,
        actors, password_b: passwordB, orders,
      }, null, 2), { flag: "wx", mode: 0o600 });
    }
    console.log(JSON.stringify({ output, sut_commit: commit, cases: cases.length,
      summary: report.summary, root_findings: findings.length, burp_executed: false }, null, 2));
    if (values["keep-lab"]) {
      console.log("Lab is ready on " + BASE + ". Ctrl+C to stop. Tokens only in the private session file, if requested.");
      await new Promise(resolve => {
        const finish = () => resolve();
        process.once("SIGINT", finish);
        process.once("SIGTERM", finish);
        server.once("exit", finish);
      });
    }
  } finally {
    if (server.exitCode === null) {
      const stopped = once(server, "close");
      server.kill();
      await stopped;
    }
  }
}

if (require.main === module) main().catch(error => {
  console.error("Preflight failed: " + error.message);
  process.exitCode = 1;
});

module.exports = { checkpoint, readMatrix, redact };
