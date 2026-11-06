"""Visual iteration, fixed time samples and clean current-cover export."""
import argparse,hashlib
from PIL import Image
from playwright.sync_api import sync_playwright
from step9_common import *
parser=argparse.ArgumentParser();parser.add_argument('--capture-cover',action='store_true');args=parser.parse_args()
with sync_playwright()as p:
 b=launch(p);page=b.new_page(viewport={'width':1440,'height':900});issues=[];page.on('pageerror',lambda e:issues.append({'type':'exception','text':str(e)}));page.on('console',lambda m:issues.append({'type':m.type,'text':m.text})if m.type in ['error','warning']else None)
 ready(page,'http://127.0.0.1:5173/?tour=prototype&waterTime=2');assert data(page)['fountainStyle']=='refined'and data(page)['orbStyle']=='lively'
 if args.capture_cover:
  page.add_style_tag(content='.tour-prototype > :not(.tour-stage):not(.tour-scroll-space):not(.tour-viewport-probe){visibility:hidden!important;}');go(page,0);frames(page)
  raw=OUT/'cover-current-canvas.png';page.locator('canvas').screenshot(path=str(raw));asset=ROOT/'src/assets/courtyard-orb-cover.webp';Image.open(raw).save(asset,'WEBP',lossless=True)
  save('cover-provenance.json',{'source':'actual final single canvas; refined pool and lively orb; narrative O; no generated scene','viewport':[1440,900],'canvasSize':list(Image.open(raw).size),'environmentTime':2,'renderMode':'pixel','scene':data(page),'asset':str(asset.relative_to(ROOT)),'assetSha256':hashlib.sha256(asset.read_bytes()).hexdigest(),'runtimeSourceSha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest()for f in (ROOT/'src').rglob('*.ts')}})
  print('Captured actual cover',Image.open(raw).size,flush=True)
 else:
  for time in [2,4,6,8]:
   ready(page,f'http://127.0.0.1:5173/?tour=prototype&waterTime={time}')
   for mode in ['pixel','native']:
    page.locator(f'.tour-actions [data-mode={mode}]').click()
    for key,h in [('W',11.5),('O',0)]:
     go(page,h);frames(page);page.mouse.move(10,450);page.screenshot(path=str(OUT/f'initial-{time}-{mode}-{key}.png'))
  save('layout-initial.json',{'diagnostics':issues,'bindings':data(page)['fountainResources']});print('Initial views captured;diagnostics',issues,flush=True)
 assert not issues,issues;b.close()
