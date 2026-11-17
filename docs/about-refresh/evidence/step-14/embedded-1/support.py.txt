"""Real-browser final journeys. No application clock or scene mutations."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urlsplit
import argparse, hashlib, json, os, shutil, traceback
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
STOPS = {'opening': 0, 'A1': 1.74, 'A2': 2.54, 'A3': 3.34,
         'B1': 4.95, 'B2': 5.95, 'B3': 6.84, 'B4': 7.64,
         'C1': 9.14, 'C2': 10.05, 'C3': 10.83, 'water': 11.5, 'ending': 12.3}

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def now():
    return datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()

STATE = r'''()=>{const main=document.querySelector('main'),host=document.querySelector('#tour-host'),root=document.querySelector('.ar-tools-browser'),rail=root?.querySelector('.ar-tool-rail');return{
 url:location.href,viewport:[innerWidth,innerHeight],y:scrollY,mode:main?.dataset.readingMode,anchor:main?.dataset.flowAnchor,
 host:host?{...host.dataset}:null,tools:root?{...root.dataset}:null,railX:rail?.scrollLeft,
 cards:rail?[...rail.querySelectorAll('.ar-tool-card')].map(e=>({id:e.dataset.toolId,instance:e.dataset.cardInstance,expanded:e.dataset.expanded,detailHidden:e.querySelector('.ar-card-detail').hidden})):[],
 overflow:document.documentElement.scrollWidth-innerWidth,canvas:document.querySelectorAll('canvas').length,frames:document.querySelectorAll('iframe').length,
 dialogs:[...document.querySelectorAll('dialog[open]')].map(e=>({class:e.className,d:{...e.dataset}})),locks:document.documentElement.className,
 focus:{tag:document.activeElement?.tagName,action:document.activeElement?.dataset.action,id:document.activeElement?.id,hidden:!!document.activeElement?.closest('[hidden],[inert]')}}}'''

class Run:
    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--origin', required=True)
        parser.add_argument('--out', type=Path, required=True)
        parser.add_argument('--engine', default='chromium', choices=['chromium', 'firefox'])
        parser.add_argument('--env-file', type=Path)
        parser.add_argument('--build-record', type=Path)
        parser.add_argument('--only', nargs='*')
        parser.add_argument('--seconds', type=int, default=600)
        self.args = parser.parse_args()
        self.out = self.args.out.resolve()
        self.out.mkdir(parents=True, exist_ok=False)
        self.origin = self.args.origin.rstrip('/') + '/'
        if self.args.env_file:
            os.environ.update(json.loads(self.args.env_file.read_text())['browserEnvironment'])
        cache = Path('/workspace/.cache/ms-playwright')
        if cache.is_dir():
            os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH', str(cache))
        self.pw = sync_playwright().start()
        opts = {'headless': True}
        if self.args.engine == 'chromium':
            executable = os.environ.get('CHROMIUM_EXECUTABLE') or shutil.which('chromium')
            if executable:
                opts['executable_path'] = executable
            opts['args'] = ['--no-sandbox', '--use-gl=angle', '--use-angle=gl', '--ignore-gpu-blocklist']
        else:
            opts['firefox_user_prefs'] = {'webgl.force-enabled': True}
        self.browser = getattr(self.pw, self.args.engine).launch(**opts)
        self.report = {'startedAtShanghai': now(), 'engine': self.args.engine,
                       'version': self.browser.version, 'origin': self.origin, 'checks': [],
                       'complete': False, 'physicalDevice': False, 'clockModified': False}
        if self.args.build_record:
            build = json.loads(self.args.build_record.read_text())
            self.report['candidateId'] = build['candidateId']
            self.report['runtimeInputDigest'] = build['runtimeInputDigest']
            save(self.out / 'build.json', build)
        for p in Path(__file__).parent.glob('*.py'):
            shutil.copy2(p, self.out / (p.name + '.txt'))
        self.page = None
        self.case_id = ''

    def case(self, name, fn, size=(1440, 900), touch=False, reduced=False, video=False):
        if self.args.only and name not in self.args.only:
            return
        self.case_id = name
        self.touch = touch
        opts = {'viewport': {'width': size[0], 'height': size[1]}, 'has_touch': touch,
                'accept_downloads': True, 'reduced_motion': 'reduce' if reduced else 'no-preference'}
        if self.args.engine == 'chromium':
            opts['is_mobile'] = touch
        if video:
            opts.update(record_video_dir=str(self.out / 'video'), record_video_size=opts['viewport'])
        ctx = self.browser.new_context(**opts)
        errors, failed, http, external, warnings = [], [], [], [], []
        allowed = urlsplit(self.origin).netloc
        def route(req):
            if req.request.url.startswith(('http:', 'https:')) and urlsplit(req.request.url).netloc != allowed:
                external.append(req.request.url)
                req.abort('blockedbyclient')
            else:
                req.continue_()
        ctx.route('**/*', route)
        page = ctx.new_page()
        self.page = page
        page.set_default_timeout(25000)
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else warnings.append(m.text) if m.type == 'warning' else None)
        page.on('requestfailed', lambda req: failed.append({'url': req.url, 'type': req.resource_type, 'error': req.failure}))
        page.on('response', lambda response: http.append({'url': response.url, 'status': response.status}) if response.status >= 400 else None)
        entry = {'id': name, 'status': '失败', 'viewport': list(size), 'touchEmulation': touch}
        try:
            page.goto(self.origin, wait_until='domcontentloaded')
            page.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"&&document.querySelector("#tour-host")?.dataset.renderState==="ready"', timeout=90000)
            data = fn(page)
            unexpected = [v for v in failed if not (v['error'] == 'net::ERR_ABORTED' and v['type'] in ['image', 'media', 'document'])]
            assert not errors and not unexpected and not http and not external, (errors, unexpected, http, external)
            state = self.state(page)
            assert state['overflow'] <= 1 and not state['focus']['hidden'], state
            save(self.out / f'{name}-data.json', data)
            page.screenshot(path=str(self.out / f'{name}.png'))
            entry.update(status='通过', data=f'{name}-data.json')
        except Exception as e:
            entry.update(error=str(e), traceback=traceback.format_exc())
            try:
                save(self.out / f'{name}-failure.json', self.state(page))
                page.screenshot(path=str(self.out / f'{name}-failure.png'))
            except Exception:
                pass
        finally:
            entry.update(errors=errors, requestFailures=failed, httpFailures=http, externalAttempts=external, warnings=warnings)
            ctx.close()
            if video:
                entry['video'] = str(Path(page.video.path()).relative_to(self.out))
            self.report['checks'].append(entry)
            save(self.out / 'browser.json', self.report)
            print(json.dumps({'id': name, 'status': entry['status'], 'error': entry.get('error', '')[:220]}, ensure_ascii=False), flush=True)
        return entry['status'] == '通过'

    def state(self, page):
        return page.evaluate(STATE)

    def checkpoint(self, page, label):
        state = self.state(page)
        save(self.out / f'{self.case_id}-{label}.json', state)
        page.screenshot(path=str(self.out / f'{self.case_id}-{label}.png'))
        return state

    def stable(self, page):
        if self.state(page)['mode'] != 'stable':
            self.activate(page.locator('#tour-layout-toggle'))
            page.wait_for_function('document.querySelector("main").dataset.readingMode==="stable"')

    def activate(self, locator):
        if self.touch:
            locator.tap()
        else:
            locator.click()

    def go(self, page, station):
        if self.state(page)['mode'] == 'stable':
            anchor = 'opening' if station == 'opening' else station
            page.locator(f'.tour-reading-flow [data-flow-anchor="{anchor}"]').scroll_into_view_if_needed()
            page.wait_for_timeout(200)
        else:
            target = STOPS[station] if isinstance(station, str) else station
            delta = page.evaluate('h=>h/12.3*(document.documentElement.scrollHeight-innerHeight)-scrollY', target)
            page.mouse.move(24, 300)
            page.mouse.wheel(0, delta)
            page.wait_for_function('h=>Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-h)<.006&&document.querySelector("#tour-host").dataset.cameraState==="settled"', arg=target, timeout=30000)
            page.wait_for_timeout(120)

    def open_project(self, page, identifier, tab='live'):
        self.go(page, 'C2')
        self.activate(page.locator(f'[data-project-select="{identifier}"]'))
        page.wait_for_function('document.querySelector(".experiment-reading").dataset.coverState==="ready"')
        self.activate(page.locator(f'[data-project-tab="{tab}"]'))
        page.wait_for_function('document.querySelector(".tour-project-dialog").open')
        if identifier == 'courtyard' or tab == 'archive':
            return None
        page.wait_for_selector('iframe', state='attached')
        frame = page.locator('iframe').element_handle().content_frame()
        if identifier == 'lawson':
            frame.wait_for_function('window.__LAWSON__?.ready===true', timeout=120000)
            frame.locator('#loader').wait_for(state='hidden', timeout=60000)
        else:
            frame.wait_for_function('window.__bottleOcean?.ready===true&&getComputedStyle(document.querySelector("#loader")).display==="none"', timeout=120000)
        page.wait_for_function('document.querySelector(".tour-project-dialog").dataset.embeddedState==="ready"', timeout=30000)
        return frame

    def close_project(self, page):
        self.activate(page.locator('.tour-project-close'))
        page.wait_for_function('!document.querySelector(".tour-project-dialog").open&&document.querySelectorAll("iframe").length===0')
        page.wait_for_timeout(250)
        assert 'tour-project-open' not in self.state(page)['locks']

    def finish(self):
        self.browser.close()
        self.pw.stop()
        self.report.update(browserClosed=True, finishedAtShanghai=now(), complete=bool(self.report['checks']) and all(v['status'] == '通过' for v in self.report['checks']))
        save(self.out / 'browser.json', self.report)
        return self.report['complete']
