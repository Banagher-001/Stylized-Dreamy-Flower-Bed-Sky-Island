from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import os,json,hashlib,traceback,shutil,sys
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent;run=OUT/(sys.argv[1] if len(sys.argv)>1 else 'regressions-1');run.mkdir(exist_ok=False)
s=json.loads((OUT/'services-started.json').read_text());os.environ.update(s['browserEnvironment']);origin=s['origin'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
report={'startedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'checks':[],'events':[],'complete':False,'physicalDevice':False};shutil.copy2(__file__,run/'verify-regressions.py.txt');save(run/'source-manifest.json',[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in [*[f for f in (ROOT/'src/tour').rglob('*') if f.is_file()],*(ROOT/'src/assets/tool-marks').glob('*.svg'),ROOT/'dist/index.html',*(ROOT/'dist/assets').glob('startTourPrototype*')]])
with sync_playwright() as play:
 browser=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist']);report['version']=browser.version
 def ready(p):p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"&&document.querySelector("#tour-host").dataset.renderState==="ready"',timeout=90000);p.wait_for_timeout(350)
 def go(p,h):
  p.evaluate('(h)=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})',h);p.wait_for_function('h=>Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-h)<.001&&document.querySelector("#tour-host").dataset.cameraState==="settled"',arg=h,timeout=20000);p.wait_for_timeout(250)
 def state(p):return p.evaluate('({mode:document.querySelector("main").dataset.readingMode,host:{...document.querySelector("#tour-host").dataset},tools:{...document.querySelector(".ar-tools-browser").dataset},railX:document.querySelector(".ar-tool-rail").scrollLeft,focus:document.activeElement?.dataset.action,locks:document.documentElement.className})')
 def case(name,fn,fixed=True):
  ctx=browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1);p=ctx.new_page();p.set_default_timeout(30000);begin=len(report['events']);entry={'id':name}
  p.on('pageerror',lambda e:report['events'].append({'case':name,'type':'pageerror','text':str(e)}));p.on('console',lambda m:report['events'].append({'case':name,'type':'console.error','text':m.text}) if m.type=='error' else None)
  try:
   p.goto(origin+('/?waterTime=2' if fixed else '/?birds=inspect'),wait_until='domcontentloaded');ready(p);data=fn(p);assert len(report['events'])==begin,report['events'][begin:]
   save(run/(name+'-data.json'),data);p.screenshot(path=str(run/(name+'.png')));entry.update(status='通过',data=name+'-data.json',screenshot=name+'.png')
  except Exception as e:
   entry.update(status='失败',error=str(e),traceback=traceback.format_exc())
   try:save(run/(name+'-failure.json'),state(p));p.screenshot(path=str(run/(name+'-failure.png')))
   except Exception:pass
  finally:report['checks'].append(entry);save(run/'browser.json',report);ctx.close()
 def resize_modal(p):
  go(p,3.34);p.locator('[data-action=next]').click();p.locator('[data-action=next]').click();p.wait_for_timeout(250);before=state(p)
  p.locator('[data-action=all]').click();p.wait_for_timeout(200);assert p.locator('.ar-overview-dialog').evaluate('(e)=>e.open')
  p.set_viewport_size({'width':390,'height':844});p.wait_for_timeout(450);assert p.locator('.ar-catalog .ar-tool-card').count()==22
  p.keyboard.press('Escape');p.wait_for_function('document.querySelector("main").dataset.readingMode==="stable"',timeout=20000);p.wait_for_timeout(450)
  after=state(p);assert after['tools']['activeId']==before['tools']['activeId'];assert 'tour-about-open' not in after['locks'] and after['focus']=='all';assert p.locator('[data-reading-station]').evaluate_all('(es)=>es.every(e=>!e.hidden&&!e.inert)')
  return {'before':before,'after':after}
 def native_wheel(p):
  p.locator('[data-stop=about]').click();p.wait_for_function('Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-1.74)<.001');p.wait_for_timeout(300)
  old=state(p);p.mouse.move(80,350);p.mouse.wheel(0,300);p.wait_for_function('Number(document.querySelector("#tour-host").dataset.displayH)>1.8');p.wait_for_timeout(300);after=state(p)
  mapped=p.evaluate('scrollY/(document.documentElement.scrollHeight-innerHeight)*12.3');assert abs(float(after['host']['displayH'])-mapped)<.001
  p.mouse.wheel(0,-300);p.wait_for_function('Number(document.querySelector("#tour-host").dataset.displayH)<1.8')
  return {'before':old,'after':after,'nativeScrollMappedH':mapped}
 def media(p):
  go(p,3.34);p.locator('[data-category=G5]').click();p.locator('[data-action=next]').click();p.wait_for_timeout(250);before=state(p)
  p.locator('[data-stop=films]').click();p.wait_for_function('document.querySelector("#tour-host").dataset.filmStation==="B1"&&document.querySelector("#tour-host").dataset.cameraState==="settled"');p.wait_for_timeout(250)
  p.locator('[data-film-station=B1] .film-image-button').click();p.wait_for_function('document.querySelector(".film-dialog").dataset.state==="ready"',timeout=30000)
  assert p.locator('.film-dialog img').evaluate('(e)=>e.complete&&e.naturalWidth>0');image=p.locator('.film-dialog img').get_attribute('src');p.keyboard.press('Escape');p.wait_for_timeout(450);assert not p.locator('dialog[open]').count()
  go(p,3.34);after=state(p);assert after['tools']['category']=='G5' and after['tools']['activeId']==before['tools']['activeId'];assert 'tour-media-open' not in after['locks']
  return {'image':image,'before':before,'after':after}
 def embedded(p,id):
  p.locator('#tour-layout-toggle').click();p.wait_for_function('document.querySelector("main").dataset.readingMode==="stable"');p.locator('.tour-reading-flow [data-flow-anchor=C2]').scroll_into_view_if_needed()
  p.locator(f'[data-project-select="{id}"]').click();p.wait_for_function('document.querySelector(".experiment-reading").dataset.coverState==="ready"',timeout=25000)
  p.locator('[data-project-tab=live]').click();p.wait_for_selector('iframe',state='attached');frame=p.locator('iframe').element_handle().content_frame()
  if id=='lawson':
   frame.wait_for_function('window.__LAWSON__?.ready===true',timeout=90000);frame.locator('#loader').wait_for(state='hidden',timeout=30000)
   before=frame.evaluate('({state:__LAWSON__.api.getState(),stats:__LAWSON__.api.getStats()})')
   frame.locator('#time-slider').press('Home');frame.wait_for_function('Math.abs(__LAWSON__.api.getStats().timeOfDay)<.02',timeout=45000)
   after=frame.evaluate('({state:__LAWSON__.api.getState(),stats:__LAWSON__.api.getStats()})');assert float(frame.locator('#time-slider').input_value())==0
  else:
   frame.wait_for_function('window.__bottleOcean?.ready===true&&getComputedStyle(document.querySelector("#loader")).display==="none"',timeout=120000)
   before=frame.evaluate('({...__bottleOcean.state})');frame.locator('[data-action=pause]').click();after=frame.evaluate('({...__bottleOcean.state})');assert after['paused'] is not before['paused']
   assert frame.evaluate('__bottleOcean.getDiagnostics().renderer.triangles')>1000
  p.wait_for_function('document.querySelector(".tour-project-dialog").dataset.embeddedState==="ready"',timeout=25000)
  p.screenshot(path=str(run/(id+'-open.png')));url=frame.url;entry=ROOT/'public/experiments'/('lawson' if id=='lawson' else 'bottle-ocean')/'index.html'
  p.locator('.tour-project-close').click();p.wait_for_function('document.querySelectorAll("iframe").length===0&&!document.querySelector(".tour-project-dialog").open',timeout=20000);p.wait_for_timeout(300)
  end=state(p);assert 'tour-project-open' not in end['locks'];assert p.locator('.about-pillar-reader').count()==1
  return {'url':url,'entrySHA256':sha(entry),'nativeInteraction':'time slider Home' if id=='lawson' else 'pause button','before':before,'after':after,'returned':end}
 def guide_flow(p):
  go(p,1.74);p.locator('#tour-guide').click();records=[]
  for id in ['A1','A2','A3']:
   p.wait_for_function("id=>{const d=document.querySelector('#tour-host').dataset;return (d.guideStation===id&&d.guidePhase==='reading')||d.guidePhase==='paused'||d.guideState==='blocked'}",arg=id,timeout=60000)
   record=p.locator('#tour-host').evaluate('(e)=>({station:e.dataset.guideStation,phase:e.dataset.guidePhase,state:e.dataset.guideState,seconds:e.dataset.guideReadSeconds,deadline:e.dataset.guideDeadline,reason:e.dataset.guideReason})')
   assert record['station']==id and record['phase']=='reading',record
   records.append(record)
  p.locator('#tour-guide').click();assert p.locator('#tour-guide').get_attribute('aria-pressed')=='false'
  return {'actualAutomaticReading':records,'timingModified':False}
 def environment(p):
  before=state(p);p.wait_for_timeout(650);after=state(p);assert float(after['host']['sceneTime'])>float(before['host']['sceneTime'])
  assert after['host']['orbStyle']=='lively' and after['host']['fountainStyle']=='refined'
  birds=json.loads(after['host']['birdState']);assert len(birds['poses'])==3
  p.locator('#tour-motion').click();p.wait_for_timeout(400);paused=state(p);p.wait_for_timeout(500);still=state(p);assert paused['host']['sceneTime']==still['host']['sceneTime']
  p.locator('#tour-motion').click();p.wait_for_timeout(450);resumed=state(p);assert float(resumed['host']['sceneTime'])>float(still['host']['sceneTime'])
  return {'runningBefore':before,'runningAfter':after,'paused':paused,'resumed':resumed,'birdCount':3}
 try:
  case('modal-resize-to-phone',resize_modal)
  case('native-scroll-navigation',native_wheel)
  case('film-open-return',media)
  case('lawson-open-interact-return',lambda p:embedded(p,'lawson'))
  case('bottle-open-interact-return',lambda p:embedded(p,'bottle-ocean'))
  case('environment-play-pause-resume',environment,False)
  case('automatic-A1-A2-A3',guide_flow)
  report['complete']=all(c['status']=='通过' for c in report['checks'])
 finally:browser.close();report['cleanup']={'browserClosed':True,'sharedServicesStopped':False};save(run/'browser.json',report)
print(json.dumps({'checks':len(report['checks']),'passed':sum(c['status']=='通过' for c in report['checks']),'complete':report['complete'],'failures':[{'id':c['id'],'error':c.get('error')} for c in report['checks'] if c['status']!='通过']},ensure_ascii=False))
if not report['complete']:raise SystemExit(1)
