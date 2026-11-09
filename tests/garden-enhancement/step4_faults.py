"""Actual image-request delays/errors and explicit decode rejection injection.
Fault injection is labelled; it is not footage or physical-device evidence.
"""
import argparse,json
from playwright.sync_api import sync_playwright
from step4_common import *

parser=argparse.ArgumentParser();parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');parser.add_argument('--url',default='http://127.0.0.1:4177');args=parser.parse_args()
candidate=json.loads((OUT/'build-verification.json').read_text())['candidateId']
results=[]
def dom_ready(page):
    page.goto(args.url+'/?waterTime=2',wait_until='domcontentloaded')
    page.wait_for_selector('#tour-host[data-render-state=ready]')
    page.wait_for_function('document.querySelector("main").dataset.layoutReady==="true"')
    frames(page)

with sync_playwright()as p:
    browser=launch(p,args.engine)
    for scenario in ['release','timeout','error']:
        context=browser.new_context(viewport={'width':1440,'height':900});context.add_init_script(probe)
        page=context.new_page();held=[];exceptions=[];page.on('pageerror',lambda e:exceptions.append(str(e)))
        def intercept(route):
            if route.request.resource_type=='image':held.append(route)
            else:route.continue_()
        page.route('**/*signal-garden*.webp*',intercept)
        dom_ready(page);guide_start(page,4.95,reading=False);page.wait_for_timeout(700)
        assert held and data(page)['guidePhase']=='arriving'and data(page)['guideReadyAt']==''
        pending=guide_data(page)
        if scenario=='timeout':
            page.wait_for_function('document.querySelector("#tour-host").dataset.guidePhase==="paused"',timeout=10000)
            timed_out=guide_data(page)
        for route in held:
            if scenario=='error':route.fulfill(status=404,content_type='image/webp',body=b'')
            else:route.continue_()
        if scenario=='timeout':
            page.wait_for_timeout(500);assert data(page)['guidePhase']=='paused'
            resumed=guide_start(page,reading=True)
            result={'scenario':scenario,'pending':pending,'timedOut':timed_out,'lateLoadDoesNotRestart':True,'explicitResume':resumed}
        else:
            page.wait_for_function('document.querySelector("#tour-host").dataset.guidePhase==="reading"',timeout=5000)
            actual=guide_data(page);assert float(actual['guideReadSeconds'])>=12
            assert float(actual['guideDeadline'])-float(actual['guideReadyAt'])>=12000
            result={'scenario':scenario,'pending':pending,'actual':actual,'quietAfterReady':still(page)}
        assert not exceptions,exceptions
        guide_stop(page);page.unroute_all(behavior='ignoreErrors');context.close();results.append(result);print(args.engine,'image',scenario,'passed',flush=True)
    # A decoder can reject even after naturalWidth is known. Do not microtask-spin.
    context=browser.new_context(viewport={'width':1440,'height':900});context.add_init_script(probe)
    context.add_init_script('HTMLImageElement.prototype.decode=()=>Promise.reject(new Error("Step4 intentional decode-rejection test"))')
    page=context.new_page();exceptions=[];page.on('pageerror',lambda e:exceptions.append(str(e)));dom_ready(page)
    guide_start(page,4.95,reading=False);page.wait_for_function('document.querySelector("#tour-host").dataset.guidePhase==="paused"',timeout=10000)
    assert not exceptions,exceptions
    results.append({'scenario':'explicit test-only decode rejection','result':guide_data(page),'finiteFailureNoUnhandledException':True,'quietAfterStop':still(page)})
    context.close()
    # Root-font stress is labelled as CSS text scaling, not OS/browser zoom.
    context=browser.new_context(viewport={'width':320,'height':568},device_scale_factor=3);context.add_init_script(probe);page=context.new_page();dom_ready(page)
    page.evaluate('document.documentElement.style.fontSize="32px"');page.wait_for_timeout(450);frames(page)
    assert page.locator('main').get_attribute('data-reading-mode')=='stable'
    assert data(page)['guideState']=='blocked'
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    rows=page.locator('.tour-reading-flow article').evaluate_all('es=>es.map(e=>({id:e.dataset.flowAnchor,hidden:e.hidden,aria:e.getAttribute("aria-hidden"),overflowX:e.scrollWidth-e.clientWidth,overflowY:e.scrollHeight-e.clientHeight}))')
    assert len(rows)==10 and all(not r['hidden']and r['aria']=='false'and r['overflowX']<=1 and r['overflowY']<=1 for r in rows),rows
    page.screenshot(path=str(OUT/f'{args.engine}-320-200percent-font.png'));results.append({'scenario':'320px CSS root font200percent,DPR3','allOriginalArticles':rows,'guide':guide_data(page),'horizontalOverflow':False});context.close()
    if args.engine=='chromium':
        failed=launch(p,extra=['--disable-webgl']);page=failed.new_page(viewport={'width':390,'height':844})
        page.goto(args.url+'/?waterTime=2',wait_until='networkidle');page.wait_for_function('document.querySelector("main").dataset.readingMode==="stable"')
        assert page.locator('.tour-reading-flow article[aria-hidden=false]').count()==10 and data(page)['guideState']=='blocked'
        assert page.locator('#tour-reference').is_visible();page.screenshot(path=str(OUT/'no-webgl-guide-blocked.png'));results.append({'scenario':'real --disable-webgl renderer failure','guide':guide_data(page),'tenReadableArticles':True,'referenceAvailable':True});failed.close()
    browser.close()
save(OUT,f'faults-{args.engine}.json',{'passed':True,'candidateId':candidate,'url':args.url,'engine':args.engine,'cases':results,'method':'real intercepted image requests delayed/fulfilled404; decoder-rejection explicitly injected in test; no production timing overrides, DOM ready-state flags or fake visibility events','physicalDevice':False})
print('PASS',args.engine,len(results),'fault/capacity groups',flush=True)
