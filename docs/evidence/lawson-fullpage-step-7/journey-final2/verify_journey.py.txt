"""Final production host journeys and engine/mobile representative checks."""
import json
from playwright.sync_api import sync_playwright
from host_harness import Harness,arguments
args=arguments()
with sync_playwright()as pw:
    h=Harness(pw,args)
    def journey(prefix):
        c,p=h.setup(prefix=prefix);requests=[];p.on('request',lambda r:requests.append(r.url));h.c2(p)
        assert not any('/experiments/lawson/'in u for u in requests)and p.locator('iframe').count()==0
        before=h.open(p);f=h.ready(p)
        defaults=f.evaluate('({time:__LAWSON__.state.timeOfDay,lights:__LAWSON__.state.lights,roof:__LAWSON__.state.roofVisible,walk:__LAWSON__.state.walk,controls:document.querySelectorAll("button,input,.toggle").length,viewport:[innerWidth,innerHeight]})')
        assert defaults['controls']==41 and defaults['time']==18.5 and defaults['roof']and not defaults['walk']and all(defaults['lights'].values())
        geometry=p.locator('iframe').bounding_box();header=p.locator('.tour-project-header').bounding_box();assert abs(geometry['width']-p.evaluate('innerWidth'))<1 and abs(geometry['height']-(p.evaluate('innerHeight')-header['height']))<1
        assert h.draws(p,p)==0;f.locator('[data-preset=night]').click();f.wait_for_function('Math.abs(__LAWSON__.api.getStats().timeOfDay-22)<.02',timeout=30000,polling=100)
        h.picture('live-'+('root'if prefix=='/'else'prefix'))
        old=f;p.locator('#project-tab-archive').click();p.wait_for_function('document.querySelectorAll("iframe").length===0');assert old.is_detached()
        assert p.locator('#tour-project-archive').get_attribute('data-project-id')=='lawson'
        p.wait_for_function('[...document.querySelectorAll("#tour-project-archive img")].every(i=>i.complete&&i.naturalWidth>0)')
        assert h.draws(p,p)==0
        link=p.locator('.tour-project-header [data-project-independent]');expected='http://127.0.0.1:4197'+prefix+'experiments/lawson/index.html';assert link.get_attribute('href')==expected
        assert set(link.get_attribute('rel').split())>={'noopener','noreferrer'}
        with c.expect_page()as opened:link.click()
        other=opened.value;other.wait_for_function('window.__LAWSON__?.ready===true',timeout=90000,polling=100);assert other.url==expected and other.evaluate('opener===null');other.close()
        p.locator('#project-tab-live').click();new=h.ready(p);assert new!=old and p.locator('iframe').count()==1
        assert new.evaluate('__LAWSON__.state.timeOfDay===18.5&&__LAWSON__.state.roofVisible&&!__LAWSON__.state.walk')
        h.close(p);p.wait_for_function('document.activeElement?.dataset.projectTab==="live"')
        after=p.evaluate('({y:scrollY,h:document.querySelector("#tour-host").dataset.displayH,guide:document.querySelector("#tour-guide").getAttribute("aria-pressed")})')
        assert abs(after['y']-before['y'])<3 and abs(float(after['h'])-float(before['h']))<.01 and after['guide']=='false'
        assert p.locator('dialog[open]').count()==0
        p.locator('[data-project-select=courtyard]').click();h.open(p,'archive');assert p.locator('#tour-project-archive').get_attribute('data-project-id')=='courtyard'
        assert p.locator('.tour-project-frame-pair img').count()==2
        for img in p.locator('.tour-project-frame-pair img').all():img.scroll_into_view_if_needed();img.evaluate('e=>e.decode()')
        p.locator('.tour-project-play').click();p.wait_for_function('document.querySelector(".tour-project-dialog").dataset.mediaState==="ready"',timeout=30000,polling=100)
        p.wait_for_function('document.querySelector(".tour-project-dialog video")?.currentTime>0',timeout=15000,polling=100)
        clip=p.locator('.tour-project-dialog video').evaluate('e=>({time:e.currentTime,duration:e.duration,controls:e.controls})')
        p.locator('#project-tab-live').click();assert p.locator('video').count()==0 and p.locator('iframe').count()==0
        for mode in ['native','pixel']:
            p.locator('[data-project-mode='+mode+']').click();p.wait_for_function('m=>document.querySelector("#tour-host canvas").dataset.renderMode===m',arg=mode)
        if p.locator('#tour-host').get_attribute('data-motion-state')!='running':p.locator('.tour-project-motion').click()
        p.wait_for_function('document.querySelector("#tour-host").dataset.motionState==="running"');assert h.draws(p,p)>0
        p.locator('.tour-project-motion').click();p.wait_for_function('document.querySelector("#tour-host").dataset.motionState==="paused"')
        p.wait_for_timeout(400);paused_samples=[h.draws(p,p,400)for _ in range(3)]
        (h.folder/('paused-draw-observation-'+('root'if prefix=='/'else'prefix')+'.json')).write_text(json.dumps({'afterLayoutSettlingMS':400,'intervalMS':400,'drawSamples':paused_samples,'host':p.locator('#tour-host').evaluate('e=>({...e.dataset})')},ensure_ascii=False,indent=2)+'\n')
        assert all(n==0 for n in paused_samples),paused_samples
        h.close(p);assert p.locator('video').count()==0
        p.locator('[data-project-select=lawson]').click()
        if p.locator('main').get_attribute('data-reading-mode')!='stable':p.locator('#tour-layout-toggle').click()
        p.locator('[data-flow-live]').click();assert p.locator('.tour-project-dialog').get_attribute('data-project-id')=='courtyard';assert p.locator('iframe').count()==0;h.close(p)
        p.reload(wait_until='domcontentloaded');p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=60000,polling=100);h.c2(p)
        assert p.locator('.experiment-reading').get_attribute('data-project-id')=='lawson'and p.locator('iframe').count()==0
        return {'prefix':prefix,'lazyBeforeOpen':True,'defaults':defaults,'iframeBounds':geometry,'headerBounds':header,'originalIndependentURL':expected,'originalIndependentReadyAndNoOpener':True,'parentDrawsWhileCovered':0,'archiveAndReentryUnload':True,'readingBefore':before,'readingAfter':after,'courtyardFrames':2,'courtyardOriginalClipPlayed':clip,'courtyardLiveModesAndPlayPause':True,'waterEntryStillCourtyard':True,'refreshResetsSelectionWithoutPreloading':True}
    if args.engine=='chromium':
        for prefix in ['/','/Stylized-Dreamy-Flower-Bed-Sky-Island/']:h.check('journey '+prefix,lambda prefix=prefix:journey(prefix))
    def engine_controls():
        c,p=h.setup();h.c2(p);h.open(p);f=h.ready(p);records=[]
        for preset,value in [('day',9),('night',22),('dusk',18.5)]:
            f.locator('[data-preset='+preset+']').click();f.wait_for_function('v=>Math.abs(__LAWSON__.api.getStats().timeOfDay-v)<.02',arg=value,timeout=45000,polling=100);records.append({'preset':preset,'time':f.evaluate('__LAWSON__.api.getStats().timeOfDay')})
        for selector,on in [('#lights-all-off',False),('#lights-all-on',True)]:f.locator(selector).click();assert all(v is on for v in f.evaluate('__LAWSON__.state.lights').values())
        cameras=[]
        for name in ['front','interior','hero']:
            before=f.evaluate('__LAWSON__.debugDoor().cam');f.locator('[data-cam='+name+']').click();f.wait_for_function('b=>JSON.stringify(__LAWSON__.debugDoor().cam)!==JSON.stringify(b)',arg=before,timeout=45000,polling=100);assert f.evaluate('__LAWSON__.state.cameraMode')==name;cameras.append({'preset':name,'actualCamera':f.evaluate('__LAWSON__.debugDoor().cam')})
        f.locator('#btn-roof').click();assert not f.evaluate('__LAWSON__.state.roofVisible');f.locator('#btn-roof').click();assert f.evaluate('__LAWSON__.state.roofVisible')
        f.locator('#btn-help').click();assert f.locator('#help').is_visible();f.locator('#help-close').click();assert f.locator('#help').is_hidden()
        f.locator('#panel-collapse').click();assert f.locator('#panel').evaluate('e=>e.classList.contains("collapsed")');f.locator('#panel-collapse').click();assert not f.locator('#panel').evaluate('e=>e.classList.contains("collapsed")')
        capability=f.evaluate('({fullscreen:document.fullscreenEnabled,pointerLock:typeof document.querySelector("#viewport").requestPointerLock==="function"})')
        assert h.draws(p,p)==0;h.picture('engine-native-controls');h.close(p)
        return {'actualEngine':args.engine,'timePresets':records,'allLightsNativeButtons':True,'cameraActualMotion':cameras,'roofHelpAndPanel':True,'capabilities':capability,'parentDraws':0,'full41And17NotClaimedOnThisEngine':args.engine!='chromium'}
    h.check('engine representative original controls',engine_controls)
    def mobile_comparison():
        c,p=h.setup(390,844);h.c2(p);h.open(p);f=h.ready(p)
        script='''()=>{const b=s=>{const r=document.querySelector(s).getBoundingClientRect();return [r.x,r.y,r.width,r.height]};return {viewport:[innerWidth,innerHeight],controls:document.querySelectorAll('button,input,.toggle').length,brand:b('.brand'),panel:b('#panel'),topbar:b('.topbar'),time:__LAWSON__.state.timeOfDay,roof:__LAWSON__.state.roofVisible}}'''
        embedded=f.evaluate(script);h.picture('mobile-embedded-default');h.close(p)
        p.set_viewport_size({'width':embedded['viewport'][0],'height':embedded['viewport'][1]});p.goto('http://127.0.0.1:4197/original/index.html',wait_until='domcontentloaded');p.wait_for_function('window.__LAWSON__?.ready===true',timeout=90000,polling=100)
        independent=p.evaluate(script);assert embedded==independent,(embedded,independent);h.picture('mobile-independent-default')
        return {'embedded':embedded,'independent':independent,'originalSameViewportAndGeometry':True,'knownOriginalMobileLayoutNotReportedAsFixed':True,'physicalDevice':False}
    h.check('mobile independent embedded default parity',mobile_comparison)
    passed=h.finish()
raise SystemExit(0 if passed else 1)
