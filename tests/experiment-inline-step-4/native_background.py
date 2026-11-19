"""Switch real Chromium tabs and measure the loader's visible waiting time."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import traceback
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'about-refresh-final'))
from support import now, save


STAGE = '.experiment-window-stage'


def window_id(context, page):
    session = context.new_cdp_session(page)
    try:
        return session.send('Browser.getWindowForTarget')['windowId']
    finally:
        session.detach()


def show(page):
    page.bring_to_front()
    page.wait_for_function('document.visibilityState==="visible"', polling=100, timeout=10000)


def hide(page, other, frame):
    other.bring_to_front()
    page.wait_for_function('document.hidden', polling=100, timeout=10000)
    frame.wait_for_function('document.hidden', polling=100, timeout=10000)


def scene_state(page):
    return page.locator(STAGE).get_attribute('data-scene-state')


def frame_for(page, project, ready=False):
    locator = page.locator(f'{STAGE} iframe[src$="/experiments/{project}/index.html"]')
    locator.wait_for(state='visible' if ready else 'attached', timeout=90000)
    assert page.locator(f'{STAGE} iframe').count() == 1
    return locator.element_handle().content_frame()


def go_to_window(page):
    if page.locator('main').get_attribute('data-reading-mode') == 'stable':
        page.locator('[data-experiment-station=C2]').evaluate('''article => {
          const header=document.querySelector('.tour-header');
          scrollBy({top:article.getBoundingClientRect().top-header.getBoundingClientRect().bottom-16,behavior:'instant'});
        }''')
        return
    delta = page.evaluate('10.05/12.3*(document.documentElement.scrollHeight-innerHeight)-scrollY')
    page.mouse.move(24, 300)
    page.mouse.wheel(0, delta)
    page.wait_for_function('''() => {
      const host=document.querySelector('#tour-host');
      return Math.abs(Number(host.dataset.displayH)-10.05)<.006 && host.dataset.cameraState==='settled';
    }''', polling=100, timeout=30000)


def loading_clock(page, other):
    held = []
    model = '**/experiments/lawson/assets/models/lawson_scene.glb'
    page.route(model, lambda route: held.append(route))
    page.locator(STAGE).evaluate('''stage => {
      window.__sceneWaitingTimeline=[];
      const record=kind=>window.__sceneWaitingTimeline.push({kind, time:performance.now(),
        scene:stage.dataset.sceneState, visibility:document.visibilityState});
      document.addEventListener('visibilitychange',()=>record('visibility'));
      new MutationObserver(()=>record('scene')).observe(stage,{attributes:true,attributeFilter:['data-scene-state']});
    }''')
    with page.expect_request(model, timeout=45000):
        go_to_window(page)
    frame = frame_for(page, 'lawson')
    assert scene_state(page) == 'loading' and len(held) == 1
    page.wait_for_timeout(1500)
    hide(page, other, frame)
    page.wait_for_timeout(13100)
    hidden_stage = scene_state(page)
    assert hidden_stage == 'loading' and frame_for(page, 'lawson') == frame, hidden_stage

    show(page)
    page.wait_for_timeout(750)
    assert scene_state(page) == 'loading' and frame_for(page, 'lawson') == frame, scene_state(page)
    page.locator(f'{STAGE}[data-scene-state=slow]').wait_for(timeout=18000)
    assert page.locator(f'{STAGE} .experiment-scene-retry').is_enabled()
    timeline = page.evaluate('window.__sceneWaitingTimeline')
    started = next(e['time'] for e in timeline if e['kind'] == 'scene' and e['scene'] == 'loading')
    hidden = next(e['time'] for e in timeline if e['kind'] == 'visibility' and e['visibility'] == 'hidden')
    visible = next(e['time'] for e in timeline if e['kind'] == 'visibility' and e['visibility'] == 'visible' and e['time'] > hidden)
    slow = next(e['time'] for e in timeline if e['kind'] == 'scene' and e['scene'] == 'slow')
    active_ms, hidden_ms = (hidden - started) + (slow - visible), visible - hidden
    assert hidden_ms >= 12000 and 11800 <= active_ms <= 13400, timeline
    held[0].continue_()
    assert frame_for(page, 'lawson', ready=True) == frame
    assert scene_state(page) == 'ready'
    return {'sameFrameAfterReturn': True, 'backgroundState': hidden_stage, 'visibleWaitingMs': round(active_ms),
            'backgroundMs': round(hidden_ms), 'timeline': timeline}


def preserve_ready_scene(page, other, out):
    entries = []
    page.on('request', lambda request: entries.append(request.url) if request.url.endswith('/experiments/bottle-ocean/index.html') else None)
    page.locator('[data-project-select=bottle-ocean]').click()
    frame = frame_for(page, 'bottle-ocean', ready=True)
    frame.locator('#waveHeight').press('End')
    frame.locator('[data-action=pause]').click()
    snapshot = '() => [__bottleOcean.state.waveHeight,__bottleOcean.state.paused,__bottleOcean.getDiagnostics().simTime]'
    before = frame.evaluate(snapshot)
    assert before[:2] == [100, True]
    hide(page, other, frame)
    page.wait_for_timeout(1100)
    assert scene_state(page) == 'ready' and frame.evaluate(snapshot) == before
    show(page)
    assert frame_for(page, 'bottle-ocean', ready=True) == frame
    assert frame.evaluate(snapshot) == before and len(entries) == 1
    page.screenshot(path=str(out / 'ready-return.png'))
    frame.locator('[data-action=pause]').click()
    frame.wait_for_function('t=>!__bottleOcean.state.paused&&__bottleOcean.getDiagnostics().simTime>t', arg=before[2], polling=100)
    return {'sameFrameAfterReturn': True, 'waveHeight': before[0], 'originalPauseKept': True,
            'entryRequests': entries, 'canResumeUsingOriginalControl': True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--origin', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--env-file', type=Path, required=True)
    parser.add_argument('--build-record', type=Path, required=True)
    args = parser.parse_args()
    os.environ.update(json.loads(args.env_file.read_text())['browserEnvironment'])
    args.out.mkdir(parents=True, exist_ok=False)
    build = json.loads(args.build_record.read_text())
    report = {'candidateId': build['candidateId'], 'runtimeInputDigest': build['runtimeInputDigest'],
              'startedAtShanghai': now(), 'origin': args.origin, 'nativeBrowser': True,
              'clockModified': False, 'visibilityOverridden': False, 'complete': False, 'checks': []}
    with tempfile.TemporaryDirectory(prefix='experiment-native-', dir='/tmp') as profile, (args.out / 'chromium.log').open('w') as log:
        command = [shutil.which('chromium') or 'chromium', '--no-sandbox', '--remote-debugging-port=0',
                   '--user-data-dir=' + profile, '--no-first-run', '--no-default-browser-check',
                   '--disable-background-networking', '--disable-component-update', '--disable-dev-shm-usage',
                   '--disable-default-apps', '--disable-sync',
                   '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost, EXCLUDE 127.0.0.1',
                   '--use-gl=angle', '--use-angle=gl', '--ignore-gpu-blocklist', '--window-size=1680,1040', 'about:blank']
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            info = Path(profile) / 'DevToolsActivePort'
            deadline = time.monotonic() + 15
            while not info.exists():
                assert process.poll() is None and time.monotonic() < deadline, 'Chromium startup failed'
                time.sleep(.1)
            port = info.read_text().splitlines()[0]
            with sync_playwright() as pw:
                browser = pw.chromium.connect_over_cdp(f'http://127.0.0.1:{port}', no_defaults=True)
                report['version'] = browser.version
                context = browser.contexts[0]
                allowed = urlsplit(args.origin).netloc
                external, errors, http = [], [], []

                def local_only(route):
                    url = route.request.url
                    if url.startswith(('http:', 'https:')) and urlsplit(url).netloc != allowed:
                        external.append(url)
                        route.abort('blockedbyclient')
                    else:
                        route.continue_()

                context.route('**/*', local_only)
                page = context.pages[0]
                page.set_viewport_size({'width': 1440, 'height': 900})
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.on('console', lambda message: errors.append(message.text) if message.type == 'error' else None)
                page.on('response', lambda response: http.append(response.url) if response.status >= 400 else None)
                other = context.new_page()
                assert window_id(context, page) == window_id(context, other)
                report['sameNativeWindow'] = True
                show(page)
                page.goto(args.origin, wait_until='domcontentloaded')
                show(page)
                try:
                    page.wait_for_function('''() => document.querySelector('main')?.dataset.layoutReady==='true'
                      && document.querySelector('#tour-host')?.dataset.renderState==='ready' ''', polling=100, timeout=35000)
                    report['readingMode'] = page.locator('main').get_attribute('data-reading-mode')
                    for name, check in [('foreground-only-slow-clock', lambda: loading_clock(page, other)),
                                        ('ready-frame-background-return', lambda: preserve_ready_scene(page, other, args.out))]:
                        result = check()
                        assert not (errors or http or external), (errors, http, external)
                        report['checks'].append({'id': name, 'status': '通过', 'measurements': result})
                        print(json.dumps({'id': name, 'status': '通过'}, ensure_ascii=False), flush=True)
                except Exception:
                    report['failureState'] = page.evaluate('''() => ({visibility:document.visibilityState,
                      viewport:[innerWidth,innerHeight], main:{...document.querySelector('main')?.dataset},
                      stage:document.querySelector('.experiment-window-stage')?.dataset.sceneState,
                      render:document.querySelector('#tour-host')?.dataset.renderState})''')
                    report.update(consoleErrors=errors, httpFailures=http, externalAttempts=external)
                    raise
                finally:
                    other.close()
                    browser.close()
                report['complete'] = True
        except Exception as error:
            report.update(error=str(error), traceback=traceback.format_exc())
            print(report['traceback'], flush=True)
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=6)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)
    report.update(browserClosed=True, finishedAtShanghai=now())
    save(args.out / 'browser.json', report)
    return report['complete']


if __name__ == '__main__':
    raise SystemExit(0 if main() else 1)
