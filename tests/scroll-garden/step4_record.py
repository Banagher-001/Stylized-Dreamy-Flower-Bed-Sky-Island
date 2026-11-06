"""Actual wheel recording and no-WebGL fallback for the third-step prototype."""
from pathlib import Path
import argparse,json,os,time
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/scroll-garden-step-4'
parser=argparse.ArgumentParser();parser.add_argument('--url',default='http://127.0.0.1:4173');parser.add_argument('--fallback-only',action='store_true');args=parser.parse_args()
executable=os.environ.get('CHROMIUM_EXECUTABLE','/usr/bin/chromium')
if not args.fallback_only:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=executable,headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  context=b.new_context(viewport={'width':1280,'height':800},record_video_dir=str(OUT/'raw-recording'),record_video_size={'width':1280,'height':800});page=context.new_page()
  page.goto(args.url+'/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]');page.mouse.move(1190,280);page.wait_for_timeout(500)
  samples=[];start=time.monotonic()
  for target in [1.74,2.02,2.54,2.82,3.34,3.7,4.95,3.34,2.54,1.74]:
   destination=page.evaluate('h=>h/12.3*(document.documentElement.scrollHeight-innerHeight)',target)
   for _ in range(180):
    current=page.evaluate('scrollY');distance=destination-current
    if abs(distance)<1:break
    page.mouse.wheel(0,max(-55,min(55,distance)));page.wait_for_timeout(95)
   else:raise RuntimeError('Native wheel did not reach target')
   page.wait_for_function('()=>document.querySelector("#tour-host").dataset.cameraState==="settled"')
   page.wait_for_timeout(850 if target in [1.74,2.54,3.34]else 500)
   samples.append({'requestedH':target,'scene':page.locator('#tour-host').evaluate('e=>({h:Number(e.dataset.displayH),station:e.dataset.readingStation,opacity:Number(e.dataset.readingOpacity)})')})
  wall=time.monotonic()-start;video=page.video;context.close();video.save_as(str(OUT/'magic-reading-demo.webm'));b.close()
  (OUT/'demo-recording.json').write_text(json.dumps({'method':'actual browser screen recording driven by native wheel input in both directions','viewport':[1280,800],'kind':'fixed environment, actual scroll-controlled magic','wallSeconds':wall,'environmentTime':2,'environmentPausedForComparison':True,'hardwareFPSProof':False,'samples':samples},ensure_ascii=False,indent=2)+'\n');print('Recorded actual two-direction reading, wall seconds',round(wall,2),flush=True)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=executable,headless=True,args=['--no-sandbox','--disable-webgl']);page=b.new_page(viewport={'width':1280,'height':800});errors=[];diagnostics=[]
 page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:diagnostics.append({'type':m.type,'text':m.text})if m.type in ['warning','error']else None)
 page.goto(args.url+'/?tour=prototype',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="error"]')
 assert page.get_by_role('alert').inner_text()and page.locator('canvas').count()==0 and page.locator('button:disabled').count()==11
 assert page.locator('.pillar-reading').get_attribute('aria-hidden')=='true'
 page.screenshot(path=str(OUT/'no-webgl.png'));page.locator('#tour-reference').click();page.wait_for_selector('#about');assert '枫叶互动'in page.locator('#about').inner_text()and not errors
 (OUT/'fallback.json').write_text(json.dumps({'noWebGL':True,'readableAlert':True,'disabledSceneControls':11,'readerHidden':True,'referenceLinkUsable':True,'unhandledExceptions':errors,'expectedInitializationDiagnostics':diagnostics},ensure_ascii=False,indent=2)+'\n');b.close();print('No-WebGL fallback and reference link passed',flush=True)
