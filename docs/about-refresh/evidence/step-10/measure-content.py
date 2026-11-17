from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from threading import Thread
from datetime import datetime
from zoneinfo import ZoneInfo
import json,hashlib
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
source=ROOT/'docs/about-refresh/evidence/step-9/component-preview.html';payload=source.read_bytes()
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(payload)
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);Thread(target=server.serve_forever,daemon=True).start();results=[]
try:
 with sync_playwright() as play:
  browser=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);ctx=browser.new_context(viewport={'width':1440,'height':1100});p=ctx.new_page();p.goto(f'http://127.0.0.1:{server.server_port}');p.wait_for_function('!!window.__aboutRefreshPreview');p.locator('[data-preview-station=A3]').click();p.wait_for_timeout(200)
  p.add_style_tag(content='.ar-tool-rail .ar-stone-card .ar-card-footer{display:flex;flex-direction:row-reverse;align-items:center;justify-content:space-between;gap:8px}.ar-tool-rail .ar-stone-card .ar-detail-toggle{flex:0 0 auto}.ar-tool-rail .ar-stone-card .ar-card-tags{flex-wrap:nowrap}')
  for width in [340,360]:
   results.append(p.evaluate('''width=>[...document.querySelectorAll('.ar-tool-rail .ar-stone-card')].map(e=>{e.style.width=width+'px';e.style.minHeight='300px';e.style.setProperty('--ar-card-min-height','300px');e.querySelector('.ar-card-detail').hidden=false;const f=e.querySelector('.ar-card-front'),d=e.querySelector('.ar-card-detail'),b=e.querySelector('button');return{id:e.dataset.toolId,width,frontHeight:f.getBoundingClientRect().height,detailHeight:d.getBoundingClientRect().height,detailCharacters:d.textContent.length,overflow:f.scrollWidth-f.clientWidth,buttonHeight:b.getBoundingClientRect().height,bodyVisible:!d.hidden}})''',width))
  ctx.close();browser.close()
finally:server.shutdown();server.server_close()
report={'measuredAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'basis':'Step-9 real card DOM with temporary proposed width/footer CSS in test browser only. Not final implementation acceptance.','sourceSHA256':hashlib.sha256(payload).hexdigest(),'results':results,'allCardsMeasured':all(len(v)==22 for v in results),'browserClosed':True,'serverClosed':True};(OUT/'content-measurement.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'cards':len(results[0]),'widths':[{'width':v[0]['width'],'maxHeight':max(c['frontHeight'] for c in v),'maxOverflow':max(c['overflow'] for c in v),'minButtonHeight':min(c['buttonHeight'] for c in v)} for v in results]}))
