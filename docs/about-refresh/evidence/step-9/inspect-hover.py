from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from threading import Thread
import json,os
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
payload=(OUT/'component-preview.html').read_bytes()
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(payload)
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);Thread(target=server.serve_forever,daemon=True).start()
s=json.loads((OUT/'services-started.json').read_text());os.environ.update(s['browserEnvironment'])
READ='''()=>{const root=document.querySelector('.ar-tools-browser'),r=root.querySelector('.ar-tool-rail'),a=root.querySelector('[data-reading="true"]');return {viewport:[innerWidth,innerHeight],mode:document.querySelector('main')?.dataset.readingMode,context:document.querySelector('.about-pillar-reader')?.dataset.safeBounds,root:{...root.dataset},rail:r.getBoundingClientRect().toJSON(),active:a?{id:a.dataset.toolId,pose:a.dataset.pose,reading:a.dataset.readingPose,front:a.querySelector('.ar-card-front').getBoundingClientRect().toJSON(),shadow:a.querySelector('.ar-card-shadow').getBoundingClientRect().toJSON()}:null,controls:root.querySelector('.ar-tool-controls').getBoundingClientRect().toJSON()}}'''
report=[]
try:
 with sync_playwright() as play:
  browser=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist'])
  for name,size,url in [('component',(1440,1100),f'http://127.0.0.1:{server.server_port}'),('main',(1440,900),s['origin']+'/?waterTime=2')]:
   ctx=browser.new_context(viewport={'width':size[0],'height':size[1]});p=ctx.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
   p.goto(url,wait_until='domcontentloaded')
   if name=='component':
    p.wait_for_function('!!window.__aboutRefreshPreview');p.locator('[data-preview-station=A3]').click();p.wait_for_timeout(150)
    p.evaluate('()=>{const v=__aboutRefreshPreview.view;v.presentToolsEntrance({active:true,enabled:false,revealed:true});v.presentToolsTrack({active:true,allowed:true,automatic:false,top:70,bottom:innerHeight-40})}');p.locator('[data-action=auto]').click();p.wait_for_timeout(1150)
   else:
    p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=90000)
    if p.locator('main').get_attribute('data-reading-mode')=='stable':p.locator('.tour-reading-flow [data-flow-anchor=A3]').scroll_into_view_if_needed();p.wait_for_timeout(700);p.locator('[data-action=auto]').click()
    else:p.evaluate('scrollTo({top:3.34/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})')
    p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.trackState==="running"',timeout=30000);p.wait_for_timeout(1150)
   before=p.evaluate(READ)
   box=p.locator('.ar-tool-card[data-tool-id=comfyui] .ar-card-front').bounding_box();p.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2);p.wait_for_timeout(900)
   hovered=p.evaluate(READ);p.screenshot(path=str(OUT/(name+'-hover-second.png')))
   p.mouse.move(50,80);p.wait_for_timeout(1200);after=p.evaluate(READ)
   report.append({'name':name,'before':before,'hovered':hovered,'after':after,'errors':errors});ctx.close()
  browser.close()
finally:server.shutdown();server.server_close();(OUT/'inspection-2.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps([{'name':r['name'],'mode':r['before'].get('mode'),'state':r['hovered']['root'].get('hoverState'),'profile':r['hovered']['root'].get('hoverProfile'),'errors':r['errors']} for r in report],ensure_ascii=False))
