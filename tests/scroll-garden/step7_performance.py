"""Perf-only matched C-route sampling, with raw CPU/layout metrics for diagnosis.

Run old/current URLs in alternating fresh-browser pairs with identical options.
No screenshots, trimming, threshold changes, or app/source mutations occur here.
"""
import argparse,hashlib,re,time
from playwright.sync_api import sync_playwright
from step7_common import *

parser=argparse.ArgumentParser()
parser.add_argument('--url',required=True)
parser.add_argument('--label',required=True)
parser.add_argument('--source-root',type=Path,required=True)
args=parser.parse_args()
assert re.fullmatch(r'[A-Za-z0-9_-]+',args.label), 'label must be a simple new receipt name'
destination=OUT/f'latency-{args.label}.json'
assert not destination.exists(),str(destination)+' exists; use a fresh label to preserve raw evidence'
source_root=args.source_root.resolve();assert(source_root/'src/tour/startTourPrototype.ts').is_file()
route=[0,1.74,2.54,3.34,4.95,5.95,6.84,7.64,9.14,10.05,10.83,11.5,0,10.05]
metric_names=['Timestamp','LayoutDuration','RecalcStyleDuration','ScriptDuration','TaskDuration','LayoutCount','RecalcStyleCount','JSHeapUsedSize','Nodes','Documents','Frames']
duration_names=['LayoutDuration','RecalcStyleDuration','ScriptDuration','TaskDuration']
issues=[]
with sync_playwright() as p:
    browser=launch(p);context=browser.new_context(viewport={'width':1440,'height':900});context.add_init_script(PROBE)
    page=context.new_page();page.on('pageerror',lambda e:issues.append(str(e)))
    page.goto(args.url.rstrip('/')+'/?tour=prototype&waterTime=2',wait_until='networkidle')
    page.wait_for_selector('#tour-host[data-render-state="ready"]')
    session=context.new_cdp_session(page);session.send('Performance.enable',{'timeDomain':'timeTicks'})
    def metrics():
        values={v['name']:v['value']for v in session.send('Performance.getMetrics')['metrics']}
        return {k:values[k]for k in metric_names if k in values}
    caches=[]
    for mode in ['pixel','native','pixel']:
        page.locator(f'.tour-actions [data-mode={mode}]').click()
        for h in route:go(page,h)
        frames(page);caches.append(json.loads(data(page)['rendererStats']))
    go(page,9.14);page.wait_for_timeout(200);page.evaluate('window.__tourProbe.settles=[]');page.mouse.move(1100,260)
    before=metrics();previous_metrics=before;per_stop=[];started=time.perf_counter()
    for index,delta in enumerate([96]*15+[-96]*15):
        prior=page.evaluate('scrollY');page.mouse.wheel(0,delta)
        page.wait_for_function('y=>Math.abs(scrollY-y)>1',arg=prior)
        page.wait_for_function('()=>document.querySelector("#tour-host").dataset.cameraState==="settled"')
        page.wait_for_timeout(20)
        current=metrics();d=data(page)
        per_stop.append({'index':index,'wheelDeltaY':delta,'displayH':float(d['displayH']),'absoluteMetrics':current,'deltaMetrics':{k:current[k]-previous_metrics[k]for k in current if k in previous_metrics}})
        previous_metrics=current
    elapsed=(time.perf_counter()-started)*1000
    samples=page.evaluate('window.__tourProbe.settles');assert len(samples)==30,len(samples)
    after=metrics();delta_metrics={k:after[k]-before[k]for k in after if k in before}
    assert not issues,issues
    receipt={
        'label':args.label,'pageTitle':page.title(),'url':args.url,'browser':{'engine':'Chromium','version':browser.version,'graphics':'ANGLE/SwiftShader','freshBrowserPerRun':True},
        'method':'same fully warmed C-route and pixel/native/pixel history; 1440x900; waterTime=2; 30 real wheel stops (+96x15,-96x15); no screenshots; all raw samples retained; CDP Performance metrics collected between stops; run with other diagnostic browsers closed',
        'warmRouteH':route,'warmCaches':caches,'samplesMs':samples,'p95Ms':sorted(samples)[int((len(samples)-1)*.95)],'maxMs':max(samples),'elapsedClientMs':elapsed,
        'metricsBefore':before,'metricsAfter':after,'metricsDelta':delta_metrics,'durationDeltaMs':{k:delta_metrics[k]*1000 for k in duration_names if k in delta_metrics},'perStop':per_stop,
        'sourceRoot':str(source_root),'runtimeSourceSha256':{str(f.relative_to(source_root)):hashlib.sha256(f.read_bytes()).hexdigest()for f in (source_root/'src/tour').glob('*')if f.suffix in ['.ts','.css']},
        'unhandledExceptions':issues,'hardwareFPSProof':False,
    }
    save(destination.name,receipt);session.detach();browser.close()
    print(args.label,'p95',receipt['p95Ms'],'max',receipt['maxMs'],'CPU/layout ms',receipt['durationDeltaMs'],flush=True)
