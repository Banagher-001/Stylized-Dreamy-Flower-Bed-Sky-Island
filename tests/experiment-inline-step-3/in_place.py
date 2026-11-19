"""Production-window tests with trusted inputs and controlled entry responses."""
from pathlib import Path
import sys

from playwright.sync_api import Error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'about-refresh-final'))
from support import Run


STAGE = '.experiment-window-stage'
ARCHIVE = '.experiment-project-archive'
LAWSON = '**/experiments/lawson/index.html'
r = Run()


def position(page):
    host = r.state(page)
    return [host['url'], host['y'], host['host']['displayH'], host['host']['cameraTarget']]


def geometry(page):
    return page.locator(STAGE).bounding_box()


def select(page, identifier):
    r.activate(page.locator(f'[data-project-select="{identifier}"]'))
    assert page.locator(f'[data-project-select="{identifier}"]').get_attribute('aria-selected') == 'true'


def assert_window(page, frame):
    state = r.state(page)
    assert len(page.context.pages) == 1 and not state['dialogs'] and 'tour-project-open' not in state['locks']
    stage = geometry(page)
    bounds = page.locator(f'{STAGE} iframe').bounding_box()
    assert len(page.frames) == 2 and bounds == stage
    width, height = frame.evaluate('() => [innerWidth, innerHeight]')
    assert abs(width - stage['width']) <= 1 and abs(height - stage['height']) <= 1, (bounds, width, height)
    assert frame.evaluate('() => window === window.top') is False
    assert page.locator(f'{STAGE} .experiment-scene-mount').get_attribute('aria-busy') == 'false'
    return [width, height]


def archive(page, identifier, align):
    details = page.locator(ARCHIVE)
    assert not details.evaluate('e=>e.open')
    toggle = details.locator('summary')
    before = geometry(page)
    r.activate(toggle)
    content = details.locator(f'.experiment-archive-content[data-project-id="{identifier}"]')
    content.wait_for()
    assert content.locator('.experiment-archive-features section').count() == 3
    assert page.locator(f'{STAGE} iframe').count() == 1 and not page.locator('dialog[open]').count()
    assert content.evaluate('e=>getComputedStyle(e).position') == align
    if align == 'absolute':
        assert before == geometry(page)
        content.focus()
        page.keyboard.press('Escape')
        assert toggle.evaluate('e=>e===document.activeElement')
    else:
        assert content.bounding_box()['y'] > geometry(page)['y'] + geometry(page)['height']
        r.activate(toggle)
    assert not details.evaluate('e=>e.open')


def desktop(page):
    assert r.state(page)['mode'] == 'immersive'
    assert len(page.frames) == 1
    r.go(page, 'C1')
    assert page.locator('iframe').count() == 0
    r.go(page, 'C2')
    before = position(page)
    window = geometry(page)
    lawson = r.wait_scene(page, 'lawson')
    lawson_size = assert_window(page, lawson)
    assert lawson_size[0] >= 1100 and lawson_size[1] >= 558
    assert lawson.locator('#loader').count() == 0
    assert lawson.url == r.origin + 'experiments/lawson/index.html'
    point = lawson.evaluate('''() => {
      for (const x of [0.35,0.25,0.45]) for (const y of [.55,.60,.53]) {
        const px=Math.round(innerWidth*x), py=Math.round(innerHeight*y);
        if (document.elementFromPoint(px,py)?.id==='viewport') return [px,py];
      } return null;
    }''')
    assert point, 'The original canvas must receive pointer input at an open point.'
    sample = '__LAWSON__.api.project([3,1,2])'
    old_view = lawson.evaluate(sample)
    viewport_point = [window['x'] + point[0], window['y'] + point[1]]
    page.mouse.move(*viewport_point)
    page.mouse.down()
    page.mouse.move(viewport_point[0] + 95, viewport_point[1] + 40, steps=12)
    page.mouse.up()
    lawson.wait_for_function(f'v=>JSON.stringify({sample})!==JSON.stringify(v)', arg=old_view)
    new_view = lawson.evaluate(sample)
    assert position(page) == before and geometry(page) == window
    assert_window(page, lawson)
    r.checkpoint(page, 'lawson')
    archive(page, 'lawson', 'absolute')
    assert not lawson.is_detached()

    select(page, 'bottle-ocean')
    bottle = r.wait_scene(page, 'bottle-ocean')
    bottle_size = assert_window(page, bottle)
    assert lawson.is_detached() and bottle_size == lawson_size
    assert bottle.url == r.origin + 'experiments/bottle-ocean/index.html'
    assert bottle.locator('#loader').evaluate('e=>getComputedStyle(e).display') == 'none'
    assert bottle.evaluate('__bottleOcean.state.waveHeight') == 35
    bottle.locator('#waveHeight').press('End')
    assert bottle.evaluate('__bottleOcean.state.waveHeight') == 100
    assert position(page) == before and geometry(page) == window
    r.checkpoint(page, 'bottle')
    archive(page, 'bottle-ocean', 'absolute')
    assert bottle.evaluate('__bottleOcean.state.waveHeight') == 100

    r.go(page, 'C3')
    page.wait_for_function('document.querySelectorAll("iframe").length===0')
    assert bottle.is_detached()
    r.go(page, 'water')
    assert not page.locator('dialog[open],iframe').count()
    return {'window': window, 'nativeDimensions': [lawson_size, bottle_size], 'lawsonProjection': [old_view, new_view],
            'bottleWave': [35, 100], 'unchangedParent': before, 'releasedAtC3': True}


def tap_native(page, control):
    height = page.evaluate('innerHeight')
    for _ in range(4):
        bounds = control.bounding_box()
        header = page.locator('.tour-header').bounding_box()
        center = bounds['y'] + bounds['height'] / 2
        safe_top = header['y'] + header['height'] + 12
        if safe_top <= center <= height - 12:
            control.tap()
            return
        delta = (safe_top + height - 12) / 2 - center
        start = safe_top + 8 if delta > 0 else height - 20
        stop = min(height - 8, max(safe_top, start + delta))
        # A short viewport can show only part of the large window. Swipe the
        # parent margin as a visitor would to reveal the original control.
        client = page.context.new_cdp_session(page)
        previous = page.evaluate('scrollY')
        try:
            client.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': 7, 'y': start}]})
            for step in range(1, 9):
                client.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': 7, 'y': start + step * (stop - start) / 8}]})
                page.wait_for_timeout(24)
            client.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
        finally:
            client.detach()
        page.wait_for_function('y=>Math.abs(scrollY-y)>3', arg=previous)
        page.wait_for_timeout(240)
    raise AssertionError('The original control should be reachable by scrolling the parent margin.')


def touch(page):
    assert r.state(page)['mode'] == 'stable'
    lawson = r.open_scene(page, 'lawson')
    lawson_size = assert_window(page, lawson)
    assert lawson_size[0] >= page.evaluate('innerWidth') - 65 and lawson_size[1] >= 380
    panel = lawson.locator('#panel')
    initial = panel.evaluate('e=>e.classList.contains("collapsed")')
    tap_native(page, lawson.locator('#panel-collapse'))
    assert panel.evaluate('e=>e.classList.contains("collapsed")') is not initial

    select(page, 'bottle-ocean')
    page.locator(STAGE).scroll_into_view_if_needed()
    bottle = r.wait_scene(page, 'bottle-ocean')
    bottle_size = assert_window(page, bottle)
    assert lawson.is_detached() and bottle_size == lawson_size
    controls = bottle.locator('#control-panel')
    initial = controls.evaluate('e=>e.classList.contains("collapsed")')
    tap_native(page, bottle.locator('#panel-toggle'))
    assert controls.evaluate('e=>e.classList.contains("collapsed")') is not initial
    r.checkpoint(page, 'bottle-touch')
    archive(page, 'bottle-ocean', 'static')
    r.go(page, 'water')
    page.wait_for_function('document.querySelectorAll("iframe").length===0')
    assert bottle.is_detached()
    return {'nativeDimensions': [lawson_size, bottle_size], 'touchControls': ['#panel-collapse', '#panel-toggle'], 'samePageArchive': True}


def failure_and_retry(page):
    attempts = []

    def first_response(route):
        attempts.append(route.request.url)
        if len(attempts) == 1:
            route.fulfill(status=200, content_type='text/html', body='<!doctype html><title>Test response</title><p>Scene document unavailable</p>')
        else:
            route.continue_()

    page.route(LAWSON, first_response)
    r.go(page, 'C2')
    before, window = position(page), geometry(page)
    stage = page.locator(STAGE)
    page.wait_for_selector(f'{STAGE}[data-scene-state=error]')
    assert '重新载入' in stage.locator('[role=status]').inner_text()
    assert not stage.locator('iframe').is_visible()
    assert stage.locator('img').evaluate('e=>e.complete&&e.naturalWidth>0')
    old = stage.locator('iframe').element_handle().content_frame()
    r.checkpoint(page, 'error')
    stage.locator('.experiment-scene-retry').click()
    recovered = r.wait_scene(page, 'lawson')
    assert old.is_detached() and len(attempts) == 2
    assert_window(page, recovered)
    assert position(page) == before and geometry(page) == window
    assert not stage.locator('.experiment-scene-retry').is_visible()
    return {'entryAttempts': attempts, 'window': window, 'unchangedParent': before, 'recovered': True}


def slow_switch(page):
    held = []
    page.route(LAWSON, lambda route: held.append(route))
    r.go(page, 'C2')
    page.wait_for_selector(f'{STAGE}[data-scene-state=loading]')
    stage = page.locator(STAGE)
    iframe = stage.locator('iframe')
    iframe.wait_for(state='attached')
    previous = iframe.element_handle().content_frame()
    assert stage.locator('.experiment-scene-mount').get_attribute('aria-busy') == 'true'
    assert not iframe.is_visible()
    page.wait_for_selector(f'{STAGE}[data-scene-state=slow]', timeout=32000)
    assert stage.locator('.experiment-scene-retry').is_enabled() and len(held) == 1
    assert '载入较慢' in stage.locator('[role=status]').inner_text()
    before = position(page)
    select(page, 'bottle-ocean')
    current = r.wait_scene(page, 'bottle-ocean')
    assert previous.is_detached()
    try:
        held[0].fulfill(status=200, content_type='text/html', body='<!doctype html><title>Late response</title>')
        old_response = 'released after detach'
    except Error:
        old_response = 'request was disposed with the frame'
    page.wait_for_timeout(750)
    assert_window(page, current)
    assert position(page) == before
    return {'oldResponse': old_response, 'selected': current.url, 'unchangedParent': before, 'fallbackThresholdSeconds': 12}


def guide_waits(page):
    held = []
    page.route(LAWSON, lambda route: held.append(route))
    page.locator('#tour-motion').click()
    r.go(page, 'C2')
    stage = page.locator(STAGE)
    stage.locator('iframe').wait_for(state='attached')
    guide = page.locator('#tour-guide')
    guide.click()
    page.wait_for_function('document.querySelector("#tour-host").dataset.guidePhase==="arriving"')
    initial = r.state(page)['host']
    assert initial['guideDeadline'] == '' and stage.get_attribute('data-scene-state') == 'loading' and len(held) == 1
    held[0].continue_()
    r.wait_scene(page, 'lawson')
    page.wait_for_function('document.querySelector("#tour-host").dataset.guidePhase==="reading"')
    ready = r.state(page)['host']
    assert ready['guideStation'] == 'C2' and float(ready['guideReadSeconds']) >= 12
    guide.click()
    return {'whileLoading': initial['guidePhase'], 'whenReady': ready['guidePhase'], 'readSeconds': ready['guideReadSeconds']}


try:
    r.case('desktop-inline-playback', desktop)
    r.case('phone-inline-playback', touch, size=(390, 844), touch=True)
    r.case('landscape-inline-playback', touch, size=(844, 390), touch=True)
    r.case('inline-error-retry', failure_and_retry)
    r.case('inline-slow-switch', slow_switch)
    r.case('guide-waits-for-scene', guide_waits)
finally:
    good = r.finish()
raise SystemExit(0 if good else 1)
