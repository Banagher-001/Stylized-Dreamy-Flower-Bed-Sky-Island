"""Early actual production shader compilation and full unaltered visual frames."""
import json
from playwright.sync_api import sync_playwright
from step5_common import *
build=json.loads((OUT/'build-verification.json').read_text());errors=[];shots=[]
with sync_playwright()as p:
    browser=launch(p);context=browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1)
    context.add_init_script(probe);page=context.new_page();watch(page,errors)
    for t,h,label in [(2,0,'O-02'),(18,0,'O-18'),(40,0,'O-40'),(2,2.54,'A2'),(2,11.5,'W')]:
        load(page,f'http://127.0.0.1:4179/?waterTime={t}');visit(page,h)
        for mode in ['pixel','native']:
            page.locator(f'.tour-actions [data-mode={mode}]').click();frames(page)
            name=f'trial-{build["candidateId"]}-{label}-{mode}.png';page.screenshot(path=str(OUT/name))
            shots.append({'file':name,'time':t,'H':h,'mode':mode,'bindings':json.loads(data(page)['cloudShadows'])})
    assert not errors,errors
    save(OUT,'smoke-'+build['candidateId']+'.json',{'passed':True,'candidateId':build['candidateId'],'screenshots':shots,'errors':errors})
    context.close();browser.close()
print('PASS actual shaders, 10 full visual frames',flush=True)
