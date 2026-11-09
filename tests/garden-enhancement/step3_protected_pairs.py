"""Fresh identical legacy and About-alpha comparisons with actual production pages.
Full courtyard equality is deliberately NOT required: orb, stem, drops and true
impact ripples are approved differences, protected world data is checked separately.
"""
from playwright.sync_api import sync_playwright
from step3_common import *
from step2_common import background_measurement, about

rows,errors=[],[]
with sync_playwright() as p:
    browser=launch(p)
    context=browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1)
    page=context.new_page()
    watch(page,errors)
    for kind,query,host in [('original-reference','tour=reference','#scene-host'),('historical-orb-query','orb=legacy','#tour-host')]:
        for mode in ['pixel','native']:
            images=[]
            for label,port in [('before',4176),('after',4177)]:
                page.goto(f'http://127.0.0.1:{port}/?{query}&waterTime=2&render={mode}',wait_until='networkidle')
                page.wait_for_selector(host+'[data-render-state=ready]')
                decode(page);page.mouse.move(10,450);frames(page)
                raw=page.screenshot();images.append(raw)
                (OUT/f'protected-{kind}-{mode}-{label}.png').write_bytes(raw)
            assert equal(*images),(kind,mode)
            rows.append({'kind':kind,'mode':mode,'actualFullPageExact':True,'method':'entire actual viewport, no masks/crops/tolerance'})
    context.close()
    alphas=[]
    for w,h,dpr in [(1440,900,1),(390,844,2)]:
        context=browser.new_context(viewport={'width':w,'height':h},device_scale_factor=dpr)
        page=context.new_page();watch(page,errors)
        for mode in ['pixel','native']:
            measurements=[]
            for label,port in [('before',4176),('after',4177)]:
                load(page,f'http://127.0.0.1:{port}/?waterTime=2&render={mode}');visit(page,2.54)
                filename=f'protected-About-{w}-{mode}-{label}-alpha.png'
                result=background_measurement(page,OUT,filename,check=True)
                measurements.append({'file':filename,'measurement':result,'about':about(page)})
            assert equal(*( (OUT/m['file']).read_bytes() for m in measurements))
            assert measurements[0]['about']==measurements[1]['about']
            alphas.append({'viewport':[w,h],'DPR':dpr,'mode':mode,'actualRgbaBackgroundExact':True,'measurements':measurements})
        context.close()
    assert not errors,errors
    save(OUT,'protected-raster-pairs.json',{'passed':True,'browser':browser.version,'legacyPairs':rows,'aboutPairs':alphas,'exceptions':errors,
        'baseline':'actual extracted Step2 production snapshot at 4176; orb=legacy is historical legacy only, NOT the Step2 lively before-orb'})
    print('PASS 4 full unmasked legacy/reference pages and 4 exact actual About background pairs',flush=True)
    browser.close()
