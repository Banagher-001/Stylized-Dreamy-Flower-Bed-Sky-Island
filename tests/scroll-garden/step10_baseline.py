"""Frozen Step9 / Step10 baseline: matched 30 wheel stops, then screenshots."""
import argparse,hashlib
from playwright.sync_api import sync_playwright
from step10_common import *
parser=argparse.ArgumentParser();parser.add_argument('--phase',required=True,choices=['before','after']);parser.add_argument('--url',required=True);args=parser.parse_args()
with sync_playwright()as p:
 b=launch(p);context=b.new_context(viewport={'width':1440,'height':900});context.add_init_script(PROBE);page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 ready(page,args.url+'/?tour=prototype&waterTime=2');assert ('STEP 09'in page.title()if args.phase=='before'else'张辰翰'in page.title())
 caches=[]
 for mode in ['pixel','native','pixel']:
  page.locator(f'.tour-actions [data-mode={mode}]').click()
  for _,h in VIEWS:go(page,h)
  frames(page);caches.append(json.loads(data(page)['rendererStats']))
 grouped=[];samples=[]
 for key,at in [('T01',.9),('T12',4.05),('T23',8.35),('T3W',11.26),('WIDE',11.66)]:
  go(page,at);frames(page);page.mouse.move(1100,260);page.wait_for_timeout(80);page.evaluate('window.__tourProbe.settles=[]')
  for delta in [15]*3+[-15]*3:
   prior=page.evaluate('scrollY');page.mouse.wheel(0,delta);page.wait_for_function('y=>Math.abs(scrollY-y)>1',arg=prior);page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"');page.wait_for_timeout(20)
  values=page.evaluate('window.__tourProbe.settles');assert len(values)==6,(key,values);samples.extend(values);grouped.append({'route':key,'startH':at,'deltasCssPixels':[15]*3+[-15]*3,'samplesMs':values})
 assert len(samples)==30
 save(f'latency-{args.phase}.json',{'phase':args.phase,'method':'five route centers T01/.9,T12/4.05,T23/8.35,T3W/11.26,WIDE/11.66; per route +15px×3,−15px×3; same1440×900/pixel/native/pixel fullroute prewarm/time2; native wheel30stops; no concurrent browser/recording or screenshots during sampling; six samples per route are not a per-route p95 estimate','routes':grouped,'samplesMs':samples,'p95Ms':sorted(samples)[int((len(samples)-1)*.95)],'maxMs':max(samples),'hardwareFPSProof':False})

 views=[]
 for w,h in [(1440,900),(1366,768),(390,844)]:
  resize(page,w,h)
  for mode in ['pixel','native']:
   page.locator(f'.tour-actions [data-mode={mode}]').click()
   for key,at in VIEWS:
    go(page,at);frames(page);page.mouse.move(10,h/2);page.screenshot(path=str(OUT/f'{args.phase}-{w}-{mode}-{key}.png'));views.append({'viewport':[w,h],'mode':mode,'key':key,'scene':data(page)})
 for mode in ['pixel','native']:
  page.set_viewport_size({'width':1440,'height':1000});page.goto(args.url+'/?waterTime=2&render='+mode,wait_until='networkidle');page.wait_for_selector('#scene-host[data-render-state="ready"]');frames(page);page.mouse.move(10,500);page.locator('canvas').screenshot(path=str(OUT/f'{args.phase}-reference-{mode}.png'))
 assert not errors,errors;save(f'baseline-{args.phase}.json',{'phase':args.phase,'views':views,'fullWarmCaches':caches,'unhandledExceptions':errors});print(args.phase,'p95',sorted(samples)[int((len(samples)-1)*.95)],'max',max(samples),'warm',[(v['geometries'],v['textures'],v['programs'])for v in caches],flush=True);b.close()
