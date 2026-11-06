"""Actual two-way wheel recording of the exhibition and its full-image viewer."""
from pathlib import Path
import json,time
from playwright.sync_api import sync_playwright
OUT=Path(__file__).resolve().parents[2]/'docs/evidence/scroll-garden-step-6'
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);context=b.new_context(viewport={'width':1280,'height':800},record_video_dir=str(OUT/'raw-recording'),record_video_size={'width':1280,'height':800});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('http://127.0.0.1:4173/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]');page.mouse.move(1190,280);samples=[];start=time.monotonic()
 for target in [3.34,4.95,5.34,5.95,6.30,6.84,7.18,7.64,8.30,9.14,7.64,6.84,5.95,4.95]:
  for _ in range(180):
   current=page.evaluate('({y:scrollY,range:document.documentElement.scrollHeight-innerHeight})');distance=target/12.3*current['range']-current['y']
   if abs(distance)<1:break
   page.mouse.wheel(0,max(-55,min(55,distance)));page.wait_for_timeout(95)
  else:raise RuntimeError('Wheel did not reach target')
  page.wait_for_function('()=>document.querySelector("#tour-host").dataset.cameraState==="settled"');page.wait_for_timeout(850 if target in [4.95,5.95,6.84,7.64]else 450)
  d=page.locator('#tour-host').evaluate('e=>({h:Number(e.dataset.displayH),station:e.dataset.filmStation,phase:e.dataset.filmPhase,sceneTime:Number(e.dataset.sceneTime),targetH:Number(e.dataset.targetH),nativeH:scrollY/(document.documentElement.scrollHeight-innerHeight)*12.3,scrollY,scrollHeight:document.documentElement.scrollHeight,innerHeight,presentation:JSON.parse(e.dataset.filmPresentation)})');print('record target',target,'actual',d['h'],flush=True);samples.append({'requestedH':target,'actual':d});(OUT/'recording-progress.json').write_text(json.dumps(samples,ensure_ascii=False,indent=2)+'\n')
 before=page.locator('#tour-host').get_attribute('data-display-h');page.locator('[data-film-station=B1] button[data-work]').click();page.wait_for_selector('.film-dialog[open][data-state=ready]');assert '非个人实际项目'in page.locator('.film-dialog-label').inner_text();page.wait_for_timeout(1200);page.get_by_role('button',name='关闭画面',exact=True).click();page.wait_for_function('document.querySelector("#tour-host").dataset.overlayState==="closed"');assert page.locator('#tour-host').get_attribute('data-display-h')==before;page.mouse.move(1190,280);page.wait_for_timeout(650)
 wall=time.monotonic()-start;assert all(abs(x['actual']['h']-x['requestedH'])<.003 for x in samples),samples;assert not errors;video=page.video;context.close();video.save_as(str(OUT/'film-reading-demo.webm'));b.close()
 (OUT/'demo-recording.json').write_text(json.dumps({'method':'actual native wheel input, both directions, followed by an actual full-image open/close','viewport':[1280,800],'environmentTime':2,'environmentPausedForComparison':True,'wallSeconds':wall,'samples':samples,'imageViewerReturnsToSameH':True,'mediaStatus':'clearly labelled website-design concepts; no real personal film supplied','hardwareFPSProof':False,'unhandledExceptions':errors},ensure_ascii=False,indent=2)+'\n');print('Recorded',len(samples),'real wheel stops and full-image return; wall seconds',round(wall,2),flush=True)
