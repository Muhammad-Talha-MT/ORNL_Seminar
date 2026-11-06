// Render every slide to PNG at 1920x1080 and report layout problems.
// Usage: node tools/render_slides.mjs <deck-url> <out-dir>
//   e.g. node tools/render_slides.mjs http://localhost:8000/index.html renders
// Needs the `playwright` package (npm i playwright && npx playwright install chromium).
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

const url = process.argv[2] || "http://localhost:8000/index.html";
const out = process.argv[3] || "renders";
fs.mkdirSync(out, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
page.on("requestfailed", (r) => errors.push("request failed: " + r.url()));

await page.goto(url, { waitUntil: "networkidle" });
await page.waitForFunction(() => window.Reveal && Reveal.isReady());
await page.evaluate(() => document.fonts.ready);
const total = await page.evaluate(() => Reveal.getTotalSlides());
const report = [];

for (let i = 0; i < total; i++) {
  await page.evaluate((i) => { Reveal.slide(i, 0, 999); }, i);
  await page.waitForTimeout(2600);
  const issues = await page.evaluate(() => {
    const sec = Reveal.getCurrentSlide();
    const sr = sec.getBoundingClientRect();
    const sx = sr.width / 1920, sy = sr.height / 1080;
    const out = [];
    const desc = (el) => (el.className && typeof el.className === "string" ? "." + el.className.trim().split(/\s+/).join(".") : el.tagName.toLowerCase()) + (el.textContent ? ' "' + el.textContent.trim().slice(0, 40).replace(/\s+/g, " ") + '"' : "");
    sec.querySelectorAll("*").forEach((el) => {
      if (el.closest("aside.notes") || el.closest(".katex-mathml") || el.closest("svg") && el.tagName.toLowerCase() !== "svg") return;
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height) return;
      const L = (r.left - sr.left) / sx, T = (r.top - sr.top) / sy, R = (r.right - sr.left) / sx, B = (r.bottom - sr.top) / sy;
      if (R > 1921 || B > 1081 || L < -1 || T < -1) out.push(`outside slide (${L|0},${T|0})-(${R|0},${B|0}) ${desc(el)}`);
      const cs = getComputedStyle(el);
      if (el.scrollHeight > el.clientHeight + 2 && cs.overflowY !== "visible" && el.clientHeight > 0 && el.tagName !== "HTML") out.push(`scroll-clipped y ${el.scrollHeight}>${el.clientHeight} ${desc(el)}`);
      if (el.scrollWidth > el.clientWidth + 2 && cs.overflowX !== "visible" && el.clientWidth > 0) out.push(`scroll-clipped x ${el.scrollWidth}>${el.clientWidth} ${desc(el)}`);
    });
    // children overflowing their flex/card parents (visible overflow)
    sec.querySelectorAll(".card, .body, .concl > div, .banner, .qbox").forEach((p) => {
      const pr = p.getBoundingClientRect();
      p.querySelectorAll(":scope > *").forEach((c) => {
        if (c.classList.contains("tab")) return;
        const r = c.getBoundingClientRect();
        if (r.bottom > pr.bottom + 3 * sy || r.right > pr.right + 3 * sx) out.push(`child overflows ${desc(p).slice(0, 30)} -> ${desc(c)}`);
      });
    });
    sec.querySelectorAll("img").forEach((im) => { if (!im.complete || !im.naturalWidth) out.push("image not loaded " + im.getAttribute("src")); });
    const notes = sec.querySelector("aside.notes");
    const words = notes ? notes.textContent.trim().split(/\s+/).length : 0;
    return { issues: [...new Set(out)], words, title: (sec.querySelector(".tbar, h2, h1") || {}).textContent?.trim().slice(0, 70) };
  });
  const file = path.join(out, `slide-${String(i + 1).padStart(2, "0")}.png`);
  await page.screenshot({ path: file });
  report.push({ slide: i + 1, ...issues });
}
await browser.close();
for (const r of report) {
  console.log(`#${r.slide} [${r.words}w] ${r.title}`);
  r.issues.forEach((x) => console.log("    ! " + x));
}
if (errors.length) { console.log("\nPage errors:"); [...new Set(errors)].forEach((e) => console.log("  " + e)); }
