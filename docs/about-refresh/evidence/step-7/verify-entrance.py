from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import os,json,argparse,traceback,ast,hashlib,shutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('run');ap.add_argument('--only');args=ap.parse_args();run=OUT/args.run;run.mkdir(exist_ok=False)
s=json.loads((OUT/'services-started.json').read_text());os.environ.update(s['browserEnvironment'])
constants={}
for n in ast.parse((OUT/'inspect-entrance.py').read_text()).body:
 if isinstance(n,ast.Assign) and isinstance(n.value,ast.Constant):
  for target in n.targets:
   if isinstance(target,ast.Name) and target.id in ['INIT','SAMPLE']:constants[target.id]=n.value.value
shutil.copy2(__file__,run/'verify-entrance.py.txt');shutil.copy2(OUT/'inspect-entrance.py',run/'inspect-entrance.py.txt')
sources=[p for p in (ROOT/'src/tour').rglob('*') if p.is_file()]+list((ROOT/'src/assets/tool-marks').glob('*.svg'))+[ROOT/'dist/index.html']+list((ROOT/'dist/assets').glob('startTourPrototype*'))
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
save(run/'source-manifest.json',[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources])
report={'startedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'complete':False,'checks':[],'errors':[],'physicalDevice':False,'clockModified':False};failures=[]
with sync_playwright() as play:
 browser=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist']);report['version']=browser.version
 def ready(p):p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"&&document.querySelector("#tour-host").dataset.renderState==="ready"',timeout=90000);p.wait_for_timeout(150)
 def raw_go(p,h):p.evaluate('h=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})',h)
 def enter(p):raw_go(p,3.34);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entrance==="playing"',timeout=20000)
 def settled(p):p.wait_for_function('["ready","cancelled"].includes(document.querySelector(".ar-tools-browser").dataset.entrance)',timeout=10000);p.wait_for_timeout(80)
 def snap(p):return p.evaluate(constants['SAMPLE'])
 def invariant(p):
  m=snap(p);b=m['browser'];assert b['entranceReady']=='true' and b['entranceFramePending']=='false',b
  assert m['foreground']==0 and not m['duplicateIDs'],m
  assert all(c['inSlot'] and not c['inert'] and not c['frontInert'] and c['pose']=='0,0' for c in m['cards']),m['cards']
  assert p.locator('.ar-tools-browser [data-entry-card]').count()==0
  assert p.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
  assert p.locator('.ar-tools-browser .ar-tool-card').count()==22 if b['category']=='all' else True
  for c in m['cards']:
   assert abs(c['front']['left']-c['box']['left'])<.1 and abs(c['front']['top']-c['box']['top'])<.1
  return m
 def case(name,action,size=(1440,900),reduced=False,large=False):
  if args.only and name!=args.only:return
  context=browser.new_context(viewport={'width':size[0],'height':size[1]},reduced_motion='reduce' if reduced else 'no-preference',device_scale_factor=1);context.add_init_script(constants['INIT']);p=context.new_page();p.set_default_timeout(20000);errors=[]
  p.on('pageerror',lambda e:errors.append(str(e)))
  entry={'id':name,'viewport':list(size),'status':'失败'}
  try:
   p.goto(s['origin']+'/?waterTime=2',wait_until='domcontentloaded');ready(p)
   if large:p.evaluate('document.documentElement.style.fontSize="200%"');p.wait_for_timeout(500)
   before=snap(p);assert before['browser']['entrance']=='waiting' and before['browser']['entrancePlays']=='0',before['browser']
   action(p);p.wait_for_timeout(80);assert not errors,errors
   data={'before':before,'after':snap(p),'motion':p.evaluate('window.__entranceEvidence')};save(run/(name+'-data.json'),data);p.screenshot(path=str(run/(name+'.png')))
   entry.update(status='通过',data=name+'-data.json',screenshot=name+'.png')
  except Exception as e:
   entry.update(error=str(e),traceback=traceback.format_exc());failures.append(name)
   try:save(run/(name+'-data.json'),{'after':snap(p),'motion':p.evaluate('window.__entranceEvidence')});p.screenshot(path=str(run/(name+'-failure.png')))
   except Exception:pass
  finally:report['checks'].append(entry);report['errors'].extend(errors);save(run/'browser.json',report);context.close()
 def geometry(p):
  enter(p);flying=snap(p);assert flying['foreground']==1 and all(not c['inSlot'] and c['inert'] for c in flying['cards'])
  settled(p);m=invariant(p);b=m['browser'];assert b['entranceReason']=='completed' and b['entrancePlays']=='1',b
  assert 1450<=float(b['entranceFinishedAt'])-float(b['entranceStartedAt'])<2000,b
  evidence=p.evaluate('window.__entranceEvidence');first=next(f for f in evidence['phases'] if f['phase']=='playing')
  assert [c['id'] for c in first['cards']]==['midjourney','comfyui','kling','blender']
  assert all(max(r[2] for r in c['faces']) < -32 or min(r[0] for r in c['faces'])>m['main'].get('viewport',0)+p.viewport_size['width']+32 for c in first['cards'])
  for c in first['cards']:
   last=next(v for v in m['cards'] if v['id']==c['id'])
   assert max(abs(a-b) for a,b in zip(c['slot'],[last['slot']['left'],last['slot']['top'],last['slot']['right'],last['slot']['bottom']]))<.2
  assert any(c['frontInert'] and abs(float(c['pose'].split(',')[1]))>90 and max(r[2] for r in c['faces'])>m['rail']['left'] and min(r[0] for r in c['faces'])<m['rail']['right'] for f in evidence['frames'] for c in f['cards'])
  positions=[c['position'] for f in evidence['frames'] for c in f['cards']];assert len(set(positions))>15
 def return_once(p):
  enter(p);settled(p)
  for h in [2.54,3.34,4.95,3.34]:
   raw_go(p,h);p.wait_for_function('h=>Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-h)<.001',arg=h);p.wait_for_timeout(100)
  assert invariant(p)['browser']['entrancePlays']=='1'
 def resize_probe(p):
  p.set_viewport_size({'width':1450,'height':900});p.wait_for_timeout(200);p.set_viewport_size({'width':1440,'height':900});p.wait_for_timeout(200)
  assert snap(p)['browser']['entrance']=='waiting';enter(p);settled(p);assert invariant(p)['browser']['entranceReason']=='completed'
 def category(p):
  enter(p);p.locator('.ar-category-buttons [data-category=G5]').click();p.wait_for_timeout(80)
  b=invariant(p)['browser'];assert b['category']=='G5' and b['activeId']=='substance-painter' and b['entranceReason'] in ['interaction','focus'],b
 def next_key(p):
  enter(p);p.locator('[data-action=next]').focus();p.keyboard.press('Enter');p.wait_for_timeout(100)
  assert invariant(p)['browser']['activeId']=='comfyui'
 def all_tools(p):
  enter(p);p.locator('[data-action=all]').click();p.wait_for_timeout(100)
  assert p.locator('.ar-overview-dialog').evaluate('(d)=>d.open') and p.locator('.ar-catalog .ar-tool-card').count()==22
  assert p.locator('.ar-card-foreground .ar-tool-card').count()==0
  p.keyboard.press('Escape');p.wait_for_timeout(150);invariant(p)
 def leave(p,button=False):
  enter(p)
  if button:p.locator('[data-action=continue]').click()
  else:raw_go(p,4.95)
  p.wait_for_function('document.querySelector("#tour-host").dataset.filmStation==="B1"&&document.querySelector("#tour-host").dataset.cameraState==="settled"');p.wait_for_timeout(100)
  assert invariant(p)['browser']['entrance']=='cancelled'
  raw_go(p,3.34);p.wait_for_function('document.querySelector("#tour-host").dataset.readingStation==="A3"');assert invariant(p)['browser']['entrancePlays']=='1'
 def resize_mid(p):
  enter(p);p.set_viewport_size({'width':390,'height':844});p.wait_for_function('document.querySelector("main").dataset.readingMode==="stable"');p.wait_for_timeout(300);invariant(p)
 def mode_mid(p):
  enter(p);p.locator('#tour-layout-toggle').click();p.wait_for_function('document.querySelector("main").dataset.readingMode==="stable"');invariant(p)
 def static(p):
  p.locator('.tour-reading-flow [data-flow-anchor=A3]').scroll_into_view_if_needed();settled(p);m=invariant(p);assert m['browser']['entrancePlays']=='0' and m['browser']['entranceReason']=='static-reading',m['browser']
  p.locator('[data-action=next]').click();assert snap(p)['browser']['activeId']=='comfyui';p.locator('.ar-tool-card[data-tool-id=comfyui] button').click();assert p.locator('.ar-tool-card[data-tool-id=comfyui] button').get_attribute('aria-expanded')=='true'
 def hidden(p):
  enter(p)
  # Explicitly exercise the lifecycle branch; this is a simulated visibility event.
  p.evaluate('Object.defineProperty(document,"hidden",{configurable:true,get:()=>true});document.dispatchEvent(new Event("visibilitychange"))')
  m=invariant(p);assert m['browser']['entranceReason']=='page-hidden';p.evaluate('delete document.hidden;document.dispatchEvent(new Event("visibilitychange"))');p.wait_for_timeout(200);assert snap(p)['browser']['entrancePlays']=='1'
 def reduced_mid(p):
  enter(p);p.emulate_media(reduced_motion='reduce');p.wait_for_timeout(250);invariant(p)
 def guide_gate(p):
  # Start the real guide at A2; inspect its real A3 arrival and reading deadline.
  raw_go(p,2.54);p.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"');p.locator('#tour-guide').click()
  p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entrance==="playing"',timeout=45000)
  d=p.locator('#tour-host').evaluate('(e)=>({...e.dataset})');assert d['guideStation']=='A3' and d['guidePhase'] in ['moving','arriving'] and not d['guideDeadline'],d
  settled(p);p.wait_for_function('document.querySelector("#tour-host").dataset.guideStation==="A3"&&document.querySelector("#tour-host").dataset.guidePhase==="reading"',timeout=15000)
  m=invariant(p);assert float(m['host']['guideReadyAt'])>=float(m['browser']['entranceFinishedAt'])
  p.locator('.ar-category-buttons [data-category=G1]').click();assert p.locator('#tour-host').get_attribute('data-guide-deadline')=='' and p.locator('#tour-guide').get_attribute('aria-pressed')=='false'
 def prepare_leave(p):
  raw_go(p,2.94);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entrance==="preparing"');raw_go(p,2.54);p.wait_for_function('document.querySelector("#tour-host").dataset.readingStation==="A2"');assert snap(p)['browser']['entrance']=='waiting';enter(p);settled(p);invariant(p)
 def resource_fallback(p):
  raw_go(p,2.94);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entrance==="preparing"')
  # Delayed readiness is injected into an existing image, with no source changes.
  p.evaluate('Object.defineProperty(document.querySelector(".ar-tool-card[data-tool-id=midjourney] img"),"complete",{configurable:true,get:()=>false})')
  raw_go(p,3.34);settled(p);m=invariant(p);assert m['browser']['entranceReason']=='resource-fallback' and m['browser']['entrancePlays']=='0';p.locator('#tour-guide').click();p.wait_for_function('document.querySelector("#tour-host").dataset.guideStation==="A3"&&document.querySelector("#tour-host").dataset.guidePhase==="reading"',timeout=15000);assert float(p.locator('#tour-host').get_attribute('data-guide-ready-at'))>=float(m['browser']['entranceFinishedAt']);p.locator('#tour-guide').click();p.evaluate('delete document.querySelector(".ar-tool-card[data-tool-id=midjourney] img").complete')
 try:
  case('four-card-geometry',geometry);case('large-four-card-geometry',geometry,size=(1920,1080))
  case('return-does-not-replay',return_once);case('capacity-probes-do-not-trigger',resize_probe)
  case('category-first-click',category);case('next-native-enter',next_key);case('overview-first-click-escape',all_tools)
  case('scroll-away-cancel',leave);case('continue-first-click',lambda p:leave(p,True))
  case('resize-during-flight',resize_mid);case('reading-mode-during-flight',mode_mid)
  case('phone-static',static,size=(390,844));case('narrow-static',static,size=(320,740));case('laptop-static',static,size=(1366,768));case('large-font-static',static,size=(800,600),large=True);case('reduced-static',static,reduced=True)
  case('simulated-page-hidden',hidden);case('reduced-change-during-flight',reduced_mid)
  case('prepare-leave-preserves-first-flight',prepare_leave);case('resource-readiness-fallback',resource_fallback)
  case('automatic-guide-waits-for-settlement',guide_gate)
  report['complete']=True
 finally:
  browser.close();report['browserClosed']=True;report['finishedAtShanghai']=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat();save(run/'browser.json',report)
print(json.dumps({'passed':len(report['checks'])-len(failures),'total':len(report['checks']),'failures':failures},ensure_ascii=False))
raise SystemExit(1 if failures else 0)
