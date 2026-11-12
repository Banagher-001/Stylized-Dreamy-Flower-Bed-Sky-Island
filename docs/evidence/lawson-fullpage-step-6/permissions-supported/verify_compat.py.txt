from playwright.sync_api import sync_playwright
from harness import Harness,arguments

args=arguments()
with sync_playwright()as pw:
    h=Harness(pw,args)
    def final_engine():
        c,p=h.setup();h.c2(p);h.open(p);f=h.ready(p)
        capability=f.evaluate('({fullscreen:document.fullscreenEnabled,pointerLock:typeof document.querySelector("#viewport").requestPointerLock==="function"})')
        feedback=p.locator('.tour-project-feedback').is_visible()
        assert feedback==(capability['fullscreen']is False)
        assert not p.locator('.tour-project-retry').is_visible()
        f.locator('#lights-all-off').click();assert all(v is False for v in f.evaluate('__LAWSON__.state.lights').values())
        f.locator('#lights-all-on').click();assert all(v is True for v in f.evaluate('__LAWSON__.state.lights').values())
        assert h.draws(p,p)==0;h.close(p)
        return {'realEngine':args.engine,'capabilities':capability,'capabilityNoticeMatchesActualSupport':True,'nativeLightsControlsWork':True,'parentSuspended':True}
    h.check('compat final engine native controls',final_engine)
    def original_comparison():
        c,p=h.setup(390,844);h.c2(p);h.open(p);f=h.ready(p);height=f.evaluate('innerHeight')
        script='''()=>{const r=e=>{const a=document.querySelector(e).getBoundingClientRect();return [a.x,a.y,a.width,a.height]};return {controls:document.querySelectorAll('button,input,.toggle').length,brand:r('.brand'),panel:r('#panel'),topbar:r('.topbar'),time:__LAWSON__.state.timeOfDay,roof:__LAWSON__.state.roofVisible,brandTopbarOverlap:(()=>{const a=document.querySelector('.brand').getBoundingClientRect(),b=document.querySelector('.topbar').getBoundingClientRect();return a.right>b.left&&a.top<b.bottom&&a.bottom>b.top})()}}'''
        embedded=f.evaluate(script)
        other=c.new_page();other.set_viewport_size({'width':390,'height':height});other.goto('http://127.0.0.1:4196/experiments/lawson/index.html',wait_until='domcontentloaded');other.wait_for_function('window.__LAWSON__?.ready===true',timeout=90000,polling=100)
        independent=other.evaluate(script)
        for key in ['controls','brand','panel','topbar','time','roof','brandTopbarOverlap']:assert embedded[key]==independent[key],(key,embedded[key],independent[key])
        assert embedded['controls']==41
        other.close();h.close(p)
        return {'sameOriginalViewport':[390,height],'embedded':embedded,'independent':independent,'knownMobileLayoutPreservedNotReportedAsFixed':True,'physicalDevice':False}
    h.check('compat independent and embedded original mobile',original_comparison)
    passed=h.finish()
raise SystemExit(0 if passed else 1)
