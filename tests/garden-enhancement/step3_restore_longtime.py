"""New orb attributes/uniforms survive real context loss; actual long-time frames.
The test respects the existing stable-reading recovery, then explicitly returns.
"""
from playwright.sync_api import sync_playwright
from step3_common import *

errors,restores,longtimes=[],[],[]
with sync_playwright() as p:
    browser=launch(p)
    context=browser.new_context(viewport={'width':1440,'height':900})
    context.add_init_script(probe)
    page=context.new_page();watch(page,errors)
    load(page,'http://127.0.0.1:4177/?waterTime=2')
    page.evaluate('window.__originalCanvas=document.querySelector("canvas")')
    for live in [False,True]:
        visit(page,10.05 if live else 11.5)
        if live:
            page.locator('[data-project-tab=live]').click()
            page.locator('[data-project-mode=native]').click()
        else:
            page.locator('.tour-actions [data-mode=native]').click()
        frames(page)
        old=data(page);picture=pure_canvas(page)
        (OUT/f'restore-orb-{"live" if live else "W"}-before.png').write_bytes(picture)
        page.evaluate('window.__orbLoss=document.querySelector("canvas").getContext("webgl2").getExtension("WEBGL_lose_context");window.__orbLoss.loseContext()')
        page.wait_for_selector('#tour-host[data-render-state=context-lost]')
        page.evaluate('window.__orbLoss.restoreContext()')
        page.wait_for_function('document.querySelector("main").dataset.immersiveAvailable==="true"')
        if not live:
            assert page.locator('main').get_attribute('data-reading-mode')=='stable'
            page.locator('#tour-layout-toggle').click()
            visit(page,11.5)
        else:
            page.wait_for_function('document.querySelector("#tour-host").dataset.renderState==="ready"')
        frames(page)
        actual=pure_canvas(page)
        (OUT/f'restore-orb-{"live" if live else "W"}-after.png').write_bytes(actual)
        assert equal(picture,actual),('restore pixels',live)
        assert data(page)['sceneTime']==old['sceneTime']
        assert page.evaluate('window.__originalCanvas===document.querySelector("canvas")')
        restores.append({'view':'live'if live else'W','fullGpuCanvasExact':True,'sameTime':old['sceneTime'],'sameOriginalCanvas':True,'method':'real WEBGL_lose_context; explicit return from stable reading for W'})
        if live:page.locator('.tour-project-close').click();frames(page)
    print('PASS new-orb W/live exact-pixel context restore',flush=True)
    # Existing visitor diagnostic accepts 0..86400 only; preserve that contract.
    # Positive neighborhoods beyond it are tested in the independent field probe.
    for t in [0,2,6,60,600,3600,86399.98,86399.99,86400]:
        load(page,f'http://127.0.0.1:4177/?waterTime={t}')
        visit(page,11.5)
        for mode in ['pixel','native']:
            page.locator(f'.tour-actions [data-mode={mode}]').click();frames(page)
            assert abs(float(data(page)['sceneTime'])-t)<1e-6
            row={'time':t,'mode':mode,'scene':data(page)}
            if t in [86399.98,86399.99,86400]:
                name=f'longtime-W-{mode}-t{t}.png';page.screenshot(path=str(OUT/name));row['file']=name
            longtimes.append(row)
    assert not errors,errors
    context.close();browser.close()
    failed=launch(p,extra=['--disable-webgl'])
    page=failed.new_page(viewport={'width':390,'height':844})
    page.goto('http://127.0.0.1:4177/?waterTime=2',wait_until='networkidle')
    page.wait_for_function('document.querySelector("main").dataset.readingMode==="stable"')
    assert page.locator('.tour-reading-flow article[aria-hidden=false]').count()==10
    assert page.locator('#tour-reference').is_visible()
    page.screenshot(path=str(OUT/'no-webgl-stable-reading.png'))
    fallback={'passed':True,'method':'real Chromium --disable-webgl, actual renderer failure; no fake scene ready state','tenReadableArticles':True,'referenceAvailable':True}
    failed.close()
    save(OUT,'orb-context-longtime.json',{'passed':True,'restores':restores,'longTimeProductionFrames':longtimes,'noWebGL':fallback,'errors':errors})
    print('PASS exact W/live new-orb recovery,18 long-time production renders,actual no-WebGL fallback',flush=True)
