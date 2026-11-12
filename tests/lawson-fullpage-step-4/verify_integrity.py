"""Read-only source/runtime/history audit, writing only step-4 evidence."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/evidence/lawson-fullpage-step-4'
SOURCE=ROOT.parent/'luosen-asset/lawson-blender/out/web_final'
MODIFIED={f'src/tour/{name}.ts' for name in [
    'createExperimentReader','createMediaViewer','createProjectViewer',
    'experimentReading','startTourPrototype','autoGuide',
]}
NEW={'src/tour/projectContent.ts','src/tour/projectHost.css','src/assets/lawson-cover.png'}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())
def row(path):return {'path':path.relative_to(ROOT).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)}
def git(directory,*args):return subprocess.check_output(['git','-C',str(directory),*args],text=True).strip()
def write(name,data):(OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

baseline=read(OUT/'baseline.json')
assert git(ROOT,'rev-parse','HEAD')==baseline['head']
history=[]
for item in baseline['oldSeals']:
    path=ROOT/item['path'];assert sha(path)==item['sha256'],path
    seal=read(path);assert seal['fileCount']==item['fileCount']==len(seal['files'])
    for f in seal['files']:
        p=ROOT/f['path'];assert p.stat().st_size==f['bytes'] and sha(p)==f['sha256'],p
    history.append({**item,'manifestUnchanged':True,'allSealedFilesUnchanged':True})

manifest_path=ROOT/baseline['runtimeManifest'];manifest=read(manifest_path)
assert sha(manifest_path)=='f33ad8e769c37cbc034542b0ced3fba76dcbac7f01844e9e7504ab32d3d2e696'
assert git(SOURCE,'rev-parse','HEAD')==manifest['sourceCommit']
expected=manifest['runtimeFiles'];assert len(expected)==46
runtime=[]
for directory in [SOURCE,ROOT/'public/experiments/lawson',ROOT/'dist/experiments/lawson']:
    if directory!=SOURCE:
        actual=sorted(p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file())
        assert actual==sorted(f['path']for f in expected),directory
    for f in expected:
        p=directory/f['path'];assert p.stat().st_size==f['bytes']and sha(p)==f['sha256'],p
    runtime.append({'root':str(directory),'fileCount':len(expected),'totalBytes':sum(f['bytes']for f in expected),'allSHA256MatchPinnedManifest':True})

changed=[];unchanged=[]
for before in baseline['hostInputsBefore']:
    after=row(ROOT/before['path'])
    (changed if after!=before else unchanged).append({'before':before,'after':after}if after!=before else after)
assert {r['after']['path']for r in changed}==MODIFIED
assert set(git(ROOT,'diff','--name-only').splitlines())==MODIFIED
assert all((ROOT/p).is_file()for p in NEW)
assert sha(ROOT/'src/assets/lawson-cover.png')==sha(ROOT/'docs/evidence/lawson-fullpage-step-2/assets/lawson-hero.png')
subprocess.run(['git','-C',str(ROOT),'diff','--check'],check=True)
(OUT/'host-changes.patch').write_text(git(ROOT,'diff','--',*sorted(MODIFIED))+'\n')
# These additional modules were identified by the media and copy audits.
for name in ['createMediaViewer.ts','autoGuide.ts']:
    before=OUT/'before/src/tour'/name;relative='src/tour/'+name
    if not before.exists():before.write_bytes(subprocess.check_output(['git','-C',str(ROOT),'show',baseline['head']+':'+relative]))
    assert sha(before)==next(f['sha256']for f in baseline['hostInputsBefore']if f['path']==relative)

# The final build changed only two descriptions after the broad build-4 run.
# Prove the exact text-only delta before reusing its unaffected 17 groups.
build4=read(OUT/'build-4-result.json')
for f in build4['productionInputs']:
    if f['path']!='src/tour/startTourPrototype.ts':assert row(ROOT/f['path'])==f
old_start=OUT/'label-audit/startTourPrototype.ts';old_guide=OUT/'label-audit/autoGuide.ts'
assert sha(old_start)==next(f['sha256']for f in build4['productionInputs']if f['path']=='src/tour/startTourPrototype.ts')
assert sha(old_guide)==next(f['sha256']for f in baseline['hostInputsBefore']if f['path']=='src/tour/autoGuide.ts')
replacements=[(old_start,'第三柱交互实验与真实庭院体验','第三柱交互实验与罗森、庭院体验'),
    (old_guide,"C2: ['交互实验 · 庭院'","C2: ['交互实验 · 交互作品'")]
for before,old,new in replacements:
    text=before.read_text();assert text.count(old)==1
    assert text.replace(old,new)==(ROOT/'src/tour'/before.name).read_text()
write('label-audit/result.json',{'passed':True,'build4ToBuild5OnlyChanges':[
    {'path':'src/tour/'+p.name,'beforeSHA256':sha(p),'afterSHA256':sha(ROOT/'src/tour'/p.name),'from':a,'to':b}for p,a,b in replacements],
    'changesAreDescriptionsOnly':True,'targetedFinalBrowserReport':'run-5/host.json'})

run2=read(OUT/'run-2/host.json');run3=read(OUT/'run-3/host.json');run5=read(OUT/'run-5/host.json')
for run in [run2,run3,run5]:
    for field in ['pageErrors','httpErrors','unexpectedFailedRequests','mainRuntimeRequests']:assert not run[field],field
assert len(run2['checks'])==18 and len(run3['checks'])==1
assert [c['name']for c in run2['checks']if not c['passed']]==['guide resize and playing restoration']
assert run3['checks'][0]['passed']and run3['checks'][0]['name']=='guide resize and playing restoration'
assert run5['passed']and len(run5['checks'])==1
accepted=[{'report':'run-2/host.json',**c}for c in run2['checks']if c['passed']]+[{'report':'run-5/host.json',**c}for c in run5['checks']]
assert len(accepted)==18
write('accepted-browser-results.json',{'passed':True,'acceptedGroups':18,'groups':accepted,
    'historicalAttemptsPreserved':['run-1','run-2','run-3','run-4','run-5'],
    'testCorrections':['Stable C2 locator restricted to article (run1).','Guide resume assertion uses the existing running status, rather than playing (run2).','Copy audit reads the actual button title instead of hidden tooltip innerText (run4).'],
    'broadBuild':'build-4.log','finalBuild':'build-5.log','finalCodeChangedAfterBuild':False,
    'descriptionOnlyBuildDelta':'label-audit/result.json',
    'browser':run2['browser'],'webGLBackend':'Headful Chromium, Mesa software GL via ANGLE',
    'limitations':['No real iframe in step4.','Viewport and root font emulation are not physical phone or OS text scaling tests.','Retired image events and rapid owner overlap include explicitly labelled synthetic fault injections.']})

result={'schema':1,'capturedAtUTC':datetime.now(timezone.utc).isoformat(),'passed':True,
    'hostHead':baseline['head'],'sourceHead':manifest['sourceCommit'],
    'oldSeals':history,'runtimeManifestSHA256':sha(manifest_path),'runtime':runtime,
    'hostInputsBefore':len(baseline['hostInputsBefore']),'authorizedModifiedInputs':changed,
    'untouchedInputs':unchanged,'untouchedInputCount':len(unchanged),
    'newProductionFiles':[row(ROOT/p)for p in sorted(NEW)],
    'trackedChangedFiles':sorted(MODIFIED),'buildLog':'build-5.log','buildExitCode':0,
    'buildExitCodeSource':'Successful exec_command completion recorded during this turn; build script includes tsc --noEmit.',
    'gitDiffCheckPassed':True,'acceptedBrowserGroups':len(accepted),
    'sourceWorkingTreeStatus':git(SOURCE,'status','--short'),
    'published':False,'committedOrPushedByThisStep':False}
write('integrity.json',result)
write('build-result.json',{'command':'npm run build','log':'build-5.log','exitCode':0,
    'includesTypecheck':True,'productionInputs':[row(ROOT/p)for p in sorted(MODIFIED|NEW)],
    'builtFiles':[row(p)for p in sorted((ROOT/'dist').rglob('*'))if p.is_file()]})
print(json.dumps({'passed':True,'runtimeFilesPerCopy':46,'historyFileCounts':[x['fileCount']for x in history],
    'modifiedHostInputs':len(changed),'untouchedHostInputs':len(unchanged),'newProductionFiles':len(NEW),'acceptedBrowserGroups':len(accepted)},ensure_ascii=False))
