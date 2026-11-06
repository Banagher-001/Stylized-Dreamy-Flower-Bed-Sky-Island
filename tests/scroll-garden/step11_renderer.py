"""DPR cap, repeated-size allocation, single-scene and paused/offscreen draw guards."""
import argparse
from playwright.sync_api import sync_playwright
from step11_common import *
parser=argparse.ArgumentParser();parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');args=parser.parse_args();rows=[]
BUFFER_PROBE='''(()=>{window.__bufferWrites=0;for(const key of ['width','height']){const d=Object.getOwnPropertyDescriptor(HTMLCanvasElement.prototype,key);Object.defineProperty(HTMLCanvasElement.prototype,key,{...d,set(value){window.__bufferWrites++;d.set.call(this,value)}})}})()'''
with sync_playwright()as p:
 b=launch(p,args.engine)
 for ratio in [1,2,3]:
  c=b.new_context(viewport={'width':390,'height':844},device_scale_factor=ratio);c.add_init_script(PROBE);c.add_init_script(BUFFER_PROBE);page=c.new_page();ready(page,'http://127.0.0.1:4173/?tour=prototype&waterTime=2');page.wait_for_function('document.querySelector("main").dataset.layoutReady==="true"');frames(page);assert page.locator('main').get_attribute('data-reading-mode')=='immersive'
  buffers=page.locator('canvas').evaluate('e=>({dpr:devicePixelRatio,width:e.width,height:e.height,rect:e.getBoundingClientRect().toJSON(),profile:e.dataset.pixelProfile})')
  assert buffers['width']==int(buffers['rect']['width'])*min(ratio,2)and buffers['height']==int(buffers['rect']['height'])*min(ratio,2),buffers
  assert buffers['profile']=='384'
  for render in ['pixel','native','pixel']:
   page.locator(f'.tour-actions [data-mode={render}]').click()
   for _,h in STOPS:go(page,h)
  go(page,0);frames(page);page.wait_for_timeout(250);before=json.loads(data(page)['rendererStats']);writes=page.evaluate('window.__bufferWrites')
  for i in range(10):page.evaluate('dispatchEvent(new Event("resize"))');frames(page)
  page.wait_for_timeout(250);afterWrites=page.evaluate('window.__bufferWrites');after=json.loads(data(page)['rendererStats']);assert afterWrites==writes,(writes,afterWrites)
  assert all(before[k]==after[k]for k in ['geometries','textures','programs'])
  a=page.evaluate('window.__tourProbe.draws');page.wait_for_timeout(400);assert page.evaluate('window.__tourProbe.draws')==a
  page.locator('#tour-layout-toggle').click();page.locator('#tour-stop-experiments').click();frames(page);page.locator('#tour-motion').evaluate('e=>e.click()');page.wait_for_timeout(250);a=page.evaluate('window.__tourProbe.draws');t=data(page)['sceneTime'];page.wait_for_timeout(400);assert page.evaluate('window.__tourProbe.draws')==a and data(page)['sceneTime']==t
  page.locator('#tour-stop-overview').click();frames(page);page.wait_for_function('t=>Number(document.querySelector("#tour-host").dataset.sceneTime)>Number(t)+.1',arg=t)
  page.locator('#tour-motion').click();frames(page);assert page.locator('canvas').count()==1
  rows.append({'requestedDPR':ratio,'buffers':buffers,'warmBefore':before,'warmAfterSameSizeEvents':after,'sameSizeResizeEvents':10,'bufferSetterWritesBefore':writes,'bufferSetterWritesAfter':afterWrites,'zeroDrawPausedWindowMs':400,'offscreenWhilePlayIntentZeroDrawWindowMs':400,'visibleResumesUserPlayChoice':True});c.close();print(args.engine,'DPR',ratio,'PASS',flush=True)
 save(f'renderer-{args.engine}.json',{'passed':True,'engine':args.engine,'checks':rows,'physicalDpiOrFPSProof':False});b.close()
