// Kiểm tra trang quản trị kho đề + gợi ý bài tương tự (Edge headless + CDP).
//   node demo/browser_admin_check.mjs <mã ADMIN_TOKEN> <file đề .docx/.pdf/.png>
import { spawn } from "node:child_process";
import { existsSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const [TOKEN, DOC] = [process.argv[2], resolve(process.argv[3])];
const EDGE = ["C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe", "C:/Program Files/Microsoft/Edge/Application/msedge.exe"].find(existsSync);
const PORT = 9338;
const edge = spawn(EDGE, [`--remote-debugging-port=${PORT}`, "--headless=new", "--disable-gpu", "--hide-scrollbars",
  "--window-size=1280,1500", "--user-data-dir=" + process.env.TEMP + "/edge-cdp-admin", "about:blank"], { stdio: "ignore" });

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
  for (let t = 0; t < ms; t += 300) { if (await ev(js)) return true; await sleep(300); }
  throw new Error("hết giờ chờ: " + js);
};
const shot = async (f) => writeFileSync(f, Buffer.from((await send("Page.captureScreenshot", { format: "png" })).result.data, "base64"));
const setInput = (sel, val) => ev(`(() => { const el = document.querySelector(${JSON.stringify(sel)});
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(el, ${JSON.stringify(val)});
  el.dispatchEvent(new Event("input", { bubbles: true })); })()`);

await send("Page.enable"); await send("Runtime.enable"); await send("DOM.enable");
await send("Page.navigate", { url: "http://localhost:3000/admin" });
await waitFor(`!!document.querySelector(".app__head")`);
await ev(`localStorage.removeItem("math9.admin.token")`);
await send("Page.reload");
await waitFor(`!!document.querySelector(".login")`);
await sleep(3000);                 // chờ React hydrate xong, không thì gõ vào ô sẽ bị ghi đè

// Sai mã -> bị từ chối
await setInput(".login input", "sai-ma");
await ev(`[...document.querySelectorAll(".login button")].find(b => b.textContent === "Vào").click()`);
await waitFor(`!!document.querySelector(".login .error") || !!document.querySelector(".stats")`, 10000);
console.log("1. Mã sai:", await ev(`document.querySelector(".login .error")?.textContent ?? "KHÔNG bị chặn"`));

await setInput(".login input", TOKEN);
await ev(`[...document.querySelectorAll(".login button")].find(b => b.textContent === "Vào").click()`);
await waitFor(`!!document.querySelector(".stats")`);
console.log("2. Thống kê:", await ev(`document.querySelector(".stats").innerText.replace(/\\n+/g, " | ")`));
console.log("   Các lô:", await ev(`[...document.querySelectorAll(".batches li")].map(l => l.innerText.replace(/\\n/g, " — "))`));

// Tải lại đúng tài liệu cũ qua ô chọn file: mọi bài phải bị báo trùng
const { root } = (await send("DOM.getDocument")).result;
const { nodeId } = (await send("DOM.querySelector", { nodeId: root.nodeId, selector: "input[type=file]" })).result;
await send("DOM.setFileInputFiles", { nodeId, files: [DOC] });
await waitFor(`/Đang tách bài/.test(document.body.innerText)`, 15000);
console.log("3. Đã tải lên, đang tách bài…");
await waitFor(`!!document.querySelector(".adm-bar")`, 180000);
const res = await ev(`({
  bai: document.querySelectorAll(".adm").length,
  trung: [...document.querySelectorAll(".adm .st--bad")].map(e => e.textContent),
  canhBao: [...document.querySelectorAll(".adm .warn li")].map(e => e.textContent.slice(0, 70)),
})`);
console.log("4. Lô mới:", res.bai, "bài · báo trùng:", res.trung.length, JSON.stringify(res.trung));
console.log("   cảnh báo:", JSON.stringify(res.canhBao, null, 0));
await shot("demo/admin_1_batch.png");

// Loại cả lô trùng cho sạch
await ev(`[...document.querySelectorAll(".adm .q__head input[type=checkbox]")].forEach(c => c.click())`);
await sleep(300);
await ev(`[...document.querySelectorAll(".adm-bar button")].find(b => b.textContent === "Loại").click()`);
await waitFor(`/Đã loại/.test(document.querySelector(".okmsg")?.textContent ?? "")`, 15000);
console.log("5. Loại lô trùng:", await ev(`document.querySelector(".okmsg").textContent`));

// Trang Giải bài: giải xong phải có khung "Bài tương tự"
await send("Page.navigate", { url: "http://localhost:3000/?q=" + encodeURIComponent("Từ điểm M nằm ngoài đường tròn (O) kẻ hai tiếp tuyến MA, MB (A, B là tiếp điểm). Chứng minh tứ giác MAOB nội tiếp.") });
await waitFor(`document.querySelector("textarea")?.value?.length > 10`, 20000);
await ev(`[...document.querySelectorAll("button")].find(b => b.textContent.trim() === "Giải").click()`);
await waitFor(`!!document.querySelector(".conf") || !!document.querySelector(".error")`, 300000);
await waitFor(`!!document.querySelector(".similar")`, 20000).catch(() => {});
const sim = await ev(`[...document.querySelectorAll(".similar li")].map(li => li.innerText.split("\\n")[0].slice(0, 70))`);
console.log("6. Bài tương tự:", sim.length, JSON.stringify(sim, null, 0));
await ev(`document.querySelector(".similar").scrollIntoView()`);
await shot("demo/admin_2_similar.png");
await ev(`document.querySelector(".similar .linkbtn").click()`);
await sleep(500);
console.log("7. Bấm 'Làm bài này' -> ô đề:", JSON.stringify(await ev(`document.querySelector("textarea").value.slice(0, 70)`)));
console.log("Lỗi console:", errs.length ? errs : "không có");
ws.close(); edge.kill();
