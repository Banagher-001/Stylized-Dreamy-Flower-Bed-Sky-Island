from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse,os,json,hashlib,traceback,shutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--suite',choices=['smoke','full'],default='full');args=ap.parse_args();run=OUT/args.run;run.mkdir(exist_ok=False)
s=json.loads((OUT/'services-started.json').read_text());os.environ.update(s['browserEnvironment']);origin=s['origin'];now=lambda:datetime.now(ZoneInfo('Asia/Shanghai')).isoformat();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
sources=[p for p in (ROOT/'src/tour').rglob('*') if p.is_file()]+list((ROOT/'src/assets/tool-marks').glob('*.svg'))+[ROOT/'dist/index.html']+list((ROOT/'dist/assets').glob('startTourPrototype*'))
save(run/'source-manifest.json',[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sources]);shutil.copy2(__file__,run/'verify-main.py.txt')
report={'startedAtShanghai':now(),'origin':origin,'checks':[],'events':[],'externalAttempts':[],'physicalDevice':False,'clockModified':False,'complete':False};failures=[]
SNAP=r'''() => {const root=document.querySelector('.about-pillar-reader'),host=document.querySelector('#tour-host'),main=document.querySelector('main');const box=e=>{const r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height,right:r.right,bottom:r.bottom}};const shown=e=>!!e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden';const rail=root.querySelector('.ar-tool-rail');return {viewport:[innerWidth,innerHeight],documentWidth:document.documentElement.scrollWidth,scrollY,main:{...main.dataset},host:{...host.dataset},root:{...root.dataset},bounds:box(root),stations:[...root.querySelectorAll('[data-reading-station]')].map(e=>({id:e.dataset.readingStation,hidden:e.hidden,inert:e.inert,aria:e.getAttribute('aria-hidden'),visible:shown(e),bounds:box(e)})),anchors:[...document.querySelectorAll('.tour-reading-flow [data-flow-anchor]')].map(e=>e.dataset.flowAnchor),toolAnchors:document.querySelectorAll('.ar-tool-card[data-flow-anchor]').length,toolBrowser:{...document.querySelector('.ar-tools-browser').dataset},rail:box(rail),railX:rail.scrollLeft,cards:[...root.querySelectorAll('.ar-tool-rail .ar-tool-card')].map(e=>({id:e.dataset.toolId,expanded:e.dataset.expanded,bounds:box(e),texts:[...e.querySelectorAll('h3,p,li,button')].filter(shown).map(t=>({text:t.textContent,bounds:box(t),overflow:t.scrollHeight-t.clientHeight}))})),focus:{tag:document.activeElement?.tagName,action:document.activeElement?.dataset.action,id:document.activeElement?.id},dialogs:[...document.querySelectorAll('dialog[open]')].map(e=>e.className),aboutLock:document.documentElement.classList.contains('tour-about-open')};}'''
positions={'A1':1.74,'A2':2.54,'A3':3.34,'B1':4.95,'C2':10.14}
with sync_playwright() as play:
 browser=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist'])
 report['version']=browser.version
 def settle(p,ms=240):p.wait_for_timeout(ms)
 def go(p,id):
  if p.locator('main').get_attribute('data-reading-mode')=='stable':p.locator(f'.tour-reading-flow [data-flow-anchor={id}]').scroll_into_view_if_needed();settle(p)
  else:
   p.evaluate('(h)=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})',positions[id]);p.wait_for_function('h=>Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-h)<.001&&document.querySelector("#tour-host").dataset.cameraState==="settled"',arg=positions[id],timeout=20000);settle(p)
 def invariants(p):
  m=p.evaluate(SNAP);assert m['host']['renderState']=='ready';assert m['documentWidth']<=m['viewport'][0]+1,(m['documentWidth'],m['viewport'])
  assert p.locator('.about-pillar-reader').count()==1 and p.locator('.pillar-reading').count()==0
  assert m['anchors']==['opening','A1','A2','A3','B1','B2','B3','B4','C1','C2','C3','water','ending'],m['anchors'];assert m['toolAnchors']==0
  if m['main']['readingMode']=='stable':assert all(not e['hidden'] and not e['inert'] and e['aria']=='false' for e in m['stations']),m['stations']
  elif m['host']['readingStation']:
   selected=[e for e in m['stations'] if not e['hidden']];assert len(selected)==1 and selected[0]['id']==m['host']['readingStation']
   if float(m['host']['readingOpacity'])>=.999:
    b=m['bounds'];safe=json.loads(m['root']['safeBounds']);assert b['x']>=safe[0]-1 and b['right']<=safe[2]+1 and b['y']>=safe[1]-1 and b['bottom']<=safe[3]+1,(b,safe)
  for c in m['cards']:
   if not c['bounds']['width']:continue
   for t in c['texts']:
    assert t['overflow']<=2,(c['id'],t)
    assert t['bounds']['x']>=c['bounds']['x']-1 and t['bounds']['right']<=c['bounds']['right']+1,(c['id'],t)
  return m
 def case(name,size=(1440,900),station='A3',action=None,reduced=False,unavailable=False):
  context=browser.new_context(viewport={'width':size[0],'height':size[1]},device_scale_factor=1,reduced_motion='reduce' if reduced else 'no-preference');p=context.new_page();p.set_default_timeout(20000);start=len(report['events']);entry={'id':name,'viewport':list(size)}
  p.on('pageerror',lambda e:report['events'].append({'case':name,'type':'pageerror','text':str(e)}));p.on('console',lambda m:report['events'].append({'case':name,'type':'console.error','text':m.text}) if m.type=='error' else None)
  def route(r):
   if r.request.url.startswith(origin+'/') or r.request.url.startswith(('data:','blob:')):r.continue_()
   else:report['externalAttempts'].append({'case':name,'url':r.request.url});r.abort()
  context.route('**/*',route)
  if unavailable:context.add_init_script("const nativeContext=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type,...args){return /^webgl/.test(type)?null:nativeContext.call(this,type,...args)}")
  try:
   p.goto(origin+'/?waterTime=2',wait_until='domcontentloaded');p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=90000);settle(p)
   go(p,station)
   if action:action(p)
   settle(p);m=p.evaluate(SNAP);save(run/(name+'-measurement.json'),m)
   if not unavailable:invariants(p);assert len(report['events'])==start,report['events'][start:]
   else:
    assert m['main']['readingMode']=='stable' and m['host']['renderState']=='error'
    assert all(not e['hidden'] and not e['inert'] for e in m['stations'])
    assert all('WebGL' in e['text'] or 'Tour scene initialization failed' in e['text'] for e in report['events'][start:])
   p.screenshot(path=str(run/(name+'.png')),full_page=False)
   entry.update(status='通过',measurement=name+'-measurement.json',screenshot=name+'.png',mode=m['main']['readingMode'])
  except Exception as error:
   entry.update(status='失败',error=str(error),traceback=traceback.format_exc());failures.append(name)
   try:save(run/(name+'-measurement.json'),p.evaluate(SNAP));p.screenshot(path=str(run/(name+'-failure.png')))
   except Exception:pass
  finally:report['checks'].append(entry);save(run/'browser.json',report);context.close()
 def category(p,id):
  if p.locator(f'.ar-category-buttons [data-category={id}]').is_visible():p.locator(f'.ar-category-buttons [data-category={id}]').click()
  else:p.locator('.ar-category-select select').select_option(id)
  settle(p)
 def overview(p,escape=False):
  category(p,'G5');p.locator('[data-action=next]').click();settle(p)
  before=p.evaluate(SNAP);p.locator('[data-action=all]').click();settle(p)
  immersive=before['main']['readingMode']=='immersive'
  assert p.locator('.ar-catalog .ar-tool-card').count()==22
  if immersive:
   assert p.locator('.ar-overview-dialog').evaluate('(e)=>e.open');assert p.evaluate('document.documentElement.classList.contains("tour-about-open")')
   old_y=p.evaluate('scrollY');h=p.locator('#tour-host').get_attribute('data-display-h');p.mouse.wheel(0,450);settle(p);assert p.evaluate('scrollY')==old_y;assert p.locator('#tour-host').get_attribute('data-display-h')==h
  if escape and immersive:p.keyboard.press('Escape')
  else:p.locator('.ar-all-tools [data-action=return]').first.click()
  settle(p,550);after=p.evaluate(SNAP)
  assert not after['dialogs'] and not after['aboutLock']
  assert after['toolBrowser']['category']=='G5' and after['toolBrowser']['activeId']==before['toolBrowser']['activeId']
  assert abs(after['railX']-before['railX'])<1
  assert p.locator('[data-action=all]').evaluate('(e)=>e===document.activeElement')
  save(run/(('escape' if escape else 'return')+f'-{int(before["viewport"][0])}-state.json'),{'before':before,'after':after})
 def overview_offset(p,resize=False):
  p.locator('[data-action=next]').click();p.locator('[data-action=next]').click();settle(p)
  before=p.evaluate(SNAP);assert before['railX']>100
  p.locator('[data-action=all]').click();settle(p)
  assert p.locator('.ar-overview-dialog').evaluate('(e)=>e.open')
  if resize:p.set_viewport_size({'width':1920,'height':1080});settle(p,500)
  p.keyboard.press('Escape');settle(p,800);after=p.evaluate(SNAP)
  assert not after['dialogs'] and not after['aboutLock']
  assert before['toolBrowser']['activeId']==after['toolBrowser']['activeId']
  if not resize:assert abs(before['railX']-after['railX'])<1,(before['railX'],after['railX'])
  save(run/('overview-offset'+('-resize' if resize else '')+'.json'),{'before':before,'after':after})
 def card_detail(p):
  p.locator('.ar-tool-card[data-tool-id=comfyui] button').click();settle(p,900)
  assert p.locator('.ar-tool-card[data-tool-id=comfyui] button').get_attribute('aria-expanded')=='true'
  assert p.locator('.ar-tool-card[data-tool-id=comfyui] .ar-card-detail').is_visible()
  assert p.locator('.ar-tool-card[data-tool-id=comfyui] button').evaluate('(e)=>e===document.activeElement')
 def mode_roundtrip(p):
  category(p,'G5');p.locator('[data-action=next]').click();settle(p);before=p.evaluate(SNAP)
  assert before['main']['readingMode']=='immersive'
  p.locator('#tour-layout-toggle').click();settle(p,500);assert p.locator('main').get_attribute('data-reading-mode')=='stable'
  assert p.locator('[data-reading-station]').evaluate_all('(es)=>es.every(e=>!e.hidden&&!e.inert)')
  p.locator('#tour-layout-toggle').click();settle(p,500);after=p.evaluate(SNAP)
  assert after['main']['readingMode']=='immersive' and after['host']['readingStation']=='A3'
  assert after['toolBrowser']['category']=='G5' and after['toolBrowser']['activeId']==before['toolBrowser']['activeId'];assert abs(after['railX']-before['railX'])<1
 def native_details(p,kind='experience'):
  summary=p.locator(f'[data-about-details={kind}] summary');summary.focus();p.keyboard.press('Enter');settle(p,650)
  assert p.locator(f'[data-about-details={kind}]').evaluate('(e)=>e.open')
  if kind=='experience':assert '辽宁师范大学' in p.locator('[data-about-details=experience]').inner_text()
 def next_chapter(p):
  p.locator('[data-action=continue]').click();settle(p,600)
  if p.locator('main').get_attribute('data-reading-mode')=='stable':assert p.locator('main').get_attribute('data-flow-anchor')=='B1'
  else:p.wait_for_function('document.querySelector("#tour-host").dataset.filmStation==="B1"&&document.querySelector("#tour-host").dataset.cameraState==="settled"',timeout=15000)
 def large(p):p.evaluate('document.documentElement.style.fontSize="200%"');settle(p,800);assert p.locator('main').get_attribute('data-reading-mode')=='stable';go(p,'A3');assert p.locator('.about-pillar-reader').get_attribute('data-large-text')=='true'
 def guide_interrupt(p):
  assert p.locator('main').get_attribute('data-reading-mode')=='immersive';p.locator('#tour-guide').click();p.wait_for_function('document.querySelector("#tour-host").dataset.guidePhase==="reading"',timeout=15000)
  before=p.locator('#tour-host').get_attribute('data-guide-read-seconds');assert float(before)<45,float(before)
  category(p,'G1');settle(p,500);assert p.locator('#tour-guide').get_attribute('aria-pressed')=='false';assert p.locator('#tour-host').get_attribute('data-guide-deadline')=='';settle(p,500);assert p.locator('#tour-guide').get_attribute('aria-pressed')=='false'
 def reversal(p):
  values=[1.74,2.02,2.54,2.88,3.34,3.699,3.701,4.1];states=[]
  for h in values+list(reversed(values)):
   p.evaluate('(h)=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})',h);p.wait_for_function('h=>Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-h)<.001&&document.querySelector("#tour-host").dataset.cameraState==="settled"',arg=h,timeout=15000)
   states.append(p.locator('#tour-host').evaluate('(e)=>[e.dataset.cameraPosition,e.dataset.cameraTarget,e.dataset.viewHeight,e.dataset.readingStation,e.dataset.readingOpacity]'))
  assert states[:len(values)]==list(reversed(states[len(values):])),states
  a=[json.loads(v) if i<2 else float(v) for i,v in enumerate(states[5][:3])];b=[json.loads(v) if i<2 else float(v) for i,v in enumerate(states[6][:3])]
  assert max(abs(x-y) for x,y in zip(a[0],b[0]))<.01 and abs(a[2]-b[2])<.01,(a,b)
  save(run/'reversal-states.json',{'h':values,'states':states})
 try:
  if args.suite=='smoke':
   for id in ['A1','A2','A3']:case('desktop-'+id,station=id)
   case('overview-return',action=overview)
   case('stable-phone',size=(390,844))
   case('reading-mode-roundtrip',action=mode_roundtrip)
  else:
   for label,w,h in [('large',1920,1080),('desktop',1440,900),('laptop',1366,768),('short-laptop',1280,720),('tablet-landscape',1024,768),('tablet-portrait',820,1180),('phone',390,844),('narrow',320,740),('short-landscape',844,390)]:
    for id in ['A1','A2','A3']:case(label+'-'+id,size=(w,h),station=id)
   case('overview-offset',action=overview_offset)
   case('overview-resize',action=lambda p:overview_offset(p,True))
   case('card-detail',action=card_detail)
   case('overview-return',action=overview)
   case('overview-escape',action=lambda p:overview(p,True))
   case('phone-overview-return',size=(390,844),action=overview)
   case('reading-mode-roundtrip',action=mode_roundtrip)
   case('identity-expanded',station='A1',action=lambda p:native_details(p,'identity'))
   case('experience-expanded',station='A2',action=native_details)
   case('phone-experience-expanded',size=(390,844),station='A2',action=native_details)
   case('large-text',size=(800,600),action=large)
   case('reduced-motion',reduced=True)
   case('graphical-unavailable',unavailable=True)
   case('continue-immersive',action=next_chapter)
   case('continue-stable',size=(390,844),action=next_chapter)
   case('guide-interrupt',action=guide_interrupt)
   case('camera-reversal',action=reversal)
  report['complete']=not failures
 finally:browser.close();report['cleanup']={'browserClosed':True,'sharedServicesStopped':False};report['finishedAtShanghai']=now();save(run/'browser.json',report)
print(json.dumps({'run':args.run,'checks':len(report['checks']),'passed':sum(c['status']=='通过' for c in report['checks']),'failures':failures,'complete':report['complete']},ensure_ascii=False))
if failures:raise SystemExit(1)
