import { chromium } from "playwright";
const [,, url, n, out] = process.argv;
const b = await chromium.launch(); const p = await b.newPage({ viewport:{width:1920,height:1080}});
await p.goto(url,{waitUntil:"networkidle"}); await p.waitForFunction(()=>window.Reveal&&Reveal.isReady());
await p.evaluate(i=>Reveal.slide(i,0,999),+n-1); await p.waitForTimeout(2500);
await p.screenshot({path:out}); await b.close();
