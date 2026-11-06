// Export the deck to PDF via reveal.js print mode (?print-pdf).
// Usage: node tools/export_pdf.mjs http://localhost:8000/index.html ORNL_Seminar_Talha.pdf
import { chromium } from "playwright";

const url = process.argv[2] || "http://localhost:8000/index.html";
const out = process.argv[3] || "ORNL_Seminar_Talha.pdf";
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
await page.goto(url.split("#")[0] + "?print-pdf", { waitUntil: "networkidle" });
await page.waitForFunction(() => window.Reveal && Reveal.isReady());
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(1500);
await page.pdf({ path: out, width: "1920px", height: "1080px", printBackground: true, preferCSSPageSize: true });
await browser.close();
console.log("wrote", out);
