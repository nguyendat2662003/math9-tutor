// Kiểm tra luồng gửi ảnh đề trên frontend (Edge headless + CDP).
//   node demo/browser_image_check.mjs demo/de_anh.png demo/web_img.png
import { spawn } from "node:child_process";
import { writeFileSync, existsSync, readFileSync } from "node:fs";
import { basename } from "node:path";

const EDGE = ["C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", "C:/Program Files/Microsoft/Edge/Application/msedge.exe"].find(existsSync);
const [imgPath, outPng] = [process.argv[2], process.argv[3] ?? "demo/web_img.png"];
const PORT = 9334;

const edge = spawn(EDGE, [`--remote-debugging-port=${PORT}`, "--headless=new", "--disable-gpu", "--hide-scrollbars",
  "--window-size=1280,1500", "--user-data-dir=" + process.env.TEMP + "/edge-cdp-img", "about:blank"], { stdio: "ignore" });

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
const evaluate = async (expr) => {
  const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true });
  if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails.exception?.description ?? r.result.exceptionDetails));
  return r.result?.result?.value;
};

await send("Page.enable"); await send("Runtime.enable");
await send("Page.navigate", { url: "http://localhost:3000" });
await sleep(2500);

// Dán ảnh qua clipboard: dựng File từ base64 rồi phát sự kiện paste — đúng đường người dùng hay dùng nhất
const b64 = readFileSync(imgPath).toString("base64");
await evaluate(`(async () => {
  const bin = atob(${JSON.stringify(b64)});
  const arr = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
  const file = new File([arr], ${JSON.stringify(basename(imgPath))}, { type: "image/png" });
  const dt = new DataTransfer(); dt.items.add(file);
  window.dispatchEvent(new ClipboardEvent("paste", { clipboardData: dt, bubbles: true, cancelable: true }));
  return true;
})()`);

for (let i = 0; i < 40; i++) {
  if (await evaluate(`!!document.querySelector(".pick--has img")`)) break;
  await sleep(500);
}
console.log("ảnh đã đính kèm:", await evaluate(`!!document.querySelector(".pick--has img")`));
console.log("nút Giải bật:", await evaluate(`!([...document.querySelectorAll("button")].find(b => b.textContent.trim() === "Giải")?.disabled ?? true)`));

await evaluate(`[...document.querySelectorAll("button")].find(b => b.textContent.trim() === "Giải").click()`);
const t0 = Date.now();
const stages = new Set();
while (Date.now() - t0 < 300000) {
  const st = await evaluate(`({conf: !!document.querySelector(".conf"), err: document.querySelector(".error")?.textContent ?? null,
     active: document.querySelector(".stages li.active")?.textContent?.trim() ?? null,
     ocr: document.querySelector(".ocr pre")?.textContent?.slice(0, 80) ?? null})`);
  if (st.active) stages.add(st.active);
  if (st.ocr && !globalThis.__ocr) { globalThis.__ocr = st.ocr; console.log("đề đọc từ ảnh:", st.ocr.replace(/\n/g, " | ")); }
  if (st.conf || st.err) { console.log("kết quả:", st.err ? "LỖI " + st.err : "OK"); break; }
  await sleep(1000);
}
console.log("giai đoạn:", [...stages].join(" → "));
console.log("độ tin cậy:", await evaluate(`document.querySelector(".conf strong")?.textContent`));
console.log("số gợi ý:", await evaluate(`document.querySelectorAll(".hints li").length`));
console.log("có hình:", await evaluate(`!!document.querySelector(".figure svg")`));

const shot = await send("Page.captureScreenshot", { format: "png" });
writeFileSync(outPng, Buffer.from(shot.result.data, "base64"));
console.log("ảnh:", outPng);
ws.close(); edge.kill();
