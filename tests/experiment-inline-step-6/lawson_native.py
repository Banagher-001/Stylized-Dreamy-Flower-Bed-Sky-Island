"""Use a headed private display for browser fullscreen and pointer lock."""
import os
from pathlib import Path
import subprocess

from lawson_replay import Replay, historical, previous
from pair_support import BrowserRun, DESKTOP, IFRAME, LAWSON, position, save


XDOTOOL = Path('/workspace/.cache/browser-deps/root/usr/bin/xdotool')


def escape(display):
    assert display.startswith(':') and display == os.environ['DISPLAY']
    assert XDOTOOL.is_file()

    def xdo(*args):
        return subprocess.check_output([str(XDOTOOL), *args], text=True, timeout=5).strip()

    windows = xdo('search', '--onlyvisible', '--class', 'chromium').splitlines()
    for window in windows:
        bounds = dict(line.split('=', 1) for line in xdo('getwindowgeometry', '--shell', window).splitlines() if '=' in line)
        if int(bounds.get('WIDTH', 0)) >= 500 and int(bounds.get('HEIGHT', 0)) >= 300:
            title = xdo('getwindowname', window)
            xdo('windowfocus', '--sync', window)
            xdo('key', 'Escape')
            return {'method': 'XTest Escape', 'privateDisplay': display, 'window': title}
    raise AssertionError('Chromium main window unavailable on the private display')


def fullscreen(page, scene, embedded, display, exit_methods=('button', 'Escape')):
    state = []
    original = position(page)
    assert scene.evaluate('document.fullscreenEnabled')
    for exit_method in exit_methods:
        scene.locator('#btn-fullscreen').click()
        scene.wait_for_function('document.fullscreenElement===document.documentElement', timeout=15000, polling=100)
        page.wait_for_function('arg=>document.fullscreenElement === (arg ? document.querySelector("iframe") : document.documentElement)',
                               arg=embedded, timeout=15000, polling=100)
        scene.wait_for_function('''() => {
          const {renderSize,drawCalls}=__LAWSON__.api.getStats();
          return renderSize[0]===innerWidth && renderSize[1]===innerHeight && drawCalls>0;
        }''', timeout=60000, polling=100)
        entered = scene.evaluate('() => ({viewport:[innerWidth,innerHeight],render:__LAWSON__.api.getStats().renderSize})')
        assert min(entered['viewport'] + entered['render']) > 0
        if exit_method == 'button':
            scene.locator('#btn-fullscreen').click()
            event = None
        else:
            page.wait_for_timeout(300)
            event = escape(display)
        page.wait_for_function('!document.fullscreenElement', timeout=15000, polling=100)
        scene.wait_for_function('!document.fullscreenElement', timeout=15000, polling=100)
        assert position(page) == original, (original, position(page))
        if embedded:
            assert page.locator(IFRAME).element_handle().content_frame() == scene
        state.append({'exitMethod': exit_method, 'entered': entered, 'nativeEscape': event, 'returnedToOriginal': True})
    return state


def all_native(walk=True):
    results = {}
    child_size = None
    for side in ('embedded', 'reference'):
        embedded = side == 'embedded'
        context, page, events = runner.context(DESKTOP if embedded else child_size, probe=previous.PROBE)
        before = None
        try:
            scene, conditions = runner.open(page, LAWSON, embedded)
            before = position(page)
            if embedded:
                child_size = tuple(conditions['viewport'])
            assert tuple(conditions['viewport']) == child_size
            replay = Replay(runner, page, scene, side, 'keyboard')
            replay.low()
            full = fullscreen(page, scene, embedded, runner.environment['DISPLAY'])
            if walk:
                historical(replay, 'keyboard')
            assert scene.evaluate('!document.pointerLockElement && !document.fullscreenElement')
            scene.locator('[data-preset=day]').click()
            scene.wait_for_function('Math.abs(__LAWSON__.api.getStats().timeOfDay-9)<.02', polling=100)
            assert position(page) == before, (before, position(page))
            assert not (events['external'] or events['errors'] or events['unexpectedHttp']), events
            assert all(error == 'net::ERR_ABORTED' for error, _ in events['failures']), events
            details = replay.report['checks']
            results[side] = {'conditions': conditions, 'fullscreen': full, 'keyboard': details, 'network': events,
                             'hostBefore': before, 'hostAfter': position(page), 'originalControlsAfterExit': True}
            save(runner.out / f'{side}.json', results[side])
        except Exception:
            if not page.is_closed():
                page.screenshot(path=str(runner.out / f'{side}-failure.png'), timeout=20000)
            raise
        finally:
            context.close()
    if not walk:
        return results
    left, right = results['reference']['keyboard'], results['embedded']['keyboard']
    expected = {'KEY.KeyW','KEY.KeyA','KEY.KeyS','KEY.KeyD','KEY.ShiftLeft','KEY.ShiftRight','POINTER.walk-look','BOUNDARY.R-in-walk'}
    assert {case['id'] for case in left + right if not case['id'].endswith('.load')} == expected
    for standalone, inline in zip(left,right):
        assert standalone['id'] == inline['id']
        if inline['id'] not in ('KEY.KeyW','KEY.KeyS'):
            assert standalone['status'] == inline['status'], inline['id']
    return results


if __name__ == '__main__':
    runner = BrowserRun(headed=True)
    try:
        if runner.args.only == ['lawson-native-fullscreen-drawing']:
            runner.record('lawson-native-fullscreen-drawing', lambda: all_native(walk=False))
        else:
            runner.record('lawson-native-fullscreen-and-walk', all_native)
    finally:
        ok = runner.finish()
    raise SystemExit(0 if ok else 1)
