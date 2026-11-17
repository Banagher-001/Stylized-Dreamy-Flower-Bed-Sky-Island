from pathlib import Path
import json,os,sys,traceback,hashlib,shutil
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent;run=OUT/(sys.argv[1] if len(sys.argv)>1 else 'projection-1');run.mkdir(exist_ok=False)
s=json.loads((OUT/'services-started.json').read_text());os.environ.update(s['browserEnvironment']);report={'checks':[],'events':[],'complete':False};save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
shutil.copy2(__file__,run/'verify-projection.py.txt')
sources=[p for p in (ROOT/'src/tour').rglob('*') if p.is_file()]+list((ROOT/'src/assets/tool-marks').glob('*.svg'))+[ROOT/'dist/index.html']+list((ROOT/'dist/assets').glob('startTourPrototype*'))
save(run/'source-manifest.json',[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources])
READ=r'''()=>{const rail=document.querySelector('.ar-tool-rail'),r=rail.getBoundingClientRect();const box=e=>e.getBoundingClientRect().toJSON();return {mode:document.querySelector('main').dataset.readingMode,viewport:[innerWidth,innerHeight],rail:box(rail),cards:[...rail.querySelectorAll('.ar-stone-card')].map(e=>{const b=e.getBoundingClientRect(),faces=[...e.querySelectorAll('[data-card-face]')].map(box);return {id:e.dataset.toolId,expanded:e.dataset.expanded,ready:e.dataset.geometryReady,rect:box(e),faces,paint:{left:Math.min(b.left-10,...faces.map(x=>x.left)),right:Math.max(b.right+10,...faces.map(x=>x.right)),top:Math.min(b.top-4,...faces.map(x=>x.top)),bottom:Math.max(b.bottom+18,...faces.map(x=>x.bottom))},full:b.left>=r.left-.5&&b.right<=r.right+.5}})}}'''
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist'])
 try:
  def case(name,size,expanded=False,large=False,last=False):
   ctx=browser.new_context(viewport={'width':size[0],'height':size[1]});p=ctx.new_page();entry={'id':name};p.on('pageerror',lambda e:report['events'].append(str(e)))
   try:
    p.goto(s['origin']+'/?waterTime=2',wait_until='domcontentloaded');p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=90000)
    if p.locator('main').get_attribute('data-reading-mode')=='stable':p.locator('.tour-reading-flow [data-flow-anchor=A3]').scroll_into_view_if_needed()
    else:
     p.evaluate('scrollTo({top:3.34/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})');p.wait_for_function('document.querySelector("#tour-host").dataset.readingStation==="A3"&&document.querySelector("#tour-host").dataset.cameraState==="settled"')
    p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceReady==="true"',timeout=12000)
    p.wait_for_timeout(1200)
    if p.locator('[data-action=auto]').is_visible() and p.locator('[data-action=auto]').get_attribute('aria-pressed')=='true':p.locator('[data-action=auto]').click()
    if large:p.evaluate('document.documentElement.style.fontSize="200%"');p.wait_for_timeout(700);p.locator('.tour-reading-flow [data-flow-anchor=A3]').scroll_into_view_if_needed()
    p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceReady==="true"',timeout=12000)
    if last:
     for _ in range(21):p.locator('[data-action=next]').click()
    if expanded:p.locator(f'.ar-tool-card[data-tool-id={"vibe-coding" if last else "midjourney"}] button').click()
    p.wait_for_timeout(650);p.wait_for_function('[...document.querySelectorAll(".ar-tool-rail .ar-stone-card")].every(e=>e.dataset.geometryReady==="true")')
    m=p.evaluate(READ);save(run/(name+'-measurement.json'),m);full=[c for c in m['cards'] if c['full']];assert full
    for c in full:
     b=c['paint'];r=m['rail'];assert b['left']>=r['left']-.6 and b['right']<=r['right']+.6 and b['top']>=r['top']-.6 and b['bottom']<=r['bottom']+.6,(c['id'],b,r)
    if expanded:assert next(c for c in m['cards'] if c['expanded']=='true')['full']
    p.screenshot(path=str(run/(name+'.png')));entry.update(status='通过',measurement=name+'-measurement.json')
   except Exception as e:
    entry.update(status='失败',error=str(e),traceback=traceback.format_exc())
    try:p.screenshot(path=str(run/(name+'-failure.png')))
    except Exception:pass
   finally:report['checks'].append(entry);save(run/'browser.json',report);ctx.close()
  case('desktop-front',(1440,900));case('large-front',(1920,1080));case('phone-front',(390,844));case('narrow-front',(320,740))
  case('first-detail',(1440,900),True);case('last-detail',(1440,900),True,last=True);case('narrow-detail',(320,740),True);case('large-text-detail',(800,600),True,True)
  report['complete']=all(c['status']=='通过' for c in report['checks'])
 finally:browser.close();report['browserClosed']=True;save(run/'browser.json',report)
print(json.dumps({'checks':len(report['checks']),'passed':sum(c['status']=='通过' for c in report['checks']),'complete':report['complete'],'failures':[{'id':c['id'],'error':c.get('error')} for c in report['checks'] if c['status']!='通过']},ensure_ascii=False))
if not report['complete']:raise SystemExit(1)
