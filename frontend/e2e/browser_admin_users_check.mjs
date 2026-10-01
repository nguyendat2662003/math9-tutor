// Kiểm tra tài khoản do admin cấp (Edge headless + CDP): trang đăng nhập không có tự đăng ký ->
// admin tạo 2 học sinh, đặt lại mật khẩu, khóa 1 em -> học sinh đăng nhập bị bắt đổi mật khẩu ->
// đổi xong mới dùng được app -> học sinh không vào được /admin -> tài khoản bị khóa không đăng nhập được.
//   node e2e/browser_admin_users_check.mjs <admin> <mật khẩu admin>
import { spawn } from "node:child_process";
import { existsSync, writeFileSync } from "node:fs";

const [ADMIN, ADMIN_PW] = process.argv.slice(2);
const TAG = Date.now().toString(36).slice(-4);
const EDGE = ["C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", "C:/Program Files/Microsoft/Edge/Application/msedge.exe"].find(existsSync);
const PORT = 9342;
const edge = spawn(EDGE, [`--remote-debugging-port=${PORT}`, "--headless=new", "--disable-gpu", "--hide-scrollbars",
  "--window-size=1280,1400", "--user-data-dir=" + process.env.TEMP + "/edge-cdp-users-" + Date.now(), "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let target;
for (let i = 0; i < 30 && !target; i++) {
  try { target = (await (await fetch(`http://localhost:${PORT}/json`)).json()).find((t) => t.type === "page"); } catch { await sleep(300); }
}
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0; const pending = new Map(); const errs = [];
const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
ws.onmessage = (m) => {
  const d = JSON.parse(m.data);
  if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); }
  if (d.method === "Page.javascriptDialogOpening") send("Page.handleJavaScriptDialog", { accept: true });
  if (d.method === "Runtime.exceptionThrown") errs.push(d.params.exceptionDetails.exception?.description ?? "exception");
};
const ev = async (e) => {
  const r = await send("Runtime.evaluate", { expression: e, awaitPromise: true, returnByValue: true });
  if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails.exception?.description));
  return r.result?.result?.value;
};
const waitFor = async (js, ms = 30000) => {
  for (let t = 0; t < ms; t += 250) { if (await ev(js)) return; await sleep(250); }
  throw new Error("hết giờ chờ: " + js);
};
const go = async (u) => { await send("Page.navigate", { url: "http://localhost:3000" + u }); await sleep(1500); };
const setVal = (sel, val, idx = 0, proto = "HTMLInputElement") => ev(`(() => { const el = document.querySelectorAll(${JSON.stringify(sel)})[${idx}];
  Object.getOwnPropertyDescriptor(${proto}.prototype, "value").set.call(el, ${JSON.stringify(val)});
  el.dispatchEvent(new Event("input", { bubbles: true })); })()`);
const click = (sel, text) => ev(`[...document.querySelectorAll(${JSON.stringify(sel)})].find(b => b.textContent.trim().includes(${JSON.stringify(text)})).click()`);
const shot = async (f) => writeFileSync(f, Buffer.from((await send("Page.captureScreenshot", { format: "png" })).result.data, "base64"));
async function login(u, p) {
  await go("/login");
  await waitFor(`!!document.querySelector(".auth__form")`);
  await sleep(1200);
  await setVal(".auth__form input[autocomplete=username]", u);
  await setVal(".auth__form input[type=password]", p);
  await click(".auth__form button", "Đăng nhập");
}
async function logout() {
  await ev(`[...document.querySelectorAll(".nav__user button")].find(b => b.textContent.includes("Đăng xuất"))?.click()`);
  await waitFor(`location.pathname === "/login"`);
}

await send("Page.enable"); await send("Runtime.enable");

// 1. Trang đăng nhập không còn tự đăng ký
await go("/login");
await waitFor(`!!document.querySelector(".auth__form")`);
console.log("1. Trang đăng nhập có thẻ 'Tạo tài khoản'?", await ev(`/Tạo tài khoản/.test(document.body.innerText)`),
  "· ghi chú:", await ev(`document.querySelector(".auth__form p.muted")?.textContent`));

// 2. Admin vào Quản trị -> tạo 2 học sinh
await login(ADMIN, ADMIN_PW);
await waitFor(`!!document.querySelector(".nav__user")`);
console.log("2. Admin đăng nhập · menu:", await ev(`[...document.querySelectorAll(".nav__link")].map(a => a.innerText.trim())`));
await go("/admin");
await waitFor(`!!document.querySelector(".students textarea")`);
await setVal(".students textarea", `Nguyễn Văn Thử ${TAG}\nthu.b${TAG}, Trần Thị Bê`, 0, "HTMLTextAreaElement");
await click(".students .btn", "Tạo");
await waitFor(`document.querySelectorAll(".print-area tbody tr").length === 2`);
const accts = await ev(`[...document.querySelectorAll(".print-area tbody tr")].map(tr => [...tr.querySelectorAll("td")].map(td => td.innerText.trim()))`);
console.log("   Tạo tài khoản:", accts.map(([n, u]) => `${n} -> ${u}`).join(" · "), "· có mật khẩu tạm:", accts.every((a) => a[2]?.length === 10));
await shot("e2e/users_1_created.png");
const [[, userA, pwA], [, userB]] = accts;

// 3. Đặt lại mật khẩu em A, khóa em B
await waitFor(`[...document.querySelectorAll(".students .no-print .tbl tbody tr")].some(tr => tr.innerText.includes(${JSON.stringify(userB)}))`);
await ev(`[...document.querySelectorAll(".students .no-print .tbl tbody tr")].find(tr => tr.innerText.includes(${JSON.stringify(userB)}))
  .querySelectorAll(".tbl__act .linkbtn")[1].click()`);
await waitFor(`[...document.querySelectorAll(".students .no-print .tbl tbody tr")].find(tr => tr.innerText.includes(${JSON.stringify(userB)}))?.innerText.includes("Đã khóa")`);
await ev(`[...document.querySelectorAll(".students .no-print .tbl tbody tr")].find(tr => tr.innerText.includes(${JSON.stringify(userA)}))
  .querySelectorAll(".tbl__act .linkbtn")[0].click()`);
await waitFor(`/Mật khẩu mới/.test(document.querySelector(".print-area h3")?.textContent ?? "")`);
const newPwA = await ev(`document.querySelectorAll(".print-area tbody tr td")[2].innerText.trim()`);
console.log("3. Khóa", userB, "✓ · đặt lại mật khẩu", userA, "-> mật khẩu mới khác mật khẩu cũ:", newPwA !== pwA && newPwA.length === 10);
await logout();

// 4. Học sinh A: mật khẩu cũ không còn dùng được; mật khẩu mới -> bị bắt đổi
await login(userA, pwA);
await waitFor(`!!document.querySelector(".auth__form .error")`);
console.log("4. Đăng nhập bằng mật khẩu cũ (đã bị đặt lại):", await ev(`document.querySelector(".auth__form .error").textContent`));
await login(userA, newPwA);
await waitFor(`location.pathname === "/account"`);
console.log("   Mật khẩu tạm -> bị đưa tới", await ev(`location.pathname`), "·", await ev(`document.querySelector("h1").textContent`));
await go("/exam");
await sleep(800);
console.log("   Thử vào /exam khi chưa đổi -> vẫn ở", await ev(`location.pathname`));
await shot("e2e/users_2_force_change.png");
await setVal(".auth__form input[type=password]", newPwA, 0);
await setVal(".auth__form input[type=password]", "mat-khau-cua-em-1", 1);
await setVal(".auth__form input[type=password]", "mat-khau-cua-em-1", 2);
await click(".auth__form button", "Đổi mật khẩu");
await waitFor(`location.pathname === "/" && !!document.querySelector(".nav__user")`);
console.log("   Đổi xong -> vào được trang", await ev(`location.pathname`), "· menu:", await ev(`[...document.querySelectorAll(".nav__link")].map(a => a.innerText.trim())`));

// 5. Học sinh không vào được trang quản trị
await go("/admin");
await waitFor(`/chỉ dành cho tài khoản quản trị/.test(document.body.innerText)`);
console.log("5. Học sinh mở /admin ->", await ev(`document.querySelector("main .card").textContent`));
await logout();

// 6. Tài khoản bị khóa
await login(userB, "bat-ky-12345");
await waitFor(`!!document.querySelector(".auth__form .error")`);
console.log("6. Em bị khóa, sai mật khẩu:", await ev(`document.querySelector(".auth__form .error").textContent`));

console.log("TẠO:", JSON.stringify([userA, userB]));
console.log("Lỗi console:", errs.length ? errs : "không có");
ws.close(); edge.kill();
