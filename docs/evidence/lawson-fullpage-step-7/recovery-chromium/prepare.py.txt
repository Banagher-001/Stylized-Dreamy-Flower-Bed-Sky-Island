"""Capture the step-7 inputs and verify, without rewriting earlier evidence."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json,shutil,subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/evidence/lawson-fullpage-step-7'
OLD=ROOT/'docs/evidence/lawson-fullpage-step-6'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
git=lambda d,*a:subprocess.check_output(['git','-C',str(d),*a],text=True).strip()
def row(p):return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
assert not (OUT/'baseline.json').exists(),'Keep the baseline; do not overwrite it'
OUT.mkdir(parents=True,exist_ok=True)
previous=read(OLD/'baseline.json')['oldSeals']
previous.append({'path':str((OLD/'evidence-manifest.json').relative_to(ROOT)),'fileCount':315,'sha256':'fa5a9557e129cabe1f9e893ea4a6b00937caff6b039e87669808d1d478515474'})
for seal in previous:
    path=ROOT/seal['path'];assert sha(path)==seal['sha256']
    data=read(path);assert len(data['files'])==seal['fileCount']
    for f in data['files']:assert row(ROOT/f['path'])==f,f['path']
inputs=read(OLD/'build-result.json')['productionInputs']+read(OLD/'integrity.json')['untouchedInputs']
assert len(inputs)==95
for f in inputs:assert row(ROOT/f['path'])==f,f['path']
source=ROOT.parent/'luosen-asset'
assert git(source,'status','--short')==''
manifest=ROOT/'docs/evidence/lawson-fullpage-step-1/runtime-manifest.json'
runtime=read(manifest)['runtimeFiles']
for directory in [source/'lawson-blender/out/web_final',ROOT/'public/experiments/lawson']:
    for f in runtime:
        p=directory/f['path'];assert p.stat().st_size==f['bytes']and sha(p)==f['sha256'],str(p)
standard=ROOT/'docs/lawson-fullpage/step-7-standard.md'
shutil.copyfile(standard,OUT/'standard-before.md')
baseline={'schema':1,'capturedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
 'hostCommit':git(ROOT,'rev-parse','HEAD'),'sourceCommit':git(source,'rev-parse','HEAD'),
 'statusBefore':git(ROOT,'status','--short'),'sourceStatusBefore':'','productionInputs':sorted(inputs,key=lambda r:r['path']),
 'previousSeals':previous,'runtimeManifest':str(manifest.relative_to(ROOT)),'runtimeManifestSHA256':sha(manifest),
 'runtimeFiles':len(runtime),'runtimeBytes':sum(f['bytes']for f in runtime),'standardBeforeSHA256':sha(standard),
 'node':subprocess.check_output(['node','--version'],text=True).strip(),'npm':subprocess.check_output(['npm','--version'],text=True).strip(),
 'committed':False,'pushed':False,'published':False}
(OUT/'baseline.json').write_text(json.dumps(baseline,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'baselineCaptured':True,'productionInputs':len(inputs),'historicalSealsVerified':len(previous),'originalFiles':len(runtime)}))
