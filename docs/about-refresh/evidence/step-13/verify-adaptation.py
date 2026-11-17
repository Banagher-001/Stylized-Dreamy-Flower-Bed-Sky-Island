from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse,os,json,hashlib,shutil,traceback,time
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('run');ap.add_argument('--engine',default='chromium');ap.add_argument('--only',nargs='*');args=ap.parse_args()
run=OUT/args.run;run.mkdir(exist_ok=False);s=json.loads((OUT/'services-started.json').read_text());os.environ.update(s['browserEnvironment']);os.environ['PLAYWRIGHT_BROWSERS_PATH']='/workspace/.cache/ms-playwright'
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
shutil.copy2(__file__,run/'test.py.txt')
paths=[p for p in (ROOT/'src').rglob('*') if p.is_file()]+[ROOT/'dist/index.html']+list((ROOT/'dist/assets').glob('startTourPrototype*'))
save(run/'source-manifest.json',[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths])
READ=r'''()=>{const root=document.querySelector('.ar-tools-browser'),rail=root.querySelector('.ar-tool-rail'),host=document.querySelector('#tour-host'),box=e=>e?.getBoundingClientRect().toJSON(),help=root.querySelector('.ar-tool-help-panel');return {viewport:[innerWidth,innerHeight],d:{...root.dataset},mode:document.querySelector('main').dataset.readingMode,capacity:JSON.parse(document.querySelector('main').dataset.readingCapacity||'{}'),host:{...host.dataset},y:scrollY,overflow:document.documentElement.scrollWidth-innerWidth,rail:box(rail),railX:rail.scrollLeft,controls:box(root.querySelector('.ar-tool-controls')),header:box(document.querySelector('.tour-header')),focus:{tag:document.activeElement?.tagName,action:document.activeElement?.dataset.action,id:document.activeElement?.dataset.toolId,rect:box(document.activeElement),hidden:!!document.activeElement?.closest('[hidden],[inert]')},help:{hidden:help.hidden,rect:box(help),presentation:help.dataset.presentation},hint:root.querySelector('.ar-current-hint').textContent,canvas:document.querySelectorAll('canvas').length,instances:document.querySelectorAll('.ar-tools-browser').length,cards:[...rail.querySelectorAll('.ar-tool-card')].map(e=>({id:e.dataset.toolId,instance:e.dataset.cardInstance,expanded:e.dataset.expanded,wide:e.dataset.detailWide,front:box(e.querySelector('.ar-card-front')),button:box(e.querySelector('button')),bodyHidden:e.querySelector('.ar-card-detail').hidden,bodyText:e.querySelector('.ar-card-detail').textContent,flight:e.dataset.flightPose,reading:e.dataset.readingPose}))}}'''
report={'startedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'checks':[],'events':[],'complete':False,'engine':args.engine,'physicalDevice':False,'clockModified':False};failures=[]
with sync_playwright() as play:
 opts={'executable_path':'/usr/bin/chromium','args':['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist']} if args.engine=='chromium' else {'firefox_user_prefs':{'webgl.force-enabled':True,'webgl.disable-fail-if-major-performance-caveat':False}}
 browser=getattr(play,args.engine).launch(headless=True,**opts);report['version']=browser.version
 def read(p):return p.evaluate(READ)
 def go(p,h=3.34):
  if p.locator('main').get_attribute('data-reading-mode')=='stable':p.locator('.tour-reading-flow [data-flow-anchor=A3]').scroll_into_view_if_needed()
  else:
   p.evaluate('h=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})',h);p.wait_for_function('h=>Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-h)<.001&&document.querySelector("#tour-host").dataset.cameraState==="settled"',arg=h,timeout=25000)
  p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceReady==="true"',timeout=15000);p.wait_for_timeout(400)
 def setup(p):
  p.goto(s['origin']+'/?waterTime=2',wait_until='domcontentloaded');p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=90000);go(p)
 def case(name,fn,size=(1440,900),touch=False,reduce=False,unavailable=False):
  if args.only and name not in args.only:return
  opts={'viewport':{'width':size[0],'height':size[1]},'has_touch':touch,'reduced_motion':'reduce' if reduce else 'no-preference'}
  video=name=='hybrid-first-tap'
  if video:opts.update(record_video_dir=str(run/'video'),record_video_size={'width':size[0],'height':size[1]})
  if args.engine=='chromium':opts['is_mobile']=touch
  ctx=browser.new_context(**opts);p=ctx.new_page();p.set_default_timeout(12000);errors=[];console=[];p.on('console',lambda m:console.append(m.text) if m.type=='error' else None);p.on('pageerror',lambda e:errors.append(str(e)));entry={'id':name,'status':'失败','viewport':list(size),'touchEmulation':touch}
  try:
   if unavailable:ctx.add_init_script("const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type,...args){return type==='webgl'||type==='webgl2'?null:original.call(this,type,...args)}")
   setup(p);data=fn(p);
   if not unavailable:assert not console,console
   m=read(p);assert not errors,errors;assert m['overflow']<=1 and m['instances']==1,m
   ids=[c['id'] for c in m['cards']];assert len(ids)==len(set(ids)),ids;assert not m['focus']['hidden'],m['focus']
   save(run/(name+'-data.json'),data);p.screenshot(path=str(run/(name+'.png')));entry.update(status='通过',data=name+'-data.json')
  except Exception as e:
   failures.append(name);entry.update(error=str(e),traceback=traceback.format_exc())
   try:save(run/(name+'-failure.json'),read(p));p.screenshot(path=str(run/(name+'-failure.png')))
   except Exception:pass
  finally:
   entry['events']=errors;entry['consoleErrors']=console;report['checks'].append(entry);report['events'].extend(errors);ctx.close();
   if video:entry['video']=str(Path(p.video.path()).relative_to(run))
   save(run/'browser.json',report);print(json.dumps({'id':name,'status':entry['status'],'error':entry.get('error','')[:200]},ensure_ascii=False),flush=True)
 def card(m,id='comfyui'):return next(c for c in m['cards'] if c['id']==id)
 def paused(p):
  if p.locator('[data-action=auto]').is_visible() and p.locator('[data-action=auto]').get_attribute('aria-pressed')=='true':p.locator('[data-action=auto]').click()
 def pinned(p):
  paused(p);p.locator('.ar-tool-card[data-tool-id=comfyui] button').click();p.wait_for_timeout(500);m=read(p);assert m['d']['detailMode']=='pinned' and m['d']['readingId']=='comfyui';return m
 def unchanged(a,b):assert [(c['id'],c['instance']) for c in a['cards']]==[(c['id'],c['instance']) for c in b['cards']];assert a['canvas']==b['canvas']
 def retained(m):assert m['d']['readingId']=='comfyui' and not card(m)['bodyHidden'] and m['d']['trackEnabled']=='false',m['d']
 def matrix(p):
  paused(p);a=read(p);assert len(a['cards'])==22;aids=[c['instance'] for c in a['cards']]
  p.locator('[data-action=help]').click();p.wait_for_timeout(200);b=read(p);assert not b['help']['hidden'];assert b['help']['rect']['left']>=-.6 and b['help']['rect']['right']<=b['viewport'][0]+.6
  if b['mode']=='immersive':assert b['help']['presentation']=='popover' and abs(a['controls']['height']-b['controls']['height'])<.6
  else:assert b['help']['presentation']=='inline'
  p.locator('[data-action=help-close]').click();p.locator('.ar-tool-card[data-tool-id=midjourney] button').click();p.wait_for_timeout(500);c=read(p);assert c['d']['readingId']=='midjourney' and not card(c,'midjourney')['bodyHidden'];assert [x['instance'] for x in c['cards']]==aids
  p.locator('.ar-tool-card[data-tool-id=midjourney] button').click();p.wait_for_timeout(400);d=read(p);assert d['d']['detailMode']=='summary'
  return {'initial':a,'help':b,'expanded':c,'closed':d}
 def roundtrip(p):
  a=pinned(p);r=[]
  for size in [(390,844),(1440,900)]:p.set_viewport_size({'width':size[0],'height':size[1]});p.wait_for_timeout(1100);m=read(p);retained(m);unchanged(a,m);r.append(m)
  assert r[-1]['mode']=='stable'
  if p.locator('#tour-layout-toggle').is_disabled():
   assert not read(p)['capacity']['fits'];p.set_viewport_size({'width':1440,'height':1100});p.wait_for_timeout(1100);r.append(read(p));retained(r[-1])
  p.locator('#tour-layout-toggle').click();p.wait_for_function('document.querySelector("main").dataset.readingMode==="immersive"');p.wait_for_timeout(650);m=read(p);retained(m);unchanged(a,m);return {'before':a,'resized':r,'returned':m}
 def font(p):
  a=pinned(p);p.locator('[data-action=help]').click();p.evaluate('document.documentElement.style.fontSize="200%"');p.wait_for_timeout(1100);b=read(p);retained(b);assert b['mode']=='stable' and b['help']['hidden']
  p.locator('.ar-tool-card[data-tool-id=comfyui] button').focus();p.keyboard.press('Tab');assert not read(p)['focus']['hidden'];p.evaluate('document.documentElement.style.fontSize=""');p.wait_for_timeout(900);c=read(p);retained(c);assert c['mode']=='stable';unchanged(a,c);return {'before':a,'large':b,'normal':c,'fontEmulation':True}
 def orientation(p):
  a=pinned(p);p.set_viewport_size({'width':844,'height':390});p.wait_for_timeout(1000);b=read(p);retained(b);assert b['mode']=='stable';p.set_viewport_size({'width':390,'height':844});p.wait_for_timeout(1000);c=read(p);retained(c);unchanged(a,c);return {'portrait':a,'landscape':b,'returned':c}
 def touch(c,p,kind,x,y):c.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':[] if kind in ['touchEnd','touchCancel'] else [{'x':x,'y':y}]})
 def swipe(p,x,y,dx,dy):
  c=p.context.new_cdp_session(p);touch(c,p,'touchStart',x,y)
  for i in range(1,13):touch(c,p,'touchMove',x+dx*i/12,y+dy*i/12);p.wait_for_timeout(20)
  touch(c,p,'touchEnd',0,0);p.wait_for_timeout(600)
 def native_swipes(p):
  a=read(p);r=a['rail'];x=min(r['right']-25,350);y=min(max(r['top']+80,a['header']['bottom']+60),650);swipe(p,x,y,-210,0);b=read(p);assert b['railX']>a['railX']+80 and abs(b['y']-a['y'])<3,(a['railX'],b['railX'],a['y'],b['y']);swipe(p,150,y,0,-140);c=read(p);assert c['y']>b['y']+50,(b['y'],c['y']);return {'before':a,'horizontal':b,'vertical':c,'input':'CDP native touch'}
 def hybrid(p,kind):
  paused(p);r=p.locator('.ar-tool-card[data-tool-id=comfyui] .ar-card-front').bounding_box();p.mouse.move(r['x']+r['width']/2,r['y']+r['height']*.45);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.hoverState==="reading"');a=read(p);r=card(a)['button'];x=r['x']+r['width']/2;y=r['y']+r['height']/2;c=p.context.new_cdp_session(p);touch(c,p,'touchStart',x,y);p.wait_for_timeout(220);down=read(p)
  assert down['d']['toolInput']=='touch';assert max(abs(card(a)['button'][k]-card(down)['button'][k]) for k in ['left','top','right','bottom'])<.6,(card(a)['button'],card(down)['button'])
  if kind=='tap':
   touch(c,p,'touchEnd',0,0);p.wait_for_timeout(900);end=read(p);retained(end);assert end['d']['trackMode']=='native' and card(end)['wide']=='false';unchanged(a,end)
  elif kind=='swipe':
   for i in range(1,13):touch(c,p,'touchMove',x-210*i/12,y);p.wait_for_timeout(20)
   touch(c,p,'touchEnd',0,0);p.wait_for_timeout(650);end=read(p);assert end['d']['trackMode']=='native' and end['d']['detailMode']=='summary';assert end['railX']>a['railX']+70,(a['railX'],end['railX']);assert abs(end['y']-a['y'])<3
  else:
   touch(c,p,'touchCancel',0,0);p.wait_for_timeout(500);end=read(p);assert end['d']['trackMode']=='native' and end['d']['detailMode']=='summary' and end['d']['hoverFramePending']=='false';p.locator('.ar-tool-card[data-tool-id=comfyui] button').click();p.wait_for_timeout(500);assert read(p)['d']['detailMode']=='pinned'
  return {'before':a,'fingerDown':down,'after':end,'input':'CDP real touch on fine-pointer browser'}
 def first_mouse_after_swipe(p):
  gesture=hybrid(p,'swipe');p.wait_for_timeout(350);p.mouse.move(10,80);r=p.locator('.ar-tool-card[data-tool-id=comfyui] .ar-card-front').bounding_box();p.mouse.move(r['x']+r['width']/2,r['y']+r['height']*.45);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.hoverState==="reading"',timeout=2500);m=read(p);assert m['d']['toolInput']=='mouse' and m['d']['readingId']=='comfyui' and not card(m)['bodyHidden'];assert m['d']['trackEnabled']=='false';return {'touchGesture':gesture,'singleMouseMove':m,'extraMouseMoves':0}
 def mouse_return(p):
  hybrid(p,'tap');a=read(p);p.mouse.move(10,80);p.mouse.move(400,400);p.wait_for_timeout(500);b=read(p);assert b['d']['toolInput']=='mouse' and b['d']['trackEnabled']=='false';go(p);p.locator('[data-action=auto]').click();p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.trackState==="running"');p.wait_for_timeout(900);c=read(p);assert c['d']['trackMode']=='program' and float(c['d']['trackSpeed'])>25;return {'touch':a,'mouse':b,'explicitPlay':c}
 def reduced(p):
  a=pinned(p);p.locator('[data-action=help]').click();p.emulate_media(reduced_motion='reduce');p.wait_for_timeout(1000);b=read(p);retained(b);assert b['mode']=='stable' and b['help']['hidden'];assert all(b['d'][k]=='false' for k in ['trackFramePending','hoverFramePending','departureFramePending','entranceFramePending']);p.emulate_media(reduced_motion='no-preference');p.wait_for_timeout(900);c=read(p);retained(c);assert c['mode']=='stable' and c['d']['entrancePlays']==a['d']['entrancePlays'];return {'before':a,'reduced':b,'restored':c}
 def background(p):
  a=read(p);p.evaluate('Object.defineProperty(document,"hidden",{configurable:true,get:()=>true});document.dispatchEvent(new Event("visibilitychange"))');p.wait_for_timeout(100);b=read(p);p.evaluate('delete document.hidden;document.dispatchEvent(new Event("visibilitychange"))');p.wait_for_timeout(900);c=read(p);assert b['d']['trackEnabled']=='false' and c['d']['trackEnabled']=='false' and c['d']['trackFramePending']=='false';assert b['d'].get('trackOffset')==c['d'].get('trackOffset');return {'before':a,'hidden':b,'returned':c,'simulatedVisibility':True}
 def resize_burst(p):
  a=pinned(p)
  for w,h in [(1179,900),(1181,900),(768,1024),(1440,650),(1280,720),(1920,1080),(1440,900)]:p.set_viewport_size({'width':w,'height':h});p.wait_for_timeout(70)
  p.wait_for_timeout(1300);b=read(p);retained(b);unchanged(a,b);assert b['d']['departureFramePending']=='false' and b['d']['entranceFramePending']=='false';return {'before':a,'after':b}
 def font_ready(p):
  a=pinned(p);value=p.evaluate('''async()=>{const f=new FontFace('AdaptationProbe','local("DejaVu Sans")');document.fonts.add(f);document.querySelector('.about-refresh').style.fontFamily='AdaptationProbe, sans-serif';await document.fonts.load('16px AdaptationProbe');await document.fonts.ready;return{status:document.fonts.status,loaded:f.status}}''');p.wait_for_timeout(1000);b=read(p);retained(b);unchanged(a,b);assert value['loaded']=='loaded';return {'before':a,'font':value,'after':b,'localFontOnly':True}
 def graphics(p):
  a=pinned(p);p.evaluate("()=>{window.__graphicsEvents=[];for(const type of ['webglcontextlost','webglcontextrestored'])document.querySelector('#tour-host canvas').addEventListener(type,()=>__graphicsEvents.push(type))}");supported=p.evaluate('''()=>{const gl=document.querySelector('#tour-host canvas').getContext('webgl2');window.__lost=gl.getExtension('WEBGL_lose_context');if(!__lost)return false;__lost.loseContext();return true}''');assert supported
  p.wait_for_function('document.querySelector("#tour-host").dataset.renderState==="context-lost"');p.wait_for_function('document.querySelector("main").dataset.readingMode==="stable"');p.wait_for_timeout(300);b=read(p);retained(b);p.evaluate('__lost.restoreContext()');p.wait_for_function('window.__graphicsEvents.includes("webglcontextrestored")',timeout=30000);p.wait_for_function('["restored","ready"].includes(document.querySelector("#tour-host").dataset.renderState)');p.wait_for_timeout(4500);c=read(p);retained(c);unchanged(a,c);assert c['mode']=='stable'
  notice=p.evaluate('({hidden:document.querySelector("#tour-notice").hidden,text:document.querySelector("#tour-notice").textContent,motionDisabled:document.querySelector("#tour-motion").disabled,events:__graphicsEvents})');assert notice['hidden'] and not notice['motionDisabled'];assert abs(c['y']-b['y'])<2
  p.evaluate('scrollTo({top:0,behavior:"instant"})');p.wait_for_function('document.querySelector("#tour-host").dataset.renderState==="ready"',timeout=30000);visible=read(p);go(p);d=read(p);retained(d);unchanged(a,d);return {'before':a,'lost':b,'restoredOffscreen':c,'noticeAfterOldTimeout':notice,'firstVisibleFrame':visible,'returnedToReading':d,'input':'WEBGL_lose_context actual browser extension'}
 def measurement_input(p,font_change=False):
  paused(p);r=p.locator('.ar-tool-card[data-tool-id=comfyui] .ar-card-front').bounding_box();p.mouse.move(r['x']+r['width']/2,r['y']+r['height']*.45);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.hoverState==="reading"');p.wait_for_timeout(300)
  p.evaluate('window.__probes=[];window.__probeObserver=new MutationObserver(rs=>__probes.push(...rs.map(r=>({at:performance.now(),attribute:r.attributeName}))));__probeObserver.observe(document.querySelector("main"),{attributes:true,attributeFilter:["data-reading-capacity"]})')
  a=read(p);r=card(a)['button'];x=r['x']+r['width']/2;y=r['y']+r['height']/2;cdp=p.context.new_cdp_session(p);touch(cdp,p,'touchStart',x,y);p.wait_for_timeout(320);held=p.evaluate('__probes');assert not held,held
  if font_change:
   p.evaluate('document.documentElement.style.fontSize="200%"');p.wait_for_timeout(1000);during=read(p);during_probes=p.evaluate('__probes');assert during['mode']=='stable' and during_probes
  else:
   for i in range(1,13):touch(cdp,p,'touchMove',x-210*i/12,y);p.wait_for_timeout(20)
   during=read(p);during_probes=p.evaluate('__probes');assert not during_probes and during['railX']>a['railX']+70,(during_probes,during['railX'])
  touch(cdp,p,'touchEnd',0,0);p.wait_for_timeout(1200);after=read(p);probes=p.evaluate('()=>{__probeObserver.disconnect();return __probes}');assert probes;assert after['d']['detailMode']=='summary' and after['d']['trackFramePending']=='false';return {'before':a,'heldProbes':held,'during':during,'duringProbes':during_probes,'after':after,'afterProbes':probes,'actualBrowserInput':True,'fontSizeEmulation':font_change}
 def automatic_policy(p,kind):
  a=read(p);assert a['d']['trackEnabled']=='true'
  if kind=='resize':
   p.set_viewport_size({'width':1536,'height':900});p.wait_for_timeout(1400);b=read(p);assert b['mode']=='immersive' and b['d']['trackEnabled']=='true' and b['d']['trackState']=='running';return {'before':a,'resized':b}
  p.emulate_media(reduced_motion='reduce');p.wait_for_timeout(900);b=read(p);assert b['d']['trackEnabled']=='false';p.emulate_media(reduced_motion='no-preference');p.wait_for_timeout(900);c=read(p);assert c['d']['trackEnabled']=='false' and c['mode']=='stable';return {'before':a,'reduced':b,'returned':c}
 def accessibility(p):
  paused(p);p.locator('[data-action=help]').focus();p.keyboard.press('Enter');p.keyboard.press('Tab');assert read(p)['focus']['action']=='help-close';p.keyboard.press('Escape');assert read(p)['focus']['action']=='help'
  data=p.evaluate('''()=>{const r=document.querySelector('.ar-tools-browser');return {buttons:[...r.querySelectorAll('button,select')].filter(e=>e.getBoundingClientRect().width&&getComputedStyle(e).visibility!=='hidden').map(e=>({text:e.textContent,disabled:e.disabled,w:e.offsetWidth,h:e.offsetHeight,color:getComputedStyle(e).color,bg:getComputedStyle(e).backgroundColor})),focus:{color:getComputedStyle(document.activeElement).outlineColor,width:getComputedStyle(document.activeElement).outlineWidth},headingLevels:[...document.querySelector('[data-about-station=A3]').querySelectorAll('h2,h3,h4')].map(e=>({tag:e.tagName,text:e.textContent})),description:document.getElementById(r.querySelector('.ar-tool-rail').getAttribute('aria-describedby'))?.textContent}}''')
  assert all(v['w']>=44 and v['h']>=44 for v in data['buttons']),data['buttons']
  assert data['focus']['width']=='3px' and data['description']
  def ratio(a,b):
   def lum(h):
    c=[int(h[i:i+2],16)/255 for i in (0,2,4)];c=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in c];return sum(x*y for x,y in zip(c,[.2126,.7152,.0722]))
   x,y=sorted([lum(a),lum(b)]);return (y+.05)/(x+.05)
  data['paletteContrast']=[{'ink':a,'paper':b,'ratio':ratio(a,b)} for a,b in [('244c40','fffced'),('52705b','f1ecd7'),('526b4e','f1ecd7'),('4b654a','f1ecd7'),('536b49','e4e9d3'),('476b52','f9fceb'),('fffce8','2a5341'),('526b4e','f1f3df')]]
  assert all(v['ratio']>=4.5 for v in data['paletteContrast']),data['paletteContrast'];assert ratio('326f73','fffced')>=3
  return data
 try:
  case('initial-reduced-motion',matrix,reduce=True)
  case('graphics-unavailable-reading',matrix,unavailable=True)
  for w,h in [(320,740),(390,844),(430,932),(844,390),(768,1024),(1024,768),(1280,720),(1440,900),(1920,1080),(1179,900),(1180,900),(1181,900)]:case(f'viewport-{w}x{h}',matrix,(w,h),w<500)
  case('pinned-mode-roundtrip',roundtrip);case('pinned-font-200-roundtrip',font);case('pinned-phone-orientation',orientation,(390,844),True)
  if args.engine=='chromium':
   case('native-touch-horizontal-and-page',native_swipes,(390,844),True)
   for kind in ['tap','swipe','cancel']:case('hybrid-first-'+kind,lambda p,k=kind:hybrid(p,k))
   case('gesture-defers-capacity-probes',measurement_input);case('font-change-takes-priority-over-gesture',lambda p:measurement_input(p,True));case('first-mouse-hover-main-integration',first_mouse_after_swipe);case('hybrid-return-to-mouse',mouse_return);case('graphics-loss-and-recovery',graphics)
  case('same-mode-resize-keeps-automatic',lambda p:automatic_policy(p,'resize'));case('reduced-motion-does-not-restart-automatic',lambda p:automatic_policy(p,'reduce'));case('reduced-motion-roundtrip',reduced);case('background-clears-inertia',background);case('continuous-resize-keeps-pin',resize_burst);case('font-ready-keeps-reading',font_ready);case('keyboard-and-targets',accessibility)
  report['complete']=not failures
 finally:browser.close();report['browserClosed']=True;report['finishedAtShanghai']=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat();save(run/'browser.json',report)
print(json.dumps({'checks':len(report['checks']),'passed':len(report['checks'])-len(failures),'failures':failures},ensure_ascii=False));raise SystemExit(1 if failures else 0)
