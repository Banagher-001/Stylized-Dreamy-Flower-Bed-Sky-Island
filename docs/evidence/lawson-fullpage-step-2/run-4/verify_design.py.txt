"""Browser checks for the static design. These are not original-page/iframe tests."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse,json,traceback,shutil
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/evidence/lawson-fullpage-step-2'
parser=argparse.ArgumentParser()
parser.add_argument('--run',default='run-1')
parser.add_argument('--only-prefix',default='',help='Run only cases whose names start with this prefix')
args=parser.parse_args()
folder=OUT/args.run
folder.mkdir(exist_ok=False)
for path in [Path(__file__),*[OUT/name for name in ['design-preview.html','design-preview.css','design-preview.js']]]:
    shutil.copyfile(path,folder/(path.name+'.txt'))
report={'scope':'Static second-step design only; no actual source page or iframe loaded','createdAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'checks':[],'pageErrors':[],'httpErrors':[],'failedRequests':[],'requests':[]}
def save():
    (folder/'design-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
def case(name,fn):
    if args.only_prefix and not name.startswith(args.only_prefix):return
    try:
        evidence=fn();report['checks'].append({'name':name,'passed':True,'evidence':evidence});print('PASS '+name,flush=True)
    except Exception as e:
        report['checks'].append({'name':name,'passed':False,'error':str(e),'traceback':traceback.format_exc()});print('FAIL '+name+': '+str(e),flush=True)
    save()

URL='http://127.0.0.1:4192/design-preview.html'
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
    report['browser']=browser.version
    def page_for(w,h,reduced=False):
        context=browser.new_context(viewport={'width':w,'height':h},device_scale_factor=1,reduced_motion='reduce' if reduced else 'no-preference')
        page=context.new_page()
        page.on('pageerror',lambda e:report['pageErrors'].append(str(e)))
        page.on('request',lambda r:report['requests'].append(r.url))
        page.on('response',lambda r:report['httpErrors'].append({'url':r.url,'status':r.status})if r.status>=400 else None)
        page.on('requestfailed',lambda r:report['failedRequests'].append({'url':r.url,'failure':r.failure}))
        page.goto(URL,wait_until='networkidle')
        page.wait_for_function('document.querySelector("#cover-image").naturalWidth>0')
        return context,page
    def click_open(page,selector='#open-live'):
        page.locator(selector).scroll_into_view_if_needed()
        before=page.evaluate('scrollY')
        page.locator(selector).click()
        page.wait_for_function('document.querySelector("#project-dialog").open')
        page.wait_for_timeout(200)
        page.wait_for_function('document.querySelector("#reference-image").naturalWidth>0')
        return before
    def toolbar_targets(page):
        rows=page.locator('.viewer-toolbar button,.viewer-toolbar a').evaluate_all('''els=>els.filter(e=>e.getClientRects().length).map(e=>({id:e.id,rect:e.getBoundingClientRect().toJSON()}))''')
        for row in rows:
            r=row['rect'];assert r['width']>=43.9 and r['height']>=43.9,row
            assert r['left']>=-.5 and r['right']<=page.viewport_size['width']+.5,row
            assert r['top']>=-.5 and r['bottom']<=page.viewport_size['height']+.5,row
        return rows
    def layout(w,h):
        context,page=page_for(w,h)
        try:
            initial=page.evaluate('__STEP2_DESIGN__.snapshot()')
            assert initial['selectedProjectId']=='lawson' and initial['actualIframes']==0
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            entry=page.locator('#project-entry').bounding_box()
            assert entry['width']<=500.5
            buttons=page.locator('.project-selector button,.entry-actions button,.site-header button').evaluate_all('els=>els.map(e=>({id:e.id,width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height}))')
            assert all(r['width']>=43.9 and r['height']>=43.9 for r in buttons)
            page.screenshot(path=str(folder/f'entry-{w}x{h}.png'),full_page=True)
            before=click_open(page)
            assert page.evaluate('document.activeElement.id')=='return-reading'
            toolbar=page.locator('.viewer-toolbar').bounding_box();live=page.locator('#live-panel').bounding_box()
            expected=48 if w<=767 or h<=480 else 56
            assert abs(toolbar['height']-expected)<.5,toolbar
            assert abs(live['width']-w)<.5 and abs(live['height']-(h-toolbar['height']))<.5,(toolbar,live)
            assert abs(live['y']-toolbar['height'])<.5
            targets=toolbar_targets(page)
            toolbar=page.locator('.viewer-toolbar').bounding_box()
            page.screenshot(path=str(folder/f'live-{w}x{h}.png'))
            page.locator('#tab-archive').click()
            assert page.locator('#archive-panel').is_visible() and page.locator('#live-panel').is_hidden()
            assert page.locator('#archive-panel h3').inner_text().replace('\n','')=='一间店，几个日夜。'
            if w in [1440,390]:page.screenshot(path=str(folder/f'archive-{w}x{h}.png'))
            page.locator('#return-reading').click()
            assert not page.locator('#project-dialog').evaluate('e=>e.open')
            assert page.evaluate('document.activeElement.id')=='open-live'
            assert abs(page.evaluate('scrollY')-before)<=2
            return {'viewport':[w,h],'entryBounds':entry,'entryTargets':buttons,'toolbar':toolbar,'pageArea':live,'toolbarTargets':targets,'focusAndScrollRestored':True,'realIframes':0,'meaning':'Measured host design area; the displayed image is a static reference, not an interactive page.'}
        finally:context.close()
    for w,h in [(1920,1080),(1440,900),(1366,768),(768,1024),(390,844),(320,568),(844,390)]:
        case(f'layout {w}x{h}',lambda w=w,h=h:layout(w,h))

    def selection_and_keys():
        context,page=page_for(1440,900)
        try:
            page.locator('#select-lawson').focus();page.keyboard.press('ArrowRight')
            assert page.evaluate('__STEP2_DESIGN__.snapshot().selectedProjectId')=='courtyard'
            assert page.evaluate('document.activeElement.id')=='select-courtyard'
            page.locator('#open-archive').click()
            assert page.evaluate('__STEP2_DESIGN__.snapshot().activeProject.id')=='courtyard'
            assert '停一会儿' in page.locator('#archive-panel h3').inner_text()
            page.screenshot(path=str(folder/'courtyard-archive.png'))
            page.locator('#return-reading').click()
            assert page.evaluate('document.activeElement.id')=='open-archive'
            assert page.locator('#entry-title').inner_text()=='庭院习作'
            page.locator('#select-courtyard').focus();page.keyboard.press('Home')
            assert page.evaluate('__STEP2_DESIGN__.snapshot().selectedProjectId')=='lawson'
            click_open(page)
            page.locator('#reference-page').focus();page.keyboard.press('Escape')
            assert page.locator('#project-dialog').evaluate('e=>e.open')
            page.locator('#return-reading').focus();page.keyboard.press('Escape')
            assert not page.locator('#project-dialog').evaluate('e=>e.open')
            assert page.evaluate('document.activeElement.id')=='open-live'
            page.reload(wait_until='networkidle')
            assert page.evaluate('__STEP2_DESIGN__.snapshot().selectedProjectId')=='lawson'
            return {'keyboardProjectSelection':True,'correctArchiveIdentity':True,'selectedProjectRetainedAfterClose':True,'reloadDefaultsToLawson':True,'referenceEscapeKeptDialogOpen':True,'hostEscapeClosedDialog':True,'limitation':'Escape was checked on a static focusable reference, not inside a real iframe, fullscreen or pointer lock.'}
        finally:context.close()
    case('project identity, keyboard selection and Escape design',selection_and_keys)

    def states_and_independent():
        context,page=page_for(1440,900)
        try:
            click_open(page);rows=[]
            for state in ['loading','slow','error','ready']:
                page.locator('.design-controls summary').click();page.locator('#design-state').select_option(state);page.locator('.design-controls summary').click()
                assert page.locator('#project-dialog').get_attribute('data-state')==state
                assert page.locator('#return-reading').is_visible() and page.locator('#open-independent').is_visible()
                assert page.locator('#host-retry').is_visible()==(state in ['slow','error'])
                assert page.locator('#original-retry-demo').is_visible()==(state=='error')
                if state=='error':
                    page.locator('#original-retry-demo').click();assert page.locator('#project-dialog').get_attribute('data-state')=='loading'
                    page.locator('.design-controls summary').click();page.locator('#design-state').select_option('error');page.locator('.design-controls summary').click()
                page.screenshot(path=str(folder/f'state-{state}.png'));rows.append({'state':state,'toolbar':page.locator('.viewer-toolbar').bounding_box()})
            with context.expect_page() as opened:page.locator('#open-independent').click()
            other=opened.value;other.wait_for_load_state('networkidle')
            assert 'standalone=lawson' in other.url and other.locator('#standalone-reference').is_visible()
            assert '静态样稿' in other.locator('#standalone-reference header').inner_text()
            other.screenshot(path=str(folder/'independent-static-reference.png'));other.close()
            for _ in range(3):
                page.locator('#return-reading').click();click_open(page)
                assert page.locator('dialog[open]').count()==1 and page.locator('iframe').count()==0
            return {'manualStateDesigns':rows,'independentLink':'design-preview.html?standalone=lawson (static reference only)','repeatedDialogOpenClose':3,'actualSourcePageLoaded':False,'actualIframes':0}
        finally:context.close()
    case('state layouts, independent static reference and repeated opening',states_and_independent)

    def large_font(w,h):
        context,page=page_for(w,h)
        try:
            click_open(page);page.locator('.design-controls summary').click();page.locator('#design-font').select_option('200');page.locator('.design-controls summary').click()
            assert page.evaluate('getComputedStyle(document.documentElement).fontSize')=='32px'
            targets=toolbar_targets(page)
            toolbar=page.locator('.viewer-toolbar').bounding_box()
            assert page.locator('#live-panel').bounding_box()['height']>0
            page.screenshot(path=str(folder/f'font-200-{w}x{h}.png'))
            page.locator('#return-reading').click()
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
            return {'rootFontPixels':32,'viewport':[w,h],'toolbar':toolbar,'targets':targets,'meaning':'CSS text enlargement at 200%, not a physical-browser zoom or mobile hardware test.'}
        finally:context.close()
    for w,h in [(1440,900),(390,844),(320,568)]:case(f'200 percent text {w}x{h}',lambda w=w,h=h:large_font(w,h))

    def reduced_motion():
        context,page=page_for(390,844,True)
        try:
            click_open(page)
            css=page.locator('#project-dialog').evaluate('e=>({animation:getComputedStyle(e).animationName,duration:getComputedStyle(e).animationDuration,reduced:matchMedia("(prefers-reduced-motion: reduce)").matches})')
            assert css['reduced'] and css['animation']=='none'
            return css
        finally:context.close()
    case('reduced motion removes opening transition',reduced_motion)
    browser.close()

report['modelRequests']=[u for u in report['requests']if '.glb' in u or '/vendor/three/'in u or '/js/main.js'in u]
report['externalRequests']=[u for u in report['requests']if not u.startswith('http://127.0.0.1:4192/')and not u.startswith('data:')]
report['passed']=all(c['passed']for c in report['checks'])and not any(report[k]for k in ['pageErrors','httpErrors','failedRequests','modelRequests','externalRequests'])
save()
print(json.dumps({'passed':report['passed'],'checks':len(report['checks']),'pageErrors':len(report['pageErrors']),'httpErrors':len(report['httpErrors']),'modelRequests':len(report['modelRequests'])},ensure_ascii=False))
raise SystemExit(0 if report['passed'] else 1)
