from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from threading import Thread
import os,json,argparse,traceback,hashlib,shutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('run');args=ap.parse_args();run=OUT/args.run;run.mkdir(exist_ok=False)
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
build=json.loads((OUT/'component-build.json').read_text());payload=(ROOT/build['output']['path']).read_bytes();save(run/'build.json',build);shutil.copy2(__file__,run/'verify-track-state.py.txt')
report={'startedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'checks':[],'events':[],'complete':False,'clockModified':False,'standaloneActualComponents':True};failures=[]
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  if self.path not in ['/','/preview.html']:self.send_error(404);return
  self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(payload)
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}'
PRESENT='''()=>{const a=__aboutRefreshPreview,v=a.view;v.presentToolsEntrance({active:true,enabled:false,revealed:true});v.presentToolsTrack({active:true,allowed:true,automatic:false,top:document.querySelector('.ar-preview-bar').getBoundingClientRect().bottom+8,bottom:innerHeight-40});}'''
READ='''()=>({snapshot:__aboutRefreshPreview.view.captureState(),state:{...__aboutRefreshPreview.view.toolsElement.dataset},cards:[...__aboutRefreshPreview.view.toolsElement.querySelectorAll('.ar-tool-card')].map(e=>({id:e.dataset.toolId,instance:e.dataset.cardInstance,x:e.getBoundingClientRect().x})),old:window.__oldRoot?{connected:__oldRoot.isConnected,state:{...__oldBrowser.dataset}}:null})'''
try:
 with sync_playwright() as play:
  browser=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);report['version']=browser.version
  def setup(p):
   p.goto(origin+'/preview.html');p.wait_for_function('!!window.__aboutRefreshPreview');p.locator('[data-preview-station=A3]').click();p.wait_for_timeout(150);p.evaluate(PRESENT);p.locator('[data-action=auto]').click();p.wait_for_timeout(1200);assert float(p.locator('.ar-tools-browser').get_attribute('data-track-offset'))>0
  def read(p):return p.evaluate(READ)
  def case(name,fn):
   ctx=browser.new_context(viewport={'width':1440,'height':1100});p=ctx.new_page();p.set_default_timeout(15000);events=[];p.on('pageerror',lambda e:events.append(str(e)));entry={'id':name,'status':'失败'}
   try:
    setup(p);data=fn(p);assert not events,events;save(run/(name+'-data.json'),data);p.screenshot(path=str(run/(name+'.png')));entry.update(status='通过',data=name+'-data.json')
   except Exception as e:
    failures.append(name);entry.update(error=str(e),traceback=traceback.format_exc())
    try:save(run/(name+'-data.json'),read(p));p.screenshot(path=str(run/(name+'-failure.png')))
    except Exception:pass
   finally:report['checks'].append(entry);report['events'].extend(events);save(run/'browser.json',report);ctx.close()
  def remount(p,playing):
   if not playing:p.locator('[data-action=auto]').click()
   before=read(p);p.evaluate('()=>{window.__saved=__aboutRefreshPreview.view.captureState();window.__oldBrowser=__aboutRefreshPreview.view.toolsElement;window.__oldRoot=__aboutRefreshPreview.view.root;__aboutRefreshPreview.remount(__saved)}');p.wait_for_timeout(120)
   assert p.evaluate('__aboutRefreshPreview.view.captureState().tools.track.enabled')==playing
   p.evaluate(PRESENT);p.wait_for_timeout(120);initial=read(p)
   assert abs(float(initial['state']['trackOffset'])-float(before['state']['trackOffset']))<1
   assert initial['old']['state']['trackState']=='disposed' and initial['old']['state']['trackFramePending']=='false' and not initial['old']['connected']
   p.wait_for_timeout(1200);after=read(p)
   if playing:assert float(after['state']['trackOffset'])>float(initial['state']['trackOffset'])+5
   else:assert after['state']['trackOffset']==initial['state']['trackOffset'] and after['state']['trackFramePending']=='false'
   assert after['old']['state']['trackOffset']==initial['old']['state']['trackOffset']
   assert len(after['cards'])==len({c['id'] for c in after['cards']})==22
   return {'before':before,'initial':initial,'after':after}
  def all_snapshot(p):
   p.locator('[data-action=auto]').click();before=read(p);p.locator('[data-action=all]').click();p.wait_for_timeout(80);assert p.evaluate('__aboutRefreshPreview.view.captureState().tools.mode')=='all'
   p.evaluate('()=>{window.__saved=__aboutRefreshPreview.view.captureState();window.__oldBrowser=__aboutRefreshPreview.view.toolsElement;window.__oldRoot=__aboutRefreshPreview.view.root;__aboutRefreshPreview.remount(__saved)}');p.wait_for_timeout(100);p.evaluate(PRESENT)
   p.locator('.ar-all-tools [data-action=return]').first.click();p.wait_for_timeout(250);p.evaluate(PRESENT);after=read(p)
   assert after['state']['trackMode']=='program' and after['state']['trackEnabled']=='false';assert abs(float(before['state']['trackOffset'])-float(after['state']['trackOffset']))<.1
   return {'before':before,'after':after}
  def dispose(p):
   p.evaluate('window.__oldBrowser=__aboutRefreshPreview.view.toolsElement;window.__oldRoot=__aboutRefreshPreview.view.root');before=read(p);p.evaluate('__aboutRefreshPreview.view.dispose()');p.wait_for_timeout(200);a=read(p);p.wait_for_timeout(450);b=read(p)
   assert not b['old']['connected'] and b['old']['state']['trackState']=='disposed' and b['old']['state']['trackFramePending']=='false';assert a['old']['state']['trackOffset']==b['old']['state']['trackOffset'];return {'before':before,'after':b}
  def suspend(p):
   p.evaluate('()=>__aboutRefreshPreview.view.presentToolsTrack({active:false,allowed:true,automatic:false,top:60,bottom:innerHeight-40})');a=read(p);p.wait_for_timeout(450);b=read(p);assert a['state']['trackOffset']==b['state']['trackOffset'] and b['state']['trackFramePending']=='false'
   p.evaluate(PRESENT);p.wait_for_timeout(1200);c=read(p);assert float(c['state']['trackOffset'])>float(b['state']['trackOffset'])+5;return {'suspended':b,'resumed':c}
  case('paused-snapshot-remount',lambda p:remount(p,False));case('playing-snapshot-remount',lambda p:remount(p,True));case('all-tools-snapshot-remount',all_snapshot);case('dispose-stops-old-clock',dispose);case('suspend-no-catchup',suspend)
  browser.close();report['browserClosed']=True;report['complete']=True
finally:server.shutdown();server.server_close();report['serverClosed']=True;save(run/'browser.json',report)
print(json.dumps({'checks':len(report['checks']),'passed':len(report['checks'])-len(failures),'failures':failures},ensure_ascii=False));raise SystemExit(1 if failures else 0)
