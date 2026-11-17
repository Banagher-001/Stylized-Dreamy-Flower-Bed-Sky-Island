from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from threading import Thread
import json,os,argparse,traceback,hashlib,shutil,math
from playwright.sync_api import sync_playwright
from PIL import Image,ImageChops
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('run');ap.add_argument('--main',action='store_true');ap.add_argument('--only',nargs='*');args=ap.parse_args();run=OUT/args.run;run.mkdir(exist_ok=False)
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
shutil.copy2(__file__,run/'test.py.txt')
sources=[p for p in (ROOT/'src/tour').rglob('*') if p.is_file()]+list((ROOT/'src/assets/tool-marks').glob('*.svg'))+[ROOT/'dist/index.html']+list((ROOT/'dist/assets').glob('startTourPrototype*'))
save(run/'source-manifest.json',[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sources])
report={'startedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'checks':[],'events':[],'complete':False,'clockModified':False,'physicalDevice':False,'main':args.main};failures=[];server=None
if args.main:
 s=json.loads((OUT/'services-started.json').read_text());os.environ.update(s['browserEnvironment']);origin=s['origin'];os.environ['PLAYWRIGHT_BROWSERS_PATH']='/workspace/.cache/ms-playwright'
else:
 payload=(OUT/'component-preview.html').read_bytes();save(run/'build.json',json.loads((OUT/'component-build.json').read_text()))
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*args):pass
  def do_GET(self):
   self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(payload)
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}'
PRESENT='''active=>{const v=__aboutRefreshPreview.view;v.presentToolsEntrance({active:active!==false,enabled:false,revealed:true});v.presentToolsTrack({active:active!==false,allowed:innerWidth>=1180,automatic:false,top:70,bottom:innerHeight-40})}'''
READ=r'''()=>{const root=document.querySelector('.ar-tools-browser'),rail=root.querySelector('.ar-tool-rail'),active=root.querySelector('[data-reading="true"]');const box=e=>e.getBoundingClientRect().toJSON();return{now:performance.now(),y:scrollY,mode:document.querySelector('main')?.dataset.readingMode,d:{...root.dataset},rail:box(rail),railX:rail.scrollLeft,controls:box(root.querySelector('.ar-tool-controls')),active:active?{id:active.dataset.toolId,instance:active.dataset.cardInstance,pose:active.dataset.pose,reading:active.dataset.readingPose,front:box(active.querySelector('.ar-card-front')),faces:[...active.querySelectorAll('[data-card-face]')].map(box),shadow:box(active.querySelector('.ar-card-shadow')),shadowBlur:parseFloat(getComputedStyle(active.querySelector('.ar-card-shadow')).filter.match(/[\d.]+/)[0])}:null,cards:[...rail.querySelectorAll('.ar-tool-card')].map(e=>({id:e.dataset.toolId,instance:e.dataset.cardInstance,pose:e.dataset.pose,reading:e.dataset.readingPose,expanded:e.dataset.expanded,front:box(e.querySelector('.ar-card-front'))})),focus:{action:document.activeElement?.dataset.action,tool:document.activeElement?.dataset.toolId},duplicates:[...document.querySelectorAll('[id]')].filter((e,i,a)=>a.findIndex(x=>x.id===e.id)!==i).map(e=>e.id),overflow:document.documentElement.scrollWidth-innerWidth}}'''
try:
 with sync_playwright() as play:
  opts=['--no-sandbox']+(['--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist'] if args.main else [])
  browser=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=opts);report['version']=browser.version
  def read(p):return p.evaluate(READ)
  def go(p,h=3.34):
   if p.locator('main').get_attribute('data-reading-mode')=='stable':p.locator('.tour-reading-flow [data-flow-anchor=A3]').scroll_into_view_if_needed();p.wait_for_timeout(400)
   else:
    p.evaluate('h=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})',h);p.wait_for_function('h=>Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-h)<.001&&document.querySelector("#tour-host").dataset.cameraState==="settled"',arg=h,timeout=25000)
  def setup(p,program=True,paused=False):
   p.goto(origin+('/?waterTime=2' if args.main else '/'),wait_until='domcontentloaded')
   if args.main:
    p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=90000);go(p);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceReady==="true"',timeout=15000)
    if program:
     if p.locator('main').get_attribute('data-reading-mode')=='stable':p.locator('[data-action=auto]').click()
     p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.trackState==="running"',timeout=15000)
   else:
    p.wait_for_function('!!window.__aboutRefreshPreview');p.locator('[data-preview-station=A3]').click();p.wait_for_timeout(120);p.evaluate(PRESENT)
    if program:p.locator('[data-action=auto]').click()
   if program:p.wait_for_timeout(1150)
   if paused and p.locator('[data-action=auto]').get_attribute('aria-pressed')=='true':p.locator('[data-action=auto]').click()
  def case(name,fn,size=None,paused=False,program=True,reduced=False,video=False):
   if args.only and name not in args.only:return
   size=size or ((1440,900) if args.main else (1440,1100));options={'viewport':{'width':size[0],'height':size[1]},'reduced_motion':'reduce' if reduced else 'no-preference'}
   if video:options.update(record_video_dir=str(run/'video'),record_video_size=options['viewport'])
   ctx=browser.new_context(**options);p=ctx.new_page();p.set_default_timeout(12000);errors=[];p.on('pageerror',lambda e:errors.append(str(e)));entry={'id':name,'viewport':list(size),'status':'失败'}
   try:
    setup(p,program,paused);data=fn(p);last=read(p);assert not errors,errors;assert not last['duplicates'] and last['overflow']<=1,last
    save(run/(name+'-data.json'),data);p.screenshot(path=str(run/(name+'.png')));entry.update(status='通过',data=name+'-data.json')
   except Exception as e:
    failures.append(name);entry.update(error=str(e),traceback=traceback.format_exc())
    try:save(run/(name+'-failure.json'),read(p));p.screenshot(path=str(run/(name+'-failure.png')))
    except Exception:pass
   finally:
    report['checks'].append(entry);report['events'].extend(errors);save(run/'browser.json',report);ctx.close()
    if video:entry['video']=str(Path(p.video.path()).relative_to(run));save(run/'browser.json',report)
  def point(p,id,fx=.5,fy=.45):
   b=p.locator(f'.ar-tool-card[data-tool-id="{id}"] .ar-card-front').bounding_box();r=p.locator('.ar-tool-rail').bounding_box();x=max(r['x']+6,min(r['x']+r['width']-6,b['x']+b['width']*fx));y=b['y']+b['height']*fy;return {'x':x,'y':y}
  def hover(p,id='comfyui'):
   pt=point(p,id);p.mouse.move(**pt);p.wait_for_function('id=>{const r=document.querySelector(".ar-tools-browser");return r.dataset.hoverId===id&&r.dataset.hoverState==="reading"}',arg=id,timeout=4500);return read(p)
  def leave(p):p.mouse.move(10,80);p.wait_for_timeout(1600)
  def bounds(m):
   a=m['active'];assert a,m['d'];r=m['rail'];scale=float(a['reading'].split(',')[4]);margin=math.ceil(3*a['shadowBlur']*scale*1.05);shadow=a['shadow'];faces=a['faces'];b={'left':min([f['left'] for f in faces]+[shadow['left']-margin]),'right':max([f['right'] for f in faces]+[shadow['right']+margin]),'top':min([f['top'] for f in faces]+[shadow['top']-margin]),'bottom':max([f['bottom'] for f in faces]+[shadow['bottom']+margin])}
   assert b['left']>=r['left']+7 and b['right']<=r['right']-7 and b['top']>=r['top']+7 and b['bottom']<=r['bottom']-7,(b,r,a)
   assert b['bottom']<m['controls']['top']-6;return b
  def hold_resume(p):
   a=read(p);b=hover(p);bounds(b);p.wait_for_timeout(450);c=read(p);assert b['d']['trackOffset']==c['d']['trackOffset'] and c['d']['trackEnabled']=='true' and c['d']['trackHeld']=='true' and c['d']['trackFramePending']=='false' and c['d']['hoverFramePending']=='false'
   ratio=b['active']['front']['width']/next(x['front']['width'] for x in a['cards'] if x['id']=='comfyui');assert 1.09<ratio<1.18,ratio;leave(p);d=read(p);assert d['d']['hoverState']=='idle' and d['d']['trackEnabled']=='true' and abs(float(d['d']['trackSpeed'])-28)<.1
   assert [x['instance'] for x in a['cards']]==[x['instance'] for x in d['cards']];return {'ratio':ratio,'before':a,'hover':b,'held':c,'resumed':d}
  def paused(p):
   a=hover(p);leave(p);b=read(p);assert b['d']['trackEnabled']=='false' and b['d']['trackFramePending']=='false' and b['d']['trackOffset']==a['d']['trackOffset'];return {'hover':a,'after':b}
  def tilt(p):
   a=hover(p);b=a['active']['front'];positions=[(.1,.1),(.9,.1),(.9,.9),(.1,.9),(.5,.1),(.9,.5),(.5,.9),(.1,.5),(.5,.5)];states=[]
   for x,y in positions:
    p.mouse.move(b['x']+b['width']*x,b['y']+b['height']*y);p.wait_for_timeout(550);m=read(p);bounds(m);assert m['active']['id']=='comfyui';states.append(m)
   angles=[list(map(float,m['active']['pose'].split(','))) for m in states];assert max(a[0] for a in angles)>2.5 and min(a[0] for a in angles)<-2.5 and max(a[1] for a in angles)>4 and min(a[1] for a in angles)<-4,angles
   p.wait_for_timeout(250);stable=read(p);assert stable['d']['hoverFramePending']=='false';return {'states':states,'angles':angles,'stable':stable}
  def edge(p,last=False):
   if last:p.locator('[data-action=previous]').click();id='vibe-coding'
   else:
    r=p.locator('.ar-tool-rail').bounding_box();p.mouse.move(r['x']+r['width']/2,r['y']+r['height']/2);p.mouse.wheel(0,120);p.wait_for_timeout(1400);id='midjourney'
   before=read(p);m=hover(p,id);b=bounds(m);assert m['d']['trackEnabled']=='false';assert m['d']['trackOffset']==read(p)['d']['trackOffset'];return {'before':before,'after':m,'bounds':b}
  def occlusion(p):
   r=p.locator('.ar-tool-rail').bounding_box();p.mouse.move(r['x']+r['width']/2,r['y']+r['height']/2);p.mouse.wheel(0,400);p.wait_for_timeout(1400);m=hover(p,'midjourney');bounds(m)
   records=[]
   for fx,fy in [(.85,.2),(.85,.8),(.15,.2),(.15,.8)]:
    b=m['active']['front'];p.mouse.move(b['x']+b['width']*fx,b['y']+b['height']*fy);p.wait_for_timeout(600);state=read(p);bounds(state)
    hits=p.evaluate('''()=>{const a=document.querySelector('[data-reading="true"]'),b=a.querySelector('.ar-card-front').getBoundingClientRect();return [.15,.5,.85,.92].flatMap(fx=>[.2,.5,.8].map(fy=>{const x=b.x+b.width*fx,y=b.y+b.height*fy;return{x,y,expected:a.dataset.toolId,actual:document.elementFromPoint(x,y)?.closest('.ar-tool-card')?.dataset.toolId}}))}''')
    records.append({'state':state,'hits':hits});save(run/'edge-interior-hit-grid.json',records);assert all(h['expected']==h['actual'] for h in hits),hits
   return {'reading':m,'records':records}
  def click(p,last=False,entering=False):
   if last:p.locator('[data-action=previous]').click();id='vibe-coding'
   else:id='comfyui'
   if entering:p.mouse.move(**point(p,id));p.wait_for_timeout(180)
   else:hover(p,id)
   loc=p.locator(f'.ar-tool-card[data-tool-id={id}] button');b=loc.bounding_box();p.mouse.move(b['x']+b['width']/2,b['y']+b['height']/2);p.mouse.click(b['x']+b['width']/2,b['y']+b['height']/2);p.wait_for_timeout(400);m=read(p);assert next(c for c in m['cards'] if c['id']==id)['expanded']=='true';assert m['focus']['tool']==id and m['d']['hoverState']=='idle' and m['d']['trackHeld']=='false';return m
  def press(p):
   a=hover(p);b=a['active']['front'];p.mouse.move(b['x']+b['width']*.5,b['y']+b['height']*.5);p.wait_for_timeout(400);p.mouse.down();first=read(p);p.wait_for_timeout(250);second=read(p);assert first['d']['hoverState']=='pressed' and second['active']['reading']==first['active']['reading'] and second['d']['hoverFramePending']=='false';p.mouse.up();p.wait_for_timeout(450);after=read(p);assert after['d']['hoverState']=='idle';return {'pressed':first,'still':second,'released':after}
  def stationary(p):
   m=read(p);first=next(c for c in m['cards'] if c['id']=='midjourney')['front'];second=next(c for c in m['cards'] if c['id']=='comfyui')['front'];p.mouse.move((first['right']+second['left'])/2,(first['top']+first['bottom'])/2);p.wait_for_timeout(3200);a=read(p);assert a['d']['hoverState']=='idle' and float(a['d']['trackDistance'])>float(m['d']['trackDistance'])+65;return {'before':m,'after':a}
  def sweep(p):
   for id in ['midjourney','comfyui','kling']:p.mouse.move(**point(p,id));p.wait_for_timeout(40)
   p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.hoverState==="reading"');m=read(p);assert m['active']['id']=='kling';assert p.locator('[data-reading=true]').count()==1;return m
  def wheel(p,horizontal=False):
   a=hover(p);p.mouse.wheel(100 if horizontal else 0,0 if horizontal else 120);p.wait_for_timeout(130);b=read(p);assert b['d']['hoverState']=='idle' and b['d']['trackHeld']=='false'
   if horizontal:assert b['d']['trackMode']=='native' and b['railX']>50
   else:assert b['d']['trackEnabled']=='true' and float(b['d']['trackDistance'])>float(a['d']['trackDistance'])+3 and float(b['d']['trackSpeed'])>60 and b['y']==a['y']
   return {'hover':a,'after':b}
  def scrolling(p):
   r=p.locator('.ar-tool-rail').bounding_box();p.mouse.move(r['x']+r['width']/2,r['y']+r['height']/2)
   for _ in range(7):p.mouse.wheel(0,160);p.wait_for_timeout(25)
   p.mouse.move(r['x']+r['width']/2+10,r['y']+r['height']/2);p.wait_for_timeout(1400);a=read(p);assert a['d']['hoverState']=='idle';id=next(c['id'] for c in a['cards'] if c['front']['left']>a['rail']['left']+20 and c['front']['right']<a['rail']['right']-20);b=hover(p,id);return {'afterScroll':a,'newIntent':b}
  def keyboard(p,escape=False):
   p.locator('.ar-tool-rail').focus();p.keyboard.press('Tab');p.wait_for_timeout(700);a=read(p);assert a['active'] and a['d']['hoverSource']=='keyboard' and a['active']['pose']=='0,0',a
   assert a['focus']['tool']==a['active']['id'];p.keyboard.press('Escape' if escape else 'Enter');p.wait_for_timeout(350);b=read(p);assert b['d']['hoverState']=='idle' and b['focus']['tool']==a['focus']['tool']
   if not escape:assert next(c for c in b['cards'] if c['id']==a['focus']['tool'])['expanded']=='true'
   return {'focused':a,'afterKey':b}
  def mixed_focus(p):
   a=hover(p,'midjourney');p.locator('.ar-tool-rail').focus();p.keyboard.press('Tab');p.wait_for_timeout(700);b=read(p);assert b['active'] and b['d']['hoverSource']=='keyboard' and b['active']['pose']=='0,0' and b['focus']['tool']=='midjourney';return {'pointer':a,'keyboard':b}
  def category(p):
   a=hover(p);p.locator('[data-category=G2]').click();p.wait_for_timeout(250);b=read(p);assert b['d']['hoverState']=='idle' and not b['active'] and b['d']['trackHeld']=='false' and len(b['cards'])==2;return {'before':a,'after':b}
  def overview(p):
   a=hover(p);p.locator('[data-action=all]').click();p.wait_for_timeout(180);b=read(p);assert b['d']['hoverState']=='idle' and p.locator('.ar-catalog .ar-tool-card').count()==22
   p.locator('.ar-all-tools [data-action=return]').first.click();p.wait_for_timeout(500);c=read(p);assert c['d']['hoverState']=='idle' and c['d']['trackEnabled']=='false';return {'hover':a,'catalog':b,'return':c}
  def remount(p):
   a=hover(p);p.evaluate('()=>{window.__snapshot=__aboutRefreshPreview.view.captureState();window.__old=__aboutRefreshPreview.view.toolsElement;__aboutRefreshPreview.remount(__snapshot)}');p.wait_for_timeout(120);p.evaluate(PRESENT);p.wait_for_timeout(1300);b=read(p);old=p.evaluate('({...__old.dataset})');assert b['d']['hoverState']=='idle' and b['d']['trackEnabled']=='true' and not b['active'];assert old['hoverState']=='disposed' and old['hoverFramePending']=='false' and old['trackState']=='disposed';return {'before':a,'new':b,'old':old}
  def resize(p):
   a=hover(p);p.set_viewport_size({'width':1280,'height':1100});p.wait_for_timeout(650);b=read(p);assert not b['active'] and b['d']['hoverState']=='idle' and b['d']['hoverFramePending']=='false';return {'before':a,'after':b}
  def hidden(p):
   a=hover(p);p.evaluate('Object.defineProperty(document,"hidden",{configurable:true,get:()=>true});document.dispatchEvent(new Event("visibilitychange"))');p.wait_for_timeout(100);p.evaluate('delete document.hidden;document.dispatchEvent(new Event("visibilitychange"))');p.wait_for_timeout(700);b=read(p);assert b['d']['hoverState']=='idle' and not b['active'] and b['d']['trackEnabled']=='false' and b['d']['hoverFramePending']=='false';return {'simulatedHidden':True,'before':a,'after':b}
  def reduced_change(p):
   a=hover(p);p.emulate_media(reduced_motion='reduce');p.wait_for_timeout(650);b=read(p);assert b['d']['hoverState']=='idle' and not b['active'] and b['d']['hoverFramePending']=='false';return {'before':a,'after':b}
  def native(p):
   a=hover(p);bounds(a);assert a['d']['trackMode']=='native' and a['d']['trackEnabled']=='false';leave(p);b=read(p);assert b['d']['trackMode']=='native' and b['d']['trackEnabled']=='false';return {'hover':a,'after':b}
  def dispose(p):
   hover(p);p.evaluate('()=>{window.__old=__aboutRefreshPreview.view.toolsElement;__aboutRefreshPreview.view.dispose()}');p.wait_for_timeout(400);a=p.evaluate('({connected:__old.isConnected,d:{...__old.dataset}})');assert not a['connected'] and a['d']['hoverState']=='disposed' and a['d']['hoverFramePending']=='false' and a['d']['trackFramePending']=='false';p.evaluate('document.querySelector("#about-refresh-preview").append(__old)');return a
  def shadow(p):
   records=[]
   for mode in ['base','tilt-left','tilt-right']:
    if mode!='base':
     a=hover(p) if mode=='tilt-left' else read(p);b=a['active']['front'];p.mouse.move(b['x']+b['width']*(.15 if mode=='tilt-left' else .85),b['y']+b['height']*.2);p.wait_for_timeout(600)
    card=p.locator('.ar-tool-card[data-tool-id=comfyui]' if mode!='base' else '.ar-tool-card[data-tool-id=midjourney]');b=card.locator('.ar-card-front').bounding_box();region=(math.ceil(b['x']+22),math.ceil(b['y']+22),math.floor(b['x']+b['width']-22),math.floor(b['y']+b['height']-22));visible=run/('shadow-'+mode+'-visible.png');hidden=run/('shadow-'+mode+'-hidden.png');p.screenshot(path=str(visible));card.locator('.ar-card-shadow').evaluate('(e)=>e.style.visibility="hidden"');p.screenshot(path=str(hidden));card.locator('.ar-card-shadow').evaluate('(e)=>e.style.removeProperty("visibility")');diff=ImageChops.difference(Image.open(visible).convert('RGB').crop(region),Image.open(hidden).convert('RGB').crop(region));bbox=diff.getbbox();assert bbox is None,(mode,bbox);records.append({'pose':mode,'interiorRegion':region,'differentPixels':0})
   return records
  def guide(p):
   p.locator('#tour-guide').click();p.wait_for_function('document.querySelector("#tour-host").dataset.guidePhase==="reading"');a=hover(p);assert p.locator('#tour-guide').get_attribute('aria-pressed')=='false' and a['d']['trackEnabled']=='true';leave(p);b=read(p);assert p.locator('#tour-guide').get_attribute('aria-pressed')=='false' and b['d']['trackEnabled']=='true';return {'hover':a,'after':b}
  def outside(p):
   a=hover(p);p.mouse.move(50,500);p.mouse.wheel(0,160);p.wait_for_timeout(500);b=read(p);assert b['y']>a['y']+100 and not b['active'] and b['d']['hoverFramePending']=='false';return {'hover':a,'outsidePage':b}
  def film(p):
   hover(p);p.locator('[data-action=continue]').click();p.wait_for_function('document.querySelector("#tour-host").dataset.filmStation==="B1"&&document.querySelector("#tour-host").dataset.cameraState==="settled"');a=read(p);assert a['d']['hoverState']=='idle' and a['d']['trackFramePending']=='false';go(p);p.wait_for_timeout(700);b=read(p);assert not b['active'] and b['d']['hoverState']=='idle';return {'film':a,'returned':b}
  def fallback(p):
   p.mouse.move(**point(p,'midjourney'));p.wait_for_timeout(500);a=read(p);assert a['d']['hoverState']=='idle' and not a['active'];return a
  def video(p):
   a=hover(p);b=a['active']['front'];states=[a]
   for fx,fy in [(.15,.2),(.85,.2),(.85,.8),(.15,.8),(.5,.5)]:
    p.mouse.move(b['x']+b['width']*fx,b['y']+b['height']*fy);p.wait_for_timeout(500);m=read(p);bounds(m);states.append(m)
   p.mouse.wheel(0,120);p.wait_for_timeout(1100);leave(p);return {'states':states,'after':read(p)}
  case('hover-holds-and-resumes-choice',hold_resume);case('paused-choice-survives-hover',paused,paused=True);case('four-corners-and-edges',tilt)
  case('partial-first-card-safe-reading',edge,paused=True);case('last-card-safe-reading',lambda p:edge(p,True),paused=True);case('edge-card-front-occlusion',occlusion,paused=True)
  case('hover-first-native-detail-click',click);case('hover-last-native-detail-click',lambda p:click(p,True),paused=True);case('click-during-lift',lambda p:click(p,False,True))
  case('pointer-press-freezes-pose',press);case('stationary-pointer-does-not-intercept',stationary);case('fast-sweep-one-active-card',sweep);case('first-wheel-interrupts-hover',wheel);case('horizontal-native-handoff',lambda p:wheel(p,True));case('scrolling-defers-hover',scrolling)
  case('pointer-to-keyboard-reading',mixed_focus);case('keyboard-reading-enter',keyboard);case('keyboard-escape-keeps-focus',lambda p:keyboard(p,True));case('category-clears-reading',category);case('catalog-clears-reading',overview);case('resize-clears-reading',resize);case('hidden-clears-reading',hidden);case('reduce-clears-reading',reduced_change)
  if not args.main:
   case('snapshot-clears-ephemeral-reading',remount);case('dispose-clears-reading-clock',dispose);case('native-hover-does-not-enable-track',native,program=False);case('shadow-behind-front-pixel-check',shadow,paused=True)
  else:
   case('hover-stops-main-guide',guide);case('outside-row-scrolls-page',outside);case('continue-film-and-return',film);case('actual-hover-demonstration',video,video=True)
   case('phone-stable-reading',fallback,size=(390,844),program=False);case('reduced-stable-reading',fallback,reduced=True,program=False)
  report['complete']=not failures
  browser.close();report['browserClosed']=True
finally:
 if server:server.shutdown();server.server_close();report['serverClosed']=True
 report['finishedAtShanghai']=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat();save(run/'browser.json',report)
print(json.dumps({'checks':len(report['checks']),'passed':len(report['checks'])-len(failures),'failures':failures},ensure_ascii=False));raise SystemExit(1 if failures else 0)
