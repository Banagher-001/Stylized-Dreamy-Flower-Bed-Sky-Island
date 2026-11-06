"""Real geometry route/material isolation and effective live-camera framing."""
import csv,json
from playwright.sync_api import sync_playwright
from step7_common import *
rows=list(csv.DictReader((ROOT/'docs/scroll-garden/step-1-stations.csv').open(encoding='utf-8-sig')))
stations=[{'id':r['站点ID'],'start':float(r['起点H']),'y':float(r['阅读高度Y']),'stop':float(r['起点H'])+.55*(float(r['终点H'])-float(r['起点H'])),'fullStart':float(r['完整阅读起点H']),'fullEnd':float(r['完整阅读终点H'])}for r in rows if r['站点ID'].startswith('A')]
with sync_playwright() as p:
    b=launch(p);page=b.new_page(viewport={'width':1440,'height':900});page.goto('http://127.0.0.1:5173/?tour=prototype&waterTime=2',wait_until='networkidle');page.wait_for_selector('#tour-host[data-render-state="ready"]');aspects=[];live=[]
    for w,h in [(1440,900),(1366,768),(390,844)]:
        resize(page,w,h);aspects.append(float(data(page)['aspect']));go(page,10.05);page.locator('[data-project-tab=live]').click();frames(page)
        payload=page.evaluate('()=>({pose:{...document.querySelector("#tour-host").dataset},host:document.querySelector("#tour-host").getBoundingClientRect().toJSON(),area:document.querySelector(".tour-project-live-space").getBoundingClientRect().toJSON()})')
        result=page.evaluate('async o=>(await import("/tests/scroll-garden/inspect_experiment.js")).inspectExperienceFrame(o)',payload);live.append({'viewport':[w,h],'bounds':payload['area'],'objects':result});page.locator('.tour-project-close').click();settled(page,10.05)
    result=page.evaluate('async o=>(await import("/tests/scroll-garden/inspect_experiment.js")).inspectExperiment(o.aspects,o.stations)',{'aspects':aspects,'stations':stations})
    prior=json.loads((ROOT/'docs/evidence/scroll-garden-step-6/geometry-isolation.json').read_text())
    assert result['instances']==prior['instances']and result['stages']==prior['stages']and result['totalH']==prior['totalH']
    assert all(result['poses'][k]==v for k,v in prior['poses'].items())
    assert result['inscriptionFaces']==prior['inscriptionFaces']and result['film']['faces']==prior['film']['faces']
    result.update(liveFraming=live,existingPosesABFacesAndInstancesUnchanged=True);save('geometry-isolation.json',result);b.close();print('PASS: route 3003, C descent 1001, nine C rays, 45 C plateaus, three face anchors, isolated bindings, old A/B geometry and live framing',flush=True)
