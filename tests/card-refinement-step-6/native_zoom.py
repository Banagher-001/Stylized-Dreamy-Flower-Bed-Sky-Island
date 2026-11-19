"""Use the browser's own zoom shortcut with a real X11 Chromium window."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

from playwright.sync_api import sync_playwright

from verify import CONTINUE, HELP, OPEN, help_geometry


def check(page, keyboard, origin, out):
    page.goto(origin, wait_until='domcontentloaded')
    page.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"', timeout=90000)
    before = page.evaluate('() => ({width:innerWidth, dpr:devicePixelRatio})')
    windows = subprocess.check_output([keyboard, 'search', '--onlyvisible', '--class', 'chromium'], text=True).splitlines()
    subprocess.run([keyboard, 'windowfocus', '--sync', windows[-1], 'key', '--repeat', '5', '--delay', '160', 'ctrl+equal'], check=True)
    page.wait_for_function('d=>Math.abs(devicePixelRatio/d-2)<.02', arg=before['dpr'], timeout=10000)
    page.wait_for_function('document.querySelector("main")?.dataset.readingMode==="stable"')
    after = page.evaluate('() => ({width:innerWidth, dpr:devicePixelRatio, overflow:document.documentElement.scrollWidth-innerWidth})')
    assert after['overflow'] <= 1 and abs(after['width'] * 2 - before['width']) <= 3, (before, after)
    page.locator(OPEN).click()
    geometry = help_geometry(page)
    assert geometry['mode'] == 'inline' and geometry['overflow'] <= 1 and all(min(size) >= 44 for size in geometry['buttons'])
    close = page.locator('[data-action="help-close"]')
    page.locator(HELP).evaluate('e=>e.scrollIntoView({block:"center",behavior:"instant"})')
    page.wait_for_function('''() => {const panel=document.querySelector('.ar-tool-help-panel').getBoundingClientRect();
      return panel.top >= document.querySelector('.tour-header').getBoundingClientRect().bottom && panel.bottom <= innerHeight;}''')
    page.evaluate('() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))')
    subprocess.run(['import', '-silent', '-window', hex(int(windows[-1])), str(out / 'browser-zoom-200.png')], check=True)
    close.click()
    assert page.locator(HELP).is_hidden()
    page.locator(CONTINUE).click()
    page.wait_for_function('document.querySelector("main")?.dataset.flowAnchor==="B1"')
    return {'before': before, 'after': after, 'help': geometry, 'continuedTo': 'B1'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--origin', required=True)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--env-file', required=True, type=Path)
    parser.add_argument('--build-record', required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    os.environ.update(json.loads(args.env_file.read_text())['browserEnvironment'])
    keyboard = shutil.which('xdotool') or '/workspace/.cache/browser-deps/root/usr/bin/xdotool'
    build = json.loads(args.build_record.read_text())
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False, executable_path=shutil.which('chromium'),
            args=['--no-sandbox', '--use-gl=angle', '--use-angle=gl', '--ignore-gpu-blocklist', '--window-size=1652,1010'])
        try:
            context = browser.new_context(no_viewport=True)
            page = context.new_page()
            page.set_default_timeout(15000)
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            data = check(page, keyboard, args.origin, args.out)
            assert not errors, errors
            result = {**data, 'candidateId': build['candidateId'], 'engine': browser.version, 'complete': True}
            (args.out / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
            print({'actualBrowserZoom': data['after']['dpr'] / data['before']['dpr'], 'complete': True}, flush=True)
        finally:
            browser.close()
