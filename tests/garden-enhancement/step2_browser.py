"""Actual before/after feather, readability and input checks for Step2."""
import argparse
import json
from pathlib import Path
import re
from playwright.sync_api import sync_playwright
from step2_common import *

parser = argparse.ArgumentParser()
parser.add_argument('--engine', choices=['chromium', 'firefox', 'webkit'], default='chromium')
parser.add_argument('--url', default='http://127.0.0.1:4177')
parser.add_argument('--baseline', default='http://127.0.0.1:4176')
parser.add_argument('--out', type=Path, default=ROOT / 'docs/evidence/garden-enhancement-step-2')
args = parser.parse_args()
OUT = args.out.resolve()
OUT.mkdir(parents=True, exist_ok=True)
rows, measures, extra, errors = [], [], [], []
STATIONS = [('A1', 1.3, 2.1), ('A2', 2.1, 2.9), ('A3', 2.9, 3.7)]

def picture(page, name):
    page.bring_to_front()
    frames(page)
    page.mouse.move(10, page.viewport_size['height'] / 2)
    page.screenshot(path=str(OUT / name))
    return name

def state(page):
    return page.locator('.pillar-reading').evaluate('''e=>({rect:e.getBoundingClientRect().toJSON(),state:{...e.dataset},text:e.textContent,
      articles:[...e.querySelectorAll('article')].map(a=>({id:a.dataset.readingStation,aria:a.getAttribute('aria-hidden'),inert:a.inert,body:a.querySelector('.pillar-reading-body').getBoundingClientRect().toJSON(),title:a.querySelector('h2').getBoundingClientRect().toJSON()}))})''')

with sync_playwright() as p:
    browser = launch(p, args.engine)
    for w, h, dpr in [(1440, 900, 1), (1366, 768, 1), (390, 844, 2)]:
        options = {'viewport': {'width': w, 'height': h}, 'device_scale_factor': dpr, 'has_touch': w == 390}
        if args.engine != 'firefox':
            options['is_mobile'] = w == 390
        context = browser.new_context(**options)
        old, new = context.new_page(), context.new_page()
        for page, base in [(old, args.baseline), (new, args.url)]:
            page.on('pageerror', lambda e: errors.append(str(e)))
            load(page, base + '/?waterTime=2')
            assert page.locator('main').get_attribute('data-reading-mode') == 'immersive'
        new.evaluate('window.__originalAboutArticles=[...document.querySelectorAll(".pillar-reading article")]')
        for mode in ['pixel', 'native']:
            for page in [old, new]:
                page.bring_to_front()
                page.locator(f'.tour-actions [data-mode={mode}]').click()
            for key, start, end in STATIONS:
                for direction, phases in [('forward', [('reveal', .18), ('read', .55), ('leave', .93)]), ('reverse', [('leave', .93), ('read', .55), ('reveal', .18)])]:
                    for phase, u in phases:
                        at = start + (end - start) * u
                        for page in [old, new]:
                            visit(page, at)
                        before, after = state(old), state(new)
                        assert before == after, (args.engine, w, mode, key, phase, before, after)
                        assert after['state']['station'] == key and after['state']['visible'] == 'true'
                        assert sum(a['aria'] == 'false' for a in after['articles']) == 1
                        camera_keys = ['cameraPosition', 'cameraTarget', 'viewHeight', 'sceneTime', 'displayH', 'readingStation', 'readingPhase', 'magicFrame']
                        od, nd = data(old), data(new)
                        assert all(od[k] == nd[k] for k in camera_keys)
                        item = {'viewport': [w, h], 'DPR': dpr, 'mode': mode, 'station': key, 'phase': phase, 'direction': direction, 'H': at,
                            'originalTextGeometryVisibilityAndCameraExact': True, 'titleOpacity': after['state']['titleOpacity'], 'bodyOpacity': after['state']['opacity']}
                        if direction == 'forward' and (phase == 'read' or (w == 1440 and mode == 'pixel')):
                            prefix = f'{args.engine}-{w}-{mode}-{key}-{phase}'
                            item['before'] = picture(old, prefix + '-before.png')
                            item['after'] = picture(new, prefix + '-after.png')
                        if direction == 'forward' and phase == 'read':
                            old.bring_to_front()
                            before_mask = background_measurement(old, OUT, f'{args.engine}-{w}-{mode}-{key}-alpha-before.png')
                            new.bring_to_front()
                            after_mask = background_measurement(new, OUT, f'{args.engine}-{w}-{mode}-{key}-alpha-after.png', check=True)
                            measures.append({'viewport': [w, h], 'DPR': dpr, 'mode': mode, 'station': key, 'before': before_mask, 'after': after_mask})
                        rows.append(item)
                print(args.engine, w, mode, key, 'forward/reverse + alpha/contrast PASS', flush=True)
            for at in [1.29, 3.71]:
                visit(new, at)
                e = about(new)
                assert e['state']['visible'] == 'false' and float(e['opacity']) == 0
        # Same original text nodes, native selection/copy, then a real small wheel.
        visit(new, 2.54)
        company = new.locator('.pillar-reading .about-company').first
        company.click(click_count=3)
        new.evaluate('window.__selectionBefore=getSelection().toString();window.__selectedCompany=document.querySelector(".about-company");window.__copyEvidence=null;document.addEventListener("copy",e=>window.__copyEvidence={trusted:e.isTrusted,selection:getSelection().toString()},{once:true})')
        assert new.evaluate('getSelection().toString().length>0')
        new.keyboard.press('Control+c')
        copy = new.evaluate('window.__copyEvidence')
        assert copy and copy['trusted'] and copy['selection']
        new.mouse.move(w - 28, min(310, h - 100))
        if not (args.engine == 'webkit' and w == 390):
            new.mouse.wheel(0, 5)
            new.wait_for_timeout(250)
            assert new.evaluate('getSelection().toString()===window.__selectionBefore')
        position = new.evaluate('scrollY')
        returned = []
        for _ in range(3):
            new.locator('#tour-layout-toggle').click()
            frames(new)
            assert new.locator('main').get_attribute('data-reading-mode') == 'stable'
            assert new.locator('.pillar-reading').evaluate('e=>getComputedStyle(e,"::before").display') == 'none'
            assert new.locator('.pillar-reading article').evaluate_all('es=>es.length===3&&es.every(e=>!e.inert&&e.getAttribute("aria-hidden")==="false")')
            new.locator('#tour-layout-toggle').click()
            frames(new)
            new.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"')
            assert abs(new.evaluate('scrollY') - position) <= 1
            returned.append(new.evaluate('scrollY'))
        assert new.evaluate('window.__originalAboutArticles.every((e,i)=>e===document.querySelectorAll(".pillar-reading article")[i])&&window.__selectedCompany===document.querySelector(".about-company")')
        new.evaluate('getSelection().removeAllRanges()')
        new.locator('#tour-stop-about').focus()
        new.keyboard.press('Enter')
        new.wait_for_function('Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-1.74)<.003')
        assert new.evaluate('document.activeElement.id') == 'tour-stop-about'
        touch = None
        if w == 390:
            new.locator('#tour-stop-films').tap()
            new.wait_for_function('Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-4.95)<.003')
            touch = {'nativeTapNavigates': True, 'physicalDevice': False}
            if args.engine == 'chromium':
                cdp = context.new_cdp_session(new)
                y0 = new.evaluate('scrollY')
                cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': 300, 'y': 340}]})
                for y in [300, 260, 220, 180]:
                    cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': 300, 'y': y}]})
                    new.wait_for_timeout(35)
                cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
                new.wait_for_timeout(400)
                assert new.evaluate('scrollY') > y0
                touch['nativeTouchDragScrolls'] = True
        extra.append({'viewport': [w, h], 'nativeSelectionAndTrustedCopy': copy, 'threeLayoutRoundTripsY': returned,
            'originalNodesAndCurrentAnchorPreserved': True, 'nativeKeyboardEnterAndFocus': True, 'touch': touch})
        context.close()
    # Measured capacity in small/short screens, 200% rem and reduced motion.
    sizes = [(320, 568, 1), (375, 667, 2), (430, 932, 2), (844, 390, 1), (390, 844, 3)]
    if args.engine != 'chromium':
        sizes = [(320, 568, 1), (844, 390, 1), (390, 844, 3)]
    for w, h, dpr in sizes:
        context = browser.new_context(viewport={'width': w, 'height': h}, device_scale_factor=dpr, has_touch=True)
        page = context.new_page()
        load(page, args.url + '/?waterTime=2')
        initial = page.locator('main').get_attribute('data-reading-mode')
        if initial == 'immersive':
            visit(page, 2.54)
            measured = background_measurement(page, OUT, f'{args.engine}-{w}-{h}-dpr{dpr}-boundary-alpha.png', check=True)
            page.locator('#tour-layout-toggle').click()
            frames(page)
        else:
            measured = None
        assert page.locator('.pillar-reading').evaluate('e=>getComputedStyle(e,"::before").display') == 'none'
        page.locator('#tour-stop-about').click()
        frames(page)
        picture(page, f'{args.engine}-{w}-{h}-boundary-stable.png')
        page.evaluate('document.documentElement.style.fontSize="200%"')
        page.wait_for_timeout(350)
        frames(page)
        audit = page.locator('.pillar-reading article').evaluate_all('es=>es.map(e=>({overflow:e.scrollWidth-e.clientWidth,hidden:e.hidden,inert:e.inert,bodyFont:parseFloat(getComputedStyle(e.querySelector(".pillar-reading-body")).fontSize)}))')
        assert all(not x['hidden'] and not x['inert'] and x['overflow'] <= 1 and x['bodyFont'] >= 32 for x in audit), audit
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        picture(page, f'{args.engine}-{w}-{h}-200percent.png')
        page.emulate_media(reduced_motion='reduce')
        page.wait_for_timeout(250)
        assert page.locator('main').get_attribute('data-reading-mode') == 'stable'
        assert page.locator('#tour-motion').inner_text() == '播放动效'
        extra.append({'viewport': [w, h], 'DPR': dpr, 'initialMode': initial, 'immersiveAlphaWhenAvailable': measured,
            'stableHasNoFloatingBackground': True, 'text200RemAudit': audit, 'reducedMotionStableAndPaused': True, 'physicalDevice': False})
        context.close()
    # A genuine failed WebGL context creation keeps the original full reading path.
    context = browser.new_context(viewport={'width': 390, 'height': 844})
    context.add_init_script('''(()=>{const f=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(t,...a){return String(t).startsWith('webgl')?null:f.call(this,t,...a)}})()''')
    page = context.new_page()
    page.goto(args.url + '/', wait_until='networkidle')
    page.wait_for_selector('#tour-host[data-render-state=error]')
    page.wait_for_function('document.querySelector("main").dataset.readingMode==="stable"')
    assert page.locator('.pillar-reading article').evaluate_all('es=>es.length===3&&es.every(e=>!e.inert&&e.getAttribute("aria-hidden")==="false")')
    assert page.locator('.pillar-reading').evaluate('e=>getComputedStyle(e,"::before").display') == 'none'
    assert all(t in page.locator('.tour-reading-flow').inner_text() for t in ['张辰翰', '枫叶互动', '游族网络', '网页设计样片'])
    extra.append({'realWebGLCreationFailure': True, 'allChaptersReadable': True, 'noFeatherBackgroundInFlow': True})
    context.close()
    assert not errors, errors
    save(OUT, f'background-{args.engine}.json', {'passed': True, 'engine': args.engine, 'version': browser.version,
        'stationPhaseDirectionCases': rows, 'stationPhaseDirectionCount': len(rows), 'backgroundMeasurements': measures,
        'extraCases': extra, 'minimumContrastOverWhite': min(m['after']['minimumContrastOverWhite']['ratio'] for m in measures),
        'maximumOuterAlpha': max(max(m['after']['outerOneCssPixelAlpha'].values()) for m in measures),
        'exceptions': errors, 'physicalDevice': False, 'rem200IsLayoutSimulation': True,
        'touchSelectionHandlesAndOSClipboardNeedPhysicalReview': True})
    print(args.engine, 'PASS', len(rows), 'station/direction phases;', len(measures), 'paired actual-size alpha/contrast measurements;', len(extra), 'input/reading cases', flush=True)
    browser.close()
