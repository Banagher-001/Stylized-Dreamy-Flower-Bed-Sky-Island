"""Verify the portfolio shell, media and real offscreen rendering suspension.

Optional dependencies: tests/final/requirements.txt. No physical-device/FPS claim.
"""
from pathlib import Path
from io import BytesIO
import argparse
import json
import os
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/evidence/portfolio'
OUT.mkdir(parents=True, exist_ok=True)
parser = argparse.ArgumentParser()
parser.add_argument('--engine', choices=['chromium', 'firefox', 'webkit'], default='chromium')
parser.add_argument('--url', default='http://127.0.0.1:4173')
args = parser.parse_args()
checks, issues, requests = [], [], []


def passed(name, evidence):
    checks.append({'check': name, 'passed': True, 'evidence': evidence})
    print(args.engine + ': ' + name, flush=True)


def capture(page):
    page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))')
    return Image.open(BytesIO(page.locator('canvas').screenshot())).convert('RGB')


def report(page):
    return page.evaluate('''()=>({overflow:document.documentElement.scrollWidth>innerWidth,
      canvasCount:document.querySelectorAll('canvas').length,
      time:document.querySelector('#scene-host').dataset.sceneTime,
      visibility:document.querySelector('#scene-host').dataset.visibility,
      draws:window.__portfolioProbe.draws})''')


PROBE = '''(()=>{window.__portfolioProbe={draws:0};
for(const name of ['drawArrays','drawElements','drawArraysInstanced','drawElementsInstanced']){
const original=WebGL2RenderingContext.prototype[name];
WebGL2RenderingContext.prototype[name]=function(...args){window.__portfolioProbe.draws++;return original.apply(this,args);};}
})()'''

with sync_playwright() as p:
    options = {'headless': args.engine == 'chromium'}
    if args.engine == 'chromium':
        options.update(executable_path=os.environ.get('CHROMIUM_EXECUTABLE', '/usr/bin/chromium'), args=['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
    if args.engine == 'firefox':
        options['firefox_user_prefs'] = {'webgl.force-enabled': True}
    if args.engine == 'webkit' and os.environ.get('COURTYARD_WEBKIT_EXECUTABLE'):
        options['executable_path'] = os.environ['COURTYARD_WEBKIT_EXECUTABLE']
    browser = getattr(p, args.engine).launch(**options)
    context = browser.new_context(viewport={'width': 1440, 'height': 1000})
    context.add_init_script(PROBE)
    page = context.new_page()
    page.on('pageerror', lambda error: issues.append({'type': 'exception', 'text': str(error)}))
    page.on('console', lambda msg: issues.append({'type': msg.type, 'text': msg.text}) if msg.type in ['warning', 'error'] else None)
    page.on('response', lambda response: issues.append({'type': 'http', 'text': f'{response.status} {response.url}'}) if response.status >= 400 else None)
    page.on('request', lambda request: requests.append(request.url))
    page.goto(args.url + '/?waterTime=2', wait_until='networkidle')
    page.wait_for_selector('#scene-host[data-render-state="ready"]')
    assert page.locator('h1').count() == 1
    assert '张辰翰' in page.title()
    for text in ['枫叶互动', '游族网络', 'AI 动画', 'Vibe Coding']:
        assert text in page.locator('#about').inner_text()
    assert page.locator('.work-card').count() == 3
    assert page.locator('.work-kind', has_text='概念样片').count() == 2
    assert not any('.mp4' in url for url in requests), 'Video should not load before opening/playing'
    initial = capture(page)
    assert len(initial.getcolors(1000000)) > 32
    passed('visible live cover, confirmed biography, labeled concepts and deferred video', report(page))

    page.get_by_role('button', name='正常画面', exact=True).click()
    assert page.locator('canvas').get_attribute('data-render-mode') == 'native'
    assert ImageChops.difference(initial, capture(page)).getbbox() is not None, 'Mode label changed but the presented picture did not'
    page.get_by_role('button', name='像素预览', exact=True).click()
    assert ImageChops.difference(initial, capture(page)).getbbox() is None
    passed('mode switching preserves the deterministic cover', {'scenePixelsExact': True})

    for kind, count in [('visual', 2), ('interactive', 1), ('all', 3)]:
        page.locator(f'[data-filter="{kind}"]').click()
        assert page.locator('.work-card:not([hidden])').count() == count
        assert page.locator(f'[data-filter="{kind}"]').get_attribute('aria-pressed') == 'true'
        assert page.locator('#work-status').inner_text() == f'显示 {count} 个项目。'
    passed('working project categories and accessible count', {'visual': 2, 'interactive': 1, 'all': 3})

    for project in ['signal-garden', 'courtyard', 'liquid-form']:
        button = page.locator(f'[data-project="{project}"]')
        button.focus()
        page.keyboard.press('Enter')
        page.wait_for_selector('#project-dialog[open]')
        assert page.locator('#project-title').inner_text()
        assert page.locator('.dialog-close').evaluate('e=>e===document.activeElement')
        page.keyboard.press('Tab')
        assert page.evaluate('document.querySelector("dialog").contains(document.activeElement)')
        page.keyboard.press('Escape')
        page.wait_for_function('!document.querySelector("dialog").open')
        assert button.evaluate('e=>e===document.activeElement')
    passed('all project dossiers open by keyboard, trap focus and return it on Escape', {'projects': 3})

    page.locator('[data-project="courtyard"]').click()
    video = page.locator('video')
    can_play = video.evaluate('v=>v.canPlayType("video/mp4; codecs=avc1.42E01E")')
    if args.engine == 'chromium':
        video.evaluate('v=>v.play()')
        page.wait_for_function('document.querySelector("video").currentTime>0.1')
        duration = video.evaluate('v=>v.duration')
        assert 11.9 <= duration <= 12.1
        video.evaluate('v=>window.__videoUnderTest=v')
    else:
        duration = None
    page.locator('.dialog-close').click()
    if args.engine == 'chromium':
        # The native dialog close event is queued; verify its completed behavior.
        page.wait_for_function('window.__videoUnderTest.paused')
        assert page.evaluate('window.__videoUnderTest.paused')
    passed('film, frames and closed-dialog media behavior', {'durationSeconds': duration, 'h264Support': can_play, 'playbackTested': args.engine == 'chromium'})

    page.goto(args.url + '/', wait_until='networkidle')
    page.wait_for_selector('#scene-host[data-motion-state="running"]')
    page.locator('.site-nav a[href="#about"]').click()
    page.wait_for_selector('#scene-host[data-visibility="offscreen"]', state='attached')
    page.wait_for_timeout(150)
    before = report(page)
    page.wait_for_timeout(500)
    after = report(page)
    assert before['draws'] == after['draws'] and before['time'] == after['time'], (before, after)
    page.locator('.site-nav a[href="#home"]').click()
    page.wait_for_selector('#scene-host[data-visibility="visible"]', state='attached')
    resumed = report(page)
    assert float(resumed['time']) - float(after['time']) < .4
    page.get_by_role('button', name='暂停动效', exact=True).click()
    page.locator('.site-nav a[href="#works"]').click()
    page.wait_for_selector('#scene-host[data-visibility="offscreen"]', state='attached')
    page.locator('.site-nav a[href="#home"]').click()
    page.wait_for_selector('#scene-host[data-motion-state="paused"]', state='attached')
    passed('scrolling actually stops GPU draws and time, resumes without fast-forward, preserves manual pause', {'before': before, 'after': after, 'resumed': resumed})

    layouts = [(280,600,1),(320,568,1),(390,844,2),(760,1000,1.25),(768,1024,1.5),(1024,768,1),(1920,1080,2),(844,390,3)] if args.engine == 'chromium' else [(390,844,2),(1440,1000,1)]
    for width, height, dpr in layouts:
        c = browser.new_context(viewport={'width': width, 'height': height}, device_scale_factor=dpr, reduced_motion='reduce')
        q = c.new_page()
        q.goto(args.url + '/?waterTime=2', wait_until='networkidle')
        q.wait_for_selector('#scene-host[data-render-state="ready"]')
        assert not q.evaluate('document.documentElement.scrollWidth>innerWidth'), (width, height)
        targets = q.locator('[data-mode],#motion-control,[data-filter],.site-nav a').evaluate_all('es=>es.map(e=>{const r=e.getBoundingClientRect();return {width:r.width,height:r.height};})')
        assert all(t['width'] >= 44 and t['height'] >= 44 for t in targets), (width, targets)
        q.locator('.site-nav a[href="#works"]').click()
        assert q.locator('#works').evaluate('e=>e.getBoundingClientRect().top') >= 75
        if width == 390:
            q.locator('[data-project="signal-garden"]').click()
            assert q.locator('dialog').evaluate('e=>e.scrollWidth<=e.clientWidth')
            q.locator('.dialog-close').click()
            for card in q.locator('.work-card').all():
                card.scroll_into_view_if_needed()
                card.locator('img').evaluate('i=>i.decode()')
            q.locator('.site-nav a[href="#home"]').click()
            q.wait_for_selector('#scene-host[data-visibility="visible"]', state='attached')
            q.screenshot(path=str(OUT / f'{args.engine}-mobile.png'), full_page=True)
        c.close()
    passed('responsive layout, real anchors, 44px controls and mobile modal', {'viewportDPRCombinations': layouts, 'phoneSimulated': True})

    page.goto(args.url + '/?waterTime=2', wait_until='networkidle')
    page.wait_for_selector('#scene-host[data-render-state="ready"]')
    reference = capture(page)
    supported = page.evaluate('!!document.querySelector("canvas").getContext("webgl2").getExtension("WEBGL_lose_context")')
    if supported:
        page.evaluate('window.__loss=document.querySelector("canvas").getContext("webgl2").getExtension("WEBGL_lose_context");window.__loss.loseContext()')
        page.wait_for_selector('#scene-notice:not([hidden])')
        page.evaluate('window.__loss.restoreContext()')
        page.wait_for_selector('#scene-host[data-render-state="ready"]')
        assert ImageChops.difference(reference, capture(page)).getbbox() is None
    passed('paused cover context restoration retains the actual presented picture', {'contextLossAvailable': supported})

    for card in page.locator('.work-card').all():
        card.scroll_into_view_if_needed()
        card.locator('img').evaluate('i=>i.decode()')
        page.wait_for_function('e=>e.dataset.reveal==="visible"', arg=card.element_handle())
    page.wait_for_timeout(850)
    page.locator('.site-nav a[href="#home"]').click()
    page.wait_for_selector('#scene-host[data-visibility="visible"]', state='attached')
    page.wait_for_timeout(600)
    page.screenshot(path=str(OUT / f'{args.engine}-desktop.png'), full_page=True)
    page.screenshot(path=str(OUT / f'{args.engine}-cover.png'))
    page.locator('#about').screenshot(path=str(OUT / f'{args.engine}-about.png'))
    page.locator('#works').screenshot(path=str(OUT / f'{args.engine}-works.png'))
    page.locator('[data-project="courtyard"]').click()
    page.screenshot(path=str(OUT / f'{args.engine}-project.png'))

    known = [i for i in issues if args.engine == 'firefox' and ('Depth texture comparison requests' in i['text'] or 'WebGL context was lost.' in i['text'])]
    unexpected = [i for i in issues if i not in known]
    assert not unexpected, unexpected
    passed('diagnostics retain known Firefox notices and reject all unexpected issues', {'knownFirefoxDiagnostics': len(known), 'unexpectedIssues': unexpected})
    (OUT / f'verification-{args.engine}.json').write_text(json.dumps({'engine': args.engine, 'version': browser.version, 'environment': 'Linux cloud software rendering; not physical device acceptance', 'checks': checks, 'issues': issues}, ensure_ascii=False, indent=2) + '\n')
    browser.close()
