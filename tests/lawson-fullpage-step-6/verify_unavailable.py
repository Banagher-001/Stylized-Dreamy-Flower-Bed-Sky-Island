from playwright.sync_api import sync_playwright
from harness import Harness,arguments

args=arguments();assert args.no_webgl
with sync_playwright()as pw:
    h=Harness(pw,args)
    def unavailable():
        c,p=h.setup(390,844);h.c2(p);h.open(p);h.state(p,'error',30000);f=h.child(p)
        assert f.locator('#fatal').is_visible()and f.evaluate('__LAWSON__.ready===false&&!!__LAWSON__.error')
        assert p.locator('.tour-project-close').is_visible();h.close(p)
        p.locator('[data-project-select=courtyard]').click();assert p.locator('[data-project-tab=live]').is_disabled()
        h.open(p,'archive');assert p.locator('#tour-project-archive').is_visible()and p.locator('iframe').count()==0;h.close(p)
        return {'browserActuallyLaunchedWithDisableWebGL':True,'originalNativeRendererFailureDetected':True,'mainReadingAndArchivesUsable':True,'independentLinkNotClaimedToBypassHardware':True}
    h.check('graphics browser without WebGL',unavailable)
    passed=h.finish()
raise SystemExit(0 if passed else 1)
