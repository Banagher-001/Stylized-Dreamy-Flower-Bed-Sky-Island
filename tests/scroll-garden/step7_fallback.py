"""Decoration/font/WebGL/media failure paths, separate from normal diagnostics."""
from io import BytesIO
from types import SimpleNamespace
import ast, math
from PIL import Image
from playwright.sync_api import sync_playwright
from step7_common import *

args=SimpleNamespace(engine='fallback')
source=(ROOT/'tests/scroll-garden/step5_browser.py').read_text()
node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='contrast')
contrast_source=ast.get_source_segment(source,node).replace('.pillar-reading','.experiment-reading').replace('data-reading-ink','data-experiment-ink')
exec(compile(contrast_source,'<fallback actual contrast>','exec'))
NO_2D="""(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(kind,...args){return kind==='2d'?null:original.call(this,kind,...args);};})()"""

def observe(page,errors,diagnostics):
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('console',lambda m:diagnostics.append({'type':m.type,'text':m.text}) if m.type in ['warning','error'] else None)
def ready(page):
    page.goto('http://127.0.0.1:4173/?tour=prototype&waterTime=2',wait_until='networkidle')
    page.wait_for_selector('#tour-host[data-render-state="ready"]')
def close_project(page):
    page.locator('.tour-project-close').click()
    page.wait_for_function('document.querySelector("#tour-host").dataset.overlayState==="closed"')
    frames(page)

with sync_playwright() as p:
    browser=launch(p);context=browser.new_context(viewport={'width':1440,'height':900});context.add_init_script(NO_2D)
    page=context.new_page();errors=[];diagnostics=[];observe(page,errors,diagnostics);ready(page)
    assert all(data(page)[key]=='fallback' for key in ['magicStatus','filmMagicStatus','experimentMagicStatus'])
    views=[]
    for width,height in [(1440,900),(1366,768),(390,844)]:
        resize(page,width,height)
        for station,h,y in STOPS:
            go(page,h)
            article=page.locator('.experiment-reading article:not([hidden])')
            article.locator('h2').evaluate("e=>e.style.fontFamily=\"'Missing Step Seven Font', serif\"")
            article.locator('.experiment-body').evaluate("e=>e.style.fontFamily=\"'Missing Step Seven Font', serif\"")
            frames(page)
            r=page.locator('.experiment-reading').evaluate('e=>({data:{...e.dataset},rect:e.getBoundingClientRect().toJSON(),noInternalScroll:e.scrollHeight<=e.clientHeight+1,text:e.innerText})')
            assert r['data']['fits']=='true' and r['data']['anchorClear']=='true' and r['noInternalScroll'],r
            bounds=article.locator('h2,[data-experiment-ink]').evaluate_all('es=>es.map(e=>{const p=e.closest(".experiment-reading").getBoundingClientRect(),r=e.getBoundingClientRect();return{font:parseFloat(getComputedStyle(e).fontSize),inside:r.left>=p.left+10&&r.right<=p.right-10&&r.top>=p.top+10&&r.bottom<=p.bottom-10}})')
            assert all(b['inside'] and b['font']>=16 for b in bounds),bounds
            if station=='C2':
                assert article.locator('button:enabled').count()==2
                assert article.locator('button').evaluate_all('es=>es.every(e=>{const r=e.getBoundingClientRect();return r.width>=44&&r.height>=44})')
            page.mouse.move(10,height/2);page.screenshot(path=str(OUT/f'fallback-font-{width}-{station}.png'))
            views.append({'viewport':[width,height],'station':station,'layout':r,'textBounds':bounds,'contrast':contrast(page,f'font-{width}-{station}')})
        go(page,10.05);h=data(page)['displayH'];page.locator('[data-project-tab=live]').click();page.wait_for_selector('.tour-project-dialog[open][data-tab=live]');frames(page)
        assert page.locator('canvas').count()==1;page.locator('[data-project-mode=native]').click();assert page.locator('canvas').get_attribute('data-render-mode')=='native'
        close_project(page);assert data(page)['displayH']==h
        page.locator('[data-project-tab=archive]').click();page.wait_for_selector('.tour-project-dialog[open][data-tab=archive]');assert '当前可体验' in page.locator('.tour-project-archive').inner_text();close_project(page)
    assert not errors,errors
    save('fallback-decoration-font.json',{'passed':True,'checks':3,'method':'Canvas2D disabled only in test; actual serif fallback applied to all three C stations at three target dimensions; actual composed text contrast; live/archive actions and return exercised','views':views,'unhandledExceptions':errors,'diagnostics':diagnostics})
    browser.close();print('PASS: nine no-decoration/font-fallback C layouts, actual contrast and usable live/archive actions',flush=True)

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-webgl'])
    page=browser.new_page(viewport={'width':390,'height':844});errors=[];diagnostics=[];observe(page,errors,diagnostics)
    page.goto('http://127.0.0.1:4173/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="error"]')
    assert page.locator('canvas').count()==0 and page.get_by_role('alert').inner_text()
    assert page.locator('[data-stop]:disabled,[data-reading-stop]:disabled,.mode-controls button:disabled,#tour-motion:disabled').count()==18
    panel=page.locator('.experiment-fallback');assert panel.get_attribute('aria-hidden')=='false'
    assert panel.locator('article:not([hidden])').count()==3 and panel.locator('article').evaluate_all('es=>es.every(e=>!e.inert&&e.getAttribute("aria-hidden")==="false")')
    text=panel.inner_text();assert all(t in text for t in ['从想法到交互','Vibe Coding','庭院习作','让想象，动起来。'])
    assert page.locator('[data-project-tab=live]').is_disabled() and page.locator('[data-project-tab=archive]').is_enabled()
    page.locator('[data-project-tab=archive]').click();page.wait_for_selector('.tour-project-dialog[open][data-tab=archive]')
    assert page.locator('[data-project-view=live]').is_disabled() and '固定视角动效片段' in page.locator('.tour-project-archive').inner_text()
    page.screenshot(path=str(OUT/'fallback-no-webgl-archive.png'));close_project(page);assert page.locator('[data-project-tab=archive]').evaluate('e=>document.activeElement===e')
    page.screenshot(path=str(OUT/'fallback-no-webgl.png'));page.locator('#tour-reference').click();page.wait_for_selector('#about');assert '枫叶互动' in page.locator('#about').inner_text()
    assert not errors,errors
    save('fallback-no-webgl.json',{'passed':True,'noWebGL':True,'canvasCount':0,'disabledGraphicControls':18,'allCTextUsable':True,'liveExplicitlyDisabled':True,'archiveAndCloseFocusUsable':True,'referenceUsable':True,'unhandledExceptions':errors,'expectedInitializationDiagnostics':diagnostics})
    browser.close();print('PASS: no-WebGL C content, archive, focus return and reference remain usable',flush=True)

with sync_playwright() as p:
    browser=launch(p);page=browser.new_page(viewport={'width':390,'height':844});errors=[];diagnostics=[];observe(page,errors,diagnostics)
    pattern='**/courtyard-interactive-cover-*.webp';page.route(pattern,lambda route:route.abort());ready(page);go(page,10.05)
    page.wait_for_function('document.querySelector(".experiment-reading").dataset.coverState==="error"')
    assert '封面暂不可用' in page.locator('.experiment-image-state').inner_text()
    before=data(page)['displayH'];page.locator('[data-project-tab=archive]').click();page.wait_for_selector('.tour-project-dialog[open][data-tab=archive]')
    page.wait_for_selector('.project-current-cover .tour-project-image-error')
    page.screenshot(path=str(OUT/'fallback-cover-error.png'));page.unroute(pattern)
    page.locator('.project-current-cover .tour-project-image-error button').click()
    page.wait_for_function('(()=>{const i=document.querySelector(".project-current-cover img");return i.complete&&i.naturalWidth===1440&&!document.querySelector(".project-current-cover .tour-project-image-error")})()')
    close_project(page);assert data(page)['displayH']==before
    assert not errors,errors
    save('fallback-cover.json',{'passed':True,'realCoverRequestAborted':True,'previewErrorReadable':True,'archiveRetryLoads1440pxOriginal':True,'closeRestoresStation':True,'unhandledExceptions':errors,'expectedAbortedImageDiagnostics':diagnostics})
    browser.close();print('PASS: real cover failure, archive retry and return restoration',flush=True)

with sync_playwright() as p:
    browser=launch(p);page=browser.new_page(viewport={'width':1440,'height':900});errors=[];diagnostics=[];observe(page,errors,diagnostics)
    pattern='**/courtyard-motion-*.mp4';page.route(pattern,lambda route:route.abort());ready(page);go(page,10.05);before=data(page)['displayH']
    page.locator('[data-project-tab=archive]').click();page.wait_for_selector('.tour-project-dialog[open][data-tab=archive]');page.locator('.tour-project-play').click()
    page.wait_for_selector('.tour-project-dialog[data-media-state=error]');assert page.locator('.tour-project-media-retry').is_visible();assert '暂时无法载入' in page.locator('.tour-project-media-status').inner_text()
    page.screenshot(path=str(OUT/'fallback-video-error.png'));page.unroute(pattern);page.locator('.tour-project-media-retry').click()
    page.wait_for_selector('.tour-project-dialog[data-media-state=ready]')
    metadata=page.locator('video').evaluate('v=>({duration:v.duration,width:v.videoWidth,height:v.videoHeight,paused:v.paused,controls:v.controls,inline:v.playsInline,loop:v.loop})')
    assert abs(metadata['duration']-12)<.1 and metadata['width']==metadata['height']==680 and metadata['controls'] and metadata['inline'] and not metadata['loop'] and metadata['paused']
    # Retry deliberately does not autoplay. Native HTMLMediaElement playback remains usable.
    page.locator('video').evaluate('v=>v.play()');page.wait_for_function('document.querySelector("video").currentTime>.15&&!document.querySelector("video").paused')
    assert page.locator('video').count()==1;close_project(page);assert not page.locator('video').count() and data(page)['displayH']==before
    assert not errors,errors
    save('fallback-video.json',{'passed':True,'realClipRequestAborted':True,'errorAndRetryUsable':True,'retryDoesNotAutoplay':True,'nativeMediaControls':metadata,'actualDecoderAdvancesAfterRetry':True,'closeRemovesDecoderAndRestoresStation':True,'unhandledExceptions':errors,'expectedAbortedVideoDiagnostics':diagnostics})
    browser.close();print('PASS: actual clip abort/retry, native decode and close cleanup',flush=True)
