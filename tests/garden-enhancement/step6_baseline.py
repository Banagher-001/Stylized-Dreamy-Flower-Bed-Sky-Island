"""Freeze Step5 and verify all older seals before product changes."""
from pathlib import Path
import datetime,hashlib,json,subprocess,tarfile
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/garden-enhancement-step-6';OUT.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(OUT/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
assert not(OUT/'baseline-version.json').exists()
old=ROOT/'docs/evidence/garden-enhancement-step-5';build=json.loads((old/'build-verification.json').read_text())
assert all(sha(ROOT/n)==v for n,v in build['buildInputsSha256'].items())
seals=[]
for step,count in [(1,79),(2,355),(3,226),(4,235),(5,310)]:
    p=ROOT/f'docs/evidence/garden-enhancement-step-{step}/evidence-manifest.json';d=json.loads(p.read_text())
    assert len(d['files'])==count and all(sha(ROOT/n)==v['sha256']for n,v in d['files'].items())
    seals.append({'step':step,'manifestSha256':sha(p),'verifiedFiles':count})
archive=json.loads((old/'candidate-archive-manifest.json').read_text());assert sha(old/archive['file'])==archive['sha256']
destination=Path('/tmp/garden-enhancement-step6-before');destination.mkdir(exist_ok=True)
with tarfile.open(old/archive['file'])as t:
    assert len(t.getmembers())==107;t.extractall(destination,filter='data')
assert all(sha(destination/n)==v['sha256']for n,v in archive['files'].items())
names=set(subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=ROOT).decode().strip('\0').split('\0'))
names={n for n in names if n and not n.startswith('docs/evidence/garden-enhancement-step-6/')and n!='tests/garden-enhancement/step6_baseline.py'}
files={n:{'bytes':(ROOT/n).stat().st_size,'sha256':sha(ROOT/n)}for n in sorted(names)if(ROOT/n).is_file()}
save('before-files.json',{'files':files})
save('baseline-version.json',{'createdAtUtc':datetime.datetime.now(datetime.UTC).isoformat(),'candidateId':build['candidateId'],'gitHead':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(),
    'oldSeals':seals,'beforeFiles':len(files),'baselineArchiveSha256':archive['sha256'],'archiveMembers':107,'independentBaseline':str(destination),'baselineProductionSha256':build['productionSha256'],
    'scope':'Step6 three birds only; no seventh step, publishing, Git/remote writes or old artifact/archive changes'})
print('PASS Step5 baseline',build['candidateId'],';',len(files),'prior files;1205sealed artifacts;independent107-file snapshot')
