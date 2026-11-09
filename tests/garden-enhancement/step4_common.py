"""Independent Step4 outputs; no earlier test or evidence file is changed."""
from pathlib import Path
from step3_common import launch,load,visit,frames,data,save,watch,decode,pure_canvas,equal,still,playing,pause,probe,STOPS,VIEWS

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/evidence/garden-enhancement-step-4'

def guide_data(page):
    return {k:v for k,v in data(page).items()if k.startswith('guide')or k in ['displayH','targetH','cameraState','sceneTime','motionState']}

def guide_stop(page):
    if page.locator('#tour-guide').get_attribute('aria-pressed')=='true':
        page.locator('#tour-guide').click()
    frames(page)

def guide_start(page,h=None,reading=True):
    guide_stop(page)
    if h is not None:visit(page,h)
    page.wait_for_function('document.querySelector("#tour-guide").getAttribute("aria-disabled")==="false"')
    page.locator('#tour-guide').click()
    page.wait_for_function('document.querySelector("#tour-guide").getAttribute("aria-pressed")==="true"')
    if reading:page.wait_for_function('document.querySelector("#tour-host").dataset.guidePhase==="reading"')
    return guide_data(page)

def manual_stays(page,milliseconds=450):
    page.wait_for_function('document.querySelector("#tour-guide").getAttribute("aria-pressed")==="false"')
    # Native PageDown/Home/End and touch inertia may continue after takeover.
    # Wait for that real input to finish; never suppress it to satisfy a test.
    page.wait_for_timeout(350)
    page.wait_for_function('performance.now()-window.__tourProbe.lastScroll>220')
    page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"')
    frames(page)
    before=page.evaluate('scrollY');h=data(page)['displayH'];page.wait_for_timeout(milliseconds)
    assert abs(page.evaluate('scrollY')-before)<=1
    assert abs(float(data(page)['displayH'])-float(h))<.000001
    return {'scrollY':before,'H':h,'noAutomaticWritesWindowMs':milliseconds,'guide':guide_data(page)}
