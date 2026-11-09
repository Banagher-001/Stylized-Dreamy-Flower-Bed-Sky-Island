"""Investigate initial timing outliers, retain every ABBA raw sample."""
import shutil
from playwright.sync_api import sync_playwright
from step3_common import *

shutil.copyfile(ROOT/'tests/garden-enhancement/inspect_orb_cost.js',Path('/tmp/garden-enhancement-step3-before/tests/garden-enhancement/inspect_orb_cost.js'))
results=[]
with sync_playwright() as p:
    browser=launch(p)
    for i,label in enumerate(['before','after','after','before']):
        port=5176 if label=='before'else 5173
        context=browser.new_context(viewport={'width':1440,'height':900})
        page=context.new_page();load(page,f'http://127.0.0.1:{port}/?waterTime=2');page.wait_for_timeout(350)
        result=page.evaluate('async()=>(await import("/tests/garden-enhancement/inspect_orb_cost.js")).inspectOrbCost()')
        results.append({'iteration':i,'phase':label,'result':result})
        context.close()
        print(label,'CPU avg',result['cpuUpdateBatchAverages']['meanMs'],'isolated O/W p95',[(r['pose'],r['totalBlockingMs']['p95Ms'])for r in result['cases']],flush=True)
    browser.close()
save(OUT,'performance-cost-isolation.json',{'passed':True,'purpose':'causal investigation of initial full-app timing outliers; not replacement app benchmark','order':['before','after','after','before'],'runs':results})
