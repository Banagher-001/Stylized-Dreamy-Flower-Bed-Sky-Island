"""Real production controls/inputs/readiness; full original-time tour separately.
Checkpoint each viewport so successful scopes need not be rerun after tool issues.
"""
import argparse,json
from playwright.sync_api import sync_playwright
from step4_common import *

parser=argparse.ArgumentParser();parser.add_argument('--engine',choices=['chromium','firefox','webkit'],default='chromium');parser.add_argument('--url',default='http://127.0.0.1:4177');parser.add_argument('--resume',action='store_true');args=parser.parse_args()
build=json.loads((OUT/'build-verification.json').read_text());checks=[];errors=[];completed=[];active_width=None
checkpoint=OUT/f'browser-{args.engine}-progress.json'
if args.resume and checkpoint.exists():
    previous=json.loads(checkpoint.read_text());assert previous['candidateId']==build['candidateId'];completed=previous['completedWidths'];checks=[c for c in previous['checks']if c.get('scopeWidth')in completed]
def record(name,evidence):
    checks.append({'check':name,'passed':True,'scopeWidth':active_width,'evidence':evidence});print(args.engine,name,flush=True)
    save(OUT,checkpoint.name,{'complete':False,'candidateId':build['candidateId'],'completedWidths':completed,'checks':checks})
def hold_opacity(page,key):
    d=data(page)
    if key.startswith('A'):return {'body':float(d['readingOpacity']),'title':float(d['readingTitleOpacity'])}
    return json.loads(d['filmPresentation']if key.startswith('B')else d['experimentPresentation'])

with sync_playwright()as p:
    browser=launch(p,args.engine)
    for w,h,dpr in [(1440,900,1),(1366,768,1),(390,844,2)]:
        if w in completed:continue
        active_width=w
        context=browser.new_context(viewport={'width':w,'height':h},device_scale_factor=dpr,has_touch=w==390)
        context.add_init_script(probe)
        page=context.new_page();watch(page,errors);load(page,args.url+'/?waterTime=2')
        page.wait_for_function('document.querySelector("#tour-host").dataset.guideState==="manual"')
        page.evaluate('window.__originalCanvas=document.querySelector("canvas");window.__nodes=[...document.querySelectorAll(".tour-reading-flow article")];window.__texts=window.__nodes.map(e=>e.textContent)')
        assert page.locator('main').get_attribute('data-reading-mode')=='immersive'
        # Opening/closing a work never grants implicit guide consent.
        visit(page,4.95);trigger=page.locator('[data-film-station=B1] .film-image-button');trigger.click();page.wait_for_selector('.film-dialog[data-state=ready]')
        assert data(page)['guideState']=='blocked'and data(page)['guidePhase']=='manual'
        page.locator('.film-dialog-close').click();page.wait_for_function('document.querySelector("#tour-host").dataset.guideState==="manual"')
        record(f'{w}:default off and never-started identity survives viewer',{'guide':guide_data(page),'canvas':1})
        # First guide is a held station: no prior automatic write may exist.
        guide_start(page,2.54);page.evaluate('scrollBy({top:70,behavior:"instant"})');external=manual_stays(page,250)
        record(f'{w}:first held start yields to source-unattributed native scroll',{'method':'external native scroll API, not fake trusted input; scrollbar separately exercised by native CDP harness','result':external})
        # Held reading: two actual full frames, complete clock, mode/env independence.
        current=guide_start(page,2.54);assert current['guideStation']=='A2'and float(current['guideReadSeconds'])>=14
        quiet=still(page);deadline=data(page)['guideDeadline'];original=pure_canvas(page)
        for mode in ['native','pixel']:
            page.locator(f'.tour-actions [data-mode={mode}]').click();frames(page);assert data(page)['guideDeadline']==deadline
        assert equal(original,pure_canvas(page))
        before,after=playing(page);assert data(page)['guideDeadline']==deadline
        guide_stop(page);start=float(data(page)['sceneTime']);page.wait_for_function('t=>Number(document.querySelector("#tour-host").dataset.sceneTime)>t+.1',arg=start)
        pause(page);both_off=still(page)
        record(f'{w}:four guide/environment combinations and render-mode retention',{'guideOnly':current,'heldZeroGL':quiet,'bothOnTimes':[before,after],'guideOffEnvironmentOn':True,'bothOff':both_off,'exactPixelModeRoundtrip':True})
        # Each real inscription must reach full readable state before its deadline.
        stations=[]
        for key,at in STOPS:
            state=guide_start(page,at);op=hold_opacity(page,key)
            assert state['guideStation']==key and op['body']>=.999 and op['title']>=.999
            assert float(state['guideDeadline'])-float(state['guideReadyAt'])>=float(state['guideReadSeconds'])*1000-.001
            if key in ['A1','B2','C2']:
                page.mouse.move(10,h/2);page.screenshot(path=str(OUT/f'{args.engine}-{w}-{key}-guided.png'))
            stations.append({'id':key,'H':at,'opacity':op,'guide':state})
            guide_stop(page)
        record(f'{w}:all ten actual stations hold complete original content',stations)
        # Real movement uses native document progress; reverse wheel takes over.
        guide_start(page,.9,reading=False);page.wait_for_function('Number(document.querySelector("#tour-host").dataset.displayH)>.92')
        at=float(data(page)['displayH']);page.mouse.move(w*.7,h*.4);page.mouse.wheel(0,-90)
        takeover=manual_stays(page);assert float(takeover['H'])<at
        record(f'{w}:actual reverse wheel interrupts moving camera',takeover)
        # Original image/project return and focus while guide previously active.
        guide_start(page,4.95);position=page.evaluate('scrollY');trigger.click();page.wait_for_selector('.film-dialog[data-state=ready]');covered=still(page)
        assert data(page)['guideState']=='blocked'and data(page)['guidePhase']=='paused'
        page.locator('.film-dialog-close').click();page.wait_for_function('document.querySelector("[data-film-station=B1] .film-image-button")===document.activeElement');frames(page)
        assert abs(page.evaluate('scrollY')-position)<=1 and data(page)['guideState']=='paused'
        guide_start(page,10.05);position=page.evaluate('scrollY');project_trigger=page.locator('[data-project-tab=live]');project_trigger.click();frames(page)
        assert data(page)['guideState']=='blocked'and page.evaluate('window.__originalCanvas===document.querySelector("canvas")')
        page.locator('[data-project-view=archive]').click();page.locator('.tour-project-play').click();page.wait_for_function('document.querySelector("video")?.currentTime>.15');archive=still(page)
        page.locator('.tour-project-close').click();page.wait_for_function('document.querySelector("[data-project-tab=live]")===document.activeElement');frames(page)
        assert abs(page.evaluate('scrollY')-position)<=1 and page.locator('video').count()==0 and data(page)['guideState']=='paused'
        record(f'{w}:image/live/archive stop first and restore native position/focus',{'imagePause':covered,'archivePause':archive,'within1CssPixel':True,'focusReturned':True,'videoReleased':True,'oneOriginalCanvas':True})
        if w==1440:
            # One full real deadline per engine, with no water animation/GL hold.
            held=guide_start(page,1.74);quiet=still(page);remaining=float(held['guideDeadline'])-page.evaluate('performance.now()')
            assert remaining>0;page.wait_for_timeout(max(0,remaining-120));assert data(page)['guideStation']=='A1'and data(page)['guidePhase']=='reading'
            page.wait_for_function('document.querySelector("#tour-host").dataset.guideStation==="A2"&&document.querySelector("#tour-host").dataset.guidePhase==="reading"',timeout=25000)
            arrived=guide_data(page);guide_stop(page)
            record('actual A1 deadline wakes existing loop and reaches A2 with water frozen',{'A1':held,'heldZeroGL':quiet,'A2':arrived,'sceneTime':data(page)['sceneTime']})
            keys=[]
            for key in ['PageDown','ArrowUp','Home','End','Tab']:
                guide_start(page,2.54);page.keyboard.press(key);keys.append({'key':key,'result':manual_stays(page,250)})
            record('trusted browser keyboard preserves native meaning and yields control',keys)
            # Actual mouse text selection and trusted copy; no preventDefault.
            guide_start(page,2.54)
            rect=page.locator('.about-company').first.evaluate('e=>{const r=document.createRange();r.selectNodeContents(e.firstChild);return r.getBoundingClientRect().toJSON()}')
            page.evaluate('window.__copies=[];document.addEventListener("copy",e=>window.__copies.push({trusted:e.isTrusted,text:getSelection().toString()}))')
            page.mouse.move(rect['left']+1,rect['top']+rect['height']/2);page.mouse.down();page.mouse.move(rect['right']-1,rect['top']+rect['height']/2,steps=10);page.mouse.up()
            assert page.evaluate('getSelection().toString().length>0')
            selected=page.evaluate('getSelection().toString()');page.keyboard.press('Control+c');copies=page.evaluate('window.__copies');assert copies and copies[-1]['trusted']
            assert data(page)['guidePhase']=='paused';page.evaluate('getSelection().removeAllRanges()')
            record('native selection/copy keeps original text nodes',{'selected':selected,'copyEvents':copies})
        if w==390:
            guide_start(page,2.54);y=page.evaluate('scrollY')
            if args.engine=='chromium':
                cdp=context.new_cdp_session(page)
                cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':110,'y':330}]})
                for yy in [310,285,260,235,210]:
                    cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':110,'y':yy}]});page.wait_for_timeout(35)
                cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});page.wait_for_timeout(500)
                assert abs(page.evaluate('scrollY')-y)>1
                method='actual CDP native touch scroll, no synthetic DOM TouchEvent'
            else:
                page.touchscreen.tap(110,330);method='actual Playwright touchscreen tap; native drag covered in Chromium, real phones remain pending'
            record('touch interaction relinquishes guide without scroll suppression',{'method':method,'beforeY':y,'after':manual_stays(page)})
        # Semantic reading remains one original set when layout changes.
        guide_start(page,2.54);page.locator('#tour-layout-toggle').click();frames(page)
        assert data(page)['guideState']=='blocked'and data(page)['guidePhase']=='paused'
        assert page.locator('.tour-reading-flow article[aria-hidden=false]').count()==10
        assert page.evaluate('window.__nodes.every((n,i)=>n===document.querySelectorAll(".tour-reading-flow article")[i]&&n.textContent===window.__texts[i])')
        page.locator('#tour-layout-toggle').click();visit(page,2.54);assert data(page)['guideState']=='paused'
        record(f'{w}:stable reading preserves all original nodes and explicit resume',{'articles':10,'sameTextAndNodes':True,'noAutomaticReturnStart':True})
        # Warm actual geometry/shader paths, including both live viewport sizes.
        for mode in ['pixel','native']:
            page.locator(f'.tour-actions [data-mode={mode}]').click()
            for _,at in VIEWS:visit(page,at)
        guide_start(page,2.54);guide_stop(page);warm=json.loads(data(page)['rendererStats']);cycles=[]
        count=20 if w==1440 else 4
        for i in range(count):
            state=guide_start(page,2.54);guide_stop(page);s=json.loads(data(page)['rendererStats'])
            assert all(s[k]==warm[k]for k in ['geometries','textures','programs']);cycles.append({'guide':state,'stats':s})
        record(f'{w}:repeated actual start/stop keeps fixed GPU resources',{'cycles':count,'warm':warm,'samples':cycles,'quietAfterStop':still(page)})
        assert not errors,errors
        context.close();completed.append(w);save(OUT,checkpoint.name,{'complete':False,'candidateId':build['candidateId'],'completedWidths':completed,'checks':checks})
    # Narrow/landscape/high-DPR and reduced motion use existing complete reading.
    active_width=None;capacity=[]
    for w,h,dpr in [(320,568,3),(844,390,2),(390,844,3)]:
        context=browser.new_context(viewport={'width':w,'height':h},device_scale_factor=dpr,has_touch=True)
        context.add_init_script(probe);page=context.new_page();watch(page,errors);load(page,args.url+'/?waterTime=2')
        if page.locator('main').get_attribute('data-reading-mode')!='stable':page.locator('#tour-layout-toggle').click();frames(page)
        decode(page);page.locator('.tour-actions [data-mode=native]').click();frames(page)
        assert data(page)['guideState']=='blocked'and page.locator('.tour-reading-flow article[aria-hidden=false]').count()==10
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        bounds=page.locator('canvas').evaluate('e=>({css:e.getBoundingClientRect().toJSON(),width:e.width,height:e.height})')
        assert bounds['width']<=bounds['css']['width']*2+1 and bounds['height']<=bounds['css']['height']*2+1
        page.screenshot(path=str(OUT/f'{args.engine}-{w}-capacity-dpr{dpr}.png'));capacity.append({'viewport':[w,h],'DPR':dpr,'bounds':bounds,'guide':guide_data(page),'allTenArticles':True,'horizontalOverflow':False});context.close()
    context=browser.new_context(viewport={'width':1440,'height':900},reduced_motion='reduce');context.add_init_script(probe);page=context.new_page();watch(page,errors);load(page,args.url+'/')
    assert data(page)['guideState']=='blocked'and data(page)['guidePhase']=='manual'
    paused=still(page);page.emulate_media(reduced_motion='no-preference');frames(page);assert data(page)['guidePhase']=='manual'and data(page)['sceneTime']==paused['time']
    context.close();record('capacity/DPR and reduced-motion preserve manual consent',{'cases':capacity,'reducedMotionQuiet':paused,'noAutomaticStartAfterPreferenceRemoval':True})
    assert not errors,errors
    save(OUT,f'browser-{args.engine}.json',{'passed':True,'candidateId':build['candidateId'],'browser':browser.version,'engine':args.engine,'checks':checks,'errors':errors,'realDevice':False})
    print('PASS',args.engine,len(checks),'browser groups',flush=True);browser.close()
