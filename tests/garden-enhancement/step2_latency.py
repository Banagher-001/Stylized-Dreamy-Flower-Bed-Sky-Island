"""Standalone matched scroll measurements; run BEFORE then AFTER, alone.

Thirty original travel-route samples and eighteen visible-about reveal samples
are reported separately. No screenshots, video or second browser during sampling.
"""
import argparse
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
from step2_common import *

parser = argparse.ArgumentParser()
parser.add_argument('--phase', choices=['before', 'after'], required=True)
parser.add_argument('--out', type=Path, default=ROOT / 'docs/evidence/garden-enhancement-step-2')
args = parser.parse_args()
OUT = args.out.resolve()
version = json.loads((OUT / 'baseline-version.json').read_text())
build = json.loads((OUT / 'build-verification.json').read_text())
base = 'http://127.0.0.1:' + ('4176' if args.phase == 'before' else '4177')
old_gate = "if(new URLSearchParams(location.search).get('tour')==='prototype'&&!attach())"
assert old_gate in PROBE
probe = PROBE.replace(old_gate, 'if(!attach())')

with sync_playwright() as p:
    browser = launch(p)
    context = browser.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    context.add_init_script(probe)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    load(page, base + '/?waterTime=2')
    warm = []
    for mode in ['pixel', 'native', 'pixel']:
        page.locator(f'.tour-actions [data-mode={mode}]').click()
        for _, h in VIEWS:
            visit(page, h)
        warm.append(json.loads(data(page)['rendererStats']))
    groups = {}
    for name, centers in [('travel30', [('T01', .9), ('T12', 4.05), ('T23', 8.35), ('T3W', 11.26), ('WIDE', 11.66)]),
                          ('aboutVisible18', [('A1-reveal', 1.44), ('A2-reveal', 2.24), ('A3-reveal', 3.04)])]:
        samples, routes = [], []
        for label, at in centers:
            visit(page, at)
            page.mouse.move(1100, 260)
            page.wait_for_timeout(80)
            page.evaluate('window.__tourProbe.settles=[]')
            states = []
            for delta in [15] * 3 + [-15] * 3:
                y = page.evaluate('scrollY')
                page.mouse.wheel(0, delta)
                page.wait_for_function('y=>Math.abs(scrollY-y)>1', arg=y)
                page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"')
                page.wait_for_timeout(20)
                states.append({'h': data(page)['displayH'], 'background': page.locator('.pillar-reading').evaluate('e=>({visible:e.dataset.visible,veil:e.style.getPropertyValue("--veil-opacity")})')})
            values = page.evaluate('window.__tourProbe.settles')
            assert len(values) == 6, (name, label, values)
            if name == 'aboutVisible18':
                assert all(s['background']['visible'] == 'true' for s in states)
                assert len(set(s['background']['veil'] for s in states)) > 1
            samples.extend(values)
            routes.append({'center': label, 'H': at, 'deltas': [15] * 3 + [-15] * 3, 'samplesMs': values, 'states': states})
        groups[name] = {'sampleCount': len(samples), 'samplesMs': samples,
            'p95Ms': sorted(samples)[int((len(samples) - 1) * .95)], 'maxMs': max(samples), 'routes': routes}
    assert groups['travel30']['sampleCount'] == 30 and groups['aboutVisible18']['sampleCount'] == 18
    assert not errors, errors
    save(OUT, f'latency-{args.phase}.json', {'passed': True, 'phase': args.phase,
        'sourceIdentity': version['gitCommit'] if args.phase == 'before' else build['candidateId'],
        'browser': browser.version, 'viewport': [1440, 900], 'DPR': 1, 'renderMode': 'pixel384', 'fixedEnvironmentTime': 2,
        'method': 'native wheel to camera-settled; pixel/native/pixel full-route prewarm; no concurrent browser/screenshot/recording; original travel30 and visible-changing-background18 kept separate',
        'p95Convention': 'sorted[floor((n-1)*.95)]', 'groups': groups, 'warmCaches': warm,
        'hardwareFPSProof': False, 'exceptions': errors})
    print(args.phase, {k: {'n': v['sampleCount'], 'p95': v['p95Ms']} for k, v in groups.items()}, flush=True)
    context.close()
    browser.close()
