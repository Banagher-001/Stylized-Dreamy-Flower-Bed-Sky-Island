"""Measured layout iteration and actual clean-canvas cover capture."""
import argparse,hashlib,json
from PIL import Image
from playwright.sync_api import sync_playwright
from step7_common import *
parser=argparse.ArgumentParser();parser.add_argument('--capture-cover',action='store_true');args=parser.parse_args()
with sync_playwright() as p:
    b=launch(p);page=b.new_page(viewport={'width':1440,'height':900});issues=[];page.on('pageerror',lambda e:issues.append(str(e)))
    page.goto('http://127.0.0.1:5173/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]');views=[]
    if args.capture_cover:
        go(page,10.05);page.locator('.experiment-entry-actions [data-project-tab=live]').click();page.wait_for_selector('.tour-project-dialog[open]');frames(page)
        # Hide only project chrome. The existing live-view camera/canvas remains real.
        page.add_style_tag(content='.tour-project-dialog,.tour-prototype > :not(.tour-stage):not(.tour-scroll-space):not(.tour-viewport-probe){visibility:hidden !important;}')
        # Capture the narrative overview, using the real canvas with no reading overlays.
        page.locator('.tour-project-dialog').evaluate('e=>e.close()');page.wait_for_function('document.querySelector("#tour-host").dataset.overlayState==="closed"');go(page,0);frames(page)
        raw=OUT/'cover-current-canvas.png';page.locator('canvas').screenshot(path=str(raw));Image.open(raw).save(ROOT/'src/assets/courtyard-interactive-cover.webp','WEBP',lossless=True)
        receipt={'source':'actual single browser canvas; all three shafts completed; narrative overview O; no invented imagery','viewport':[1440,900],'canvasSize':list(Image.open(raw).size),'environmentTime':2,'renderMode':'pixel','scene':data(page),'assetSha256':hashlib.sha256((ROOT/'src/assets/courtyard-interactive-cover.webp').read_bytes()).hexdigest(),'runtimeSourceSha256':{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest()for f in (ROOT/'src/tour').glob('*')if f.suffix in ['.ts','.css']}}
        save('cover-provenance.json',receipt);print('Captured actual cover',receipt['canvasSize'],flush=True);b.close();raise SystemExit
    for width,height in [(1440,900),(1366,768),(390,844)]:
        resize(page,width,height)
        for key,h,y in STOPS:
            go(page,h);frames(page);page.mouse.move(10,height/2)
            r=page.locator('.experiment-reading').evaluate('e=>({data:{...e.dataset},rect:e.getBoundingClientRect().toJSON(),nav:document.querySelector(".tour-stops").getBoundingClientRect().toJSON(),text:e.innerText,buttons:[...e.querySelectorAll("article:not([hidden]) button")].map(b=>b.getBoundingClientRect().toJSON())})')
            views.append({'viewport':[width,height],'station':key,**r,'scene':data(page)});page.screenshot(path=str(OUT/f'layout-{width}-{key}.png'))
        go(page,10.05);page.locator('[data-project-tab=live]').click();frames(page);page.screenshot(path=str(OUT/f'layout-{width}-live.png'));page.locator('[data-project-view=archive]').click();frames(page);page.screenshot(path=str(OUT/f'layout-{width}-archive.png'));page.locator('.tour-project-close').click();settled(page,10.05)
    save('layout-initial.json',{'views':views,'exceptions':issues});print([(v['viewport'],v['station'],v['data']['fits'],v['scene']['experimentMagicStatus'],round(v['rect']['height']),round(v['rect']['top']),round(v['nav']['top']))for v in views]);assert not issues,issues;b.close()
