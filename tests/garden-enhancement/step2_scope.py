"""Protect full canvas, other chapters, viewers, reference page and GPU budget."""
import argparse
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
from step2_common import *

parser = argparse.ArgumentParser()
parser.add_argument('--url', default='http://127.0.0.1:4177')
parser.add_argument('--baseline', default='http://127.0.0.1:4176')
parser.add_argument('--out', type=Path, default=ROOT / 'docs/evidence/garden-enhancement-step-2')
args = parser.parse_args()
OUT = args.out.resolve()
OUT.mkdir(parents=True, exist_ok=True)
paired, chapters, resources, viewers, errors = [], [], [], [], []

with sync_playwright() as p:
    browser = launch(p)
    for w, h, dpr in [(1440, 900, 1), (1366, 768, 1), (390, 844, 2)]:
        context = browser.new_context(viewport={'width': w, 'height': h}, device_scale_factor=dpr)
        old, new = context.new_page(), context.new_page()
        for page, base in [(old, args.baseline), (new, args.url)]:
            page.on('pageerror', lambda e: errors.append(str(e)))
            load(page, base + '/?waterTime=2')
            for mode in ['pixel', 'native', 'pixel']:
                page.locator(f'.tour-actions [data-mode={mode}]').click()
                for _, at in VIEWS:
                    visit(page, at)
        before_resource = json.loads(data(new)['rendererStats'])
        for mode in ['pixel', 'native']:
            for page in [old, new]:
                page.bring_to_front()
                page.locator(f'.tour-actions [data-mode={mode}]').click()
            for key, at in [('A2', 2.54), ('W', 11.5)]:
                images = []
                for page in [old, new]:
                    visit(page, at)
                    images.append(pure_canvas(page))
                assert pixels_equal(*images), (w, mode, key)
                paired.append({'viewport': [w, h], 'DPR': dpr, 'mode': mode, 'pose': key, 'fullGPUCanvasExact': True})
                if (w == 1440 and mode == 'pixel') or (w == 390 and mode == 'native'):
                    for raw, label in zip(images, ['before', 'after']):
                        (OUT / f'pure-{w}-{mode}-{key}-{label}.png').write_bytes(raw)
            if w in [1440, 390]:
                for key, at in [('B1', 4.95), ('C2', 10.05)]:
                    images = []
                    for page in [old, new]:
                        visit(page, at)
                        page.wait_for_function('Array.from(document.querySelectorAll(".tour-reading-flow img")).every(e=>!e.currentSrc||e.complete)')
                        page.evaluate('Promise.all(Array.from(document.querySelectorAll(".film-reading img,.experiment-reading img")).filter(e=>e.currentSrc).map(e=>e.decode()))')
                        page.mouse.move(10, h / 2)
                        frames(page)
                        images.append(page.screenshot())
                    if not pixels_equal(*images):
                        for raw, label in zip(images, ['before', 'after']):
                            (OUT / f'chapter-failure-{w}-{mode}-{key}-{label}.png').write_bytes(raw)
                        save(OUT, 'chapter-failure.json', {'viewport': [w, h], 'mode': mode, 'chapter': key,
                            'before': data(old), 'after': data(new), 'method': 'actual full pages after image decode, no masks'})
                        raise AssertionError((w, mode, key, 'other chapter full page'))
                    chapters.append({'viewport': [w, h], 'mode': mode, 'chapter': key, 'actualFullPageExact': True})
        # Ten warm mode round trips: compare actual baseline in each matching mode.
        cycles = []
        for i in range(10):
            mode = 'native' if i % 2 else 'pixel'
            stats = []
            for page in [old, new]:
                page.bring_to_front()
                page.locator(f'.tour-actions [data-mode={mode}]').click()
                visit(page, 0)
                stats.append(json.loads(data(page)['rendererStats']))
            keys = ['geometries', 'textures', 'programs', 'calls', 'triangles', 'outputWidth', 'outputHeight']
            assert all(stats[0][k] == stats[1][k] for k in keys), stats
            assert all(stats[1][k] == before_resource[k] for k in ['geometries', 'textures', 'programs'])
            cycles.append({'mode': mode, 'before': stats[0], 'after': stats[1]})
        resources.append({'viewport': [w, h], 'DPR': dpr, 'prewarmedCandidate': before_resource,
            'tenModeCycles': cycles, 'gpuResourceIncrease': 0})
        if w in [1440, 390]:
            new.bring_to_front()
            visit(new, 4.95)
            y = new.evaluate('scrollY')
            new.locator('[data-film-station=B1] .film-image-button').click()
            new.wait_for_selector('.film-dialog[data-state=ready]')
            new.locator('.film-dialog-close').click()
            new.wait_for_function('document.querySelector("#tour-host").dataset.overlayState==="closed"')
            frames(new)
            assert abs(new.evaluate('scrollY') - y) <= 1
            visit(new, 10.05)
            y = new.evaluate('scrollY')
            new.locator('[data-project-tab=live]').click()
            frames(new)
            assert new.locator('canvas').count() == 1
            assert new.locator('.pillar-reading').evaluate('e=>getComputedStyle(e).visibility') == 'hidden'
            new.locator('[data-project-view=archive]').click()
            new.locator('.tour-project-play').click()
            new.wait_for_function('document.querySelector("video")?.currentTime>.15')
            new.locator('.tour-project-close').click()
            new.wait_for_function('document.querySelector("#tour-host").dataset.overlayState==="closed"')
            frames(new)
            assert abs(new.evaluate('scrollY') - y) <= 1 and new.locator('video').count() == 0 and new.locator('canvas').count() == 1
            viewers.append({'viewport': [w, h], 'imageReturnExactWithin1CssPixel': True,
                'liveArchiveVideoReturnExactWithin1CssPixel': True, 'oneCanvas': True, 'videoReleased': True,
                'aboutBackgroundHiddenDuringViewer': True})
        context.close()
    # Legacy page does not load the changed garden styles.
    references = []
    context = browser.new_context(viewport={'width': 1440, 'height': 1000})
    for mode in ['pixel', 'native']:
        images = []
        for base in [args.baseline, args.url]:
            page = context.new_page()
            page.bring_to_front()
            page.goto(base + f'/?tour=reference&waterTime=2&render={mode}', wait_until='networkidle')
            page.wait_for_selector('#scene-host[data-render-state=ready]')
            frames(page)
            page.mouse.move(10, 500)
            images.append(page.screenshot())
            page.close()
        assert pixels_equal(*images), mode
        references.append({'mode': mode, 'referenceActualFullPageExact': True})
    context.close()
    assert not errors, errors
    save(OUT, 'scene-resource-viewer-scope.json', {'passed': True, 'browser': browser.version,
        'pureCanvasPairs': paired, 'pureCanvasMethod': 'entire original canvas rectangle; DOM UI hidden equally only for GPU isolation, all scene and GPU lettering retained; no pixel crop/masks/tolerance; separate unaltered page screenshots prove the changed background',
        'otherChapterFullPagePairs': chapters, 'legacyFullPagePairs': references,
        'warmResourceCases': resources, 'viewerCases': viewers, 'exceptions': errors})
    print('PASS', len(paired), 'full canvas pairs,', len(chapters), 'other chapter pages,2legacy pages,3warm resource cases,2viewer cases', flush=True)
    browser.close()
