from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from threading import Thread
import json,argparse,traceback,hashlib,shutil,time
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('run');ap.add_argument('--only',nargs='*');args=ap.parse_args();run=OUT/args.run;run.mkdir(exist_ok=False)
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
build=json.loads((OUT/'component-build.json').read_text());payload=(ROOT/build['output']['path']).read_bytes();save(run/'build.json',build);shutil.copy2(__file__,run/'test.py.txt')
report={'startedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'checks':[],'events':[],'complete':False,'clockModified':False,'standaloneActualComponents':True,'physicalDevice':False};failures=[]
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  if self.path not in ['/','/preview.html']:self.send_error(404);return
  self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(payload)
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}'
PRESENT='''(active)=>{__aboutRefreshPreview.view.presentToolsEntrance({active:active!==false,enabled:false,revealed:true});__aboutRefreshPreview.view.presentToolsTrack({active:active!==false,allowed:true,automatic:false,top:document.querySelector('.ar-preview-bar').getBoundingClientRect().bottom+8,bottom:innerHeight-40})}'''
READ='''()=>{const root=__aboutRefreshPreview.view.toolsElement,rail=root.querySelector('.ar-tool-rail');return {now:performance.now(),d:{...root.dataset},position:__aboutRefreshPreview.view.captureState().tools.track,rail:rail.getBoundingClientRect().toJSON(),stage:!!rail.querySelector('.ar-track-stage'),reduced:matchMedia('(prefers-reduced-motion: reduce)').matches,railX:rail.scrollLeft,pageY:scrollY,focus:document.activeElement?.outerHTML.slice(0,120),cards:[...rail.querySelectorAll('.ar-tool-card')].map(e=>({id:e.dataset.toolId,instance:e.dataset.cardInstance,x:e.getBoundingClientRect().x,expanded:e.dataset.expanded}))}}'''
RECORD='''()=>{window.__frames=[];window.__recording=true;const root=__aboutRefreshPreview.view.toolsElement,rail=root.querySelector('.ar-tool-rail');const sample=now=>{if(!__recording)return;const r=rail.getBoundingClientRect();__frames.push({now,y:scrollY,d:{...root.dataset},rail:{left:r.left,right:r.right},cards:[...rail.querySelectorAll('.ar-tool-card')].map(e=>{const a=e.getBoundingClientRect(),f=e.querySelector('.ar-card-front').getBoundingClientRect(),s=e.querySelector('.ar-card-shadow').getBoundingClientRect();return{id:e.dataset.toolId,instance:e.dataset.cardInstance,x:f.x,right:f.right,leftPaint:Math.min(...[...e.querySelectorAll('[data-card-face]')].map(v=>v.getBoundingClientRect().left),s.left-Math.ceil(3*parseFloat(getComputedStyle(e.querySelector('.ar-card-shadow')).filter.match(/[\d.]+/)?.[0]||0)*1.05)),rightPaint:Math.max(...[...e.querySelectorAll('[data-card-face]')].map(v=>v.getBoundingClientRect().right),s.right+Math.ceil(3*parseFloat(getComputedStyle(e.querySelector('.ar-card-shadow')).filter.match(/[\d.]+/)?.[0]||0)*1.05))}})});requestAnimationFrame(sample)};requestAnimationFrame(sample)}'''
try:
 with sync_playwright() as play:
  browser=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);report['version']=browser.version
  def read(p):return p.evaluate(READ)
  def frames(p):return p.evaluate('()=>{__recording=false;return __frames}')
  def over(p):
   box=p.locator('.ar-tool-rail').bounding_box();p.mouse.move(box['x']+box['width']*.5,box['y']+box['height']*.5)
  def wheel(p,delta=120,n=1,gap=35,x=0):
   over(p)
   for i in range(n):p.mouse.wheel(x,delta);p.wait_for_timeout(gap)
  def setup(p,paused=True):
   p.goto(origin+'/preview.html');p.wait_for_function('!!window.__aboutRefreshPreview');p.locator('[data-preview-station=A3]').click();p.wait_for_timeout(120)
   p.evaluate('()=>__aboutRefreshPreview.view.presentToolsEntrance({active:true,enabled:false,revealed:true})');p.evaluate(PRESENT);p.locator('[data-action=auto]').click();p.wait_for_timeout(1150)
   if paused:p.locator('[data-action=auto]').click()
   assert read(p)['d']['trackMode']=='program'
  def case(name,fn,paused=True):
   if args.only and name not in args.only:return
   ctx=browser.new_context(viewport={'width':1440,'height':1100});p=ctx.new_page();p.set_default_timeout(15000);events=[];p.on('pageerror',lambda e:events.append(str(e)));entry={'id':name,'status':'失败'}
   try:
    setup(p,paused);data=fn(p);assert not events,events;save(run/(name+'-data.json'),data);p.screenshot(path=str(run/(name+'.png')));entry.update(status='通过',data=name+'-data.json')
   except Exception as e:
    failures.append(name);entry.update(error=str(e),traceback=traceback.format_exc())
    try:save(run/(name+'-failure.json'),read(p));p.screenshot(path=str(run/(name+'-failure.png')))
    except Exception:pass
   finally:report['checks'].append(entry);report['events'].extend(events);save(run/'browser.json',report);ctx.close()
  def gentle(p):
   a=read(p);p.evaluate(RECORD);wheel(p,120);p.wait_for_timeout(1300);f=frames(p);b=read(p);travel=float(b['d']['trackDistance'])-float(a['d']['trackDistance']);peak=max(float(v['d'].get('trackSpeed',0)) for v in f)
   assert 40<travel<115,(travel,peak);assert 80<peak<400,peak;assert b['d']['trackEnabled']=='false' and b['d']['trackFramePending']=='false' and b['d']['trackSpeed']=='0.0000';assert b['pageY']==a['pageY']
   return {'travel':travel,'peak':peak,'before':a,'after':b,'frames':f}
  def intensity(p):
   p.evaluate(RECORD);wheel(p,35,5,150);p.wait_for_timeout(1300);slow=frames(p);p.evaluate(RECORD);wheel(p,160,12,22);p.wait_for_timeout(1400);fast=frames(p)
   a=max(abs(float(v['d'].get('trackSpeed',0))) for v in slow);b=max(abs(float(v['d'].get('trackSpeed',0))) for v in fast)
   assert b>a*1.8 and b<=560.01,(a,b);assert read(p)['d']['trackFramePending']=='false';return {'slowPeak':a,'fastPeak':b,'slow':slow,'fast':fast}
  def cap(p):
   p.evaluate(RECORD);wheel(p,20000,10,12);p.wait_for_timeout(1400);f=frames(p);peak=max(abs(float(v['d'].get('trackSpeed',0))) for v in f);assert 500<peak<=560.01,peak;return {'peak':peak,'frames':f}
  def reverse(p):
   p.evaluate(RECORD);wheel(p,120,7,25);a=read(p);wheel(p,-120,6,25);b=read(p);p.wait_for_timeout(1450);f=frames(p);c=read(p)
   assert float(a['d']['trackSpeed'])>100 and float(b['d']['trackSpeed'])<-100,(a['d'],b['d']);assert c['d']['trackDirection']=='-1'
   speeds=[float(v['d'].get('trackSpeed',0)) for v in f];assert any(0<s<100 for s in speeds) and any(-100<s<0 for s in speeds)
   assert c['d']['trackFramePending']=='false';return {'forward':a,'reverse':b,'after':c,'frames':f}
  def auto_tail(p):
   p.evaluate(RECORD);wheel(p,-160,6,25);p.wait_for_timeout(1500);f=frames(p);a=read(p);assert a['d']['trackEnabled']=='true' and a['d']['trackDirection']=='-1' and abs(float(a['d']['trackSpeed'])+28)<.01,a['d']
   p.wait_for_timeout(600);b=read(p);assert float(b['d']['trackDistance'])<float(a['d']['trackDistance'])-12;return {'afterTail':a,'later':b,'frames':f}
  def hard_pause(p):
   wheel(p,160,6,25);p.locator('[data-action=auto]').click();a=read(p);p.wait_for_timeout(250);b=read(p);assert a['d']['trackOffset']==b['d']['trackOffset'] and b['d']['trackSpeed']=='0.0000' and b['d']['trackFramePending']=='false'
   p.locator('[data-action=auto]').click();p.wait_for_timeout(1600);c=read(p);assert abs(float(c['d']['trackSpeed'])-28)<.01,c['d'];return {'pause':a,'still':b,'resume':c}
  def leave(p):
   wheel(p,160,5,25);a=read(p);p.mouse.move(10,1000);p.wait_for_timeout(650);b=read(p);assert b['d']['trackFramePending']=='false' and b['d']['trackSpeed']=='0.0000';return {'beforeLeave':a,'afterLeave':b}
  def horizontal(p):
   over(p);a=read(p);p.mouse.wheel(100,0);p.wait_for_timeout(150);b=read(p);assert b['d']['trackMode']=='native' and b['d']['trackFramePending']=='false';assert 80<=b['railX']-a['position']['position']['scrollLeft']<=120,(a['position'],b['railX'])
   p.mouse.wheel(100,0);p.wait_for_timeout(200);c=read(p);assert 80<=c['railX']-b['railX']<=120;return {'before':a,'first':b,'second':c}
  def reverse_native(p):
   wheel(p,-120);p.wait_for_timeout(1300);a=read(p);assert a['d']['activeId']=='midjourney'
   over(p);p.mouse.wheel(80,0);p.wait_for_timeout(200);b=read(p);assert b['d']['trackMode']=='native';assert b['railX']<200 and next(c for c in b['cards'] if c['id']=='midjourney')['x']<b['rail']['right'];return {'reverseSeam':a,'nativeHandoff':b}
  def axis(p):
   wheel(p,120);over(p);p.mouse.wheel(100,0);p.wait_for_timeout(50);a=read(p);assert a['d']['trackMode']=='program',a['d'];p.wait_for_timeout(240);p.mouse.wheel(100,0);p.wait_for_timeout(100);b=read(p);assert b['d']['trackMode']=='native';return {'sameGesture':a,'newGesture':b}
  def units(p):
   def send(y,mode=0,**kw):
    return p.evaluate('''v=>{const e=document.querySelector('.ar-tool-rail'),b=e.getBoundingClientRect(),w=new WheelEvent('wheel',{bubbles:true,cancelable:true,deltaY:v.y,deltaMode:v.mode,clientX:b.x+b.width/2,clientY:b.y+b.height/2,...v.kw});e.dispatchEvent(w);return{prevented:w.defaultPrevented,d:{...__aboutRefreshPreview.view.toolsElement.dataset}}}''',{'y':y,'mode':mode,'kw':kw})
   a=send(3,1);p.wait_for_timeout(30);b=read(p);assert a['prevented'];assert 80<float(b['d']['trackTargetSpeed'])<250,b['d'];p.wait_for_timeout(1400)
   c=send(1,2);p.wait_for_timeout(50);d=read(p);assert c['prevented'] and float(d['d']['trackTargetSpeed'])>500
   p.wait_for_timeout(1400);zero=send(0);nan=send(float('nan')) if False else None
   assert not zero['prevented'];return {'lineEvent':a,'line':b,'pageEvent':c,'page':d,'zero':zero,'trusted':False}
  def modifiers(p):
   over(p);a=read(p);p.keyboard.down('Control');p.mouse.wheel(0,120);p.keyboard.up('Control');p.wait_for_timeout(200);b=read(p);assert b['d']['trackOffset']==a['d']['trackOffset'] and b['d']['trackFramePending']=='false';return {'before':a,'after':b}
  def operations(p):
   wheel(p,160,5,25);p.locator('[data-action=next]').click();a=read(p);p.wait_for_timeout(300);b=read(p);assert a['d']['trackOffset']==b['d']['trackOffset'] and b['d']['trackFramePending']=='false'
   wheel(p,160,5,25);p.locator('[data-category=G6]').click();p.wait_for_timeout(250);c=read(p);assert c['d']['trackMode']=='native' and c['d']['trackFramePending']=='false'
   p.locator('[data-action=auto]').click();p.wait_for_timeout(1000);wheel(p,160,3,25);p.locator('[data-action=all]').click();p.wait_for_timeout(100);d=read(p);assert d['d']['mode']=='all' and d['d']['trackFramePending']=='false'
   p.locator('.ar-all-tools [data-action=return]').first.click();p.wait_for_timeout(300);e=read(p);assert e['d']['trackEnabled']=='false' and e['d']['trackFramePending']=='false';return {'next':b,'category':c,'all':d,'return':e}
  def snapshot(p):
   wheel(p,-160,4,25);p.evaluate('()=>{window.__saved=__aboutRefreshPreview.view.captureState();window.__oldRoot=__aboutRefreshPreview.view.toolsElement;__aboutRefreshPreview.remount(__saved)}');p.wait_for_timeout(100);p.evaluate(PRESENT);p.wait_for_timeout(250);a=read(p);old=p.evaluate('({...__oldRoot.dataset})');assert a['position']['direction']==-1 and a['d']['trackFramePending']=='false' and a['d']['trackSpeed']=='0.0000';assert old['trackState']=='disposed' and old['trackFramePending']=='false'
   p.locator('[data-action=auto]').click();p.wait_for_timeout(1500);b=read(p);assert abs(float(b['d']['trackSpeed'])+28)<.01;return {'snapshot':p.evaluate('__saved'),'restored':a,'old':old,'resume':b}
  def suspend(p):
   wheel(p,-160,4,25);p.evaluate(PRESENT,False);a=read(p);p.wait_for_timeout(600);p.evaluate(PRESENT);p.wait_for_timeout(300);b=read(p);assert a['d']['trackOffset']==b['d']['trackOffset'] and b['d']['trackFramePending']=='false' and b['d']['trackSpeed']=='0.0000';return {'suspended':a,'returned':b}
  def hidden(p):
   wheel(p,160,4,25);p.evaluate('Object.defineProperty(document,"hidden",{configurable:true,get:()=>true});document.dispatchEvent(new Event("visibilitychange"))');a=read(p);p.wait_for_timeout(200);p.evaluate('delete document.hidden;document.dispatchEvent(new Event("visibilitychange"))');p.wait_for_timeout(400);b=read(p);assert a['d']['trackOffset']==b['d']['trackOffset'] and b['d']['trackFramePending']=='false';return {'simulatedHidden':True,'hidden':a,'returned':b}
  def resize(p):
   wheel(p,160,4,25);p.set_viewport_size({'width':1280,'height':1100});p.wait_for_timeout(500);p.evaluate(PRESENT);a=read(p);p.wait_for_timeout(500);b=read(p);assert a['d']['trackOffset']==b['d']['trackOffset'] and b['d']['trackFramePending']=='false';return {'resized':a,'later':b}
  def reduce(p):
   wheel(p,160,4,25);p.emulate_media(reduced_motion='reduce');p.wait_for_timeout(400);a=read(p);assert a['d']['trackMode']=='native' and a['d']['trackFramePending']=='false';return a
  def cycle(p,category=None):
   if category:
    p.locator('[data-category='+category+']').click();p.locator('[data-action=auto]').click();p.wait_for_timeout(1150);p.locator('[data-action=auto]').click()
   a=read(p);ids=[c['id'] for c in a['cards']];instances={c['id']:c['instance'] for c in a['cards']};p.evaluate(RECORD);over(p);segments=[];goal=float(a['d']['trackPeriod'])+500
   for direction in [-1,1]:
    start=read(p);t=time.monotonic()
    while time.monotonic()-t<24:
     p.mouse.wheel(0,300*direction);p.wait_for_timeout(55);m=read(p)
     if abs(float(m['d']['trackDistance'])-float(start['d']['trackDistance']))>goal:break
    assert abs(float(m['d']['trackDistance'])-float(start['d']['trackDistance']))>goal-80,(direction,m['d']);segments.append({'direction':direction,'before':start,'after':m})
   p.wait_for_timeout(1300);f=frames(p);save(run/('cycle-'+(category or 'all')+'-frames.json'),f);seen=set();wraps=[];sampled_entries=[];largest_gap=0
   for i,v in enumerate(f):
    assert [c['id'] for c in v['cards']]==ids
    visible=[c for c in v['cards'] if c['right']>v['rail']['left'] and c['x']<v['rail']['right']]
    seen.update(c['id'] for c in visible)
    ordered=sorted(visible,key=lambda c:c['x'])
    for first,second in zip(ordered,ordered[1:]):largest_gap=max(largest_gap,second['x']-first['right']);assert second['x']-first['right']<(160 if float(v['d'].get('trackLeadIn',0)) else 70)
    for c in v['cards']:assert instances[c['id']]==c['instance']
    if not i:continue
    prev={c['id']:c for c in f[i-1]['cards']};rail=v['rail'];oldrail=f[i-1]['rail']
    for c in v['cards']:
     old=prev[c['id']]
     if abs(c['x']-old['x'])>float(v['d']['trackPeriod'])/2:
      before=old['rightPaint']<=oldrail['left']+.6 or old['leftPaint']>=oldrail['right']-.6
      after=c['rightPaint']<=rail['left']+.6 or c['leftPaint']>=rail['right']-.6
      # A dropped frame can cross the entire fully-clipped seam interval.
      # The sampled incoming paint may then have entered naturally during that
      # physical advance. Require the outgoing paint to be fully clipped and
      # bound the entry by the measured travel, rather than requiring the first
      # incoming sample to still be offscreen. All ten faces and 3-sigma shadow
      # remain part of these bounds; node identity and gap assertions stay above.
      if not (before and after):
       travel=abs(float(v['d']['trackDistance'])-float(f[i-1]['d']['trackDistance']))
       direction=int(v['d']['trackDirection'])
       incoming=max(0,rail['right']-c['leftPaint']) if direction==1 else max(0,c['rightPaint']-rail['left'])
       assert before and incoming<=travel+1,{'id':c['id'],'old':old,'new':c,'rail':rail,'travel':travel,'incoming':incoming}
       sampled_entries.append({'id':c['id'],'time':v['now'],'travel':travel,'incomingPaintPx':incoming,'outgoingFullyClipped':before,'sampleGapMs':v['now']-f[i-1]['now']})
      wraps.append({'id':c['id'],'time':v['now'],'direction':v['d']['trackDirection']})
   assert len(seen)==len(ids) and len(wraps)>=2*len(ids)-4,(seen,len(wraps));assert float(read(p)['d']['trackLeadIn'])==0
   return {'segments':segments,'seen':sorted(seen),'wraps':wraps,'largestFaceGap':largest_gap,'sampledEntries':sampled_entries,'framesFile':'cycle-'+(category or 'all')+'-frames.json'}
  case('gentle-notch-manual-tail',gentle);case('slow-fast-intensity',intensity);case('extreme-input-speed-cap',cap);case('reverse-brakes-smoothly',reverse)
  case('automatic-reverse-tail-base',auto_tail,False);case('pause-hard-stop-resume-base',hard_pause,False);case('pointer-leave-short-tail',leave)
  case('horizontal-first-native-delta',horizontal);case('reverse-seam-native-current-card',reverse_native);case('gesture-axis-ownership',axis);case('line-page-zero-normalization',units);case('ctrl-wheel-native-zoom',modifiers)
  case('buttons-categories-overview-clear-motion',operations);case('snapshot-direction-not-velocity',snapshot);case('leave-return-no-old-inertia',suspend);case('hidden-no-old-inertia',hidden);case('resize-paused-clears-inertia',resize);case('reduced-motion-clears-inertia',reduce)
  case('real-wheel-two-full-directions',cycle);case('real-wheel-five-card-directions',lambda p:cycle(p,'G6'))
  report['complete']=not failures;browser.close();report['browserClosed']=True
finally:server.shutdown();server.server_close();report['serverClosed']=True;report['finishedAtShanghai']=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat();save(run/'browser.json',report)
print(json.dumps({'checks':len(report['checks']),'passed':len(report['checks'])-len(failures),'failures':failures},ensure_ascii=False));raise SystemExit(1 if failures else 0)
