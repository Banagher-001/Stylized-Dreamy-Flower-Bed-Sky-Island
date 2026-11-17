from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import os,json,argparse,traceback,ast,hashlib,shutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('run');ap.add_argument('--only',nargs='*');args=ap.parse_args();run=OUT/args.run;run.mkdir(exist_ok=False)
s=json.loads((OUT/'services-started.json').read_text());os.environ.update(s['browserEnvironment'])
SAMPLE=next(ast.literal_eval(n.value) for n in ast.parse((OUT/'inspect-track.py').read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SAMPLE' for t in n.targets))
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
sources=[p for p in (ROOT/'src/tour').rglob('*') if p.is_file()]+list((ROOT/'src/assets/tool-marks').glob('*.svg'))+[ROOT/'dist/index.html']+list((ROOT/'dist/assets').glob('startTourPrototype*'))
save(run/'source-manifest.json',[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources]);shutil.copy2(__file__,run/'verify-track.py.txt');shutil.copy2(OUT/'inspect-track.py',run/'inspect-track.py.txt')
content=json.loads((ROOT/'src/tour/about-refresh/content.ts').read_text().split('export const aboutRefreshContent = ',1)[1].split(' as const satisfies AboutContent;',1)[0]);order=[v['id'] for v in sorted(content['cards'],key=lambda v:v['recommendationOrder'])]
report={'startedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'complete':False,'checks':[],'events':[],'clockModified':False,'physicalDevice':False};fails=[]
with sync_playwright() as play:
 browser=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist']);report['version']=browser.version
 def snap(p):return p.evaluate(SAMPLE)
 def go(p,h=3.34):
  if p.locator('main').get_attribute('data-reading-mode')=='stable':p.locator('.tour-reading-flow [data-flow-anchor=A3]').scroll_into_view_if_needed()
  else:p.evaluate('h=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})',h)
 def auto(p):
  go(p);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.trackState==="running"&&document.querySelector(".ar-tools-browser").dataset.trackMode==="program"',timeout=25000)
 def pause(p):
  if p.locator('[data-action=auto]').get_attribute('aria-pressed')=='true':p.locator('[data-action=auto]').click()
 def clean(p):
  m=snap(p);assert m['overflow']<=1 and not m['duplicates'];ids=[c['id'] for c in m['cards']];assert len(ids)==len(set(ids))
  assert p.locator('.ar-card-foreground .ar-tool-card').count()==0
  if m['root']['trackState']!='running':assert m['root']['trackFramePending']=='false',m['root']
  if m['root']['mode']=='cards' and m['root']['category']=='all':assert ids==order,ids
  return m
 def category(p,id):
  if p.locator(f'.ar-category-buttons [data-category={id}]').is_visible():p.locator(f'.ar-category-buttons [data-category={id}]').click()
  else:p.locator('.ar-category-select select').select_option(id)
 def case(name,fn,size=(1440,900),reduced=False,large=False):
  if args.only and name not in args.only:return
  ctx=browser.new_context(viewport={'width':size[0],'height':size[1]},device_scale_factor=1,reduced_motion='reduce' if reduced else 'no-preference');p=ctx.new_page();p.set_default_timeout(20000);ev=[];entry={'id':name,'viewport':list(size),'status':'失败'}
  p.on('pageerror',lambda e:ev.append(str(e)))
  try:
   p.goto(s['origin']+'/?waterTime=2',wait_until='domcontentloaded');p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=90000);p.wait_for_timeout(120)
   if large:p.evaluate('document.documentElement.style.fontSize="200%"');p.wait_for_timeout(500)
   before=snap(p);data=fn(p) or {};p.wait_for_timeout(60);after=clean(p);assert not ev,ev
   save(run/(name+'-data.json'),{'before':before,'after':after,'details':data});p.screenshot(path=str(run/(name+'.png')));entry.update(status='通过',data=name+'-data.json',screenshot=name+'.png')
  except Exception as error:
   fails.append(name);entry.update(error=str(error),traceback=traceback.format_exc())
   try:save(run/(name+'-data.json'),{'after':snap(p)});p.screenshot(path=str(run/(name+'-failure.png')))
   except Exception:pass
  finally:report['checks'].append(entry);report['events'].extend(ev);save(run/'browser.json',report);ctx.close()
 def timing(p):
  assert snap(p)['root']['trackMode']=='native';auto(p);a=snap(p);assert a['root']['entranceReason']=='completed' and float(a['root']['trackDistance'])<1
  p.wait_for_timeout(350);b=snap(p);assert float(b['root']['trackDistance'])<1
  p.wait_for_timeout(850);c=snap(p);assert float(c['root']['trackDistance'])>5 and c['host']['sceneTime']=='2.000000'
  return {'ready':a,'hold':b,'moving':c}
 def velocity(p):
  auto(p);p.wait_for_timeout(1100)
  measure='() => new Promise(resolve => requestAnimationFrame(now => resolve({now,distance:Number(document.querySelector(".ar-tools-browser").dataset.trackDistance)})))'
  a=p.evaluate(measure);p.wait_for_timeout(2200);b=p.evaluate(measure);v=(b['distance']-a['distance'])/((b['now']-a['now'])/1000);assert abs(v-28)<1,v
  pause(p);return {'measuredPXPerSecond':v,'start':a,'end':b}
 def frozen(p):
  auto(p);p.wait_for_timeout(1300);pause(p);a=snap(p);p.wait_for_timeout(450);b=snap(p)
  assert a['root']['trackOffset']==b['root']['trackOffset'] and b['root']['trackFramePending']=='false'
  assert all(x['front']==y['front'] for x,y in zip(a['cards'],b['cards']))
  p.locator('[data-action=auto]').focus();p.keyboard.press('Enter');p.wait_for_timeout(550);early=snap(p)
  def z(card):
   values=[float(v) for v in card['position'].split('(',1)[1].rstrip(')').split(',')];return values[14] if len(values)==16 else 0
  frozenCard=next(c for c in b['cards'] if c['id']=='blender');earlyCard=next(c for c in early['cards'] if c['id']=='blender');assert abs(z(frozenCard)-z(earlyCard))<2,(frozenCard['position'],earlyCard['position'])
  p.wait_for_timeout(450);c=snap(p);assert float(c['root']['trackDistance'])>float(b['root']['trackDistance'])+3
  return {'paused':a,'still':b,'resumeEarly':early,'resumed':c}
 def toggles(p):
  auto(p)
  for _ in range(5):p.locator('[data-action=auto]').click()
  a=snap(p);assert a['root']['trackEnabled']=='false';p.wait_for_timeout(300);assert snap(p)['root']['trackOffset']==a['root']['trackOffset']
 def wrap_buttons(p):
  auto(p);p.locator('[data-action=previous]').click();a=snap(p);assert a['root']['activeId']=='vibe-coding' and a['root']['trackState']=='paused'
  p.locator('[data-action=next]').focus();p.keyboard.press('Enter');b=snap(p);assert b['root']['activeId']=='midjourney' and b['root']['trackState']=='paused';return {'last':a,'first':b}
 def overview(p):
  auto(p);p.wait_for_timeout(1450);pause(p);a=snap(p);p.locator('[data-action=all]').click();p.wait_for_timeout(150)
  assert p.locator('.ar-catalog .ar-tool-card').count()==22 and p.locator('.ar-track-stage').count()==0
  p.keyboard.press('Escape');p.wait_for_timeout(350);b=snap(p);assert b['root']['trackMode']=='program' and b['root']['trackEnabled']=='false',b['root']
  assert abs(float(a['root']['trackOffset'])-float(b['root']['trackOffset']))<.1,(a['root'],b['root'])
  assert a['root']['activeId']==b['root']['activeId'] and b['focus']['action']=='all'
  assert max(abs(x-y) for c,d in zip(a['cards'],b['cards']) for x,y in zip(c['front'],d['front']))<.2
  return {'before':a,'after':b}
 def detail(p):
  auto(p);p.wait_for_timeout(1200);box=p.locator('.ar-tool-card[data-tool-id=comfyui] button').bounding_box();p.mouse.click(box['x']+box['width']/2,box['y']+box['height']/2);p.wait_for_timeout(100);a=snap(p)
  assert a['root']['trackMode']=='native' and a['root']['trackEnabled']=='false'
  assert p.locator('.ar-tool-card[data-tool-id=comfyui] button').get_attribute('aria-expanded')=='true'
  assert p.locator('.ar-tool-card[data-tool-id=comfyui] button').evaluate('e=>e===document.activeElement')
  p.keyboard.press('Enter');assert p.locator('.ar-tool-card[data-tool-id=comfyui] button').get_attribute('aria-expanded')=='false';p.wait_for_timeout(120);assert snap(p)['root']['trackState']!='running'
  return a
 def partial_detail(p):
  auto(p);p.wait_for_timeout(1100);button=p.locator('.ar-tool-card[data-tool-id=blender] button');box=button.bounding_box();rail=p.locator('.ar-tool-rail').bounding_box();x=min(box['x']+box['width']/2,rail['x']+rail['width']-8);p.mouse.click(x,box['y']+box['height']/2);p.wait_for_timeout(250)
  assert button.get_attribute('aria-expanded')=='true';assert button.evaluate('e=>e===document.activeElement');assert snap(p)['root']['trackEnabled']=='false'
 def groups(p):
  auto(p);data=[]
  for group in content['categories']:
   category(p,group['id']);p.wait_for_timeout(80);m=snap(p);assert [c['id'] for c in m['cards']]==group['cardIds'];assert m['root']['trackEnabled']=='false'
   if len(group['cardIds'])<=3:assert m['button']['hidden']
   else:
    assert not m['button']['hidden'];p.locator('[data-action=auto]').click();p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.trackMode==="program"');pause(p)
   data.append({'category':group['id'],'ids':[c['id'] for c in m['cards']],'button':m['button']})
  return data
 def horizontal(p):
  auto(p);p.wait_for_timeout(1500);a=snap(p);p.mouse.move(650,480);p.mouse.wheel(220,0);p.wait_for_timeout(250);b=snap(p)
  assert b['root']['trackMode']=='native' and b['root']['trackEnabled']=='false';assert b['rail']['scrollLeft']>float(a['root']['trackOffset'])+100,(a['root'],b['rail']);return {'before':a,'after':b}
 def vertical(p):
  auto(p);a=p.evaluate('scrollY');p.mouse.move(650,480);p.mouse.wheel(0,850);p.wait_for_timeout(650);b=snap(p);assert p.evaluate('scrollY')>a+300
  assert b['root']['trackState']!='running' and b['root']['trackFramePending']=='false';return b
 def returns(p,manual=False):
  auto(p);p.wait_for_timeout(1200)
  if manual:pause(p)
  go(p,2.54);p.wait_for_function('document.querySelector("#tour-host").dataset.readingStation==="A2"&&document.querySelector("#tour-host").dataset.cameraState==="settled"');a=snap(p);p.wait_for_timeout(250);assert snap(p)['root']['trackOffset']==a['root']['trackOffset']
  go(p);p.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"&&document.querySelector("#tour-host").dataset.readingStation==="A3"');p.wait_for_timeout(150);b=snap(p);advance=float(b['root']['trackOffset'])-float(a['root']['trackOffset']);assert -.001<=advance<=28*(b['now']-a['now'])/1000+1,(a['root'],b['root'])
  p.wait_for_timeout(1300);c=snap(p)
  if manual:assert c['root']['trackOffset']==b['root']['trackOffset'] and c['root']['trackEnabled']=='false'
  else:assert float(c['root']['trackDistance'])>float(b['root']['trackDistance'])+5
  assert c['root']['entrancePlays']=='1';return {'away':a,'return':b,'later':c}
 def resize(p,phone=False):
  auto(p);p.wait_for_timeout(1200);pause(p);a=snap(p);p.set_viewport_size({'width':390 if phone else 1920,'height':844 if phone else 1080});p.wait_for_timeout(700);b=snap(p)
  if phone:
   assert b['root']['trackMode']=='native' and b['button']['hidden'];p.locator('.tour-reading-flow [data-flow-anchor=A3]').scroll_into_view_if_needed();p.locator('[data-action=next]').click();assert snap(p)['root']['activeId']=='comfyui'
   p.set_viewport_size({'width':1440,'height':900});p.wait_for_timeout(700);assert snap(p)['root']['activeId']=='comfyui';p.evaluate('()=>{const b=document.querySelector(".ar-tool-controls").getBoundingClientRect();scrollBy(0,b.bottom-innerHeight+25)}');p.wait_for_timeout(100);p.locator('[data-action=auto]').click();p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.trackMode==="program"');assert snap(p)['root']['activeId']=='comfyui';pause(p)
  else:
   assert b['root']['trackMode']=='program' and b['root']['trackEnabled']=='false';ratioA=float(a['root']['trackOffset'])/256;ratioB=float(b['root']['trackOffset'])/264;assert abs(ratioA-ratioB)<.01,(ratioA,ratioB)
  return {'before':a,'after':b}
 def stable(p):
  auto(p);p.locator('#tour-layout-toggle').click();p.wait_for_function('document.querySelector("main").dataset.readingMode==="stable"');p.wait_for_timeout(350);a=snap(p);assert a['root']['trackEnabled']=='false' and a['root']['trackMode']=='native';return a
 def fallback(p):
  go(p);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceReady==="true"');p.wait_for_timeout(300);m=snap(p);assert m['root']['trackMode']=='native' and m['root']['trackState']!='running' and m['button']['hidden']
  p.locator('[data-action=next]').click();assert snap(p)['root']['activeId']=='comfyui';p.locator('.ar-tool-card[data-tool-id=comfyui] button').click();assert p.locator('.ar-tool-card[data-tool-id=comfyui] button').get_attribute('aria-expanded')=='true'
 def stable_opt_in(p):
  go(p);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceReady==="true"')
  if p.locator('main').get_attribute('data-reading-mode')!='stable':p.locator('#tour-layout-toggle').click();p.wait_for_timeout(200)
  p.evaluate('()=>{const b=document.querySelector(".ar-tool-controls").getBoundingClientRect();scrollBy(0,b.bottom-innerHeight+20)}');p.wait_for_timeout(150);assert p.locator('[data-action=auto]').get_attribute('aria-pressed')=='false';p.locator('[data-action=auto]').click();p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.trackMode==="program"');p.wait_for_timeout(1100);assert float(snap(p)['root']['trackDistance'])>0;pause(p)
 def hidden(p):
  auto(p);p.wait_for_timeout(1100);p.evaluate('Object.defineProperty(document,"hidden",{configurable:true,get:()=>true});document.dispatchEvent(new Event("visibilitychange"))');a=snap(p);p.wait_for_timeout(250);p.evaluate('delete document.hidden;document.dispatchEvent(new Event("visibilitychange"))');p.wait_for_timeout(700);b=snap(p);assert a['root']['trackOffset']==b['root']['trackOffset'] and b['root']['trackEnabled']=='false';return {'hidden':a,'returned':b}
 def reduced_change(p):
  auto(p);p.emulate_media(reduced_motion='reduce');p.wait_for_timeout(400);a=snap(p);assert a['root']['trackMode']=='native' and a['root']['trackEnabled']=='false' and a['button']['hidden'];return a
 def focus(p):
  auto(p);p.wait_for_timeout(1100);p.locator('.ar-tool-card[data-tool-id=comfyui] button').focus();a=snap(p);p.wait_for_timeout(350);b=snap(p);assert a['root']['trackOffset']==b['root']['trackOffset'] and b['focus']['tool']=='comfyui';return b
 def hover(p):
  auto(p);p.wait_for_timeout(1000);a=snap(p);p.mouse.move(650,480);p.wait_for_timeout(900);b=snap(p);assert b['root']['trackState']=='running' and float(b['root']['trackDistance'])>float(a['root']['trackDistance'])+10;pause(p)
 def environment(p):
  auto(p);p.wait_for_timeout(1000);a=snap(p);p.locator('#tour-motion').click();p.wait_for_timeout(550);b=snap(p);assert float(b['host']['sceneTime'])>float(a['host']['sceneTime']);p.locator('#tour-motion').click();p.wait_for_timeout(550);c=snap(p);assert float(c['root']['trackDistance'])>float(b['root']['trackDistance'])+5 and c['root']['trackEnabled']=='true';pause(p);return {'before':a,'playing':b,'environmentPaused':c}
 def guide(p):
  auto(p);p.locator('#tour-guide').click();p.wait_for_function('document.querySelector("#tour-host").dataset.guidePhase==="reading"');a=snap(p);p.wait_for_timeout(1300);b=snap(p);assert b['host']['guidePhase']=='reading' and b['root']['trackState']=='running'
  p.locator('[data-action=auto]').click();assert p.locator('#tour-host').get_attribute('data-guide-deadline')=='';p.locator('[data-action=auto]').click();p.wait_for_timeout(200);assert p.locator('#tour-guide').get_attribute('aria-pressed')=='false';pause(p);return {'before':a,'during':b}
 try:
  case('entrance-hold-start',timing);case('measured-base-speed',velocity);case('pause-native-enter-resume',frozen);case('rapid-toggle-last-choice',toggles)
  case('manual-first-last-wrap',wrap_buttons);case('all-tools-exact-return',overview);case('detail-native-handoff',detail);case('partial-card-first-click',partial_detail);case('seven-categories',groups)
  case('horizontal-native-first-gesture',horizontal);case('vertical-wheel-still-navigates',vertical);case('leave-return-resumes',returns);case('manual-pause-survives-return',lambda p:returns(p,True))
  case('resize-anchor-ratio',resize);case('resize-to-phone',lambda p:resize(p,True));case('switch-stable-stays-manual',stable)
  case('phone-native',fallback,size=(390,844));case('narrow-native',fallback,size=(320,740));case('large-font-native',fallback,size=(800,600),large=True);case('reduced-native',fallback,reduced=True)
  case('wide-stable-opt-in',stable_opt_in,size=(1366,900));case('simulated-hidden-no-catchup',hidden);case('reduced-change-stops',reduced_change)
  case('keyboard-focus-freezes',focus);case('pointer-enter-keeps-base-speed',hover);case('environment-independent',environment);case('guide-independent',guide)
  report['complete']=True
 finally:browser.close();report['browserClosed']=True;report['finishedAtShanghai']=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat();save(run/'browser.json',report)
print(json.dumps({'checks':len(report['checks']),'passed':len(report['checks'])-len(fails),'failures':fails},ensure_ascii=False));raise SystemExit(1 if fails else 0)
