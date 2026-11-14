"""Pin untouched original and existing host inputs before standalone inspection."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json,shutil,subprocess
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT.parent/'Beach-Bottle-Boat';OUT=ROOT/'docs/evidence/beach-bottle-boat-step-1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def git(p,*a):return subprocess.check_output(['git','-C',str(p),*a],text=True).strip()
def row(p,base=ROOT):return {'path':p.relative_to(base).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
assert not(OUT/'baseline.json').exists(),'Preserve the baseline'
OUT.mkdir(parents=True,exist_ok=True)
host=read(ROOT/'docs/evidence/lawson-fullpage-step-7/candidate-manifest.json')
for f in host['productionInputs']:assert row(ROOT/f['path'])==f
seal=ROOT/'docs/evidence/lawson-fullpage-step-7/evidence-manifest.json';old=read(seal)['previousSeals']+[{'path':seal.relative_to(ROOT).as_posix(),'sha256':sha(seal),'fileCount':750}]
for s in old:
 p=ROOT/s['path'];assert sha(p)==s['sha256'];data=read(p);assert len(data['files'])==s['fileCount']
 for f in data['files']:assert row(ROOT/f['path'])==f,f['path']
assert git(SOURCE,'status','--short')==''
assert sha(SOURCE/'index.html')==sha(SOURCE/'bottle_ocean_sandbox.html')=='941feb2ea6ddd3cc93aad5b0b92dbca52ee66a3e1098fee0dbf16f01ca63d1ef'
files=[row(p,SOURCE)for p in sorted(SOURCE.rglob('*'))if p.is_file()and'.git'not in p.parts]
lawson=read(ROOT/'docs/evidence/lawson-fullpage-step-1/runtime-manifest.json')['runtimeFiles']
for f in lawson:
 p=ROOT/'public/experiments/lawson'/f['path'];assert p.stat().st_size==f['bytes']and sha(p)==f['sha256']
standard=ROOT/'docs/beach-bottle-boat/step-1-standard.md';shutil.copyfile(standard,OUT/'standard-before.md')
baseline={'schema':1,'capturedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'hostCommit':git(ROOT,'rev-parse','HEAD'),'sourceCommit':git(SOURCE,'rev-parse','HEAD'),'hostStatusBefore':git(ROOT,'status','--short'),'sourceStatusBefore':'','hostProductionInputs':host['productionInputs'],'originalFiles':files,'originalEntry':row(SOURCE/'index.html',SOURCE),'oldSeals':old,'lawsonRuntimeFiles':lawson,'standardBeforeSHA256':sha(standard),'originalNotRebuilt':True,'hostApplicationNotChanged':True}
(OUT/'baseline.json').write_text(json.dumps(baseline,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'baselineCaptured':True,'originalFiles':len(files),'protectedHostProductionInputs':len(host['productionInputs']),'protectedLawsonRuntimeFiles':len(lawson),'oldSealsVerified':len(old)}))
