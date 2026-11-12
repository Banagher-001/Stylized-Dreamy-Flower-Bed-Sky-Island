from playwright.sync_api import sync_playwright
from harness import Harness,arguments,ROOT

args=arguments()
with sync_playwright()as pw:
    h=Harness(pw,args)
    def document_error(code):
        c,p=h.setup();bad=[True]
        c.route('**/experiments/lawson/index.html',lambda r:r.fulfill(status=code,content_type='text/html',body='<!doctype html><title>Unavailable</title><p>Unavailable</p>')if bad[0]else r.continue_())
        h.c2(p);h.open(p);h.state(p,'error',5000);assert '页面未能正常打开'in p.locator('.tour-project-feedback').inner_text()
        bad[0]=False;p.locator('.tour-project-retry').click();h.ready(p);h.close(p)
        return {'HTTPStatusInjected':code,'genericDocumentFailureNotGuessedStatus':True,'explicitRetryRecovered':True}
    for code in [404,500]:h.check('network document '+str(code),lambda code=code:document_error(code))
    def vendor_error():
        c,p=h.setup();bad=[True]
        c.route('**/experiments/lawson/vendor/three/three.module.js',lambda r:r.abort('failed')if bad[0]else r.continue_())
        h.c2(p);h.open(p);h.state(p,'slow',20000);f=h.child(p)
        assert f.evaluate('!window.__LAWSON__');h.state(p,'error',30000);assert f.locator('#fatal').is_visible()
        bad[0]=False;p.locator('.tour-project-retry').click();h.ready(p);h.close(p)
        return {'realVendorFetchAborted':True,'slowBeforeOriginalTimeout':True,'originalFatalObserved':True,'retryRecovered':True}
    h.check('network vendor module failure',vendor_error)
    def car_error():
        c,p=h.setup();bad=[True]
        c.route('**/experiments/lawson/assets/models/car_B.glb',lambda r:r.abort('failed')if bad[0]else r.continue_())
        h.c2(p);h.open(p);h.state(p,'error',30000);f=h.child(p);assert f.locator('#fatal').is_visible()
        bad[0]=False;f.locator('#fatal-retry').click();h.ready(p);h.close(p)
        return {'realCarResourceFailure':True,'nativeRetryRecovered':True}
    h.check('network car model failure',car_error)
    def offline(warm=False):
        c,p=h.setup();h.c2(p);p.wait_for_function('document.querySelector(".experiment-reading").dataset.coverState==="ready"')
        if warm:h.open(p);h.ready(p);h.close(p)
        c.set_offline(True);h.open(p);p.wait_for_timeout(13500)
        state=p.locator('.tour-project-dialog').get_attribute('data-embedded-state')
        assert state in ['ready','slow','error']
        if state=='ready':assert h.child(p).evaluate('__LAWSON__.ready===true')
        c.set_offline(False)
        if state!='ready':p.locator('.tour-project-retry').click();h.ready(p)
        h.close(p);return {'warmCache':warm,'actualOfflineState':state,'recovered':True,'offlineDidNotAutomaticallyMeanFailure':True}
    h.check('network cold offline and return',lambda:offline(False))
    h.check('network warm offline and return',lambda:offline(True))
    def blocked_embed():
        c,p=h.setup();blocked=[True];original=(ROOT/'public/experiments/lawson/index.html').read_bytes()
        c.route('**/experiments/lawson/index.html',lambda r:r.fulfill(status=200,content_type='text/html',body=original,headers={'Content-Security-Policy':"frame-ancestors 'none'"})if blocked[0]else r.continue_())
        h.c2(p);h.open(p);h.state(p,'slow',20000)
        with c.expect_page()as popup:p.locator('.tour-project-header [data-project-independent]').click()
        other=popup.value;other.wait_for_function('window.__LAWSON__?.ready===true',timeout=90000,polling=100);other.close()
        blocked[0]=False;p.locator('.tour-project-retry').click();h.ready(p);h.close(p)
        return {'realFrameAncestorsDenial':True,'independentOriginalReadyWithSamePolicy':True,'noGuessedFailureCause':True,'retryAfterPolicyRestored':True}
    h.check('network restricted embedding',blocked_embed)
    passed=h.finish()
raise SystemExit(0 if passed else 1)
