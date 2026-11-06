"""Matched C-route wheel benchmark, screenshots, route state and warm cache receipts."""
import argparse, hashlib
from playwright.sync_api import sync_playwright
from step7_common import *

parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['before','after'],required=True);parser.add_argument('--url',default='http://127.0.0.1:4173');args=parser.parse_args()
with sync_playwright() as p:
    b=launch(p);context=b.new_context(viewport={'width':1440,'height':900});context.add_init_script(PROBE);page=context.new_page();issues=[]
    page.on('pageerror',lambda e:issues.append(str(e)))
    page.goto(args.url+'/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]')
    assert ('STEP 06' if args.phase=='before' else 'STEP 07') in page.title()
    caches=[]
    for mode in ['pixel','native','pixel']:
        page.locator(f'.tour-actions [data-mode={mode}]').click()
        for h in [0,1.74,2.54,3.34,4.95,5.95,6.84,7.64,9.14,10.05,10.83,11.5,0,10.05]:go(page,h)
        frames(page);caches.append(__import__('json').loads(data(page)['rendererStats']))
    go(page,9.14);page.wait_for_timeout(200);page.evaluate('window.__tourProbe.settles=[]');page.mouse.move(1100,260)
    for delta in [96]*15+[-96]*15:
        prior=page.evaluate('scrollY');page.mouse.wheel(0,delta);page.wait_for_function('y=>Math.abs(scrollY-y)>1',arg=prior)
        page.wait_for_function('()=>document.querySelector("#tour-host").dataset.cameraState==="settled"');page.wait_for_timeout(20)
    samples=page.evaluate('window.__tourProbe.settles');assert len(samples)==30,len(samples)
    save(f'latency-{args.phase}.json',{'phase':args.phase,'method':'same warmed C-route, Chromium SwiftShader, 1440x900, waterTime=2; 30 real wheel stops; no screenshots/parallel browsers during sampling','samplesMs':samples,'p95Ms':sorted(samples)[int((len(samples)-1)*.95)],'maxMs':max(samples),'hardwareFPSProof':False,'runtimeSourceSha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (ROOT/'src/tour').glob('*') if f.suffix in ['.ts','.css']}})
    views=[]
    for width,height in [(1440,900),(1366,768),(390,844)]:
        resize(page,width,height)
        for key,h in OLD+[('C1',9.14),('C2',10.05),('C3',10.83),('O',0),('W',11.5)]:
            go(page,h);frames(page);page.mouse.move(10,height/2);page.screenshot(path=str(OUT/f'{args.phase}-{width}-{key}.png'))
            views.append({'viewport':[width,height],'station':key,'scene':data(page)})
    resize(page,1440,900);page.locator('.tour-actions [data-mode=native]').click()
    for key,h in OLD+[('C1',9.14),('C2',10.05),('C3',10.83)]:
        go(page,h);frames(page);page.mouse.move(10,450);page.screenshot(path=str(OUT/f'{args.phase}-native-{key}.png'))
    for mode in ['pixel','native']:
        page.set_viewport_size({'width':1440,'height':1000});page.goto(args.url+'/?waterTime=2&render='+mode,wait_until='networkidle');page.wait_for_selector('#scene-host[data-render-state="ready"]');frames(page);page.mouse.move(10,500);page.locator('canvas').screenshot(path=str(OUT/f'{args.phase}-reference-{mode}.png'))
    assert not issues,issues
    save(f'baseline-{args.phase}.json',{'phase':args.phase,'views':views,'warmCaches':caches,'exceptions':issues})
    print(args.phase, 'p95',sorted(samples)[int((len(samples)-1)*.95)],'max',max(samples),'cache',[(v['geometries'],v['textures'],v['programs'])for v in caches],flush=True);b.close()
