"""Focused medium viewport and simulated phone rotation checks."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

OUT=Path(__file__).resolve().parents[2]/'docs/evidence/scroll-garden-step-3'
def data(page):return page.locator('#tour-host').evaluate('e=>({...e.dataset})')
def settle(page,h):page.wait_for_function('h=>{const d=document.querySelector("#tour-host").dataset;return d.cameraState==="settled"&&Math.abs(Number(d.displayH)-h)<.003}',arg=h)
def go(page,h):
 page.evaluate('h=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})',h);settle(page,h)
def resize(page,w,h):
 old=float(data(page)['displayH']);page.set_viewport_size({'width':w,'height':h});page.wait_for_function('()=>{const e=document.querySelector("#tour-host"),r=e.getBoundingClientRect();return Math.abs(Number(e.dataset.aspect)-r.width/r.height)<.00001}');page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');settle(page,old)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=b.new_page(viewport={'width':1366,'height':768});page.goto('http://127.0.0.1:4173/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]')
 medium=[]
 for key,h in [('A1',1.74),('A2',2.54),('A3',3.34)]:
  go(page,h);d=data(page);r=page.locator('.pillar-reading').evaluate('e=>({fits:e.dataset.fits,rect:e.getBoundingClientRect().toJSON()})');assert d['readingStation']==key and d['readingOpacity']=='1.0000000'and r['fits']=='true';page.screenshot(path=str(OUT/f'layout-1366-{key}.png'));medium.append({'station':key,'layout':r})
 mobile=b.new_context(viewport={'width':390,'height':844},is_mobile=True,has_touch=True,device_scale_factor=2,reduced_motion='reduce');m=mobile.new_page();m.goto('http://127.0.0.1:4173/?tour=prototype&waterTime=2',wait_until='networkidle');m.wait_for_selector('#tour-host[data-render-state="ready"]');rotations=[]
 for h in [2.54,2.08]:
  go(m,h);before=data(m);resize(m,844,390);landscape=data(m)
  assert landscape['readingStation']==before['readingStation']and landscape['readingPhase']==before['readingPhase']and abs(float(landscape['readingOpacity'])-float(before['readingOpacity']))<.025
  landscape_fits=m.locator('.pillar-reading').get_attribute('data-fits');m.screenshot(path=str(OUT/f'rotation-landscape-{h}.png'));resize(m,390,844);after=data(m);assert after['readingStation']==before['readingStation']and after['sceneTime']==before['sceneTime']
  if h==2.54:assert m.locator('.pillar-reading').get_attribute('data-fits')=='true'
  rotations.append({'h':h,'progressPreserved':True,'stationPreserved':True,'phasePreserved':True,'pauseTimePreserved':True,'landscapeFits':landscape_fits,'scope':'simulated viewport rotation; short landscape composition belongs to step 11'})
 mobile.close();b.close();(OUT/'layout-orientation.json').write_text(json.dumps({'engine':'chromium','mediumViewport':[1366,768],'threeStationLayouts':medium,'simulatedPhoneRotation':rotations,'physicalDevice':False},ensure_ascii=False,indent=2)+'\n');print('All 1366px reading stations and simulated rotation progress preservation passed.')
