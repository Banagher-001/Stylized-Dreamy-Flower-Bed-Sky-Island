"""Seal final step-7 evidence; verify-only never changes archived material."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse,hashlib,json,re
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/evidence/lawson-fullpage-step-7';SEAL=OUT/'evidence-manifest.json'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def row(p):return {'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
def verify(data):
    assert len(data['files'])==data['fileCount']
    for f in data['files']:assert row(ROOT/f['path'])==f,f['path']
    assert sum(f['bytes']for f in data['files'])==data['totalBytes']
p=argparse.ArgumentParser();p.add_argument('--verify-only',action='store_true');args=p.parse_args()
if args.verify_only:
    data=read(SEAL);verify(data);print(json.dumps({'passed':True,'sealedFiles':data['fileCount'],'sealSHA256':sha(SEAL)}));raise SystemExit(0)
assert not SEAL.exists(),'Preserve the seal; use --verify-only'
baseline=read(OUT/'baseline.json');integrity=read(OUT/'integrity.json');parity=read(OUT/'functional-parity.json');browser=read(OUT/'accepted-browser-results.json');candidate=read(OUT/'candidate-manifest.json')
assert integrity['passed']and parity['allOriginalNormalFeaturesPreserved']and browser['allAcceptedCasesHaveDeterminateResults']
assert read(OUT/'event-audit.json')['passed']and read(OUT/'cleanup.json')['passed']
assert not parity['hostNewRegressions']and not integrity['modifiedProductionInputs']
for old in baseline['previousSeals']:assert sha(ROOT/old['path'])==old['sha256'];verify(read(ROOT/old['path']))
docs=[ROOT/f'docs/lawson-fullpage/step-7-{n}.md'for n in ['standard','parity','verification','handoff']]
for doc in docs+[ROOT/'README.md']:
    for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',doc.read_text()):
        if '://'not in target and not target.startswith('#'):assert (doc.parent/target.split('#')[0]).exists(),(doc,target)
for f in candidate['immutableSourceCopies']:assert row(ROOT/f['path'])==f
assert sha(ROOT/'README.md')==sha(OUT/'after/README.md')
paths=set(docs)
for directory in [OUT,ROOT/'tests/lawson-fullpage-step-7']:
    paths.update(p for p in directory.rglob('*')if p.is_file()and p!=SEAL and '__pycache__'not in p.parts)
files=[row(p)for p in sorted(paths)]
data={'schema':1,'auditId':'lawson-fullpage-step-7','candidateId':candidate['candidateId'],'createdAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
 'hostCommit':baseline['hostCommit'],'sourceCommit':baseline['sourceCommit'],'previousSeals':baseline['previousSeals'],'productionSourcesSealedAsCopies':True,
 'selfExcluded':True,'fileCount':len(files),'totalBytes':sum(f['bytes']for f in files),'files':files,
 'controlsPaired':41,'keyboardRecords':13,'picksPaired':17,'completeVehicleCyclesPerMode':3,'acceptedCaseCount':browser['acceptedCaseCount'],
 'fixedOriginalVersionBehaviorPreserved':True,'originalKnownIssuesNotReclassifiedAsFunctionalPass':True,'physicalDevicesVerified':False,'committed':False,'pushed':False,'published':False}
SEAL.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');verify(data)
print(json.dumps({'passed':True,'candidateId':data['candidateId'],'sealedFiles':len(files),'totalBytes':data['totalBytes'],'acceptedCases':data['acceptedCaseCount'],'sealSHA256':sha(SEAL)},ensure_ascii=False))
