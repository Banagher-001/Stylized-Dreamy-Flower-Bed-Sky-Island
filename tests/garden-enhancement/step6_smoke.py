"""Actual production visual compilation and initial projected bird state."""
import json
from playwright.sync_api import sync_playwright
from step6_common import *
build=json.loads((OUT/'build-verification.json').read_text());errors=[];shots=[];states=[]
with sync_playwright()as p:
    browser=launch(p);context=browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1)
    context.add_init_script(probe);page=context.new_page();watch(page,errors)
    for t,h,label in [(2,0,'O-02'),(8,0,'O-08'),(18,0,'O-18'),(28,0,'O-28'),(18,2.54,'A2'),(18,11.5,'W')]:
        load(page,f'http://127.0.0.1:4181/?waterTime={t}');visit(page,h)
        for mode in ['pixel','native']:
            page.locator(f'.tour-actions [data-mode={mode}]').click();frames(page)
            name=f'trial-{build["candidateId"]}-{label}-{mode}.png';page.screenshot(path=str(OUT/name));shots.append(name)
        load(page,f'http://127.0.0.1:4181/?waterTime={t}&debug=1');visit(page,h)
        state=json.loads(data(page)['birdState']);states.append({'time':t,'H':h,'state':state})
        print(label,'visible',state['visible'],'screens',[(round(r['screen']['x']),round(r['screen']['y']),round(r['screen']['alpha'],2))for r in state['poses']],flush=True)
    assert not errors,errors
    save(OUT,'smoke-'+build['candidateId']+'.json',{'passed':True,'candidateId':build['candidateId'],'fullNormalPageScreenshots':shots,'debugProjectionStates':states,'errors':errors})
    context.close();browser.close()
print('PASS actual bird shaders and12normal visual frames',flush=True)
