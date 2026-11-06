"""Independent static delivery check; no repo/history/server fixtures required.

python3 -m pip install playwright
python3 -m playwright install chromium
python3 tests/scroll-garden/step12_release_check.py --site dist --out /tmp/release-check
Use --engines chromium,firefox,webkit when those browsers are installed.
Browser executables can be selected through CHROMIUM_EXECUTABLE and
COURTYARD_WEBKIT_EXECUTABLE. Linux headed engines need a display and GL libraries.
"""
import argparse
import functools
import hashlib
import json
import mimetypes
import os
from pathlib import Path
import shutil
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import urlopen
from playwright.sync_api import sync_playwright

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass

def launch(p, engine):
    options = {'headless': engine == 'chromium'}
    if engine == 'chromium':
        binary = os.environ.get('CHROMIUM_EXECUTABLE') or shutil.which('chromium')
        if binary:
            options['executable_path'] = binary
        options['args'] = ['--no-sandbox', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']
    if engine == 'firefox':
        options['firefox_user_prefs'] = {'webgl.force-enabled': True}
    if engine == 'webkit' and os.environ.get('COURTYARD_WEBKIT_EXECUTABLE'):
        options['executable_path'] = os.environ['COURTYARD_WEBKIT_EXECUTABLE']
    return getattr(p, engine).launch(**options)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--site', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--engines', default='chromium')
    args = parser.parse_args()
    site, out = args.site.resolve(), args.out.resolve()
    assert (site / 'index.html').is_file()
    assert site != out and site not in out.parents, 'Keep evidence outside the tested artifact.'
    out.mkdir(parents=True, exist_ok=True)
    files = {str(p.relative_to(site)): digest(p) for p in sorted(site.rglob('*')) if p.is_file()}
    html = (site / 'index.html').read_text()
    assert 'lang="zh-CN"' in html and 'og:image' in html and 'twitter:card' in html
    assert 'canonical' not in html and 'og:url' not in html and 'example.com' not in html
    assert '/workspace/' not in html and '%BASE_URL%' not in html
    servers, checks, asset_checks = [], [], []
    with tempfile.TemporaryDirectory(prefix='garden-static-check-') as temp:
        parent = Path(temp)
        mount = parent / 'review' / 'courtyard'
        shutil.copytree(site, mount)
        origins = []
        for folder, prefix in [(site, '/'), (parent, '/review/courtyard/')]:
            handler = functools.partial(QuietHandler, directory=str(folder))
            server = ThreadingHTTPServer(('127.0.0.1', 0), handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            servers.append(server)
            origins.append(f'http://127.0.0.1:{server.server_port}{prefix}')
        try:
            for base in origins:
                for name, expected in files.items():
                    with urlopen(base + name) as response:
                        body, mime = response.read(), response.headers.get_content_type()
                        assert response.status == 200
                    assert hashlib.sha256(body).hexdigest() == expected, (base, name)
                    ext = Path(name).suffix
                    required = {'.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml', '.webp': 'image/webp', '.png': 'image/png', '.mp4': 'video/mp4', '.json': 'application/json'}.get(ext)
                    if required:
                        assert mime == required, (name, mime, required)
                    asset_checks.append({'mount': 'root' if base.endswith(f':{servers[0].server_port}/') else 'subdirectory', 'file': name, 'mime': mime, 'sha256': expected})
                try:
                    urlopen(base + 'assets/does-not-exist.js')
                except HTTPError as error:
                    assert error.code == 404
                else:
                    raise AssertionError('Missing asset must return 404, not an HTML fallback.')
            with sync_playwright() as p:
                for engine in args.engines.split(','):
                    browser = launch(p, engine)
                    for index, base in enumerate(origins):
                        context = browser.new_context(viewport={'width': 1440, 'height': 900})
                        page = context.new_page()
                        errors, failed, external = [], [], []
                        page.on('pageerror', lambda e: errors.append(str(e)))
                        page.on('requestfailed', lambda r: failed.append(r.url))
                        page.on('request', lambda r: external.append(r.url) if not r.url.startswith(('http://127.0.0.1:', 'data:', 'blob:')) else None)
                        for suffix in ['', '?tour=prototype']:
                            page.goto(base + suffix, wait_until='networkidle')
                            page.wait_for_selector('#tour-host[data-render-state="ready"]')
                            page.wait_for_function('document.querySelector("main").dataset.layoutReady === "true"')
                            assert '张辰翰' in page.title() and 'STEP' not in page.title()
                            assert page.locator('canvas').count() == 1
                            assert not page.locator('#tour-reference').is_visible()
                            assert page.locator('.tour-reading-flow article').count() == 10
                            assert page.locator('html').get_attribute('lang') == 'zh-CN'
                            page.reload(wait_until='networkidle')
                            page.wait_for_selector('#tour-host[data-render-state="ready"]')
                            checks.append({'engine': engine, 'mount': index, 'entry': suffix or 'default', 'refresh': True, 'passed': True})
                        for mode in ['pixel', 'native']:
                            page.goto(base + f'?render={mode}&waterTime=2', wait_until='networkidle')
                            page.wait_for_selector('#tour-host[data-render-state="ready"]')
                            page.locator(f'.tour-actions [data-mode={mode}]').wait_for(state='visible')
                            assert page.locator(f'.tour-actions [data-mode={mode}]').get_attribute('aria-pressed') == 'true'
                        page.goto(base + '?tour=reference&waterTime=2', wait_until='networkidle')
                        page.wait_for_selector('#scene-host[data-render-state="ready"]')
                        text = page.locator('body').inner_text()
                        assert all(s in text for s in ['张辰翰', '枫叶互动', '游族网络', 'Vibe Coding'])
                        assert page.locator('#tour-host').count() == 0
                        checks.append({'engine': engine, 'mount': index, 'entry': 'reference', 'passed': True})
                        page.goto(base + '?debug=1&render=native&marker=preserved#old', wait_until='networkidle')
                        page.wait_for_selector('#tour-host[data-render-state="ready"]')
                        href = page.locator('#tour-reference').get_attribute('href')
                        assert href == base + '?debug=1&render=native&marker=preserved&tour=reference', href
                        page.locator('#tour-reference').click()
                        page.wait_for_selector('#scene-host[data-render-state="ready"]')
                        assert not errors and not failed and not external, (engine, errors, failed, external)
                        checks.append({'engine': engine, 'mount': index, 'debugReferenceHref': href, 'noExternalRuntimeRequests': True, 'passed': True})
                        context.close()
                        # Real WebGL creation failure at the new root; the visible
                        # reference link must leave the courtyard, retaining path/mode.
                        fallback = browser.new_context(viewport={'width': 390, 'height': 844})
                        fallback.add_init_script('''(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type,...args){if(String(type).startsWith('webgl'))return null;return original.call(this,type,...args)}})()''')
                        fp = fallback.new_page()
                        fp.goto(base + '?render=native&marker=preserved', wait_until='networkidle')
                        fp.wait_for_selector('#tour-host[data-render-state="error"]')
                        assert fp.locator('main').get_attribute('data-reading-mode') == 'stable'
                        assert fp.locator('.tour-reading-flow article').count() == 10
                        assert fp.locator('#tour-reference').is_visible()
                        assert fp.locator('#tour-reference').get_attribute('href') == base + '?render=native&marker=preserved&tour=reference'
                        fp.locator('#tour-reference').click()
                        fp.wait_for_selector('#scene-host')
                        assert 'tour=reference' in fp.url and fp.locator('#tour-host').count() == 0
                        checks.append({'engine': engine, 'mount': index, 'noWebGLReferenceEscape': True, 'stableDocument': True, 'passed': True})
                        fallback.close()
                        reduced = browser.new_context(viewport={'width': 390, 'height': 844}, reduced_motion='reduce')
                        rp = reduced.new_page()
                        rp.goto(base, wait_until='networkidle')
                        rp.wait_for_selector('#tour-host[data-render-state="ready"]')
                        assert rp.locator('main').get_attribute('data-reading-mode') == 'stable'
                        assert rp.locator('#tour-motion').inner_text() == '播放动效'
                        checks.append({'engine': engine, 'mount': index, 'reducedMotionDefaultEntry': True, 'passed': True})
                        if index == 0:
                            rp.screenshot(path=str(out / f'{engine}-default-reduced-motion.png'))
                        reduced.close()
                    browser.close()
            report = {'passed': True, 'siteFiles': files, 'staticAssetChecks': asset_checks, 'browserChecks': checks, 'browserCheckGroups': len(checks), 'actualSubdirectory': 'review/courtyard/', 'physicalDevice': False}
            (out / 'release-check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
            print(f'PASS {len(checks)} browser groups; {len(asset_checks)} exact file/MIME checks; root + actual subdirectory', flush=True)
        finally:
            for server in servers:
                server.shutdown()
                server.server_close()

if __name__ == '__main__':
    main()
