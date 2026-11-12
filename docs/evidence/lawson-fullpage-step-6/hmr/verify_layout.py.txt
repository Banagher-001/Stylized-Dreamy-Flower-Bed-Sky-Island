from playwright.sync_api import sync_playwright
from harness import Harness,arguments

args=arguments()
with sync_playwright()as pw:
    h=Harness(pw,args)
    def layout(w,ht):
        c,p=h.setup(w,ht);h.c2(p);before=h.open(p);f=h.ready(p)
        box=p.locator('iframe').bounding_box();bar=p.locator('.tour-project-header').bounding_box()
        assert abs(box['width']-w)<1 and abs(box['height']-(ht-bar['height']))<1,(box,bar)
        assert abs(bar['height']-(48 if w<=767 or ht<=480 else 56))<1
        assert abs(f.evaluate('innerHeight')-box['height'])<1 and f.evaluate('innerWidth')==w
        for r in p.locator('.tour-project-header button,.tour-project-header a').evaluate_all('es=>es.filter(e=>e.getClientRects().length).map(e=>e.getBoundingClientRect().toJSON())'):
            assert r['width']>=44 and r['height']>=44 and r['left']>=0 and r['right']<=w+.5 and r['bottom']<=ht,r
        parent_draws=h.draws(p,p);assert parent_draws==0,parent_draws
        child_start=f.evaluate('__audit.draws');f.wait_for_function('n=>__audit.draws>n',arg=child_start,timeout=15000,polling=100)
        f.locator('#panel-collapse').click();assert f.locator('#panel').evaluate('e=>e.classList.contains("collapsed")')
        h.picture('viewport-'+str(w)+'x'+str(ht))
        p.locator('#project-tab-archive').click();assert p.locator('iframe').count()==0
        archive=p.locator('#tour-project-archive');archive.evaluate('e=>e.scrollTop=200')
        assert archive.is_visible();h.close(p);assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
        return {'viewport':[w,ht],'frame':box,'toolbar':bar,'parentDraws':0,'originalRendered':True,'returnMode':p.locator('main').get_attribute('data-reading-mode'),'before':before}
    sizes=[(1920,1080),(1440,900),(1366,768),(768,1024),(390,844),(375,812),(320,568),(844,390)]if args.engine=='chromium'else[(1440,900),(390,844)]
    for w,ht in sizes:h.check('layout '+str(w)+'x'+str(ht),lambda w=w,ht=ht:layout(w,ht))
    def rotation():
        c,p=h.setup(390,844);h.c2(p);h.open(p);f=h.ready(p)
        frames=[]
        for w,ht in [(844,390),(375,812),(390,844)]:
            old=f.evaluate('__audit.draws');p.set_viewport_size({'width':w,'height':ht});f.wait_for_function('v=>innerWidth===v',arg=w)
            f.wait_for_function('n=>__audit.draws>n+2000',arg=old,timeout=20000)
            assert h.draws(p,p,300)==0 and p.locator('iframe').count()==1;frames.append(p.locator('iframe').bounding_box())
        h.close(p);p.wait_for_function('document.querySelector("main").dataset.readingMode==="stable"')
        b=p.locator('article[data-experiment-station=C2]').bounding_box();assert b['y']<844 and b['y']+b['height']>0
        return {'realViewportResizes':3,'frames':frames,'physicalRotation':False,'restoredC2':b}
    h.check('layout continuous rotation and return',rotation)
    passed=h.finish()
raise SystemExit(0 if passed else 1)
