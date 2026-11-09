"""Actual local video404, visible retry, decoder recovery and return ownership."""
import json
from playwright.sync_api import sync_playwright
from step7_common import *
build=json.loads((OUT/'build-verification.json').read_text());checks=[];exceptions=[];rejected=[]
with sync_playwright()as p:
    browser=launch(p);context=browser.new_context(viewport={'width':1440,'height':900});context.add_init_script(probe)
    page=context.new_page();page.on('pageerror',lambda e:exceptions.append(str(e)));fault={'enabled':True}
    def video_route(route):
        if fault['enabled']:rejected.append(route.request.url);route.fulfill(status=404,content_type='video/mp4',body=b'')
        else:route.continue_()
    page.route('**/*.mp4',video_route)
    load(page,'http://127.0.0.1:4183/?waterTime=2&birds=inspect');guide_start(page,10.05);position=page.evaluate('scrollY');held=data(page)['sceneTime']
    page.locator('[data-project-tab=archive]').click();page.locator('.tour-project-play').click()
    page.wait_for_function('document.querySelector(".tour-project-dialog").dataset.mediaState==="error"')
    assert rejected and page.locator('.tour-project-media-retry').is_visible()
    page.screenshot(path=str(OUT/'actual-video404-retry.png'))
    checks.append({'name':'actual intercepted video404 exposes retry and retains project reading','passed':True,'rejectedRequests':rejected.copy(),'guide':guide_data(page)})
    fault['enabled']=False;page.locator('.tour-project-media-retry').click()
    page.wait_for_function('document.querySelector(".tour-project-dialog").dataset.mediaState==="ready"')
    page.locator('video').evaluate('v=>v.play()');page.wait_for_function('document.querySelector("video").currentTime>.15')
    decoded=page.locator('video').evaluate('v=>({duration:v.duration,width:v.videoWidth,height:v.videoHeight,currentTime:v.currentTime})')
    page.locator('.tour-project-close').click();frames(page)
    assert page.locator('video').count()==0 and abs(page.evaluate('scrollY')-position)<=1 and data(page)['sceneTime']==held
    assert page.locator('#tour-guide').get_attribute('aria-pressed')=='false'
    page.wait_for_function('document.querySelector("[data-project-tab=archive]")===document.activeElement')
    checks.append({'name':'original retry loads real decoded clip; close releases video and retains focus/position/paused time','passed':True,'decoded':decoded,'canvasCount':page.locator('canvas').count(),'nativePosition':position,'guide':guide_data(page)})
    assert not exceptions,exceptions
    save(OUT,'video-failure-recovery.json',{'passed':True,'candidateId':build['candidateId'],'checks':checks,'unhandledExceptions':exceptions,
        'method':'explicit real MP4 HTTP404 injection followed by original retry button; real decoder metadata and playback observed (video.play is test media API, not claimed trusted footage); native close/focus and paused original scene time checked','physicalDevice':False})
    context.close();browser.close()
print('PASS actual video failure/retry/decode and ownership return',flush=True)
