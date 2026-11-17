from pathlib import Path
import json,os
from playwright.sync_api import sync_playwright
OUT=Path(__file__).parent;s=json.loads((OUT/'services-started.json').read_text());os.environ.update(s['browserEnvironment'])
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=gl','--ignore-gpu-blocklist'])
 try:
  page=browser.new_page(viewport={'width':1440,'height':900});page.goto(s['origin']+'/?waterTime=2',wait_until='domcontentloaded');page.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"');page.wait_for_timeout(200)
  page.evaluate('scrollTo({top:3.34/12.3*(document.documentElement.scrollHeight-innerHeight),behavior:"instant"})');page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"&&document.querySelector("#tour-host").dataset.readingStation==="A3"');page.wait_for_timeout(200)
  page.locator('[data-action=all]').click();page.wait_for_timeout(200);assert page.locator('.ar-overview-dialog').evaluate('(e)=>e.open');assert page.locator('.ar-catalog .ar-tool-card').count()==22
  page.screenshot(path=str(OUT/'visual-overview.png'))
  (OUT/'visual-overview.json').write_text(json.dumps(page.locator('.ar-overview-dialog').evaluate('(e)=>({open:e.open,bounds:e.getBoundingClientRect().toJSON(),cardCount:e.querySelectorAll(".ar-tool-card").length,focus:document.activeElement.id})'),ensure_ascii=False,indent=2)+'\n')
  page.keyboard.press('Escape');page.wait_for_timeout(150);assert not page.locator('dialog[open]').count()
 finally:browser.close()
