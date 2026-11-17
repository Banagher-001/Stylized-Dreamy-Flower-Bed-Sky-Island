"""Real-browser checks of the standalone bundle; never starts or changes the main site."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from threading import Thread
import argparse,hashlib,json,shutil,traceback
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--suite',choices=['smoke','full'],default='full');args=parser.parse_args()
run=OUT/args.run;run.mkdir(exist_ok=False)
html=ROOT/'docs/about-refresh/evidence/step-5/component-preview.html';payload=html.read_bytes();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
now=lambda:datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
report={'startedAtShanghai':now(),'suite':args.suite,'htmlSHA256':sha(html),'checks':[],'events':[],'externalAttempts':[],'requests':[],'complete':False}
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
shutil.copy2(OUT/'component-build.json',run/'build.json');shutil.copy2(__file__,run/'verify-browser.py.txt')
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*a): pass
 def do_GET(self):
  report['requests'].append(self.path)
  if self.path=='/favicon.ico':self.send_response(204);self.end_headers();return
  if self.path not in ['/','/preview.html']:self.send_error(404);return
  self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(payload)
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=Thread(target=server.serve_forever,daemon=True);thread.start();origin=f'http://127.0.0.1:{server.server_port}'
report['server']={'origin':origin,'servesOnlyStandalonePreview':True}
MEASURE=r'''() => {
 const api=window.__aboutRefreshPreview,root=api.view.root,active=root.querySelector('.ar-screen:not([hidden])');
 const box=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom}};
 const shown=e=>!!e.getClientRects().length;
 const rail=root.querySelector('.ar-tool-rail');const rb=box(rail);
 const cards=[...root.querySelectorAll('.ar-tool-card')].filter(shown).map(e=>({id:e.dataset.toolId,expanded:e.dataset.expanded==='true',rect:box(e),texts:[...e.querySelectorAll('h3,p,li,button')].filter(shown).map(t=>({text:t.textContent,rect:box(t),font:parseFloat(getComputedStyle(t).fontSize),overflow:t.scrollHeight-t.clientHeight}))}));
 return {viewport:[innerWidth,innerHeight],documentWidth:document.documentElement.scrollWidth,documentHeight:document.documentElement.scrollHeight,root:box(root),layout:root.dataset.layout,station:root.dataset.station,activeScreens:[...root.querySelectorAll('.ar-screen')].filter(shown).map(e=>e.dataset.aboutStation),inactive:[...root.querySelectorAll('.ar-screen[hidden]')].map(e=>({id:e.dataset.aboutStation,inert:e.inert,aria:e.getAttribute('aria-hidden')})),rootFont:parseFloat(getComputedStyle(document.documentElement).fontSize),reduced:matchMedia('(prefers-reduced-motion: reduce)').matches,rail:rb,railScroll:rail.scrollLeft,cards,controls:[...document.querySelectorAll('button,select,summary')].filter(shown).map(e=>({text:e.textContent?.trim(),rect:box(e)})),snapshot:api.view.captureState(),catalogCount:root.querySelectorAll('.ar-catalog .ar-tool-card').length,focus:{tag:document.activeElement?.tagName,action:document.activeElement?.dataset.action},defaultPrevented:document.documentElement.dataset.wheelPrevented||'false'};
}'''
expected=json.loads((ROOT/'docs/about-refresh/evidence/step-3/content.json').read_text())
viewports=[('large',1920,1080),('desktop',1440,900),('laptop',1366,768),('short-laptop',1280,720),('tablet-landscape',1024,768),('tablet-portrait',820,1180),('phone',390,844),('narrow',320,740),('short-landscape',844,390)]
failures=[];browser=None
try:
 with sync_playwright() as play:
  browser=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  report['version']=browser.version
  def settle(p):
   p.wait_for_timeout(110)
   p.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
  def goto_station(p,station):
   p.locator(f'[data-preview-station={station}]').click();settle(p)
  def category(p,value):
   if p.locator(f'[data-category="{value}"]').is_visible():p.locator(f'[data-category="{value}"]').click()
   else:p.locator('.ar-category-select select').select_option(value)
   settle(p)
  def snap(p):return p.evaluate('window.__aboutRefreshPreview.view.captureState()')
  def open_all(p):p.locator('[data-action=all]').click();settle(p)
  def back(p):p.locator('.ar-all-tools [data-action=return]').first.click();settle(p)
  def assertions(m,desktop_peek=False):
   assert m['documentWidth']<=m['viewport'][0]+1,('page horizontal overflow',m['documentWidth'],m['viewport'])
   assert m['activeScreens']==[m['station']],m['activeScreens']
   assert all(i['inert'] and i['aria']=='true' for i in m['inactive'])
   assert all(c['rect']['height']>=43.5 for c in m['controls']),[(c['text'],c['rect']['height']) for c in m['controls'] if c['rect']['height']<43.5]
   if m['layout']=='immersive':assert m['documentHeight']<=m['viewport'][1]+1,('immersive overflow',m['documentHeight'])
   for c in m['cards']:
    for t in c['texts']:
     assert t['rect']['x']>=c['rect']['x']-1 and t['rect']['right']<=c['rect']['right']+1,(c['id'],'horizontal text overflow',t)
     assert t['rect']['y']>=c['rect']['y']-1 and t['rect']['bottom']<=c['rect']['bottom']+1,(c['id'],'vertical text overflow',t)
     assert t['overflow']<=2,(c['id'],'text box clipped',t)
     if t['text']==next((e['use'] for e in expected['cards'] if e['id']==c['id']),None):assert t['font']>=16
   if m['station']=='A3' and m['snapshot']['tools']['mode']=='cards':
    rb=m['rail'];fracs=[max(0,min(c['rect']['right'],rb['right'])-max(c['rect']['x'],rb['x']))/c['rect']['width'] for c in m['cards']]
    assert sum(f>.995 for f in fracs)>=1,('no full card',fracs)
    if desktop_peek:
     assert sum(f>.995 for f in fracs)==3,fracs
     assert .05<fracs[3]<.9,fracs[:4]
   assert len({c['id'] for c in m['cards']})==len(m['cards'])
  def case(name,station='A3',size=(1440,900),action=None,peek=False,touch=False,reduced=False):
   context=browser.new_context(viewport={'width':size[0],'height':size[1]},device_scale_factor=1,has_touch=touch,is_mobile=touch,reduced_motion='reduce' if reduced else 'no-preference')
   p=context.new_page();start_events=len(report['events']);start_external=len(report['externalAttempts'])
   p.on('pageerror',lambda e:report['events'].append({'case':name,'type':'pageerror','message':str(e)}))
   p.on('console',lambda e:report['events'].append({'case':name,'type':'console.error','message':e.text}) if e.type=='error' else None)
   def route(r):
    if r.request.url.startswith(origin) or r.request.url.startswith('data:'):r.continue_()
    else:report['externalAttempts'].append({'case':name,'url':r.request.url});r.abort()
   p.route('**/*',route)
   entry={'id':name,'station':station,'viewport':list(size),'status':'未完成'}
   try:
    p.goto(origin+'/preview.html',wait_until='load');p.wait_for_function('!!window.__aboutRefreshPreview');settle(p);goto_station(p,station)
    assert p.evaluate('window.__aboutRefreshPreview.content')==expected
    assert p.evaluate('window.__aboutRefreshPreview.initialEntryIds')==['midjourney','comfyui','kling','blender']
    if action:action(p)
    settle(p);m=p.evaluate(MEASURE);save(run/(name+'-measurement.json'),m)
    assertions(m,peek)
    assert len(report['events'])==start_events,report['events'][start_events:]
    assert len(report['externalAttempts'])==start_external
    p.screenshot(path=str(run/(name+'.png')),full_page=station!='A3' or m['snapshot']['tools']['mode']!='all')
    entry.update(status='通过',layout=m['layout'],measurement=name+'-measurement.json',screenshot=name+'.png')
   except Exception as error:
    entry.update(status='失败',error=str(error),traceback=traceback.format_exc());failures.append(name)
    try:
     save(run/(name+'-measurement.json'),p.evaluate(MEASURE));p.screenshot(path=str(run/(name+'-failure.png')),full_page=False)
    except Exception:pass
   finally:report['checks'].append(entry);context.close();save(run/'browser.json',report)
  def expanded(which):
   def action(p):
    p.locator(f'[data-about-details={which}] summary').click();settle(p)
    assert p.locator(f'[data-about-details={which}]').evaluate('(e)=>e.open')
   return action
  def native_keys(p):
   summary=p.locator('[data-about-details=identity] summary');summary.focus();p.keyboard.press('Enter');settle(p)
   assert p.locator('[data-about-details=identity]').evaluate('(e)=>e.open')
   p.keyboard.press('Space');settle(p);assert not p.locator('[data-about-details=identity]').evaluate('(e)=>e.open')
   goto_station(p,'A3');toggle=p.locator('[data-tool-id=midjourney] button');toggle.focus();p.keyboard.press('Enter');settle(p)
   assert toggle.get_attribute('aria-expanded')=='true';assert toggle.evaluate('(e)=>e===document.activeElement')
   p.keyboard.press('Space');settle(p);assert toggle.get_attribute('aria-expanded')=='false'
  def orders(p):
   for cat in expected['categories']:
    category(p,cat['id']);assert p.locator('.ar-tool-slot').evaluate_all('(els)=>els.map(e=>e.dataset.cardId)')==cat['cardIds']
   category(p,'all');assert p.locator('.ar-tool-slot').evaluate_all('(els)=>els.map(e=>e.dataset.cardId)')==[c['id'] for c in expected['cards']]
  def catalog_return(p,cat=None,resize=False):
   if cat:category(p,cat)
   p.locator('[data-action=next]').click();p.locator('[data-action=next]').click();settle(p)
   active=snap(p)['tools']['cards']['activeId'];p.locator(f'.ar-tool-card[data-tool-id="{active}"] button').click();settle(p)
   before=snap(p)['tools']['cards'];open_all(p)
   assert p.locator('.ar-catalog .ar-tool-card').count()==22
   assert p.locator('.ar-catalog .ar-card-detail:visible').count()==22
   expected_ids=[id for c in expected['categories'] for id in c['cardIds']]
   assert p.locator('.ar-catalog .ar-tool-card').evaluate_all('(els)=>els.map(e=>e.dataset.toolId)')==expected_ids
   if resize:p.set_viewport_size({'width':390,'height':844});settle(p)
   back(p);after=snap(p)['tools']['cards']
   assert all(after[k]==before[k] for k in ['category','activeId','expandedId']),(before,after)
   if not resize:assert abs(after['position']['scrollLeft']-before['position']['scrollLeft'])<1,(before,after)
   else:assert after['position']['anchorId']==before['position']['anchorId'],(before,after)
   assert p.locator('[data-action=all]').evaluate('(e)=>e===document.activeElement')
   save(run/('return-'+(cat or 'all')+('-resize' if resize else '')+'.json'),{'before':before,'after':after})
  def all_tools(p):open_all(p);assert p.locator('.ar-catalog .ar-tool-card').count()==22
  def detail(p,id='comfyui'):
   p.locator(f'.ar-tool-card[data-tool-id="{id}"] button').click();settle(p)
   assert p.locator(f'.ar-tool-card[data-tool-id="{id}"] .ar-card-detail').is_visible()
  def long_name(p):
   category(p,'G5');detail(p,'substance-painter')
   assert p.locator('.ar-tool-card[data-tool-id=substance-painter] h3').inner_text()=='Substance 3D Painter'
  def large_text(p):p.locator('[data-preview-large]').click();settle(p);assert p.evaluate('parseFloat(getComputedStyle(document.documentElement).fontSize)')==32
  def bounds(p):
   assert p.locator('[data-action=previous]').is_disabled()
   for _ in range(21):p.locator('[data-action=next]').click()
   settle(p);assert p.locator('[data-action=next]').is_disabled();assert snap(p)['tools']['cards']['activeId']=='vibe-coding'
   for _ in range(21):p.locator('[data-action=previous]').click()
   settle(p);assert p.locator('[data-action=previous]').is_disabled();assert snap(p)['tools']['cards']['activeId']=='midjourney'
  def lifecycle(p,all_mode=False):
   detail(p)
   if all_mode:open_all(p)
   before=snap(p)
   for _ in range(3):p.evaluate('window.__aboutRefreshPreview.remount(window.__aboutRefreshPreview.view.captureState())');settle(p)
   assert p.locator('.about-refresh').count()==1
   after=snap(p);assert after['station']==before['station'];assert after['tools']['mode']==before['tools']['mode'];assert after['tools']['cards']['expandedId']==before['tools']['cards']['expandedId']
   if all_mode:back(p)
   old=p.evaluate('window.__aboutRefreshPreview.interactions');p.locator('[data-action=next]').click();settle(p)
   assert p.evaluate('window.__aboutRefreshPreview.interactions')==old+1
   # A detached old control must not invoke its old listener after dispose.
   result=p.evaluate('''() => {const api=window.__aboutRefreshPreview,old=api.view.root.querySelector('[data-action=next]');const state=api.view.captureState();api.remount(state);const before=api.interactions;old.click();return {before,after:api.interactions}}''')
   assert result['before']==result['after']
  def wheel(p):
   p.evaluate("document.addEventListener('wheel',e=>queueMicrotask(()=>document.documentElement.dataset.wheelPrevented=String(e.defaultPrevented)),{once:true})")
   rail=p.locator('.ar-tool-rail');rail.scroll_into_view_if_needed();p.evaluate('scrollTo(0,0)');settle(p)
   box=rail.bounding_box();old=p.evaluate('scrollY');x=rail.evaluate('(e)=>e.scrollLeft')
   p.mouse.move(box['x']+box['width']/2,min(box['y']+60,700));p.mouse.wheel(0,430);p.wait_for_timeout(240)
   assert p.evaluate('scrollY')>old
   assert p.evaluate("document.documentElement.dataset.wheelPrevented")=='false'
   assert rail.evaluate('(e)=>e.scrollLeft')==x
  def touch_swipe(p):
   rail=p.locator('.ar-tool-rail');rail.scroll_into_view_if_needed();settle(p);p.evaluate("window.__arTouchEnded=false;document.querySelector('.ar-tool-rail').addEventListener('scrollend',()=>window.__arTouchEnded=true,{once:true})");box=rail.bounding_box();x=box['x']+box['width']-25;y=min(box['y']+80,700)
   client=p.context.new_cdp_session(p)
   client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
   for step in range(1,9):
    client.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x-step*24,'y':y}]});p.wait_for_timeout(30)
   client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});p.wait_for_function('window.__arTouchEnded===true',timeout=10000)
   assert rail.evaluate('(e)=>e.scrollLeft')>40,'native touch did not move rail'
   client.detach()
  if args.suite=='smoke':
   for station in ['A1','A2','A3']:case('desktop-'+station,station,peek=station=='A3')
   case('expanded-experience','A2',action=expanded('experience'))
   case('phone-A3',size=(390,844))
   case('narrow-A3',size=(320,740))
   case('catalog-return',action=lambda p:catalog_return(p))
   case('catalog-return-G5',action=lambda p:catalog_return(p,'G5'))
   case('large-text-A3',size=(800,600),action=large_text)
  else:
   for name,w,h in viewports:
    for station in ['A1','A2','A3']:case(name+'-'+station,station,size=(w,h),peek=station=='A3' and w>=1440)
   case('identity-expanded','A1',action=expanded('identity'))
   case('experience-expanded','A2',action=expanded('experience'))
   case('phone-experience-expanded','A2',size=(390,844),action=expanded('experience'))
   case('category-orders',action=orders)
   case('catalog-return',action=lambda p:catalog_return(p))
   case('catalog-return-G5',action=lambda p:catalog_return(p,'G5'))
   case('catalog-resize-return',action=lambda p:catalog_return(p,resize=True))
   case('desktop-detail',action=lambda p:detail(p))
   case('edge-detail',action=lambda p:detail(p,'blender'))
   case('long-name',action=long_name)
   case('phone-detail',size=(390,844),action=lambda p:detail(p))
   case('narrow-all-tools',size=(320,740),action=all_tools)
   for station in ['A1','A2','A3']:case('large-text-'+station,station,size=(800,600),action=large_text)
   case('reduced-motion',reduced=True)
   case('native-keys','A1',action=native_keys)
   case('track-boundaries',action=bounds)
   case('native-touch',size=(390,844),action=touch_swipe,touch=True)
   case('native-wheel-passthrough',size=(390,844),action=wheel)
   case('remount-cards',action=lambda p:lifecycle(p))
   case('remount-all',action=lambda p:lifecycle(p,True))
  report['complete']=not failures
  report['finishedAtShanghai']=now()
  browser.close();browser=None
finally:
 server.shutdown();server.server_close();thread.join(timeout=5)
 report['cleanup']={'serverClosed':not thread.is_alive(),'browserClosed':browser is None,'otherServicesStopped':False}
 save(run/'browser.json',report)
 print(json.dumps({'run':args.run,'checks':len(report['checks']),'passed':sum(c['status']=='通过' for c in report['checks']),'failures':failures,'complete':report['complete']},ensure_ascii=False))
if failures:raise SystemExit(1)
