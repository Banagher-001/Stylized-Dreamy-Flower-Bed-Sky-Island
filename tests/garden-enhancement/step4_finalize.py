"""Seal Step4 only after current-version gates pass; verify old artifacts read-only.
No Git metadata/remote/release writes, publishing or later-step implementation.
Known diagnostic failures remain in the manifest, distinct from final reports.
"""
from pathlib import Path
import datetime,hashlib,json,re,subprocess,tarfile

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/evidence/garden-enhancement-step-4'
def read(n):return json.loads((OUT/n).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

build=read('build-verification.json');baseline=read('baseline-version.json')
candidate=build['candidateId'];inputs=build['buildInputsSha256']
assert build['passed']and build['exitCode']==0 and build['finalRebuildByteIdenticalToTestedBuild']
assert len(inputs)==83 and len(build['productionSha256'])==18
assert all(sha(ROOT/n)==v for n,v in inputs.items())
finger=hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert build['buildInputFingerprint']==finger and candidate=='garden-enhancement-step4-'+finger[:16]
assert {str(p.relative_to(ROOT)):sha(p)for p in sorted((ROOT/'dist').rglob('*'))if p.is_file()}==build['productionSha256']
old_build=json.loads((ROOT/'docs/evidence/garden-enhancement-step-3/build-verification.json').read_text())
protected={n:v for n,v in old_build['buildInputsSha256'].items()if n!='src/tour/startTourPrototype.ts'}
assert len(protected)==80 and all(sha(ROOT/n)==v for n,v in protected.items())
assert set(build['changedRuntimeSources'])=={'src/tour/autoGuide.ts','src/tour/autoGuide.css','src/tour/startTourPrototype.ts'}

reports=['controller-deterministic.json','browser-chromium.json','browser-firefox.json','browser-webkit.json',
    'faults-chromium.json','faults-firefox.json','faults-webkit.json','native-guide-recovery.json',
    'scene-and-background-protection.json','performance-comparison.json','auto-guide-recording-full.json',
    'auto-guide-recording-takeover.json','replay-native-takeover.json','video-timing-verification.json',
    'video-frame-review.json','production-preview-verification.json','service-lifecycle.json']
for name in reports:
    d=read(name)
    assert d['passed']and d['candidateId']==candidate,name
controller=read('controller-deterministic.json')
assert len(controller['cases'])==10 and all(r['passed']for r in controller['cases'])
assert controller['sourceSha256']['src/tour/autoGuide.ts']==inputs['src/tour/autoGuide.ts']
for engine,count in [('chromium',6),('firefox',5),('webkit',5)]:
    d=read(f'browser-{engine}.json');assert len(d['checks'])==29 and not d['errors']
    assert len(read(f'faults-{engine}.json')['cases'])==count
native=read('native-guide-recovery.json');assert len(native['checks'])==8 and not native['unhandledExceptions']and not native['fakeHiddenEventsUsed']
scope=read('scene-and-background-protection.json')
assert len(scope['wholeGpuCanvasPairs'])==18 and len(scope['AboutActualAlphaPairs'])==4 and len(scope['referenceWholePages'])==2 and not scope['errors']
assert not read('performance-comparison.json')['productionCodeChangedDuringBenchmark']
timing=read('video-timing-verification.json')
minimums={'O':4,'A1':10,'A2':14,'A3':14,'B1':12,'B2':10,'B3':10,'B4':8,'C1':10,'C2':12,'C3':12,'W':8,'S99':6}
assert [r['station']for r in timing['holds']]==list(minimums)
for row in timing['holds']:
    assert row['minimumSeconds']>=minimums[row['station']]
    assert row['observedDepartureAtMs']>=row['deadlineMs']>=row['actualReadyAtMs']+row['minimumSeconds']*1000-.001
for kind in ['full','takeover']:
    d=read(f'auto-guide-recording-{kind}.json')
    assert not d['errors']and (OUT/d['file']).is_file()
    assert sha(OUT/d['file'])==timing['durations'][kind]['fileSha256']
    assert abs(float(d['originalMetadata']['format']['duration'])-float(d['outputMetadata']['format']['duration']))<.12
assert len(read('replay-native-takeover.json')['checks'])==2
assert len(read('production-preview-verification.json')['responses'])==36
origins=read('video-frame-origins.json');review=read('video-frame-review.json')
assert len(origins['frames'])==5 and review['originManifestSha256']==sha(OUT/'video-frame-origins.json')
for row in origins['frames']:
    assert sha(OUT/row['frame'])==row['sha256']and sha(OUT/row['source'])==row['sourceSha256']

archive=read('candidate-archive-manifest.json')
assert archive['candidateId']==candidate and len(archive['files'])==104
assert sha(OUT/archive['file'])==archive['sha256']
with tarfile.open(OUT/archive['file'])as t:
    assert len(t.getmembers())==104
    for name,value in archive['files'].items():
        assert hashlib.sha256(t.extractfile(name).read()).hexdigest()==value['sha256']
        assert sha(ROOT/name)==value['sha256'],('archive/current mismatch',name)

before=read('before-files.json')['files']
changed=sorted(n for n,v in before.items()if not(ROOT/n).is_file()or sha(ROOT/n)!=v['sha256'])
assert set(changed)=={'src/tour/startTourPrototype.ts','docs/garden-enhancement/progress.md'},changed
paths=set(subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=ROOT).decode().strip('\0').split('\0'))
paths|={str((OUT/n).relative_to(ROOT))for n in ['scope-guard.json','result-binding.json','evidence-manifest.json','summary.json']}
added=sorted(n for n in paths-set(before)if n)
def allowed_new(name):
    return name.startswith('docs/evidence/garden-enhancement-step-4/')or name in{
        'src/tour/autoGuide.ts','src/tour/autoGuide.css','docs/garden-enhancement/step-4-standard.md',
        'docs/garden-enhancement/step-4-implementation.md','docs/garden-enhancement/step-4-verification.md',
        'tests/garden-enhancement/inspect_auto_guide.js'}or name.startswith('tests/garden-enhancement/step4_')
assert all(allowed_new(n)for n in added),[n for n in added if not allowed_new(n)]
old_seals=[]
for step,count in [(1,79),(2,355),(3,226)]:
    path=ROOT/f'docs/evidence/garden-enhancement-step-{step}/evidence-manifest.json'
    d=json.loads(path.read_text());assert len(d['files'])==count
    saved=next(row for row in baseline['oldSeals']if row['step']==step)
    assert sha(path)==saved['manifestSha256']
    assert all(sha(ROOT/n)==v['sha256']for n,v in d['files'].items())
    old_seals.append({'step':step,'manifestSha256':sha(path),'verifiedFiles':count})
releases={n:v for n,v in before.items()if n.startswith('release/')}
assert len(releases)==10 and all(sha(ROOT/n)==v['sha256']for n,v in releases.items())
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
assert head==baseline['gitHead']
save('scope-guard.json',{'passed':True,'candidateId':candidate,'frozenBeforeFiles':len(before),'changedExisting':changed,
    'allowedNewFileCount':len(added),'protectedOldBuildInputCount':80,'protectedOldBuildInputsSha256':protected,
    'oldSeals':old_seals,'oldReleaseFiles':releases,'gitHeadUnchanged':head,'autoGuideImplemented':True,
    'cloudShadowImplemented':False,'birdsImplemented':False,'oldReleaseArchivesOverwritten':False,
    'committed':False,'pushed':False,'deployed':False})

links=[]
for name in ['step-4-standard.md','step-4-implementation.md','step-4-verification.md','progress.md']:
    path=ROOT/'docs/garden-enhancement'/name
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',path.read_text()):
        if target.startswith(('http:','https:','#','skill:')):continue
        local=(path.parent/target.split('#')[0]).resolve()
        assert local.is_file()or local in{OUT/'result-binding.json',OUT/'evidence-manifest.json',OUT/'summary.json'},(path,target)
        links.append({'document':str(path.relative_to(ROOT)),'target':target})
pending=['physical iOS Safari/Android devices','device GPU FPS','mobile browser address-bar changes',
    'system font scaling and notch safe areas','VoiceOver/TalkBack','physical trackpad/APZ']
save('result-binding.json',{'passed':True,'candidateId':candidate,'baselineId':baseline['candidateId'],
    'buildInputFingerprint':finger,'productionFiles':build['productionSha256'],'candidateArchiveSha256':archive['sha256'],
    'reports':{n:sha(OUT/n)for n in reports+['build-verification.json','scope-guard.json','candidate-archive-manifest.json','video-frame-origins.json']},
    'rawPerformanceSources':{n:sha(OUT/n)for n in ['performance-matched.json','performance-native-recheck.json']},
    'documentLinks':links,'intermediateDiagnosticsPreserved':['external-scroll-diagnostic-before.json','delayed-image-diagnostic-before.json','pre-scroll-init-fix/','pre-image-wake-fix/'],
    'physicalDevicePending':pending,'published':False})
files=[p for p in OUT.rglob('*')if p.is_file()and p not in{OUT/'evidence-manifest.json',OUT/'summary.json'}]
files+=[ROOT/'docs/garden-enhancement'/n for n in ['step-4-standard.md','step-4-implementation.md','step-4-verification.md']]
files+=[p for p in (ROOT/'tests/garden-enhancement').glob('*')if p.is_file()and(p.name.startswith('step4_')or p.name=='inspect_auto_guide.js')]
manifest={'schema':1,'candidateId':candidate,'files':{str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(set(files))}}
save('evidence-manifest.json',manifest)
save('summary.json',{'passed':True,'completedStep':4,'candidateId':candidate,'baselineId':baseline['candidateId'],
    'completedAtUtc':datetime.datetime.now(datetime.UTC).isoformat(),'currentEnvironmentGates':{f'H{i:02d}':True for i in range(1,17)},
    'immutableArtifacts':len(manifest['files']),'evidenceManifestSha256':sha(OUT/'evidence-manifest.json'),
    'mutableProgressExcluded':'docs/garden-enhancement/progress.md','step5Started':False,'step6Started':False,'step7Started':False,
    'gitHead':head,'committed':False,'pushed':False,'deployed':False,'physicalDevicePending':True,
    'videos':['auto-guide-full.mp4','auto-guide-takeover.mp4'],'verification':'../../garden-enhancement/step-4-verification.md'})
assert all(sha(ROOT/n)==v['sha256']for n,v in manifest['files'].items())
for link in links:
    assert (ROOT/link['document']).parent.joinpath(link['target'].split('#')[0]).resolve().is_file()
print('PASS Step4 H01-H16:',candidate,';',len(manifest['files']),'sealed artifacts;',len(links),'valid document links; prior 660 artifacts intact; no Git/remote writes.')
