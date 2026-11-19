"""Schedule trusted wheel pulses independently of Chromium's input acknowledgements."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import shutil
from urllib.parse import urlsplit

from playwright.async_api import async_playwright
from observe import DESKTOP, START_TRACE, save


async def verify(args):
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            executable_path=shutil.which('chromium'),
            args=['--no-sandbox', '--use-gl=angle', '--use-angle=gl', '--ignore-gpu-blocklist'],
        )
        try:
            page = await browser.new_page(viewport={'width': DESKTOP[0], 'height': DESKTOP[1]})
            errors = []
            requests = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('console', lambda message: errors.append(message.text) if message.type == 'error' else None)
            page.on('requestfailed', lambda request: requests.append(request.failure))
            page.on('response', lambda response: requests.append(response.status) if response.status >= 400 else None)

            async def local_only(route):
                parts = urlsplit(route.request.url)
                if parts.scheme in ('http', 'https') and parts.netloc != urlsplit(args.origin).netloc:
                    errors.append('External request: ' + parts.netloc)
                    await route.abort()
                else:
                    await route.continue_()

            await page.route('**/*', local_only)
            await page.goto(args.origin, wait_until='domcontentloaded')
            await page.wait_for_function('''() => document.querySelector('main')?.dataset.layoutReady==='true' &&
                document.querySelector('#tour-host')?.dataset.renderState==='ready' ''', timeout=90000)
            delta = await page.evaluate('3.34/12.3*(document.documentElement.scrollHeight-innerHeight)-scrollY')
            await page.mouse.move(24, 300)
            await page.mouse.wheel(0, delta)
            await page.wait_for_function('''() => document.querySelector('.ar-tools-browser').dataset.entranceReason==='completed' &&
                document.querySelector('.ar-tools-browser').dataset.trackMode==='program' ''')
            await page.locator('[data-action="auto"]').click()
            client = await page.context.new_cdp_session(page)
            loop = asyncio.get_running_loop()
            groups = {}
            for label, period in [('slow', .2), ('fast', .04)]:
                await page.locator('button[data-category="G6"]').click()
                await page.wait_for_function('''() => document.querySelector('.ar-tools-browser').dataset.trackEnabled==='false' &&
                    document.querySelector('.ar-tools-browser').dataset.trackMode==='native' ''')
                xy = await page.evaluate('''() => {
                    const c=document.querySelector('.ar-tool-controls').getBoundingClientRect();
                    const r=document.querySelector('.ar-tool-rail').getBoundingClientRect();
                    return [(c.left+r.left)/2,(r.top+r.bottom)/2];
                }''')
                await page.mouse.move(*xy)
                await page.evaluate(START_TRACE)
                sends = []
                issued = []
                started = loop.time()
                for i in range(5):
                    await asyncio.sleep(max(0, started + i * period - loop.time()))
                    issued.append((loop.time()-started)*1000)
                    sends.append(asyncio.create_task(client.send('Input.dispatchMouseEvent', {
                        'type': 'mouseWheel', 'x': xy[0], 'y': xy[1], 'deltaX': 0, 'deltaY': 60,
                    })))
                await asyncio.gather(*sends)
                await page.wait_for_timeout(380)
                trace = await page.evaluate('window.wheelTrace.stop()')
                rows, events = trace['frames'], trace['events']
                groups[label] = {'targetIntervalMs': period*1000, 'issuedAtMs': issued, 'trace': trace}
                save(args.out / 'samples.json', groups)
                assert 1 <= len(events) <= 5 and sum(e['dy'] for e in events) == 300, events
                assert all(e['trusted'] and e['claimed'] for e in events), events
                assert all(row['y'] == rows[0]['y'] and row['target'] == rows[0]['target'] for row in rows)
                assert rows[-1]['x'] > rows[0]['x'] + 12 and not rows[-1]['pending'] and rows[-1]['speed'] == 0
                peak = max(row['speed'] for row in rows)
                last = events[-1]['at']
                idle_at = next(at for at in trace['stops'] if at > last)
                sampled_idle_at = next(row['at'] for row in rows if row['at'] > last and not row['pending'] and row['speed'] == 0)
                assert 180 < idle_at-last <= 360, (idle_at-last, sampled_idle_at-last)
                assert peak <= 560
                groups[label].update(peakPxPerSecond=peak, tailMs=idle_at-last, observedIdleMs=sampled_idle_at-last)
            assert groups['fast']['peakPxPerSecond'] >= 1.5 * groups['slow']['peakPxPerSecond']
            assert not errors and not requests, (errors, requests)
            build = json.loads(args.build_record.read_text())
            return {'candidateId': build['candidateId'], 'runtimeInputDigest': build['runtimeInputDigest'],
                    'groups': groups, 'engine': browser.version, 'trustedInput': True, 'clockModified': False, 'passed': True}
        finally:
            await browser.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--origin', required=True)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--env-file', required=True, type=Path)
    parser.add_argument('--build-record', required=True, type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    os.environ.update(json.loads(args.env_file.read_text())['browserEnvironment'])
    result = asyncio.run(verify(args))
    save(args.out / 'result.json', result)
    print({k: {n: round(v[n],1) for n in ('peakPxPerSecond', 'tailMs')} for k, v in result['groups'].items()}, flush=True)
