from pathlib import Path
import json,os
from playwright.sync_api import sync_playwright
OUT=Path(__file__).parent;s=json.loads((OUT/'services-started.json').read_text());os.environ.update(s['browserEnvironment'])
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist'])
 try:
  page=b.new_page(viewport={'width':1440,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('console',lambda m:errors.append(m.text) if m.type=='error' else None)
  page.goto(s['origin']+'/?waterTime=2',wait_until='domcontentloaded');page.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=90000);page.wait_for_timeout(400)
  state=page.evaluate('({main:{...document.querySelector("main").dataset},host:{...document.querySelector("#tour-host").dataset},about:document.querySelector(".about-pillar-reader").outerHTML.slice(0,750)})')
  (OUT/'probe-1.json').write_text(json.dumps({'errors':errors,'state':state},ensure_ascii=False,indent=2)+'\n')
  print(json.dumps({'errors':errors,'mode':state['main'].get('readingMode'),'render':state['host'].get('renderState'),'capacity':json.loads(state['main'].get('readingCapacity','{}'))},ensure_ascii=False))
  page.screenshot(path=str(OUT/'probe-1.png'))
 finally:b.close()
