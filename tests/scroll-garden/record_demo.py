"""Record actual wheel-driven browser presentation; not a hardware FPS test."""
from pathlib import Path
import argparse
import json
import os
import time
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/evidence/scroll-garden-step-2'
parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:4173')
parser.add_argument('--fallback-only', action='store_true')
args = parser.parse_args()
executable = os.environ.get('CHROMIUM_EXECUTABLE', '/usr/bin/chromium')

if not args.fallback_only:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=executable, headless=True, args=['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        context = browser.new_context(viewport={'width':1280,'height':800}, record_video_dir=str(OUT/'raw-recording'), record_video_size={'width':1280,'height':800})
        page = context.new_page()
        page.goto(args.url+'/?tour=prototype&waterTime=2', wait_until='networkidle')
        page.wait_for_selector('#tour-host[data-render-state="ready"]')
        page.mouse.move(650,380)
        page.wait_for_timeout(700)
        start = time.monotonic()
        samples = []
        for target in [.5,1.74,3.7,4.95,8,9.14,11.1,11.5,12.3]:
            destination = page.evaluate('h=>h/12.3*(document.documentElement.scrollHeight-innerHeight)', target)
            for _ in range(200):
                current = page.evaluate('scrollY')
                if current >= destination-1:
                    break
                page.mouse.wheel(0,min(65,destination-current))
                page.wait_for_timeout(90)
            else:
                raise RuntimeError('Native scroll did not reach target')
            page.wait_for_timeout(650 if target in [1.74,4.95,9.14,11.5] else 240)
            samples.append({'requestedH':target,'actualH':float(page.locator('#tour-host').get_attribute('data-display-h'))})
        page.mouse.wheel(0,-700)
        page.wait_for_timeout(700)
        wall = time.monotonic()-start
        video = page.video
        context.close()
        video.save_as(str(OUT/'scroll-camera-demo.webm'))
        browser.close()
        (OUT/'demo-recording.json').write_text(json.dumps({'method':'actual browser screen recording driven by native wheel inputs','viewport':[1280,800],'wallSeconds':wall,'environmentTime':2,'environmentPausedForCameraComparison':True,'hardwareFPSProof':False,'samples':samples},ensure_ascii=False,indent=2)+'\n')
        print('Recorded actual wheel tour, wall seconds',round(wall,2),flush=True)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=executable, headless=True, args=['--no-sandbox','--disable-webgl'])
    page = browser.new_page(viewport={'width':1280,'height':800})
    errors, diagnostics = [], []
    page.on('pageerror',lambda error:errors.append(str(error)))
    page.on('console',lambda message:diagnostics.append({'type':message.type,'text':message.text}) if message.type in ['warning','error'] else None)
    page.goto(args.url+'/?tour=prototype',wait_until='networkidle')
    page.wait_for_selector('#tour-host[data-render-state="error"]')
    assert page.get_by_role('alert').inner_text()
    assert page.locator('canvas').count()==0
    assert page.locator('button:disabled').count()==8
    page.screenshot(path=str(OUT/'no-webgl.png'))
    page.locator('#tour-reference').click()
    page.wait_for_selector('#about')
    assert '枫叶互动' in page.locator('#about').inner_text()
    assert not errors
    (OUT/'fallback.json').write_text(json.dumps({'noWebGL':True,'readableAlert':True,'sceneControlsDisabled':8,'referenceLinkUsable':True,'unhandledExceptions':errors,'expectedInitializationDiagnostics':diagnostics},ensure_ascii=False,indent=2)+'\n')
    browser.close()
    print('No-WebGL fallback and return to profile passed',flush=True)
