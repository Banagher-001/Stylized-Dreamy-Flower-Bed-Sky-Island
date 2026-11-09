"""Seal Step6 only, including failed trials and immutable historical artifacts."""
from pathlib import Path
import datetime,hashlib,json,re,subprocess,tarfile
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/garden-enhancement-step-6'
def read(n):return json.loads((OUT/n).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
build=read('build-verification.json');baseline=read('baseline-version.json');candidate=build['candidateId'];inputs=build['buildInputsSha256']
assert build['passed']and build['exitCode']==0 and build['finalRebuildByteIdenticalToTestedBuild']
assert len(inputs)==92 and len(build['productionSha256'])==18
assert all(sha(ROOT/n)==v for n,v in inputs.items())
finger=hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert build['buildInputFingerprint']==finger and candidate=='garden-enhancement-step6-'+finger[:16]
assert {str(p.relative_to(ROOT)):sha(p)for p in sorted((ROOT/'dist').rglob('*'))if p.is_file()}==build['productionSha256']
old=json.loads((ROOT/'docs/evidence/garden-enhancement-step-5/build-verification.json').read_text())
new_sources={'src/config/birds.ts','src/animation/birdMotion.ts','src/geometry/createBirdGeometry.ts','src/materials/createBirdMaterial.ts','src/scene/createBirds.ts','src/tour/birdVisibility.ts'}
changed_runtime=new_sources|{'src/scene/createScene.ts','src/tour/startTourPrototype.ts'}
assert set(build['changedRuntimeSources'])==changed_runtime
protected={n:v for n,v in old['buildInputsSha256'].items()if n not in changed_runtime}
assert len(protected)==84 and all(sha(ROOT/n)==v for n,v in protected.items())
reports=['motion-geometry-and-safety.json','projection-motion-and-depth.json','browser-chromium.json','browser-firefox.json','browser-webkit.json',
    'birds-off-protection.json','native-guide-recovery.json','failure-and-font.json','fresh-regressions.json','performance-comparison.json',
    'birds-recording-overview.json','birds-recording-controls.json','video-timing-verification.json','video-frame-review.json','production-preview-verification.json','service-lifecycle.json']
for n in reports:assert read(n)['passed']and read(n)['candidateId']==candidate,n
model=read('motion-geometry-and-safety.json');assert len(model['cases'])==5 and all(r['passed']for r in model['cases'])
assert model['sourceSha256']=={n:inputs[n]for n in build['changedRuntimeSources']}
clearance=model['cases'][2]['evidence'];assert clearance['staticGap']>=.25 and clearance['birdGap']>=.25
for engine in ['chromium','firefox','webkit']:
    d=read(f'browser-{engine}.json');assert len(d['checks'])==29 and not d['errors']
safety=read('projection-motion-and-depth.json');assert len(safety['checks'])==6 and not safety['errors']
assert sum(len(r['evidence']['samples'])for r in safety['checks']if 'actual normal UI full bird envelopes'in r['name'])==216
scope=read('birds-off-protection.json')
assert len(scope['wholeGpuCanvasPairs'])==18 and len(scope['AboutActualAlphaPairs'])==4 and len(scope['referenceWholePages'])==2 and not scope['errors']
native=read('native-guide-recovery.json');assert len(native['checks'])==10 and not native['unhandledExceptions']
assert native['exactCloudedCanvasBeforeAfterContextRestore']and native['exactBirdOverviewBeforeAfterContextRestore']and not native['fakeHiddenEventsUsed']
assert len(read('failure-and-font.json')['checks'])==2 and len(read('fresh-regressions.json')['reports'])==6
perf=read('performance-comparison.json')
assert perf['completed']and perf['wheelP95ChangePercent']<=10 and len(perf['runs'])==8 and not perf['errors']and perf['withinBirdResourceBudget']
for a,b in zip(perf['resources']['before'],perf['resources']['after']):
    x,y=a['stats'],b['stats'];assert y['geometries']-x['geometries']==1 and y['textures']==x['textures']and 0<=y['programs']-x['programs']<=2
    assert 0<=y['calls']-x['calls']<=1 and 0<=y['triangles']-x['triangles']<=180
assert perf['cpuEnvironment']['boundedCpu']and len(perf['cpuEnvironment']['benchmarkAffinity'])==3
stat_before=dict(row.split()for row in perf['cpuEnvironment']['statBefore'].splitlines());stat_after=dict(row.split()for row in perf['cpuEnvironment']['statAfter'].splitlines())
assert int(stat_after['nr_throttled'])==int(stat_before['nr_throttled'])
for group in perf['groups'].values():
    assert group['maxMatchedHError']<.000003 and group['maxEnvironmentTimeError']<.000002 and group['maxCameraCoordinateError']<.000003
    assert group['frameWorkP95ChangePercent']<=10 and group['intervalP95ChangePercent']<=10
    assert all(group[p]['frameWork']['count']==336 and group[p]['intervals']['count']==334 for p in ['before','after'])
trials=[OUT/'versions/garden-enhancement-step6-3171e6fa0a9fe255/pre-layout-cache/performance-initial-summary.json',
    OUT/'versions/garden-enhancement-step6-b1c21e4a6491ee54/unrestricted-cpu-profile/performance-comparison.json',
    OUT/'versions/garden-enhancement-step6-b1c21e4a6491ee54/before-single-batch/performance-comparison.json']
assert all(not json.loads(p.read_text())['passed']for p in trials)
for p in [OUT/'candidate-archive-manifest.json',*(OUT/'versions').glob('*/archive-manifest.json')]:
    archive=json.loads(p.read_text());path=p.parent/archive['file'];assert sha(path)==archive['sha256']
    with tarfile.open(path)as t:
        assert len(t.getmembers())==len(archive['files'])==113
        for n,v in archive['files'].items():
            assert hashlib.sha256(t.extractfile(n).read()).hexdigest()==v['sha256']
            if p.parent==OUT:assert sha(ROOT/n)==v['sha256']
timing=read('video-timing-verification.json');assert timing['overviewEnvironmentEnd']-timing['overviewEnvironmentStart']>61 and not timing['accelerated']
assert len(timing['actualObservedCycles'])==3 and all(r['actualPhaseWraps']>=1 and r['flapAndGlideObserved']for r in timing['actualObservedCycles'])
for kind in ['overview','controls']:
    d=read(f'birds-recording-{kind}.json');assert not d['errors']
    assert sha(OUT/d['file'])==timing['durations'][kind]['sha256']and abs(timing['durations'][kind]['differenceSeconds'])<.12
origins=read('video-frame-origins.json');review=read('video-frame-review.json')
assert len(origins['frames'])==4 and review['originManifestSha256']==sha(OUT/'video-frame-origins.json')
assert all(sha(OUT/r['frame'])==r['sha256']and sha(OUT/r['source'])==r['sourceSha256']for r in origins['frames'])
assert len(read('production-preview-verification.json')['responses'])==36
before=read('before-files.json')['files']
changed=sorted(n for n,v in before.items()if not(ROOT/n).is_file()or sha(ROOT/n)!=v['sha256'])
assert set(changed)=={'src/scene/createScene.ts','src/tour/startTourPrototype.ts','docs/garden-enhancement/progress.md'},changed
paths=set(subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=ROOT).decode().strip('\0').split('\0'))
paths|={str((OUT/n).relative_to(ROOT))for n in ['scope-guard.json','result-binding.json','evidence-manifest.json','summary.json']}
added=sorted(n for n in paths-set(before)if n)
def allowed(n):return n.startswith(('docs/evidence/garden-enhancement-step-6/','tests/garden-enhancement/step6_'))or n in new_sources|{
    'docs/garden-enhancement/step-6-standard.md','docs/garden-enhancement/step-6-implementation.md','docs/garden-enhancement/step-6-verification.md'}
assert all(allowed(n)for n in added),[n for n in added if not allowed(n)]
seals=[]
for step,count in [(1,79),(2,355),(3,226),(4,235),(5,310)]:
    p=ROOT/f'docs/evidence/garden-enhancement-step-{step}/evidence-manifest.json';d=json.loads(p.read_text())
    assert len(d['files'])==count and sha(p)==next(r['manifestSha256']for r in baseline['oldSeals']if r['step']==step)
    assert all(sha(ROOT/n)==v['sha256']for n,v in d['files'].items())
    seals.append({'step':step,'verifiedFiles':count,'manifestSha256':sha(p)})
releases={n:v for n,v in before.items()if n.startswith('release/')}
assert len(releases)==10 and all(sha(ROOT/n)==v['sha256']for n,v in releases.items())
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip();assert head==baseline['gitHead']
save('scope-guard.json',{'passed':True,'candidateId':candidate,'frozenBeforeFiles':len(before),'changedExisting':changed,'allowedNewFileCount':len(added),
    'protectedOldBuildInputsSha256':protected,'protectedOldBuildInputCount':84,'oldSeals':seals,'oldReleaseFiles':releases,'gitHeadUnchanged':head,
    'birdsImplemented':True,'step7Started':False,'oldReleaseArchivesOverwritten':False,'committed':False,'pushed':False,'deployed':False})
links=[]
for name in ['step-6-standard.md','step-6-implementation.md','step-6-verification.md','progress.md']:
    p=ROOT/'docs/garden-enhancement'/name
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
        if target.startswith(('http:','https:','#','skill:')):continue
        local=(p.parent/target.split('#')[0]).resolve()
        assert local.is_file()or local in{OUT/'result-binding.json',OUT/'evidence-manifest.json',OUT/'summary.json'},(p,target)
        links.append({'document':str(p.relative_to(ROOT)),'target':target})
save('result-binding.json',{'passed':True,'candidateId':candidate,'baselineId':baseline['candidateId'],'buildInputFingerprint':finger,
    'productionFiles':build['productionSha256'],'candidateArchiveSha256':read('candidate-archive-manifest.json')['sha256'],
    'reports':{n:sha(OUT/n)for n in reports+['build-verification.json','scope-guard.json','candidate-archive-manifest.json','video-frame-origins.json']},
    'initialPerformanceFlagsPreserved':[{'file':str(p.relative_to(OUT)),'sha256':sha(p),'passed':False}for p in trials],'documentLinks':links,
    'physicalDevicePending':['iOS Safari/Android devices','hardware GPU FPS','browser address bar/system font/safe area','VoiceOver/TalkBack','physical trackpad/APZ'],
    'committed':False,'pushed':False,'deployed':False})
files=[p for p in OUT.rglob('*')if p.is_file()and p not in{OUT/'evidence-manifest.json',OUT/'summary.json'}]
files+=[ROOT/'docs/garden-enhancement'/n for n in ['step-6-standard.md','step-6-implementation.md','step-6-verification.md']]
files+=[p for p in(ROOT/'tests/garden-enhancement').glob('step6_*')if p.is_file()]
manifest={'schema':1,'candidateId':candidate,'files':{str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(set(files))}}
save('evidence-manifest.json',manifest)
save('summary.json',{'passed':True,'completedStep':6,'candidateId':candidate,'baselineId':baseline['candidateId'],'completedAtUtc':datetime.datetime.now(datetime.UTC).isoformat(),
    'currentEnvironmentGates':{f'J{i:02d}':True for i in range(1,17)},'immutableArtifacts':len(manifest['files']),'evidenceManifestSha256':sha(OUT/'evidence-manifest.json'),
    'mutableProgressExcluded':'docs/garden-enhancement/progress.md','step7Started':False,'gitHead':head,'committed':False,'pushed':False,'deployed':False,
    'physicalDevicePending':True,'videos':['birds-overview.mp4','birds-controls.mp4'],'verification':'../../garden-enhancement/step-6-verification.md'})
assert all(sha(ROOT/n)==v['sha256']for n,v in manifest['files'].items())
for link in links:assert(ROOT/link['document']).parent.joinpath(link['target'].split('#')[0]).resolve().is_file()
print('PASS Step6 J01-J16:',candidate,';',len(manifest['files']),'sealed artifacts;',len(links),'valid links; prior1205artifacts and10release files unchanged; no Git/remote writes.')
