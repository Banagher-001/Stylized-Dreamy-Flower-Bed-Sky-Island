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
READ=r'''()=>{const root=document.querySelector('.ar-tools-browser'),rail=root.querySelector('.ar-tool-rail'),active=rail.querySelector('[data-reading="true"]');const box=e=>e.getBoundingClientRect().toJSON();const hitGrid=e=>{if(e.dataset.expanded!=='true')return[];const f=e.querySelector('.ar-card-front').getBoundingClientRect(),r=rail.getBoundingClientRect(),h=document.querySelector('.tour-header')?.getBoundingClientRect().bottom??0;const l=Math.max(f.left+6,r.left+4),t=Math.max(f.top+6,r.top+4,h+4),right=Math.min(f.right-6,r.right-4,innerWidth-4),bottom=Math.min(f.bottom-6,r.bottom-4,innerHeight-4);if(right<=l||bottom<=t)return[];return [.1,.5,.9].flatMap(x=>[.2,.5,.8].map(y=>document.elementFromPoint(l+(right-l)*x,t+(bottom-t)*y)?.closest('.ar-tool-card')?.dataset.toolId??null))};const card=e=>{const front=e.querySelector('.ar-card-front'),d=e.querySelector('.ar-card-detail'),button=e.querySelector('button'),shade=e.querySelector('.ar-card-shadow');return{id:e.dataset.toolId,instance:e.dataset.cardInstance,state:{...e.dataset},hitGrid:hitGrid(e),front:box(front),width:e.offsetWidth,height:front.offsetHeight,overflowX:front.scrollWidth-front.clientWidth,reading:e.dataset.readingPose,faces:[...e.querySelectorAll('[data-card-face]')].map(box),shadow:box(shade),shadowBlur:parseFloat(getComputedStyle(shade).filter.match(/[\d.]+/)?.[0] ?? '0'),detail:{text:d.textContent,hidden:d.hidden,aria:d.getAttribute('aria-hidden'),opacity:Number(getComputedStyle(d).opacity),font:parseFloat(getComputedStyle(d).fontSize),rect:box(d)},button:button?{text:button.textContent,expanded:button.getAttribute('aria-expanded'),rect:box(button)}:null}};return{now:performance.now(),y:scrollY,mode:document.querySelector('main')?.dataset.readingMode,d:{...root.dataset},rail:box(rail),railX:rail.scrollLeft,controls:box(root.querySelector('.ar-tool-controls')),count:root.querySelector('.ar-card-count').textContent,active:active?card(active):null,cards:[...rail.querySelectorAll('.ar-tool-card')].map(card),focus:{action:document.activeElement?.dataset.action,tool:document.activeElement?.dataset.toolId},snapshot:window.__aboutRefreshPreview?.view.captureState(),duplicates:[...document.querySelectorAll('[id]')].filter((e,i,a)=>a.findIndex(x=>x.id===e.id)!==i).map(e=>e.id),overflow:document.documentElement.scrollWidth-innerWidth}}'''
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
  content=json.loads((ROOT/'src/tour/about-refresh/content.ts').read_text().split('export const aboutRefreshContent = ',1)[1].split(' as const satisfies AboutContent;',1)[0]);order=[c['id'] for c in sorted(content['cards'],key=lambda c:c['recommendationOrder'])];byid={c['id']:c for c in content['cards']}
  def detail(m,id):return next(c for c in m['cards'] if c['id']==id)
  def complete(m,id,mode='preview'):
   c=detail(m,id);assert c['detail']['text']==byid[id]['detail'] and not c['detail']['hidden'] and c['detail']['aria']=='false' and c['detail']['opacity']==1,c
   assert c['button']['expanded']=='true' and c['button']['text']==('固定阅读' if mode=='preview' else '收起详情'),c['button']
   assert c['overflowX']<=1 and c['detail']['font']>=16,c
   assert c['hitGrid'] and set(c['hitGrid'])=={id},(id,c['hitGrid'],c['front'],m['d'])
   d=c['detail']['rect'];f=c['front'];assert d['left']>=f['left']+4 and d['right']<=f['right']-4 and d['top']>f['top']+10 and d['bottom']<=c['button']['rect']['top']-2,(d,f,c['button'])
   if c['state']['detailWide']=='true':assert 339<=c['width']<=361 and c['height']<=320,c
   return c
  def click_button(p,id):
   b=p.locator(f'.ar-tool-card[data-tool-id={id}] button').bounding_box();p.mouse.move(b['x']+b['width']/2,b['y']+b['height']/2);p.mouse.click(b['x']+b['width']/2,b['y']+b['height']/2)
  def all_cards(p):
   start=read(p);results=[]
   for i,id in enumerate(order):
    if i:p.locator('[data-action=next]').click()
    m=hover(p,id);complete(m,id);bounds(m);assert m['d']['readingId']==id and m['count']==f'{i+1} / 22'
    assert abs(m['rail']['height']-start['rail']['height'])<.6,(id,start['rail'],m['rail']);assert m.get('mode')==start.get('mode')
    results.append(m)
   p.locator('[data-action=next]').click();p.wait_for_timeout(350);end=read(p);assert [c['instance'] for c in end['cards']]==[c['instance'] for c in start['cards']];assert [c['id'] for c in end['cards']]==order
   return {'before':start,'readings':results,'after':end}
  def preview_exit(p):
   a=hover(p);complete(a,'comfyui');p.wait_for_timeout(300);b=read(p);assert a['d']['trackOffset']==b['d']['trackOffset'] and b['d']['trackEnabled']=='true' and b['d']['hoverFramePending']=='false';leave(p);c=read(p);assert c['d']['detailMode']=='summary' and detail(c,'comfyui')['detail']['hidden'] and detail(c,'comfyui')['width']==232 and c['d']['trackEnabled']=='true' and float(c['d']['trackSpeed'])>25;return {'preview':a,'held':b,'after':c}
  def paused_preview(p):
   a=hover(p);complete(a,'comfyui');leave(p);b=read(p);assert b['d']['trackEnabled']=='false' and b['d']['trackFramePending']=='false' and b['d']['detailMode']=='summary';return {'preview':a,'after':b}
  def pin(p):
   a=hover(p);p.evaluate('''()=>{window.__pinFrames=[];window.__pinRecording=true;const c=document.querySelector('.ar-tool-card[data-tool-id=comfyui]');const sample=()=>{if(!__pinRecording)return;__pinFrames.push({width:c.offsetWidth,hidden:c.querySelector('.ar-card-detail').hidden});requestAnimationFrame(sample)};requestAnimationFrame(sample)}''');click_button(p,'comfyui');p.wait_for_timeout(650);p.mouse.move(10,80);p.wait_for_timeout(500);b=read(p);f=p.evaluate('()=>{__pinRecording=false;return __pinFrames}');complete(b,'comfyui','pinned');bounds(b);assert b['d']['trackEnabled']=='false' and b['d']['detailMode']=='pinned' and b['d']['trackOffset']==a['d']['trackOffset'];assert all(v['width']>=339 and not v['hidden'] for v in f),f
   click_button(p,'comfyui');p.wait_for_timeout(650);c=read(p);assert c['d']['detailMode']=='summary' and detail(c,'comfyui')['detail']['hidden'] and c['d']['trackEnabled']=='false';p.mouse.move(**point(p,'comfyui'));p.wait_for_timeout(500);d=read(p);assert d['d']['detailMode']=='summary';return {'preview':a,'pinned':b,'frames':f,'closed':c,'suppressed':d}
  def during(p):
   p.mouse.move(**point(p,'comfyui'));p.wait_for_timeout(180);c=p.locator('.ar-tool-card[data-tool-id=comfyui] button');b=c.bounding_box();p.mouse.move(b['x']+b['width']/2,b['y']+b['height']/2);p.mouse.down();first=read(p);p.wait_for_timeout(200);second=read(p);assert detail(first,'comfyui')['width']==detail(second,'comfyui')['width'] and detail(first,'comfyui')['reading']==detail(second,'comfyui')['reading'];p.mouse.up();p.wait_for_timeout(800);end=read(p);complete(end,'comfyui','pinned');return {'down':first,'held':second,'pinned':end}
  def direct(p):
   click_button(p,'midjourney');p.wait_for_timeout(700);m=read(p);complete(m,'midjourney','pinned');assert m['d']['detailMode']=='pinned' and m['d']['trackEnabled']=='false';return m
  def resume(p):
   hover(p);click_button(p,'comfyui');p.wait_for_timeout(400);p.locator('[data-action=auto]').click();p.wait_for_timeout(1700);m=read(p);assert m['d']['detailMode']=='summary' and m['d']['trackEnabled']=='true' and float(m['d']['trackSpeed'])>25 and not m['active'];assert all(c['detail']['hidden'] for c in m['cards']);return m
  def switch_pinned(p):
   hover(p,'midjourney');click_button(p,'midjourney');p.wait_for_timeout(500);p.locator('[data-action=next]').click();p.wait_for_timeout(700);a=read(p);complete(a,'comfyui','pinned');assert a['count']=='2 / 22';p.locator('[data-action=previous]').click();p.wait_for_timeout(700);b=read(p);complete(b,'midjourney','pinned');assert b['count']=='1 / 22' and b['d']['trackEnabled']=='false';return {'next':a,'previous':b}
  def edge(p):
   r=p.locator('.ar-tool-rail').bounding_box();p.mouse.move(r['x']+r['width']/2,r['y']+r['height']/2);p.mouse.wheel(0,400);p.wait_for_timeout(1400);a=hover(p,'midjourney');complete(a,'midjourney');bounds(a);assert a['count']=='1 / 22';f=a['active']['front'];samples=[]
   for fx,fy in [(.15,.2),(.85,.2),(.85,.8),(.15,.8)]:
    p.mouse.move(f['x']+f['width']*fx,f['y']+f['height']*fy);p.wait_for_timeout(500);m=read(p);complete(m,'midjourney');bounds(m);hits=p.evaluate('''()=>{const c=document.querySelector('[data-reading=true]'),b=c.querySelector('.ar-card-front').getBoundingClientRect();return [.1,.5,.9].flatMap(x=>[.2,.5,.8].map(y=>document.elementFromPoint(b.x+b.width*x,b.y+b.height*y)?.closest('.ar-tool-card')?.dataset.toolId))}''');assert set(hits)=={'midjourney'},hits;samples.append(m)
   return {'first':a,'corners':samples}
  def last(p):
   p.locator('[data-action=previous]').click();a=hover(p,'vibe-coding');complete(a,'vibe-coding');bounds(a);click_button(p,'vibe-coding');p.wait_for_timeout(500);b=read(p);complete(b,'vibe-coding','pinned');assert b['count']=='22 / 22';return {'preview':a,'pinned':b}
  def wheel(p,horizontal=False):
   a=hover(p);p.mouse.wheel(100 if horizontal else 0,0 if horizontal else 120);p.wait_for_timeout(180);b=read(p);assert b['d']['detailMode']=='summary' and detail(b,'comfyui')['detail']['hidden'] and detail(b,'comfyui')['width']==232
   if horizontal:assert b['d']['trackMode']=='native' and b['railX']>50
   else:assert b['y']==a['y'] and float(b['d']['trackDistance'])>float(a['d']['trackDistance'])+3 and float(b['d']['trackSpeed'])>40
   return {'before':a,'after':b}
  def pinned_page(p):
   hover(p);click_button(p,'comfyui');p.wait_for_timeout(500);a=read(p);p.mouse.move(**point(p,'comfyui'));p.mouse.wheel(0,120);p.wait_for_timeout(500);b=read(p);assert b['y']>a['y']+70 and b['d']['detailMode']=='pinned' and b['d']['trackEnabled']=='false';return {'pinned':a,'afterWheel':b}
  def category(p):
   hover(p);click_button(p,'comfyui');p.wait_for_timeout(400);p.locator('[data-category=G2]').click();p.wait_for_timeout(400);m=read(p);assert len(m['cards'])==2 and m['d']['detailMode']=='summary' and all(c['detail']['hidden'] for c in m['cards']);return m
  def overview(p):
   a=hover(p);click_button(p,'comfyui');p.wait_for_timeout(400);p.locator('[data-action=all]').click();p.wait_for_timeout(200);assert p.locator('.ar-catalog .ar-card-detail:not([hidden])').count()==22
   p.locator('.ar-all-tools [data-action=return]').first.click();p.wait_for_timeout(700);b=read(p);complete(b,'comfyui','pinned');assert abs(float(b['d']['trackOffset'])-float(a['d']['trackOffset']))<1 and b['d']['trackEnabled']=='false';return {'before':a,'returned':b}
  def keyboard(p):
   p.locator('.ar-tool-rail').focus();p.keyboard.press('Tab');p.wait_for_timeout(650);a=read(p);id=a['focus']['tool'];complete(a,id);assert a['active']['state']['pose']=='0,0';p.keyboard.press('Enter');p.wait_for_timeout(500);b=read(p);complete(b,id,'pinned');p.keyboard.press('Escape');p.wait_for_timeout(500);c=read(p);assert c['focus']['tool']==id and c['d']['detailMode']=='summary';p.keyboard.press('Tab');p.keyboard.press('Shift+Tab');p.wait_for_timeout(650);d=read(p);complete(d,id);return {'preview':a,'pinned':b,'escaped':c,'refocused':d}
  def remount(p,preview=False):
   a=hover(p)
   if not preview:click_button(p,'comfyui');p.wait_for_timeout(450)
   p.evaluate('()=>{window.__snapshot=__aboutRefreshPreview.view.captureState();window.__old=__aboutRefreshPreview.view.toolsElement;__aboutRefreshPreview.remount(__snapshot)}');p.wait_for_timeout(120);p.evaluate(PRESENT);p.wait_for_timeout(900);b=read(p);old=p.evaluate('({...__old.dataset})');assert old['hoverState']=='disposed' and old['hoverFramePending']=='false'
   if preview:assert b['d']['detailMode']=='summary' and all(c['detail']['hidden'] for c in b['cards'])
   else:complete(b,'comfyui','pinned');assert b['d']['trackEnabled']=='false'
   return {'before':a,'snapshot':p.evaluate('__snapshot'),'new':b,'old':old}
  def resize(p):
   hover(p);click_button(p,'comfyui');p.wait_for_timeout(450);p.set_viewport_size({'width':390,'height':844});p.wait_for_timeout(700);a=read(p);complete(a,'comfyui','pinned');assert detail(a,'comfyui')['state']['detailWide']=='false';assert detail(a,'comfyui')['front']['left']>=a['rail']['left']-.6 and detail(a,'comfyui')['front']['right']<=a['rail']['right']+.6;a['selectedFullyVisible']=True;p.set_viewport_size({'width':1440,'height':1100});p.wait_for_timeout(900)
   if not args.main:p.evaluate(PRESENT);p.wait_for_timeout(500)
   b=read(p);complete(b,'comfyui','pinned');assert b['d']['trackEnabled']=='false';return {'phone':a,'wide':b}
  def fallback(p,large=False):
   if large:p.evaluate('document.documentElement.style.fontSize="200%"');p.wait_for_timeout(400)
   p.locator('.ar-tool-card[data-tool-id=midjourney] button').scroll_into_view_if_needed();click_button(p,'midjourney');p.wait_for_timeout(650);a=read(p);complete(a,'midjourney','pinned');assert detail(a,'midjourney')['state']['detailWide']=='false' and not a['active'];p.locator('.ar-tool-card[data-tool-id=midjourney] button').scroll_into_view_if_needed();click_button(p,'midjourney');p.wait_for_timeout(400);b=read(p);assert detail(b,'midjourney')['detail']['hidden'];return {'pinned':a,'closed':b}
  def hidden(p):
   hover(p);p.evaluate('Object.defineProperty(document,"hidden",{configurable:true,get:()=>true});document.dispatchEvent(new Event("visibilitychange"))');p.wait_for_timeout(100);p.evaluate('delete document.hidden;document.dispatchEvent(new Event("visibilitychange"))');p.wait_for_timeout(400);m=read(p);assert m['d']['detailMode']=='summary' and all(c['detail']['hidden'] for c in m['cards']);return {'simulatedHidden':True,'after':m}
  def reduced(p):
   hover(p);click_button(p,'comfyui');p.wait_for_timeout(400);p.emulate_media(reduced_motion='reduce');p.wait_for_timeout(650);m=read(p);complete(m,'comfyui','pinned');assert detail(m,'comfyui')['state']['detailWide']=='false' and m['d']['hoverFramePending']=='false';return m
  def native_resume(p):
   click_button(p,'midjourney');p.wait_for_timeout(600);a=read(p);complete(a,'midjourney','pinned');p.locator('[data-action=auto]').click();p.wait_for_timeout(1700);b=read(p);assert b['d']['detailMode']=='summary' and b['d']['trackMode']=='program' and float(b['d']['trackSpeed'])>25
   r=b['rail'];p.mouse.move(r['x']+r['width']/2,r['y']+r['height']/2);p.mouse.wheel(100,0);p.wait_for_timeout(180);c=read(p);assert c['d']['trackMode']=='native' and all(abs(float(x['reading'].split(',')[0]))<.001 and abs(float(x['reading'].split(',')[3]))<.001 for x in c['cards']);assert detail(c,'midjourney')['detail']['hidden'];return {'pinned':a,'resumed':b,'native':c}
  def dispose(p):
   hover(p);click_button(p,'comfyui');p.wait_for_timeout(350);p.evaluate('()=>{window.__old=__aboutRefreshPreview.view.toolsElement;__aboutRefreshPreview.view.dispose()}');p.wait_for_timeout(400);m=p.evaluate('({connected:__old.isConnected,d:{...__old.dataset}})');assert not m['connected'] and m['d']['hoverState']=='disposed' and m['d']['hoverFramePending']=='false' and m['d']['trackFramePending']=='false';p.evaluate('document.querySelector("#about-refresh-preview").append(__old)');return m
  def video(p):
   a=hover(p);complete(a,'comfyui');f=a['active']['front'];states=[a]
   for x,y in [(.2,.2),(.8,.2),(.8,.8),(.5,.5)]:p.mouse.move(f['x']+f['width']*x,f['y']+f['height']*y);p.wait_for_timeout(450);states.append(read(p))
   click_button(p,'comfyui');p.wait_for_timeout(500);p.mouse.move(30,80);p.wait_for_timeout(500);b=read(p);complete(b,'comfyui','pinned');p.locator('[data-action=auto]').click();p.wait_for_timeout(1500);return {'previews':states,'pinned':b,'resumed':read(p)}
  def chapter(p):
   hover(p);click_button(p,'comfyui');p.wait_for_timeout(450);p.locator('[data-action=continue]').click();p.wait_for_function('document.querySelector("#tour-host").dataset.filmStation==="B1"&&document.querySelector("#tour-host").dataset.cameraState==="settled"');go(p);p.wait_for_timeout(700);m=read(p);complete(m,'comfyui','pinned');assert m['d']['trackEnabled']=='false';return m
  def guide(p):
   p.locator('#tour-guide').click();p.wait_for_function('document.querySelector("#tour-host").dataset.guidePhase==="reading"');a=hover(p);assert p.locator('#tour-guide').get_attribute('aria-pressed')=='false';leave(p);b=read(p);assert p.locator('#tour-guide').get_attribute('aria-pressed')=='false' and b['d']['trackEnabled']=='true';return {'preview':a,'after':b}
  case('all-22-full-paragraphs',all_cards,paused=True);case('preview-closes-and-resumes',preview_exit);case('paused-preview-stays-paused',paused_preview,paused=True);case('one-click-pin-no-reopening',pin);case('click-during-width-transition',during);case('direct-click-pins-full-detail',direct);case('resume-closes-before-moving',resume);case('pinned-adjacent-navigation',switch_pinned,paused=True);case('partial-edge-full-text-and-hit-grid',edge,paused=True);case('last-card-full-text-and-pin',last,paused=True);case('first-wheel-closes-preview',wheel);case('horizontal-first-event',lambda p:wheel(p,True));case('category-clears-pinned-detail',category);case('catalog-restores-fixed-reading',overview);case('keyboard-preview-pin-escape',keyboard);case('resize-keeps-fixed-content',resize);case('hidden-clears-preview',hidden);case('reduced-motion-keeps-full-content',reduced)
  if args.main:
   case('fixed-reading-wheel-scrolls-page',pinned_page);case('fixed-reading-chapter-return',chapter);case('preview-stops-main-guide',guide);case('actual-detail-demonstration',video,video=True)
   case('phone-one-tap-full-detail',fallback,size=(390,844),program=False);case('narrow-one-tap-full-detail',fallback,size=(320,740),program=False);case('large-text-full-detail',lambda p:fallback(p,True),size=(800,600),program=False);case('reduced-stable-full-detail',fallback,reduced=True,program=False)
  else:
   case('snapshot-restores-pin',remount);case('snapshot-discards-preview',lambda p:remount(p,True));case('dispose-pinned-reading',dispose);case('native-click-full-detail',direct,program=False);case('native-pin-resume-handoff',native_resume,program=False)
  report['complete']=not failures;browser.close();report['browserClosed']=True
finally:
 if server:server.shutdown();server.server_close();report['serverClosed']=True
 report['finishedAtShanghai']=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat();save(run/'browser.json',report)
print(json.dumps({'checks':len(report['checks']),'passed':len(report['checks'])-len(failures),'failures':failures},ensure_ascii=False));raise SystemExit(1 if failures else 0)
