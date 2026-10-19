// Prepare a disposable API lab and private requests; this does not operate Burp.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { spawn, execFileSync } = require("node:child_process");
const { parseArgs } = require("node:util");

const ROOT = path.resolve(__dirname, "../..");
const PRIVATE = path.join(ROOT, "Nhu", "private");
const ORIGIN = "http://127.0.0.1:3000";
const ACTORS = ["guest", "user_a", "user_b", "admin"];
const positiveId = value => Number.isSafeInteger(value) && value > 0;
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));

function buildKit(session, matrix) {
  assert(session && session.api_origin === ORIGIN, "Only the loopback N1 lab is allowed.");
  assert(/^[a-f0-9]{40}$/.test(session.sut_commit || ""), "Missing actual SUT commit.");
  assert(session.actors && session.orders, "Missing lab setup data.");
  const identities = {};
  for (const name of ACTORS) {
    const actor = session.actors[name];
    assert(actor && actor.role === (name === "admin" ? "admin" : name === "guest" ? "guest" : "user"),
      "Incorrect actor role.");
    if (name === "guest") {
      assert(actor.id === null && !actor.token, "Guest must not have a login session.");
    } else {
      assert(positiveId(actor.id), "Invalid actor ID.");
      assert(typeof actor.token === "string" && actor.token.length < 20000 &&
        /^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/.test(actor.token),
      "Expected a lab JWT without whitespace or extra headers.");
    }
    identities[name] = { id: actor.id, role: actor.role };
  }
  assert(new Set([identities.user_a.id, identities.user_b.id, identities.admin.id]).size === 3,
    "The three authenticated identities must be distinct.");
  for (const name of ["user_a", "user_b"]) {
    assert(positiveId(session.orders[name]?.id), "Invalid lab order ID.");
  }
  assert(session.orders.user_a.id !== session.orders.user_b.id, "Orders must be distinct.");
  assert(Array.isArray(matrix) && matrix.length === 11, "Expected the existing 11-case matrix.");
  assert(new Set(matrix.map(row => row.case_id)).size === 11, "Duplicate case IDs.");
  const requests = matrix.map(row => {
    assert(/^N1-(?:0[1-9]|1[01])$/.test(row.case_id), "Invalid case ID.");
    assert(row.method === "GET" && ACTORS.includes(row.actor), "Only scoped read-only cases are allowed.");
    assert(["allow", "deny"].includes(row.expected_access), "Missing expected access.");
    assert(/^\/api\/(?:orders\/(?:\{order_a\}|\{order_b\}|\{nonexistent_order\})|admin\/users)$/.test(row.path_template),
      "Path is outside the N1 matrix scope.");
    const route = row.path_template.replace("{order_a}", session.orders.user_a.id)
      .replace("{order_b}", session.orders.user_b.id).replace("{nonexistent_order}", "2147483647");
    const headers = ["GET " + route + " HTTP/1.1", "Host: 127.0.0.1:3000", "Accept: application/json"];
    if (row.actor !== "guest") headers.push("Authorization: Bearer " + session.actors[row.actor].token);
    headers.push("Connection: close");
    return { case_id: row.case_id, actor: row.actor, resource_owner: row.resource_owner,
      path: route, expected_access: row.expected_access, checkpoint: row.checkpoint,
      actual_status: null, checkpoint_result: null, burp_executed: false,
      request_file: "requests/" + row.case_id + ".request.txt", raw: headers.join("\r\n") + "\r\n\r\n" };
  });
  return { identities, requests, manifest: {
    owner: "Thach Nhu", student_id: "23120312", status: "awaiting_actual_Burp_run",
    sut_commit: session.sut_commit, api_origin: ORIGIN, frontend_origin: null,
    burp_version: null, executed_at_utc: null, scope_approved: false,
    burp_executed: false, student_performed: false, is_preparation_only: true,
    lab_identity_and_order_map: { identities, order_a: session.orders.user_a.id, order_b: session.orders.user_b.id },
    cases: [], video_url: null,
    notice: "Preparation only. No Burp request, screenshot, manual action or video is claimed. Never share session.json or unredacted requests."
  } };
}

function inside(parent, target) {
  const relative = path.relative(parent, target);
  return relative !== "" && !relative.startsWith(".." + path.sep) && relative !== ".." && !path.isAbsolute(relative);
}

function write(file, text) {
  fs.writeFileSync(file, text, { flag: "wx", encoding: "utf8", mode: 0o600 });
}

function writeKit(folder, kit) {
  fs.mkdirSync(path.join(folder, "requests"));
  for (const request of kit.requests) write(path.join(folder, request.request_file), request.raw);
  write(path.join(folder, "case-plan.json"), JSON.stringify(kit.requests.map(({ raw, ...row }) => row), null, 2) + "\n");
  write(path.join(folder, "burp-manifest.blank.json"), JSON.stringify(kit.manifest, null, 2) + "\n");
  const table = kit.requests.map(row => `| ${row.case_id} | ${row.actor} | ${row.path} | ${row.expected_access} |`).join("\n");
  write(path.join(folder, "README.md"), `# Private Burp handoff\n\n` +
    `PREPARATION ONLY. Raw requests include lab JWTs. Do not commit, upload or record these files.\n\n` +
    `API: ${ORIGIN}\nSUT commit: ${kit.manifest.sut_commit}\n\n` +
    `1. Keep the launcher running. It resets only the disposable clone on each new run.\n` +
    `2. Open Burp Community, then Proxy > Intercept > Open browser. Visit ${ORIGIN}/api/products.\n` +
    `3. Capture/Forward one request with Intercept on, then switch Intercept off. Keep only the lab origin in scope.\n` +
    `4. In HTTP history send that request to Repeater. Replace its complete Raw request with one request file below. Keep the target HTTP 127.0.0.1 port 3000.\n` +
    `5. Send owner controls N1-01/N1-02 and admin control N1-10 first. Check JSON IDs/owners against session.json. Stop interpretation if controls fail.\n` +
    `6. Send the remaining cases in separate named tabs. Compare returned private data, not only status codes. All cases are GET requests; do not add write/delete tests.\n` +
    `7. Save actual request/response pairs and screenshots. Redact JWTs/Cookies before sharing. Fill a NEW evidence manifest from that actual Burp run.\n` +
    `8. Ctrl+C stops the launcher and its lab processes. Regenerate this kit for the next lab session instead of reusing stale tokens/orders.\n\n` +
    `| Case | Actor | Path | Expected access |\n|---|---|---|---|\n${table}\n\n` +
    `case-plan.json contains expected values only; actual_status/checkpoint_result remain null. The API preflight is automated, not Burp or student-performed evidence.\n`);
}

async function stopTree(child, ended) {
  if (child.pid && child.exitCode === null && child.signalCode === null) {
    if (process.platform === "win32") {
      // Kill only the process tree we just spawned, including its disposable API.
      execFileSync("taskkill.exe", ["/PID", String(child.pid), "/T", "/F"], { windowsHide: true, stdio: "ignore" });
    } else {
      process.kill(-child.pid, "SIGTERM");
    }
  }
  await ended;
}

async function main() {
  const { values } = parseArgs({ options: {
    sut: { type: "string", default: "Nhu/private/eshop-n1-main" },
    "output-dir": { type: "string" }, "reset-lab": { type: "boolean", default: false },
    "stop-after-setup": { type: "boolean", default: false },
  } });
  assert(values["reset-lab"], "Pass --reset-lab only for a disposable Nhu/private clone.");
  const privateRoot = fs.realpathSync(PRIVATE);
  const sut = fs.realpathSync(path.resolve(ROOT, values.sut));
  assert(inside(privateRoot, sut), "SUT must be a disposable clone inside Nhu/private.");
  const suffix = new Date().toISOString().replace(/[:.]/g, "-");
  const folder = path.resolve(ROOT, values["output-dir"] || "Nhu/private/burp-manual-" + suffix);
  assert(inside(privateRoot, folder) && !fs.existsSync(folder), "Use a NEW output folder inside Nhu/private.");
  const parent = fs.realpathSync(path.dirname(folder));
  assert(parent === privateRoot || inside(privateRoot, parent), "Output parent must remain inside Nhu/private.");
  const matrix = JSON.parse(execFileSync("python", ["-X", "utf8", "-c",
    "import csv,json,sys\nwith open(sys.argv[1],encoding='utf-8-sig',newline='') as f: json.dump(list(csv.DictReader(f)),sys.stdout)",
    path.join(__dirname, "case-matrix.csv")], { encoding: "utf8", windowsHide: true }));
  fs.mkdirSync(folder);
  const sessionFile = path.join(folder, "session.json");
  const child = spawn(process.execPath, [path.join(__dirname, "run_preflight.cjs"), "--sut", sut,
    "--reset-lab", "--keep-lab", "--session-file", sessionFile, "--output-dir", path.join(folder, "api-preflight")],
  { cwd: ROOT, windowsHide: true, detached: process.platform !== "win32", stdio: ["ignore", "pipe", "pipe"] });
  let finished = false;
  let launchError;
  let messages = "";
  const capture = chunk => { messages = (messages + chunk.toString("utf8")).slice(-12000); };
  child.stdout.on("data", capture);
  child.stderr.on("data", capture);
  child.on("error", error => { launchError = error; });
  const ended = new Promise(resolve => child.once("close", () => { finished = true; resolve(); }));
  let interrupted = false;
  const interrupt = () => { interrupted = true; };
  process.on("SIGINT", interrupt);
  process.on("SIGTERM", interrupt);
  try {
    const deadline = Date.now() + 60000;
    while (!fs.existsSync(sessionFile) || !messages.includes("Lab is ready on " + ORIGIN)) {
      if (launchError) throw launchError;
      if (finished) throw new Error("API preflight did not finish setup. " + messages.trim());
      if (interrupted) throw new Error("Cancelled before setup completed.");
      assert(Date.now() < deadline, "Timed out waiting for lab setup.");
      await delay(150);
    }
    const kit = buildKit(JSON.parse(fs.readFileSync(sessionFile, "utf8")), matrix);
    writeKit(folder, kit);
    const preflight = JSON.parse(fs.readFileSync(path.join(folder, "api-preflight/results.json"), "utf8"));
    console.log(JSON.stringify({ private_kit: folder, api_origin: ORIGIN, sut_commit: kit.manifest.sut_commit,
      prepared_requests: kit.requests.length, automated_api_results: preflight.summary,
      burp_executed: false, student_performed: false }, null, 2));
    if (!values["stop-after-setup"]) {
      console.log("Lab ready. Open Burp and follow the private README. Ctrl+C stops this lab.");
      while (!interrupted && !finished) await delay(200);
      if (finished && !interrupted) throw new Error("Lab process stopped unexpectedly; regenerate the kit before reuse.");
    }
  } finally {
    process.removeListener("SIGINT", interrupt);
    process.removeListener("SIGTERM", interrupt);
    await stopTree(child, ended);
  }
}

module.exports = { buildKit, inside, writeKit };
if (require.main === module) main().catch(error => { console.error("Burp preparation failed: " + error.message); process.exitCode = 1; });
