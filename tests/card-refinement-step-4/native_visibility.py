"""Use genuine background tabs to check that a stopped frame keeps its preference."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
import traceback

from playwright.sync_api import sync_playwright
from reading_support import detail_button, hover_card, midpoint, points, tool_state


def check(page, context, origin, out):
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(origin, wait_until='domcontentloaded')
    page.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"&&document.querySelector("#tour-host")?.dataset.renderState==="ready"', timeout=90000)
    page.bring_to_front()
    assert page.evaluate('document.visibilityState') == 'visible'
    y = page.evaluate('3.34/12.3*(document.documentElement.scrollHeight-innerHeight)-scrollY')
    page.mouse.move(24, 300)
    page.mouse.wheel(0, y)
    page.wait_for_function('Number(document.querySelector(".ar-tools-browser").dataset.trackSpeed)>25')
    auto = page.locator('[data-action="auto"]')
    auto.click()
    auto.click()  # Establish an explicit choice instead of relying on the entrance default.
    page.wait_for_function('Number(document.querySelector(".ar-tools-browser").dataset.trackSpeed)>25')

    def window_id(tab):
        return context.new_cdp_session(tab).send('Browser.getWindowForTarget')['windowId']

    def hide(other):
        other.bring_to_front()
        page.wait_for_function('document.hidden', polling=100, timeout=10000)
        state = tool_state(page)
        assert state['trackEnabled'] == 'true' and state['trackFramePending'] == 'false'
        assert state['trackWheelActive'] == 'false' and float(state['trackSpeed']) == 0
        assert state['hoverFramePending'] == 'false' and not state.get('detailPressed')
        return state

    def show():
        page.bring_to_front()
        page.wait_for_function('document.visibilityState==="visible"', polling=100, timeout=10000)

    other = context.new_page()
    other.goto('about:blank')
    source_id, other_id = window_id(page), window_id(other)
    assert source_id == other_id
    show()
    page.mouse.move(*points(page)['left'])
    page.mouse.wheel(0, 360)
    page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.trackWheelActive==="true"')
    hidden = hide(other)
    show()
    page.wait_for_function('''() => {
      const t=document.querySelector('.ar-tools-browser').dataset;
      return Number(t.trackSpeed)>25 && t.trackWheelActive==='false';
    }''')
    resumed = tool_state(page)
    assert resumed['trackEnabled'] == 'true' and 25 < float(resumed['trackSpeed']) <= 28.5

    card = hover_card(page)
    page.mouse.click(*midpoint(detail_button(page, card)), delay=80)
    page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.detailMode==="pinned"')
    fixed_hidden = hide(other)
    show()
    page.wait_for_timeout(620)
    fixed_visible = tool_state(page)
    assert fixed_visible['readingId'] == fixed_hidden['readingId'] == card
    assert fixed_visible['detailMode'] == 'pinned' and fixed_visible['trackEnabled'] == 'true'
    assert fixed_visible['trackFramePending'] == 'false' and float(fixed_visible['trackSpeed']) == 0
    assert not errors, errors
    page.screenshot(path=str(out / 'pinned-after-native-return.png'))
    other.close()
    return {'sameNativeWindow': True, 'hidden': hidden, 'resumed': resumed,
            'fixedHidden': fixed_hidden, 'fixedReturned': fixed_visible}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--origin', required=True)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--env-file', required=True, type=Path)
    parser.add_argument('--build-record', required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, args.out / 'native_visibility.py.txt')
    os.environ.update(json.loads(args.env_file.read_text())['browserEnvironment'])
    build = json.loads(args.build_record.read_text())
    result = {'complete': False, 'nativeBrowser': True, 'clockModified': False,
              'documentPropertiesOverridden': False, 'candidateId': build['candidateId'],
              'runtimeInputDigest': build['runtimeInputDigest']}
    with tempfile.TemporaryDirectory(prefix='card-reading-native-', dir='/tmp') as scratch:
        command = [shutil.which('chromium') or 'chromium', '--no-sandbox', '--remote-debugging-port=0',
                   '--user-data-dir='+scratch, '--no-first-run', '--no-default-browser-check',
                   '--disable-background-networking', '--disable-dev-shm-usage', '--use-gl=angle',
                   '--use-angle=gl', '--ignore-gpu-blocklist', '--window-size=1680,1040', 'about:blank']
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        try:
            port_file = Path(scratch) / 'DevToolsActivePort'
            deadline = time.monotonic() + 12
            while not port_file.exists():
                assert process.poll() is None and time.monotonic() < deadline, 'Chromium startup'
                time.sleep(.1)
            port = port_file.read_text().splitlines()[0]
            with sync_playwright() as playwright:
                browser = playwright.chromium.connect_over_cdp('http://127.0.0.1:'+port, no_defaults=True)
                try:
                    context = browser.contexts[0]
                    page = context.pages[0]
                    page.set_viewport_size({'width': 1652, 'height': 949})
                    result.update(check(page, context, args.origin, args.out), complete=True, version=browser.version)
                finally:
                    browser.close()
        except Exception as error:
            result.update(complete=False, error=str(error), traceback=traceback.format_exc())
        finally:
            if process.poll() is None:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            try:
                process.wait(timeout=6)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                process.wait(timeout=5)
            result['ownedNativeBrowserClosed'] = True
    (args.out / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print({key: result[key] for key in ('complete', 'error', 'sameNativeWindow', 'ownedNativeBrowserClosed') if key in result}, flush=True)
    raise SystemExit(0 if result['complete'] else 1)
