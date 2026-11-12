"""Verify authorized step-5 deltas, pinned original bytes and accepted UI runs."""
from pathlib import Path
from datetime import datetime,timezone
import difflib,hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/lawson-fullpage-step-5'
MODIFIED={'src/tour/createProjectViewer.ts','src/tour/startTourPrototype.ts','src/tour/projectHost.css'}
NEW={'src/tour/createLawsonExperience.ts'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def row(p):return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
def write(name,data):(OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def git(path,*args):return subprocess.check_output(['git','-C',str(path),*args],text=True).strip()

baseline=read(OUT/'baseline.json');assert git(ROOT,'rev-parse','HEAD')==baseline['head']
history=[]
for seal_info in baseline['oldSeals']:
    p=ROOT/seal_info['path'];assert sha(p)==seal_info['sha256'];seal=read(p)
    assert len(seal['files'])==seal_info['fileCount']
    for f in seal['files']:assert row(ROOT/f['path'])==f,f['path']
    history.append({**seal_info,'allFilesUnchanged':True})
manifest_path=ROOT/baseline['runtimeManifest'];assert sha(manifest_path)==baseline['runtimeManifestSHA256']
manifest=read(manifest_path);assert len(manifest['runtimeFiles'])==46
source=ROOT.parent/'luosen-asset/lawson-blender/out/web_final'
assert git(source,'rev-parse','HEAD')==baseline['sourceHead']
assert git(source,'status','--short')==baseline['sourceStatusBefore']==''
runtime=[]
for directory in [source,ROOT/'public/experiments/lawson',ROOT/'dist/experiments/lawson']:
    if directory!=source:
        assert sorted(p.relative_to(directory).as_posix()for p in directory.rglob('*')if p.is_file())==sorted(f['path']for f in manifest['runtimeFiles'])
    for f in manifest['runtimeFiles']:
        p=directory/f['path'];assert p.stat().st_size==f['bytes']and sha(p)==f['sha256'],p
    runtime.append({'path':str(directory),'fileCount':46,'bytes':sum(f['bytes']for f in manifest['runtimeFiles']),'allSHA256Match':True})
changed=[];unchanged=[]
for before in baseline['hostInputsBefore']:
    actual=row(ROOT/before['path'])
    (changed if actual!=before else unchanged).append({'before':before,'after':actual}if actual!=before else actual)
assert {r['after']['path']for r in changed}==MODIFIED
build=read(OUT/'build-result.json');assert build['exitCode']==0 and build['includesTypecheck']
assert {r['path']for r in build['productionInputs']}==MODIFIED|NEW
for f in build['productionInputs']+build['builtFiles']:assert row(ROOT/f['path'])==f,f['path']
first=read(OUT/'build-1-result.json')
for f in first['productionInputs']:
    if f['path']!='src/tour/projectHost.css':assert row(ROOT/f['path'])==f
css_before=(OUT/'feedback-before.css').read_text();css_after=(ROOT/'src/tour/projectHost.css').read_text()
assert css_before.replace('.tour-project-feedback { flex:', '.tour-project-dialog[data-project-id="lawson"] .tour-project-feedback { flex:')==css_after
assert read(OUT/'build-delta.json')['passed']
subprocess.run(['git','-C',str(ROOT),'diff','--check'],check=True)
patch=[]
for p in sorted(MODIFIED|NEW):
    old=(OUT/'before'/p).read_text().splitlines(keepends=True)if p in MODIFIED else []
    patch.extend(difflib.unified_diff(old,(ROOT/p).read_text().splitlines(keepends=True),fromfile='a/'+p,tofile='b/'+p))
(OUT/'host-changes.patch').write_text(''.join(patch))

latest={};attempts=[]
for run,build_log in [('run-1','build-1.log'),('run-2','build-1.log'),('run-3','build-2.log'),('run-4','build-2.log')]:
    r=read(OUT/run/'browser.json')
    assert not r['pageErrors']and not r['httpErrors']
    assert not r.get('unexpectedFailedRequests',[])and not r.get('unexpectedConsoleErrors',[])
    if run=='run-1':assert not r['failedRequests']and not r['consoleErrors']
    for case in r['checks']:latest[case['name']]={'report':run+'/browser.json','build':build_log,**case}
    attempts.append({'report':run+'/browser.json','passed':r['passed'],'checks':len(r['checks']),
        'failedChecks':[c['name']for c in r['checks']if not c['passed']]})
assert len(latest)==15 and all(c['passed']for c in latest.values()),[(n,c['passed'])for n,c in latest.items()]
write('accepted-browser-results.json',{'passed':True,'acceptedGroups':len(latest),'groups':list(latest.values()),'allAttemptsPreserved':attempts,
    'finalBuild':build['log'],'unchangedJavaScriptAcrossBuilds':True,'onlyBuildDelta':'build-delta.json',
    'testCorrections':['Pending slow route must continue once; removing its handler first already handled it (run2).','Pointer lock is read from the owning child document; the parent getter is null in this browser (run2).'],
    'environment':{'browser':r['browser'],'backend':'Headful Chromium, Mesa software GL','physicalMobile':False,'hardwarePerformanceProof':False},
    'productionBridgeOrRuntimeInjected':False,'testOnlyDrawCounters':True,'testOnlyNetworkFaults':True,
    'nativeFullscreenAndPointerLockEscape':'X11 Escape, not synthetic DOM key events'})
write('integrity.json',{'passed':True,'capturedAtUTC':datetime.now(timezone.utc).isoformat(),'hostHead':baseline['head'],'sourceHead':baseline['sourceHead'],
    'oldSeals':history,'runtime':runtime,'hostInputsBefore':94,'authorizedModifiedInputs':changed,'untouchedInputCount':len(unchanged),'untouchedInputs':unchanged,
    'newProductionFiles':[row(ROOT/p)for p in NEW],'build':build['log'],'buildPassed':True,'gitDiffCheckPassed':True,'acceptedBrowserGroups':len(latest),
    'originalRuntimeChanged':False,'originalWorkingTreeClean':True,'committed':False,'pushed':False,'published':False})
print(json.dumps({'passed':True,'originalRuntimeFiles':46,'oldSealFileCounts':[s['fileCount']for s in history],
    'changedExistingInputs':len(changed),'untouchedExistingInputs':len(unchanged),'newProductionFiles':len(NEW),'acceptedBrowserGroups':len(latest)},ensure_ascii=False))
