"""Actual production-page terminal hold, explicit replay and native takeover.
The initial near-ending position is test setup, not claimed as trusted input.
No product clock overrides, shortened deadlines or synthetic visibility events.
"""
import json
from playwright.sync_api import sync_playwright
from step4_common import *

build=json.loads((OUT/'build-verification.json').read_text())
errors=[];checks=[]
with sync_playwright()as p:
    browser=launch(p)
    context=browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1)
    context.add_init_script(probe)
    page=context.new_page();watch(page,errors)
    load(page,'http://127.0.0.1:4177/?waterTime=2')
    guide_start(page,12.28)
    start=guide_data(page)
    assert start['guideStation']=='S99' and float(start['guideReadSeconds'])>=6
    page.wait_for_function('document.querySelector("#tour-host").dataset.guidePhase==="finished"')
    ended=guide_data(page)
    actual_end=page.evaluate('performance.now()')
    assert actual_end>=float(start['guideDeadline'])
    assert page.locator('#tour-guide').inner_text()=='重新导览'
    page.wait_for_timeout(1100)
    assert guide_data(page)['guidePhase']=='finished'
    assert abs(float(data(page)['displayH'])-12.3)<.003
    checks.append({'name':'actual final six-second hold and no loop','start':start,'end':ended,'observedEndAt':actual_end,'noLoopWindowMs':1100})
    page.screenshot(path=str(OUT/'replay-terminal-before.png'))
    t=data(page)['sceneTime']
    page.locator('#tour-guide').click()
    page.wait_for_function('document.querySelector("#tour-guide").getAttribute("aria-pressed")==="true"')
    replay=guide_data(page)
    assert replay['guideStation']=='O' and page.evaluate('scrollY')<=1
    assert data(page)['sceneTime']==t
    page.mouse.move(1100,350);page.mouse.wheel(0,160)
    handed=manual_stays(page,1000)
    assert handed['scrollY']>20
    page.screenshot(path=str(OUT/'replay-native-wheel-takeover.png'))
    checks.append({'name':'explicit replay uses original overview, native wheel interrupts return without rebound','replay':replay,'takeover':handed,'environmentTimeBefore':t,'environmentTimeAfter':data(page)['sceneTime']})
    assert not errors,errors
    save(OUT,'replay-native-takeover.json',{'passed':True,'candidateId':build['candidateId'],'browser':browser.version,'checks':checks,'errors':errors,
        'method':'real production controller/deadlines; near-ending native scroll position is test setup; actual button and native wheel provide replay/takeover proof; no accelerated time','physicalDevice':False})
    context.close();browser.close()
print('PASS actual terminal hold, explicit replay and native wheel takeover',flush=True)
