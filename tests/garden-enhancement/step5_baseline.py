"""Freeze Step4 and read-only historical seals before changing any product input."""
from pathlib import Path
import datetime,hashlib,json,subprocess,tarfile
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/garden-enhancement-step-5'
OUT.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
assert not(OUT/'baseline-version.json').exists(),'Baseline must not be overwritten'
old=ROOT/'docs/evidence/garden-enhancement-step-4';build=json.loads((old/'build-verification.json').read_text())
assert all(sha(ROOT/n)==v for n,v in build['buildInputsSha256'].items())
seals=[]
for step,count in [(1,79),(2,355),(3,226),(4,235)]:
    p=ROOT/f'docs/evidence/garden-enhancement-step-{step}/evidence-manifest.json';d=json.loads(p.read_text())
    assert len(d['files'])==count and all(sha(ROOT/n)==v['sha256']for n,v in d['files'].items())
    seals.append({'step':step,'manifestSha256':sha(p),'verifiedFiles':count})
archive=json.loads((old/'candidate-archive-manifest.json').read_text())
assert sha(old/archive['file'])==archive['sha256']
destination=Path('/tmp/garden-enhancement-step5-before');destination.mkdir(exist_ok=True)
with tarfile.open(old/archive['file'])as t:
    assert len(t.getmembers())==104
    t.extractall(destination,filter='data')
assert all(sha(destination/n)==v['sha256']for n,v in archive['files'].items())
names=set(subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=ROOT).decode().strip('\0').split('\0'))
# The baseline helper is this step's own new artifact, not part of the prior tree.
names={n for n in names if n and not n.startswith('docs/evidence/garden-enhancement-step-5/')and n!='tests/garden-enhancement/step5_baseline.py'}
files={n:{'bytes':(ROOT/n).stat().st_size,'sha256':sha(ROOT/n)}for n in sorted(names)if(ROOT/n).is_file()}
save('before-files.json',{'files':files})
save('baseline-version.json',{'createdAtUtc':datetime.datetime.now(datetime.UTC).isoformat(),'candidateId':build['candidateId'],
    'gitHead':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),'oldSeals':seals,'beforeFiles':len(files),
    'baselineArchiveSha256':archive['sha256'],'archiveMembers':104,'independentBaseline':str(destination),'baselineProductionSha256':build['productionSha256'],
    'scope':'Step5 cloud shadows only; no birds, Git/remote/deploy/release archive changes'})
print('PASS Step4 baseline:',build['candidateId'],';',len(files),'prior files; 895 sealed artifacts; independent104-file snapshot')
