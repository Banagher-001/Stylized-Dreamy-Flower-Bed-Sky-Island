"""Resize while a viewer owns input, then restore the original semantic station."""
from playwright.sync_api import sync_playwright
from step11_common import *
rows=[]
with sync_playwright()as p:
 for engine in ['chromium','firefox','webkit']:
  b=launch(p,engine);c=b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,has_touch=True);page=c.new_page();ready(page,'http://127.0.0.1:4173/?tour=prototype&waterTime=2');page.wait_for_function('document.querySelector("main").dataset.layoutReady==="true"');go(page,10.05);frames(page);page.evaluate('window.__modalResizeCanvas=document.querySelector("canvas")')
  before=data(page);page.locator('[data-project-tab=live]').tap();frames(page);page.locator('[data-project-mode=native]').tap();page.set_viewport_size({'width':844,'height':390});frames(page);assert page.locator('.tour-project-dialog').evaluate('e=>e.open')and data(page)['overlayState']=='open'
  r=page.locator('.tour-project-close').bounding_box();assert r and r['y']>=0 and r['height']>=44
  page.locator('.tour-project-close').tap();page.wait_for_function('document.querySelector("main").dataset.readingMode==="stable"&&document.querySelector("main").dataset.flowAnchor==="C2"');frames(page);short=page.locator('main').evaluate('e=>({...e.dataset})')
  page.set_viewport_size({'width':390,'height':844});page.wait_for_function('document.querySelector("main").dataset.immersiveAvailable==="true"');frames(page);assert page.locator('main').get_attribute('data-flow-anchor')=='C2';page.locator('#tour-layout-toggle').tap();settled(page,10.05)
  assert page.evaluate('window.__modalResizeCanvas===document.querySelector("canvas")')and page.locator('canvas').count()==1 and not page.locator('video').count()
  assert data(page)['sceneTime']==before['sceneTime']and page.locator('.tour-actions [data-mode=native]').get_attribute('aria-pressed')=='true'
  rows.append({'engine':engine,'version':b.version,'originalH':before['displayH'],'whileOpenViewport':[844,390],'viewerRetainedOwnership':True,'afterClose':{'mode':short['readingMode'],'anchor':short['flowAnchor']},'returnH':data(page)['displayH'],'sameCanvas':True,'pauseTimeAndLatestNativeModeKept':True,'rotationMethod':'touch-enabled actual CSS layout viewport; not physical orientation or GTK fixedLayout emulation'});b.close();print(engine,'modal resize PASS',flush=True)
save('overlay-resize.json',{'passed':True,'checks':rows})
