"""Read-only baseline sampling for the next seven-step garden enhancement.

No application files or historical reports are changed. Serve the extracted
baseline with its scripts/serve-dist.mjs on :4176. Run latency alone before
capture/recording. Playwright and the existing scroll-garden helpers are needed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from urllib.request import urlopen
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests/scroll-garden'))
from step11_common import PROBE, STOPS, VIEWS, launch, ready, go, frames, data

# The historical probe only discovers the ?tour=prototype entrance. Keep the
# actual scroll/draw measurement identical while also discovering the new root.
_old_discovery = "if(new URLSearchParams(location.search).get('tour')==='prototype'&&!attach())"
assert _old_discovery in PROBE
PROBE = PROBE.replace(_old_discovery, 'if(!attach())')

parser = argparse.ArgumentParser()
parser.add_argument('--phase', choices=['latency', 'capture'], required=True)
parser.add_argument('--url', default='http://127.0.0.1:4176')
parser.add_argument('--out', type=Path, default=ROOT / 'docs/evidence/garden-enhancement-step-1')
args = parser.parse_args()
OUT = args.out.resolve()
OUT.mkdir(parents=True, exist_ok=True)
BASE = args.url.rstrip('/')
VERSION = json.loads((OUT / 'baseline-version.json').read_text())
SEAL = json.loads((OUT / 'runtime-build-seal.json').read_text())

def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def identity():
    return {'gitCommit': VERSION['gitCommit'], 'applicationCandidateId': VERSION['applicationCandidateId'],
            'source': 'independently extracted baseline-source-site.tar.gz, not workspace dist',
            'sourceArchiveSha256': VERSION['sourceArchiveSha256'], 'baseURL': BASE}

def layout_ready(page):
    page.wait_for_function('document.querySelector("main").dataset.layoutReady === "true"')
    frames(page)

def position(page):
    return page.evaluate('({y:scrollY,h:document.querySelector("#tour-host").dataset.displayH,mode:document.querySelector("main").dataset.readingMode,focus:document.activeElement?.id})')

def shot(page, name):
    frames(page)
    page.mouse.move(10, page.viewport_size['height'] / 2)
    page.screenshot(path=str(OUT / name))
    return {'file': name, 'position': position(page), 'scene': data(page)}

def mask_edge(page):
    return page.locator('.pillar-reading').evaluate('''async e=>{
      const s=getComputedStyle(e,'::before'),r=e.getBoundingClientRect(),image=new Image();
      image.src=s.maskImage.slice(4,-1).replace(/^"|"$/g,'');await image.decode();
      const c=document.createElement('canvas');c.width=420;c.height=240;
      const ctx=c.getContext('2d');ctx.drawImage(image,0,0,420,240);
      const d=ctx.getImageData(0,0,420,240).data,edges={left:0,right:0,top:0,bottom:0};
      for(let x=0;x<420;x++){edges.top=Math.max(edges.top,d[x*4+3]);edges.bottom=Math.max(edges.bottom,d[(239*420+x)*4+3]);}
      for(let y=0;y<240;y++){edges.left=Math.max(edges.left,d[y*420*4+3]);edges.right=Math.max(edges.right,d[(y*420+419)*4+3]);}
      return{rect:r.toJSON(),background:s.backgroundColor,boxShadow:s.boxShadow,filter:s.filter,
        maskSVG:s.maskImage,maskRasterSize:[420,240],outerEdgeAlpha:edges,alphaRange:[0,255],
        maximumResidualAlpha:Math.max(...Object.values(edges)),panel:{...e.dataset}};
    }''')

with sync_playwright() as p:
    browser = launch(p)
    if args.phase == 'latency':
        context = browser.new_context(viewport={'width': 1440, 'height': 900}, device_scale_factor=1)
        context.add_init_script(PROBE)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        ready(page, BASE + '/?waterTime=2')
        layout_ready(page)
        caches = []
        for mode in ['pixel', 'native', 'pixel']:
            page.locator(f'.tour-actions [data-mode={mode}]').click()
            for _, h in VIEWS:
                go(page, h)
            frames(page)
            caches.append({'warmMode': mode, **json.loads(data(page)['rendererStats'])})
        gl = page.locator('canvas').evaluate('''e=>{const g=e.getContext('webgl2'),x=g.getExtension('WEBGL_debug_renderer_info');return{vendor:g.getParameter(g.VENDOR),renderer:g.getParameter(g.RENDERER),unmaskedRenderer:x?g.getParameter(x.UNMASKED_RENDERER_WEBGL):null}}''')
        samples, groups = [], []
        for key, at in [('T01', .9), ('T12', 4.05), ('T23', 8.35), ('T3W', 11.26), ('WIDE', 11.66)]:
            go(page, at)
            frames(page)
            page.mouse.move(1100, 260)
            page.wait_for_timeout(80)
            page.evaluate('window.__tourProbe.settles=[]')
            for delta in [15] * 3 + [-15] * 3:
                prior = page.evaluate('scrollY')
                page.mouse.wheel(0, delta)
                page.wait_for_function('y=>Math.abs(scrollY-y)>1', arg=prior)
                page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"')
                page.wait_for_timeout(20)
            values = page.evaluate('window.__tourProbe.settles')
            assert len(values) == 6, (key, values)
            samples.extend(values)
            groups.append({'route': key, 'startH': at, 'deltasCssPixels': [15] * 3 + [-15] * 3, 'samplesMs': values})
        assert len(samples) == 30 and not errors, errors
        save('latency-baseline.json', {'passed': True, **identity(), 'browser': browser.version,
            'viewport': [1440, 900], 'DPR': 1, 'mode': 'pixel', 'pixelDesignResolution': 384,
            'fixedEnvironmentTime': 2, 'fullWarmCaches': caches, 'graphics': gl,
            'method': 'native wheel to actual camera-settled signal; five route centers, six stops each; pixel/native/pixel full-route prewarm; no concurrent browser, screenshots or recording during measurement',
            'probeAdaptation': 'Only host discovery changed from prototype-only to current default root; no application code or sampling method changed.',
            'samplesMs': samples, 'routes': groups, 'p95Ms': sorted(samples)[int((len(samples) - 1) * .95)],
            'maxMs': max(samples), 'p95Convention': 'sorted[floor((n-1)*.95)], kept identical to previous baselines',
            'physicalDevice': False, 'hardwareFPSProof': False, 'exceptions': errors})
        print('PASS isolated baseline: 30 native wheel stops, p95', sorted(samples)[27], 'ms;', 'warm resources', [(s['geometries'], s['textures'], s['programs']) for s in caches], flush=True)
        context.close()
    else:
        files = []
        for name, expected in SEAL['productionSha256'].items():
            with urlopen(BASE + '/' + name) as response:
                body, mime = response.read(), response.headers.get_content_type()
                assert response.status == 200
            assert hashlib.sha256(body).hexdigest() == expected, name
            files.append({'file': name, 'sha256': expected, 'mime': mime})
        rows, overlays, contents, masks, errors = [], [], [], [], []
        for label, w, h, dpr in [('desktop', 1440, 900, 1), ('phone', 390, 844, 2)]:
            context = browser.new_context(viewport={'width': w, 'height': h}, device_scale_factor=dpr,
                has_touch=label == 'phone', is_mobile=label == 'phone')
            context.add_init_script(PROBE)
            page = context.new_page()
            page.on('pageerror', lambda e: errors.append(str(e)))
            ready(page, BASE + '/?waterTime=2')
            layout_ready(page)
            assert page.locator('main').get_attribute('data-reading-mode') == 'immersive'
            if not contents:
                contents = page.locator('.tour-reading-flow article').evaluate_all('''es=>es.map(e=>{
                  const title=e.querySelector('h2')?.textContent?.trim()??'',body=e.querySelector('[class$="-body"]')?.textContent?.replace(/\\s+/g,' ').trim()??'';
                  return{id:e.dataset.flowAnchor,title,body,bodyNonWhitespaceCodePoints:Array.from(body.replace(/\\s/g,'')).length,
                    fullText:e.textContent.replace(/\\s+/g,' ').trim(),buttons:[...e.querySelectorAll('button')].map(b=>b.textContent.trim())};})''')
                assert [x['id'] for x in contents] == [s[0] for s in STOPS]
            for mode in ['pixel', 'native']:
                page.locator(f'.tour-actions [data-mode={mode}]').click()
                for key, at in [('O', 0), ('A1', 1.74), ('A2', 2.54), ('A3', 3.34), ('B1', 4.95), ('C2', 10.05), ('W', 11.5), ('S99', 12.3)]:
                    go(page, at)
                    rows.append({'viewport': [w, h], 'DPR': dpr, 'mode': mode, 'pose': key,
                        **shot(page, f'{label}-{mode}-{key}.png')})
                go(page, 1.74)
                masks.append({'viewport': [w, h], 'DPR': dpr, 'mode': mode, **mask_edge(page)})
                if label == 'desktop' and mode == 'pixel':
                    box = page.locator('.pillar-reading').bounding_box()
                    page.screenshot(path=str(OUT / 'about-edge-detail.png'), clip={'x': box['x'] - 16, 'y': box['y'] - 16, 'width': box['width'] + 32, 'height': box['height'] + 32})
                    for name, at in [('reveal', 1.49), ('leave', 2.04)]:
                        go(page, at)
                        rows.append({'viewport': [w, h], 'DPR': dpr, 'mode': mode, 'pose': 'A1-' + name,
                            **shot(page, f'about-A1-{name}.png')})
                go(page, 4.95)
                before = position(page)
                page.locator('[data-film-station=B1] .film-image-button').click()
                page.wait_for_selector('.film-dialog[data-state=ready]')
                rows.append({'viewport': [w, h], 'mode': mode, 'viewer': 'complete-image', **shot(page, f'{label}-{mode}-image-viewer.png')})
                page.locator('.film-dialog-close').click()
                page.wait_for_function('document.querySelector("#tour-host").dataset.overlayState==="closed"')
                frames(page)
                after = position(page)
                assert abs(before['y'] - after['y']) <= 1, (before, after)
                overlays.append({'viewport': [w, h], 'mode': mode, 'viewer': 'image', 'before': before, 'after': after})
                go(page, 10.05)
                before = position(page)
                page.locator('[data-project-tab=live]').click()
                assert page.locator('canvas').count() == 1
                rows.append({'viewport': [w, h], 'mode': mode, 'viewer': 'live', **shot(page, f'{label}-{mode}-live-viewer.png')})
                page.locator('[data-project-view=archive]').click()
                page.wait_for_function('document.querySelector(".tour-project-archive figure img").complete && document.querySelector(".tour-project-archive figure img").naturalWidth>0')
                rows.append({'viewport': [w, h], 'mode': mode, 'viewer': 'archive', **shot(page, f'{label}-{mode}-archive-viewer.png')})
                page.locator('.tour-project-close').click()
                page.wait_for_function('document.querySelector("#tour-host").dataset.overlayState==="closed"')
                frames(page)
                after = position(page)
                assert abs(before['y'] - after['y']) <= 1 and page.locator('canvas').count() == 1, (before, after)
                overlays.append({'viewport': [w, h], 'mode': mode, 'viewer': 'live/archive', 'before': before, 'after': after})
            go(page, 2.54)
            page.locator('#tour-layout-toggle').click()
            frames(page)
            assert page.locator('main').get_attribute('data-reading-mode') == 'stable'
            rows.append({'viewport': [w, h], 'mode': 'native', 'reading': 'stable', **shot(page, f'{label}-stable-A2.png')})
            page.evaluate('document.documentElement.style.fontSize="200%"')
            page.wait_for_timeout(400)
            frames(page)
            rows.append({'viewport': [w, h], 'mode': 'native', 'reading': 'stable', 'textScale': '200% root rem simulation, not native browser or OS text size', **shot(page, f'{label}-200percent-text.png')})
            context.close()
        assert not errors, errors
        save('content-inventory.json', {'passed': True, **identity(), 'stations': contents,
            'readingTimerImplementationPresent': False, 'countsAreUnicodeCodePointsNotReadingSpeed': True})
        save('about-edge-measurement.json', {'passed': True, **identity(), 'measurements': masks,
            'knownDefectConfirmed': any(m['maximumResidualAlpha'] > 0 for m in masks),
            'method': 'Current real SVG mask rasterized in browser to intrinsic420x240; maximum alpha on outermost pixel rows/columns; screenshots of actual page, no image manipulation.',
            'newFeatheringImplemented': False})
        save('visual-baseline.json', {'passed': True, **identity(), 'browser': browser.version,
            'screenshots': rows, 'screenshotCount': len(rows) + 1, 'detailScreenshot': 'about-edge-detail.png',
            'overlayReturns': overlays, 'exactProductionFileChecks': files,
            'phoneIsBrowserEmulationNotPhysicalDevice': True, 'allFramesPausedAtTime2': True,
            'exceptions': errors, 'newFeaturesImplemented': False})
        print('PASS baseline:', len(rows) + 1, 'screenshots,', len(contents), 'original stations,', len(overlays), 'viewer returns;', len(files), 'exact served production files', flush=True)
    browser.close()
