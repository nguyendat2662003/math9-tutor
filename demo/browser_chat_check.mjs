// Kiểm tra hỏi đáp sau khi giải (Edge headless + CDP): giải bài hình -> hỏi thêm -> chữ hiện dần,
// nút [bước ..] tô sáng hình, số câu còn lại giảm -> mở lại trong Lịch sử vẫn thấy hỏi đáp.
//   node demo/browser_chat_check.mjs
import { spawn } from "node:child_process";
import { existsSync, writeFileSync } from "node:fs";

const EDGE = ["C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", "C:/Program Files/Microsoft/Edge/Application/msedge.exe"].find(existsSync);
const PORT = 9341;
const USER = "chat_" + Date.now().toString(36);
const PASS = "matkhau-thu-123";
const DE = "Cho đường tròn (O) và điểm A nằm ngoài đường tròn. Kẻ hai tiếp tuyến AB, AC với đường tròn (B, C là các tiếp điểm). "
  + "Gọi H là giao điểm của OA và BC.\na) Chứng minh tứ giác ABOC nội tiếp.\nb) Chứng minh OA vuông góc với BC tại H.";
const HOI = "Vì sao tổng hai góc ABO và ACO bằng 180 độ thì tứ giác ABOC nội tiếp được?";

const edge = spawn(EDGE, [`--remote-debugging-port=${PORT}`, "--headless=new", "--disable-gpu", "--hide-scrollbars",
  "--window-size=1280,1600", "--user-data-dir=" + process.env.TEMP + "/edge-cdp-chat-" + Date.now(), "about:blank"], { stdio: "ignore" });
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
  if (d.method === "Runtime.exceptionThrown") errs.push(d.params.exceptionDetails.exception?.description ?? "exception");
};
const ev = async (e) => {
  const r = await send("Runtime.evaluate", { expression: e, awaitPromise: true, returnByValue: true });
  if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails.exception?.description));
  return r.result?.result?.value;
};
const waitFor = async (js, ms = 30000) => {
  for (let t = 0; t < ms; t += 200) { if (await ev(js)) return; await sleep(200); }
  throw new Error("hết giờ chờ: " + js);
};
const setVal = (sel, val, proto = "HTMLInputElement") => ev(`(() => { const el = document.querySelector(${JSON.stringify(sel)});
  Object.getOwnPropertyDescriptor(${proto}.prototype, "value").set.call(el, ${JSON.stringify(val)});
  el.dispatchEvent(new Event("input", { bubbles: true })); })()`);
const shot = async (f) => writeFileSync(f, Buffer.from((await send("Page.captureScreenshot", { format: "png" })).result.data, "base64"));

await send("Page.enable"); await send("Runtime.enable");

// Đăng ký
await send("Page.navigate", { url: "http://localhost:3000/login" });
await waitFor(`!!document.querySelector(".auth__form")`);
await sleep(1500);
await ev(`[...document.querySelectorAll(".tabs button")].find(b => b.textContent.includes("Tạo tài khoản")).click()`);
await sleep(300);
await setVal(".auth__form input[autocomplete=username]", USER);
await ev(`(() => { const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
  document.querySelectorAll(".auth__form input[type=password]").forEach(el => { set.call(el, ${JSON.stringify(PASS)}); el.dispatchEvent(new Event("input", { bubbles: true })); }); })()`);
await ev(`[...document.querySelectorAll(".auth__form button")].find(b => b.textContent.includes("Tạo tài khoản")).click()`);
await waitFor(`!!document.querySelector(".nav__user")`);
console.log("1. Đã đăng ký", USER);

// Giải bài hình
await send("Page.navigate", { url: "http://localhost:3000/?q=" + encodeURIComponent(DE) });
await waitFor(`document.querySelector("textarea")?.value?.length > 20`, 20000);
await ev(`[...document.querySelectorAll("button")].find(b => b.textContent.trim() === "Giải").click()`);
await waitFor(`!!document.querySelector(".conf") || !!document.querySelector(".error")`, 300000);
await waitFor(`!!document.querySelector(".chat")`, 20000);
console.log("2. Giải xong:", await ev(`document.querySelector(".conf strong")?.textContent`),
  "· khung hỏi đáp:", await ev(`document.querySelector(".chat__head").innerText.replace(/\\n/g, " · ")`),
  "· câu hỏi gợi ý:", await ev(`document.querySelectorAll(".chat .samples button").length`));

// Hỏi
await setVal(".chat__input textarea", HOI, "HTMLTextAreaElement");
const t0 = Date.now();
await ev(`[...document.querySelectorAll(".chat__input button")].find(b => b.textContent.trim() === "Gửi").click()`);
await waitFor(`(document.querySelector(".chat__msg--assistant .chat__text")?.innerText ?? "").length > 0`, 60000);
const first = (Date.now() - t0) / 1000;
const len1 = await ev(`document.querySelector(".chat__msg--assistant .chat__text").innerText.length`);
await waitFor(`[...document.querySelectorAll(".chat__input button")].some(b => b.textContent.trim() === "Gửi")`, 120000);
const total = (Date.now() - t0) / 1000;
const answer = await ev(`document.querySelector(".chat__msg--assistant .chat__text").innerText`);
console.log(`3. Hỏi: chữ đầu sau ${first.toFixed(1)}s (lúc đó ${len1} ký tự) · xong sau ${total.toFixed(1)}s · ${answer.length} ký tự`);
console.log("   Còn lại:", await ev(`document.querySelector(".chat__head .muted").textContent`));
console.log("   Có LaTeX thô (\\\\( hoặc \\\\frac)?", /\\\(|\\frac|\\\[/.test(answer));
console.log("   TRẢ LỜI:\n" + answer.split("\n").map((l) => "     " + l).join("\n"));

// Nút [bước ..] -> tô sáng hình
const refs = await ev(`document.querySelectorAll(".chat .stepref:not(:disabled)").length`);
if (refs) {
  await ev(`document.querySelector(".chat .stepref:not(:disabled)").dispatchEvent(new MouseEvent("mouseover", { bubbles: true }))`);
  await sleep(400);
  console.log(`4. ${refs} nút nhắc bước · di chuột vào "${await ev(`document.querySelector(".chat .stepref:not(:disabled)").textContent`)}" -> số đối tượng tô sáng trên hình:`,
    await ev(`document.querySelectorAll(".figure svg g.hl").length`));
} else {
  console.log("4. Câu trả lời không nhắc bước nào (không có nút [bước ..])");
}
await ev(`document.querySelector(".chat").scrollIntoView()`);
await shot("demo/chat_1_answer.png");

// Lịch sử: mở lại bài, hỏi đáp vẫn còn
await send("Page.navigate", { url: "http://localhost:3000/history" });
await waitFor(`document.querySelectorAll(".hist li button").length > 0`);
await ev(`document.querySelector(".hist li button").click()`);
await waitFor(`document.querySelectorAll(".chat__msg").length >= 2`, 20000);
console.log("5. Mở lại trong Lịch sử:", await ev(`document.querySelectorAll(".chat__msg").length`), "tin nhắn ·",
  await ev(`document.querySelector(".chat__head .muted").textContent`));

console.log("Lỗi console:", errs.length ? errs : "không có");
ws.close(); edge.kill();
