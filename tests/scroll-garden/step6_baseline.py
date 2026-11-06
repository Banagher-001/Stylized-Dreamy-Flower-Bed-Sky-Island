"""Same real-wheel performance sampling before/after step 6; baseline screenshots."""
from pathlib import Path
import argparse,ast,json,os
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/scroll-garden-step-6'
parser=argparse.ArgumentParser();parser.add_argument('--phase',choices=['before','after'],default='before');parser.add_argument('--url',default='http://127.0.0.1:4173');args=parser.parse_args()
tree=ast.parse((ROOT/'tests/scroll-garden/step2_browser.py').read_text());PROBE=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='PROBE'for t in n.targets))
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);context=b.new_context(viewport={'width':1440,'height':900});context.add_init_script(PROBE);page=context.new_page();issues=[];page.on('pageerror',lambda e:issues.append(str(e)))
 page.goto(args.url+'/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]')
 assert ('STEP 05'if args.phase=='before'else'STEP 06')in page.title()
 if args.phase=='after':assert page.locator('#tour-host').get_attribute('data-magic-status')=='ready'
 def go(h):
  page.evaluate('h=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})',h);page.wait_for_function('h=>{const d=document.querySelector("#tour-host").dataset;return d.cameraState==="settled"&&Math.abs(Number(d.displayH)-h)<.003}',arg=h)
 for h in [1.74,2.54,3.34,4.95,5.95,6.84,7.64,4.95]:go(h)
 page.wait_for_function('()=>[...document.querySelectorAll(".film-reading img[src]")].every(i=>i.complete&&i.naturalWidth>0)');page.wait_for_timeout(200);page.evaluate('window.__tourProbe.settles=[]');page.mouse.move(1100,260)
 for delta in [96]*15+[-96]*15:
  prior=page.evaluate('scrollY');page.mouse.wheel(0,delta);page.wait_for_function('y=>Math.abs(scrollY-y)>1',arg=prior);page.wait_for_function('()=>document.querySelector("#tour-host").dataset.cameraState==="settled"');page.wait_for_timeout(20)
 latency=page.evaluate('window.__tourProbe.settles');assert len(latency)==30,len(latency)
 perf={'method':'same browser, viewport and 30 native wheel stops; no screenshots during measurement','viewport':[1440,900],'environmentTime':2,'samplesMs':latency,'p95Ms':sorted(latency)[int((len(latency)-1)*.95)],'maxMs':max(latency),'hardwareFPSProof':False,'phase':args.phase,'runtimeSourceSha256':{str(f):__import__('hashlib').sha256(f.read_bytes()).hexdigest()for f in Path('src/tour').glob('*')if f.suffix in ['.ts','.css']}}
 (OUT/f'latency-{args.phase}.json').write_text(json.dumps(perf,ensure_ascii=False,indent=2)+'\n');print(args.phase,'p95',perf['p95Ms'],'max',perf['maxMs'],flush=True)
 views=[]
 for w,h in [(1440,900),(1366,768),(390,844)]:
  page.set_viewport_size({'width':w,'height':h});page.wait_for_function('()=>{const e=document.querySelector("#tour-host"),r=e.getBoundingClientRect();return Math.abs(Number(e.dataset.aspect)-r.width/r.height)<.00001}');page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
  for key,at in ([('A1',1.74),('A2',2.54),('A3',3.34),('B1',4.95)]+([('B2',5.95),('B3',6.84),('B4',7.64)]if args.phase=='after'else[])):
   go(at);page.mouse.move(10,h/2);page.screenshot(path=str(OUT/f'{args.phase}-{w}-{key}.png'));views.append({'viewport':[w,h],'station':key,'scene':page.locator('#tour-host').evaluate('e=>({...e.dataset})')})
 if args.phase in ['before','after']:
  page.set_viewport_size({'width':1440,'height':900});page.wait_for_function('()=>{const e=document.querySelector("#tour-host"),r=e.getBoundingClientRect();return Math.abs(Number(e.dataset.aspect)-r.width/r.height)<.00001}');page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
  page.get_by_role('button',name='正常画面',exact=True).click()
  for key,at in ([('A1',1.74),('A2',2.54),('A3',3.34),('B1',4.95)]+([('B2',5.95),('B3',6.84),('B4',7.64)]if args.phase=='after'else[])):
   go(at);page.mouse.move(10,450);page.screenshot(path=str(OUT/f'{args.phase}-native-{key}.png'))
 if args.phase=='before':
  page.set_viewport_size({'width':1440,'height':1000})
  for mode in ['pixel','native']:
   page.goto(args.url+'/?waterTime=2&render='+mode,wait_until='networkidle');page.wait_for_selector('#scene-host[data-render-state="ready"]');page.mouse.move(10,500);page.locator('canvas').screenshot(path=str(OUT/f'before-reference-{mode}.png'))
 assert not issues
 (OUT/f'baseline-{args.phase}.json').write_text(json.dumps({'phase':args.phase,'views':views,'exceptions':issues},ensure_ascii=False,indent=2)+'\n');b.close()
