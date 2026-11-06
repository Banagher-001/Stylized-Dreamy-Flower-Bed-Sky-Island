"""Warm all three pillars in both modes; verify actual GPU and dust-pool budgets."""
from playwright.sync_api import sync_playwright
from step7_common import *

NO_2D="""(()=>{const original=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(kind,...args){return kind==='2d'?null:original.call(this,kind,...args);};})()"""
ROUTE=[0,1.74,2.54,3.34,4.95,5.95,6.84,7.64,9.14,10.05,10.83,11.5,0,10.05]
FRAME_KEYS=['magicFrame','filmMagicFrame','experimentMagicFrame']
RESOURCE_KEYS=['magicResources','filmMagicResources','experimentMagicResources']
before=json.loads((OUT/'baseline-before.json').read_text())['warmCaches']
results={};pool_receipts=[]
with sync_playwright() as p:
    browser=launch(p)
    for disabled in [False,True]:
        context=browser.new_context(viewport={'width':1440,'height':900})
        if disabled:context.add_init_script(NO_2D)
        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto('http://127.0.0.1:4173/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]');rows=[]
        for mode in ['pixel','native','pixel']:
            page.locator(f'.tour-actions [data-mode={mode}]').click()
            for h in ROUTE:go(page,h)
            frames(page);rows.append(json.loads(data(page)['rendererStats']))
        assert not errors,errors
        if disabled:
            assert all(data(page)[key]=='fallback' for key in ['magicStatus','filmMagicStatus','experimentMagicStatus'])
        else:
            for at in [1.74,4.95,10.05]:
                go(page,at);d=data(page);pool=[json.loads(d[k])for k in RESOURCE_KEYS];states=[json.loads(d[k])for k in FRAME_KEYS]
                assert sum(x['pool'] for x in pool)==72
                assert sum(x['dustVisible'] for x in states)==8 and sum(x['glyph']>.000001 for x in states)==1
                assert all(x['dustVisible']<=24 and x['dustCapacity']<=24 for x in states)
                pool_receipts.append({'viewport':[1440,900],'h':at,'allocatedSlots':72,'states':states})
            go(page,9.7);states=[json.loads(data(page)[k])for k in FRAME_KEYS]
            assert sum(x['dustVisible']for x in states)<=24 and sum(x['glyph']>.000001 for x in states)==1
            pool_receipts.append({'viewport':[1440,900],'h':9.7,'burst':True,'states':states})
        results['decorationUnavailable'if disabled else'normal']={'warmCaches':rows,'unhandledExceptions':errors};context.close()
    for reduced in [False,True]:
        context=browser.new_context(viewport={'width':390,'height':844},device_scale_factor=2,has_touch=True,is_mobile=True,reduced_motion='reduce'if reduced else'no-preference')
        page=context.new_page();page.goto('http://127.0.0.1:4173/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]')
        for at in [1.74,4.95,10.05]:
            go(page,at);d=data(page);pool=[json.loads(d[k])for k in RESOURCE_KEYS];states=[json.loads(d[k])for k in FRAME_KEYS]
            assert sum(x['pool']for x in pool)==36
            assert sum(x['dustVisible']for x in states)==(0 if reduced else 4)
            assert all(x['dustVisible']<=12 and x['dustCapacity']<=12 for x in states)
            pool_receipts.append({'viewport':[390,844],'reducedMotion':reduced,'h':at,'allocatedSlots':36,'states':states})
        context.close()
    browser.close()

normal=results['normal']['warmCaches'];deltas=[]
for index,(prior,current)in enumerate(zip(before,normal)):
    delta={k:current[k]-prior[k]for k in ['geometries','textures','programs']}
    assert delta['geometries']<=2 and delta['textures']<=1 and delta['programs']<=(1 if index==0 else 2),(index,prior,current,delta)
    deltas.append(delta)
assert normal[1]['programs']==normal[2]['programs']
assert all(normal[i]['geometries']==normal[0]['geometries']and normal[i]['textures']==normal[0]['textures'] for i in [1,2])
save('resource-caches.json',{'passed':True,'method':'same pixel/native/pixel history and complete A/B/C plus water/overview route in every mode; Chromium software graphics; actual renderer.info caches, no FPS inference','routeH':ROUTE,'freshStep6Baseline':before,'frames':results,'deltaNormal':deltas,'dustPools':pool_receipts})
print('PASS normal caches',[(x['geometries'],x['textures'],x['programs'])for x in normal],flush=True)
print('PASS no-decoration caches',[(x['geometries'],x['textures'],x['programs'])for x in results['decorationUnavailable']['warmCaches']],flush=True)
print('PASS actual three dust pools: desktop72/mobile36 allocated; one active, steady8/4, reduced0',flush=True)
