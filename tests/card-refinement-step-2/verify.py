"""Real-clock entrance visibility, handoff and interruption checks."""
from pathlib import Path
import json,sys,shutil,math
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests/about-refresh-final'))
from support import Run,save
r=Run();shutil.copyfile(__file__,r.out/'verify.py.txt')
SAMPLER=r'''()=>{const rows=[];let active=true,frame;const rect=e=>{if(!e)return null;const r=e.getBoundingClientRect();return{x:r.x,y:r.y,left:r.left,right:r.right,top:r.top,bottom:r.bottom,width:r.width,height:r.height}};function take(){if(!active)return;const root=document.querySelector('.ar-tools-browser'),rail=root?.querySelector('.ar-tool-rail');if(root&&rows.length<500){rows.push({at:performance.now(),data:{...root.dataset},rail:rect(rail),controls:rect(root.querySelector('.ar-tool-controls')),cardCount:root.querySelectorAll('.ar-tool-card').length,instances:[...root.querySelectorAll('.ar-tool-card')].map(e=>e.dataset.cardInstance),faces:['midjourney','comfyui','kling','blender'].map(id=>{const e=root.querySelector('[data-tool-id="'+id+'"]');return{id,front:rect(e?.querySelector('.ar-card-front')),back:rect(e?.querySelector('.ar-card-back')),yaw:parseFloat(e?.style.getPropertyValue('--ar-card-yaw')||'0'),z:parseFloat(e?.style.getPropertyValue('--ar-card-z')||'0'),inert:e?.inert}})});}frame=requestAnimationFrame(take)}take();window.__entryReadOnly={rows,stop(){active=false;cancelAnimationFrame(frame)}}}'''

def initial(page,debug=False):
    if debug:
        page.goto(r.origin+'?debug=1',wait_until='domcontentloaded')
        page.wait_for_function('document.querySelector("main")?.dataset.layoutReady==="true"&&document.querySelector("#tour-host")?.dataset.renderState==="ready"',timeout=90000)
    page.evaluate(SAMPLER)
def frames(page,label):
    rows=page.evaluate('()=>{window.__entryReadOnly.stop();return window.__entryReadOnly.rows}')
    save(r.out/(label+'-frames.json'),rows);return rows

def complete(page):
    initial(page)
    try:
        r.go(page,'A3')
        page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceReason==="completed"',timeout=20000)
        page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.trackState==="running"')
        page.wait_for_timeout(1500)
    finally:rows=frames(page,'complete')
    live=[s for s in rows if s['data']['entrance']=='playing'];assert len(live)>=8
    assert all(s['cardCount']==22 and len(set(s['instances']))==22 for s in rows)
    identities=set(live[0]['instances']);assert all(set(s['instances'])==identities for s in live)
    data=r.state(page)['tools'];assert data['entrancePlays']=='1' and data['entranceAttempts']=='1' and data['entranceProgress']=='1'
    assert 2300<=float(data['entranceObservedDuration'])<=2800,data
    assert float(data['entranceHandoffError'])<=1.5,data
    assert data['entranceFramePending']=='false' and data['entranceHoldPending']=='false'
    reading=[s for s in live if s['data'].get('entranceSubphase')=='reading'];assert reading and all(s['data']['entranceFramePending']=='false' for s in reading)
    assert any(json.loads(s['data']['entranceWindow'])['right']-json.loads(s['data']['entranceWindow'])['left']>s['rail']['width']+400 for s in live)
    travel=[]
    for identifier in ['midjourney','comfyui','kling','blender']:
        visible=[];backs=[]
        for s in live:
            w=json.loads(s['data']['entranceWindow']);f=next(f for f in s['faces'] if f['id']==identifier);face=f['back'] if abs(f['yaw'])>90 else f['front']
            area=max(0,min(w['right'],face['right'])-max(w['left'],face['left']))*max(0,min(w['bottom'],face['bottom'])-max(w['top'],face['top']))
            if area>=2500:
                visible.append((s['at'],face['x']+face['width']/2))
                if abs(f['yaw'])>90:backs.append(s['at'])
        assert len(visible)>=3,(identifier,len(visible))
        span=max(x[1] for x in visible)-min(x[1] for x in visible)
        assert span>=140,(identifier,span)
        travel.append({'id':identifier,'visibleSamples':len(visible),'visibleWallMs':visible[-1][0]-visible[0][0],'visibleHorizontalSpan':span,'backVisibleSamples':len(backs)})
    assert any(x['backVisibleSamples'] for x in travel)
    r.checkpoint(page,'resting')
    r.go(page,'B1');r.go(page,'A3');page.wait_for_timeout(400)
    assert r.state(page)['tools']['entranceAttempts']=='1'
    assert not page.locator('.ar-flight-stage,.ar-entry-sigil').count()
    return {'duration':data['entranceObservedDuration'],'handoffError':data['entranceHandoffError'],'travel':travel,'readingSamples':len(reading),'identityCount':len(identities),'autoplayAfterSinglePause':True,'returnDidNotReplay':True,'frames':'complete-frames.json'}

def cleanup(page):
    page.wait_for_function('!document.querySelector(".ar-flight-stage")&&document.querySelector(".ar-tools-browser").dataset.entranceFramePending==="false"&&document.querySelector(".ar-tools-browser").dataset.entranceHoldPending==="false"')
    assert page.locator('.ar-tools-browser .ar-tool-card').count()==22
    assert not page.locator('[data-entry-card],.ar-entry-sigil').count()
    return r.state(page)
def flying(page):
    initial(page);r.go(page,'A3')
    page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceSubphase==="flying"')

def category(page):
    flying(page);page.locator('button[data-category=G6]').click()
    page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.category==="G6"')
    page.wait_for_timeout(500)
    assert page.locator('.ar-tools-browser .ar-tool-card').count()==5
    assert not page.locator('.ar-flight-stage,[data-entry-card]').count()
    assert r.state(page)['tools']['entranceFramePending']=='false'
    page.wait_for_timeout(2000);assert page.locator('.ar-tools-browser .ar-tool-card').count()==5
    return r.state(page)
def pause(page):
    flying(page);page.locator('[data-action=auto]').click()
    end=cleanup(page);assert end['tools']['trackEnabled']=='false'
    page.wait_for_timeout(650);assert r.state(page)['tools']['trackEnabled']=='false'
    return end
def wheel(page):
    flying(page);box=page.locator('.ar-tool-rail').bounding_box()
    page.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2);page.mouse.wheel(0,45)
    end=cleanup(page);assert end['tools']['entrance']=='cancelled'
    return {'state':end,'newHorizontalWheelMappingNotClaimed':True}
def resized(page):
    flying(page);page.set_viewport_size({'width':390,'height':844});end=cleanup(page)
    assert end['overflow']<=1
    assert all(not c['expanded']=='true' for c in end['cards'])
    return end
def reduced(page):
    r.go(page,'A3');end=cleanup(page);assert end['tools']['entrancePlays']=='0'
    return end
def reduced_during(page):
    flying(page);page.emulate_media(reduced_motion='reduce');return cleanup(page)
def continued(page):
    flying(page);page.locator('[data-action=continue]').click()
    page.wait_for_function('Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-4.95)<.006')
    return cleanup(page)

def raw_go(page,h):
    delta=page.evaluate('h=>h/12.3*(document.documentElement.scrollHeight-innerHeight)-scrollY',h)
    page.mouse.move(24,300);page.mouse.wheel(0,delta)
def unseen_retry(page):
    initial(page);raw_go(page,3.34)
    page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entrance==="preparing"')
    page.locator('button[data-stop=films]').click()
    page.wait_for_function('Math.abs(Number(document.querySelector("#tour-host").dataset.displayH)-4.95)<.006')
    before=r.state(page)['tools'];assert before['entrancePlays']=='0' and before['entrance']=='waiting',before
    r.go(page,'A3');page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceReason==="completed"')
    after=r.state(page)['tools'];assert after['entrancePlays']=='1'
    return {'unseenDeparture':before,'retryCompleted':after}
def font_changed(page):
    flying(page);page.evaluate('document.documentElement.style.fontSize="200%"')
    end=cleanup(page);page.wait_for_timeout(650)
    assert r.state(page)['overflow']<=1
    assert page.locator('.ar-tool-card').evaluate_all('es=>es.every(e=>!e.style.width&&!e.style.height)')
    return {'fontSizeSimulation':'200%','state':end}
def resource_fallback(page):
    # Explicit readiness fault; no network, clock or RAF overrides.
    page.evaluate('Object.defineProperty(document.fonts,"status",{configurable:true,get:()=>"loading"})')
    try:
        r.go(page,'A3')
        page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceReason==="resource-fallback"')
        end=cleanup(page);assert end['tools']['entrancePlays']=='0'
    finally:page.evaluate('delete document.fonts.status')
    assert page.locator('.ar-tool-card').first.inner_text()
    return {'faultInjection':'Font readiness held at loading; original getter restored','state':end}
def region_invariant(page):
    initial(page,True);raw_go(page,3.34)
    page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entrance==="preparing"&&JSON.parse(document.querySelector(".ar-card-region-debug").dataset.snapshot).active')
    read=lambda:page.locator('.ar-card-region-debug').evaluate('e=>JSON.parse(e.dataset.snapshot)')
    before=read()
    page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceSubphase==="flying"')
    page.wait_for_timeout(250);during=read()
    page.wait_for_function('document.querySelector(".ar-tools-browser").dataset.entranceReason==="completed"')
    page.wait_for_timeout(80);after=read()
    for x in [during,after]:
        assert x['contentWidth']==before['contentWidth']
        assert all(abs(x['bounds'][key]-before['bounds'][key])<=1 for key in ['left','top','width','height'])
    return {'before':before,'during':during,'after':after}
def all_tools(page):
    flying(page);page.locator('[data-action=all]').click()
    page.wait_for_function('document.querySelector(".ar-overview-dialog").open')
    assert page.locator('.ar-catalog .ar-tool-card').count()==22
    assert not page.locator('.ar-flight-stage,[data-entry-card]').count()
    page.keyboard.press('Escape');page.wait_for_function('!document.querySelector(".ar-overview-dialog").open')
    return cleanup(page)
try:
    r.case('visible-four-card-entrance',complete,size=(1652,949),video=True)
    r.case('unseen-fast-pass-can-retry',unseen_retry,size=(1652,949))
    r.case('font-change-cleans-flight',font_changed,size=(1652,949))
    r.case('font-readiness-fallback',resource_fallback,size=(1652,949))
    r.case('step1-region-does-not-follow-flight',region_invariant,size=(1652,949))
    r.case('all-tools-interrupt-first-click',all_tools,size=(1652,949))
    r.case('category-interrupt-first-click',category,size=(1652,949))
    r.case('pause-interrupt-retains-choice',pause,size=(1652,949))
    r.case('wheel-only-shortens-entrance',wheel,size=(1652,949))
    r.case('resize-cleans-flight',resized,size=(1652,949))
    r.case('initial-reduced-motion',reduced,reduced=True)
    r.case('reduced-during-flight',reduced_during,size=(1652,949))
    r.case('continue-interrupt-first-click',continued,size=(1652,949))
finally:good=r.finish()
raise SystemExit(0 if good else 1)
