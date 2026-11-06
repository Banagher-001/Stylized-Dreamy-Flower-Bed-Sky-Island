"""Inspect the real scene geometry through Vite; no application test globals."""
from pathlib import Path
import argparse
import json
import os
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/evidence/scroll-garden-step-2'
parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:5173')
args = parser.parse_args()
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_EXECUTABLE', '/usr/bin/chromium'), headless=True, args=['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    page.goto(args.url + '/?tour=prototype&waterTime=2', wait_until='networkidle')
    page.wait_for_selector('#tour-host[data-render-state="ready"]')
    aspects = []
    for width, height in [(1440,900),(1366,768),(390,844)]:
        page.set_viewport_size({'width': width, 'height': height})
        page.wait_for_function('()=>{const h=document.querySelector("#tour-host"),r=h.getBoundingClientRect();return Math.abs(Number(h.dataset.aspect)-r.width/r.height)<.00001;}')
        aspects.append(page.locator('#tour-host').evaluate('e=>{const r=e.getBoundingClientRect();return r.width/r.height;}'))
    result = page.evaluate('async aspects=>{const m=await import("/tests/scroll-garden/inspect_route.js");return m.inspectRoute(aspects);}', aspects)
    before = json.loads((OUT/'reference-instances-before.json').read_text())
    assert result['instances'] == before, 'Scene instance data changed'
    plan = json.loads((ROOT/'docs/scroll-garden/step-1-plan.json').read_text())
    assert result['totalH'] == plan['progressModel']['totalH']
    assert [(s['id'],s['start'],s['end']) for s in result['stages']] == [(s['id'],s['startH'],s['endH']) for s in plan['stages']]
    result['stage1TimelineMatches'] = True
    result['instanceBaselineMatches'] = True
    (OUT/'route-geometry.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print('Route samples:',result['geometricSamples'],'boundary delta:',result['maximumBoundaryDelta'],'scene instances and first-step timeline unchanged')
    browser.close()
