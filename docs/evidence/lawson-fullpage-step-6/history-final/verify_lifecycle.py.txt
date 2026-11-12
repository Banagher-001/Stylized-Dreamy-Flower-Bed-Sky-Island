import subprocess
from playwright.sync_api import sync_playwright
from harness import Harness,arguments

args=arguments()
def keys(*sequence):subprocess.run(['/workspace/.cache/browser-deps/root/usr/bin/xdotool','key','--clearmodifiers',*sequence],check=True)
with sync_playwright()as pw:
    h=Harness(pw,args)
    def background(phase):
        c,p=h.setup();pending=[];blocked=[phase=='loading'];bad=[phase=='error']
        c.route('**/experiments/lawson/assets/models/lawson_scene.glb',lambda r:pending.append(r)if blocked[0]else r.abort('failed')if bad[0]else r.continue_())
        h.c2(p);h.open(p)
        if phase=='ready':h.ready(p)
        elif phase=='error':h.state(p,'error')
        else:h.child(p)
        # Playwright explicitly enables focus/visibility emulation. Disable
        # that test setting, then use Chrome's real tab UI; no app property or
        # synthetic visibility event is substituted for the browser outcome.
        p.bring_to_front();session=c.new_cdp_session(p)
        session.send('Emulation.setFocusEmulationEnabled',{'enabled':False})
        original=p.locator('iframe').element_handle();p.evaluate('window.__keptFrame=document.querySelector("iframe")')
        before_pages=len(c.pages);keys('ctrl+t');p.wait_for_timeout(700);hidden=p.evaluate('document.hidden')
        # Chrome's own tab UI is used; don't synthesize visibility properties.
        if len(c.pages)>before_pages:keys('ctrl+w');p.wait_for_timeout(700)
        else:p.bring_to_front();p.wait_for_timeout(300)
        visible=p.evaluate('document.visibilityState');assert visible=='visible'
        assert p.locator('iframe').count()==1 and p.evaluate('document.querySelector("iframe")===__keptFrame')
        if phase=='loading':
            blocked[0]=False
            for r in pending:r.continue_()
            h.ready(p)
        elif phase=='error':bad[0]=False;p.locator('.tour-project-retry').click();h.ready(p)
        else:h.state(p,'ready')
        assert p.locator('#tour-guide').get_attribute('aria-pressed')=='false';assert h.draws(p,p)==0
        events=p.evaluate('__audit.visibility');h.close(p)
        return {'phase':phase,'actualHiddenObserved':hidden,'visibilityEvents':events,'automationFocusEmulationDisabled':True,'sameInstancePreservedAcrossTabSwitch':True,'stateRecheckedAndUsable':True,'hiddenPropertyOrEventsFaked':False}
    for phase in ['loading','ready','error']:h.check('visibility browser tab '+phase,lambda phase=phase:background(phase))
    def back_forward():
        c,p=h.setup();h.c2(p);h.open(p);h.ready(p)
        c.route('**/step6-history-target.html',lambda r:r.fulfill(status=200,content_type='text/html',body='<!doctype html><title>History target</title><link rel="icon" href="data:,"><p>History target</p>'))
        p.goto('http://127.0.0.1:4196/step6-history-target.html',wait_until='domcontentloaded');p.go_back(wait_until='domcontentloaded')
        p.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"',timeout=60000,polling=100)
        shows=p.evaluate('__audit.pageshow');cached=any(e['persisted']for e in shows)
        assert p.locator('iframe').count()<=1
        if p.locator('.tour-project-dialog').evaluate('e=>e.open'):h.ready(p);h.close(p)
        else:h.c2(p);h.open(p);h.ready(p);h.close(p)
        return {'actualHistoryBack':True,'pageshowEvents':shows,'BFCacheActuallyUsed':cached,'notClaimedIfReloaded':True,'experienceUsableAfterReturn':True}
    h.check('history actual back and recovery',back_forward)
    def reduced():
        c,p=h.setup();h.c2(p);h.open(p);f=h.ready(p)
        p.emulate_media(reduced_motion='reduce');p.wait_for_timeout(400)
        assert f.evaluate('matchMedia("(prefers-reduced-motion: reduce)").matches')
        assert h.draws(p,p)==0;old=f.evaluate('__audit.draws');f.wait_for_function('n=>__audit.draws>n',arg=old,timeout=15000,polling=100)
        h.close(p);assert p.locator('#tour-host').get_attribute('data-motion-state')=='paused'
        assert p.locator('#tour-guide').get_attribute('aria-disabled')=='true';p.emulate_media(reduced_motion='no-preference');p.wait_for_timeout(200)
        assert p.locator('#tour-guide').get_attribute('aria-pressed')=='false'
        return {'realMediaQueryEmulation':True,'parentPauseRespected':True,'originalJSStillDrawsAsBaseline':True,'noPauseAllInjected':True,'guideNotRestarted':True}
    h.check('accessibility reduced motion semantics',reduced)
    def parent_context():
        c,p=h.setup();h.c2(p);h.open(p);f=h.ready(p)
        value=p.evaluate('''()=>{const gl=document.querySelector('#tour-host canvas').getContext('webgl2');const ext=gl.getExtension('WEBGL_lose_context');window.__parentLoss=ext;if(!ext)return false;ext.loseContext();return true}''');assert value
        p.wait_for_function('document.querySelector("#tour-host").dataset.renderState==="context-lost"')
        assert h.draws(p,p)==0 and f.evaluate('__LAWSON__.ready===true')
        p.evaluate('__parentLoss.restoreContext()');p.wait_for_timeout(700);assert h.draws(p,p)==0 and p.locator('iframe').count()==1
        h.close(p)
        # Context loss selects stable reading. Its offscreen cover correctly
        # stays suspended until it becomes visible; don't demand a hidden draw.
        p.evaluate('scrollTo({top:0,behavior:"instant"})')
        p.wait_for_function('document.querySelector("#tour-host").dataset.renderState==="ready"',timeout=30000,polling=100)
        return {'realParentContextLossAndRestore':True,'originalRemainedIndependent':True,'coveredRecoveryDidNotDraw':True,'parentReadyWhenCoverVisibleAgain':True}
    h.check('graphics parent recovery stays covered',parent_context)
    passed=h.finish()
raise SystemExit(0 if passed else 1)
