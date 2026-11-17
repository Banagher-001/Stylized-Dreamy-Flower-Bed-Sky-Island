from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from threading import Thread
import json,os
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent;payload=(OUT/'component-preview.html').read_bytes()
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(payload)
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);Thread(target=server.serve_forever,daemon=True).start();s=json.loads((OUT/'services-started.json').read_text());os.environ.update(s['browserEnvironment'])
READ=r'''()=>{const root=document.querySelector('.ar-tools-browser'),r=root.querySelector('.ar-tool-rail');return{mode:document.querySelector('main')?.dataset.readingMode,y:scrollY,d:{...root.dataset},rail:r.getBoundingClientRect().toJSON(),count:root.querySelector('.ar-card-count').textContent,cards:[...r.querySelectorAll('.ar-tool-card')].map(e=>({id:e.dataset.toolId,d:{...e.dataset},root:e.getBoundingClientRect().toJSON(),front:e.querySelector('.ar-card-front').getBoundingClientRect().toJSON(),detail:{text:e.querySelector('.ar-card-detail').textContent,hidden:e.querySelector('.ar-card-detail').hidden,opacity:getComputedStyle(e.querySelector('.ar-card-detail')).opacity,rect:e.querySelector('.ar-card-detail').getBoundingClientRect().toJSON()},button:e.querySelector('button').outerHTML}))}}'''
records=[]
try:
 with sync_playwright() as play:
  browser=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist'])
  for name,url,size in [('component',f'http://127.0.0.1:{server.server_port}',(1440,1100)),('main',s['origin']+'/?waterTime=2',(1440,900))]:
   ctx=browser.new_context(viewport={'width':size[0],'height':size[1]});p=ctx.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.goto(url,wait_until='domcontentloaded')
   if name=='component':
    p.wait_for_function('!!window.__aboutRefreshPreview');p.locator('[data-preview-station=A3]').click();p.wait_for_timeout(150);p.evaluate('()=>{const v=__aboutRefreshPreview.view;v.presentToolsEntrance({active:true,enabled:false,revealed:true});v.presentToolsTrack({active:true,allowed:true,automatic:false,top:70,bottom:innerHeight-40})}');p.locator('[data-action=auto]').click();p.wait_for_timeout(1200)
   else:
    p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=90000);p.evaluate('scrollTo({top:3.34/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})');p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.trackState==="running"',timeout=15000);p.wait_for_timeout(1200)
   before=p.evaluate(READ);b=p.locator('.ar-tool-card[data-tool-id=comfyui] .ar-card-front').bounding_box();p.mouse.move(b['x']+b['width']/2,b['y']+b['height']*.4);p.wait_for_timeout(1000);preview=p.evaluate(READ);p.screenshot(path=str(OUT/(name+'-preview-1.png')))
   btn=p.locator('.ar-tool-card[data-tool-id=comfyui] button').bounding_box();p.mouse.click(btn['x']+btn['width']/2,btn['y']+btn['height']/2);p.wait_for_timeout(700);p.mouse.move(10,80);p.wait_for_timeout(600);pinned=p.evaluate(READ);p.screenshot(path=str(OUT/(name+'-pinned-1.png')))
   btn=p.locator('.ar-tool-card[data-tool-id=comfyui] button').bounding_box();p.mouse.click(btn['x']+btn['width']/2,btn['y']+btn['height']/2);p.wait_for_timeout(700);closed=p.evaluate(READ)
   records.append({'name':name,'before':before,'preview':preview,'pinned':pinned,'closed':closed,'errors':errors});ctx.close()
  browser.close()
finally:server.shutdown();server.server_close();(OUT/'inspection-1.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
print(json.dumps([{'name':r['name'],'mode':r['preview'].get('mode'),'preview':r['preview']['d'],'pin':r['pinned']['d'],'closed':r['closed']['d'],'errors':r['errors']} for r in records],ensure_ascii=False))
