from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import os,json,argparse,traceback,hashlib,shutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('run');ap.add_argument('--only',nargs='*');args=ap.parse_args();run=OUT/args.run;run.mkdir(exist_ok=False)
s=json.loads((OUT/'services-started.json').read_text());os.environ.update(s['browserEnvironment']);os.environ['PLAYWRIGHT_BROWSERS_PATH']='/workspace/.cache/ms-playwright'
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
source=[p for p in (ROOT/'src/tour').rglob('*') if p.is_file()]+list((ROOT/'src/assets/tool-marks').glob('*.svg'))+[ROOT/'dist/index.html']+list((ROOT/'dist/assets').glob('startTourPrototype*'))
save(run/'source-manifest.json',[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in source]);shutil.copy2(__file__,run/'test.py.txt')
report={'startedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'checks':[],'events':[],'complete':False,'clockModified':False,'physicalDevice':False};failures=[]
READ='''()=>{const root=document.querySelector('.ar-tools-browser'),rail=root.querySelector('.ar-tool-rail');return {now:performance.now(),y:scrollY,mode:document.querySelector('main').dataset.readingMode,anchor:document.querySelector('main').dataset.flowAnchor,host:{...document.querySelector('#tour-host').dataset},d:{...root.dataset},rail:rail.getBoundingClientRect().toJSON(),railX:rail.scrollLeft,button:{hidden:root.querySelector('[data-action=auto]').hidden,pressed:root.querySelector('[data-action=auto]').getAttribute('aria-pressed')},cards:[...rail.querySelectorAll('.ar-tool-card')].map(e=>({id:e.dataset.toolId,instance:e.dataset.cardInstance,expanded:e.dataset.expanded,x:e.getBoundingClientRect().x})),focus:{action:document.activeElement?.dataset.action,tool:document.activeElement?.dataset.toolId},overflow:document.documentElement.scrollWidth-innerWidth,duplicates:[...document.querySelectorAll('[id]')].filter((e,i,a)=>a.findIndex(x=>x.id===e.id)!==i).map(e=>e.id)}}'''
RECORD='''()=>{window.__frames=[];window.__recording=true;const root=document.querySelector('.ar-tools-browser');const sample=now=>{if(!__recording)return;__frames.push({now,y:scrollY,...root.dataset});requestAnimationFrame(sample)};requestAnimationFrame(sample)}'''
with sync_playwright() as play:
 browser=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist']);report['version']=browser.version
 def read(p):return p.evaluate(READ)
 def ready(p):p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"&&document.querySelector("#tour-host").dataset.renderState==="ready"',timeout=90000)
 def go(p,h=3.34):
  if p.locator('main').get_attribute('data-reading-mode')=='stable':p.locator('.tour-reading-flow [data-flow-anchor=A3]').scroll_into_view_if_needed();p.wait_for_timeout(500)
  else:
   p.evaluate('h=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})',h)
   p.wait_for_function('h=>Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-h)<.001&&document.querySelector("#tour-host").dataset.cameraState==="settled"',arg=h,timeout=25000)
 def auto(p):
  go(p);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.trackState==="running"&&document.querySelector(".ar-tools-browser").dataset.trackMode==="program"',timeout=18000);p.wait_for_timeout(1100)
 def pause(p):
  if p.locator('[data-action=auto]').get_attribute('aria-pressed')=='true':p.locator('[data-action=auto]').click()
 def over(p):
  r=p.locator('.ar-tool-rail').bounding_box();p.mouse.move(r['x']+r['width']*.5,r['y']+r['height']*.5)
 def wheel(p,y=160,n=1,gap=35,x=0):
  over(p)
  for _ in range(n):p.mouse.wheel(x,y);p.wait_for_timeout(gap)
 def case(name,fn,size=(1440,900),reduced=False,video=False):
  if args.only and name not in args.only:return
  opts={'viewport':{'width':size[0],'height':size[1]},'device_scale_factor':1,'reduced_motion':'reduce' if reduced else 'no-preference'}
  if video:opts.update(record_video_dir=str(run/'video'),record_video_size=opts['viewport'])
  ctx=browser.new_context(**opts);p=ctx.new_page();p.set_default_timeout(18000);events=[];p.on('pageerror',lambda e:events.append(str(e)));p.on('console',lambda m:events.append(m.text) if m.type=='error' else None);entry={'id':name,'status':'失败','viewport':list(size)}
  try:
   p.goto(s['origin']+'/?waterTime=2',wait_until='domcontentloaded');ready(p);data=fn(p);end=read(p);assert not events,events;assert end['overflow']<=1 and not end['duplicates'],end
   save(run/(name+'-data.json'),data);p.screenshot(path=str(run/(name+'.png')));entry.update(status='通过',data=name+'-data.json')
  except Exception as e:
   failures.append(name);entry.update(error=str(e),traceback=traceback.format_exc())
   try:save(run/(name+'-failure.json'),read(p));p.screenshot(path=str(run/(name+'-failure.png')))
   except Exception:pass
  finally:
   report['checks'].append(entry);report['events'].extend(events);save(run/'browser.json',report);ctx.close()
   if video:entry['video']=str(Path(p.video.path()).relative_to(run));save(run/'browser.json',report)
 def measure_base(p):
  return p.evaluate('''()=>new Promise(resolve=>{const slot=document.querySelector('.ar-track-stage .ar-tool-slot');const x=()=>new DOMMatrixReadOnly(getComputedStyle(slot).transform).m41;requestAnimationFrame(start=>{const first=x();const sample=now=>{if(now-start<650){requestAnimationFrame(sample);return}resolve({start,end:now,first,last:x(),speed:-(x()-first)/((now-start)/1000)})};requestAnimationFrame(sample)})})''')
 def primary(p):
  auto(p);baseForward=measure_base(p);assert abs(baseForward['speed']-28)<2,baseForward;a=read(p);p.evaluate(RECORD);wheel(p,120);p.wait_for_timeout(1200);b=read(p);assert a['y']==b['y'] and b['d']['trackEnabled']=='true' and abs(float(b['d']['trackSpeed'])-28)<.1
  wheel(p,160,9,25);c=read(p);p.screenshot(path=str(run/'accelerating.png'));assert float(c['d']['trackSpeed'])>300
  wheel(p,-160,7,25);d=read(p);p.screenshot(path=str(run/'reversing.png'));assert float(d['d']['trackSpeed'])<-200
  p.wait_for_timeout(1400);e=read(p);assert abs(float(e['d']['trackSpeed'])+28)<.1 and e['y']==a['y']
  baseReverse=measure_base(p);assert abs(baseReverse['speed']+28)<2,baseReverse
  pause(p);f=read(p);wheel(p,120,2,80);p.wait_for_timeout(1400);g=read(p);assert g['d']['trackEnabled']=='false' and g['d']['trackSpeed']=='0.0000' and g['d']['trackFramePending']=='false'
  records=p.evaluate('()=>{__recording=false;return __frames}');peak=max(abs(float(v.get('trackSpeed',0))) for v in records);assert peak<=560.01
  return {'measuredBaseForward':baseForward,'measuredBaseReverse':baseReverse,'before':a,'gentleTail':b,'fast':c,'reverse':d,'autoTail':e,'pause':f,'manualTail':g,'peak':peak,'frames':records}
 def region(p,selector):
  auto(p);pause(p);a=read(p);box=p.locator(selector).first.bounding_box();p.mouse.move(box['x']+min(box['width']/2,100),box['y']+box['height']/2);p.mouse.wheel(0,100);p.wait_for_timeout(550);b=read(p);assert b['y']>a['y']+70,(selector,a['y'],b['y']);assert b['d']['trackOffset']==a['d']['trackOffset'];return {'area':selector,'before':a,'after':b}
 def exit_region(p):
  auto(p);wheel(p,160,5,25);a=read(p);p.mouse.move(50,500);p.mouse.wheel(0,160);p.wait_for_timeout(650);b=read(p)
  assert b['y']>=a['y']+140 and b['d']['trackWheelActive']=='false' and abs(float(b['d']['trackSpeed']))<=28.01
  go(p,4.18);p.wait_for_timeout(200);left=read(p);assert left['d']['trackFramePending']=='false' and left['d']['trackSpeed']=='0.0000'
  go(p);p.wait_for_timeout(1200);c=read(p);assert c['d']['trackEnabled']=='true' and abs(float(c['d']['trackSpeed'])-28)<.1;return {'inside':a,'outsideRow':b,'leftA3':left,'returned':c}
 def fallback(p,large=False):
  if large:p.evaluate('document.documentElement.style.fontSize="200%"');p.wait_for_timeout(500)
  go(p);p.locator('.ar-tool-rail').scroll_into_view_if_needed();p.wait_for_timeout(300);a=read(p);assert a['d']['trackMode']=='native' and a['button']['hidden'];over(p);p.mouse.wheel(0,100);p.wait_for_timeout(450);b=read(p);assert b['y']>a['y']+70 and b['d']['trackMode']=='native' and b['d']['trackFramePending']=='false';return {'before':a,'after':b}
 def stable(p):
  if read(p)['mode']!='stable':p.locator('#tour-layout-toggle').click();p.wait_for_function('document.querySelector("main").dataset.readingMode==="stable"')
  go(p);a=read(p);assert a['d']['trackMode']=='native';over(p);p.mouse.wheel(0,100);p.wait_for_timeout(350);b=read(p);assert b['y']>a['y']+70
  go(p);p.locator('[data-action=auto]').click();p.wait_for_timeout(1100);c=read(p);assert c['d']['trackMode']=='program';wheel(p,160,5,25);d=read(p);assert d['y']==c['y'] and float(d['d']['trackSpeed'])>200;return {'native':a,'pageScrolled':b,'optIn':c,'wheelOwned':d}
 def entrance(p):
  p.evaluate('scrollTo({top:3.34/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})');p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entrance==="playing"',timeout=20000);a=read(p);over(p);p.mouse.wheel(0,140);p.wait_for_timeout(450);b=read(p);assert b['y']>a['y']+100 and b['d']['trackWheelActive']!='true';return {'duringEntrance':a,'afterWheel':b}
 def horizontal(p):
  auto(p);a=read(p);wheel(p,0,x=120);p.wait_for_timeout(160);b=read(p);assert b['d']['trackMode']=='native' and b['d']['trackEnabled']=='false';assert 100<=b['railX']-float(a['d']['trackOffset'])<=140,(a['d'],b['railX']);over(p);p.mouse.wheel(100,0);p.wait_for_timeout(180);c=read(p);assert 80<=c['railX']-b['railX']<=120;return {'before':a,'first':b,'second':c}
 def fit(p):
  auto(p);p.locator('[data-category=G2]').click();p.wait_for_timeout(180);a=read(p);assert a['d']['trackMode']=='native' and a['button']['hidden'];over(p);p.mouse.wheel(0,100);p.wait_for_timeout(400);b=read(p);assert b['y']>a['y']+70 and b['d']['trackFramePending']=='false';return {'before':a,'after':b}
 def overview(p):
  auto(p);wheel(p,160,5,25);p.locator('[data-action=all]').click();p.wait_for_timeout(200);a=read(p);assert a['d']['trackFramePending']=='false';assert p.locator('.ar-overview-dialog').evaluate('(e)=>e.open');before=p.locator('.ar-overview-dialog').evaluate('(e)=>e.scrollTop');p.locator('.ar-catalog').hover(position={'x':200,'y':200});p.mouse.wheel(0,300);p.wait_for_timeout(350);after=p.locator('.ar-overview-dialog').evaluate('(e)=>e.scrollTop');assert after>before+100
  p.keyboard.press('Escape');p.wait_for_timeout(500);b=read(p);assert b['d']['trackFramePending']=='false' and b['d']['trackEnabled']=='false';return {'open':a,'scrollBefore':before,'scrollAfter':after,'returned':b}
 def detail(p,last=False,partial=False):
  auto(p);pause(p)
  if last:p.locator('[data-action=previous]').click()
  target='vibe-coding' if last else 'midjourney'
  p.locator('[data-action=auto]').click();p.wait_for_timeout(1000);wheel(p,300);p.wait_for_timeout(100 if partial else 25)
  point=p.evaluate('''id=>{const button=document.querySelector(`.ar-tool-card[data-tool-id="${id}"] button`),b=button.getBoundingClientRect(),r=document.querySelector('.ar-tool-rail').getBoundingClientRect(),c=button.closest('.ar-tool-card').getBoundingClientRect();const left=Math.max(b.left,r.left+4),right=Math.min(b.right,r.right-4),x=(left+right)/2,y=b.y+b.height/2;return{x,y,width:right-left,hit:document.elementFromPoint(x,y)?.closest('button')===button,partial:c.left<r.left||c.right>r.right}}''',target)
  assert point['width']>15 and point['hit'],point
  if partial:assert point['partial'],point
  p.mouse.move(point['x'],point['y']);p.mouse.click(point['x'],point['y']);p.wait_for_timeout(500);a=read(p);assert next(c for c in a['cards'] if c['id']==target)['expanded']=='true';assert a['focus']['action']=='detail' and a['focus']['tool']==target;assert a['d']['trackFramePending']=='false' and a['d']['detailMode']=='pinned';before=a['y'];over(p);p.mouse.wheel(0,100);p.wait_for_timeout(350);b=read(p);assert b['y']>before+70;return {'point':point,'expanded':a,'nativeReadingWheel':b}
 def keyboard(p):
  auto(p);wheel(p,160,5,25);p.locator('.ar-tool-card[data-tool-id=comfyui] button').focus();a=read(p);p.keyboard.press('Enter');p.wait_for_timeout(350);b=read(p);assert a['d']['trackSpeed']=='0.0000' and a['d']['trackFramePending']=='false';assert b['focus']['tool']=='comfyui' and next(c for c in b['cards'] if c['id']=='comfyui')['expanded']=='true';return {'focus':a,'enter':b}
 def guide(p):
  auto(p);p.locator('#tour-guide').click();p.wait_for_function('document.querySelector("#tour-host").dataset.guidePhase==="reading"');a=read(p);wheel(p,120);p.wait_for_timeout(200);b=read(p);assert p.locator('#tour-guide').get_attribute('aria-pressed')=='false' and b['d']['trackEnabled']=='true' and b['y']==a['y'];return {'before':a,'after':b}
 def contexts(p):
  auto(p);a=read(p);p.locator('#tour-motion').click();wheel(p,160,5,25);b=read(p);assert float(b['host']['sceneTime'])>float(a['host']['sceneTime']) and float(b['d']['trackSpeed'])>200;p.locator('#tour-motion').click();wheel(p,-160,5,25);c=read(p);assert c['d']['trackDirection']=='-1' and c['d']['trackEnabled']=='true';return {'before':a,'environmentPlay':b,'environmentPause':c}
 try:
  case('real-wheel-speed-direction-tail',primary,video=False)
  case('title-wheel-remains-page',lambda p:region(p,'.ar-tools-header'))
  case('filters-wheel-remains-page',lambda p:region(p,'.ar-filter-bar'))
  case('controls-wheel-remains-page',lambda p:region(p,'.ar-tool-controls'))
  case('continue-wheel-remains-page',lambda p:region(p,'.ar-continue-slot'))
  case('pointer-outside-page-return',exit_region)
  case('phone-native-page',fallback,size=(390,844));case('narrow-native-page',fallback,size=(320,740));case('large-font-native-page',lambda p:fallback(p,True),size=(800,600));case('reduced-native-page',fallback,reduced=True)
  case('wide-stable-manual-opt-in',stable,size=(1366,900));case('entrance-wheel-remains-page',entrance);case('horizontal-native-first-event',horizontal);case('fitting-category-remains-page',fit);case('overview-native-reading',overview)
  case('first-card-first-native-click',detail);case('last-card-first-native-click',lambda p:detail(p,True));case('partial-card-first-native-click',lambda p:detail(p,False,True));case('keyboard-focus-enter',keyboard)
  case('wheel-stops-guide-retains-card-choice',guide);case('scene-clock-independent',contexts)
  report['complete']=not failures
 finally:browser.close();report['browserClosed']=True;report['finishedAtShanghai']=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat();save(run/'browser.json',report)
print(json.dumps({'checks':len(report['checks']),'passed':len(report['checks'])-len(failures),'failures':failures},ensure_ascii=False));raise SystemExit(1 if failures else 0)
