from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import os,json,subprocess,hashlib,traceback,sys
from playwright.sync_api import sync_playwright
from PIL import ImageGrab
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent;run=OUT/(sys.argv[1] if len(sys.argv)>1 else 'browser-zoom-1');run.mkdir(exist_ok=False)
s=json.loads((OUT/'services-started.json').read_text());os.environ.update(s['browserEnvironment']);key='/workspace/.cache/browser-deps/root/usr/bin/xdotool'
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
(run/'test.py.txt').write_bytes(Path(__file__).read_bytes());paths=[p for p in (ROOT/'src').rglob('*') if p.is_file()]+[ROOT/'dist/index.html']+list((ROOT/'dist/assets').glob('startTourPrototype*'));save(run/'source-manifest.json',[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths])
READ='''()=>({width:innerWidth,height:innerHeight,dpr:devicePixelRatio,mode:document.querySelector('main').dataset.readingMode,overflow:document.documentElement.scrollWidth-innerWidth,d:{...document.querySelector('.ar-tools-browser').dataset},y:scrollY,header:document.querySelector('.tour-header').getBoundingClientRect().toJSON(),headerHit:!!document.elementFromPoint(30,30)?.closest('.tour-header'),visualViewport:{width:visualViewport.width,height:visualViewport.height,scale:visualViewport.scale,pageTop:visualViewport.pageTop},reading:[...document.querySelectorAll('.ar-tool-card')].filter(e=>e.dataset.expanded==='true').map(e=>({id:e.dataset.toolId,hidden:e.querySelector('.ar-card-detail').hidden})),focusHidden:!!document.activeElement?.closest('[hidden],[inert]')})'''
report={'checks':[],'events':[],'complete':False,'physicalDevice':False,'method':'Headed Chromium browser chrome keyboard shortcuts through X11, no viewport/zoom emulation','startedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=False,args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist','--window-size=1440,1000']);report['version']=b.version
 try:
  c=b.new_context(no_viewport=True);q=c.new_page();q.on('pageerror',lambda e:report['events'].append(str(e)));q.goto(s['origin']+'/?waterTime=2',wait_until='domcontentloaded');q.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=90000);q.evaluate('scrollTo({top:3.34/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})');q.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceReady==="true"');q.wait_for_timeout(700)
  if q.locator('[data-action=auto]').is_visible() and q.locator('[data-action=auto]').get_attribute('aria-pressed')=='true':q.locator('[data-action=auto]').click()
  q.locator('.ar-tool-card[data-tool-id=comfyui] button').click();q.wait_for_timeout(500);before=q.evaluate(READ)
  ids=subprocess.check_output([key,'search','--onlyvisible','--class','chromium'],text=True).split();assert ids
  wid=ids[-1];subprocess.run([key,'windowfocus','--sync',wid],check=True)
  samples=[]
  for _ in range(5):subprocess.run([key,'key','--clearmodifiers','ctrl+plus'],check=True);q.wait_for_timeout(650);samples.append(q.evaluate(READ))
  large=samples[-1];assert 1.95<large['dpr']/before['dpr']<2.05,(before,samples);assert abs(large['width']*2-before['width'])<3,(before,large);assert large['mode']=='stable' and large['overflow']<=1;assert any(x['id']=='comfyui' and not x['hidden'] for x in large['reading']);ImageGrab.grab(xdisplay=os.environ['DISPLAY']).save(run/'browser-zoom-200-desktop.png');q.screenshot(path=str(run/'browser-zoom-200.png'));assert large['headerHit'],large
  subprocess.run([key,'key','--clearmodifiers','ctrl+0'],check=True);q.wait_for_timeout(1100);after=q.evaluate(READ);assert after['width']==before['width'] and after['dpr']==before['dpr'];assert after['mode']=='stable' and after['d']['trackEnabled']=='false';assert after['d']['readingId']=='comfyui' and not after['focusHidden'];q.screenshot(path=str(run/'browser-zoom-restored.png'));ImageGrab.grab(xdisplay=os.environ['DISPLAY']).save(run/'browser-zoom-restored-desktop.png')
  assert not report['events'];save(run/'zoom-data.json',{'before':before,'steps':samples,'large':large,'restored':after});report['checks'].append({'id':'real-browser-zoom-200-roundtrip','status':'通过','data':'zoom-data.json'});report['complete']=True
 except Exception as e:
  try:save(run/'failure-state.json',q.evaluate(READ));ImageGrab.grab(xdisplay=os.environ['DISPLAY']).save(run/'failure-desktop.png')
  except Exception:pass
  report['checks'].append({'id':'real-browser-zoom-200-roundtrip','status':'失败','error':str(e),'traceback':traceback.format_exc()})
 finally:b.close();report['browserClosed']=True;save(run/'browser.json',report)
print(json.dumps(report,ensure_ascii=False));raise SystemExit(0 if report['complete'] else 1)
