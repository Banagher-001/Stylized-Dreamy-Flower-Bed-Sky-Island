"""Compare candidate default home with the independent Step11 prototype baseline.

Run baseline on :4174 and candidate on :4175 with scripts/serve-dist.mjs.
Requires Pillow, Playwright and the sibling Step11/Step2 helpers.
"""
import argparse
from io import BytesIO
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright
from step11_common import launch, ready, resize, frames, go, data
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--out', type=Path, required=True)
args = parser.parse_args()
out = args.out.resolve()
out.mkdir(parents=True, exist_ok=True)
CSS = '.tour-header,.tour-heading,.tour-stops,.tour-footer,.pillar-reading,.film-reading,.experiment-reading,.pillar-reading-link,.film-reading-link,.experiment-reading-link,.tour-flow-intro,.tour-flow-label,.tour-flow-water,.tour-flow-ending,.tour-skip{visibility:hidden!important}'
checks = []
with sync_playwright() as p:
    browser = launch(p)
    old = browser.new_page(viewport={'width': 1440, 'height': 900})
    new = browser.new_page(viewport={'width': 1440, 'height': 900})
    for page, url in [(old, 'http://127.0.0.1:4174/?tour=prototype&waterTime=2'), (new, 'http://127.0.0.1:4175/?waterTime=2')]:
        ready(page, url)
        page.add_style_tag(content=CSS)
    for w, h in [(1440, 900), (1366, 768), (390, 844)]:
        for page in [old, new]:
            page.bring_to_front()
            resize(page, w, h)
        for mode in ['pixel', 'native']:
            for page in [old, new]:
                page.bring_to_front()
                page.locator(f'.tour-actions [data-mode={mode}]').evaluate('e=>e.click()')
            for key, at in [('O', 0), ('A2', 2.54), ('B2', 5.95), ('C2', 10.05), ('W', 11.5), ('S99', 12.3)]:
                images, states = [], []
                for page, label in [(old, 'before'), (new, 'after')]:
                    page.bring_to_front()
                    go(page, at)
                    frames(page)
                    page.mouse.move(10, h / 2)
                    image = page.locator('canvas').screenshot()
                    if (w == 1440 and key in ['O', 'W']) or (w == 390 and key == 'C2'):
                        (out / f'scene-{w}-{mode}-{key}-{label}.png').write_bytes(image)
                    images.append(Image.open(BytesIO(image)).convert('RGB'))
                    states.append(data(page))
                assert ImageChops.difference(*images).getbbox() is None, (w, mode, key)
                keys = ['cameraPosition', 'cameraTarget', 'viewHeight', 'sceneTime', 'readingStation', 'magicFrame', 'filmStation', 'filmMagicFrame', 'experimentStation', 'experimentMagicFrame']
                assert all(states[0][k] == states[1][k] for k in keys), (w, mode, key)
                checks.append({'viewport': [w, h], 'mode': mode, 'pose': key, 'fullCanvasExact': True, 'cameraTimeGPUInscriptionsExact': True})
    for mode in ['pixel', 'native']:
        images = []
        for page, url in [(old, f'http://127.0.0.1:4174/?waterTime=2&render={mode}'), (new, f'http://127.0.0.1:4175/?tour=reference&waterTime=2&render={mode}')]:
            page.bring_to_front()
            page.set_viewport_size({'width': 1440, 'height': 1000})
            page.goto(url, wait_until='networkidle')
            page.wait_for_selector('#scene-host[data-render-state=ready]')
            frames(page)
            page.mouse.move(10, 500)
            images.append(Image.open(BytesIO(page.locator('canvas').screenshot())).convert('RGB'))
        assert ImageChops.difference(*images).getbbox() is None, mode
        checks.append({'mode': mode, 'referenceFullCanvasExact': True})
    browser.close()
(out / 'scene-comparison.json').write_text(json.dumps({'passed': True, 'freshPairs': len(checks), 'checks': checks, 'method': 'Full canvas, zero channel tolerance, no crop or masks; DOM reading ink hidden equally; all GPU decoration retained. Candidate root vs Step11 prototype; reference query vs Step11 root.'}, ensure_ascii=False, indent=2) + '\n')
print('PASS', len(checks), 'exact full-scene/reference pairs', flush=True)
