"""Matched ABBA recheck of ONLY four desktop cases flagged by initial timing.
Keep every sample, aggregate both before/both after runs; never pick a best run.
No screenshots, recording, other browser or production-code changes.
"""
import ast
from playwright.sync_api import sync_playwright
from step3_common import *

tree=ast.parse((ROOT/'tests/garden-enhancement/step3_performance.py').read_text())
raf_probe=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='raf_probe'for t in n.targets))
def stats(values):
    return {'count':len(values),'p50Ms':sorted(values)[int((len(values)-1)*.5)],'p95Ms':sorted(values)[int((len(values)-1)*.95)],'maxMs':max(values),'meanMs':sum(values)/len(values)}
runs=[]
with sync_playwright()as p:
    for iteration,phase in enumerate(['before','after','after','before']):
        browser=launch(p)
        context=browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1)
        context.add_init_script(probe);context.add_init_script(raf_probe)
        page=context.new_page();errors=[];watch(page,errors)
        load(page,f'http://127.0.0.1:{4176 if phase=="before"else 4177}/?waterTime=2')
        for mode in ['pixel','native','pixel']:
            page.locator(f'.tour-actions [data-mode={mode}]').click()
            for _,at in VIEWS:visit(page,at)
        cases=[]
        for mode,key,at in [('pixel','O',0),('pixel','W',11.5),('native','O',0),('native','W',11.5)]:
            pause(page);page.locator(f'.tour-actions [data-mode={mode}]').click();visit(page,at);playing(page)
            page.evaluate('window.__captureFrames=true;window.__frameSamples=[]')
            page.wait_for_function('window.__frameSamples.length>=24',timeout=60000)
            page.evaluate('window.__frameSamples=[]')
            page.wait_for_function('window.__frameSamples.length>=120',timeout=90000)
            raw=page.evaluate('window.__captureFrames=false;window.__frameSamples.slice(0,120)')
            pause(page)
            intervals=[b['timestamp']-a['timestamp']for a,b in zip(raw,raw[1:])]
            result={'mode':mode,'pose':key,'samples':raw,'intervalSamplesMs':intervals,'callback':stats([r['costMs']for r in raw]),'interval':stats(intervals),'stats':json.loads(data(page)['rendererStats'])}
            cases.append(result)
            print(iteration,phase,mode,key,'callback',result['callback']['p95Ms'],'interval',result['interval']['p95Ms'],flush=True)
        assert not errors,errors
        runs.append({'iteration':iteration,'phase':phase,'cases':cases,'errors':errors,'browser':browser.version})
        save(OUT,'performance-recheck-progress.json',{'complete':False,'runs':runs})
        context.close();browser.close()
rows=[]
for mode,key in [('pixel','O'),('pixel','W'),('native','O'),('native','W')]:
    grouped={}
    for phase in ['before','after']:
        selected=[case for run in runs if run['phase']==phase for case in run['cases']if case['mode']==mode and case['pose']==key]
        grouped[phase]={'callback':stats([r['costMs']for c in selected for r in c['samples']]),'interval':stats([v for c in selected for v in c['intervalSamplesMs']])}
    rows.append({'mode':mode,'pose':key,'groups':grouped,'callbackP95ChangePercent':100*(grouped['after']['callback']['p95Ms']/grouped['before']['callback']['p95Ms']-1),
        'intervalP95ChangePercent':100*(grouped['after']['interval']['p95Ms']/grouped['before']['interval']['p95Ms']-1)})
save(OUT,'performance-recheck.json',{'completed':True,'method':'single-browser sequential ABBA; original full-route pixel/native/pixel warmup;4 flagged desktop groups only;24drawing frames warm then120samples; aggregate ALL240callback/238interval samples per phase per case, no best-run selection','runs':runs,'comparison':rows,'allP95ChangesWithin10Percent':all(r['callbackP95ChangePercent']<=10 and r['intervalP95ChangePercent']<=10 for r in rows),'hardwareFPSProof':False})
print('DONE ABBA',[(r['mode'],r['pose'],round(r['callbackP95ChangePercent'],1),round(r['intervalP95ChangePercent'],1))for r in rows],flush=True)
