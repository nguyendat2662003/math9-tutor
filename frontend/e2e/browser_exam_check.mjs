// Kiểm tra luồng luyện đề trên frontend (Edge headless + CDP):
// chọn đề tỉnh -> làm bài -> tải lại trang (khôi phục bài) -> nộp -> tự chấm -> đề tự chọn -> màn hình hẹp.
//   node e2e/browser_exam_check.mjs
import { spawn } from "node:child_process";
import { existsSync, writeFileSync } from "node:fs";

const EDGE = ["C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", "C:/Program Files/Microsoft/Edge/Application/msedge.exe"].find(existsSync);
const PORT = 9335;
const edge = spawn(EDGE, [`--remote-debugging-port=${PORT}`, "--headless=new", "--disable-gpu", "--hide-scrollbars",
  "--window-size=1280,1600", "--user-data-dir=" + process.env.TEMP + "/edge-cdp-exam", "about:blank"], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let target;
for (let i = 0; i < 30 && !target; i++) {
  try { target = (await (await fetch(`http://localhost:${PORT}/json`)).json()).find((t) => t.type === "page"); } catch { await sleep(300); }
}
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0; const pending = new Map(); const consoleErrors = [];
const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
ws.onmessage = (m) => {
  const d = JSON.parse(m.data);
  if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); }
  if (d.method === "Page.javascriptDialogOpening") { console.log("  hộp thoại:", d.params.message); send("Page.handleJavaScriptDialog", { accept: true }); }
  if (d.method === "Runtime.exceptionThrown") consoleErrors.push(d.params.exceptionDetails.exception?.description ?? "exception");
  if (d.method === "Runtime.consoleAPICalled" && d.params.type === "error") consoleErrors.push(d.params.args.map((a) => a.value ?? a.description).join(" "));
};
const evaluate = async (expr) => {
  const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true });
  if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails.exception?.description ?? r.result.exceptionDetails));
  return r.result?.result?.value;
};
const waitFor = async (sel, ms = 20000) => {
  for (let t = 0; t < ms; t += 250) { if (await evaluate(`!!document.querySelector(${JSON.stringify(sel)})`)) return true; await sleep(250); }
  throw new Error("không thấy " + sel);
};
const shot = async (file, full = false) => {
  const r = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: full });
  writeFileSync(file, Buffer.from(r.result.data, "base64"));
};
const clickText = (sel, text) => evaluate(`[...document.querySelectorAll(${JSON.stringify(sel)})].find(b => b.textContent.includes(${JSON.stringify(text)})).click()`);

await send("Page.enable"); await send("Runtime.enable");
await send("Page.navigate", { url: "http://localhost:3000/exam" });
await waitFor(".app__head");
await evaluate(`localStorage.clear()`);          // bỏ bài làm dở của lần chạy trước (trang tự khôi phục nó)
await send("Page.reload");
await waitFor(".bp");
console.log("1. Chọn đề:", await evaluate(`[...document.querySelectorAll(".bp strong")].map(e => e.textContent).join(", ")`));
await shot("e2e/exam_1_setup.png");

await clickText(".bp", "Thanh Hóa");
await waitFor(".paper-bar");
const info = await evaluate(`({
  title: document.querySelector(".paper-bar strong").textContent,
  timer: document.querySelector(".timer").textContent,
  n: document.querySelectorAll(".q").length,
  sections: [...document.querySelectorAll("h2.section")].map(e => e.textContent),
  mcq: document.querySelectorAll(".opts").length,
  inputs: document.querySelectorAll(".q input[type=text]").length,
  drafts: document.querySelectorAll(".q textarea.draft").length,
  contexts: document.querySelectorAll(".context").length,
})`);
console.log("2. Làm bài:", JSON.stringify(info));
const t1 = info.timer; await sleep(2200);
console.log("   đồng hồ chạy:", t1, "→", await evaluate(`document.querySelector(".timer").textContent`));

// Trả lời: chọn A cho mọi câu trắc nghiệm, gõ "1" vào 2 ô đáp số đầu
await evaluate(`[...document.querySelectorAll(".opts")].forEach(o => o.querySelector(".opt").click())`);
await evaluate(`(() => {
  const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
  [...document.querySelectorAll(".q input[type=text]")].slice(0, 2).forEach(i => { set.call(i, "1"); i.dispatchEvent(new Event("input", { bubbles: true })); });
})()`);
await sleep(300);
const before = await evaluate(`document.querySelector(".paper-bar .muted:last-of-type")?.textContent ?? [...document.querySelectorAll(".paper-bar span.muted")].pop().textContent`);
console.log("   sau khi trả lời:", before);
await shot("e2e/exam_2_paper.png");

// Tải lại trang: bài làm phải còn
await send("Page.reload");
await waitFor(".paper-bar");
await sleep(500);
console.log("3. Sau khi tải lại: đã chọn", await evaluate(`document.querySelectorAll(".opt.on").length`), "phương án,",
  await evaluate(`[...document.querySelectorAll(".q input[type=text]")].filter(i => i.value === "1").length`), "ô đáp số còn giữ");

// Nộp (có hộp thoại xác nhận vì còn câu trống)
await clickText(".paper-bar button", "Nộp bài");
await waitFor(".score");
const res = await evaluate(`({
  score: document.querySelector(".score__big").textContent,
  detail: document.querySelector(".score .muted").textContent,
  statuses: [...document.querySelectorAll(".q .st")].reduce((m, e) => (m[e.textContent] = (m[e.textContent] ?? 0) + 1, m), {}),
  links: [...document.querySelectorAll("a.linkbtn")].length,
  firstLink: document.querySelector("a.linkbtn")?.getAttribute("href")?.slice(0, 60),
  solutions: document.querySelectorAll("details ol.sol").length,
})`);
console.log("4. Kết quả:", JSON.stringify(res));
const solveHref = await evaluate(`document.querySelector("a.linkbtn")?.getAttribute("href")`);

// Tự chấm một câu chứng minh
const hasSelf = await evaluate(`!!document.querySelector(".selfmark button")`);
if (hasSelf) {
  await evaluate(`[...document.querySelectorAll(".selfmark")][0].querySelectorAll("button")[2].click()`);
  await sleep(300);
  console.log("5. Sau khi tự chấm đủ điểm 1 câu:", await evaluate(`document.querySelector(".score__big").textContent`),
    "·", await evaluate(`document.querySelector(".score .muted").textContent`));
}
await shot("e2e/exam_3_result.png");

// Làm lại đề này: cùng seed -> cùng đề
const firstQ = await evaluate(`document.querySelector(".q .q__text").textContent`);
await clickText(".score button", "Làm lại đề này");
await waitFor(".paper-bar");
console.log("6. Làm lại đề cũ — câu đầu giống hệt:", firstQ === await evaluate(`document.querySelector(".q .q__text").textContent`),
  "· bài làm đã xóa:", await evaluate(`document.querySelectorAll(".opt.on").length === 0`));

// Đề tự chọn
await evaluate(`localStorage.clear()`);
await send("Page.reload");
await waitFor(".tabs");
await clickText(".tabs button", "Tự chọn");
await waitFor(".topic-grid");
const createBtn = await evaluate(`[...document.querySelectorAll(".custom .btn")][0].textContent`);
await clickText(".custom .btn", "Tạo đề");
await waitFor(".paper-bar");
console.log("7. Đề tự chọn:", createBtn, "→", await evaluate(`document.querySelectorAll(".q").length`), "câu,",
  await evaluate(`document.querySelector(".timer").textContent`));

// Màn hình điện thoại: không được tràn ngang
await send("Emulation.setDeviceMetricsOverride", { width: 390, height: 844, deviceScaleFactor: 2, mobile: true });
await sleep(600);
console.log("8. Rộng 390px — tràn ngang:", await evaluate(`document.documentElement.scrollWidth > window.innerWidth`));
await shot("e2e/exam_4_mobile.png");

// "Xem lời giải chi tiết" mở trang Giải bài với đề điền sẵn
await send("Emulation.clearDeviceMetricsOverride");
await send("Page.navigate", { url: "http://localhost:3000" + solveHref });
await waitFor("textarea");
// Đề điền vào sau khi trang hydrate xong (dev server mất khoảng 1–2 giây)
for (let t = 0; t < 10000 && !(await evaluate(`document.querySelector("textarea").value`)); t += 250) await sleep(250);
console.log("9. Trang Giải bài nhận đề:", JSON.stringify(await evaluate(`document.querySelector("textarea").value.slice(0, 90)`)));

console.log("Lỗi console:", consoleErrors.length ? consoleErrors : "không có");
ws.close(); edge.kill();
