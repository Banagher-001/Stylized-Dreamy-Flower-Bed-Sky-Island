"""Unchanged world/camera pixels and About alpha; UI guide addition is intentional.
No full-pool mask or tolerance; paused entire GPU canvas is compared exactly.
"""
import json
from playwright.sync_api import sync_playwright
from step4_common import *
from step2_common import background_measurement,about

paired,backgrounds,references,errors=[],[],[],[]
with sync_playwright()as p:
    browser=launch(p)
    for w,h,dpr in [(1440,900,1),(1366,768,1),(390,844,2)]:
        context=browser.new_context(viewport={'width':w,'height':h},device_scale_factor=dpr)
        old,new=context.new_page(),context.new_page()
        for page,port in [(old,4176),(new,4177)]:watch(page,errors);load(page,f'http://127.0.0.1:{port}/?waterTime=2')
        for mode in ['pixel','native']:
            for page in [old,new]:page.bring_to_front();page.locator(f'.tour-actions [data-mode={mode}]').click();frames(page)
            for key,at in [('O',0),('A2',2.54),('W',11.5)]:
                images=[]
                for page in [old,new]:visit(page,at);images.append(pure_canvas(page))
                if not equal(*images):
                    for raw,label in zip(images,['before','after']):(OUT/f'protection-failure-{w}-{mode}-{key}-{label}.png').write_bytes(raw)
                    raise AssertionError(('whole GPU canvas differs',w,mode,key,data(old),data(new)))
                paired.append({'viewport':[w,h],'DPR':dpr,'mode':mode,'pose':key,'fullGpuCanvasExact':True})
                if key=='W'and(w==1440 or w==390):
                    for page,label in [(old,'before'),(new,'after')]:visit(page,at);page.mouse.move(10,h/2);page.screenshot(path=str(OUT/f'world-{w}-{mode}-W-{label}.png'))
            if w in [1440,390]:
                samples=[]
                for page,label in [(old,'before'),(new,'after')]:
                    visit(page,2.54);name=f'about-alpha-{w}-{mode}-{label}.png';samples.append({'file':name,'measurement':background_measurement(page,OUT,name,check=True),'actual':about(page)})
                assert samples[0]['actual']==samples[1]['actual']and equal(*( (OUT/s['file']).read_bytes()for s in samples))
                backgrounds.append({'viewport':[w,h],'mode':mode,'RGBAExact':True,'samples':samples})
        context.close()
    context=browser.new_context(viewport={'width':1440,'height':900})
    for mode in ['pixel','native']:
        images=[]
        for label,port in [('before',4176),('after',4177)]:
            page=context.new_page();watch(page,errors);page.goto(f'http://127.0.0.1:{port}/?tour=reference&waterTime=2&render={mode}',wait_until='networkidle');page.wait_for_selector('#scene-host[data-render-state=ready]');decode(page);page.mouse.move(10,450);frames(page);raw=page.screenshot();images.append(raw);(OUT/f'reference-{mode}-{label}.png').write_bytes(raw);page.close()
        assert equal(*images);references.append({'mode':mode,'wholeActualPageExact':True})
    context.close();assert not errors,errors
    save(OUT,'scene-and-background-protection.json',{'passed':True,'candidateId':json.loads((OUT/'build-verification.json').read_text())['candidateId'],'browser':browser.version,'wholeGpuCanvasPairs':paired,'AboutActualAlphaPairs':backgrounds,'referenceWholePages':references,'method':'same native scroll/camera/time/mode/DPR; only DOM hidden equally for whole GPU canvas isolation, all GPU content retained; no pixel masks/crops/tolerance; actual full pages kept separately','errors':errors})
    print('PASS',len(paired),'entire GPU pairs,',len(backgrounds),'actual About alpha pairs,2full reference pages',flush=True);browser.close()
