"""Bind and seal the final local delivery; historical files remain immutable."""
from pathlib import Path
import datetime,hashlib,json,re,subprocess,tarfile,zipfile
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/garden-enhancement-step-7'
def read(n):return json.loads((OUT/n).read_text())
def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        while b:=f.read(1024*1024):h.update(b)
    return h.hexdigest()
def save(n,d):(OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
build=read('build-verification.json');baseline=read('baseline-version.json');candidate=build['candidateId']
assert build['passed']and build['finalRebuildByteIdenticalToTestedBuild']and build['applicationInputsIdenticalToStep6']and build['productionIdenticalToStep6']
assert len(build['buildInputsSha256'])==92 and len(build['productionSha256'])==18 and not build['changedRuntimeSources']
assert all(sha(ROOT/n)==v for n,v in build['buildInputsSha256'].items())and all(sha(ROOT/n)==v for n,v in build['productionSha256'].items())
finger=hashlib.sha256(json.dumps(build['buildInputsSha256'],sort_keys=True,separators=(',',':')).encode()).hexdigest();assert finger==build['buildInputFingerprint']and candidate=='garden-enhancement-step7-'+finger[:16]
reports=['motion-geometry-and-safety.json','browser-chromium.json','browser-firefox.json','browser-webkit.json','projection-motion-and-depth.json','complete-scene-protection.json',
    'native-guide-recovery.json','failure-and-font.json','replay-native-takeover.json','faults-chromium.json','faults-firefox.json','faults-webkit.json','fresh-regressions.json','video-failure-recovery.json',
    'launcher-and-http.json','overall-resource-cost.json','performance-comparison.json','endurance.json','recording-full.json','recording-controls.json','video-timing-verification.json','video-frame-review.json',
    'production-preview-verification.json','package-verification.json','unpacked-source-integrity.json','unpacked-site-integrity.json','unpacked-evidence-integrity.json','unpacked-source-browser.json','unpacked-site-browser.json','service-lifecycle.json']
for name in reports:assert read(name)['passed']and read(name)['candidateId']==candidate,name
assert len(read('motion-geometry-and-safety.json')['cases'])==5
for engine in ['chromium','firefox','webkit']:
    d=read(f'browser-{engine}.json');assert len(d['checks'])==29 and not d['errors']
    assert len(read(f'faults-{engine}.json')['cases'])==(6 if engine=='chromium' else 5)
safety=read('projection-motion-and-depth.json');assert len(safety['checks'])==6 and not safety['errors']
assert sum(len(r['evidence']['samples'])for r in safety['checks']if 'actual normal UI full bird envelopes'in r['name'])==216
scope=read('complete-scene-protection.json');assert len(scope['wholeGpuCanvasPairs'])==18 and len(scope['AboutActualAlphaPairs'])==4 and len(scope['referenceWholePages'])==2 and not scope['errors']
native=read('native-guide-recovery.json');assert len(native['checks'])==10 and not native['unhandledExceptions']and not native['fakeHiddenEventsUsed']
assert native['exactCloudedCanvasBeforeAfterContextRestore']and native['exactBirdOverviewBeforeAfterContextRestore']
assert len(read('fresh-regressions.json')['reports'])==11 and len(read('video-failure-recovery.json')['checks'])==2
perf=read('performance-comparison.json');assert perf['completed']and perf['wheelP95ChangePercent']<=10 and not perf['errors']and perf['sameWholeApplicationResourceProfile']and perf['applicationByteIdenticalToBaseline']
assert perf['resources']['before']==perf['resources']['after']
for group in perf['groups'].values():
    assert group['maxMatchedHError']<.000003 and group['maxEnvironmentTimeError']<.000002 and group['maxCameraCoordinateError']<.000003
    assert group['frameWorkP95ChangePercent']<=10 and group['intervalP95ChangePercent']<=10
    assert all(group[phase]['frameWork']['count']>=336 and group[phase]['intervals']['count']>=334 for phase in ['before','after'])
if 'initialPerformanceFlagPreserved'in perf:
    first=OUT/perf['initialPerformanceFlagPreserved'];assert first.is_file()and not json.loads(first.read_text())['passed']
    assert perf['recheck']['allInitialAndNewSamplesIncluded']
endurance=read('endurance.json');assert endurance['wallSeconds']>=600 and endurance['interactionCycles']==20 and endurance['continuousOverviewEnvironmentSpan']>=150
assert all(r['observedPhaseWraps']>=1 and r['flapAndGlide']for r in endurance['birdCycles'])
assert all(all(row['stats'][key]==endurance['warmResources'][key]for key in ['geometries','textures','programs'])for row in endurance['samples'])
timing=read('video-timing-verification.json');assert len(timing['actualReadingHolds'])==13 and not timing['accelerated']
for kind in ['full','controls']:
    recording=read(f'recording-{kind}.json');assert not recording['errors']
    assert sha(OUT/recording['file'])==timing['videos'][kind]['sha256']and abs(timing['videos'][kind]['differenceSeconds'])<.12
origins=read('video-frame-origins.json');review=read('video-frame-review.json');assert len(origins['frames'])==6 and review['originManifestSha256']==sha(OUT/'video-frame-origins.json')
assert all(sha(OUT/r['frame'])==r['sha256']and sha(OUT/r['source'])==r['sourceSha256']for r in origins['frames'])
assert len(read('production-preview-verification.json')['responses'])==36 and len(read('launcher-and-http.json')['responses'])==36
for name in ['candidate-archive-manifest.json','baseline-archive-manifest.json']:
    m=read(name);path=OUT/m['file'];assert sha(path)==m['sha256']
    with tarfile.open(path)as t:
        assert len(t.getmembers())==len(m['files'])==113
        for n,v in m['files'].items():
            assert hashlib.sha256(t.extractfile(n).read()).hexdigest()==v['sha256']
            if name=='candidate-archive-manifest.json':assert sha(ROOT/n)==v['sha256']
manifest_path=ROOT/'release'/f'{candidate}-manifest.json';release=json.loads(manifest_path.read_text());assert release['candidateId']==candidate and release['independentUnzip']=='passed'
assert release['verificationReportSha256']==sha(OUT/'package-verification.json')
assert all(sha(ROOT/n)==v for n,v in release['deliveryInputsSha256'].items())
for kind,meta in release['packages'].items():
    path=ROOT/meta['file'];assert sha(path)==meta['sha256']and path.stat().st_size==meta['bytes']
    with zipfile.ZipFile(path)as z:
        pm=json.loads(z.read('PACKAGE-MANIFEST.json'));assert pm['candidateId']==candidate and pm['kind']==kind
        assert len(z.namelist())==meta['files']and set(z.namelist())==set(pm['files'])|{'PACKAGE-MANIFEST.json'}
        if kind=='source':
            for n,v in pm['files'].items():
                if(ROOT/n).is_file()and n!='README.md':assert sha(ROOT/n)==v['sha256'],('Source changed after packaging',n)
pkg=read('package-verification.json');assert pkg['sourceStrictBuildByteIdentical']and pkg['sourceInitiallyHadNoNodeModules']and pkg['zipEntryIntegrityAfterBuildAndBrowserChecks']
for kind in ['source','site']:
    d=read(f'unpacked-{kind}-browser.json');assert len(d['checks'])==2 and not d['errors']and{'dist/'+n:v for n,v in d['productionSha256'].items()}==build['productionSha256']
before=read('before-files.json')['files'];changed=sorted(n for n,v in before.items()if not(ROOT/n).is_file()or sha(ROOT/n)!=v['sha256'])
assert set(changed)=={'docs/garden-enhancement/step-7-standard.md','docs/garden-enhancement/progress.md'},changed
paths=set(subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=ROOT).decode().strip('\0').split('\0'))
paths|={p.relative_to(ROOT).as_posix()for p in (ROOT/'release').glob(f'{candidate}-*')}
paths|={str((OUT/n).relative_to(ROOT))for n in ['scope-guard.json','result-binding.json','evidence-manifest.json','summary.json']}
added=sorted(n for n in paths-set(before)if n)
allowed_files={'START-PREVIEW.cmd','START-DEV.cmd','scripts/preview-site.mjs','scripts/package-garden-enhancement.py',
    *[f'docs/garden-enhancement/{n}'for n in ['quickstart.md','maintenance.md','delivery.md','step-7-implementation.md','step-7-verification.md']]}
def allowed(n):return n in allowed_files or n.startswith(('docs/evidence/garden-enhancement-step-7/','tests/garden-enhancement/step7_','release/'+candidate+'-'))
assert all(allowed(n)for n in added),[n for n in added if not allowed(n)]
seals=[]
for step,count in [(1,79),(2,355),(3,226),(4,235),(5,310),(6,223)]:
    p=ROOT/f'docs/evidence/garden-enhancement-step-{step}/evidence-manifest.json';m=json.loads(p.read_text())
    assert len(m['files'])==count and sha(p)==next(r['manifestSha256']for r in baseline['oldSeals']if r['step']==step)
    assert all(sha(ROOT/n)==v['sha256']for n,v in m['files'].items())
    seals.append({'step':step,'verifiedFiles':count,'manifestSha256':sha(p)})
assert all(sha(ROOT/n)==v['sha256']for n,v in baseline['oldReleaseFiles'].items())and len(baseline['oldReleaseFiles'])==10
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip();assert head==baseline['gitHead']
save('scope-guard.json',{'passed':True,'candidateId':candidate,'frozenBeforeFiles':len(before),'changedExisting':changed,'addedFiles':added,'oldSeals':seals,'oldReleaseFiles':baseline['oldReleaseFiles'],
    'application92InputsAnd18OutputsUnchanged':True,'gitHeadUnchanged':head,'oldReleaseArchivesOverwritten':False,'committed':False,'pushed':False,'deployed':False})
links=[];planned={OUT/n for n in ['summary.json','result-binding.json','evidence-manifest.json']}
docs=['step-7-standard.md','step-7-implementation.md','step-7-verification.md','quickstart.md','maintenance.md','delivery.md','progress.md']
for name in docs:
    p=ROOT/'docs/garden-enhancement'/name
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
        if target.startswith(('http:','https:','#','skill:')):continue
        local=(p.parent/target.split('#')[0]).resolve();assert local.is_file()or local in planned,(p,target)
        links.append({'document':p.relative_to(ROOT).as_posix(),'target':target})
save('result-binding.json',{'passed':True,'candidateId':candidate,'baselineId':baseline['candidateId'],'buildInputFingerprint':finger,'productionFiles':build['productionSha256'],
    'reports':{n:sha(OUT/n)for n in reports+['build-verification.json','scope-guard.json','video-frame-origins.json']},'releaseManifest':manifest_path.relative_to(ROOT).as_posix(),'releaseManifestSha256':sha(manifest_path),
    'packages':release['packages'],'documentLinks':links,'windowsRuntimeTested':False,'physicalDevicePending':True,'committed':False,'pushed':False,'deployed':False})
files=[p for p in OUT.rglob('*')if p.is_file()and p not in{OUT/'evidence-manifest.json',OUT/'summary.json'}]
files += [ROOT/'docs/garden-enhancement'/n for n in docs if n!='progress.md']
files += [p for p in (ROOT/'tests/garden-enhancement').glob('step7_*')if p.is_file()]
files += [ROOT/n for n in ['START-PREVIEW.cmd','START-DEV.cmd','scripts/preview-site.mjs','scripts/package-garden-enhancement.py']]
files += [ROOT/v['file']for v in release['packages'].values()]+[manifest_path]
seal={'schema':1,'candidateId':candidate,'files':{p.relative_to(ROOT).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(set(files))}}
save('evidence-manifest.json',seal)
save('summary.json',{'passed':True,'completedStep':7,'allSevenStepsCompleteInCurrentEnvironment':True,'candidateId':candidate,'baselineId':baseline['candidateId'],
    'completedAtUtc':datetime.datetime.now(datetime.UTC).isoformat(),'currentEnvironmentGates':{f'K{i:02d}':True for i in range(1,19)},'immutableArtifacts':len(seal['files']),
    'evidenceManifestSha256':sha(OUT/'evidence-manifest.json'),'mutableProgressExcluded':'docs/garden-enhancement/progress.md','gitHead':head,'committed':False,'pushed':False,'deployed':False,
    'physicalDevicePending':True,'windowsRuntimeTested':False,'packages':release['packages'],'releaseManifest':manifest_path.relative_to(ROOT).as_posix(),'verification':'../../garden-enhancement/step-7-verification.md'})
assert all(sha(ROOT/n)==v['sha256']for n,v in seal['files'].items())
for r in links:assert(ROOT/r['document']).parent.joinpath(r['target'].split('#')[0]).resolve().is_file()
print('PASS final Step7 K01-K18',candidate,len(seal['files']),'sealed artifacts;',len(links),'links;1428historical files and10old releases unchanged;3independent ZIPs;no Git/remote publication')
