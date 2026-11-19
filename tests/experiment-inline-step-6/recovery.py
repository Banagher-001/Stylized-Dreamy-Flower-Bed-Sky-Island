"""Compare source recovery with the portfolio's retry after actual scene faults."""
from pair_support import BOTTLE, BrowserRun, CHILD, DESKTOP, IFRAME, LAWSON, STAGE, position, ready_main, visit_window, wait_child, wait_original


MODEL = '**/experiments/lawson/assets/models/lawson_scene.glb'


def recover(project):
    results = {}
    for side in ('reference', 'embedded'):
        embedded = side == 'embedded'
        context, page, network = r.context(DESKTOP if embedded else CHILD[DESKTOP])
        try:
            requests = []
            entry = r.origin + f'experiments/{project}/index.html'
            page.on('request', lambda request: requests.append(request.url) if request.url == entry else None)
            if project == LAWSON:
                page.route(MODEL, lambda route: route.fulfill(status=404, content_type='application/octet-stream', body=''))
                if embedded:
                    ready_main(page, r.origin)
                    visit_window(page)
                    item = page.locator(IFRAME)
                    item.wait_for(state='attached', timeout=60000)
                    broken = item.element_handle().content_frame()
                    page.locator(STAGE+'[data-scene-state=error]').wait_for(timeout=60000)
                else:
                    page.goto(entry, wait_until='domcontentloaded')
                    broken = page
                broken.locator('#fatal').wait_for(state='attached')
                broken.wait_for_function('!document.querySelector("#fatal").classList.contains("hidden")', timeout=60000, polling=100)
                assert len(network['unexpectedHttp']) == 1 and network['unexpectedHttp'][0][0] == 404, network
                signal = broken.locator('#fatal').text_content().strip()
                page.unroute(MODEL)
            else:
                broken, _ = r.open(page, project, embedded)
                broken.evaluate('''() => {
                  const ext=__bottleOcean.renderer.getContext().getExtension('WEBGL_lose_context');
                  if(!ext)throw new Error('WEBGL_lose_context unavailable');
                  document.querySelector('#gl').addEventListener('webglcontextlost',event=>window.__observedGLLoss=event.isTrusted,{once:true});
                  ext.loseContext();
                }''')
                broken.wait_for_function('window.__observedGLLoss===true && __bottleOcean.renderer.getContext().isContextLost()', polling=100)
                broken.wait_for_function('document.querySelector("#loader-error").textContent.includes("WebGL")', polling=100)
                signal = broken.locator('#loader-error').text_content().strip()
                if embedded:
                    page.locator(STAGE+'[data-scene-state=error]').wait_for(timeout=20000)

            before = position(page)
            screenshot = r.out / f'{project}-{side}-error.png'
            page.screenshot(path=str(screenshot), timeout=20000)
            if embedded:
                feedback = page.locator('.experiment-scene-status').text_content().strip()
                page.locator('.experiment-scene-retry').click()
                scene = wait_child(page, project)
                assert scene != broken and broken.is_detached()
            elif project == LAWSON:
                feedback = signal
                broken.locator('#fatal-retry').click()
                scene = page
            else:
                feedback = signal
                page.reload(wait_until='domcontentloaded')
                scene = page
            wait_original(scene, project)
            assert len(requests) == 2 and scene.url == entry, requests
            if project == LAWSON:
                scene.locator('[data-preset=day]').click()
                scene.wait_for_function('Math.abs(__LAWSON__.api.getStats().timeOfDay-9)<.02', timeout=45000, polling=100)
            else:
                scene.locator('#waveHeight').press('End')
                scene.locator('#pause-button').click()
                assert scene.evaluate('__bottleOcean.state.waveHeight===100 && __bottleOcean.state.paused')
            after = position(page)
            assert not network['external'] and before == after, (before, after, network)
            results[side] = {'errorSignal':signal, 'feedback':feedback, 'sceneReloadCount':len(requests)-1,
                             'viewport':scene.evaluate('() => [innerWidth,innerHeight,devicePixelRatio]'),
                             'nativeControlsAfterReload':True, 'hostBefore':before, 'hostAfter':after,
                             'controlledFaultNetwork':network, 'errorCapture':screenshot.name}
            if embedded:
                other = BOTTLE if project == LAWSON else LAWSON
                page.locator(f'[data-project-select={other}]').click()
                wait_original(wait_child(page, other), other)
                results[side]['otherProjectStillUsable'] = True
        finally:
            context.close()
    assert results['reference']['viewport'] == results['embedded']['viewport']
    return results


r = BrowserRun()
try:
    r.record('lawson-missing-model-and-retry', lambda: recover(LAWSON))
    r.record('bottle-graphics-loss-and-retry', lambda: recover(BOTTLE))
finally:
    ok = r.finish()
raise SystemExit(0 if ok else 1)
