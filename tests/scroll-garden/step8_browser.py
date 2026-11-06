"""Pool-specific rendering, time, fallback and complete warm-cache budget."""
from io import BytesIO
import argparse,hashlib
from PIL import Image,ImageChops
from playwright.sync_api import sync_playwright
from step8_common import *
parser=argparse.ArgumentParser();parser.add_argument('--engine',default='chromium');args=parser.parse_args();checks=[];issues=[]
def record(name,value):checks.append({'check':name,'passed':True,'evidence':value});print(args.engine+': '+name,flush=True)
with sync_playwright()as p:
 b=launch(p,args.engine);context=b.new_context(viewport={'width':1440,'height':900});context.add_init_script(PROBE);page=context.new_page();page.on('pageerror',lambda e:issues.append(str(e)))
 ready(page,'http://127.0.0.1:4173/?tour=prototype&waterTime=2');assert data(page)['fountainStyle']=='refined';resources=json.loads(data(page)['fountainResources']);assert len(resources['bindings'])==14 and resources['newGeometries']==resources['newTextures']==resources['extraPasses']==0
 record('pool-only appearance is active with no new geometry/texture/pass',resources)
 images=[]
 for t in [2,4,6,8]:
  ready(page,f'http://127.0.0.1:4173/?tour=prototype&waterTime={t}')
  for mode in ['pixel','native']:
   page.locator(f'.tour-actions [data-mode={mode}]').click()
   for key,h in [('W',11.5),('O',0)]:
    go(page,h);frames(page);page.mouse.move(10,450);path=f'{args.engine}-{t}-{mode}-{key}.png';page.screenshot(path=str(OUT/path));images.append({'time':t,'mode':mode,'pose':key,'image':path,'camera':data(page)['cameraPosition']})
 record('four fixed times and both visual modes render O/W',images)
 go(page,11.5);frames(page);a=page.locator('canvas').screenshot();t=data(page)['sceneTime'];draws=page.evaluate('window.__tourProbe.draws');page.wait_for_timeout(400);assert data(page)['sceneTime']==t and page.evaluate('window.__tourProbe.draws')==draws
 assert ImageChops.difference(Image.open(BytesIO(a)).convert('RGB'),Image.open(BytesIO(page.locator('canvas').screenshot())).convert('RGB')).getbbox()is None
 page.bring_to_front();page.wait_for_function('!document.hidden');page.locator('#tour-motion').click();page.wait_for_function('t=>Number(document.querySelector("#tour-host").dataset.sceneTime)>Number(t)+.12',arg=t);page.locator('#tour-motion').click();frames(page);assert float(data(page)['sceneTime'])>float(t)and ImageChops.difference(Image.open(BytesIO(a)).convert('RGB'),Image.open(BytesIO(page.locator('canvas').screenshot())).convert('RGB')).getbbox()is not None
 record('water advances on the shared clock and fully freezes while paused',{'initialTime':t,'advancedTime':data(page)['sceneTime'],'pausedDraws':draws})
 ready(page,'http://127.0.0.1:4173/?tour=prototype&waterTime=2');caches=[]
 for mode in ['pixel','native','pixel']:
  page.locator(f'.tour-actions [data-mode={mode}]').click()
  for _,h in VIEWS:go(page,h)
  frames(page);caches.append(json.loads(data(page)['rendererStats']))
 baseline=json.loads((OUT/'baseline-before.json').read_text())['fullWarmCaches']
 for i,(old,new)in enumerate(zip(baseline,caches)):
  assert new['geometries']-old['geometries']<=2 and new['textures']==old['textures']and new['programs']-old['programs']<=(2 if i==0 else 4),(old,new)
 record('full-route identical mode history stays within GPU budgets',{'before':baseline,'after':caches})
 ready(page,'http://127.0.0.1:4173/?tour=prototype&waterTime=2&pool=legacy');assert data(page)['fountainStyle']=='legacy'and data(page)['fountainResources']=='null'
 record('refined pool can independently return to the verified legacy finish',{'style':data(page)['fountainStyle']})
 assert not issues,issues;save(f'pool-verification-{args.engine}.json',{'engine':args.engine,'version':b.version,'checks':checks,'unhandledExceptions':issues,'passed':True,'environment':'Linux software graphics; simulated portrait; GTK is not Apple Safari; no hardwareFPS claim'});b.close()
