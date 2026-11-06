import { chromium } from "playwright";
const [,, url, n, out, frags] = process.argv;
const b = await chromium.launch(); const p = await b.newPage({ viewport:{width:1920,height:1080}});
await p.goto(url,{waitUntil:"networkidle"}); await p.waitForFunction(()=>window.Reveal&&Reveal.isReady());
await p.evaluate(i=>Reveal.slide(i,0,-1),+n-1);
for(let k=0;k<+frags;k++) await p.evaluate(()=>Reveal.nextFragment());
await p.waitForTimeout(2200); await p.screenshot({path:out}); await b.close();
