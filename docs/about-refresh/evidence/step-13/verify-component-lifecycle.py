from pathlib import Path
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from threading import Thread
import json,traceback,shutil,hashlib,sys
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent;run=OUT/sys.argv[1];run.mkdir(exist_ok=False)
build=json.loads((OUT/'component-build.json').read_text());payload=(ROOT/build['output']['path']).read_bytes();assert hashlib.sha256(payload).hexdigest()==build['output']['sha256']
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');save(run/'build.json',build);shutil.copy2(__file__,run/'test.py.txt');(run/'loaded-component.html').write_bytes(payload)
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(payload)
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);Thread(target=server.serve_forever,daemon=True).start()
report={'checks':[],'events':[],'complete':False,'standaloneActualComponents':True,'clockModified':False,'physicalDevice':False}
PRESENT='''()=>{const v=__aboutRefreshPreview.view;v.presentToolsEntrance({active:true,enabled:false,revealed:true});v.presentToolsTrack({active:true,allowed:true,automatic:false,top:70,bottom:innerHeight-40})}'''
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);report['version']=b.version
  try:
   for name in ['first-mouse-hover-after-touch-swipe'] if len(sys.argv)>2 else ['dispose-during-touch-button','restore-during-touch-button','remount-does-not-multiply-input','first-mouse-hover-after-touch-swipe']:
    c=b.new_context(viewport={'width':1440,'height':1100});q=c.new_page();q.set_default_timeout(12000);events=[];q.on('pageerror',lambda e:events.append(str(e)));entry={'id':name,'status':'失败'}
    try:
     q.goto(f'http://127.0.0.1:{server.server_port}/');q.wait_for_function('!!window.__aboutRefreshPreview');q.locator('[data-preview-station=A3]').click();q.wait_for_timeout(150);q.evaluate(PRESENT);q.locator('[data-action=auto]').click();q.wait_for_timeout(1100);q.locator('[data-action=auto]').click()
     if name=='first-mouse-hover-after-touch-swipe':
      f=q.locator('.ar-tool-card[data-tool-id=comfyui] .ar-card-front').bounding_box();q.mouse.move(f['x']+f['width']/2,f['y']+f['height']*.45);q.wait_for_function('document.querySelector(".ar-tools-browser").dataset.hoverState==="reading"');cdp=c.new_cdp_session(q);x=f['x']+f['width']/2;y=f['y']+f['height']*.45;cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
      for i in range(1,13):cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x-160*i/12,'y':y}]});q.wait_for_timeout(20)
      cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});q.wait_for_timeout(900);q.mouse.move(10,60);f=q.locator('.ar-tool-card[data-tool-id=comfyui] .ar-card-front').bounding_box();q.mouse.move(f['x']+f['width']/2,f['y']+f['height']*.45);q.wait_for_function('document.querySelector(".ar-tools-browser").dataset.hoverState==="reading"',timeout=2000);data=q.evaluate('({...document.querySelector(".ar-tools-browser").dataset})');assert data['toolInput']=='mouse' and data['hoverId']=='comfyui'
     elif name=='remount-does-not-multiply-input':
      q.locator('.ar-tool-card[data-tool-id=comfyui] button').click();q.wait_for_timeout(450);q.evaluate('window.__snapshot=__aboutRefreshPreview.view.captureState();window.__oldRoots=[]');base=q.evaluate('__aboutRefreshPreview.interactions');q.locator('[data-action=next]').click();q.wait_for_timeout(450);control=q.evaluate('__aboutRefreshPreview.interactions')-base;q.evaluate('__aboutRefreshPreview.view.restoreState(__snapshot)')
      for _ in range(10):q.evaluate('()=>{__oldRoots.push(__aboutRefreshPreview.view.toolsElement);__aboutRefreshPreview.remount(__snapshot)}');q.wait_for_timeout(50)
      q.evaluate(PRESENT);q.wait_for_timeout(400);a=q.evaluate('__aboutRefreshPreview.interactions');q.locator('[data-action=next]').click();q.wait_for_timeout(450);data=q.evaluate('({interactions:__aboutRefreshPreview.interactions,nodes:document.querySelectorAll(".ar-tools-browser").length,cards:document.querySelectorAll(".ar-tool-rail .ar-tool-card").length,d:{...__aboutRefreshPreview.view.toolsElement.dataset},old:__oldRoots.map(e=>({connected:e.isConnected,d:{...e.dataset}}))})');data['freshActionCallbacks']=control;data['remountedActionCallbacks']=data['interactions']-a;assert data['remountedActionCallbacks']==control and control>0 and data['nodes']==1 and data['cards']==22,data;assert data['d']['readingId']=='kling';assert all(not v['connected'] and v['d']['trackState']=='disposed' and v['d']['hoverFramePending']=='false' for v in data['old'])
     else:
      f=q.locator('.ar-tool-card[data-tool-id=comfyui] .ar-card-front').bounding_box();q.mouse.move(f['x']+f['width']/2,f['y']+f['height']*.45);q.wait_for_function('document.querySelector(".ar-tools-browser").dataset.hoverState==="reading"');q.evaluate('window.__old=__aboutRefreshPreview.view.toolsElement;window.__snapshot=__aboutRefreshPreview.view.captureState()');r=q.locator('.ar-tool-card[data-tool-id=comfyui] button').bounding_box();cdp=c.new_cdp_session(q);cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':r['x']+r['width']/2,'y':r['y']+r['height']/2}]});q.wait_for_timeout(80)
      if name.startswith('dispose'):q.evaluate('__aboutRefreshPreview.view.dispose()')
      else:q.evaluate('__aboutRefreshPreview.view.restoreState(__snapshot)');q.evaluate(PRESENT)
      cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});q.wait_for_timeout(650);data=q.evaluate('({connected:__old.isConnected,old:{...__old.dataset},nodes:document.querySelectorAll(".ar-tools-browser").length,snapshot:__snapshot,current:document.querySelector(".ar-tools-browser")?{...document.querySelector(".ar-tools-browser").dataset}:null})')
      if name.startswith('dispose'):assert not data['connected'] and data['nodes']==0 and data['old']['trackState']=='disposed' and data['old']['hoverState']=='disposed' and data['old']['trackFramePending']=='false'
      else:assert data['nodes']==1 and data['current']['detailMode']=='summary' and data['current']['trackEnabled']=='false' and data['current']['trackFramePending']=='false'
     assert not events,events;save(run/(name+'-data.json'),data);q.screenshot(path=str(run/(name+'.png')));entry.update(status='通过',data=name+'-data.json')
    except Exception as e:
     entry.update(error=str(e),traceback=traceback.format_exc())
     try:save(run/(name+'-failure.json'),q.evaluate('({roots:document.querySelectorAll(".ar-tools-browser").length,d:{...__aboutRefreshPreview.view.toolsElement.dataset},interactions:__aboutRefreshPreview.interactions})'));q.screenshot(path=str(run/(name+'-failure.png')))
     except Exception:pass
    finally:report['checks'].append(entry);report['events'].extend(events);c.close();save(run/'browser.json',report);print(json.dumps({'id':name,'status':entry['status'],'error':entry.get('error','')[:200]},ensure_ascii=False),flush=True)
  finally:b.close();report['browserClosed']=True
finally:server.shutdown();server.server_close();report['serverClosed']=True;report['complete']=all(v['status']=='通过' for v in report['checks']) and len(report['checks'])==(1 if len(sys.argv)>2 else 4);save(run/'browser.json',report)
raise SystemExit(0 if report['complete'] else 1)
