"""Seal only Step3 review artifacts after actual gates pass. No Git/remote writes.
Older evidence, releases, CSS and unrelated sources are verified, never rewritten.
"""
from pathlib import Path
import datetime
import hashlib
import json
import re
import subprocess
import tarfile

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/evidence/garden-enhancement-step-3'
def read(name):return json.loads((OUT/name).read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(name,value):(OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
build=read('build-verification.json');baseline=read('baseline-version.json')
candidate=build['candidateId']
assert all(sha(ROOT/n)==v for n,v in build['buildInputsSha256'].items())
assert {str(p.relative_to(ROOT)):sha(p)for p in sorted((ROOT/'dist').rglob('*'))if p.is_file()}==build['productionSha256']
assert build['passed']and build['exitCode']==0 and build['finalRebuildByteIdenticalToTestedBuild']
reports=['browser-chromium-before.json','browser-chromium-after.json','browser-firefox-after.json','browser-webkit-after.json',
         'geometry-physics.json','world-protection.json','protected-raster-pairs.json','native-recovery.json','orb-context-longtime.json',
         'production-preview-verification.json','performance-comparison.json','water-orb-recording-before.json','water-orb-recording-after.json','service-lifecycle.json']
for name in reports:assert read(name)['passed'],name
field=read('surface-field-highlights.json');assert field['field']['passed']and field['highlights']['passed']
for engine in ['chromium','firefox','webkit']:
    d=read(f'browser-{engine}-after.json');assert d['candidateId']==candidate and len(d['fixedFrames'])==26
    assert len(d['clockViewerReading'])==3 and len(d['resources'])==3 and len(d['capacityAndPreference'])==4
for phase in ['before','after']:
    d=read(f'water-orb-recording-{phase}.json');assert d['candidateId']==(candidate if phase=='after'else baseline['candidateId'])
    assert (OUT/d['file']).is_file()
archive=read('candidate-archive-manifest.json')
assert sha(OUT/archive['file'])==archive['sha256']
with tarfile.open(OUT/archive['file'])as t:
    assert len(t.getmembers())==len(archive['files'])
    for name,value in archive['files'].items():
        assert hashlib.sha256(t.extractfile(name).read()).hexdigest()==value['sha256']
        assert sha(ROOT/name)==value['sha256'],('archive/current mismatch',name)
before=read('before-files.json')['files']
allowed={'src/config/orb.ts','src/animation/orbMotion.ts','src/materials/createOrbMaterial.ts','src/scene/createLivelyFountainEffects.ts',
         'docs/garden-enhancement/step-3-standard.md','docs/garden-enhancement/progress.md'}
changed=[n for n,v in before.items()if not(ROOT/n).is_file()or sha(ROOT/n)!=v['sha256']]
assert not set(changed)-allowed,changed
paths=set(subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=ROOT).decode().strip('\0').split('\0'))
paths|={str((OUT/n).relative_to(ROOT))for n in ['scope-guard.json','result-binding.json','evidence-manifest.json','summary.json']}
added=sorted(n for n in paths-set(before)if n)
def allowed_new(name):
    return name=='src/animation/orbSurface.ts'or name.startswith('docs/evidence/garden-enhancement-step-3/')or name in{
        'docs/garden-enhancement/step-3-implementation.md','docs/garden-enhancement/step-3-verification.md'}or(
        name.startswith('tests/garden-enhancement/step3_')or name in{
            'tests/garden-enhancement/inspect_orb_flow.js','tests/garden-enhancement/inspect_world_contract.js',
            'tests/garden-enhancement/inspect_flow_field.js','tests/garden-enhancement/inspect_orb_cost.js'})
assert all(allowed_new(n)for n in added),[n for n in added if not allowed_new(n)]
old_seals=[]
for step in [1,2]:
    p=ROOT/f'docs/evidence/garden-enhancement-step-{step}/evidence-manifest.json';d=json.loads(p.read_text())
    assert all(sha(ROOT/n)==v['sha256']for n,v in d['files'].items())
    old_seals.append({'step':step,'manifestSha256':sha(p),'verifiedFiles':len(d['files'])})
releases={n:v for n,v in before.items()if n.startswith('release/')}
assert all(sha(ROOT/n)==v['sha256']for n,v in releases.items())
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
assert head==baseline['gitHead']
css={n:sha(ROOT/n)for n in ['src/tour/tour.css','src/tour/readingLayout.css']}
assert all(v==before[n]['sha256']for n,v in css.items())
save('scope-guard.json',{'passed':True,'candidateId':candidate,'frozenBeforeFiles':len(before),'changedExisting':changed,
    'allowedNewFileCount':len(added),'cssProtectedSha256':css,'oldSeals':old_seals,'oldReleaseFiles':releases,
    'gitHeadUnchanged':head,'autoTourImplemented':False,'cloudShadowImplemented':False,'birdsImplemented':False,
    'oldReleaseArchivesOverwritten':False,'committed':False,'pushed':False,'deployed':False})
links=[]
for name in ['step-3-standard.md','step-3-implementation.md','step-3-verification.md','progress.md']:
    p=ROOT/'docs/garden-enhancement'/name
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',p.read_text()):
        if target.startswith(('http:','https:','#','skill:')):continue
        local=(p.parent/target.split('#')[0]).resolve()
        assert local.is_file()or local in{OUT/'evidence-manifest.json',OUT/'summary.json'},(p,target)
        links.append({'document':str(p.relative_to(ROOT)),'target':target})
save('result-binding.json',{'passed':True,'candidateId':candidate,'baselineId':baseline['candidateId'],
    'buildInputFingerprint':build['buildInputFingerprint'],'productionFiles':build['productionSha256'],
    'candidateArchiveSha256':archive['sha256'],'reports':{n:sha(OUT/n)for n in reports},'documentLinks':links,
    'initialTimingFlagPreserved':{'file':'performance-initial-comparison.json','passed':False,'supersededBy':'performance-comparison.json'},
    'physicalDevicePending':['iOS Safari/Android real devices','hardware GPU frame rate','VoiceOver/TalkBack','system font scaling and safe areas','physical trackpad/APZ']})
# Intermediate checkpoints remain named as such and are not acceptance reports.
files=[p for p in OUT.rglob('*')if p.is_file()and p.name not in {'evidence-manifest.json','summary.json'}]
files += [ROOT/'docs/garden-enhancement'/n for n in ['step-3-standard.md','step-3-implementation.md','step-3-verification.md']]
files += [p for p in (ROOT/'tests/garden-enhancement').glob('*')if p.is_file()and(p.name.startswith('step3_')or p.name in{
    'inspect_orb_flow.js','inspect_world_contract.js','inspect_flow_field.js','inspect_orb_cost.js'})]
manifest={'schema':1,'candidateId':candidate,'files':{str(p.relative_to(ROOT)):{'bytes':p.stat().st_size,'sha256':sha(p)}for p in sorted(set(files))}}
save('evidence-manifest.json',manifest)
summary={'passed':True,'completedStep':3,'candidateId':candidate,'baselineId':baseline['candidateId'],
    'completedAtUtc':datetime.datetime.now(datetime.UTC).isoformat(),'currentEnvironmentGates':{f'G{i:02d}':True for i in range(1,19)},
    'immutableArtifacts':len(manifest['files']),'evidenceManifestSha256':sha(OUT/'evidence-manifest.json'),
    'mutableProgressExcluded':'docs/garden-enhancement/progress.md','step4Started':False,'step5Started':False,'step6Started':False,
    'gitHead':head,'committed':False,'pushed':False,'deployed':False,'physicalDevicePending':True,
    'video':'water-orb-after.mp4','verification':'../../garden-enhancement/step-3-verification.md'}
save('summary.json',summary)
assert all(sha(ROOT/n)==v['sha256']for n,v in manifest['files'].items())
for link in links:
    assert (ROOT/link['document']).parent.joinpath(link['target'].split('#')[0]).resolve().is_file()
print('PASS Step3 G01-G18:',candidate,';',len(manifest['files']),'sealed artifacts;',len(links),'valid document links; no Git/remote actions.')
