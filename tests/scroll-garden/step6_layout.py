"""Initial/final measured layouts of the four film stations, with source receipts."""
from pathlib import Path
import hashlib,json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/scroll-garden-step-6'
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']);page=b.new_page(viewport={'width':1440,'height':900});issues=[];page.on('pageerror',lambda e:issues.append(str(e)))
 page.goto('http://127.0.0.1:4173/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]');views=[]
 for width,height in [(1440,900),(1366,768),(390,844)]:
  page.set_viewport_size({'width':width,'height':height});page.wait_for_function('()=>{const e=document.querySelector("#tour-host"),r=e.getBoundingClientRect();return Math.abs(Number(e.dataset.aspect)-r.width/r.height)<.00001}')
  for key,h in [('B1',4.95),('B2',5.95),('B3',6.84),('B4',7.64)]:
   page.evaluate('h=>scrollTo({top:h/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})',h);page.wait_for_function('h=>{const d=document.querySelector("#tour-host").dataset;return d.cameraState==="settled"&&Math.abs(Number(d.displayH)-h)<.003}',arg=h);page.wait_for_function('()=>[...document.querySelectorAll(".film-reading img[src]")].every(i=>i.complete&&i.naturalWidth>0)');page.evaluate('()=>document.fonts.ready.then(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))))');page.mouse.move(10,height/2)
   r=page.locator('.film-reading').evaluate('e=>({data:{...e.dataset},rect:e.getBoundingClientRect().toJSON(),nav:document.querySelector(".tour-stops").getBoundingClientRect().toJSON(),text:e.innerText,buttons:[...e.querySelectorAll("article:not([hidden]) button")].map(b=>b.getBoundingClientRect().toJSON())})');views.append({'viewport':[width,height],'station':key,**r,'scene':page.locator('#tour-host').evaluate('e=>({...e.dataset})')});page.screenshot(path=str(OUT/f'layout-{width}-{key}.png'))
 print([(v['viewport'],v['station'],v['data']['fits'],round(v['rect']['height'],2),[(round(b['width']),round(b['height']))for b in v['buttons']])for v in views]);assert not issues
 (OUT/'layout-initial.json').write_text(json.dumps({'views':views,'unhandledExceptions':issues,'runtimeSourceSha256':{str(f):hashlib.sha256(f.read_bytes()).hexdigest()for f in Path('src/tour').glob('*')if f.suffix in ['.ts','.css']}},ensure_ascii=False,indent=2)+'\n');b.close()
