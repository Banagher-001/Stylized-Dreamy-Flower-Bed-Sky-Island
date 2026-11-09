"""Real deformed triangles, exact birth/impact physics, fields and world digests.

Requires current Vite on 5173 and independent extracted Step2 Vite on 5176.
The same contract inspector is copied into the extracted baseline, not the repo's
historical archive. Every JSON goes only into the new Step3 evidence directory.
"""
import shutil
from playwright.sync_api import sync_playwright
from step3_common import *

baseline = Path('/tmp/garden-enhancement-step3-before')
shutil.copyfile(ROOT / 'tests/garden-enhancement/inspect_world_contract.js', baseline / 'tests/garden-enhancement/inspect_world_contract.js')
with sync_playwright() as p:
    browser = launch(p)
    page = browser.new_page(viewport={'width':1440,'height':900})
    load(page,'http://127.0.0.1:5173/?waterTime=2')
    aspects=[]
    for w,h in [(1440,900),(1366,768),(390,844)]:
        page.set_viewport_size({'width':w,'height':h})
        visit(page,0)
        aspects.append({'viewport':[w,h],'aspect':float(data(page)['aspect']),'sampleWidth':float(page.locator('canvas').get_attribute('data-sample-width'))})
    result=page.evaluate('async a=>(await import("/tests/garden-enhancement/inspect_orb_flow.js")).inspectOrbFlow(a)',aspects)
    save(OUT,'geometry-physics.json',dict(result,browser=browser.version))
    print('PASS geometry:',result['geometrySamples'],'shape samples;',result['birthCases'],'births;',result['flightSamples'],'flight points',flush=True)
    result=page.evaluate('async()=>{const m=await import("/tests/garden-enhancement/inspect_flow_field.js");return {field:m.inspectFlowField(),highlights:m.inspectFlowHighlights()}}')
    save(OUT,'surface-field-highlights.json',result)
    print('PASS field:',result['field']['directionSamples'],'directions;',result['field']['seamAndPoleChecks'],'seam/pole checks',flush=True)
    contracts,projections={},{}
    page.set_viewport_size({'width':1440,'height':900})
    for label,port in [('before',5176),('after',5173)]:
        load(page,f'http://127.0.0.1:{port}/?waterTime=2')
        contracts[label]=page.evaluate('async()=>(await import("/tests/garden-enhancement/inspect_world_contract.js")).inspectWorldContract()')
        projections[label]=[]
        for at in aspects:
            for key in ['O','W']:
                for time in [2,4,6]:
                    value=page.evaluate('async a=>(await import("/tests/garden-enhancement/inspect_world_contract.js")).projectOrb(a.aspect,a.sampleWidth,a.key,a.time)',dict(at,key=key,time=time))
                    projections[label].append(dict(at,pose=key,time=time,bounds=value))
    assert contracts['before']['protectedSha256']==contracts['after']['protectedSha256']
    assert contracts['before']['routeSha256']==contracts['after']['routeSha256']
    assert contracts['before']['fountainRootMatrix']==contracts['after']['fountainRootMatrix']
    save(OUT,'world-protection.json',{'passed':True,'beforeIdentity':'Step2 independent 101-member source/site archive','allowedExclusion':'the three fountain-effects meshes only; root transform verified separately, pool/water/architecture/vegetation included','contracts':contracts,'matchedOrbProjections':projections})
    print('PASS world:',contracts['after']['protectedObjectCount'],'exact protected objects; route and fountain transform exact',flush=True)
    browser.close()
