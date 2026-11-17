from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from threading import Thread
import argparse,os,json,hashlib,shutil,traceback,math
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('run');ap.add_argument('--main',action='store_true');ap.add_argument('--only',nargs='*');args=ap.parse_args();run=OUT/args.run;run.mkdir(exist_ok=False)
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
shutil.copy2(__file__,run/'test.py.txt');sources=[p for p in (ROOT/'src/tour').rglob('*') if p.is_file()]+list((ROOT/'src/assets/tool-marks').glob('*.svg'))+[ROOT/'dist/index.html']+list((ROOT/'dist/assets').glob('startTourPrototype*'))
save(run/'source-manifest.json',[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources])
report={'startedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'checks':[],'events':[],'complete':False,'clockModified':False,'physicalDevice':False,'main':args.main};failures=[];server=None
if args.main:
 s=json.loads((OUT/'services-started.json').read_text());os.environ.update(s['browserEnvironment']);os.environ['PLAYWRIGHT_BROWSERS_PATH']='/workspace/.cache/ms-playwright';origin=s['origin']
else:
 payload=(OUT/'component-preview.html').read_bytes();save(run/'build.json',json.loads((OUT/'component-build.json').read_text()))
 class Handler(BaseHTTPRequestHandler):
  def log_message(self,*a):pass
  def do_GET(self):self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(payload)
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}'
READ=r'''()=>{const r=document.querySelector('.ar-tools-browser'),rail=r.querySelector('.ar-tool-rail'),rect=e=>{const b=e.getBoundingClientRect();return{left:b.left,top:b.top,right:b.right,bottom:b.bottom,width:b.width,height:b.height}},alpha=e=>{let a=1;for(let n=e;n;n=n.parentElement)a*=Number(getComputedStyle(n).opacity);return a};return{t:performance.now(),y:scrollY,d:{...r.dataset},count:r.querySelector('.ar-card-count').textContent,rail:rect(rail),railX:rail.scrollLeft,rootOpacity:Number(getComputedStyle(r).opacity),world:document.querySelector('#tour-host')?{h:document.querySelector('#tour-host').dataset.displayH,camera:document.querySelector('#tour-host').dataset.cameraState,guide:document.querySelector('#tour-host').dataset.guidePhase,time:document.querySelector('#tour-host').dataset.sceneTime}:null,mode:document.querySelector('main')?.dataset.readingMode,canvas:document.querySelectorAll('canvas').length,stage:rail.querySelectorAll('.ar-track-stage').length,cards:[...rail.querySelectorAll('.ar-tool-card')].map(c=>{const f=c.querySelector('.ar-card-front'),d=c.querySelector('.ar-card-detail'),s=c.querySelector('.ar-card-shadow');return{id:c.dataset.toolId,instance:c.dataset.cardInstance,parent:c.parentElement.dataset.cardId,width:c.offsetWidth,height:f.offsetHeight,flight:(c.dataset.flightPose??'0,0,0,0,0,0').split(',').map(Number),reading:(c.dataset.readingPose??'0,0,0,0,1,0,0').split(',').map(Number),inert:c.inert,front:rect(f),frontAlpha:alpha(f),faces:[...c.querySelectorAll('[data-card-face]')].map(rect),shade:rect(s),blur:parseFloat(getComputedStyle(s).filter.match(/[\d.]+/)?.[0]??'0'),body:{text:d.textContent,hidden:d.hidden,font:parseFloat(getComputedStyle(d).fontSize)},button:rect(c.querySelector('button'))}}),focus:{action:document.activeElement?.dataset.action,id:document.activeElement?.dataset.toolId,hidden:!!document.activeElement?.closest('[hidden],[inert]')},snapshot:window.__aboutRefreshPreview?.view.captureState(),duplicates:[...document.querySelectorAll('[id]')].filter((e,i,a)=>a.findIndex(x=>x.id===e.id)!==i).map(e=>e.id),overflow:document.documentElement.scrollWidth-innerWidth}}'''
PRESENT=r'''h=>{const v=__aboutRefreshPreview.view,active=h>=2.9&&h<3.7,p=(h-2.9)/.8;v.presentToolsDeparture({active,enabled:innerWidth>=1180&&!matchMedia('(prefers-reduced-motion:reduce)').matches&&parseFloat(getComputedStyle(document.documentElement).fontSize)<=24,progress:p,readable:active&&p>=.3&&p<=.8});v.presentToolsTrack({active:active&&p>=.3&&p<=.8,allowed:innerWidth>=1180,automatic:false,top:70,bottom:innerHeight-40})}'''
RECORD=r'''()=>{window.__frames=[];window.__record=true;const tick=t=>{if(!__record)return;const r=document.querySelector('.ar-tools-browser'),ids=(r.dataset.departureIds??'').split(',');__frames.push({t,phase:r.dataset.departure,progress:r.dataset.departureProgress,rootOpacity:Number(getComputedStyle(r).opacity),cards:[...r.querySelectorAll('.ar-tool-card')].filter(c=>ids.includes(c.dataset.toolId)).map(c=>{const f=c.querySelector('.ar-card-front').getBoundingClientRect();return{id:c.dataset.toolId,pose:(c.dataset.flightPose??'0,0,0,0,0,0').split(',').map(Number),front:[f.left,f.top,f.right,f.bottom],width:c.offsetWidth,hidden:c.querySelector('.ar-card-detail').hidden}})});requestAnimationFrame(tick)};requestAnimationFrame(tick)}'''
try:
 with sync_playwright() as play:
  browser=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']+(['--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist'] if args.main else []));report['version']=browser.version
  def read(p):return p.evaluate(READ)
  def go(p,h=3.34):
   if args.main:
    p.evaluate('h=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})',h);p.wait_for_function('h=>Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-h)<.001&&document.querySelector("#tour-host").dataset.cameraState==="settled"',arg=h,timeout=22000)
   else:p.evaluate(PRESENT,h)
  def setup(p,paused=True,program=True,fixed_world=True):
   p.goto(origin+('/?waterTime=2' if args.main and fixed_world else '/'),wait_until='domcontentloaded')
   if args.main:
    p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=90000)
    if p.locator('main').get_attribute('data-reading-mode')=='stable':p.locator('.tour-reading-flow [data-flow-anchor=A3]').scroll_into_view_if_needed();p.wait_for_timeout(300)
    else:go(p)
    p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceReady==="true"',timeout=15000)
   else:
    p.wait_for_function('!!window.__aboutRefreshPreview');p.locator('[data-preview-station=A3]').click();p.wait_for_timeout(120);p.evaluate('()=>__aboutRefreshPreview.view.presentToolsEntrance({active:true,enabled:false,revealed:true})');go(p)
    if program:p.locator('[data-action=auto]').click()
   if program:
    p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.trackState==="running"');p.wait_for_timeout(900)
    if paused:p.locator('[data-action=auto]').click()
    if not args.main:go(p)
   p.mouse.move(10,80)
  def case(name,fn,paused=True,program=True,size=None,video=False,fixed_world=True):
   if args.only and name not in args.only:return
   size=size or ((1440,900) if args.main else (1440,1100));options={'viewport':{'width':size[0],'height':size[1]}}
   if video:options.update(record_video_dir=str(run/'video'),record_video_size=options['viewport'])
   ctx=browser.new_context(**options);p=ctx.new_page();p.set_default_timeout(12000);errors=[];p.on('pageerror',lambda e:errors.append(str(e)));entry={'id':name,'viewport':list(size),'status':'失败'}
   try:
    setup(p,paused,program,fixed_world);data=fn(p);assert not errors,errors
    if p.locator('.ar-tools-browser').count():
     last=read(p);assert not last['duplicates'] and last['overflow']<=1,last
    save(run/(name+'-data.json'),data);p.screenshot(path=str(run/(name+'.png')));entry.update(status='通过',data=name+'-data.json')
   except Exception as e:
    failures.append(name);entry.update(error=str(e),traceback=traceback.format_exc())
    try:save(run/(name+'-failure.json'),read(p));p.screenshot(path=str(run/(name+'-failure.png')))
    except Exception:pass
   finally:
    report['checks'].append(entry);report['events'].extend(errors);save(run/'browser.json',report);ctx.close()
    if video:entry['video']=str(Path(p.video.path()).relative_to(run));save(run/'browser.json',report)
  def phase(p,name):p.wait_for_function('s=>document.querySelector(".ar-tools-browser").dataset.departure===s',arg=name,timeout=5000)
  def card(m,id):return next(c for c in m['cards'] if c['id']==id)
  def visible(m):return [c['id'] for c in m['cards'] if not c['inert'] and c['front']['right']>m['rail']['left']+1 and c['front']['left']<m['rail']['right']-1]
  def zero(m):assert all(max(abs(n) for n in c['flight'])<.001 for c in m['cards']),m['d']
  def same(a,b):assert [(c['id'],c['instance'],c['parent']) for c in a['cards']]==[(c['id'],c['instance'],c['parent']) for c in b['cards']];assert a['canvas']==b['canvas'];assert len(b['cards'])==len(a['cards'])
  def endpoint(m):
   for id in m['d']['departureIds'].split(','):
    c=card(m,id);margin=math.ceil(3*c['blur']*c['reading'][4]*1.05);left=min([f['left'] for f in c['faces']]+[c['shade']['left']-margin]);right=max([f['right'] for f in c['faces']]+[c['shade']['right']+margin]);assert right<m['rail']['left']-30 or left>m['rail']['right']+30,(id,left,right,m['rail'])
  def start(p,direction=1):
   go(p,3.56 if direction==1 else 3.12);phase(p,'exiting');m=read(p);assert m['d']['departureOwned']=='true' and m['d']['trackFramePending']=='false' and m['d']['hoverFramePending']=='false';assert float(m['d']['departureHandoffError'])<=1;assert m['rootOpacity']==1 and all(card(m,id)['frontAlpha']==1 for id in m['d']['departureIds'].split(','));return m
  def parked(p):
   phase(p,'departed');m=read(p);endpoint(m);assert m['d']['departureFramePending']=='false';return m
  def returned(p):
   go(p);phase(p,'idle');p.wait_for_timeout(70);m=read(p);zero(m);assert m['d']['departureOwned']=='false' and m['d']['trackDepartureHeld']=='false' and m['d']['hoverDepartureHeld']=='false';assert not m['focus']['hidden'];return m
  def hover(p,id='comfyui',pin=False):
   b=p.locator(f'.ar-tool-card[data-tool-id={id}] .ar-card-front').bounding_box();p.mouse.move(b['x']+b['width']*.5,b['y']+b['height']*.45);p.wait_for_function('id=>{const d=document.querySelector(".ar-tools-browser").dataset;return d.hoverId===id&&d.hoverState==="reading"}',arg=id)
   if pin:
    b=p.locator(f'.ar-tool-card[data-tool-id={id}] button').bounding_box();p.mouse.click(b['x']+b['width']/2,b['y']+b['height']/2);p.wait_for_timeout(400)
   return read(p)
  def record(p):p.evaluate(RECORD)
  def frames(p):return p.evaluate('()=>{__record=false;return __frames}')
  def basic(p,direction=1):
   a=read(p);record(p);b=start(p,direction);assert set(b['d']['departureIds'].split(','))==set(visible(a));assert b['d']['departureDirection']==str(direction)
   c=parked(p);assert c['d']['trackOffset']==b['d']['trackOffset'];d=returned(p);same(a,d);assert d['d']['trackEnabled']==a['d']['trackEnabled'];assert d['d']['entrancePlays']==a['d']['entrancePlays'];assert abs(float(d['d']['trackOffset'])-float(b['d']['trackOffset']))<.001
   f=frames(p);assert any(any(abs(c['pose'][4])>100 and c['front'][2]>b['rail']['left']+20 and c['front'][0]<b['rail']['right']-20 for c in x['cards']) for x in f);assert any(any(abs(c['pose'][4])>30 and c['pose'][2]<-20 for c in x['cards']) for x in f);assert all(x['rootOpacity']==1 for x in f if x['phase'] in ['exiting','returning']);return {'before':a,'during':b,'departed':c,'returned':d,'frames':f}
  def middle(p):
   a=read(p);record(p);start(p);p.wait_for_timeout(40);b=read(p);assert b['d']['departure']=='exiting';go(p);phase(p,'idle');p.wait_for_timeout(80);c=read(p);same(a,c);zero(c);f=frames(p);pairs=[(x,y) for x,y in zip(f,f[1:]) if x['phase']=='exiting' and y['phase']=='returning'];assert pairs,f
   for x,y in pairs:
    for c0,c1 in zip(x['cards'],y['cards']):assert max(abs(u-v) for u,v in zip(c0['pose'],c1['pose']))<=max(100,(y['t']-x['t'])*15),(x,y)
   return {'before':a,'turning':b,'returned':c,'frames':f}
  def auto(p):
   a=start(p);b=parked(p);c=returned(p);assert c['d']['trackEnabled']=='true';assert abs(float(c['d']['trackOffset'])-float(a['d']['trackOffset']))<1;p.wait_for_timeout(1200);d=read(p);assert float(d['d']['trackSpeed'])>25;return {'start':a,'parked':b,'returned':c,'running':d}
  def fixed(p,id='comfyui'):
   a=hover(p,id,True);record(p);b=start(p);assert card(b,id)['width']>=339 and not card(b,id)['body']['hidden'];assert json.loads(b['d']['departureSnapshot'])['cards']['expandedId']==id;c=parked(p);d=returned(p);p.wait_for_timeout(450);e=read(p);f=frames(p);same(a,e);assert e['d']['readingId']==id and e['d']['detailMode']=='pinned' and e['d']['trackEnabled']=='false';assert not card(e,id)['body']['hidden'];assert all(card_['width']>=339 and not card_['hidden'] for x in f for card_ in x['cards'] if card_['id']==id),f;return {'before':a,'during':b,'departed':c,'returned':d,'settled':e,'frames':f}
  def preview(p):
   a=hover(p);b=start(p);assert json.loads(b['d']['departureSnapshot'])['cards']['expandedId'] is None;parked(p);returned(p);p.wait_for_timeout(850);c=read(p);assert c['d']['detailMode']=='summary' and all(x['body']['hidden'] for x in c['cards']);assert c['d']['trackEnabled']==a['d']['trackEnabled'];return {'before':a,'during':b,'returned':c}
  def filtered(p,small=False):
   category='G2' if small else 'G4';p.locator(f'[data-category={category}]').click();p.wait_for_timeout(250)
   if not small:
    p.locator('[data-action=auto]').click();p.wait_for_timeout(900);p.locator('[data-action=auto]').click();p.locator('[data-action=next]').click();p.wait_for_timeout(100)
   a=read(p);b=start(p);assert set(b['d']['departureIds'].split(','))==set(visible(a));assert len(b['d']['departureIds'].split(','))==(2 if small else len(visible(a)));parked(p);c=returned(p);same(a,c);assert c['d']['category']==category;return {'before':a,'during':b,'returned':c}
  def last(p):p.locator('[data-action=previous]').click();p.wait_for_timeout(150);return fixed(p,'vibe-coding')
  def rowwheel(p):
   a=read(p);r=a['rail'];p.mouse.move((r['left']+r['right'])/2,(r['top']+r['bottom'])/2)
   for n in [120,300,-240]:p.mouse.wheel(0,n);p.wait_for_timeout(70)
   b=read(p);assert b['d']['departurePlays']=='0' and b['d']['departure']=='idle';assert abs(float(b['d']['trackDistance'])-float(a['d']['trackDistance']))>1;assert b['y']==a['y'];return {'before':a,'after':b}
  def firstcontrol(p,modal=False):
   start(p);parked(p);go(p);phase(p,'returning');p.locator('[data-action=all]' if modal else '[data-category=G6]').click();p.wait_for_timeout(650);m=read(p);assert m['d']['departure']=='idle' and m['d']['departureFramePending']=='false'
   if modal:
    assert p.locator('.ar-catalog .ar-card-detail:not([hidden])').count()==22;p.locator('.ar-all-tools [data-action=return]').first.click();p.wait_for_timeout(450)
   else:assert m['d']['category']=='G6' and len(m['cards'])==5
   return m
  def firstcard(p):
   start(p);parked(p);go(p);phase(p,'returning')
   p.evaluate('''()=>{window.__clickTrace=[];for(const type of ['pointerdown','pointerup','click'])document.addEventListener(type,e=>__clickTrace.push({type,action:e.target.closest('button')?.dataset.action,card:e.target.closest('.ar-tool-card')?.dataset.toolId,tag:e.target.tagName,x:e.clientX,y:e.clientY}),{capture:true})}''')
   id=p.wait_for_function('''()=>{const r=document.querySelector('.ar-tools-browser'),rail=r.querySelector('.ar-tool-rail').getBoundingClientRect();if(r.dataset.departure!=='returning')return false;return [...r.querySelectorAll('.ar-tool-card')].find(c=>{const f=c.querySelector('.ar-card-front'),b=c.querySelector('button').getBoundingClientRect();return !c.inert&&!f.inert&&b.left>rail.left+10&&b.right<rail.right-10&&document.elementFromPoint(b.x+b.width/2,b.y+b.height/2)?.closest('.ar-tool-card')===c})?.dataset.toolId}''',timeout=4000).json_value()
   b=p.locator(f'.ar-tool-card[data-tool-id={id}] button').bounding_box();p.mouse.move(b['x']+b['width']/2,b['y']+b['height']/2);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.departurePointerPaused==="true"');b=p.locator(f'.ar-tool-card[data-tool-id={id}] button').bounding_box();p.mouse.move(b['x']+b['width']/2,b['y']+b['height']/2);p.mouse.down();a=read(p);assert a['d']['departurePressed']=='true';p.wait_for_timeout(110);held=read(p);assert card(a,id)['flight']==card(held,id)['flight'];p.mouse.up();p.wait_for_timeout(700);m=read(p);trace=p.evaluate('__clickTrace');save(run/'moving-click-trace.json',{'id':id,'events':trace,'down':a,'held':held,'after':m});assert m['d']['departure']=='idle' and m['d']['detailMode']=='pinned' and m['d']['readingId']==id,trace;return {'clicked':id,'events':trace,'down':a,'held':held,'after':m}
  def interrupt(p,kind):
   if kind=='resize':hover(p,'comfyui',True)
   start(p)
   if kind=='resize':p.set_viewport_size({'width':390,'height':844})
   elif kind=='hidden':p.evaluate('Object.defineProperty(document,"hidden",{configurable:true,get:()=>true});document.dispatchEvent(new Event("visibilitychange"))');p.wait_for_timeout(80);p.evaluate('delete document.hidden;document.dispatchEvent(new Event("visibilitychange"))')
   elif kind=='motion':p.emulate_media(reduced_motion='reduce')
   elif kind=='font':p.evaluate('document.documentElement.style.fontSize="200%"')
   p.wait_for_timeout(850);m=read(p);assert m['d']['departure']=='idle' and m['d']['departureFramePending']=='false' and m['d']['trackDepartureHeld']=='false' and m['d']['hoverDepartureHeld']=='false';zero(m);assert len(m['cards'])==22
   if kind=='resize':
    c=card(m,'comfyui');assert m['d']['detailMode']=='pinned' and not c['body']['hidden'];assert c['front']['left']>=m['rail']['left']-1 and c['front']['right']<=m['rail']['right']+1
   return {'interruption':kind,'simulatedHidden':kind=='hidden','after':m}
  def snapshot(p):
   hover(p,'comfyui',True);start(p);parked(p);a=read(p);p.evaluate('()=>{window.__old=__aboutRefreshPreview.view.toolsElement;window.__snapshot=__aboutRefreshPreview.view.captureState();__aboutRefreshPreview.remount(__snapshot)}');p.wait_for_timeout(120);p.evaluate('()=>__aboutRefreshPreview.view.presentToolsEntrance({active:true,enabled:false,revealed:true})');go(p);p.wait_for_timeout(500);m=read(p);old=p.evaluate('({...__old.dataset})');assert m['d']['detailMode']=='pinned' and m['d']['readingId']=='comfyui' and m['d']['departure']=='idle';zero(m);assert old['departure']=='disposed' and old['departureFramePending']=='false';assert 'flight' not in json.dumps(m['snapshot']) and 'departure' not in json.dumps(m['snapshot']);return {'before':a,'restored':m,'old':old}
  def dispose(p):
   start(p);p.evaluate('()=>{window.__old=__aboutRefreshPreview.view.toolsElement;__aboutRefreshPreview.view.dispose()}');p.wait_for_timeout(400);m=p.evaluate('({connected:__old.isConnected,d:{...__old.dataset}})');assert not m['connected'] and m['d']['departure']=='disposed' and m['d']['departureFramePending']=='false' and m['d']['hoverFramePending']=='false' and m['d']['trackFramePending']=='false';return m
  def boundary(p):
   a=read(p);start(p)
   for h in [3.54,3.552,3.53,3.552,3.53]:go(p,h);p.wait_for_timeout(35)
   phase(p,'idle');p.wait_for_timeout(150);b=read(p);same(a,b);zero(b);assert b['d']['departureFramePending']=='false' and b['d']['departureOwned']=='false';return {'before':a,'after':b}
  def environment(p):
   p.locator('#tour-motion').click();p.wait_for_timeout(250);a=read(p);start(p);b=parked(p);assert a['world']['time']==b['world']['time'];returned(p);return {'paused':a,'departed':b}
  def guide(p):
   p.locator('#tour-guide').click();p.wait_for_function('document.querySelector("#tour-host").dataset.guidePhase==="reading"');p.wait_for_function('Number(document.querySelector(".ar-tools-browser").dataset.departurePlays)>0',timeout=30000);m=read(p);assert p.locator('#tour-guide').get_attribute('aria-pressed')=='true' and m['d']['departure'] in ['exiting','departed'];p.locator('#tour-guide').click();return m
  def continuing(p):
   hover(p,'comfyui',True);a=read(p);p.locator('[data-action=continue]').click();p.wait_for_function('document.querySelector("#tour-host").dataset.filmStation==="B1"&&document.querySelector("#tour-host").dataset.cameraState==="settled"');p.wait_for_timeout(450);b=read(p);assert b['d']['departureFramePending']=='false' and b['d']['departureOwned']=='false';go(p);p.wait_for_timeout(650);c=read(p);assert c['d']['detailMode']=='pinned' and c['d']['readingId']=='comfyui';return {'before':a,'next':b,'returned':c}
  def native(p,large=False,wide=False):
   if wide:p.locator('#tour-layout-toggle').click();p.wait_for_timeout(500);p.locator('.tour-reading-flow [data-flow-anchor=A3]').scroll_into_view_if_needed()
   if large:p.evaluate('document.documentElement.style.fontSize="200%"');p.wait_for_timeout(500)
   p.locator('.ar-tool-card[data-tool-id=midjourney] button').scroll_into_view_if_needed();p.locator('.ar-tool-card[data-tool-id=midjourney] button').click();p.wait_for_timeout(400);a=read(p);assert not card(a,'midjourney')['body']['hidden'];p.locator('.tour-reading-flow [data-flow-anchor=B1]').scroll_into_view_if_needed();p.wait_for_timeout(500);b=read(p);assert b['d']['departure']=='idle' and b['d']['departurePlays']=='0' and b['d']['departureFramePending']=='false';return {'reading':a,'afterPageScroll':b}
  def demonstration(p):
   record(p);start(p);p.screenshot(path=str(run/'demonstration-flight.png'));go(p);phase(p,'idle');p.wait_for_timeout(400);hover(p,'comfyui',True);start(p);parked(p);p.wait_for_timeout(200);returned(p);p.wait_for_timeout(500);f=frames(p);m=read(p);assert m['d']['detailMode']=='pinned';return {'frames':f,'after':m}
  def approach_return(p):
   start(p);parked(p);go(p);phase(p,'returning')
   point=p.wait_for_function('''()=>{const r=document.querySelector('.ar-tools-browser'),rail=r.querySelector('.ar-tool-rail').getBoundingClientRect();if(r.dataset.departure!=='returning')return false;return [...r.querySelectorAll('.ar-card-front')].filter(f=>!f.inert).map(f=>{const b=f.getBoundingClientRect();return{x:(Math.max(b.left,rail.left)+Math.min(b.right,rail.right))/2,y:(b.top+b.bottom)/2,area:Math.max(0,Math.min(b.right,rail.right)-Math.max(b.left,rail.left))*b.height}}).sort((a,b)=>b.area-a.area).find(pt=>pt.area>4000&&document.elementFromPoint(pt.x,pt.y)?.closest('.ar-tool-card'))}''').json_value()
   p.mouse.move(point['x'],point['y']);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.departurePointerPaused==="true"');return read(p)
  def hover_resume(p):
   a=approach_return(p);p.wait_for_timeout(150);b=read(p);assert [c['flight'] for c in a['cards']]==[c['flight'] for c in b['cards']];assert b['d']['departureFramePending']=='false';p.mouse.move(10,80);phase(p,'idle');p.wait_for_timeout(80);c=read(p);zero(c);assert c['d']['departurePointerPaused']=='false' and c['d']['departureOwned']=='false';return {'paused':a,'still':b,'resumed':c}
  def pointer_cancel(p):
   a=approach_return(p);p.mouse.down();p.wait_for_timeout(50);b=read(p);assert b['d']['departurePressed']=='true';p.evaluate('window.dispatchEvent(new PointerEvent("pointercancel",{pointerId:1,pointerType:"mouse"}))');p.mouse.up();p.wait_for_timeout(200);c=read(p);zero(c);assert c['d']['departure']=='idle' and c['d']['departureFramePending']=='false' and c['d']['trackDepartureHeld']=='false' and c['d']['hoverDepartureHeld']=='false';p.locator('[data-action=next]').click();p.wait_for_timeout(150);d=read(p);assert d['count']=='2 / 22';return {'simulatedPointerCancel':True,'approached':a,'down':b,'cancelled':c,'nextClick':d}
  def keyboard_return(p):
   start(p);parked(p);go(p);phase(p,'returning');p.locator('.ar-tool-rail').focus();a=read(p);assert a['d']['departure']=='idle' and a['d']['departureOwned']=='false';p.keyboard.press('Tab');p.wait_for_timeout(600);p.keyboard.press('Enter');p.wait_for_timeout(500);b=read(p);assert b['d']['detailMode']=='pinned' and b['focus']['id']==b['d']['readingId'] and not b['focus']['hidden'];p.keyboard.press('Escape');p.wait_for_timeout(500);c=read(p);assert c['d']['detailMode']=='summary' and not c['focus']['hidden'];return {'focusInterrupt':a,'keyboardPinned':b,'escaped':c}
  case('return-hover-pauses-and-resumes',hover_resume);case('return-pointer-cancel-cleans-lease',pointer_cancel);case('return-keyboard-focus-and-enter',keyboard_return)
  case('forward-visible-entities',basic);case('reverse-visible-entities',lambda p:basic(p,-1));case('midflight-continuous-return',middle);case('auto-choice-and-phase',auto,paused=False);case('pinned-wide-preserves-full-text',fixed);case('temporary-preview-not-saved',preview,paused=False);case('current-filter-and-edge-cards',filtered);case('two-card-native-flight',lambda p:filtered(p,True));case('last-card-wide-flight',last);case('row-wheel-never-departs',rowwheel,paused=False);case('return-first-control-click',firstcontrol);case('return-first-moving-card-click',firstcard);case('return-first-all-tools-click',lambda p:firstcontrol(p,True));case('resize-interrupts-fixed-flight',lambda p:interrupt(p,'resize'));case('hidden-cleans-flight',lambda p:interrupt(p,'hidden'));case('reduced-cleans-flight',lambda p:interrupt(p,'motion'));case('font-change-cleans-flight',lambda p:interrupt(p,'font'))
  if args.main:
   case('paused-world-independent-flight',environment,fixed_world=False);case('guide-remains-active-on-departure',guide,paused=False);case('continue-navigation-preserves-reading',continuing);case('actual-departure-demonstration',demonstration,video=True);case('stable-wide-keeps-native-reading',lambda p:native(p,wide=True));case('phone-native-reading',native,size=(390,844),program=False);case('narrow-native-reading',native,size=(320,740),program=False);case('large-native-reading',lambda p:native(p,large=True),size=(800,600),program=False)
  else:case('snapshot-discards-flight-restores-pin',snapshot);case('dispose-during-flight',dispose);case('boundary-reversal-no-stale-callbacks',boundary)
  report['complete']=not failures;browser.close();report['browserClosed']=True
finally:
 if server:server.shutdown();server.server_close();report['serverClosed']=True
 report['finishedAtShanghai']=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat();save(run/'browser.json',report)
print(json.dumps({'checks':len(report['checks']),'passed':len(report['checks'])-len(failures),'failures':failures},ensure_ascii=False));raise SystemExit(1 if failures else 0)
