from pathlib import Path
import os,json,hashlib
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).parent
s=json.loads((OUT/'services-started.json').read_text());os.environ.update(s['browserEnvironment'])
sources=[p for p in (ROOT/'src/tour').rglob('*') if p.is_file()]+list((ROOT/'src/assets/tool-marks').glob('*.svg'))
report={'purpose':'final visual capture; not additional counted tests','sources':[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sources],'errors':[],'screenshots':[]}
with sync_playwright() as play:
 b=play.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist']);p=b.new_page(viewport={'width':1440,'height':900});p.on('pageerror',lambda e:report['errors'].append(str(e)))
 p.goto(s['origin']+'/?waterTime=2');p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=90000);p.evaluate('scrollTo({top:3.34/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})');p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.trackState==="running"');p.wait_for_timeout(1100)
 for name in ['final-desktop-default','final-desktop-help','final-desktop-help-scrolled','final-desktop-fixed-help']:
  if name=='final-desktop-help':p.locator('[data-action=help]').click();p.wait_for_timeout(500)
  elif name=='final-desktop-help-scrolled':
   r=p.locator('.ar-tool-help-panel').bounding_box();p.mouse.move(r['x']+r['width']/2,r['y']+r['height']*.7);p.mouse.wheel(0,220);p.wait_for_timeout(300)
  elif name=='final-desktop-fixed-help':
   p.keyboard.press('Escape');p.wait_for_timeout(100);f=p.locator('.ar-tool-card[data-tool-id=comfyui] .ar-card-front').bounding_box();p.mouse.move(f['x']+f['width']/2,f['y']+f['height']*.45);p.wait_for_function('document.querySelector(".ar-tools-browser").dataset.hoverState==="reading"');r=p.locator('.ar-tool-card[data-tool-id=comfyui] button').bounding_box();p.mouse.click(r['x']+r['width']/2,r['y']+r['height']/2);p.wait_for_timeout(400);p.locator('[data-action=help]').click();p.wait_for_timeout(300)
  p.screenshot(path=str(OUT/f'{name}.png'));report['screenshots'].append(f'{name}.png')
 b.close();report['browserClosed']=True
assert not report['errors'],report['errors']
(OUT/'final-capture.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'screenshots':report['screenshots'],'browserClosed':True}))
