// Kiểm tra golden path của frontend bằng Edge headless qua CDP. Không cần Playwright.
//   node demo/browser_check.mjs "<đề bài>" demo/web_shot.png
import { spawn } from "node:child_process";
import { writeFileSync, existsSync } from "node:fs";

const EDGE = ["C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", "C:/Program Files/Microsoft/Edge/Application/msedge.exe"].find(existsSync);
const [statement, outPng] = [process.argv[2], process.argv[3] ?? "demo/web_shot.png"];
const PORT = 9333;

const edge = spawn(EDGE, [`--remote-debugging-port=${PORT}`, "--headless=new", "--disable-gpu", "--hide-scrollbars",
  "--window-size=1280,1400", "--user-data-dir=" + process.env.TEMP + "/edge-cdp-profile", "about:blank"], { stdio: "ignore" });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let target;
for (let i = 0; i < 30 && !target; i++) {
  try { target = (await (await fetch(`http://localhost:${PORT}/json`)).json()).find((t) => t.type === "page"); } catch { await sleep(300); }
}
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise((r) => (ws.onopen = r));
let id = 0; const pending = new Map();
ws.onmessage = (m) => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } };
const send = (method, params = {}) => new Promise((r) => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const evaluate = async (expr) => (await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true })).result?.result?.value;

await send("Page.enable"); await send("Runtime.enable");
await send("Page.navigate", { url: "http://localhost:3000" });
await sleep(2500);
console.log("title:", await evaluate("document.title"));

// Nhập đề qua React: dùng native setter để React nhận sự kiện input
await evaluate(`(() => {
  const ta = document.querySelector("textarea");
  const set = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value").set;
  set.call(ta, ${JSON.stringify(statement)});
  ta.dispatchEvent(new Event("input", { bubbles: true }));
  return ta.value.length;
})()`);
await sleep(200);
await evaluate(`[...document.querySelectorAll("button")].find(b => b.textContent.trim() === "Giải").click()`);

const t0 = Date.now();
let stagesSeen = new Set();
while (Date.now() - t0 < 240000) {
  const st = await evaluate(`({conf: !!document.querySelector(".conf"), err: document.querySelector(".error")?.textContent ?? null,
     active: document.querySelector(".stages li.active")?.textContent?.trim() ?? null})`);
  if (st.active) stagesSeen.add(st.active);
  if (st.conf || st.err) { console.log("kết quả:", st.err ? "LỖI " + st.err : "OK"); break; }
  await sleep(1000);
}
console.log("giai đoạn đã thấy:", [...stagesSeen].join(" → "));
console.log("độ tin cậy:", await evaluate(`document.querySelector(".conf strong")?.textContent`));
console.log("số gợi ý:", await evaluate(`document.querySelectorAll(".hints li").length`));
console.log("nút xem lời giải:", await evaluate(`!![...document.querySelectorAll("button")].find(b => b.textContent.includes("xem lời giải"))`));

// Mở lời giải, rê chuột vào bước thứ 2 -> hình phải tô sáng
await evaluate(`[...document.querySelectorAll("button")].find(b => b.textContent.includes("xem lời giải"))?.click()`);
await sleep(300);
console.log("số bước:", await evaluate(`document.querySelectorAll(".step").length`));
await evaluate(`(() => { const s = document.querySelectorAll(".step")[1]; s && s.dispatchEvent(new MouseEvent("mouseenter", {bubbles: true})); s && s.click(); })()`);
await sleep(400);
console.log("đối tượng tô sáng trên hình:", await evaluate(`[...document.querySelectorAll(".figure g.hl")].map(g => g.dataset.name).join(",") || "(không có hình)"`));

const shot = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
writeFileSync(outPng, Buffer.from(shot.result.data, "base64"));
console.log("ảnh:", outPng);
ws.close(); edge.kill();
