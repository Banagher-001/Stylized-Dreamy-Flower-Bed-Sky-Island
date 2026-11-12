"""Final-build original retry, real slow loading, graphics and native input checks."""
import subprocess
from playwright.sync_api import sync_playwright
from host_harness import Harness,arguments
args=arguments()
with sync_playwright()as pw:
    h=Harness(pw,args)
    def retries():
        c,p=h.setup();bad=[True]
        c.route('**/experiments/lawson/assets/models/lawson_scene.glb',lambda r:r.abort('failed')if bad[0]else r.continue_())
        h.c2(p);h.open(p);h.state(p,'error',40000);f=h.child(p);assert f.locator('#fatal').is_visible()
        message=f.locator('#fatal-msg').inner_text();p.evaluate('window.__step7FirstIframe=document.querySelector("iframe")');f.evaluate('window.__oldFailedDocument=true')
        h.picture('original-model-error');bad[0]=False;f.locator('#fatal-retry').click();f=h.ready(p)
        assert p.evaluate('document.querySelector("iframe")===__step7FirstIframe')and f.evaluate('window.__oldFailedDocument===undefined')
        bad[0]=True;f.evaluate('location.reload()');h.state(p,'error',40000);bad[0]=False;p.locator('.tour-project-retry').click();h.ready(p)
        assert p.evaluate('document.querySelector("iframe")!==__step7FirstIframe')and p.locator('iframe').count()==1;h.close(p)
        return {'realMainModelFailure':True,'originalErrorMessage':message,'originalFatalRetryNavigatedNewDocumentInSameIframe':True,'hostRetryCreatedNewIframe':True,'readyAfterBothRetries':True,'originalControl':'#fatal-retry'}
    h.check('recovery original fatal retry and host retry',retries)
    def slow():
        c,p=h.setup(390,844);pending=[]
        c.route('**/experiments/lawson/js/main.js',lambda r:pending.append(r));h.c2(p);h.open(p);h.child(p);h.state(p,'slow',20000)
        assert pending and p.locator('.tour-project-feedback').is_visible()and p.locator('.tour-project-close').is_visible()
        assert not h.child(p).evaluate('!!window.__LAWSON__?.ready');h.picture('slow-mobile')
        for route in pending:route.continue_()
        h.ready(p);assert not p.locator('.tour-project-feedback').is_visible();h.close(p)
        return {'actualModuleRequestHeld':True,'slowBeforeReady':True,'exitStillUsable':True,'releasedModuleThenOriginalReady':True}
    h.check('recovery slow original then ready',slow)
    def graphics():
        c,p=h.setup();h.c2(p);h.open(p);f=h.ready(p)
        supported=f.evaluate('''()=>{const canvas=document.querySelector('#viewport'),gl=canvas.getContext('webgl2'),e=gl.getExtension('WEBGL_lose_context');window.__step7Loss=e;window.__step7Restore=null;canvas.addEventListener('webglcontextrestored',event=>__step7Restore={trusted:event.isTrusted},{once:true});if(e)e.loseContext();return !!e}''');assert supported
        h.state(p,'error',10000);assert f.evaluate('__LAWSON__.ready===true');h.picture('graphics-loss')
        f.evaluate('__step7Loss.restoreContext()');f.wait_for_function('window.__step7Restore?.trusted===true',timeout=30000,polling=100)
        h.state(p,'error',5000);assert '重新载入'in p.locator('.tour-project-feedback').inner_text()
        p.locator('.tour-project-retry').click();h.ready(p);assert p.locator('iframe').count()==1;h.close(p)
        return {'realWebGLContextExtensionLoss':True,'trustedRestoredEvent':True,'staleOriginalReadyNotTrusted':True,'newOriginalDocumentReadyAfterExplicitRetry':True}
    h.check('recovery graphics loss restored explicit reload',graphics)
    def keyboard():
        c,p=h.setup();h.c2(p);before=h.open(p);f=h.ready(p);assert p.evaluate('document.activeElement.classList.contains("tour-project-close")')
        f.locator('#time-slider').focus();f.locator('#time-slider').press('Home');f.wait_for_function('Math.abs(__LAWSON__.api.getStats().timeOfDay)<.02',timeout=30000,polling=100)
        f.locator('#time-slider').press('End');f.wait_for_function('Math.abs(__LAWSON__.api.getStats().timeOfDay-24)<.02',timeout=30000,polling=100)
        assert abs(p.evaluate('scrollY')-before['y'])<3
        p.locator('#project-tab-live').focus();p.keyboard.press('ArrowRight');assert p.locator('#tour-project-archive').is_visible()and p.locator('iframe').count()==0
        p.locator('.tour-project-close').focus();p.keyboard.press('Escape');p.wait_for_function('!document.querySelector(".tour-project-dialog").open&&document.activeElement?.dataset.projectTab==="live"')
        assert abs(p.evaluate('scrollY')-before['y'])<3
        return {'originalHomeEndStayedInChild':True,'parentScrollUnchanged':True,'hostArrowKeySwitchedArchiveAndUnloaded':True,'hostEscClosedAndRestoredTrigger':True,'guideDidNotResume':p.locator('#tour-guide').get_attribute('aria-pressed')=='false'}
    h.check('input child keyboard and host return isolation',keyboard)
    def native():
        c,p=h.setup();h.c2(p);h.open(p);f=h.ready(p)
        f.locator('#btn-fullscreen').click();p.wait_for_function('document.fullscreenElement?.tagName==="IFRAME"')
        n=f.evaluate('__audit.draws');f.wait_for_function('n=>__audit.draws>n+2000',arg=n,timeout=30000,polling=100);h.picture('native-fullscreen')
        subprocess.run(['/workspace/.cache/browser-deps/root/usr/bin/xdotool','key','Escape'],check=True);p.wait_for_function('document.fullscreenElement===null');assert p.locator('.tour-project-dialog').evaluate('e=>e.open')
        f.locator('#btn-walk').click();f.wait_for_function('document.pointerLockElement?.id==="viewport"')
        subprocess.run(['/workspace/.cache/browser-deps/root/usr/bin/xdotool','key','Escape'],check=True);f.wait_for_function('document.pointerLockElement===null');assert p.locator('.tour-project-dialog').evaluate('e=>e.open');h.close(p)
        return {'actualOriginalFullscreen':True,'renderedAfterEnteringFullscreen':True,'actualOriginalPointerLock':True,'realX11Escapes':True,'hostStaysOpenUntilExplicitReturn':True}
    h.check('native fullscreen rendering pointer lock and exits',native)
    passed=h.finish()
raise SystemExit(0 if passed else 1)
