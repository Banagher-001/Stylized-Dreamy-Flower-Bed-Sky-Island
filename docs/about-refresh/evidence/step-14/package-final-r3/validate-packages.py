"""Extract both ZIPs without any existing repository dependency or asset fallback."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib,json,subprocess,zipfile,shutil
ROOT=Path(__file__).resolve().parents[5];OUT=Path(__file__).parent
build=json.loads((OUT/'build.json').read_text());candidate=build['candidateId']
manifest=json.loads((ROOT/'release'/(candidate+'-r3-manifest.json')).read_text())
scratch=Path('/tmp')/('萨坎 第十四步 最终 r3 独立解压 '+candidate[-16:]);assert not scratch.exists();scratch.mkdir()
result={'candidateId':candidate,'scratch':str(scratch),'startedAtShanghai':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'archives':{},'complete':False}
def save(): (OUT/'package-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
def row(p,base): return {'path':p.relative_to(base).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
for kind,a in manifest['artifacts'].items():
    archive=ROOT/a['path'];assert hashlib.sha256(archive.read_bytes()).hexdigest()==a['sha256']
    dest=scratch/('网站 成品' if kind=='site' else '网站 源码')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert all(not Path(x).is_absolute() and '..' not in Path(x).parts for x in z.namelist())
        z.extractall(dest)
    for f in a['files']: assert row(dest/f['path'],dest)==f
    assert len([p for p in dest.rglob('*') if p.is_file()])==len(a['files'])
    for name in ['START-PREVIEW.cmd']+(['START-DEV.cmd'] if kind=='source' else []):
        raw=(dest/name).read_bytes();assert b'\r\n' in raw and raw.count(b'\n')==raw.count(b'\r\n')
        assert b'\\r\\n' not in raw and b'\\n' not in raw
    result['archives'][kind]={'directory':str(dest),'sha256':a['sha256'],'verifiedFiles':len(a['files']),'CRCAndManifestMatch':True,'windowsLaunchersCRLF':True}
    save()
source=Path(result['archives']['source']['directory']);assert not(source/'node_modules').exists() and not(source/'dist').exists()
for label,cmd in [('npm-ci',['npm','ci','--cache','/workspace/.cache/npm']),('source-build',['npm','run','build'])]:
    with (OUT/(label+'.txt')).open('w') as log:
        proc=subprocess.run(cmd,cwd=source,stdout=log,stderr=subprocess.STDOUT)
    result[label]={'exitCode':proc.returncode,'log':label+'.txt'};save();assert proc.returncode==0,label
rebuilt=[row(p,source/'dist') for p in sorted((source/'dist').rglob('*')) if p.is_file()]
assert rebuilt==build['production'], 'Fresh rebuilt output differs from reviewed production'
result['sourceRebuildExactFiles']=len(rebuilt);result['sameProductionBytes']=True;result['complete']=True
save();print(json.dumps(result,ensure_ascii=False),flush=True)
