"""Strict final application build; delivery tools have separate package hashes."""
from pathlib import Path
import hashlib,json,subprocess,tarfile
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/garden-enhancement-step-7'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
with(OUT/'build.log').open('w')as log:subprocess.run(['npm','run','build'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
old=json.loads((ROOT/'docs/evidence/garden-enhancement-step-6/build-verification.json').read_text())
inputs={n:sha(ROOT/n)for n in old['buildInputsSha256']}
finger=hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest();candidate='garden-enhancement-step7-'+finger[:16]
production={str(p.relative_to(ROOT)):sha(p)for p in sorted((ROOT/'dist').rglob('*'))if p.is_file()}
build={'passed':True,'candidateId':candidate,'baselineId':old['candidateId'],'buildInputFingerprint':finger,'buildInputsSha256':inputs,'productionSha256':production,
    'changedRuntimeSources':[n for n,v in inputs.items()if n.startswith('src/')and old['buildInputsSha256'].get(n)!=v],
    'applicationInputsIdenticalToStep6':inputs==old['buildInputsSha256'],'productionIdenticalToStep6':production==old['productionSha256'],
    'command':'npm run build (strict typecheck included)','exitCode':0,'log':'build.log','node':subprocess.check_output(['node','-v'],text=True).strip(),'npm':subprocess.check_output(['npm','--version'],text=True).strip()}
archive_old=json.loads((ROOT/'docs/evidence/garden-enhancement-step-6/candidate-archive-manifest.json').read_text())
names=sorted({n for n in archive_old['files']if not n.startswith('dist/')}|set(production));archive=OUT/'candidate-source-site.tar.gz'
with tarfile.open(archive,'w:gz')as t:
    for n in names:t.add(ROOT/n,arcname=n,recursive=False)
manifest={'candidateId':candidate,'file':archive.name,'bytes':archive.stat().st_size,'sha256':sha(archive),'files':{n:{'bytes':(ROOT/n).stat().st_size,'sha256':sha(ROOT/n)}for n in names}}
save('build-verification.json',build);save('candidate-archive-manifest.json',manifest)
print('PASS',candidate,len(inputs),'inputs',len(production),'outputs','same application as Step6:',build['productionIdenticalToStep6'])
