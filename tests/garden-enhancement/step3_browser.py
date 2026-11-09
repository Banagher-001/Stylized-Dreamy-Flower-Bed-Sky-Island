"""Actual production frames, motion controls, resources, reading and viewers."""
import argparse
import json
from playwright.sync_api import sync_playwright
from step3_common import *

parser = argparse.ArgumentParser()
parser.add_argument('--engine', choices=['chromium', 'firefox', 'webkit'], default='chromium')
parser.add_argument('--phase', choices=['before', 'after'], default='after')
parser.add_argument('--resume', action='store_true', help='reuse completed viewport checks for the identical production candidate')
args = parser.parse_args()
base = 'http://127.0.0.1:' + ('4176' if args.phase == 'before' else '4177')
rows, clocks, resources, capacities, errors = [], [], [], [], []
identity = json.loads((OUT / ('baseline-version.json' if args.phase == 'before' else 'build-verification.json')).read_text())['candidateId']
checkpoint = OUT / f'browser-{args.engine}-{args.phase}-progress.json'
completed = []
if args.resume and checkpoint.exists():
    previous = json.loads(checkpoint.read_text())
    assert previous['candidateId'] == identity and not previous['errors']
    rows, clocks, resources = previous['fixedFrames'], previous['clockViewerReading'], previous['resources']
    completed = previous['completedViewportWidths']

def checkpoint_viewport(width):
    completed.append(width)
    save(OUT, checkpoint.name, {'complete': False, 'candidateId': identity, 'engine': args.engine, 'phase': args.phase,
        'completedViewportWidths': completed, 'fixedFrames': rows, 'clockViewerReading': clocks, 'resources': resources, 'errors': errors})

with sync_playwright() as p:
    browser = launch(p, args.engine)
    for w, h, dpr in [(1440, 900, 1), (1366, 768, 1), (390, 844, 2)]:
        if w in completed:
            continue
        context = browser.new_context(viewport={'width': w, 'height': h}, device_scale_factor=dpr, has_touch=w == 390)
        context.add_init_script(probe)
        page = context.new_page()
        watch(page, errors)
        for t in ([2, 4, 6] if w == 1440 else [2]):
            load(page, base + f'/?waterTime={t}')
            page.evaluate('window.__originalCanvas=document.querySelector("canvas")')
            for mode in ['pixel', 'native']:
                page.locator(f'.tour-actions [data-mode={mode}]').click()
                for key, at in [('O', 0), ('W', 11.5)]:
                    visit(page, at)
                    page.mouse.move(10, h / 2)
                    frames(page)
                    name = f'{args.engine}-{w}-{mode}-{key}-t{t}-{args.phase}.png'
                    page.screenshot(path=str(OUT / name))
                    d = data(page)
                    assert abs(float(d['sceneTime']) - t) < 1e-6
                    assert d['orbStyle'] == 'lively'
                    rows.append({'file': name, 'viewport': [w, h], 'DPR': dpr, 'mode': mode, 'pose': key, 'time': t, 'scene': d,
                        'buffer': page.locator('canvas').evaluate('e=>({width:e.width,height:e.height,sampleWidth:e.dataset.sampleWidth,sampleHeight:e.dataset.sampleHeight})')})
        visit(page, 10.05)
        page.locator('[data-project-tab=live]').click()
        for mode in ['pixel', 'native']:
            page.locator(f'[data-project-mode={mode}]').click()
            frames(page)
            name = f'{args.engine}-{w}-{mode}-live-{args.phase}.png'
            page.mouse.move(10, h / 2)
            page.screenshot(path=str(OUT / name))
            assert page.locator('canvas').count() == 1
            rows.append({'file': name, 'viewport': [w, h], 'DPR': dpr, 'mode': mode, 'pose': 'C2-live', 'time': float(data(page)['sceneTime']), 'scene': data(page)})
        page.locator('.tour-project-close').click()
        frames(page)
        assert page.evaluate('window.__originalCanvas===document.querySelector("canvas")')
        if args.phase == 'before':
            checkpoint_viewport(w)
            context.close()
            continue
        # Frozen time: exact mode return and camera return, no independent flow clock.
        visit(page, 11.5)
        page.locator('.tour-actions [data-mode=native]').click()
        page.mouse.move(10, h / 2)
        before = pure_canvas(page)
        frozen = still(page)
        page.locator('.tour-actions [data-mode=pixel]').click()
        frames(page)
        page.locator('.tour-actions [data-mode=native]').click()
        frames(page)
        assert equal(before, pure_canvas(page)), (w, 'mode roundtrip')
        visit(page, 0)
        visit(page, 11.5)
        assert equal(before, pure_canvas(page)), (w, 'camera roundtrip')
        start, played = playing(page)
        pause(page)
        stopped = still(page)
        assert stopped['time'] != frozen['time'] and float(stopped['time']) >= played
        # Actual image dialog, while playing, freezes the shared environment.
        visit(page, 4.95)
        playing(page)
        position = page.evaluate('scrollY')
        trigger = page.locator('[data-film-station=B1] .film-image-button')
        trigger.click()
        page.wait_for_selector('.film-dialog[data-state=ready]')
        covered = still(page)
        page.locator('.film-dialog-close').click()
        page.wait_for_function('document.querySelector("#tour-host").dataset.overlayState==="closed"')
        page.wait_for_function('t=>Number(document.querySelector("#tour-host").dataset.sceneTime)>t', arg=float(covered['time']))
        page.wait_for_function('document.querySelector("[data-film-station=B1] .film-image-button")===document.activeElement')
        assert abs(page.evaluate('scrollY') - position) <= 1
        assert trigger.evaluate('e=>e===document.activeElement')
        # Inspect return focus before clicking another control (which moves it).
        pause(page)
        # Live owns the same canvas, archive covers it; close releases real video.
        visit(page, 10.05)
        position = page.evaluate('scrollY')
        page.locator('[data-project-tab=live]').click()
        page.locator('.tour-project-motion').click()
        t = float(data(page)['sceneTime'])
        page.wait_for_function('t=>Number(document.querySelector("#tour-host").dataset.sceneTime)>t+.1', arg=t)
        page.locator('.tour-project-motion').click()
        liveStill = still(page)
        page.locator('[data-project-view=archive]').click()
        page.locator('.tour-project-play').click()
        page.wait_for_function('document.querySelector("video")?.currentTime>.15')
        archiveStill = still(page)
        page.locator('.tour-project-close').click()
        frames(page)
        assert abs(page.evaluate('scrollY') - position) <= 1
        assert page.locator('canvas').count() == 1 and page.locator('video').count() == 0
        assert page.evaluate('window.__originalCanvas===document.querySelector("canvas")')
        # Exact existing text nodes/selection and second-step About mask.
        visit(page, 2.54)
        page.evaluate('''()=>{window.__nodes=[...document.querySelectorAll('.tour-reading-flow article')];window.__texts=window.__nodes.map(e=>e.textContent);
          const n=document.querySelector('.about-company').firstChild,r=document.createRange();r.selectNodeContents(n);getSelection().removeAllRanges();getSelection().addRange(r);window.__selected=getSelection().toString()}''')
        page.locator('#tour-layout-toggle').click()
        frames(page)
        assert page.locator('main').get_attribute('data-reading-mode') == 'stable'
        assert page.evaluate('getSelection().toString()===window.__selected')
        page.locator('#tour-layout-toggle').click()
        visit(page, 2.54)
        assert page.evaluate('window.__nodes.length===10&&window.__nodes.every((e,i)=>e===document.querySelectorAll(".tour-reading-flow article")[i]&&e.textContent===window.__texts[i])&&getSelection().toString()===window.__selected')
        page.evaluate('getSelection().removeAllRanges()')
        aboutMask = page.locator('.pillar-reading').evaluate('e=>({mask:getComputedStyle(e,"::before").maskImage,color:getComputedStyle(e,"::before").backgroundColor,feather:getComputedStyle(e).getPropertyValue("--veil-feather")})')
        name = f'{args.engine}-{w}-About-protected.png'
        page.screenshot(path=str(OUT / name))
        # Warm the exact resource paths, then repeat modes/camera/live ownership.
        for mode in ['pixel', 'native', 'pixel']:
            page.locator(f'.tour-actions [data-mode={mode}]').click()
            for _, at in VIEWS:
                visit(page, at)
        warm = {}
        # Live changes the original render-target size. Native releases its old
        # pixel target on that resize (5 vs 6 textures in BOTH Step2 and Step3).
        # Compare like modes after the same ownership/resize path, not native vs pixel.
        for mode in ['native', 'pixel']:
            page.locator(f'.tour-actions [data-mode={mode}]').click()
            visit(page, 10.05)
            page.locator('[data-project-tab=live]').click()
            frames(page)
            page.locator('.tour-project-close').click()
            visit(page, 0)
            warm[mode] = json.loads(data(page)['rendererStats'])
        cycles = []
        for i in range(10):
            mode = 'native' if i % 2 else 'pixel'
            page.locator(f'.tour-actions [data-mode={mode}]').click()
            visit(page, 10.05)
            page.locator('[data-project-tab=live]').click()
            frames(page)
            page.locator('.tour-project-close').click()
            visit(page, 0)
            stats = json.loads(data(page)['rendererStats'])
            if not all(stats[k] == warm[mode][k] for k in ['geometries', 'textures', 'programs']):
                save(OUT, f'resource-diagnostic-{args.engine}-{w}.json', {'warm': warm, 'iteration': i, 'stats': stats, 'previousCycles': cycles, 'scene': data(page)})
                raise AssertionError(('resource growth', warm, stats))
            cycles.append(stats)
        resources.append({'viewport': [w, h], 'DPR': dpr, 'warm': warm, 'tenModeAndViewerCycles': cycles})
        clocks.append({'viewport': [w, h], 'DPR': dpr, 'modeRoundtripExact': True, 'cameraRoundtripExact': True,
            'pause': frozen, 'afterPlay': stopped, 'imageCover': covered, 'live': liveStill, 'archive': archiveStill,
            'oneOriginalCanvas': True, 'imageFocusReturn': True, 'nativeScrollReturnWithin1px': True,
            'originalTextAndSelection': True, 'aboutMask': aboutMask, 'aboutFile': name})
        context.close()
        checkpoint_viewport(w)
        print(args.engine, w, 'frames / motion / viewer / resources passed', flush=True)
    if args.phase == 'after':
        for w, h, dpr in [(320, 568, 3), (844, 390, 2), (390, 844, 3)]:
            context = browser.new_context(viewport={'width': w, 'height': h}, device_scale_factor=dpr, has_touch=True)
            context.add_init_script(probe)
            page = context.new_page()
            watch(page, errors)
            load(page, base + '/?waterTime=2')
            if page.locator('main').get_attribute('data-reading-mode') != 'stable':
                page.locator('#tour-layout-toggle').click()
                frames(page)
            decode(page)
            page.locator('.tour-actions [data-mode=native]').click()
            frames(page)
            assert page.locator('.tour-reading-flow article').count() == 10
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
            stats = json.loads(data(page)['rendererStats'])
            bounds = page.locator('canvas').evaluate('e=>({css:e.getBoundingClientRect().toJSON(),width:e.width,height:e.height})')
            # Stable reading uses a 1.4:1 cover, which can be taller than a
            # landscape viewport. The DPR cap is relative to its CSS container.
            assert bounds['width'] <= bounds['css']['width'] * 2 + 1
            assert bounds['height'] <= bounds['css']['height'] * 2 + 1
            before = still(page)
            name = f'{args.engine}-{w}-capacity-dpr{dpr}.png'
            page.screenshot(path=str(OUT / name))
            capacities.append({'viewport': [w, h], 'DPR': dpr, 'mode': 'stable', 'tenArticles': True, 'overflow': False, 'stats': stats, 'bufferBounds': bounds, 'pause': before, 'file': name})
            context.close()
        # Reduced motion retains its explicit pause and stable-layout choice.
        context = browser.new_context(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
        context.add_init_script(probe)
        page = context.new_page()
        watch(page, errors)
        load(page, base + '/')
        assert page.locator('main').get_attribute('data-reading-mode') == 'stable'
        reduced = still(page)
        page.emulate_media(reduced_motion='no-preference')
        frames(page)
        assert page.locator('main').get_attribute('data-reading-mode') == 'stable'
        assert data(page)['sceneTime'] == reduced['time']
        capacities.append({'reducedMotion': True, 'pause': reduced, 'removedPreferenceDoesNotAutoplay': True})
        context.close()
    assert not errors, errors
    save(OUT, f'browser-{args.engine}-{args.phase}.json', {'passed': True, 'candidateId': identity, 'browser': browser.version,
        'engine': args.engine, 'phase': args.phase, 'fixedFrames': rows, 'clockViewerReading': clocks,
        'resources': resources, 'capacityAndPreference': capacities, 'errors': errors, 'physicalDevice': False})
    print('PASS', args.engine, args.phase, len(rows), 'original-size frames', flush=True)
    browser.close()
