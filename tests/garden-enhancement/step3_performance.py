"""Matched production benchmarks. Run before/after sequentially, with no other
browser, screenshots or video. SwiftShader is a comparison, never hardware FPS.
"""
import argparse
import json
from playwright.sync_api import sync_playwright
from step3_common import *

parser = argparse.ArgumentParser()
parser.add_argument('--phase', choices=['before', 'after'], required=True)
args = parser.parse_args()
port = 4176 if args.phase == 'before' else 4177
identity = json.loads((OUT / ('baseline-version.json' if args.phase == 'before' else 'build-verification.json')).read_text())['candidateId']
raf_probe = '''(()=>{
  const original=requestAnimationFrame.bind(window);
  window.__frameSamples=[];window.__captureFrames=false;
  window.requestAnimationFrame=callback=>original(timestamp=>{
    const start=performance.now(),draws=window.__tourProbe.draws;
    callback(timestamp);
    if(window.__captureFrames&&window.__tourProbe.draws>draws)window.__frameSamples.push({timestamp,costMs:performance.now()-start,drawCalls:window.__tourProbe.draws-draws});
  });
})()'''

def stats(values):
    return {'count': len(values), 'p50Ms': sorted(values)[int((len(values)-1)*.5)],
        'p95Ms': sorted(values)[int((len(values)-1)*.95)], 'maxMs': max(values), 'meanMs': sum(values)/len(values)}

errors, animation = [], []
with sync_playwright() as p:
    browser = launch(p)
    context = browser.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
    context.add_init_script(probe)
    context.add_init_script(raf_probe)
    page = context.new_page()
    watch(page, errors)
    load(page, f'http://127.0.0.1:{port}/?waterTime=2')
    for mode in ['pixel', 'native', 'pixel']:
        page.locator(f'.tour-actions [data-mode={mode}]').click()
        for _, at in VIEWS:
            visit(page, at)
    wheel = []
    for label, at in [('T01', .9), ('T12', 4.05), ('T23', 8.35), ('T3W', 11.26), ('WIDE', 11.66)]:
        visit(page, at)
        page.mouse.move(1100, 260)
        page.wait_for_timeout(80)
        page.evaluate('window.__tourProbe.settles=[]')
        for delta in [15]*3+[-15]*3:
            y = page.evaluate('scrollY')
            page.mouse.wheel(0, delta)
            page.wait_for_function('y=>Math.abs(scrollY-y)>1', arg=y)
            page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"')
            page.wait_for_timeout(20)
        values = page.evaluate('window.__tourProbe.settles')
        assert len(values) == 6, (label, values)
        wheel.append({'center': label, 'H': at, 'deltas': [15]*3+[-15]*3, 'samplesMs': values})
    wheel_values = [v for r in wheel for v in r['samplesMs']]
    print(args.phase, 'travel30', stats(wheel_values), flush=True)
    context.close()
    for w, h, dpr, combinations in [(1440, 900, 1, [('pixel','O',0),('pixel','W',11.5),('native','O',0),('native','W',11.5)]),
                                   (390, 844, 2, [('pixel','W',11.5),('native','W',11.5)])]:
        context = browser.new_context(viewport={'width': w, 'height': h}, device_scale_factor=dpr)
        context.add_init_script(probe)
        context.add_init_script(raf_probe)
        page = context.new_page()
        watch(page, errors)
        load(page, f'http://127.0.0.1:{port}/?waterTime=2')
        for mode, key, at in combinations:
            pause(page)
            page.locator(f'.tour-actions [data-mode={mode}]').click()
            visit(page, at)
            playing(page)
            page.evaluate('window.__frameSamples=[];window.__captureFrames=true')
            page.wait_for_function('window.__frameSamples.length>=24', timeout=60000)
            page.evaluate('window.__frameSamples=[]')
            page.wait_for_function('window.__frameSamples.length>=90', timeout=60000)
            raw = page.evaluate('window.__captureFrames=false;window.__frameSamples.slice(0,90)')
            pause(page)
            intervals = [b['timestamp']-a['timestamp'] for a,b in zip(raw,raw[1:])]
            costs = [r['costMs'] for r in raw]
            result = {'viewport':[w,h], 'DPR':dpr, 'mode':mode, 'pose':key, 'warmupDrawingFrames':24,
                'samples':raw, 'rafCallbackCost':stats(costs), 'drawingRafIntervals':stats(intervals),
                'intervalsOver50ms':sum(v>50 for v in intervals), 'resourceStats':json.loads(data(page)['rendererStats'])}
            animation.append(result)
            print(args.phase,w,mode,key,'callback p95',result['rafCallbackCost']['p95Ms'],'interval p95',result['drawingRafIntervals']['p95Ms'], flush=True)
        context.close()
    assert not errors, errors
    save(OUT, f'performance-{args.phase}.json', {'passed':True, 'phase':args.phase, 'candidateId':identity, 'browser':browser.version,
        'travel30':{'stats':stats(wheel_values), 'routes':wheel}, 'visibleOrbAnimation':animation,
        'method':'same machine; separate browser runs; full-route caches warm; actual 30 native-wheel-to-camera-settled samples; O/W drawing RAF callback wall costs and drawing intervals include original app update/render/submission; 24 drawing frames warm then 90 measured per view; no concurrent browser, screenshot or recording',
        'p95Convention':'sorted[floor((n-1)*.95)]', 'hardwareFPSProof':False, 'gpuCompletionTiming':False,
        'directUpdateTiming':'not isolated by this production probe; RAF wall cost includes it', 'errors':errors})
    browser.close()
