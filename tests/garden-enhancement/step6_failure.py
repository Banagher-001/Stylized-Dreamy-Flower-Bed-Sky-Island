"""Cloud-enabled real unavailable-WebGL fallback and CSS font pressure."""
import json
from playwright.sync_api import sync_playwright
from step6_common import *
build=json.loads((OUT/'build-verification.json').read_text());checks=[]
with sync_playwright()as p:
    browser=launch(p,extra=['--disable-webgl']);page=browser.new_page(viewport={'width':390,'height':844})
    exceptions=[];page.on('pageerror',lambda e:exceptions.append(str(e)))
    page.goto('http://127.0.0.1:4181/?waterTime=2',wait_until='networkidle')
    page.wait_for_function('document.querySelector("main").dataset.readingMode==="stable"')
    assert page.locator('.tour-reading-flow article[aria-hidden=false]').count()==10 and data(page)['guideState']=='blocked'
    assert page.locator('#tour-reference').is_visible()and not exceptions
    page.screenshot(path=str(OUT/'no-webgl-cloud-reading.png'))
    checks.append({'name':'actual --disable-webgl with clouds enabled retains ten articles and reference','guide':guide_data(page),'exceptions':exceptions});browser.close()
    browser=launch(p);context=browser.new_context(viewport={'width':320,'height':568},device_scale_factor=3)
    context.add_init_script(probe);page=context.new_page();load(page,'http://127.0.0.1:4181/?waterTime=2')
    page.evaluate('document.documentElement.style.fontSize="32px"');page.wait_for_timeout(450);frames(page)
    assert page.locator('main').get_attribute('data-reading-mode')=='stable'and data(page)['guideState']=='blocked'
    rows=page.locator('.tour-reading-flow article').evaluate_all('es=>es.map(e=>({id:e.dataset.flowAnchor,hidden:e.hidden,aria:e.getAttribute("aria-hidden"),overflowX:e.scrollWidth-e.clientWidth,overflowY:e.scrollHeight-e.clientHeight}))')
    assert len(rows)==10 and all(not r['hidden']and r['aria']=='false'and r['overflowX']<=1 and r['overflowY']<=1 for r in rows)
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    page.screenshot(path=str(OUT/'clouds-320-200percent-css-font.png'))
    checks.append({'name':'320px, DPR3, CSS root-font200percent; not OS zoom','articles':rows,'quiet':still(page)})
    context.close();browser.close()
save(OUT,'failure-and-font.json',{'passed':True,'candidateId':build['candidateId'],'checks':checks,'physicalDevice':False})
print('PASS actual no-WebGL reading and CSS font pressure',flush=True)
