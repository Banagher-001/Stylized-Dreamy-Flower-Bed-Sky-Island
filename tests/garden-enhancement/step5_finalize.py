"""Seal current Step5 gates, preserving all historical/trial evidence read-only."""
from pathlib import Path
import datetime,hashlib,json,re,subprocess,tarfile
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/garden-enhancement-step-5'
def read(n):return json.loads((OUT/n).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
build=read('build-verification.json');baseline=read('baseline-version.json');candidate=build['candidateId'];inputs=build['buildInputsSha256']
assert build['passed']and build['exitCode']==0 and build['finalRebuildByteIdenticalToTestedBuild']
assert len(inputs)==86 and len(build['productionSha256'])==18
assert all(sha(ROOT/n)==v for n,v in inputs.items())
finger=hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert build['buildInputFingerprint']==finger and candidate=='garden-enhancement-step5-'+finger[:16]
assert {str(p.relative_to(ROOT)):sha(p)for p in sorted((ROOT/'dist').rglob('*'))if p.is_file()}==build['productionSha256']
old=json.loads((ROOT/'docs/evidence/garden-enhancement-step-4/build-verification.json').read_text())
changed_runtime={'src/scene/createScene.ts','src/tour/startTourPrototype.ts','src/animation/cloudShadows.ts','src/config/cloudShadows.ts','src/materials/applyCloudShadows.ts'}
assert set(build['changedRuntimeSources'])==changed_runtime
protected={n:v for n,v in old['buildInputsSha256'].items()if n not in changed_runtime}
assert len(protected)==81 and all(sha(ROOT/n)==v for n,v in protected.items())

reports=['model-and-materials.json','browser-chromium.json','browser-firefox.json','browser-webkit.json',
    'gpu-field-and-lighting.json','cloud-off-protection.json','native-guide-recovery.json','failure-and-font.json',
    'fresh-regressions.json','performance-comparison.json','clouds-recording-overview.json','clouds-recording-loop-water.json',
    'video-timing-verification.json','video-frame-review.json','production-preview-verification.json','service-lifecycle.json']
for n in reports:assert read(n)['passed']and read(n)['candidateId']==candidate,n
model=read('model-and-materials.json');assert len(model['cases'])==5 and all(r['passed']for r in model['cases'])
assert model['sourceSha256']=={n:inputs[n]for n in build['changedRuntimeSources']}
for engine in ['chromium','firefox','webkit']:
    d=read(f'browser-{engine}.json');assert len(d['checks'])==29 and not d['errors']
gpu=read('gpu-field-and-lighting.json');assert len(gpu['checks'])==8 and not gpu['errors']
coverage=next(r['evidence']['samples']for r in gpu['checks']if 'mask on visible' in r['name'])
assert len(coverage)==4 and all(.20<=r['coverageAbovePoint25']<=.40 for r in coverage)
scope=read('cloud-off-protection.json')
assert len(scope['wholeGpuCanvasPairs'])==18 and len(scope['AboutActualAlphaPairs'])==4 and len(scope['referenceWholePages'])==2 and not scope['errors']
native=read('native-guide-recovery.json');assert len(native['checks'])==9 and not native['unhandledExceptions']and native['exactCloudedCanvasBeforeAfterContextRestore']
assert not native['fakeHiddenEventsUsed']and len(read('failure-and-font.json')['checks'])==2
perf=read('performance-comparison.json')
assert perf['completed']and perf['wheelP95ChangePercent']<=10 and len(perf['runs'])==8 and not perf['errors']
assert perf['sameGeometryTextureProgramCallsTriangles']and perf['resources']['before']==perf['resources']['after']
for group in perf['groups'].values():
    assert group['maxMatchedHError']<.000003 and group['maxEnvironmentTimeError']<.000002
    assert group['frameWorkP95ChangePercent']<=10 and group['intervalP95ChangePercent']<=10
    assert all(group[p]['frameWork']['count']==336 and group[p]['intervals']['count']==334 for p in ['before','after'])
trial=OUT/'versions/garden-enhancement-step5-1c195311be269c29/pre-optimization-reports/performance-comparison.json'
assert not json.loads(trial.read_text())['passed'],'Initial threshold flag must remain'
for p in [OUT/'candidate-archive-manifest.json',*(OUT/'versions').glob('*/archive-manifest.json')]:
    archive=json.loads(p.read_text());path=p.parent/archive['file'];assert sha(path)==archive['sha256']
    with tarfile.open(path)as t:
        assert len(t.getmembers())==len(archive['files'])==107
        for n,v in archive['files'].items():
            assert hashlib.sha256(t.extractfile(n).read()).hexdigest()==v['sha256']
            if p.parent==OUT:assert sha(ROOT/n)==v['sha256']

timing=read('video-timing-verification.json');assert timing['overviewEnvironmentEnd']-timing['overviewEnvironmentStart']>60
assert float(timing['crossingEnvironmentTime'])>timing['cycleSeconds']and not timing['accelerated']
for kind in ['overview','loop-water']:
    d=read(f'clouds-recording-{kind}.json');assert not d['errors']
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
def allowed(n):
    return n.startswith(('docs/evidence/garden-enhancement-step-5/','tests/garden-enhancement/step5_'))or n in{
        'src/animation/cloudShadows.ts','src/config/cloudShadows.ts','src/materials/applyCloudShadows.ts',
        'docs/garden-enhancement/step-5-standard.md','docs/garden-enhancement/step-5-implementation.md','docs/garden-enhancement/step-5-verification.md'}
assert all(allowed(n)for n in added),[n for n in added if not allowed(n)]
seals=[]
for step,count in [(1,79),(2,355),(3,226),(4,235)]:
    p=ROOT/f'docs/evidence/garden-enhancement-step-{step}/evidence-manifest.json';d=json.loads(p.read_text())
    assert len(d['files'])==count and sha(p)==next(r['manifestSha256']for r in baseline['oldSeals']if r['step']==step)
    assert all(sha(ROOT/n)==v['sha256']for n,v in d['files'].items())
    seals.append({'step':step,'verifiedFiles':count,'manifestSha256':sha(p)})
releases={n:v for n,v in before.items()if n.startswith('release/')}
assert len(releases)==10 and all(sha(ROOT/n)==v['sha256']for n,v in releases.items())
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip();assert head==baseline['gitHead']
save('scope-guard.json',{'passed':True,'candidateId':candidate,'frozenBeforeFiles':len(before),'changedExisting':changed,'allowedNewFileCount':len(added),
    'protectedOldBuildInputsSha256':protected,'protectedOldBuildInputCount':81,'oldSeals':seals,'oldReleaseFiles':releases,'gitHeadUnchanged':head,
    'cloudShadowsImplemented':True,'birdsImplemented':False,'oldReleaseArchivesOverwritten':False,'committed':False,'pushed':False,'deployed':False})
links=[]
for name in ['step-5-standard.md','step-5-implementation.md','step-5-verification.md','progress.md']:
    p=ROOT/'docs/garden-enhancement'/name
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
        if target.startswith(('http:','https:','#','skill:')):continue
        local=(p.parent/target.split('#')[0]).resolve()
        assert local.is_file()or local in{OUT/'result-binding.json',OUT/'evidence-manifest.json',OUT/'summary.json'},(p,target)
        links.append({'document':str(p.relative_to(ROOT)),'target':target})
save('result-binding.json',{'passed':True,'candidateId':candidate,'baselineId':baseline['candidateId'],'buildInputFingerprint':finger,
    'productionFiles':build['productionSha256'],'candidateArchiveSha256':read('candidate-archive-manifest.json')['sha256'],
    'reports':{n:sha(OUT/n)for n in reports+['build-verification.json','scope-guard.json','candidate-archive-manifest.json','video-frame-origins.json']},
    'initialPerformanceFlagPreserved':{'file':str(trial.relative_to(OUT)),'sha256':sha(trial),'passed':False},'documentLinks':links,
    'physicalDevicePending':['iOS Safari/Android devices','hardware GPU FPS','browser address bar/system font/safe area','VoiceOver/TalkBack','physical trackpad/APZ'],
    'committed':False,'pushed':False,'deployed':False})
files=[p for p in OUT.rglob('*')if p.is_file()and p not in{OUT/'evidence-manifest.json',OUT/'summary.json'}]
files+=[ROOT/'docs/garden-enhancement'/n for n in ['step-5-standard.md','step-5-implementation.md','step-5-verification.md']]
files+=[p for p in (ROOT/'tests/garden-enhancement').glob('step5_*')if p.is_file()]
manifest={'schema':1,'candidateId':candidate,'files':{str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(set(files))}}
save('evidence-manifest.json',manifest)
save('summary.json',{'passed':True,'completedStep':5,'candidateId':candidate,'baselineId':baseline['candidateId'],'completedAtUtc':datetime.datetime.now(datetime.UTC).isoformat(),
    'currentEnvironmentGates':{f'I{i:02d}':True for i in range(1,17)},'immutableArtifacts':len(manifest['files']),'evidenceManifestSha256':sha(OUT/'evidence-manifest.json'),
    'mutableProgressExcluded':'docs/garden-enhancement/progress.md','step6Started':False,'step7Started':False,'gitHead':head,'committed':False,'pushed':False,'deployed':False,
    'physicalDevicePending':True,'videos':['clouds-overview.mp4','clouds-loop-water.mp4'],'verification':'../../garden-enhancement/step-5-verification.md'})
assert all(sha(ROOT/n)==v['sha256']for n,v in manifest['files'].items())
for link in links:assert(ROOT/link['document']).parent.joinpath(link['target'].split('#')[0]).resolve().is_file()
print('PASS Step5 I01-I16:',candidate,';',len(manifest['files']),'sealed artifacts;',len(links),'valid links; prior895artifacts and10release files unchanged; no Git/remote writes.')
