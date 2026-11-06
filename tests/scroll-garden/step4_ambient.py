"""Actual shared-clock ambient recording at a stationary reading pose."""
from pathlib import Path
from io import BytesIO
import json
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright

OUT=Path(__file__).resolve().parents[2]/'docs/evidence/scroll-garden-step-4'
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);context=b.new_context(viewport={'width':1280,'height':800},record_video_dir=str(OUT/'raw-recording'),record_video_size={'width':1280,'height':800});page=context.new_page()
 page.goto('http://127.0.0.1:4173/?tour=prototype&waterTime=2&render=native',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]');page.evaluate('scrollTo({top:2.54/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})');page.wait_for_function('document.querySelector("#tour-host").dataset.readingOpacity==="1.0000000"&&document.querySelector("#tour-host").dataset.stage==="A2"')
 rect=page.locator('.pillar-reading').evaluate('e=>({x:Number(e.dataset.anchorX),y:Number(e.dataset.anchorY)})');clip={'x':max(0,rect['x']-64),'y':max(0,rect['y']-74),'width':128,'height':148}
 before=Image.open(BytesIO(page.screenshot(path=str(OUT/'ambient-before-face.png'),clip=clip))).convert('RGB');body=page.locator('.pillar-reading').evaluate('e=>({rect:e.getBoundingClientRect().toJSON(),body:e.dataset.opacity,title:e.dataset.titleOpacity})');start=float(page.locator('#tour-host').get_attribute('data-scene-time'))
 page.get_by_role('button',name='播放动效',exact=True).click();page.mouse.move(10,400);page.wait_for_timeout(6000);page.get_by_role('button',name='暂停动效',exact=True).click();page.mouse.move(10,400)
 after=Image.open(BytesIO(page.screenshot(path=str(OUT/'ambient-after-face.png'),clip=clip))).convert('RGB');end=float(page.locator('#tour-host').get_attribute('data-scene-time'));assert end>start and ImageChops.difference(before,after).getbbox()is not None
 assert page.locator('.pillar-reading').evaluate('e=>({rect:e.getBoundingClientRect().toJSON(),body:e.dataset.opacity,title:e.dataset.titleOpacity})')==body
 video=page.video;context.close();video.save_as(str(OUT/'magic-ambient-demo.webm'));b.close();(OUT/'ambient-recording.json').write_text(json.dumps({'kind':'actual environment playback at stationary A2; no camera or text animation','viewport':[1280,800],'mode':'native','sceneTimeBefore':start,'sceneTimeAfter':end,'faceRegionActuallyChanges':True,'paragraphLayoutAndBrightnessStable':True,'hardwareFPSProof':False,'clip':clip},ensure_ascii=False,indent=2)+'\n');print('Actual ambient clip recorded; face region changes while paragraph stays stable.')
