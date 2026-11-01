// Photographs the app's web export (EXPO_PUBLIC_USE_MOCK=1 npx expo export --platform web) at iPhone size, light and dark.
// Usage: node scripts/capture_app_screens.mjs <app>/dist <outdir> /h/find /today ...   then python3 scripts/frame_phone.py <framed-dir> <outdir>/*.png
// Content is captured at 390x766 (844 minus the status bar and home indicator) so frame_phone.py can add them back.
const PW = process.env.PLAYWRIGHT_PATH ?? 'playwright'; const pw = await import(PW); const { chromium } = pw.default ?? pw;
import http from 'node:http';
import { createReadStream, existsSync, statSync, mkdirSync } from 'node:fs';
import { join, extname } from 'node:path';
const [DIST, OUT, ...routes] = process.argv.slice(2);
mkdirSync(OUT,{recursive:true});
const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.ttf':'font/ttf','.woff2':'font/woff2','.svg':'image/svg+xml'};
const server=http.createServer((req,res)=>{let p=decodeURIComponent(req.url.split('?')[0]);let f=join(DIST,p);
if(existsSync(f)&&statSync(f).isFile()){res.writeHead(200,{'content-type':types[extname(f)]??'application/octet-stream'});return createReadStream(f).pipe(res);}
const h=f+'.html'; if(existsSync(h)){res.writeHead(200,{'content-type':'text/html'});return createReadStream(h).pipe(res);}
res.writeHead(200,{'content-type':'text/html'});createReadStream(join(DIST,'index.html')).pipe(res);});
await new Promise(r=>server.listen(4602,r));
const b=await chromium.launch();
for (const theme of ['light','dark']) {
const ctx=await b.newContext({viewport:{width:390,height:766},deviceScaleFactor:3,colorScheme:theme,isMobile:true,hasTouch:true,
 userAgent:'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1'});
for(const r of routes){const p=await ctx.newPage();await p.goto('http://localhost:4602'+r,{waitUntil:'networkidle'});await p.waitForTimeout(2500);
await p.screenshot({path:join(OUT,theme+'_'+r.replace(/\//g,'_').replace(/^_/,'')+'.png')});await p.close();}
await ctx.close();}
await b.close();server.close();console.log('done');
