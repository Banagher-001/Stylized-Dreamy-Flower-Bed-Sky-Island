"""Step3 helpers; prior immutable evidence and test files are never written."""
from pathlib import Path
from io import BytesIO
import json
from PIL import Image, ImageChops
from step2_common import launch, load, visit, frames, data, save, PROBE, STOPS, VIEWS

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/evidence/garden-enhancement-step-3'
old_gate = "if(new URLSearchParams(location.search).get('tour')==='prototype'&&!attach())"
assert old_gate in PROBE
probe = PROBE.replace(old_gate, 'if(!attach())')

def watch(page, errors):
    page.on('pageerror', lambda e: errors.append({'type': 'exception', 'text': str(e)}))
    page.on('console', lambda m: errors.append({'type': m.type, 'text': m.text}) if m.type == 'error' else None)
    page.on('response', lambda r: errors.append({'type': 'http', 'text': str(r.status) + ' ' + r.url}) if r.status >= 400 else None)

def decode(page):
    page.wait_for_function('Array.from(document.images).every(e=>!e.currentSrc||e.complete)')
    page.evaluate('Promise.all(Array.from(document.images).filter(e=>e.currentSrc).map(e=>e.decode()))')
    frames(page)

def pure_canvas(page):
    style = page.add_style_tag(content='#app *:not(canvas){visibility:hidden!important} #app canvas{visibility:visible!important}')
    frames(page)
    result = page.locator('canvas').screenshot()
    style.evaluate('e=>e.remove()')
    frames(page)
    return result

def equal(a, b):
    return ImageChops.difference(Image.open(BytesIO(a)).convert('RGB'), Image.open(BytesIO(b)).convert('RGB')).getbbox() is None

def still(page):
    page.wait_for_timeout(250)
    # Image decoding, modal layout and resize can request a finite final draw.
    # Require a continuous quiet window after they settle, never a moving clock.
    time = data(page)['sceneTime']
    for pending in range(10):
        draws = page.evaluate('window.__tourProbe.draws')
        page.wait_for_timeout(450)
        assert data(page)['sceneTime'] == time, ('paused clock moved', time, data(page))
        if page.evaluate('window.__tourProbe.draws') == draws:
            return {'time': time, 'zeroDrawWindowMs': 450, 'draws': draws, 'finitePendingDrawWindows': pending}
    raise AssertionError('Paused scene did not settle into a 450ms zero-draw window within 4.5s.')

def playing(page):
    if data(page)['motionState'] != 'running':
        page.locator('#tour-motion').click()
    t = float(data(page)['sceneTime'])
    page.wait_for_function('t=>Number(document.querySelector("#tour-host").dataset.sceneTime)>t+.1', arg=t)
    return t, float(data(page)['sceneTime'])

def pause(page):
    if data(page)['motionState'] == 'running':
        page.locator('#tour-motion').click()
    frames(page)
