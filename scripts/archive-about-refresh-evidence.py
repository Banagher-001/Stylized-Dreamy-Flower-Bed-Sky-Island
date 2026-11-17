"""Freeze raw About-refresh evidence for optional Git LFS delivery; no overwrites."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[1]
RAW=ROOT/'docs/about-refresh/evidence';PREFIX='about-refresh-step14-6341623c81b6b265'
ARCHIVE=ROOT/'release'/(PREFIX+'-evidence.zip')
MANIFEST=ROOT/'release'/(PREFIX+'-evidence-manifest.json')
SUMS=ROOT/'release'/(PREFIX+'-evidence-SHA256SUMS')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return h.hexdigest()
def encoded(value):return (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
assert not ARCHIVE.exists() and not MANIFEST.exists() and not SUMS.exists()
files=sorted(p for p in RAW.rglob('*') if p.is_file())
records=[]
for p in files:
    assert not p.is_symlink()
    records.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)})
created=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
header={'createdAtShanghai':created,'candidateId':PREFIX,'includes':'All original step 2–14 evidence present when the completed About-refresh work was saved to GitHub; step 1 content standards are normal repository Markdown. Failed and superseded attempts retain their original status.','restore':'Extract at repository root; paths start with docs/about-refresh/evidence/. Repository runtime does not need this archive.','files':records}
print(json.dumps({'phase':'archiving','files':len(records),'uncompressedBytes':sum(f['bytes'] for f in records)}),flush=True)
with zipfile.ZipFile(ARCHIVE,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=1,allowZip64=True) as z:
    z.writestr('EVIDENCE-MANIFEST.json',encoded(header))
    z.writestr('EVIDENCE-README.md','# About-refresh raw evidence\n\nAll original bytes are preserved. Extract at the repository root to restore paths used by historical reports. This optional evidence archive is not required to run or rebuild the website. Completed results, intermediate failures, draft packages and original logs remain distinct.\n')
    for i,(p,f) in enumerate(zip(files,records),1):
        assert p.stat().st_size==f['bytes']
        z.write(p,f['path'])
        if i%1000==0:print(json.dumps({'phase':'archiving','filesDone':i}),flush=True)
assert ARCHIVE.stat().st_size<2*1024**3,'GitHub LFS per-file limit exceeded; do not upload'
print(json.dumps({'phase':'verifying','archiveBytes':ARCHIVE.stat().st_size}),flush=True)
with zipfile.ZipFile(ARCHIVE) as z:
    assert len(z.infolist())==len(records)+2
    for f in records:
        h=hashlib.sha256();size=0
        with z.open(f['path']) as entry:
            for chunk in iter(lambda:entry.read(1024*1024),b''):h.update(chunk);size+=len(chunk)
        assert h.hexdigest()==f['sha256'] and size==f['bytes'],f['path']
result={'createdAtShanghai':created,'candidateId':PREFIX,'archive':{'path':ARCHIVE.relative_to(ROOT).as_posix(),'bytes':ARCHIVE.stat().st_size,'sha256':sha(ARCHIVE)},'verifiedOriginalFiles':len(records),'uncompressedBytes':sum(f['bytes'] for f in records),'everyEntrySHA256AndCRCVerified':True,'manifestInsideArchive':'EVIDENCE-MANIFEST.json','files':records}
MANIFEST.write_bytes(encoded(result));SUMS.write_text(result['archive']['sha256']+'  '+ARCHIVE.name+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='files'},ensure_ascii=False),flush=True)
