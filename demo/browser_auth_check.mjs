// Kiểm tra đăng nhập + lịch sử (Edge headless + CDP): chưa đăng nhập bị chuyển về /login ->
// đăng nhập (tài khoản do admin cấp, ĐÃ đổi mật khẩu) -> giải một bài -> xem lại trong Lịch sử ->
// luyện đề, nộp -> mở lại từ Lịch sử -> đăng xuất -> trang cần đăng nhập bị chặn -> sai mật khẩu -> đăng nhập lại.
//   node demo/browser_auth_check.mjs <tên đăng nhập> <mật khẩu>
import { spawn } from "node:child_process";
import { existsSync, writeFileSync } from "node:fs";

const EDGE = ["C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", "C:/Program Files/Microsoft/Edge/Application/msedge.exe"].find(existsSync);
const PORT = 9340;
const [USER, PASS] = process.argv.slice(2);
if (!USER || !PASS) throw new Error("Cần tên đăng nhập + mật khẩu của một tài khoản học sinh đã đổi mật khẩu");
const edge = spawn(EDGE, [`--remote-debugging-port=${PORT}`, "--headless=new", "--disable-gpu", "--hide-scrollbars",
  "--window-size=1280,1400", "--user-data-dir=" + process.env.TEMP + "/edge-cdp-auth-" + Date.now(), "about:blank"], { stdio: "ignore" });

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
  for (let t = 0; t < ms; t += 300) { if (await ev(js)) return; await sleep(300); }
  throw new Error("hết giờ chờ: " + js);
};
const go = async (url) => { await send("Page.navigate", { url: "http://localhost:3000" + url }); await sleep(1500); };
const typeInto = (sel, val) => ev(`(() => { const el = document.querySelector(${JSON.stringify(sel)});
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(el, ${JSON.stringify(val)});
  el.dispatchEvent(new Event("input", { bubbles: true })); })()`);
const click = (sel, text) => ev(`[...document.querySelectorAll(${JSON.stringify(sel)})].find(b => b.textContent.trim().includes(${JSON.stringify(text)})).click()`);
const shot = async (f) => writeFileSync(f, Buffer.from((await send("Page.captureScreenshot", { format: "png" })).result.data, "base64"));

await send("Page.enable"); await send("Runtime.enable");

// 1. Chưa đăng nhập -> bị chuyển về /login
await go("/history");
await waitFor(`location.pathname === "/login"`);
console.log("1. Vào /history khi chưa đăng nhập ->", await ev(`location.pathname + location.search`));
await waitFor(`!!document.querySelector(".auth__form")`);
await sleep(1500);

// 2. Đăng nhập (không có tự đăng ký — tài khoản do admin tạo)
await typeInto(".auth__form input[autocomplete=username]", USER);
await typeInto(".auth__form input[type=password]", PASS);
await click(".auth__form button", "Đăng nhập");
await waitFor(`location.pathname === "/history" && !!document.querySelector(".nav__user")`);
console.log(`2. Đăng nhập "${USER}" -> quay lại đúng trang:`, await ev(`location.pathname`),
  "· thanh điều hướng:", await ev(`document.querySelector(".nav__user").innerText.replace(/\n/g, " | ")`));

// 3. Giải một bài
await go("/?q=" + encodeURIComponent("Giải phương trình x² − 5x + 6 = 0."));
await waitFor(`document.querySelector("textarea")?.value?.length > 5`, 20000);
await click("button", "Giải");
await waitFor(`!!document.querySelector(".conf") || !!document.querySelector(".error")`, 240000);
console.log("3. Giải bài:", await ev(`document.querySelector(".conf strong")?.textContent ?? document.querySelector(".error")?.textContent`));

// 4. Lịch sử: bài vừa giải có trong danh sách, mở lại được
await go("/history");
await waitFor(`document.querySelectorAll(".hist li").length > 0`);
console.log("4. Lịch sử bài đã giải:", await ev(`[...document.querySelectorAll(".hist li")].map(li => li.innerText.replace(/\\n/g, " · ").slice(0, 90))`));
await ev(`document.querySelector(".hist li button").click()`);
await waitFor(`!!document.querySelector(".conf")`);
console.log("   Mở lại:", await ev(`document.querySelector(".conf strong").textContent`), "· số bước:",
  await ev(`document.querySelectorAll(".step").length`), "· gợi ý:", await ev(`document.querySelectorAll(".hints li").length`));
await shot("demo/auth_1_history_solve.png");

// 5. Luyện đề: tạo đề tự chọn nhỏ, trả lời, nộp
await go("/exam");
await waitFor(`!!document.querySelector(".tabs")`);
await sleep(800);
await click(".tabs button", "Tự chọn");
await waitFor(`!!document.querySelector(".custom .btn")`);
await ev(`document.querySelector(".custom .btn").click()`);
await waitFor(`!!document.querySelector(".paper-bar")`);
await ev(`[...document.querySelectorAll(".opts")].forEach(o => o.querySelector(".opt").click())`);
await sleep(300);
await click(".paper-bar button", "Nộp bài");
await waitFor(`!!document.querySelector(".score__big")`);
const examScore = await ev(`document.querySelector(".score__big").textContent`);
const hasSelf = await ev(`!!document.querySelector(".selfmark button")`);
if (hasSelf) { await ev(`document.querySelector(".selfmark").querySelectorAll("button")[2].click()`); await sleep(1200); }
const afterSelf = await ev(`document.querySelector(".score__big").textContent`);
console.log("5. Nộp đề:", examScore, hasSelf ? `-> tự chấm 1 câu: ${afterSelf}` : "");

// 6. Lịch sử đề: có điểm, mở lại ra đúng kết quả (điểm tự chấm lấy từ server)
await ev(`localStorage.clear()`);                     // bỏ bản lưu trên máy: kết quả phải đến từ server
await go("/history");
await waitFor(`document.querySelectorAll(".tabs button").length === 2`);
await click(".tabs button", "Đề đã luyện");
await waitFor(`document.querySelectorAll(".hist__exam").length > 0`);
console.log("6. Lịch sử đề:", await ev(`[...document.querySelectorAll(".hist__exam")].map(li => li.innerText.replace(/\\n/g, " · ").slice(0, 90))`));
await ev(`document.querySelector(".hist__exam a").click()`);
await waitFor(`!!document.querySelector(".score__big")`);
console.log("   Mở lại đề:", await ev(`location.pathname + location.search`).then((u) => u.slice(0, 20) + "…"),
  "· điểm:", await ev(`document.querySelector(".score__big").textContent`));

// 7. Đăng xuất -> trang cần đăng nhập bị chặn
await click(".nav__user button", "Đăng xuất");
await waitFor(`location.pathname === "/login"`);
await go("/exam");
await waitFor(`location.pathname === "/login"`);
console.log("7. Sau đăng xuất, vào /exam ->", await ev(`location.pathname`));

// 8. Sai mật khẩu -> báo lỗi; đúng -> vào được
await waitFor(`!!document.querySelector(".auth__form")`);
await sleep(1500);
await typeInto(".auth__form input[autocomplete=username]", USER);
await typeInto(".auth__form input[type=password]", "sai-mat-khau");
await click(".auth__form button", "Đăng nhập");
await waitFor(`!!document.querySelector(".auth__form .error")`, 10000);
console.log("8. Sai mật khẩu:", await ev(`document.querySelector(".auth__form .error").textContent`));
await typeInto(".auth__form input[type=password]", PASS);
await click(".auth__form button", "Đăng nhập");
await waitFor(`location.pathname === "/exam" && !!document.querySelector(".nav__user")`);
console.log("   Đúng mật khẩu -> về lại:", await ev(`location.pathname`));
await shot("demo/auth_2_back.png");

console.log("Lỗi console:", errs.length ? errs : "không có");
ws.close(); edge.kill();
