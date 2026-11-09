"""Resolve the remaining pixel A/A variance with controlled browser threads.
Only owned test-browser threads are pinned. Each side gets the same CPU/lifecycle
profile. Other profiles remain intact; unlike configurations are not pooled.
"""
import ast,hashlib,json,math,os
from playwright.sync_api import sync_playwright
from step7_common import *
build=json.loads((OUT/'build-verification.json').read_text());prior=json.loads((OUT/'performance-comparison.json').read_text())
assert not prior['passed']and prior['applicationByteIdenticalToBaseline']and prior['sameWholeApplicationResourceProfile']
saved=OUT/'versions'/build['candidateId']/'pooled-default-cpu';saved.mkdir(parents=True,exist_ok=True)
for name in ['performance-comparison.json','performance-recheck.json','performance-recheck-progress.json']:
    p=OUT/name
    if p.exists():
        target=saved/name;assert not target.exists();target.write_bytes(p.read_bytes())
cpus=prior['cpuEnvironment']['benchmarkAffinity'];assert len(cpus)==3
script_cpu=cpus[:1];driver_cpus=cpus[1:];os.sched_setaffinity(0,driver_cpus)
tree=ast.parse((ROOT/'tests/garden-enhancement/step7_performance.py').read_text());hook=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='HOOK'for t in n.targets))
def stats(values):
    s=sorted(values)
    return {'count':len(s),'p50Ms':s[int((len(s)-1)*.5)],'p95Ms':s[int((len(s)-1)*.95)],'meanMs':sum(s)/len(s),'maxMs':max(s)}
def intervals(rows):return[b['nativeTimestamp']-a['nativeTimestamp']for a,b in zip(rows,rows[1:])]
def change(after,before):return 100*(after/before-1)
errors=[];runs=[];pinning=[];stat_file=Path('/sys/fs/cgroup/cpu.stat')
with sync_playwright()as p:
    browser=launch(p);context=browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1);context.add_init_script(probe);context.add_init_script(hook)
    pages={phase:context.new_page()for phase in ['before','after']};neutral=context.new_page();neutral.goto('about:blank')
    def pin():
        session=browser.new_browser_cdp_session();processes=session.send('SystemInfo.getProcessInfo')['processInfo'];session.detach();rows=[]
        for process in processes:
            pid=int(process['id']);count=0
            try:tasks=list(Path(f'/proc/{pid}/task').iterdir())
            except FileNotFoundError:continue
            for task in tasks:
                tid=int(task.name);affinity=script_cpu if process['type'].lower()=='renderer'and tid==pid else driver_cpus
                try:os.sched_setaffinity(tid,affinity);count+=1
                except ProcessLookupError:continue
            rows.append({'pid':pid,'type':process['type'],'threadsAssigned':count,'rendererMainCPU':script_cpu if process['type'].lower()=='renderer'else None,'workerCPUs':driver_cpus})
        assert any(r['type'].lower()=='renderer'and r['threadsAssigned']for r in rows)
        return rows
    for phase,port in [('before',4182),('after',4183)]:
        page=pages[phase];watch(page,errors);load(page,f'http://127.0.0.1:{port}/?waterTime=2')
        for mode in ['pixel','native','pixel']:
            page.locator(f'.tour-actions [data-mode={mode}]').click()
            for _,h in VIEWS:visit(page,h)
        guide_start(page,3.8,reading=False);page.wait_for_function('window.__cloudPerf.renderer!==null');guide_stop(page)
    stat_before=stat_file.read_text()
    for phase in ['before','after','after','before']:
        neutral.bring_to_front();neutral.wait_for_timeout(300)
        page=pages[phase];page.bring_to_front();page.wait_for_timeout(150);guide_stop(page);pause(page);visit(page,3.8)
        pinning.append({'phase':phase,'processes':pin()});t=float(data(page)['sceneTime'])
        page.evaluate('window.__cloudPerf.control={base:0,index:0,count:240,started:false,done:false,frames:[]}')
        page.locator('#tour-motion').click();guide_start(page,reading=False);page.wait_for_function('window.__cloudPerf.control.done',timeout=120000,polling=100)
        raw=page.evaluate('window.__cloudPerf.control.frames');assert len(raw)==240;guide_stop(page);pause(page)
        assert abs(float(data(page)['sceneTime'])-(t+239/60))<.000002
        selected=raw[36:204];row={'mode':'pixel','phase':phase,'startEnvironmentTime':t,'raw':raw,'measured':selected,'frameWork':stats([r['costMs']for r in selected]),'intervals':stats(intervals(selected)),
            'measurementProfile':'owned Chromium renderer-main CPU0 / GPU and workers CPU1,2; neutral visibility step before every run'}
        runs.append(row);save(OUT,'performance-isolation-progress.json',{'complete':False,'candidateId':build['candidateId'],'runs':runs,'pinning':pinning})
        print('isolated pixel',phase,row['frameWork']['p95Ms'],row['intervals']['p95Ms'],flush=True)
    stat_after=stat_file.read_text();assert not errors,errors;context.close();browser.close()
max_h=max_time=max_pose=max_height=0
for a,b in zip([r for r in runs if r['phase']=='before'],[r for r in runs if r['phase']=='after']):
    assert a['startEnvironmentTime']==b['startEnvironmentTime']
    for x,y in zip(a['measured'],b['measured']):
        max_h=max(max_h,abs(x['h']-y['h']));max_time=max(max_time,abs(x['time']-y['time']));max_height=max(max_height,abs(float(x['height'])-float(y['height'])))
        max_pose=max(max_pose,*[abs(i-j)for key in ['position','target']for i,j in zip(json.loads(x[key]),json.loads(y[key]))])
assert max_h<.000003 and max_time<.000002 and max_pose<.000003 and max_height<.000003
group={'maxMatchedHError':max_h,'maxEnvironmentTimeError':max_time,'maxCameraCoordinateError':max_pose,'maxViewHeightMetadataError':max_height,
    'measurementProfile':'isolated renderer/worker affinity and symmetric true visibility, applied identically to both versions'}
for phase in ['before','after']:
    selected=[r for r in runs if r['phase']==phase];group[phase]={'frameWork':stats([f['costMs']for r in selected for f in r['measured']]),'intervals':stats([v for r in selected for v in intervals(r['measured'])])}
group['frameWorkP95ChangePercent']=change(group['after']['frameWork']['p95Ms'],group['before']['frameWork']['p95Ms']);group['intervalP95ChangePercent']=change(group['after']['intervals']['p95Ms'],group['before']['intervals']['p95Ms'])
assert all(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==v for n,v in build['buildInputsSha256'].items())
passed=group['frameWorkP95ChangePercent']<=10 and group['intervalP95ChangePercent']<=10
isolation={'passed':passed,'candidateId':build['candidateId'],'group':group,'runs':runs,'pinning':pinning,'cpuStatBefore':stat_before,'cpuStatAfter':stat_after,
    'reason':'remaining pixel A/A tail variance; identical artifacts and resource profile; reserve same main-thread CPU and same driver CPUs for both, with equal real hidden/show transitions',
    'differentCPUProfilesNotPooled':True,'originalAndPooledFlagsPreserved':str(saved.relative_to(OUT)),'productCodeChanged':False,'hardwareFPSProof':False}
save(OUT,'performance-isolation.json',isolation)
groups={**prior['groups'],'pixel':group};all_passed=prior['wheelP95ChangePercent']<=10 and all(g['frameWorkP95ChangePercent']<=10 and g['intervalP95ChangePercent']<=10 for g in groups.values())
report={**prior,'passed':all_passed,'groups':groups,'runs':prior['runs']+runs,'isolatedPixelAcceptance':isolation,
    'priorPooledProfile':str((saved/'performance-comparison.json').relative_to(OUT)),
    'method':prior['method']+'; remaining pixel group repeated with identical owned-renderer-main/worker CPU allocation and neutral visibility step before every phase; new pixel336/334 per side is a separate controlled CPU profile, not pooled with different profiles; native accepted initial336/334 and pooled90wheels retained; all prior runs preserved'}
save(OUT,'performance-comparison.json',report)
print('DONE isolated acceptance',all_passed,'pixel',group['frameWorkP95ChangePercent'],group['intervalP95ChangePercent'],flush=True)
