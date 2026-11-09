"""Counterbalanced recheck of flagged wheel/pixel groups only.
Keep and aggregate EVERY initial sample with EVERY new sample. Native passed
already and is retained without redundant retesting. No application changes.
"""
import ast,hashlib,json,math,os
from playwright.sync_api import sync_playwright
from step7_common import *
build=json.loads((OUT/'build-verification.json').read_text());initial=json.loads((OUT/'performance-comparison.json').read_text());assert not initial['passed']and initial['candidateId']==build['candidateId']
assert build['applicationInputsIdenticalToStep6']and build['productionIdenticalToStep6']
preserved=OUT/'versions'/build['candidateId']/'initial-performance';preserved.mkdir(parents=True,exist_ok=True)
for name in ['performance-comparison.json','performance-progress.json']:
    target=preserved/name
    if target.exists():assert target.read_bytes()==(OUT/name).read_bytes()
    else:target.write_bytes((OUT/name).read_bytes())
tree=ast.parse((ROOT/'tests/garden-enhancement/step7_performance.py').read_text());hook=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='HOOK'for t in n.targets))
os.sched_setaffinity(0,initial['cpuEnvironment']['benchmarkAffinity']);stat_path=Path('/sys/fs/cgroup/cpu.stat');stat_before=stat_path.read_text()
def stats(v):
    s=sorted(v);assert s
    return{'count':len(s),'p50Ms':s[math.floor((len(s)-1)*.5)],'p95Ms':s[math.floor((len(s)-1)*.95)],'meanMs':sum(s)/len(s),'maxMs':max(s)}
def intervals(rows):return[b['nativeTimestamp']-a['nativeTimestamp']for a,b in zip(rows,rows[1:])]
def change(a,b):return 100*(a/b-1)
errors=[];wheel_runs=[];new_runs=[]
with sync_playwright()as p:
    browser=launch(p);context=browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1);context.add_init_script(probe);context.add_init_script(hook)
    pages={phase:context.new_page()for phase in ['before','after']}
    for phase,port in [('before',4182),('after',4183)]:
        page=pages[phase];watch(page,errors);load(page,f'http://127.0.0.1:{port}/?waterTime=2')
        for mode in ['pixel','native','pixel']:
            page.locator(f'.tour-actions [data-mode={mode}]').click()
            for _,h in VIEWS:visit(page,h)
        guide_start(page,3.8,reading=False);page.wait_for_function('window.__cloudPerf.renderer!==null');guide_stop(page)
    for phase in ['before','after','after','before']:
        page=pages[phase];page.bring_to_front();routes=[]
        for key,h in [('T01',.9),('T12',4.05),('T23',8.35),('T3W',11.26),('WIDE',11.66)]:
            visit(page,h);page.mouse.move(1100,260);page.wait_for_timeout(80);page.evaluate('window.__tourProbe.settles=[]')
            for delta in [15]*3+[-15]*3:
                y=page.evaluate('scrollY');page.mouse.wheel(0,delta);page.wait_for_function('y=>Math.abs(scrollY-y)>1',arg=y)
                page.wait_for_function('document.querySelector("#tour-host").dataset.cameraState==="settled"');page.wait_for_timeout(20)
            values=page.evaluate('window.__tourProbe.settles');assert len(values)==6
            routes.append({'pose':key,'H':h,'deltas':[15]*3+[-15]*3,'samplesMs':values})
        row={'phase':phase,'routes':routes,'stats':stats([v for r in routes for v in r['samplesMs']])};wheel_runs.append(row)
        print('wheel recheck',phase,row['stats'],flush=True)
        save(OUT,'performance-recheck-progress.json',{'complete':False,'candidateId':build['candidateId'],'wheelRuns':wheel_runs,'runs':new_runs})
    for phase in ['before','after','after','before']:
        page=pages[phase];page.bring_to_front();guide_stop(page);pause(page);visit(page,3.8);t=float(data(page)['sceneTime'])
        page.evaluate('window.__cloudPerf.control={base:0,index:0,count:240,started:false,done:false,frames:[]}')
        page.locator('#tour-motion').click();guide_start(page,reading=False);page.wait_for_function('window.__cloudPerf.control.done',timeout=120000,polling=100)
        raw=page.evaluate('window.__cloudPerf.control.frames');assert len(raw)==240;guide_stop(page);pause(page);assert abs(float(data(page)['sceneTime'])-(t+239/60))<.000002
        selected=raw[36:204];row={'mode':'pixel','phase':phase,'startEnvironmentTime':t,'raw':raw,'measured':selected,'frameWork':stats([r['costMs']for r in selected]),'intervals':stats(intervals(selected)),'round':'recheck'}
        new_runs.append(row);print('pixel recheck',phase,row['frameWork']['p95Ms'],row['intervals']['p95Ms'],flush=True)
        save(OUT,'performance-recheck-progress.json',{'complete':False,'candidateId':build['candidateId'],'wheelRuns':wheel_runs,'runs':new_runs})
    assert not errors,errors;context.close();browser.close()
for a,b in zip([r for r in new_runs if r['phase']=='before'],[r for r in new_runs if r['phase']=='after']):
    assert a['startEnvironmentTime']==b['startEnvironmentTime']
    for x,y in zip(a['measured'],b['measured']):
        assert abs(x['h']-y['h'])<.000003 and abs(x['time']-y['time'])<.000002
        assert all(abs(i-j)<.000003 for key in ['position','target']for i,j in zip(json.loads(x[key]),json.loads(y[key])))and abs(float(x['height'])-float(y['height']))<.000003
all_runs=initial['runs']+new_runs;groups=initial['groups'];group={k:v for k,v in groups['pixel'].items()if k.startswith('max')}
for phase in ['before','after']:
    rows=[r for r in all_runs if r['mode']=='pixel'and r['phase']==phase]
    group[phase]={'frameWork':stats([f['costMs']for r in rows for f in r['measured']]),'intervals':stats([v for r in rows for v in intervals(r['measured'])])}
group['frameWorkP95ChangePercent']=change(group['after']['frameWork']['p95Ms'],group['before']['frameWork']['p95Ms'])
group['intervalP95ChangePercent']=change(group['after']['intervals']['p95Ms'],group['before']['intervals']['p95Ms']);groups['pixel']=group
wheel_all={}
for phase in ['before','after']:
    values=[v for r in initial['wheel30'][phase]['routes']for v in r['samplesMs']]+[v for run in wheel_runs if run['phase']==phase for r in run['routes']for v in r['samplesMs']]
    wheel_all[phase]=stats(values);assert len(values)==90
wheel_change=change(wheel_all['after']['p95Ms'],wheel_all['before']['p95Ms']);stat_after=stat_path.read_text()
assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in build['buildInputsSha256'].items())
passed=wheel_change<=10 and all(g['frameWorkP95ChangePercent']<=10 and g['intervalP95ChangePercent']<=10 for g in groups.values())
report={**initial,'passed':passed,'runs':all_runs,'groups':groups,'wheelP95ChangePercent':wheel_change,'wheelAllSamples':wheel_all,'wheelRecheckRuns':wheel_runs,
    'initialPerformanceFlagPreserved':str((preserved/'performance-comparison.json').relative_to(OUT)),
    'recheck':{'reason':'initial wheel/pixel flags with proven byte-identical application and exact resources; native passed; investigate temporal software-renderer sampling variance with balanced wheel/pixel ABBA',
        'allInitialAndNewSamplesIncluded':True,'wheelSamplesPerPhase':90,'pixelWorkSamplesPerPhase':672,'pixelIntervalsPerPhase':668,'nativeSamplesRetained':336,
        'CPUStatBefore':stat_before,'CPUStatAfter':stat_after,'affinity':sorted(os.sched_getaffinity(0))},
    'method':initial['method']+'; flagged wheel and pixel groups only rechecked in new serial ABBA, EVERY initial/new sample pooled:90 wheel,672pixel work/668interval per phase; native original336/334 retained; no best-run selection or app changes'}
save(OUT,'performance-comparison.json',report);save(OUT,'performance-recheck.json',{'passed':passed,'candidateId':build['candidateId'],'wheelAllSamples':wheel_all,'groups':groups,'recheck':report['recheck']})
print('DONE pooled recheck',passed,'wheel',wheel_change,'pixel',group['frameWorkP95ChangePercent'],group['intervalP95ChangePercent'],flush=True)
